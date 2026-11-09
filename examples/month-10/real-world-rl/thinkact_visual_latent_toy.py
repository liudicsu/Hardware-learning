#!/usr/bin/env python3
"""Synthetic ThinkAct-style toy: direct policy vs plan-latent policy vs a scrambled latent. Stdlib only.

A 9 x 9 grid; a task is an ordered list of target cells (stages), possibly revisiting a cell.
The stage counter advances when the robot stands on the next target. A camera shows the stage
indicator with probability 1 - Q_HIDE per step; otherwise the observation is the cell only, so
a revisited cell looks the same in different stages (perceptual aliasing).
Shared demos: N_DEMO expert episodes per trial (x first, then y; each step slips to a random
move with probability SLIP) give the labels for every learned table.

Arms (same task, same demos, same slip draws, same hide draws):
  A_direct   obs -> action: majority demo action for (cell, visible stage or "hidden")
  B_latent   a reasoner stand-in writes a plan latent = the remaining targets (each cell jittered
             to a neighbour with probability P_PLAN, a hallucination stand-in); the action model is
             the majority demo action for (cell, current plan point) and moves to the next point when
             it stands on one; the latent is rewritten every REFRESH steps when the stage is visible
             (REFRESH = 0: written once at the start)
  C_scrambled  B's action model with the same targets in a rotated order (t_2, ..., t_K, t_1);
             with one stage the rotation is the identity, so C equals B there by construction
  The first version's C used the targets of a different task in the same scene; its (cell, point)
  keys never occur in the demos, so it fell back to A's hidden-stage table; it is printed as an
  alternative.
An unseen key falls back to the (cell, hidden) majority for every arm, then to "stay"; the first
version let B stay at once and is printed as the fallback alternative.
Plan metrics for a latent (points scaled to [0, 1]^2 as in ThinkAct eq. 1-3):
  r_goal = (f(p_1, q_1) + f(p_K, q_K)) / 2 with f = max(0, 1 - |p - q|^2)
  r_traj = max(0, 1 - DTW(p, q)) (DTW: sum of Euclidean distances along the best alignment)
  r_visual = 0.5 r_goal + 0.5 r_traj; endpoint error = |p_K - q_K| in cells
The latent is a list of stage targets, not ThinkAct's 8 gripper points; no MLLM, no GRPO, no DiT.
No integration step: the grid moves one cell per step, nothing is stepped in continuous time.
Common random numbers: per (regime, seed, trial) the scene, the tasks, the demos, the plan jitter,
the slip draws and the hide draws are drawn once and shared by every arm.
Metrics per trial, averaged over TRIALS per seed: stage (share of stages completed), full
(all stages completed), endpoint, r_visual (latent arms only).
Labels: tie = identical on every seed; numerically zero = |paired mean| and sd both < 1e-9
(effectively a tie, no sign count); |m| <= sd = near-tie; |m| > sd = consistent gap (small if
|m| < 20 % of the smaller arm mean, else clear), with a sign count.
Qwen2.5-VL / LIBERO / SimplerEnv / a GPU: 本页未运行. Paper numbers: 以论文为准.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
TRIALS = 40
SIZE = 9
N_DEMO = 20
SLIP = 0.1
MOVES = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))
NUM_ZERO = 1e-9
ARMS = ("A_direct", "B_latent", "C_scrambled")
# name: (stage pattern, Q_HIDE, P_PLAN, REFRESH, drop, HIDE_BLOCK)
# HIDE_BLOCK = steps per hide draw (1 = a fresh draw every step); the two *_block regimes were
# added after the per-step regimes had run (see the en / zh prose); every regime is printed.
REGIMES = {
    "single_step": ("P", 0.5, 0.1, 0, False, 1),
    "multi_stage": ("PQP", 0.5, 0.1, 0, False, 1),
    "ambiguous": ("PQPQ", 0.8, 0.1, 0, False, 1),
    "multi_stage_block": ("PQP", 0.5, 0.1, 0, False, 8),
    "ambiguous_block": ("PQPQ", 0.8, 0.1, 0, False, 8),
    "noisy_plan": ("PQP", 0.5, 0.5, 0, False, 1),
    "drop_dense": ("PQP", 0.5, 0.1, 5, True, 1),
    "drop_sparse": ("PQP", 0.5, 0.1, 0, True, 1),
}


def cell(rng):
    return (rng.randrange(SIZE), rng.randrange(SIZE))


def expert(c, t):
    if c[0] != t[0]:
        return 1 if t[0] > c[0] else 2
    if c[1] != t[1]:
        return 3 if t[1] > c[1] else 4
    return 0


def step(c, a):
    return (min(SIZE - 1, max(0, c[0] + MOVES[a][0])), min(SIZE - 1, max(0, c[1] + MOVES[a][1])))


def world(regime, seed, trial):
    pattern, q_hide, p_plan, refresh, drop, block = REGIMES[regime]
    rng = random.Random(f"{regime}-{seed}-{trial}")
    start = cell(rng)
    names = sorted(set(pattern))
    while True:
        spots = {n: cell(rng) for n in names}
        other = {n: cell(rng) for n in names}
        allc = list(spots.values()) + list(other.values()) + [start]
        if len(set(allc)) == len(allc):
            break
    task = [spots[n] for n in pattern]
    wrong = [other[n] for n in pattern]
    horizon = 2 * sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip([start] + task, task)) + 6
    demos = []
    for _ in range(N_DEMO):
        c, s, rec = start, 0, []
        for _ in range(horizon):
            if s == len(task):
                break
            a = expert(c, task[s])
            rec.append((c, s, rng.random() < q_hide, task[s], a))
            c = step(c, rng.randrange(5) if rng.random() < SLIP else a)
            if c == task[s]:
                s += 1
        demos.append(rec)
    jit = [[(rng.random(), rng.randrange(4)) for _ in range(len(task))] for _ in range(horizon + 1)]
    slips = [(rng.random(), rng.randrange(5)) for _ in range(horizon)]
    draws = [rng.random() < q_hide for _ in range(horizon)]
    hides = [draws[t // block] for t in range(horizon)]
    t_drop = rng.randrange(horizon // 3, 2 * horizon // 3) if drop else -1
    return start, task, wrong, horizon, demos, jit, slips, hides, t_drop, p_plan, refresh


def majority(table, key):
    votes = table.get(key)
    if not votes:
        return None
    return max(range(5), key=lambda a: (votes[a], -a))


def tables(demos):
    ta, tb = {}, {}
    for rec in demos:
        for c, s, hid, tgt, a in rec:
            for key in ((c, s if not hid else -1), (c, -1)):
                ta.setdefault(key, [0] * 5)[a] += 1
            tb.setdefault((c, tgt), [0] * 5)[a] += 1
    return ta, tb


def jitter(points, draws, p_plan):
    out = []
    for p, (u, d) in zip(points, draws):
        if u < p_plan:
            m = MOVES[1 + d]
            p = (min(SIZE - 1, max(0, p[0] + m[0])), min(SIZE - 1, max(0, p[1] + m[1])))
        out.append(p)
    return out


def dtw(p, q):
    inf = float("inf")
    d = [[inf] * (len(q) + 1) for _ in range(len(p) + 1)]
    d[0][0] = 0.0
    for i in range(1, len(p) + 1):
        for j in range(1, len(q) + 1):
            c = math.dist(p[i - 1], q[j - 1])
            d[i][j] = c + min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])
    return d[len(p)][len(q)]


def plan_scores(plan, task):
    p = [(x / (SIZE - 1), y / (SIZE - 1)) for x, y in plan]
    q = [(x / (SIZE - 1), y / (SIZE - 1)) for x, y in task]
    f = lambda a, b: max(0.0, 1.0 - math.dist(a, b) ** 2)
    r_goal = 0.5 * (f(p[0], q[0]) + f(p[-1], q[-1]))
    r_traj = max(0.0, 1.0 - dtw(p, q))
    return math.dist(plan[-1], task[-1]), 0.5 * r_goal + 0.5 * r_traj


def rotate(points):
    return points[1:] + points[:1]


def latent_source(arm, task, wrong):
    if arm == "B_latent":
        return task
    if arm == "C_scrambled":
        return rotate(task)
    return wrong


def run(arm, regime, seed, trial, fallback="table"):
    start, task, wrong, horizon, demos, jit, slips, hides, t_drop, p_plan, refresh = world(regime, seed, trial)
    ta, tb = tables(demos)
    c, s = start, 0
    source = latent_source(arm, task, wrong)
    plan = jitter(source, jit[0], p_plan)
    endpoint, r_vis = plan_scores(plan, task)
    ptr = 0
    for t in range(horizon):
        if s == len(task):
            break
        if t == t_drop and s > 0:
            s -= 1
        if arm == "A_direct":
            a = majority(ta, (c, -1 if hides[t] else s))
            a = majority(ta, (c, -1)) if a is None and fallback == "table" else a
        else:
            if refresh and t > 0 and t % refresh == 0 and not hides[t]:
                remaining = latent_source(arm, task[s:], wrong[s:]) or source[-1:]
                plan, ptr = jitter(remaining, jit[t], p_plan), 0
            a = majority(tb, (c, plan[ptr])) if ptr < len(plan) else None
            a = majority(ta, (c, -1)) if a is None and fallback == "table" else a
        a = 0 if a is None else a
        u, r = slips[t]
        c = step(c, r if u < SLIP else a)
        if c == task[s]:
            s += 1
        if arm != "A_direct" and ptr < len(plan) and c == plan[ptr]:
            ptr += 1
    out = {"stage": s / len(task), "full": 1.0 if s == len(task) else 0.0}
    out["endpoint"] = endpoint if arm != "A_direct" else 0.0
    out["r_visual"] = r_vis if arm != "A_direct" else 0.0
    return out


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


KEYS = ("stage", "full", "endpoint", "r_visual")


def main():
    print("Synthetic ThinkAct-style toy; grid stages, plan latent = remaining targets; not Qwen2.5-VL / LIBERO / SimplerEnv")
    print(f"seeds={len(SEEDS)} trials={TRIALS} grid={SIZE} demos={N_DEMO} slip={SLIP}; no integration step (one cell per step); A has no latent, so its endpoint and r_visual print 0")
    print("regime arm stage full endpoint r_visual  (mean+-sd over seeds of per-seed trial means)")
    for regime, (pattern, q_hide, p_plan, refresh, drop, block) in REGIMES.items():
        print(f"{regime} (stages={len(pattern)} pattern={pattern}, q_hide={q_hide}, hide_block={block}, p_plan={p_plan}, refresh={refresh or 'start only'}, drop={drop})")
        res = {}
        for arm in ARMS:
            res[arm] = []
            for seed in SEEDS:
                rs = [run(arm, regime, seed, t) for t in range(TRIALS)]
                res[arm].append({k: sum(r[k] for r in rs) / TRIALS for k in KEYS})
            cells = " ".join("{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in KEYS)
            print(f"  {arm} {cells}")
        for x, y in (("B_latent", "A_direct"), ("C_scrambled", "B_latent"), ("C_scrambled", "A_direct")):
            for k in ("stage", "full"):
                print(f"  paired {x[0]}-{y[0]} {k}: {verdict([r[k] for r in res[x]], [r[k] for r in res[y]])}")
    print("fallback alternative (first version: an unseen (cell, plan point) key makes B stay; A keeps its (cell, hidden) fallback); paired B-A full")
    for regime in REGIMES:
        xa = [sum(run("A_direct", regime, seed, t)["full"] for t in range(TRIALS)) / TRIALS for seed in SEEDS]
        xb = [sum(run("B_latent", regime, seed, t, "stay")["full"] for t in range(TRIALS)) / TRIALS for seed in SEEDS]
        print(f"  {regime}: {verdict(xb, xa)}")
    print("C alternative (first version: the latent of a different task in the same scene); paired C-B full")
    for regime in REGIMES:
        xb = [sum(run("B_latent", regime, seed, t)["full"] for t in range(TRIALS)) / TRIALS for seed in SEEDS]
        xc = [sum(run("C_wrong_task", regime, seed, t)["full"] for t in range(TRIALS)) / TRIALS for seed in SEEDS]
        print(f"  {regime}: {verdict(xc, xb)}")
    print("No winner declared: the latent carries stage context the camera can hide; a hallucinated or stale latent costs it back")
    print("Real ThinkAct (Qwen2.5-VL 7B + DiT policy, GRPO), LIBERO, SimplerEnv, a GPU: 本页未运行; Huang et al. results 以论文为准")


if __name__ == "__main__":
    main()
