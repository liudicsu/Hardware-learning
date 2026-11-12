#!/usr/bin/env python3
"""Knowledge Insulation stand-in for a VLM backbone + continuous action expert. Stdlib only.

Not π0 weights, not ChatVLA (no MoE / phased VQA replay), not OneDP (no one-step distillation),
not DPO. Paper (arXiv 2505.23705) speed, language-following and LIBERO / DROID numbers
are 以论文为准; GPU / π0 / real-robot runs: 本页未运行.

Model assumptions (also stated in the lesson prose):
  Input x in R^D, D=6. A pretrained-style backbone h = A x starts as a semantic projector:
  A0 is block-diagonal (I_3 on the first three coordinates, zeros elsewhere) plus a small
  Gaussian jitter only in the semantic block. A frozen VQA / instruction probe reads the
  first two coordinates of h (prototypes at 0, 120, 240 degrees); its labels are defined by
  the unperturbed projector, so the printed frozen baseline is the probe on A0, not a
  retrained head. The continuous target is a 2-D action that, in the conflict and coarse_bins
  regimes, lives on coordinates 3 and 4 — coordinates the frozen backbone does not pass
  through. Discrete-action tokens are a uniform grid of BINS x BINS bins on [-3, 3]^2, a
  stand-in for the paper's FAST / naive tokens, not FAST itself. After the first run, the discrete head reads only the action-slot hidden units h[SEM:] (a stand-in for the paper's separate discrete-action tokens). The first-run alternative, which fed the full h to the discrete head, is still trained on the same seeds and printed; that choice was not fixed before the first run.

  The action expert is a linear flow-matching residual: given h, a noisy action
  a_τ = τ a + (1-τ) ε and τ, it predicts u = a - ε. Training is plain SGD on that residual
  plus, where the arm allows it, softmax cross-entropy on the discrete bins. There is no
  plant integration step (discrete SGD). Inference uses a fixed 1-step Euler read-out
  (the true velocity is constant along the straight path, so 1 step is exact for a perfect
  expert); a 4-step read-out is also printed, not as a stability criterion.

Arms (Common random numbers: per (regime, seed) the A0 jitter, expert and discrete-head
init, every training batch of (x, ε, τ), and the test set are drawn once and reused):
  A_naive      flow-matching loss back-propagates into A; no discrete-action CE
  B_insulate   discrete-action CE into A; expert grads stop at h (sg)
  C_frozen     A is held at A0; expert only; no discrete-action CE

Equal step budget STEPS, batch BATCH, learning rate LR.

Metrics per seed: probe accuracy % on the test set; control success % (|a_hat - a| <= TOL
with the 1-step read-out); 1-step and 4-step action MSE; fit_mid = mean test FM residual
after MID steps (training-speed proxy); fit_final = the same after STEPS.

Regimes, written before the first run:
  conflict     action = (x_3, x_4), BINS=4
               A consistent probe drop vs B and/or slower residual drop (higher fit_mid);
               A and B may near-tie on in-distribution control;
               C wins the probe and loses on control — both metrics kept
  coarse_bins  same targets, BINS=2 (weaker discrete CE)
               B may lose control to A; probe comparison printed either way
  aligned      action = (x_0, x_1) (inside the semantic block), BINS=4
               C may near-tie on control (the frozen features already carry the action);
               probe drop, if any, is printed; not used to pick a winner

Paper numbers 以论文为准. GPU / π0 / LIBERO: 本页未运行.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
D, ACT, NQ = 6, 2, 3
SEM = 3
STEPS, MID, BATCH, TEST = 400, 100, 8, 400
LR = 0.05
TOL = 0.35
INIT_SD = 0.05
EXP_SD = 0.05
BIN_LO, BIN_HI = -3.0, 3.0
NUM_ZERO = 1e-9
ARMS = ("A_naive", "B_insulate", "C_frozen")
# name: (action coordinates, bins-per-axis); written before the first run
REGIMES = {
    "conflict": ((3, 4), 4),
    "coarse_bins": ((3, 4), 2),
    "aligned": ((0, 1), 4),
}
STREAM = {"conflict": 0, "coarse_bins": 1, "aligned": 2}
# frozen probe prototypes in the first two hidden coordinates
V0 = [[math.cos(2 * math.pi * k / NQ), math.sin(2 * math.pi * k / NQ)] for k in range(NQ)]


def zeros(r, c=None):
    if c is None:
        return [0.0] * r
    return [[0.0] * c for _ in range(r)]


def matvec(mat, v):
    return [sum(a * b for a, b in zip(row, v)) for row in mat]


def add_vec(a, b, s=1.0):
    return [x + s * y for x, y in zip(a, b)]


def axpy_mat(dst, src, s):
    for i, row in enumerate(src):
        for j, v in enumerate(row):
            dst[i][j] += s * v


def axpy_vec(dst, src, s):
    for i, v in enumerate(src):
        dst[i] += s * v


def outer(u, v):
    return [[ui * vj for vj in v] for ui in u]


def argmax(v):
    return max(range(len(v)), key=lambda k: v[k])


def softmax(logits):
    m = max(logits)
    ex = [math.exp(x - m) for x in logits]
    z = sum(ex)
    return [e / z for e in ex]


def clip_bin(val, bins):
    t = (val - BIN_LO) / (BIN_HI - BIN_LO)
    i = int(math.floor(t * bins))
    return max(0, min(bins - 1, i))


def action_of(x, coord):
    return [x[coord[0]], x[coord[1]]]


def token_of(a, bins):
    return clip_bin(a[0], bins) * bins + clip_bin(a[1], bins)


def vqa_label(x):
    # defined by the unperturbed semantic projector: h* = (x0, x1)
    return argmax([v[0] * x[0] + v[1] * x[1] for v in V0])


def probe_pred(h):
    return argmax([v[0] * h[0] + v[1] * h[1] for v in V0])


def make_A0(rng):
    A = zeros(D, D)
    for i in range(SEM):
        for j in range(SEM):
            A[i][j] = (1.0 if i == j else 0.0) + rng.gauss(0.0, INIT_SD)
    return A


def feat_of(h, a_tau, tau):
    return list(h) + list(a_tau) + [tau]


def shared_draws(regime, seed):
    rng = random.Random(2000 * STREAM[regime] + seed)
    coord, bins = REGIMES[regime]
    nclass = bins * bins
    A0 = make_A0(rng)
    We0 = [[rng.gauss(0.0, EXP_SD) for _ in range(D + ACT + 1)] for _ in range(ACT)]
    be0 = [rng.gauss(0.0, EXP_SD) for _ in range(ACT)]
    Wd0 = [[rng.gauss(0.0, EXP_SD) for _ in range(D)] for _ in range(nclass)]
    bd0 = [0.0] * nclass
    batches = []
    for _ in range(STEPS):
        xs, eps, taus = [], [], []
        for _ in range(BATCH):
            x = [rng.gauss(0.0, 1.0) for _ in range(D)]
            e = [rng.gauss(0.0, 1.0) for _ in range(ACT)]
            t = rng.random()
            xs.append(x)
            eps.append(e)
            taus.append(t)
        batches.append((xs, eps, taus))
    test = []
    for _ in range(TEST):
        x = [rng.gauss(0.0, 1.0) for _ in range(D)]
        e = [rng.gauss(0.0, 1.0) for _ in range(ACT)]
        test.append((x, action_of(x, coord), e, vqa_label(x)))
    return {
        "coord": coord,
        "bins": bins,
        "nclass": nclass,
        "A0": A0,
        "We0": We0,
        "be0": be0,
        "Wd0": Wd0,
        "bd0": bd0,
        "batches": batches,
        "test": test,
    }


def copy_mat(m):
    return [row[:] for row in m]


def flow_predict(We, be, h, a_tau, tau):
    return add_vec(matvec(We, feat_of(h, a_tau, tau)), be)


def integrate(We, be, h, eps, steps):
    a = list(eps)
    if steps <= 1:
        u = flow_predict(We, be, h, a, 0.0)
        return add_vec(a, u)
    dt = 1.0 / steps
    t = 0.0
    for _ in range(steps):
        u = flow_predict(We, be, h, a, t)
        a = add_vec(a, u, dt)
        t += dt
    return a


def train_arm(arm, draws, discrete="slot"):
    A = copy_mat(draws["A0"])
    We = copy_mat(draws["We0"])
    be = draws["be0"][:]
    Wd = copy_mat(draws["Wd0"])
    bd = draws["bd0"][:]
    coord, bins, nclass = draws["coord"], draws["bins"], draws["nclass"]
    # "slot": discrete head sees h[SEM:] only (main; chosen after the first run)
    # "full": first-run alternative, discrete head sees the whole of h
    if discrete == "slot":
        Wd = [row[SEM:] for row in Wd]
        d_in = D - SEM
    else:
        d_in = D
    mid_snapshot = None
    for step, (xs, eps, taus) in enumerate(draws["batches"]):
        gA, gWe, gbe = zeros(D, D), zeros(ACT, D + ACT + 1), zeros(ACT)
        gWd, gbd = zeros(nclass, d_in), zeros(nclass)
        for x, e, tau in zip(xs, eps, taus):
            a = action_of(x, coord)
            h = matvec(A, x)
            a_tau = add_vec([tau * ai for ai in a], e, 1.0 - tau)
            u = add_vec(a, e, -1.0)
            feat = feat_of(h, a_tau, tau)
            u_hat = add_vec(matvec(We, feat), be)
            err = add_vec(u_hat, u, -1.0)
            # dL/d u_hat = 2 err
            scale = 2.0 / BATCH
            derr = [scale * v for v in err]
            axpy_mat(gWe, outer(derr, feat), 1.0)
            axpy_vec(gbe, derr, 1.0)
            dfeat = [sum(We[k][j] * derr[k] for k in range(ACT)) for j in range(D + ACT + 1)]
            dh_fm = dfeat[:D]
            if arm == "A_naive":
                axpy_mat(gA, outer(dh_fm, x), 1.0)
            if arm == "B_insulate":
                y = token_of(a, bins)
                h_d = h if discrete == "full" else h[SEM:]
                logits = add_vec(matvec(Wd, h_d), bd)
                p = softmax(logits)
                dlog = [scale * (pj - (1.0 if i == y else 0.0)) for i, pj in enumerate(p)]
                axpy_mat(gWd, outer(dlog, h_d), 1.0)
                axpy_vec(gbd, dlog, 1.0)
                dh_part = [sum(Wd[k][j] * dlog[k] for k in range(nclass)) for j in range(len(h_d))]
                dh_ce = dh_part if discrete == "full" else ([0.0] * SEM + dh_part)
                axpy_mat(gA, outer(dh_ce, x), 1.0)
            # C_frozen: no gA, no discrete CE
        if arm != "C_frozen":
            axpy_mat(A, gA, -LR)
        axpy_mat(We, gWe, -LR)
        axpy_vec(be, gbe, -LR)
        if arm == "B_insulate":
            axpy_mat(Wd, gWd, -LR)
            axpy_vec(bd, gbd, -LR)
        if step + 1 == MID:
            mid_snapshot = (copy_mat(A), copy_mat(We), be[:])
    return A, We, be, mid_snapshot


def eval_metrics(A, We, be, draws, steps_euler=1):
    probe_ok = 0
    ctrl_ok = 0
    mse1 = 0.0
    mse4 = 0.0
    fm = 0.0
    n = len(draws["test"])
    for x, a, e, y in draws["test"]:
        h = matvec(A, x)
        if probe_pred(h) == y:
            probe_ok += 1
        a1 = integrate(We, be, h, e, 1)
        a4 = integrate(We, be, h, e, 4)
        se1 = sum((p - q) ** 2 for p, q in zip(a1, a))
        se4 = sum((p - q) ** 2 for p, q in zip(a4, a))
        mse1 += se1
        mse4 += se4
        if math.sqrt(se1) <= TOL:
            ctrl_ok += 1
        # FM residual at a random-path point using the same test ε at τ=0.5
        tau = 0.5
        a_tau = add_vec([tau * ai for ai in a], e, 1.0 - tau)
        u = add_vec(a, e, -1.0)
        u_hat = flow_predict(We, be, h, a_tau, tau)
        fm += sum((p - q) ** 2 for p, q in zip(u_hat, u))
    return {
        "probe_%": 100.0 * probe_ok / n,
        "control_%": 100.0 * ctrl_ok / n,
        "mse_1step": mse1 / n,
        "mse_4step": mse4 / n,
        "fm": fm / n,
    }


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-5:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs, m):
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{num(m)}+-{num(s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{num(m)}+-{num(s)}: {label}; {sign_note(diffs, m)}"


def fmt_arm(name, rows, keys):
    parts = []
    for k in keys:
        xs = [r[k] for r in rows]
        m, s = mean_sd(xs)
        parts.append(f"{k}={num(m)}+-{num(s)}")
    return f"  {name} " + " ".join(parts)


def main():
    print(
        "Synthetic Knowledge Insulation probe: naive FM grads into the backbone vs "
        "discrete-action CE + stopped expert grads vs a frozen backbone; linear stand-in, not π0"
    )
    print(
        f"D={D} ACT={ACT} NQ={NQ} STEPS={STEPS} MID={MID} BATCH={BATCH} LR={LR} "
        f"TOL={TOL} TEST={TEST} seeds={len(SEEDS)}"
    )
    print(
        "no plant integration step (discrete SGD); inference 1-step Euler "
        "(true velocity constant along the path); 4-step read-out also printed"
    )
    print(
        "regime arm probe_% control_% mse_1step mse_4step fit_mid fit_final  "
        "(mean+-sd over seeds)"
    )
    keys = ("probe_%", "control_%", "mse_1step", "mse_4step", "fit_mid", "fit_final")
    for regime in REGIMES:
        coord, bins = REGIMES[regime]
        draws_all = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [] for arm in ARMS}
        baselines = []
        for d in draws_all:
            # frozen baseline: probe on A0, no expert yet
            base = eval_metrics(d["A0"], d["We0"], d["be0"], d)
            baselines.append(base["probe_%"])
            for arm in ARMS:
                A, We, be, mid = train_arm(arm, d, discrete="slot")
                out = eval_metrics(A, We, be, d)
                if mid is None:
                    mid_m = eval_metrics(d["A0"], d["We0"], d["be0"], d)
                else:
                    mid_m = eval_metrics(mid[0], mid[1], mid[2], d)
                out["fit_mid"] = mid_m["fm"]
                out["fit_final"] = out["fm"]
                res[arm].append(out)
        base_m, base_s = mean_sd(baselines)
        print(
            f"{regime} (action on x[{coord[0]}],x[{coord[1]}]; BINS={bins}; "
            f"frozen baseline probe {num(base_m)}+-{num(base_s)} %)"
        )
        for arm in ARMS:
            print(fmt_arm(arm, res[arm], keys))
        pairs = (("B_insulate", "A_naive"), ("C_frozen", "B_insulate"), ("C_frozen", "A_naive"))
        for met in keys:
            for x, y in pairs:
                print(
                    f"  paired {x}-{y} {met}: "
                    + verdict([r[met] for r in res[x]], [r[met] for r in res[y]])
                )
        if regime in ("conflict", "coarse_bins"):
            alt = {arm: [] for arm in ARMS}
            for d in draws_all:
                for arm in ARMS:
                    A, We, be, mid = train_arm(arm, d, discrete="full")
                    out = eval_metrics(A, We, be, d)
                    if mid is None:
                        mid_m = eval_metrics(d["A0"], d["We0"], d["be0"], d)
                    else:
                        mid_m = eval_metrics(mid[0], mid[1], mid[2], d)
                    out["fit_mid"] = mid_m["fm"]
                    out["fit_final"] = out["fm"]
                    alt[arm].append(out)
            print(f"  alternative discrete=full h (first-run head, same seeds) on {regime}:")
            for arm in ARMS:
                print("  " + fmt_arm(arm, alt[arm], ("probe_%", "control_%", "fit_mid", "fit_final")))
            print(
                "    paired B_insulate-A_naive probe_%: "
                + verdict([r["probe_%"] for r in alt["B_insulate"]], [r["probe_%"] for r in alt["A_naive"]])
            )
            print(
                "    paired B_insulate-A_naive control_%: "
                + verdict([r["control_%"] for r in alt["B_insulate"]], [r["control_%"] for r in alt["A_naive"]])
            )
    print(
        "No winner declared: a frozen backbone keeps the probe and can lose on control when "
        "the action sits outside the pretrained features; whether insulation also beats naive "
        "FM grads on the probe depends on how the discrete head is attached (slot vs full h)"
    )
    print("Knowledge Insulation paper numbers 以论文为准; GPU / π0 / LIBERO: 本页未运行")
    print("not ChatVLA phased alignment; not OneDP one-step regression")


if __name__ == "__main__":
    main()
