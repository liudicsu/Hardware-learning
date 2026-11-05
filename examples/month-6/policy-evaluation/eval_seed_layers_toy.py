#!/usr/bin/env python3
"""eval_seed_layers_toy.py: synthetic policy draws + nested eval seed layers (stdlib).

The K "train seeds" here are SYNTHETIC POLICY DRAWS (scripted Bernoulli success
parameters), NOT real neural-network training runs. Prints use the names
  synthetic_policy_draw_k
  shared_IC          (paired: the same evaluation IC list for every draw)
  independent_IC     (unpaired: each draw gets its own IC list)

Uncertainty layers (NEVER mixed into one unlabeled %):
  1. Count interval on one draw's trials: Wilson 95 % (frequentist) and a
     uniform-prior Beta(1+k, 1+n-k) central 95 % interval (Bayesian sketch).
  2. Across-draw dispersion: min / median / max of the K point rates, plus the
     cherry-picked best-seed rate vs the median (reporting the best alone is
     the anti-pattern).

Checklist fields reference arXiv 2409.09491v2 §4 "Analysis and Reporting"
(Kress-Gazit et al. — Robot Learning as an Empirical Science: Best
Practices for Policy Evaluation):
  §4.1 experiment parameters — semantic success criterion; counts not just %;
       timing of sessions; initial conditions and their relation to training;
  §4.2 statistical analysis — interval / Bayesian layer, separate from
       across-draw spread;
  §4.3 failure modes — categories + frequency (toy: one synthetic category).
usage: python3 eval_seed_layers_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 64
K_DRAWS = 5                 # synthetic_policy_draw_0 .. _4
N_IC = 40                   # evaluation initial conditions per table
# Per-draw true success probabilities (scripted policies, not trained nets).
P_DRAWS = (0.55, 0.62, 0.70, 0.78, 0.66)
Z95 = 1.959964


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def beta_central_interval(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Central (1-alpha) interval from Beta(1+k, 1+n-k) via incomplete-beta inverse.

    Uniform prior Beta(1,1) + Bernoulli likelihood → Beta(1+k, 1+n-k).
    Quantiles by bisection on the regularised incomplete beta.
    """
    a = 1.0 + k
    b = 1.0 + (n - k)

    def betacf(x, aa, bb, max_iter=200):
        # Lentz continued fraction for incomplete beta (NR-style).
        tiny = 1e-30
        qab = aa + bb
        qap = aa + 1.0
        qam = aa - 1.0
        c = 1.0
        d = 1.0 - qab * x / qap
        if abs(d) < tiny:
            d = tiny
        d = 1.0 / d
        h = d
        for m in range(1, max_iter + 1):
            m2 = 2 * m
            aa_m = m * (bb - m) * x / ((qam + m2) * (aa + m2))
            d = 1.0 + aa_m * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + aa_m / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            h *= d * c
            aa_m = -(aa + m) * (qab + m) * x / ((aa + m2) * (qap + m2))
            d = 1.0 + aa_m * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + aa_m / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < 1e-10:
                break
        return h

    def betai(x, aa, bb):
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        ln_beta = (math.lgamma(aa) + math.lgamma(bb) - math.lgamma(aa + bb))
        front = math.exp(aa * math.log(x) + bb * math.log(1.0 - x) - ln_beta)
        if x < (aa + 1.0) / (aa + bb + 2.0):
            return front * betacf(x, aa, bb) / aa
        return 1.0 - front * betacf(1.0 - x, bb, aa) / bb

    def quantile(p):
        lo, hi = 0.0, 1.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if betai(mid, a, b) < p:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    return quantile(alpha / 2), quantile(1.0 - alpha / 2)


def median(vals: list[float]) -> float:
    s = sorted(vals)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return 0.5 * (s[n // 2 - 1] + s[n // 2])


def run_table(tag: str, ic_seeds_per_draw: list[list[int]], rng_master: random.Random) -> list[dict]:
    """Evaluate each synthetic draw on its IC list; return per-draw records."""
    rows = []
    print(f"== {tag} ==")
    print(f"{'draw':<26} {'k/n':>7} {'rate%':>7} {'Wilson95%':>18} {'Beta95%':>18}")
    for k, p_true in enumerate(P_DRAWS):
        seeds = ic_seeds_per_draw[k]
        # Independent RNG stream per (draw, IC) from the IC seed alone so a
        # shared IC list is genuinely paired across draws.
        successes = []
        for s in seeds:
            # Paired shared_IC: same IC seed ⇒ same Uniform(0,1); draws differ
            # only through their scripted p_true threshold.
            u = random.Random(s).random()
            successes.append(1 if u < p_true else 0)
        kk = sum(successes)
        n = len(successes)
        rate = kk / n
        wlo, whi = wilson(kk, n)
        blo, bhi = beta_central_interval(kk, n)
        label = f"synthetic_policy_draw_{k}"
        print(f"{label:<26} {kk:>2}/{n:<2} {100 * rate:6.1f}%  "
              f"{100 * wlo:.1f}..{100 * whi:.1f}  {100 * blo:.1f}..{100 * bhi:.1f}")
        rows.append({"k": kk, "n": n, "rate": rate, "p_true": p_true,
                     "wilson": (wlo, whi), "beta": (blo, bhi)})
    rates = [r["rate"] for r in rows]
    best = max(rates)
    med = median(rates)
    print(f"across_draw_dispersion: min={100 * min(rates):.1f}%  "
          f"median={100 * med:.1f}%  max={100 * best:.1f}%  "
          f"best_seed_cherry_pick={100 * best:.1f}%  "
          f"cherry_pick_minus_median={100 * (best - med):.1f} pp")
    print(f"layer_note: Wilson/Beta = count uncertainty WITHIN one draw; "
          f"min/median/max = dispersion ACROSS draws — do not mix into one %")
    print()
    return rows


def main() -> None:
    print(f"seed={SEED} K_draws={K_DRAWS} N_IC={N_IC}")
    print("synthetic_policy_draw_k = scripted Bernoulli policies (NOT real training runs)")
    print(f"true_p per draw: {list(P_DRAWS)}")
    print()
    print("checklist_fields (arXiv 2409.09491v2 §4 Analysis and Reporting):")
    print("  4.1 experiment_parameters: success_criterion | n_evals_counts | "
          "session_timing | ICs_and_relation_to_train")
    print("  4.2 statistical_analysis: Wilson_or_Beta_count_interval "
          "(separate from across-draw dispersion)")
    print("  4.3 failure_modes: categories + frequency + narrative")
    print(f"  toy_success_criterion: Bernoulli trial vs scripted p_k "
          f"(semantic stand-in; real arm criterion 本页未运行)")
    print(f"  toy_IC_relation_to_train: evaluation ICs are held-out synthetic indices; "
          f"not claimed in-distribution to any training set")
    print()

    master = random.Random(SEED)
    # Shared IC list: same N_IC seeds for every draw (paired).
    shared_ics = [master.randrange(10_000_000) for _ in range(N_IC)]
    shared_per_draw = [list(shared_ics) for _ in range(K_DRAWS)]
    rows_shared = run_table("shared_IC (paired)", shared_per_draw, master)

    # Independent IC lists: each draw gets its own N_IC seeds (unpaired).
    indep_per_draw = [[master.randrange(10_000_000) for _ in range(N_IC)]
                      for _ in range(K_DRAWS)]
    rows_indep = run_table("independent_IC (unpaired)", indep_per_draw, master)

    # Synthetic failure table for the median shared draw (illustrates §4.3).
    med_rate = median([r["rate"] for r in rows_shared])
    med_idx = min(range(K_DRAWS),
                  key=lambda i: abs(rows_shared[i]["rate"] - med_rate))
    fails = rows_shared[med_idx]["n"] - rows_shared[med_idx]["k"]
    # Split failures into two toy categories with a fixed ratio.
    cat_a = int(round(0.65 * fails))
    cat_b = fails - cat_a
    print(f"== failure_modes (shared_IC, synthetic_policy_draw_{med_idx} = median) ==")
    print(f"  category              count  share")
    print(f"  near_goal_timeout     {cat_a:>5}  {100 * cat_a / fails:5.1f}%")
    print(f"  collision_mid_traj    {cat_b:>5}  {100 * cat_b / fails:5.1f}%")
    print()

    best_shared = max(r["rate"] for r in rows_shared)
    med_shared = median([r["rate"] for r in rows_shared])
    assert best_shared >= med_shared
    assert abs(best_shared - med_shared) > 0.0, "need a visible cherry-pick gap"
    print(f"ok: shared_IC and independent_IC tabulated separately; "
          f"Wilson/Beta count layer ≠ across-draw dispersion; "
          f"best_seed {100 * best_shared:.1f}% vs median {100 * med_shared:.1f}% "
          f"(do not report best alone); synthetic draws only "
          f"(real policy training 本页未运行)")


if __name__ == "__main__":
    main()
