#!/usr/bin/env python3
"""Sparse vs dense reward shaping on a discrete reach–grasp MDP (stdlib).

Lesson 7.2 used a clipped-ratio PPO toy for a 1-D reach. Here the task adds a
gripper channel: reach a cube, then close. We compare **sparse** (terminal +1)
vs **dense** (distance + grip shaping) under identical tabular Q-learning so the
success gap is seed-stable on CPU.

ManiSkill3 ``PickCubeSO100-v1`` / SB3 SAC are the GPU / off-policy counterparts
described in the MDX — this file does not import them (「本页未强制」).

State bins: x∈[0,1], y∈[0,1], grip∈{0,1}  →  N x N x 2
Actions: 5 moves {N,S,E,W,CLOSE}
Success: cell contains the goal and grip==1
"""
from __future__ import annotations

import random
from typing import Literal

SEED = 7
N = 6
GOAL = (4, 3)  # grid cell
EPISODES = 400
MAX_STEPS = 30
ALPHA = 0.35
GAMMA = 0.95
EPS_START = 0.5
EPS_END = 0.05

Action = Literal[0, 1, 2, 3, 4]  # N S E W CLOSE
N_ACTIONS = 5


def idx(x: int, y: int, g: int) -> int:
    return (g * N + y) * N + x


def clip_cell(v: int) -> int:
    return max(0, min(N - 1, v))


def step(x: int, y: int, g: int, a: int, dense: bool):
    nx, ny, ng = x, y, g
    if a == 0:
        ny = clip_cell(y - 1)
    elif a == 1:
        ny = clip_cell(y + 1)
    elif a == 2:
        nx = clip_cell(x + 1)
    elif a == 3:
        nx = clip_cell(x - 1)
    elif a == 4:
        ng = 1
    success = (nx, ny) == GOAL and ng == 1
    if dense:
        # Manhattan distance penalty + grip bonus on goal cell + terminal
        d = abs(nx - GOAL[0]) + abs(ny - GOAL[1])
        r = -0.1 * d
        if (nx, ny) == GOAL:
            r += 0.5 * ng
        if success:
            r += 5.0
    else:
        r = 1.0 if success else 0.0
    return nx, ny, ng, r, success


def train(dense: bool, seed: int = SEED):
    rng = random.Random(seed)
    q = [[0.0] * N_ACTIONS for _ in range(N * N * 2)]
    successes: list[int] = []
    returns: list[float] = []
    for ep in range(EPISODES):
        x = rng.randint(0, 1)
        y = rng.randint(0, 1)
        g = 0
        ep_ret = 0.0
        ok = False
        eps = EPS_START + (EPS_END - EPS_START) * (ep / max(1, EPISODES - 1))
        for _ in range(MAX_STEPS):
            s = idx(x, y, g)
            if rng.random() < eps:
                a = rng.randrange(N_ACTIONS)
            else:
                row = q[s]
                m = max(row)
                # tie-break deterministically by lowest index among maxima
                cands = [i for i, v in enumerate(row) if v == m]
                a = cands[0]
            nx, ny, ng, r, success = step(x, y, g, a, dense=dense)
            ns = idx(nx, ny, ng)
            best_next = max(q[ns])
            q[s][a] = (1 - ALPHA) * q[s][a] + ALPHA * (r + GAMMA * best_next)
            ep_ret += r
            x, y, g = nx, ny, ng
            if success:
                ok = True
                break
        successes.append(1 if ok else 0)
        returns.append(ep_ret)
    window = 50
    last_s = successes[-window:]
    last_r = returns[-window:]
    return {
        "mean_return": sum(last_r) / window,
        "success_rate": sum(last_s) / window,
        "last_ok": sum(last_s),
        "q": q,
    }


def greedy_rollout(q, seed: int = 99) -> bool:
    rng = random.Random(seed)
    x = rng.randint(0, 1)
    y = rng.randint(0, 1)
    g = 0
    for _ in range(MAX_STEPS):
        s = idx(x, y, g)
        row = q[s]
        m = max(row)
        a = min(i for i, v in enumerate(row) if v == m)
        x, y, g, _, success = step(x, y, g, a, dense=True)
        if success:
            return True
    return False


def main() -> None:
    sparse = train(dense=False)
    dense = train(dense=True)
    print("reward_shaping — tabular Q, sparse vs dense (seed=%d, episodes=%d, grid=%dx%d)"
          % (SEED, EPISODES, N, N))
    print("goal_cell=%s  actions=N,S,E,W,CLOSE" % (GOAL,))
    print("mode    mean_return  success_rate  last%d_ok" % 50)
    print("sparse  %11.4f  %12.3f  %9d" % (sparse["mean_return"], sparse["success_rate"], sparse["last_ok"]))
    print("dense   %11.4f  %12.3f  %9d" % (dense["mean_return"], dense["success_rate"], dense["last_ok"]))
    # evaluate greedy policy from dense Q on a few starts
    greeds = sum(1 for s in range(20) if greedy_rollout(dense["q"], seed=100 + s))
    print("dense_greedy_ok %d/20" % greeds)
    assert dense["success_rate"] > sparse["success_rate"], (
        "dense should beat sparse on success (%.3f vs %.3f)"
        % (dense["success_rate"], sparse["success_rate"])
    )
    assert dense["success_rate"] >= 0.5, "dense success_rate too low: %.3f" % dense["success_rate"]
    assert greeds >= 10, "dense greedy rollouts too weak: %d/20" % greeds
    print("ok: dense shaped reward outperforms sparse under identical Q-learning")


if __name__ == "__main__":
    main()
