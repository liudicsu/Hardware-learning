#!/usr/bin/env python3
"""imagine_rank_toy.py: rank policies in a biased world model vs the oracle env (stdlib).

Reading aid for the Ctrl-World idea (arXiv 2510.10125): roll each policy out
inside a learned world model instead of on the robot, and use the imagined
success rates to RANK policies. Here there is no video model: an episode is a
few numbers, and a "world model" is the oracle outcome rule with one bias.

Five synthetic policies (lesson-chosen, not real checkpoints) differ in
  follow  probability of picking the instructed object,
  sigma   execution error scale (m); success needs error < TOL,
  slide   chance a successful placement slides off afterwards (real physics),
  retry   whether the policy retries once after an execution miss.
Every policy, in the oracle and in every world model, sees the SAME tasks and
initial conditions and the SAME per-episode uniforms / normals (shared ICs).
World models:
  calibrated     same outcome rule as the oracle (sanity row)
  uniform_drop   imagines 15 % of successes as failures, the same episodes
                 for every policy (underestimates success, policy-blind)
  tight_tol      imagines execution as harder (TOL x 0.7): looks uniform, but
                 hurts sloppy (large-sigma) policies more
  no_slide       does not model objects sliding off after placement
  no_retry       ends the episode after the first miss (no retry)
Metric: Kendall tau between imagined and oracle success rates over the
policies (+1 same order, -1 reversed) and the list of flipped pairs.
The paper's numbers (e.g. its 44.7 % improvement) are per the paper; nothing
here is a DROID / pi0 / pi0.5 rollout (本页未运行).
usage: python3 imagine_rank_toy.py
"""
from __future__ import annotations

import random
from itertools import combinations

SEED = 10125
TOL = 0.020                # m
TASKS = ("pick_place", "drawer", "towel_fold", "stack")
N_IC = 60                  # initial conditions per task -> 240 shared episodes
POLICIES = (               # name, follow, sigma, slide, retry
    ("P1", 0.90, 0.012, 0.00, False),
    ("P2", 0.85, 0.010, 0.30, False),
    ("P3", 0.70, 0.018, 0.00, True),
    ("P4", 0.75, 0.016, 0.00, False),
    ("P5", 0.50, 0.010, 0.00, False),
)
WORLDS = ("oracle", "calibrated", "uniform_drop", "tight_tol", "no_slide", "no_retry")


def shared_episodes():
    """Per (task, ic): (u_follow, z1, z2, u_slide, u_wm); identical for every policy and world."""
    rng = random.Random(SEED)
    return [(task, ic, rng.random(), abs(rng.gauss(0, 1)), abs(rng.gauss(0, 1)), rng.random(), rng.random())
            for task in TASKS for ic in range(N_IC)]


def outcome(policy, ep, world):
    _name, follow, sigma, slide, retry = policy
    _task, _ic, u_f, z1, z2, u_s, u_wm = ep
    tol = TOL * (0.7 if world == "tight_tol" else 1.0)
    if u_f >= follow:                       # wrong object: instruction not followed
        return False
    placed = sigma * z1 < tol
    if not placed and retry and world != "no_retry":
        placed = sigma * z2 < tol
    if placed and world != "no_slide" and u_s < slide:
        return False                        # slid off after placement (real physics)
    if placed and world == "uniform_drop" and u_wm < 0.15:
        return False                        # imagined failure, same episodes for all policies
    return placed


def kendall_tau(a, b):
    conc = disc = 0
    flips = []
    for i, j in combinations(range(len(a)), 2):
        s = (a[i] - a[j]) * (b[i] - b[j])
        if s > 0:
            conc += 1
        elif s < 0:
            disc += 1
            flips.append((i, j))
    n = len(a) * (len(a) - 1) // 2
    return (conc - disc) / n, flips


def main() -> None:
    eps = shared_episodes()
    n = len(eps)
    print(f"seed={SEED} tasks={len(TASKS)} x ics={N_IC} = {n} shared episodes per policy and world; tol={TOL} m")
    rates = {w: [sum(outcome(p, e, w) for e in eps) / n for p in POLICIES] for w in WORLDS}
    print(f"{'policy':<6} {'follow':>6} {'sigma':>6} {'slide':>5} {'retry':>5} " + " ".join(f"{w:>12}" for w in WORLDS))
    for k, p in enumerate(POLICIES):
        print(f"{p[0]:<6} {p[1]:6.2f} {p[2]:6.3f} {p[3]:5.2f} {str(p[4]):>5} "
              + " ".join(f"{rates[w][k]:12.3f}" for w in WORLDS))
    oracle = rates["oracle"]
    order = sorted(range(len(POLICIES)), key=lambda k: -oracle[k])
    print("oracle ranking: " + " > ".join(POLICIES[k][0] for k in order))
    taus = {}
    for w in WORLDS[1:]:
        tau, flips = kendall_tau(oracle, rates[w])
        taus[w] = tau
        mean_gap = sum(rates[w]) / len(POLICIES) - sum(oracle) / len(POLICIES)
        names = ", ".join(f"{POLICIES[i][0]}/{POLICIES[j][0]}" for i, j in flips) or "none"
        rank = " > ".join(POLICIES[k][0] for k in sorted(range(len(POLICIES)), key=lambda k: -rates[w][k]))
        print(f"{w:<12} kendall_tau={tau:+.2f} mean_rate_shift={mean_gap:+.3f} flipped_pairs={names}  ranking: {rank}")
    assert taus["calibrated"] == 1.0
    assert taus["uniform_drop"] == 1.0, "a policy-blind bias should keep the ranking"
    assert taus["tight_tol"] < 1.0 and taus["no_slide"] < 1.0 and taus["no_retry"] < 1.0
    print("ok: a policy-blind underestimate lowers every rate but keeps the order; biases that hit "
          "some policies' failure modes flip pairs; Ctrl-World figures 以论文为准, not run here")


if __name__ == "__main__":
    main()
