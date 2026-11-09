#!/usr/bin/env python3
"""CoT-VLA-style visual chain of thought: predict a subgoal state, then a short action chunk.

Synthetic, stdlib only.  Not DreamGen's inverse-dynamics labelling (Month 9),
not TraceVLA's drawn traces, not MAP-VLA memory prompts (Month 10), not
WorldVLA.  Real CoT-VLA (7B VILA-U, 256 image tokens per subgoal) / GPU:
本页未运行.  Paper numbers are 以论文为准 (arXiv 2503.22020).

World: a 1-D track with cells 0..W-1 and a task = an ordered list of waypoints.
The observation (the stand-in "image") is (cell, stage); stage counts waypoints
already reached.  An episode succeeds if every waypoint is reached in order
within T_MAX steps.  Actions are -1, 0, +1, executed as chunks of M actions;
after each chunk the policy observes again (closed loop).  Discrete grid moves:
there is no time-step integration.
Data, all from one noisy demonstrator (with probability EPS it takes a random action):
    action demos D_r   (cell, stage, actions) for the test task: K_ACT of them,
                       plus REST demos of other tasks on the same track
    action-less videos D_v  (cell, stage) sequences of the test task: K_VID of them
Arms (each predicts one chunk of M actions per observation):
    A_direct      count table (task, cell, stage) -> next M actions, from D_r of the task
    B_cot         subgoal table (task, cell, stage) -> state N_AHEAD steps later (cut at the first
                  stage change, so a subgoal never skips a waypoint), from D_r and D_v of the task; then a task-agnostic action table (direction to subgoal) -> action,
                  learned from all D_r on the track; the subgoal is refreshed every chunk
    C_cot_stale   B's two tables, but the subgoal is refreshed only every STALE-th chunk
Unseen keys: both fall back to the task's most common demo action: A repeats it
for the chunk, B/C put the subgoal N_AHEAD cells that way.
Common random numbers: per (regime, seed) the task, the demos, the videos and
the start cells are drawn once and shared by all three arms.
Tokens per episode count the decoded tokens: an action is 7 tokens and a
subgoal image 256 tokens, the paper's sizes; this is a cost count, not a timing.
"""
import math
import random
from collections import Counter

SEEDS = (0, 1, 2, 3, 4)
W = 24                    # track cells
M = 4                     # action chunk length
N_AHEAD = 4               # subgoal horizon in steps
STALE = 2                 # C refreshes its subgoal every 2nd chunk
EPS = 0.2                 # demonstrator random-action rate
T_MAX = 60                # step budget per episode
TESTS = 40                # test episodes per seed (shared start cells)
REST = 30                 # action demos of other tasks on the same track
TOK_ACTION, TOK_IMAGE = 7, 256
NUM_ZERO = 1e-9           # |m| and sd both below this: floating-point residue, not a gap

# name: (waypoints per task, action demos of the test task K_ACT, videos of the test task K_VID)
REGIMES = {
    "multi_stage_video": (3, 1, 30),
    "multi_stage_no_video": (3, 1, 0),
    "multi_stage_action_rich": (3, 30, 30),
    "single_reach": (1, 30, 30),
}
ARMS = ("A_direct", "B_cot", "C_cot_stale")


def sign(x):
    return (x > 0) - (x < 0)


def make_task(rng, n_way):
    pts, prev = [], rng.randrange(W)
    for _ in range(n_way):
        nxt = prev
        while abs(nxt - prev) < 5:
            nxt = rng.randrange(W)
        pts.append(nxt)
        prev = nxt
    return tuple(pts)


def demo(rng, task, start):
    """Noisy demonstrator; returns states (cell, stage) and the action taken in each state."""
    cell, stage, states, acts = start, 0, [], []
    for _ in range(T_MAX):
        if stage == len(task):
            break
        a = sign(task[stage] - cell) if rng.random() >= EPS else rng.choice((-1, 0, 1))
        states.append((cell, stage))
        acts.append(a)
        cell = min(W - 1, max(0, cell + a))
        if cell == task[stage]:
            stage += 1
    states.append((cell, stage))
    return states, acts


def shared_draws(regime, seed):
    """Common random numbers: one task, one data set, one list of start cells for all arms."""
    n_way, k_act, k_vid = REGIMES[regime]
    rng = random.Random(f"{regime}/{seed}")
    task = make_task(rng, n_way)
    own = [demo(rng, task, rng.randrange(W)) for _ in range(k_act)]
    others = []
    for _ in range(REST):
        other = make_task(rng, n_way)
        others.append(demo(rng, other, rng.randrange(W)))
    videos = [demo(rng, task, rng.randrange(W))[0] for _ in range(k_vid)]
    starts = [rng.randrange(W) for _ in range(TESTS)]
    return {"task": task, "own": own, "others": others, "videos": videos, "starts": starts}


def fit(d):
    chunk = {}
    for states, acts in d["own"]:
        for i in range(len(acts)):
            seq = tuple(acts[i:i + M]) + (0,) * max(0, i + M - len(acts))
            chunk.setdefault(states[i], Counter())[seq] += 1
    prior = Counter(a for _, acts in d["own"] for a in acts)
    fallback = (prior.most_common(1)[0][0] if prior else 0,) * M
    sub = {}
    for states in [s for s, _ in d["own"]] + d["videos"]:
        for i in range(len(states) - 1):
            j = min(i + N_AHEAD, len(states) - 1)
            for jj in range(i + 1, j + 1):      # never look past the first stage change
                if states[jj][1] != states[i][1]:
                    j = jj
                    break
            sub.setdefault(states[i], Counter())[states[j]] += 1
    toward = {}
    for states, acts in d["own"] + d["others"]:
        for i, a in enumerate(acts):
            j = min(i + N_AHEAD, len(states) - 1)
            toward.setdefault(sign(states[j][0] - states[i][0]), Counter())[a] += 1
    act_of = {k: c.most_common(1)[0][0] for k, c in toward.items()}
    return ({k: c.most_common(1)[0][0] for k, c in chunk.items()}, fallback,
            {k: c.most_common(1)[0][0] for k, c in sub.items()}, act_of)


def run(regime, seed, arm):
    d = shared_draws(regime, seed)
    task = d["task"]
    chunk, fallback, sub, act_of = fit(d)
    wins, steps_used, tokens = 0, 0, 0
    for start in d["starts"]:
        cell, stage, t, k, goal = start, 0, 0, 0, None
        while stage < len(task) and t < T_MAX:
            obs = (cell, stage)
            if arm == "A_direct":
                plan = chunk.get(obs, fallback)
                tokens += TOK_ACTION * M
            else:
                if goal is None or arm == "B_cot" or k % STALE == 0:
                    goal = sub.get(obs, (min(W - 1, max(0, cell + N_AHEAD * fallback[0])), stage))
                    tokens += TOK_IMAGE
                tokens += TOK_ACTION * M
                plan = []
                c = cell
                for _ in range(M):
                    a = act_of.get(sign(goal[0] - c), 0) if c != goal[0] else 0
                    plan.append(a)
                    c = min(W - 1, max(0, c + a))
            k += 1
            for a in plan:
                if stage == len(task) or t >= T_MAX:
                    break
                cell = min(W - 1, max(0, cell + a))
                t += 1
                if cell == task[stage]:
                    stage += 1
        wins += stage == len(task)
        steps_used += t
    return {"succ": 100.0 * wins / TESTS, "steps": steps_used / TESTS, "tok": tokens / TESTS}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
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


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def cell_str(xs):
    mu, sd = mean_sd(xs)
    return f"{num(mu)}+-{num(sd)}"


def main():
    print("Synthetic CoT-VLA-style subgoal toy; count-table policies, no training loop, no time-step integration; arms differ only in how a chunk is chosen; shared task / demos / videos / starts")
    print(f"track W={W}, chunk M={M}, subgoal N_AHEAD={N_AHEAD}, stale refresh every {STALE} chunks, demonstrator EPS={EPS}, T_MAX={T_MAX}, tests={TESTS}, other-task demos={REST}, seeds={len(SEEDS)}")
    print(f"tokens: action {TOK_ACTION}, subgoal image {TOK_IMAGE} (paper sizes, a cost count)")
    res = {r: {a: [run(r, s, a) for s in SEEDS] for a in ARMS} for r in REGIMES}
    print("regime arm success_% steps_used tokens_per_episode  (mean+-sd over seeds; steps capped at T_MAX)")
    for r, (n_way, k_act, k_vid) in REGIMES.items():
        print(f"{r} (waypoints {n_way}; action demos of the task {k_act}; videos of the task {k_vid})")
        for a in ARMS:
            print(f"  {a} " + " ".join(cell_str([x[m] for x in res[r][a]]) for m in ("succ", "steps", "tok")))
        for x, y in (("B_cot", "A_direct"), ("C_cot_stale", "B_cot")):
            for m in ("succ", "steps", "tok"):
                xs, ys = [v[m] for v in res[r][x]], [v[m] for v in res[r][y]]
                print(f"  paired {x[0]}-{y[0]} {m}: {verdict(xs, ys)}")
    print("No winner declared: a subgoal learned from action-less video helps when action demos are scarce; it costs 256 tokens per chunk and goes stale if not refreshed")
    print("Real CoT-VLA / GPU: 本页未运行; paper numbers 以论文为准")


if __name__ == "__main__":
    main()
