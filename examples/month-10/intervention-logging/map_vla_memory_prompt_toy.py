#!/usr/bin/env python3
"""MAP-VLA stand-in: stage memory soft prompts, trajectory retrieval and prompt ensembling. Stdlib only.

Model assumptions (also stated in the lesson prose):
  a 2D point "end effector" must visit K stage goals in order (step <= 0.25, goal reached within
  0.15, 14 steps per stage, else the episode stops). The observation is the noisy state plus a
  4-dim noisy one-hot "scene look"; in ambiguous regimes two stages share one look, like the same
  camera view at different points of a long task. The "frozen VLA" is one linear map W from
  [state, look, 1] to the action, fit by least squares on 8 logged demonstrations (corrections) per
  seed and never changed afterwards. A stage "soft prompt" V_k is added to the prompt features, so
  its effect on the action is W V_k; prompt tuning is the least-squares fit of that effect on the
  stage-k frames (the mean residual of the frozen W there). Stage labels in the demos are known
  (the paper finds them with RDP key poses + DTW; that step is not simulated).
  Retrieval: the last 4 observed states are compared with every 4-state demo window whose stage is
  within 1 of the current stage estimate (L2 cost, paper Eq. 4-5); the best window gives the stage
  and a 4-step reference action chunk. Ensembling (Eq. 6-7): alpha = softmax weight of the memory
  chunk against the base chunk by squared distance to the reference chunk.

Arms (Common random numbers: per (regime, seed) the same demos and frozen W; per episode the same
start, observation noise, look noise and motion noise, indexed by step):
  A_memoryless  base prompt only: the current observation, no memory
  B_map         retrieve stage + reference, add that stage's prompt, ensemble with the base chunk
  C_wrongstage  same retrieval, but the prompt AND reference come from the neighbouring stage
                (a mismatched memory, e.g. a segmentation off by one); ensemble as in B

Metrics per seed (means over 20 episodes): stage = share of stages completed, full = share of
episodes that complete every stage, steps = environment steps used (an episode stops at the first
stage that runs out of budget), hit = share of retrievals whose stage equals the true stage.

Labels: tie = identical on every seed; |m| < 1e-9 and sd < 1e-9 = numerically zero
(floating-point residue), effectively a tie, no sign count; |paired mean| <= sd = near-tie / small
gap within seed noise; |m| > sd = consistent gap (small if |m| < 20 % of the smaller arm mean, else
clear), always with a sign count.
pi0 weights / LIBERO / real robot / GPU: 本页未运行. Paper numbers: 以论文为准.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
STEP, TOL, BUDGET = 0.25, 0.15, 14
WIN, H = 4, 4
N_DEMO, EPISODES = 8, 20
LOOKS = 4
SIG_DEMO, SIG_MOTION = 0.03, 0.01
ARMS = ("A_memoryless", "B_map", "C_wrongstage")
METRICS = ("stage", "full", "steps")
SQUARE = ((1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0))
# name, stage goals, stage -> look, state noise sd, look noise sd
REGIMES = (
    ("ambiguous_long", SQUARE, (0, 1, 0, 1), 0.02, 0.1),
    ("distinct_long", SQUARE, (0, 1, 2, 3), 0.02, 0.1),
    ("single_stage", ((1.0, 0.0),), (0,), 0.02, 0.1),
    ("noisy_retrieval", SQUARE, (0, 1, 0, 1), 0.12, 0.1),
)


def clip(v, m=STEP):
    n = math.hypot(*v)
    return v if n <= m else (v[0] * m / n, v[1] * m / n)


def solve(a, b):
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(m[r][i]))
        m[i], m[p] = m[p], m[i]
        for r in range(n):
            if r != i:
                q = m[r][i] / m[i][i]
                for c in range(i, n + 1):
                    m[r][c] -= q * m[i][c]
    return [m[i][n] / m[i][i] for i in range(n)]


def look(noise, stage, lookmap, sd):
    return [(1.0 if i == lookmap[stage] else 0.0) + sd * noise[i] for i in range(LOOKS)]


def feats(s, c):
    return [s[0], s[1], *c, 1.0]


def demos(regime, seed):
    """Logged demonstrations / corrections with stage labels; shared by all arms."""
    name, goals, lookmap, _, sd_c = regime
    rng = random.Random(100000 * [r[0] for r in REGIMES].index(name) + 1000 * seed)
    out = []
    for _ in range(N_DEMO):
        s, traj = (rng.gauss(0, 0.05), rng.gauss(0, 0.05)), []
        for k, g in enumerate(goals):
            n = 0
            while math.dist(s, g) > TOL / 2 and n < BUDGET:
                c = look([rng.gauss(0, 1) for _ in range(LOOKS)], k, lookmap, sd_c)
                a = clip((g[0] - s[0], g[1] - s[1]))
                a = (a[0] + rng.gauss(0, SIG_DEMO), a[1] + rng.gauss(0, SIG_DEMO))
                traj.append((s, c, a, k))
                s, n = (s[0] + a[0], s[1] + a[1]), n + 1
        out.append(traj)
    return out


def fit_base(demo):
    d = 2 + LOOKS + 1
    a = [[1e-6 if i == j else 0.0 for j in range(d)] for i in range(d)]
    b = [[0.0] * d for _ in range(2)]
    for traj in demo:
        for s, c, act, _ in traj:
            x = feats(s, c)
            for i in range(d):
                for j in range(d):
                    a[i][j] += x[i] * x[j]
                for o in range(2):
                    b[o][i] += x[i] * act[o]
    return [solve(a, b[o]) for o in range(2)]


def policy(w, s, c, prompt=(0.0, 0.0)):
    x = feats(s, c)
    return clip((sum(p * q for p, q in zip(w[0], x)) + prompt[0], sum(p * q for p, q in zip(w[1], x)) + prompt[1]))


def tune_prompts(w, demo, n_stages):
    """Least-squares effect W V_k of each stage soft prompt on the frozen W: mean residual on stage k."""
    out = []
    for k in range(n_stages):
        r, n = [0.0, 0.0], 0
        for traj in demo:
            for s, c, act, kk in traj:
                if kk == k:
                    p = policy(w, s, c)
                    r[0] += act[0] - p[0]
                    r[1] += act[1] - p[1]
                    n += 1
        out.append((r[0] / n, r[1] / n))
    return out


def chunk(w, s, c, prompt):
    out, x = [], s
    for _ in range(H):
        a = policy(w, x, c, prompt)
        out.append(a)
        x = (x[0] + a[0], x[1] + a[1])
    return out


def retrieve(demo, hist, ok):
    """Sliding-window L2 match over demo windows whose stage passes ok(stage)."""
    best = None
    for i, traj in enumerate(demo):
        for j in range(WIN - 1, len(traj)):
            if not ok(traj[j][3]):
                continue
            cost = sum(math.dist(hist[q], traj[j - WIN + 1 + q][0]) ** 2 for q in range(WIN))
            if best is None or cost < best[0]:
                best = (cost, i, j)
    _, i, j = best
    traj = demo[i]
    return traj[j][3], [traj[min(j + h, len(traj) - 1)][2] for h in range(H)]


def episode_draws(regime, seed, ep):
    rng = random.Random(100000 * [r[0] for r in REGIMES].index(regime[0]) + 1000 * seed + 500 + ep)
    n = BUDGET * len(regime[1]) + 1
    return {"s0": (rng.gauss(0, 0.05), rng.gauss(0, 0.05)),
            "obs": [(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)],
            "look": [[rng.gauss(0, 1) for _ in range(LOOKS)] for _ in range(n)],
            "motion": [(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]}


def run_episode(arm, regime, w, prompts, demo, nz):
    _, goals, lookmap, sd_s, sd_c = regime
    n_st = len(goals)
    s = nz["s0"]
    hist, k_cur, done, hits, queries, t = [s] * WIN, 0, 0, 0, 0, 0
    for k, g in enumerate(goals):
        n = 0
        while math.dist(s, g) > TOL:
            if n >= BUDGET:
                return {"stage": done / n_st, "full": 0.0, "steps": float(t)}, hits, queries
            e = nz["obs"][t]
            so = (s[0] + sd_s * e[0], s[1] + sd_s * e[1])
            c = look(nz["look"][t], k, lookmap, sd_c)
            hist = hist[1:] + [so]
            if arm == "A_memoryless":
                a = policy(w, so, c)
            else:
                k_ret, ref = retrieve(demo, hist, lambda kk: abs(kk - k_cur) <= 1)
                k_cur, queries, hits = k_ret, queries + 1, hits + (k_ret == k)
                k_use = k_ret
                if arm == "C_wrongstage":
                    k_use = k_ret + 1 if k_ret + 1 < n_st else k_ret - 1
                    _, ref = retrieve(demo, hist, lambda kk: kk == k_use)
                mem, base = chunk(w, so, c, prompts[k_use]), chunk(w, so, c, (0.0, 0.0))
                dm = sum((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for p, q in zip(mem, ref))
                db = sum((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for p, q in zip(base, ref))
                alpha = 1.0 / (1.0 + math.exp(dm - db))
                a = clip((alpha * mem[0][0] + (1 - alpha) * base[0][0], alpha * mem[0][1] + (1 - alpha) * base[0][1]))
            m = nz["motion"][t]
            s = (s[0] + a[0] + SIG_MOTION * m[0], s[1] + a[1] + SIG_MOTION * m[1])
            n, t = n + 1, t + 1
        done += 1
    return {"stage": 1.0, "full": 1.0, "steps": float(t)}, hits, queries


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
    if x != 0.0 and abs(x) < 5e-4:
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


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


NUM_ZERO = 1e-9  # |m| and sd both below this: floating-point residue, not a gap


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(mean_sd(xa)[0], mean_sd(xb)[0]):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def main() -> None:
    print("Synthetic staged reaching task; shared demos / frozen base / episode noise; stand-in for a frozen VLA, not pi0")
    print(f"seeds={len(SEEDS)} demos={N_DEMO} episodes={EPISODES} window={WIN} chunk={H} step<={STEP} tol={TOL} "
          f"budget={BUDGET}/stage")
    print("regime arm stage full steps hit  (mean+-sd over seeds of the per-seed episode means)")
    for regime in REGIMES:
        name, goals, lookmap, sd_s, sd_c = regime
        arms = ARMS if len(goals) > 1 else ARMS[:2]
        per = {arm: {m: [] for m in METRICS + ("hit",)} for arm in arms}
        for seed in SEEDS:
            demo = demos(regime, seed)
            w = fit_base(demo)
            prompts = tune_prompts(w, demo, len(goals))
            for arm in arms:
                acc, hits, queries = {m: 0.0 for m in METRICS}, 0, 0
                for ep in range(EPISODES):
                    out, h, q = run_episode(arm, regime, w, prompts, demo, episode_draws(regime, seed, ep))
                    hits, queries = hits + h, queries + q
                    for m in METRICS:
                        acc[m] += out[m] / EPISODES
                for m in METRICS:
                    per[arm][m].append(acc[m])
                per[arm]["hit"].append(hits / queries if queries else 0.0)
        print(f"{name} ({len(goals)} stage{'s' if len(goals) > 1 else ''}, looks {list(lookmap)}, state noise sd={sd_s}, look noise sd={sd_c})")
        for arm in arms:
            hit = "-" if arm == "A_memoryless" else "{}+-{}".format(*map(num, mean_sd(per[arm]["hit"])))
            print(f"{name} {arm} " + " ".join("{}+-{}".format(*map(num, mean_sd(per[arm][m]))) for m in METRICS)
                  + f" {hit}")
        pairs = (("B_map", "A_memoryless"), ("C_wrongstage", "B_map")) if len(arms) == 3 else (("B_map", "A_memoryless"),)
        for a, b in pairs:
            for m in METRICS:
                print(f"{name} paired {a[0]}-{b[0]} {m}: {verdict(per[a][m], per[b][m])}")
        if len(arms) == 2:
            print(f"{name}: C_wrongstage not run (one stage, no neighbouring stage to mismatch)")
    print("ambiguous_long: stages 1 and 3 (and 2 and 4) share one look, so the memoryless base cannot tell them apart")
    print("distinct_long: the look already names the stage, so memory adds little and the gap stays within seed noise")
    print("single_stage: one stage, one prompt; retrieval cannot pick anything else")
    print("noisy_retrieval: state noise lowers B's retrieval hit rate and shrinks its gain over A")
    print("C_wrongstage: a neighbouring stage's prompt and reference pull the arm to the wrong goal; fewer steps there mean earlier failure")
    print("No winner declared; MAP-VLA LIBERO / real-robot gains 以论文为准; pi0 weights / GPU 本页未运行")


if __name__ == "__main__":
    main()
