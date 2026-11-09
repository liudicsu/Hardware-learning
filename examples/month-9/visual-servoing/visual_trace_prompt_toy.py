#!/usr/bin/env python3
"""Synthetic visual-trace prompting toy (TraceVLA-style input, NOT TraceVLA,
NOT IBVS, NOT a VLA). Stdlib only.

A 7x7 grid world is rendered as an image. A fixed "vision encoder" reads blob
coordinates from what is drawn:
  raw image   -> the goal offset from the end-effector (EE) when a goal is
                 drawn, otherwise the EE cell
  trace image -> offsets from the EE of the oldest and newest points of a
                 polyline drawn over the last TRACE_N frames of the EE (like an
                 overlaid point track)
Every arm is trained by the SAME k-nearest-neighbour behaviour cloning
(k=3, same demonstrations, same seeds) and differs only in its input:
  A_raw          current raw image only
  B_raw_trace    raw image + trace image (both, as TraceVLA feeds both)
  C_lagged_trace raw image + trace drawn from frames t-LAG-TRACE_N..t-LAG,
                 with tracker jitter (a point shifted by one cell w.p. JITTER)
The trace is computed only from past rendered frames; no arm sees the
expert's hidden direction variable or any pose the raw arm's images lack.
Tasks:
  wipe   sweep a row edge to edge; the current frame does not show the
         sweep direction (history matters)
  reach  move to a visible goal; the current frame is sufficient (Markov)
"""
import heapq
import math
import random

W = 7
TRACE_N = 3
LAG = 2
JITTER = 0.2
K = 3
N_DEMOS = 20
N_EVAL = 30
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_raw", "B_raw_trace", "C_lagged_trace")
ACTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0))
WIPE_T = 36
REACH_T = 16


def clamp(v):
    return min(max(v, 0), W - 1)


def encode(arm, hist, goal, rng):
    """Features read from the rendered images only. hist: EE cells, oldest first."""
    ee = hist[-1]
    feat = [goal[0] - ee[0], goal[1] - ee[1]] if goal else [ee[0], ee[1]]
    if arm == "A_raw":
        return tuple(feat)
    end = len(hist) - (LAG if arm == "C_lagged_trace" else 0)
    window = hist[max(0, end - 1 - TRACE_N):max(1, end)]
    pts = []
    for p in (window[0], window[-1]):
        if arm == "C_lagged_trace" and rng.random() < JITTER:
            dx, dy = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            p = (clamp(p[0] + dx), clamp(p[1] + dy))
        pts += [p[0] - ee[0], p[1] - ee[1]]
    return tuple(feat + pts)


def wipe_expert(state):
    (x, y), d = state
    if x + d < 0 or x + d >= W:
        d = -d
    return (d, 0), ((x, y), d)


def reach_expert(ee, goal):
    if ee[0] != goal[0]:
        return (1 if goal[0] > ee[0] else -1, 0)
    if ee[1] != goal[1]:
        return (0, 1 if goal[1] > ee[1] else -1)
    return (0, 0)


def demos(task, arm, rng_ep, rng_jit):
    data = []
    for _ in range(N_DEMOS):
        if task == "wipe":
            x, d = rng_ep.randrange(W), rng_ep.choice((-1, 1))
            hist, goal, state = [(x, 3)], None, ((x, 3), d)
            for _ in range(WIPE_T):
                act, state = wipe_expert(state)
                data.append((encode(arm, hist, goal, rng_jit), act))
                hist.append((clamp(hist[-1][0] + act[0]), 3))
                state = (hist[-1], state[1])
        else:
            ee = (rng_ep.randrange(W), rng_ep.randrange(W))
            goal = (rng_ep.randrange(W), rng_ep.randrange(W))
            hist = [ee]
            for _ in range(REACH_T):
                act = reach_expert(hist[-1], goal)
                data.append((encode(arm, hist, goal, rng_jit), act))
                if act == (0, 0):
                    break                      # one "stay" sample at the goal, then stop
                hist.append((clamp(hist[-1][0] + act[0]), clamp(hist[-1][1] + act[1])))
    return data


def knn(data, f):
    best = heapq.nsmallest(K, data, key=lambda r: (sum((a - b) ** 2 for a, b in zip(r[0], f)), ACTIONS.index(r[1])))
    votes = {}
    for _, a in best:
        votes[a] = votes.get(a, 0) + 1
    return max(ACTIONS, key=lambda a: (votes.get(a, 0), -ACTIONS.index(a)))


def evaluate(task, arm, data, rng_ep, rng_jit):
    scores, steps_used = [], []
    for _ in range(N_EVAL):
        if task == "wipe":
            x = rng_ep.randrange(W)
            rng_ep.choice((-1, 1))       # keep the episode stream aligned with demos
            hist, last_edge, strokes = [(x, 3)], None, 0
            for _ in range(WIPE_T):
                act = knn(data, encode(arm, hist, None, rng_jit))
                nx = clamp(hist[-1][0] + act[0])
                hist.append((nx, 3))
                edge = 0 if nx == 0 else (W - 1 if nx == W - 1 else None)
                if edge is not None and edge != last_edge:
                    if last_edge is not None:
                        strokes += 1
                    last_edge = edge
            scores.append(strokes)
        else:
            ee = (rng_ep.randrange(W), rng_ep.randrange(W))
            goal = (rng_ep.randrange(W), rng_ep.randrange(W))
            hist, done = [ee], None
            for t in range(REACH_T):
                if hist[-1] == goal:
                    done = t
                    break
                act = knn(data, encode(arm, hist, goal, rng_jit))
                hist.append((clamp(hist[-1][0] + act[0]), clamp(hist[-1][1] + act[1])))
            if done is None and hist[-1] == goal:
                done = REACH_T
            scores.append(1.0 if done is not None else 0.0)
            steps_used.append(done if done is not None else REACH_T)
    return scores, steps_used


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def main():
    print("Synthetic visual-trace prompting toy; 7x7 grid, blob-coordinate encoder, k-NN BC; not TraceVLA / not a VLA")
    print(f"k={K} demos={N_DEMOS} eval_episodes={N_EVAL} trace_frames={TRACE_N} lag={LAG} jitter={JITTER} seeds={len(SEEDS)}")
    print("shared per seed: demo episodes, eval starts/goals, jitter stream; trace drawn only from past frames")
    expert_strokes = (WIPE_T - (W - 1)) / (W - 1)
    print(f"wipe expert reference: about {expert_strokes:.1f} edge-to-edge strokes in {WIPE_T} steps")
    print("task arm score features (mean+-sd over seeds; wipe score = strokes/episode, reach score = success rate)")
    for task in ("wipe", "reach"):
        for arm in ARMS:
            means, steps = [], []
            for seed in SEEDS:
                data = demos(task, arm, random.Random(10 + seed), random.Random(20 + seed))
                sc, st = evaluate(task, arm, data, random.Random(30 + seed), random.Random(40 + seed))
                means.append(sum(sc) / len(sc))
                if st:
                    steps.append(sum(st) / len(st))
            m, s = mean_sd(means)
            nfeat = len(encode(arm, [(0, 0)] * 6, (0, 0) if task == "reach" else None, random.Random(0)))
            extra = ""
            if steps:
                sm, ss = mean_sd(steps)
                extra = f" steps={sm:.2f}+-{ss:.2f}"
            print(f"{task} {arm} {m:.3f}+-{s:.3f} {nfeat}{extra}")
    print("No winner is declared: history helps only where the frame hides it, and extra inputs cost data")
    print("TraceVLA SimplerEnv / WidowX gains: 以论文为准; OpenVLA weights / GPU / real robot: 本页未运行")


if __name__ == "__main__":
    main()
