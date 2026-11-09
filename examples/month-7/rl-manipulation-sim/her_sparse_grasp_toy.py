#!/usr/bin/env python3
"""Synthetic Hindsight Experience Replay toy on the reach-grasp grid. Stdlib only.

The MDP is the one in reward_shaping.py, made goal-conditioned: state (x, y, grip) on an
N x N grid, actions N, S, E, W, CLOSE (CLOSE sets grip = 1 and it stays closed); the goal g
is a cell, and the episode succeeds when the gripper is closed on g. The predicate
f_g(s) = [cell(s) == g and grip(s) == 1]; the achieved goal of a state with grip = 1 is its
cell (states with grip = 0 achieve no goal).

Q is a table indexed by the goal-relative offset (x - gx, y - gy) and grip, a stand-in for the
goal-conditioned network of the paper: what is learned about one goal carries over to every
goal at the same offset. This representation was chosen after the first run, which indexed
the table by (goal, cell, grip); that run is printed as an alternative.

Arms (identical representation, hyperparameters and replay budget):
  A_sparse  reward 1 on success, 0 otherwise; replay without relabelling
  B_her     the same sparse reward; replay with the "future" strategy (Andrychowicz et al.):
            with probability K / (K + 1) a sampled transition is replayed with a goal achieved
            later in the same episode, its reward and termination recomputed for that goal
  C_dense   reward_shaping.py's dense reward (-0.1 Manhattan distance, +0.5 grip on the goal
            cell, +5 on success); replay without relabelling

Every arm learns only from replay: after each episode, UPDATES transitions are sampled
uniformly from all stored episodes and backed up with Q-learning (ALPHA, GAMMA).
Common random numbers: per (regime, seed) the start cell and goal of every episode and the
two exploration draws of every (episode, step) are drawn once and shared by all arms; the
replay-sampling stream is seeded identically per arm but is consumed differently because the
buffers differ. No integration step: the environment is a discrete grid.
Regimes: near_goal (goals within 2 cells), fixed_goal (reward_shaping.py's single goal (4, 3)),
far_goals (x + y >= 6 on 6 x 6), big_grid (x + y >= 12 on 10 x 10; added after the first run,
the 8 x 8 version tried before it is printed as an alternative).
Metrics per seed: final = greedy success over every (start, goal) pair of the regime after
the last episode; auc = mean greedy success over the checkpoints every EVAL_EVERY episodes
(sample efficiency); train = success share over the last 50 training episodes.
Labels: tie = identical on every seed; numerically zero = |paired mean| and sd both < 1e-9
(effectively a tie, no sign count); |m| <= sd = near-tie; |m| > sd = consistent gap (small if
|m| < 20 % of the smaller arm mean, else clear), with a sign count.
ManiSkill3 / SB3 HER / DDPG / a GPU: 本页未运行. Paper results: 以原文为准.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
N_ACTIONS = 5  # N S E W CLOSE
ALPHA = 0.35
GAMMA = 0.95
EPS_START, EPS_END = 0.5, 0.05
MAX_STEPS = 30
UPDATES = 64
K_FUTURE = 4
EVAL_EVERY = 50
NUM_ZERO = 1e-9
ARMS = ("A_sparse", "B_her", "C_dense")
# name: (grid N, episodes, start cells, goal cells)
REGIMES = {
    "near_goal": (6, 400, [(0, 0), (0, 1), (1, 0), (1, 1)], [(x, y) for x in range(3) for y in range(3)]),
    "fixed_goal": (6, 400, [(0, 0), (0, 1), (1, 0), (1, 1)], [(4, 3)]),
    "far_goals": (6, 400, [(0, 0), (0, 1), (1, 0), (1, 1)], [(x, y) for x in range(6) for y in range(6) if x + y >= 6]),
    "big_grid": (10, 400, [(0, 0), (0, 1), (1, 0), (1, 1)], [(x, y) for x in range(10) for y in range(10) if x + y >= 12]),
}
# big_grid was added after the first run; the 8 x 8 version tried before it is printed as an alternative
ALT_BIG = (8, 400, [(0, 0), (0, 1), (1, 0), (1, 1)], [(x, y) for x in range(8) for y in range(8) if x + y >= 9])
REPR = "relative"  # Q indexed by the goal-relative offset (chosen after the first run; ALT_REPR printed)
ALT_REPR = "absolute"  # Q indexed by (goal, cell, grip): the first run's table


def key(goal, cell, grip, repr_=REPR):
    if repr_ == "relative":
        return (cell[0] - goal[0], cell[1] - goal[1], grip)
    return (goal, cell, grip)


def step(n, cell, grip, a, goal, dense):
    x, y = cell
    nx, ny, ng = x, y, grip
    if a == 0:
        ny = max(0, y - 1)
    elif a == 1:
        ny = min(n - 1, y + 1)
    elif a == 2:
        nx = min(n - 1, x + 1)
    elif a == 3:
        nx = max(0, x - 1)
    else:
        ng = 1
    return (nx, ny), ng, reward((nx, ny), ng, goal, dense)


def reward(cell, grip, goal, dense):
    """Reward and termination of arriving in (cell, grip) when pursuing goal."""
    success = cell == goal and grip == 1
    if not dense:
        return (1.0 if success else 0.0), success
    r = -0.1 * (abs(cell[0] - goal[0]) + abs(cell[1] - goal[1]))
    if cell == goal:
        r += 0.5 * grip
    if success:
        r += 5.0
    return r, success


def shared_draws(regime, seed):
    """Common random numbers: episode (start, goal) and exploration draws, shared by every arm."""
    n, episodes, starts, goals = REGIMES[regime] if regime in REGIMES else ALT_BIG
    rng = random.Random(f"{regime}-{seed}")
    eps = [(rng.choice(starts), rng.choice(goals)) for _ in range(episodes)]
    explore = [[(rng.random(), rng.randrange(N_ACTIONS)) for _ in range(MAX_STEPS)] for _ in range(episodes)]
    return eps, explore


def greedy(row):
    m = max(row)
    return row.index(m)


def evaluate(q, regime, repr_=REPR):
    n, _, starts, goals = REGIMES[regime] if regime in REGIMES else ALT_BIG
    ok = 0
    for s0 in starts:
        for g in goals:
            cell, grip = s0, 0
            for _ in range(MAX_STEPS):
                a = greedy(q[key(g, cell, grip, repr_)])
                cell, grip, (_, done) = step(n, cell, grip, a, g, False)
                if done:
                    ok += 1
                    break
    return ok / (len(starts) * len(goals))


def train(arm, regime, seed, k_future=K_FUTURE, repr_=REPR):
    n, episodes, starts, goals = REGIMES[regime] if regime in REGIMES else ALT_BIG
    cells = [(x, y) for x in range(n) for y in range(n)]
    q = {key(g, c, gr, repr_): [0.0] * N_ACTIONS for g in cells for c in cells for gr in (0, 1)}
    eps_draws, explore = shared_draws(regime, seed)
    replay_rng = random.Random(f"replay-{regime}-{seed}")
    dense = arm == "C_dense"
    her = arm == "B_her"
    buffer, curve, train_ok = [], [], []
    for ep in range(episodes):
        start, goal = eps_draws[ep]
        eps = EPS_START + (EPS_END - EPS_START) * ep / max(1, episodes - 1)
        cell, grip, traj, ok = start, 0, [], False
        for t in range(MAX_STEPS):
            u, ra = explore[ep][t]
            a = ra if u < eps else greedy(q[key(goal, cell, grip, repr_)])
            ncell, ngrip, (_, done) = step(n, cell, grip, a, goal, dense)
            traj.append((cell, grip, a, ncell, ngrip))
            cell, grip = ncell, ngrip
            if done:
                ok = True
                break
        train_ok.append(ok)
        buffer.append((goal, traj))
        for _ in range(UPDATES):
            g, tr = buffer[replay_rng.randrange(len(buffer))]
            i = replay_rng.randrange(len(tr))
            c, gr, a, nc, ngr = tr[i]
            if her and replay_rng.random() < k_future / (k_future + 1.0):
                j = replay_rng.randrange(i, len(tr))
                if tr[j][4] == 1:  # a goal is achieved only with the gripper closed
                    g = tr[j][3]
            r, done = reward(nc, ngr, g, dense)
            target = r if done else r + GAMMA * max(q[key(g, nc, ngr, repr_)])
            row = q[key(g, c, gr, repr_)]
            row[a] += ALPHA * (target - row[a])
        if (ep + 1) % EVAL_EVERY == 0:
            curve.append(evaluate(q, regime, repr_))
    return {"final": curve[-1], "auc": sum(curve) / len(curve), "train": sum(train_ok[-50:]) / 50.0}


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


KEYS = ("final", "auc", "train")


def main():
    print("Synthetic HER toy; goal-conditioned tabular Q on the reach-grasp grid; shared episodes / exploration draws; not SB3 / ManiSkill")
    print(f"seeds={len(SEEDS)} alpha={ALPHA} gamma={GAMMA} eps {EPS_START}->{EPS_END} max_steps={MAX_STEPS} "
          f"updates/episode={UPDATES} future k={K_FUTURE} (relabel share {K_FUTURE / (K_FUTURE + 1):.2f}) eval every {EVAL_EVERY}; no integration step (discrete grid)")
    print("regime arm final auc train  (mean+-sd over seeds)")
    for regime, (n, episodes, starts, goals) in REGIMES.items():
        print(f"{regime} (grid {n}x{n}, episodes={episodes}, {len(starts)} starts x {len(goals)} goals)")
        res = {arm: [train(arm, regime, seed) for seed in SEEDS] for arm in ARMS}
        for arm in ARMS:
            cells = " ".join("{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in KEYS)
            print(f"  {arm} {cells}")
        for x, y in (("B_her", "A_sparse"), ("B_her", "C_dense"), ("C_dense", "A_sparse")):
            for k in ("final", "auc"):
                print(f"  paired {x[0]}-{y[0]} {k}: {verdict([r[k] for r in res[x]], [r[k] for r in res[y]])}")
    print("alternatives (choices made after the first run; final / auc means over seeds):")
    for regime in REGIMES:
        res = {arm: [train(arm, regime, seed, repr_=ALT_REPR) for seed in SEEDS] for arm in ARMS}
        cells = " ".join(f"{arm} {num(mean_sd([r['final'] for r in res[arm]])[0])}/{num(mean_sd([r['auc'] for r in res[arm]])[0])}" for arm in ARMS)
        print(f"  Q indexed by (goal, cell, grip), {regime}: {cells}")
    res = {arm: [train(arm, "big_grid_8x8", seed) for seed in SEEDS] for arm in ARMS}
    cells = " ".join(f"{arm} {num(mean_sd([r['final'] for r in res[arm]])[0])}/{num(mean_sd([r['auc'] for r in res[arm]])[0])}" for arm in ARMS)
    print(f"  big_grid at 8x8 (goals x + y >= 9): {cells}")
    print("near_goal: random exploration already finds nearby goals, so relabelling adds little")
    print("fixed_goal / far_goals: sparse rarely sees a success; hindsight goals teach the goal-relative table to close on the goal")
    print("big_grid: exploration never reaches the far offsets, so there is nothing to relabel there; dense shaping still points the way")
    print("No winner declared: HER needs achieved goals near the ones you want; a good dense reward can match or beat it")
    print("Real ManiSkill3 / SB3 HER / DDPG runs: 本页未运行; Andrychowicz et al. results 以原文为准")


if __name__ == "__main__":
    main()
