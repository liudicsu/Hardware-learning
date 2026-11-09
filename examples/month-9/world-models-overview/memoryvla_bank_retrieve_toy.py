#!/usr/bin/env python3
"""Synthetic MemoryVLA-style perceptual-cognitive memory-bank literacy toy.

NOT MemoryVLA weights, NOT MTC stage-prefix memory, NOT DreamGen IDM/LAPA,
NOT TraceVLA. Stdlib only.

Paper (Shi et al., arXiv 2508.19236; numbers 以论文为准): long-horizon
manipulation is non-Markovian; working memory + a Perceptual-Cognitive Memory
Bank that retrieves/consolidates past tokens, then conditions the action
expert. MemoryVLA++ (2606.09827) is reading-only here — not a second toy.

Shared long-horizon POMDP for every arm (equal action budget; no future leak).
Three delay regimes are reported separately so fairness is visible:
  (a) no_delay       cue shown at the decision step — A/B/C should tie
  (b) beyond_window  cue early enough that a fixed window of W misses it
                     (delay chosen on purpose to exceed B's window; B and C
                     therefore get unequal information)
  (c) stale_switch   mid-episode cue flip + distractor bank entries + small
                     BANK_CAP so wrong retrieval visibly degrades C

Arms (same 1-D mover; differ only in memory):
  A_markov          current observation only
  B_window          concat of the last W observations
  C_memory_bank     working memory retrieves top-1 consolidated bank entry

Metrics: success rate per regime. ≥5 seeds. GPU / MemoryVLA weights 本页未运行.
"""
from __future__ import annotations

import math
import random

T = 16
BUTTON_STEP = T - 1  # 15
W = 6
# beyond_window: cue must satisfy cue_t <= BUTTON_STEP - W (= 9) so B misses it
BEYOND_CUE_HI = BUTTON_STEP - W  # 9
BANK_CAP = 8
BANK_CAP_STALE = 3  # tight capacity under distractors
SEEDS = (0, 1, 2, 3, 4)
N_EP = 40
ARMS = ("A_markov", "B_window", "C_memory_bank")
REGIMES = ("a_no_delay", "b_beyond_window", "c_stale_switch")


def obs_vector(pos: int, cue_visible: int | None, distractor: int) -> tuple:
    cue = -1 if cue_visible is None else cue_visible
    return (pos, cue, distractor)


def run_episode(arm: str, rng: random.Random, regime: str) -> bool:
    if regime == "a_no_delay":
        cue_bit = rng.randint(0, 1)
        cue_t = BUTTON_STEP  # visible at decision
        switch_t = None
        final_bit = cue_bit
        bank_cap = BANK_CAP
        inject_distractors = False
    elif regime == "b_beyond_window":
        cue_bit = rng.randint(0, 1)
        # deliberately earlier than the window can reach at decision time
        cue_t = rng.randint(2, BEYOND_CUE_HI)  # 2..9 inclusive
        switch_t = None
        final_bit = cue_bit
        bank_cap = BANK_CAP
        inject_distractors = False
    else:
        # c_stale_switch: early cue, then flip; distractors fill a tiny bank
        cue_bit = rng.randint(0, 1)
        cue_t = rng.randint(2, 5)
        switch_t = rng.randint(6, 9)
        final_bit = 1 - cue_bit
        bank_cap = BANK_CAP_STALE
        inject_distractors = True

    pos = 0
    hist: list[tuple] = []
    bank: list[tuple[tuple, float]] = []

    for t in range(T):
        distractor = rng.randint(0, 1)
        cue_vis: int | None = None
        if t == cue_t:
            cue_vis = cue_bit
        elif switch_t is not None and t == switch_t:
            cue_vis = final_bit
        o = obs_vector(pos, cue_vis, distractor)
        hist.append(o)

        if arm == "A_markov":
            cue_est = o[1]
        elif arm == "B_window":
            window = hist[-W:]
            while len(window) < W:
                window = [(-1, -1, -1)] + window
            cue_est = -1
            for w in window:
                if w[1] != -1:
                    cue_est = w[1]
        else:
            if o[1] != -1:
                key = (o[0], o[2])
                bank.append((key, float(o[1])))
                if inject_distractors:
                    # distractor consolidations with the opposite bit
                    for _ in range(2):
                        dpos = rng.randint(0, BUTTON_STEP)
                        ddis = rng.randint(0, 1)
                        bank.append(((dpos, ddis), float(1 - int(o[1]))))
                if len(bank) > bank_cap:
                    bank = bank[-bank_cap:]
            cue_est = -1.0
            if bank:
                best = min(
                    bank,
                    key=lambda kv: abs(kv[0][0] - o[0]) + abs(kv[0][1] - o[2]),
                )
                cue_est = best[1] if o[1] == -1 else float(o[1])
            elif o[1] != -1:
                cue_est = float(o[1])

        if t < BUTTON_STEP:
            pos = min(pos + 1, BUTTON_STEP)
        else:
            if cue_est == -1 or cue_est == -1.0:
                guess = rng.randint(0, 1)
            else:
                guess = int(round(cue_est))
            return guess == final_bit

    return False


_REGIME_SALT = {"a_no_delay": 11, "b_beyond_window": 22, "c_stale_switch": 33}


def run_arm(arm: str, seed: int, regime: str) -> float:
    shared = random.Random(60_000 + seed * 17 + _REGIME_SALT[regime])
    episodes = [shared.randint(0, 10**9) for _ in range(N_EP)]
    succ = []
    for ep_seed in episodes:
        ok = run_episode(arm, random.Random(ep_seed), regime)
        succ.append(1.0 if ok else 0.0)
    return sum(succ) / len(succ)


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    print(
        "Synthetic MemoryVLA memory-bank toy; shared delayed-cue POMDP; "
        "three delay regimes; not MTC stage memory; not DreamGen IDM"
    )
    print(
        f"T={T} button_t={BUTTON_STEP} window={W} "
        f"beyond_cue_t∈[2,{BEYOND_CUE_HI}] (chosen to exceed B's window; "
        f"B and C get unequal information) "
        f"bank_cap={BANK_CAP} stale_cap={BANK_CAP_STALE} "
        f"episodes/seed={N_EP} seeds={len(SEEDS)}; "
        f"no future leak; equal move budget; paper % 以论文为准"
    )
    print("regime arm success (mean+-sd over seeds)")
    for regime in REGIMES:
        for arm in ARMS:
            vals = [run_arm(arm, seed, regime) for seed in SEEDS]
            m, s = mean_sd(vals)
            print(f"{regime} {arm} {m:.4f}+-{s:.4f}")
    print(
        "Regime note: (a) cue at decision → A/B/C should tie; "
        "(b) delay beyond W → B misses, C can keep the cue (unequal info); "
        "(c) cue switch + distractors + tight bank → C degrades"
    )
    print(
        "GPU / MemoryVLA weights / robot: 本页未运行; Shi et al. 2508.19236 以论文为准; "
        "MemoryVLA++ 2606.09827 reading only"
    )


if __name__ == "__main__":
    main()
