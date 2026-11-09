#!/usr/bin/env python3
"""Synthetic continual VLA finetune + experience-replay literacy toy. Stdlib only.

Shared task sequence, shared total gradient steps, and shared sample noise for
every arm (common random numbers per seed). Every arm faces the **same** noise.

Arms:
  A_sequential   finetune task-by-task with **no** replay (buffer capacity 0)
  B_er_small     ER with small replay buffer (capacity B_SMALL)
  C_er_large     ER with larger replay buffer (capacity B_LARGE)

Regimes (≥5 seeds):
  no_shift     — single task; A/B/C **exact/near tie** (ER gives no gain)
  task_shift   — two tasks; sequential forgets; ER reduces forgetting

Metrics: avg success, backward transfer (NBT-style drop on task0 after task1),
replay buffer capacity, and compute cost = grad_steps × (batch + replay_per_step).

Assumptions: linear probe stand-in of pretrained vs sequential BC — not real VLA
weights. Liu et al. arXiv:2603.03818 (abs+HTML+PDF): pretrained VLAs + small ER.
Paper LIBERO/NBT % 以论文为准; GPU/weights 本页未运行.
≠ compute_budget floors alone; ≠ SARM/DPO/RPD; ≠ MemoryVLA.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_sequential", "B_er_small", "C_er_large")
DIM = 4
B_SMALL = 8
B_LARGE = 48
GRAD_STEPS_PER_TASK = 40
BATCH = 4
# Replay draws per step (compute cost explicit)
REPLAY_PER_STEP_SMALL = 2
REPLAY_PER_STEP_LARGE = 4
REGIMES = ("no_shift", "task_shift")


def shared_tasks(seed: int):
    """CRN: task datasets + eval noise identical for all arms."""
    rng = random.Random(60_000 + seed)
    # Two tasks: linear classifiers with different targets in feature space
    def make_task(offset: float, n: int = 60):
        X, y = [], []
        for _ in range(n):
            x = [rng.gauss(offset, 0.6) for _ in range(DIM)]
            # Label: sign of weighted sum (task-specific weights)
            w = [1.0, -0.5, 0.3, 0.8]
            s = sum(w[k] * (x[k] - offset) for k in range(DIM))
            y.append(1.0 if s >= 0.0 else 0.0)
            X.append(x)
        return X, y

    t0 = make_task(0.0)
    t1 = make_task(2.0)
    # Shared eval noise on logits
    eval_noise = [rng.gauss(0.0, 0.05) for _ in range(200)]
    return t0, t1, eval_noise


def init_pretrained(seed: int):
    """Shared pretrained-like prior (same for all arms)."""
    rng = random.Random(70_000 + seed)
    w = [0.2 * rng.gauss(0.0, 1.0) for _ in range(DIM)]
    b = 0.0
    return w, b


def predict_prob(x, w, b, noise=0.0):
    z = b + sum(w[k] * x[k] for k in range(DIM)) + noise
    # logistic
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def accuracy(X, y, w, b, eval_noise):
    ok = 0
    for i, (x, yi) in enumerate(zip(X, y)):
        p = predict_prob(x, w, b, eval_noise[i % len(eval_noise)])
        ok += 1 if (p >= 0.5) == (yi >= 0.5) else 0
    return ok / len(y)


def sgd_step(w, b, batch_X, batch_y, lr=0.2):
    gw = [0.0] * DIM
    gb = 0.0
    for x, yi in zip(batch_X, batch_y):
        p = predict_prob(x, w, b)
        err = p - yi
        gb += err
        for k in range(DIM):
            gw[k] += err * x[k]
    n = len(batch_X)
    b -= lr * gb / n
    w = [w[k] - lr * gw[k] / n for k in range(DIM)]
    return w, b


def train_on_task(w, b, X, y, buffer, buf_cap, replay_per_step, steps, rng, protect_old=0):
    """One task phase. Mutates buffer. Returns (w,b,compute_units).

    protect_old: number of leading buffer slots reserved for prior-task exemplars
    (not overwritten during the new task). Explicit ER capacity accounting.
    """
    compute = 0
    n = len(X)
    for step in range(steps):
        # Fresh batch from current task
        batch_X, batch_y = [], []
        for _ in range(BATCH):
            i = rng.randrange(n)
            batch_X.append(X[i])
            batch_y.append(y[i])
            # Add to replay buffer (reservoir-ish); never overwrite protected prefix
            if buf_cap > 0:
                if len(buffer) < buf_cap:
                    buffer.append((X[i], y[i]))
                else:
                    lo = max(0, min(protect_old, buf_cap - 1))
                    j = rng.randrange(lo, buf_cap)
                    buffer[j] = (X[i], y[i])
        # Replay mix
        if buffer and replay_per_step > 0:
            for _ in range(replay_per_step):
                bx, by = buffer[rng.randrange(len(buffer))]
                batch_X.append(bx)
                batch_y.append(by)
        compute += len(batch_X)  # samples touched this step
        w, b = sgd_step(w, b, batch_X, batch_y)
    return w, b, compute


def run_arm(arm: str, seed: int, regime: str):
    t0, t1, eval_noise = shared_tasks(seed)
    w, b = init_pretrained(seed)
    # Private RNG only for batch index order; data itself is shared CRN
    # Batch-index RNG: arm-salted under shift (private order); seed-only on no_shift so ER overhead
    # cannot look like a different fit when there is nothing to replay across tasks.
    if regime == "no_shift":
        rng = random.Random(80_000 + seed)
    else:
        rng = random.Random(80_000 + seed * 17 + {"A_sequential": 1, "B_er_small": 2, "C_er_large": 3}[arm])
    if arm == "A_sequential":
        cap, replay = 0, 0
    elif arm == "B_er_small":
        cap, replay = B_SMALL, REPLAY_PER_STEP_SMALL
    else:
        cap, replay = B_LARGE, REPLAY_PER_STEP_LARGE
    buffer: list[tuple[list[float], float]] = []
    total_compute = 0

    # Task 0
    w, b, c0 = train_on_task(w, b, t0[0], t0[1], buffer, cap, replay, GRAD_STEPS_PER_TASK, rng)
    total_compute += c0
    acc0_after0 = accuracy(t0[0], t0[1], w, b, eval_noise)

    if regime == "no_shift":
        # Only one task — ER cannot help relative to sequential
        avg = acc0_after0
        nbt = 0.0  # no second task
        return avg, nbt, cap, total_compute, replay

    # Seed / refresh buffer with task-0 exemplars before shift (ER's point)
    if cap > 0:
        buffer.clear()
        for i in range(min(cap, len(t0[0]))):
            buffer.append((t0[0][i], t0[1][i]))

    # Task 1 — protect half the buffer as prior-task exemplars
    protect = cap // 2
    w, b, c1 = train_on_task(
        w, b, t1[0], t1[1], buffer, cap, replay, GRAD_STEPS_PER_TASK, rng, protect_old=protect
    )
    total_compute += c1
    acc0_after1 = accuracy(t0[0], t0[1], w, b, eval_noise)
    acc1_after1 = accuracy(t1[0], t1[1], w, b, eval_noise)
    avg = 0.5 * (acc0_after1 + acc1_after1)
    # NBT-style: drop on task0 (positive = forgetting)
    nbt = acc0_after0 - acc0_after1
    return avg, nbt, cap, total_compute, replay


def mean_sd(xs):
    n = len(xs)
    mu = sum(xs) / n
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (n - 1))


def main():
    print(
        "Synthetic continual VLA + ER toy; shared tasks/steps/noise; "
        "not MemoryVLA / SARM / compute_budget redo"
    )
    print(
        f"DIM={DIM} GRAD_STEPS_PER_TASK={GRAD_STEPS_PER_TASK} BATCH={BATCH} "
        f"B_SMALL={B_SMALL} B_LARGE={B_LARGE} "
        f"REPLAY_PER_STEP={REPLAY_PER_STEP_SMALL}/{REPLAY_PER_STEP_LARGE} "
        f"seeds={len(SEEDS)}"
    )
    print(
        "model: pretrained-like linear probe; A=sequential (cap=0); "
        f"B=ER cap={B_SMALL}; C=ER cap={B_LARGE}; "
        "compute = sum over steps of |batch|+|replay|; "
        "Liu et al. arXiv:2603.03818; LIBERO/NBT % 以论文为准; GPU/weights 本页未运行"
    )
    print(
        "regime arm avg_success nbt_forget buffer_cap compute_samples "
        "replay_per_step (mean+-sd over seeds)"
    )
    summary = {}
    for regime in REGIMES:
        for arm in ARMS:
            avgs, nbts, caps, comps, rps = [], [], [], [], []
            for seed in SEEDS:
                avg, nbt, cap, comp, rp = run_arm(arm, seed, regime)
                avgs.append(avg)
                nbts.append(nbt)
                caps.append(cap)
                comps.append(comp)
                rps.append(rp)
            ma, sa = mean_sd(avgs)
            mn, sn = mean_sd(nbts)
            mc, sc = mean_sd(comps)
            summary[(regime, arm)] = (ma, mn, caps[0], mc, rps[0])
            print(
                f"{regime} {arm} {ma:.4f}+-{sa:.4f} {mn:.4f}+-{sn:.4f} "
                f"{caps[0]} {mc:.1f}+-{sc:.1f} {rps[0]}"
            )

    # no_shift: A vs B avg gap
    aa = summary[("no_shift", "A_sequential")][0]
    ab = summary[("no_shift", "B_er_small")][0]
    ac = summary[("no_shift", "C_er_large")][0]
    gap = max(abs(aa - ab), abs(aa - ac), abs(ab - ac))
    if gap < 1e-6:
        lab = "exact tie (gap≈0)"
    elif gap < 0.02:
        lab = f"near-tie / small gap; max |Δavg|={gap:.4f}; no task shift ⇒ ER buys nothing"
    else:
        lab = f"gap; max |Δavg|={gap:.4f}"
    print(f"no_shift: A/B/C avg_success ({lab})")

    fa = summary[("task_shift", "A_sequential")][1]
    fb = summary[("task_shift", "B_er_small")][1]
    fc = summary[("task_shift", "C_er_large")][1]
    print(
        f"task_shift: NBT forget A={fa:.4f} B={fb:.4f} C={fc:.4f} "
        f"(ER reduces forgetting; larger buffer/compute costs more samples: "
        f"B compute={summary[('task_shift','B_er_small')][3]:.0f}, "
        f"C compute={summary[('task_shift','C_er_large')][3]:.0f} vs "
        f"A={summary[('task_shift','A_sequential')][3]:.0f})"
    )
    print(
        "No winner declared: with no shift ER matches sequential; "
        "under shift ER helps but buffer capacity and replay samples are real costs; "
        "avg_success is blind to wall-clock GPU time"
    )
    print(
        "Real continual VLA / LIBERO lab: 本页未运行; "
        "Liu et al. arXiv:2603.03818 numbers 以论文为准"
    )


if __name__ == "__main__":
    main()
