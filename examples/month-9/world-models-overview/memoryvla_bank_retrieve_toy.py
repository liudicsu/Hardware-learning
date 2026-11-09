#!/usr/bin/env python3
"""Synthetic MemoryVLA-style perceptual-cognitive memory-bank literacy toy.

NOT MemoryVLA weights, NOT MTC stage-prefix memory, NOT DreamGen IDM/LAPA,
NOT TraceVLA. Stdlib only.

Paper (Shi et al., arXiv 2508.19236; numbers 以论文为准): long-horizon
manipulation is non-Markovian; working memory + a Perceptual-Cognitive Memory
Bank that retrieves/consolidates past tokens, then conditions the action
expert. MemoryVLA++ (2606.09827) is reading-only here — not a second toy.

Shared long-horizon POMDP for every arm (delayed cue; equal action budget):
  Corridor of length T. At a random early step a cue bit c ∈ {0,1} is shown
  for one frame, then hidden. At the end the agent must press button c.
  Observations otherwise are position + a distractor bit. No arm sees the
  future; bank updates use only past/current tokens.

Arms (same greedy 1-D mover; differ only in memory):
  A_markov          current observation only
  B_window          concat of the last W observations
  C_memory_bank     working memory retrieves top-1 consolidated bank entry
                    by cue-slot similarity, then fuses with current tokens

Metrics: success rate on the memory-dependent button task; mean steps used.
≥5 seeds. No winner presumed. GPU / MemoryVLA weights 本页未运行.
"""
from __future__ import annotations

import math
import random

T = 16  # horizon
CUE_LO, CUE_HI = 2, 12  # cue shown once in this range
BUTTON_STEP = T - 1
W = 6  # fixed window for arm B (misses early cues)
BANK_CAP = 8
SEEDS = (0, 1, 2, 3, 4)
N_EP = 40
ARMS = ("A_markov", "B_window", "C_memory_bank")


def obs_vector(pos: int, cue_visible: int | None, distractor: int) -> tuple:
    """Partial observation. cue_visible is None when hidden."""
    cue = -1 if cue_visible is None else cue_visible
    return (pos, cue, distractor)


def run_episode(arm: str, rng: random.Random) -> tuple[bool, int]:
    cue_bit = rng.randint(0, 1)
    cue_t = rng.randint(CUE_LO, CUE_HI)
    pos = 0
    hist: list[tuple] = []
    # Memory bank: list of (key_feat, value_cue_estimate)
    bank: list[tuple[tuple, float]] = []
    working: tuple | None = None

    for t in range(T):
        distractor = rng.randint(0, 1)
        cue_vis = cue_bit if t == cue_t else None
        o = obs_vector(pos, cue_vis, distractor)
        hist.append(o)

        # --- build feature for the policy ---
        if arm == "A_markov":
            feat = o
            cue_est = o[1]  # -1 when hidden
        elif arm == "B_window":
            window = hist[-W:]
            # pad left
            while len(window) < W:
                window = [(-1, -1, -1)] + window
            flat = []
            for w in window:
                flat.extend(w)
            feat = tuple(flat)
            # estimate cue as last non -1 cue in window
            cue_est = -1
            for w in window:
                if w[1] != -1:
                    cue_est = w[1]
        else:
            # C: working memory = current tokens; retrieve from bank; consolidate
            working = o
            if o[1] != -1:
                # consolidate: store perceptual (pos,distractor) + cognitive cue
                key = (o[0], o[2])
                bank.append((key, float(o[1])))
                if len(bank) > BANK_CAP:
                    # merge redundancies: drop oldest duplicate-ish by key proximity
                    bank = bank[-BANK_CAP:]
            # retrieve: nearest key by L1 on (pos, distractor); only past entries
            cue_est = -1.0
            if bank:
                best = min(bank, key=lambda kv: abs(kv[0][0] - o[0]) + abs(kv[0][1] - o[2]))
                # fuse: prefer retrieved cue if current has none
                cue_est = best[1] if o[1] == -1 else float(o[1])
            elif o[1] != -1:
                cue_est = float(o[1])
            feat = (o[0], cue_est, o[2])

        # --- equal action budget: move +1 toward end, or press at BUTTON_STEP ---
        if t < BUTTON_STEP:
            # advance along corridor (shared policy skeleton)
            pos = min(pos + 1, BUTTON_STEP)
            action = "move"
        else:
            # must press 0 or 1
            if arm == "A_markov":
                # Markov cannot see past cue → random guess from current (no cue)
                guess = rng.randint(0, 1) if cue_est == -1 else int(cue_est)
            elif arm == "B_window":
                if cue_est == -1:
                    guess = rng.randint(0, 1)
                else:
                    guess = int(cue_est)
            else:
                guess = int(round(cue_est)) if cue_est != -1 else rng.randint(0, 1)
            success = guess == cue_bit
            return success, t + 1

    return False, T


def run_arm(arm: str, seed: int) -> tuple[float, float]:
    rng = random.Random(50_000 + seed)
    # Shared episode parameters stream: pre-draw cue bits / times / distractors
    # by using a dedicated RNG so every arm sees the same POMDP realizations.
    shared = random.Random(60_000 + seed)
    episodes = []
    for _ in range(N_EP):
        # draw shared episode seed so arms replay identical POMDPs
        ep_seed = shared.randint(0, 10**9)
        episodes.append(ep_seed)

    succ = []
    steps = []
    for ep_seed in episodes:
        ok, n = run_episode(arm, random.Random(ep_seed))
        succ.append(1.0 if ok else 0.0)
        steps.append(float(n))
    return sum(succ) / len(succ), sum(steps) / len(steps)


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    print(
        "Synthetic MemoryVLA memory-bank toy; shared delayed-cue POMDP; "
        "not MTC stage memory; not DreamGen IDM"
    )
    print(
        f"T={T} cue_t∈[{CUE_LO},{CUE_HI}] button_t={BUTTON_STEP} "
        f"window={W} bank_cap={BANK_CAP} episodes/seed={N_EP} seeds={len(SEEDS)}; "
        f"no future leak; equal move budget; paper % 以论文为准"
    )
    print("arm success mean_steps (mean+-sd over seeds)")
    for arm in ARMS:
        succs, steps = [], []
        for seed in SEEDS:
            s, st = run_arm(arm, seed)
            succs.append(s)
            steps.append(st)
        ms, ss = mean_sd(succs)
        mt, st = mean_sd(steps)
        print(f"{arm} {ms:.4f}+-{ss:.4f} {mt:.4f}+-{st:.4f}")
    print(
        "No winner declared: Markov vs window vs memory-bank trade success; "
        "not a MemoryVLA benchmark"
    )
    print(
        "GPU / MemoryVLA weights / robot: 本页未运行; Shi et al. 2508.19236 以论文为准; "
        "MemoryVLA++ 2606.09827 reading only"
    )


if __name__ == "__main__":
    main()
