#!/usr/bin/env python3
"""Synthetic GD&T bilateral / tolerance stack-up literacy toy. Stdlib only.

Shared nominal chain and shared bilateral half-widths within each regime.
Arms differ only in how the stack prediction is formed:
  A_worst_case   half-width = sum |t_i|  (linear worst-case)
  B_rss          half-width = sqrt(sum t_i^2)  (root-sum-square)
  C_datum_reroot re-root on a mid datum → shorter chain, then worst-case on that chain

Regimes (≥5 Monte Carlo seeds):
  short_chain   1 dim — worst-case == RSS (exact tie)
  long_normal   6 dims, normal MC — RSS covers most hits; worst is wider
  long_skew     6 dims, one-sided skew MC — RSS under-covers (RSS unsafe)

Not an ASME Y14.5 certification. Real CMM / GD&T drawing lab: 本页未运行.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_worst_case", "B_rss", "C_datum_reroot")
N_MC = 2000  # samples per seed


def worst_half(tols: list[float]) -> float:
    return sum(abs(t) for t in tols)


def rss_half(tols: list[float]) -> float:
    return math.sqrt(sum(t * t for t in tols))


def predict(arm: str, tols: list[float], reroot_idx: int) -> float:
    if arm == "A_worst_case":
        return worst_half(tols)
    if arm == "B_rss":
        return rss_half(tols)
    if arm == "C_datum_reroot":
        # Re-root: keep only dims after the datum (shorter stack)
        short = tols[reroot_idx:]
        return worst_half(short)
    raise ValueError(arm)


def mc_stack(
    tols: list[float], seed: int, dist: str
) -> list[float]:
    """Return N_MC signed stack errors for the full chain."""
    rng = random.Random(40_000 + seed)
    out = []
    for _ in range(N_MC):
        s = 0.0
        for t in tols:
            if dist == "normal":
                # ±t ≈ ±3σ → σ = t/3
                s += rng.gauss(0.0, abs(t) / 3.0)
            elif dist == "skew":
                # One-sided: exponential excess toward +tol (non-normal)
                # mean shift so mass sits near + side; unsafe for symmetric RSS
                u = rng.random()
                # triangular-ish toward +t
                s += abs(t) * (1.0 - math.sqrt(1.0 - u))  # in [0, t]
            else:
                raise ValueError(dist)
        out.append(s)
    return out


def hit_rate(samples: list[float], half: float) -> float:
    return sum(1 for x in samples if abs(x) <= half + 1e-15) / len(samples)


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


REGIMES = (
    # name, tols (bilateral half-widths, mm synthetic), reroot_idx, dist
    ("short_chain", [0.15], 0, "normal"),  # 1 dim: worst == RSS (exact tie)
    ("long_normal", [0.05, 0.08, 0.06, 0.10, 0.07, 0.09], 3, "normal"),
    ("long_skew", [0.05, 0.08, 0.06, 0.10, 0.07, 0.09], 3, "skew"),
)


def main() -> None:
    print(
        "Synthetic GD&T / tolerance-stack toy; shared chain/tolerances; "
        "not an ASME Y14.5 certification"
    )
    print(
        f"N_MC={N_MC} seeds={len(SEEDS)}; "
        "A=worst-case sum|t|; B=RSS sqrt(sum t^2); C=datum re-root then worst"
    )
    print(
        "regime arm pred_half_mm mc_hit_rate mean_abs_stack_mm "
        "(pred fixed; hit/mean over seeds mean+-sd)"
    )
    summary = {}
    for reg_name, tols, reroot, dist in REGIMES:
        for arm in ARMS:
            pred = predict(arm, tols, reroot)
            hits, means = [], []
            for seed in SEEDS:
                samples = mc_stack(tols, seed, dist)
                # For C, MC should be on the shortened chain for a fair hit test
                if arm == "C_datum_reroot":
                    samples = mc_stack(tols[reroot:], seed, dist)
                hits.append(hit_rate(samples, pred))
                means.append(sum(abs(x) for x in samples) / len(samples))
            hm, hs = mean_sd(hits)
            mm, ms = mean_sd(means)
            summary[(reg_name, arm)] = (pred, hm)
            print(
                f"{reg_name} {arm} {pred:.4f} {hm:.4f}+-{hs:.4f} "
                f"{mm:.4f}+-{ms:.4f}"
            )
    # Short-chain tie: worst ≈ RSS
    pw = predict("A_worst_case", REGIMES[0][1], REGIMES[0][2])
    pr = predict("B_rss", REGIMES[0][1], REGIMES[0][2])
    print(
        f"short_chain: |worst - RSS| = {abs(pw - pr):.4e} mm "
        f"(exact tie — one dim; worst==RSS)"
    )
    # Long skew: RSS hit rate low (unsafe) vs worst
    hit_rss = summary[("long_skew", "B_rss")][1]
    hit_wc = summary[("long_skew", "A_worst_case")][1]
    print(
        f"long_skew: RSS mc_hit={hit_rss:.3f} vs worst mc_hit={hit_wc:.3f} "
        f"(RSS under-covers skewed one-sided stack — RSS unsafe here)"
    )
    pred_c = summary[("long_normal", "C_datum_reroot")][0]
    pred_a = summary[("long_normal", "A_worst_case")][0]
    print(
        f"long_normal: datum re-root half {pred_c:.4f} mm < "
        f"full worst {pred_a:.4f} mm (shorter stack)"
    )
    print(
        "No winner declared: short chains make worst≈RSS; "
        "skewed stacks make RSS look safe on paper but fail MC; "
        "re-root helps only when the datum is real"
    )
    print(
        "Real CMM / GD&T drawing / ASME Y14.5 lab: 本页未运行; "
        "Wikipedia GD&T and Tolerance analysis 以原文为准"
    )


if __name__ == "__main__":
    main()
