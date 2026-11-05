#!/usr/bin/env python3
"""suite_score_table.py: aggregate fake LIBERO-style suite scores (stdlib).

Pinned fake episode outcomes (seed=88) for five named suites. Prints per-suite
mean success, optional Wilson 95 % intervals (Month 6 formula, not re-derived),
and a grand mean. No lerobot-eval / GPU / MuJoCo.
usage: python3 suite_score_table.py
"""
from __future__ import annotations

import math
import random

SEED = 88
Z95 = 1.959964
# Five suites (docs: 5 suites / 130 tasks total). Toy uses fixed episode counts.
SUITES = (
    ("libero_spatial", 40),
    ("libero_object", 40),
    ("libero_goal", 30),
    ("libero_10", 20),
    ("libero_90", 50),
)
# Success rates used to sample fixed-seed Bernoulli outcomes (not real eval).
P_SUCCESS = {
    "libero_spatial": 0.70,
    "libero_object": 0.55,
    "libero_goal": 0.60,
    "libero_10": 0.45,
    "libero_90": 0.35,
}


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval (same intuition as Month 6 eval_report)."""
    if n <= 0:
        return 0.0, 0.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def main() -> None:
    rng = random.Random(SEED)
    print(f"seed={SEED} suites={len(SUITES)} (fake episode outcomes; not real LIBERO)")
    print(
        f"{'suite':<16} {'n':>4} {'k':>4} {'mean':>8} "
        f"{'wilson_lo':>10} {'wilson_hi':>10}"
    )
    total_k = 0
    total_n = 0
    means: list[float] = []
    for name, n in SUITES:
        p = P_SUCCESS[name]
        outcomes = [1 if rng.random() < p else 0 for _ in range(n)]
        k = sum(outcomes)
        mean = k / n
        lo, hi = wilson(k, n)
        means.append(mean)
        total_k += k
        total_n += n
        print(
            f"{name:<16} {n:4d} {k:4d} {mean:8.4f} "
            f"{lo:10.4f} {hi:10.4f}"
        )
    suite_mean = sum(means) / len(means)
    overall = total_k / total_n
    lo_o, hi_o = wilson(total_k, total_n)
    print(
        f"ok: n_suites={len(SUITES)} suite_mean={suite_mean:.4f} "
        f"overall={overall:.4f} ({total_k}/{total_n}) "
        f"wilson=[{lo_o:.4f},{hi_o:.4f}]"
    )
    print(
        "note: graduation bar remains Month 8.7 (safety/CI/20-start Wilson/"
        "portfolio 8/8); LIBERO is bonus reporting only"
    )


if __name__ == "__main__":
    main()
