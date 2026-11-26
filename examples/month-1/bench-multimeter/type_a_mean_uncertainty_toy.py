#!/usr/bin/env python3
"""Type A standard uncertainty of the mean vs a Type-B spec limit.

Synthetic repeat observations, stdlib only.  Not a real DMM log, not a
calibration certificate, and not a rewrite of the Type-B I=V/R budget,
Kelvin four-wire sensing, or true-RMS estimators.  Real DMM /
calibration laboratory / repeated physical observations: 本页未运行.
NIST Type A statements 以原文为准.

The official Type A display (opened eq (5)) is the estimated standard
deviation of the mean.  An algebraic check that eq (5) equals s/sqrt(n)
is labelled 手算; it is not a second official displayed equation.

Common random numbers: one shared observation series per seed (a prefix
of the same draws is used at each n).  Arms, shared draws (per seed):
  A_type_a       : official Type A u(x) from eq (5),
                   sqrt(sum((X_k - mean)^2) / (n*(n-1)))
  B_type_b       : already-taught Type-B conversion u = L/sqrt(3) from a
                   declared rectangular half-width L; not computed from
                   this series, so it does not shrink when n grows
  C_s_as_u_mean  : treat the observation sample standard deviation s
                   (denominator n-1 only) as if it were u of the mean.
                   Pre-declared lose, kept.  One fail mode, declared
                   before the first run.
The arms differ only in how u is formed.  No integration step.

Regimes were written before the first run:
  official identity / 手算 check
      : Arm A vs a 手算 of s/sqrt(n) on the same draws must tie
        (identical, or numerically zero within printed rounding)
  larger n (same seed family, CRN)
      : Arm A shrinks consistently with the official 1/(n*(n-1))
        formula; Arm B stays put
  C loses
      : C is larger than A by sqrt(n), 手算, same sign on all seeds
"""

from __future__ import annotations

import math
import random

# Declared before the first official run.
MU = 5.0000  # synthetic true value of X, volt (not a real DMM reading)
SIGMA = 0.0200  # observation noise sd, volt
N = 16  # Type A series length (n >= 2 so eq (5) is defined)
N_LARGE = 64  # larger n, same seed family, CRN
N_ALT = 256  # named alternative n, same seed family, not adopted
L = 0.0500  # Type-B rectangular half-width, volt; not from this series
SEEDS = (0, 1, 2, 3, 4)
CLEAR_FRAC = 0.2000  # small-vs-clear factor; printed before the first official run
NUM_ZERO = 1e-9
ARMS = ("A_type_a", "B_type_b", "C_s_as_u_mean")
N_MAX = N_ALT


def u_type_b(half_width: float) -> float:
    """Already-taught rectangular conversion u = L/sqrt(3). Not from the series."""
    return half_width / math.sqrt(3.0)


U_B = u_type_b(L)


def draw_series(seed: int, n: int) -> list[float]:
    """First n draws of the shared series for this seed (CRN prefixes)."""
    rng = random.Random(seed)
    return [rng.gauss(MU, SIGMA) for _ in range(n)]


def sample_mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def sum_sq_dev(xs: list[float], mean: float) -> float:
    return sum((x - mean) ** 2 for x in xs)


def type_a_eq5(xs: list[float]) -> float:
    """Official Type A u(x): opened eq (5), denominator n(n-1)."""
    n = len(xs)
    mean = sample_mean(xs)
    return math.sqrt(sum_sq_dev(xs, mean) / (n * (n - 1)))


def sample_s(xs: list[float]) -> float:
    """Sample standard deviation of the observations (denominator n-1)."""
    n = len(xs)
    mean = sample_mean(xs)
    return math.sqrt(sum_sq_dev(xs, mean) / (n - 1))


def hand_s_over_sqrt_n(xs: list[float]) -> float:
    """手算 algebraic check, not a second official display: s/sqrt(n)."""
    return sample_s(xs) / math.sqrt(len(xs))


def arm_values(xs: list[float]) -> dict[str, float]:
    return {
        "A_type_a": type_a_eq5(xs),
        "B_type_b": U_B,
        "C_s_as_u_mean": sample_s(xs),
        "hand_s_over_sqrt_n": hand_s_over_sqrt_n(xs),
        "mean": sample_mean(xs),
    }


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    if len(xs) == 1:
        return mu, 0.0
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
    if x != 0.0 and abs(x) < 5e-5:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs: list[float], m: float) -> str:
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m: float, s: float) -> str:
    return f"{num(m)}+-{num(s)}"


def verdict(xa: list[float], xb: list[float]) -> str:
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < CLEAR_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def collect(n: int) -> dict[str, list[float]]:
    keys = ("A_type_a", "B_type_b", "C_s_as_u_mean", "hand_s_over_sqrt_n", "mean")
    out = {k: [] for k in keys}
    for seed in SEEDS:
        vals = arm_values(draw_series(seed, n))
        for k in keys:
            out[k].append(vals[k])
    return out


def print_regime(name: str, tag: str, n: int, res: dict[str, list[float]]) -> None:
    print(f"{name} ({tag})")
    print(
        f"  A_type_a {fmt_pair(*mean_sd(res['A_type_a']))} V  "
        f"B_type_b {fmt_pair(*mean_sd(res['B_type_b']))} V  "
        f"C_s_as_u_mean {fmt_pair(*mean_sd(res['C_s_as_u_mean']))} V"
    )
    print(f"  mean {fmt_pair(*mean_sd(res['mean']))} V  hand_s_over_sqrt_n {fmt_pair(*mean_sd(res['hand_s_over_sqrt_n']))} V")
    print(f"  paired A-hand_s_over_sqrt_n u: {verdict(res['A_type_a'], res['hand_s_over_sqrt_n'])}")
    print(f"  paired A-B u: {verdict(res['A_type_a'], res['B_type_b'])}")
    print(f"  paired C-A u: {verdict(res['C_s_as_u_mean'], res['A_type_a'])}")
    ratios = [c / a for c, a in zip(res["C_s_as_u_mean"], res["A_type_a"])]
    root_n = [math.sqrt(n)] * len(SEEDS)
    print(f"  hand_calc C/A vs sqrt({n})={math.sqrt(n):.10f}: {verdict(ratios, root_n)}")


def main() -> None:
    print("Synthetic Type A mean uncertainty toy; shared observations; not a real DMM")
    print(
        f"seeds={len(SEEDS)} n={N} n_large={N_LARGE} mu={MU:.4f} V sigma={SIGMA:.4f} V "
        f"L={L:.4f} V uB=L/sqrt(3)={U_B:.10f} V clear_frac={CLEAR_FRAC:.4f}"
    )
    print("Type-B u is the already-taught L/sqrt(3) conversion; it is not computed from this series")
    print(
        "Arm C lose mode, declared before the first run: treat the observation sample sd s as if it were s(mean)"
    )
    print(
        "hand_calc eq(5)=s/sqrt(n) (algebraic, 手算, not a second official display); "
        f"sqrt({N})={math.sqrt(N):.10f}; sqrt({N_LARGE})={math.sqrt(N_LARGE):.10f}; "
        f"sqrt({N_ALT})={math.sqrt(N_ALT):.10f}"
    )
    print(f"hand_calc L/sqrt(3)={U_B:.10f} V (L={L:.4f} V); work_plan 30+25+50+40+35=180")
    print("Regimes were written before the first run")

    res_n = collect(N)
    res_large = collect(N_LARGE)
    res_alt = collect(N_ALT)

    print_regime(
        f"n={N}",
        "official Type A series; shared draws",
        N,
        res_n,
    )
    print_regime(
        f"n={N_LARGE}",
        f"same seed family, CRN: first {N} observations shared with n={N}",
        N_LARGE,
        res_large,
    )
    print(f"  paired A(n={N_LARGE})-A(n={N}) u: {verdict(res_large['A_type_a'], res_n['A_type_a'])}")
    print(f"  paired B(n={N_LARGE})-B(n={N}) u: {verdict(res_large['B_type_b'], res_n['B_type_b'])}")

    print(
        f"alternative n={N_ALT} (same seed family, CRN: first {N_LARGE} observations shared, not adopted)"
    )
    print(
        f"  A_type_a {fmt_pair(*mean_sd(res_alt['A_type_a']))} V  "
        f"B_type_b {fmt_pair(*mean_sd(res_alt['B_type_b']))} V  "
        f"C_s_as_u_mean {fmt_pair(*mean_sd(res_alt['C_s_as_u_mean']))} V"
    )
    print(f"  paired A-hand_s_over_sqrt_n u: {verdict(res_alt['A_type_a'], res_alt['hand_s_over_sqrt_n'])}")
    print(f"  paired A(n={N_ALT})-A(n={N_LARGE}) u: {verdict(res_alt['A_type_a'], res_large['A_type_a'])}")
    print(f"  paired B(n={N_ALT})-B(n={N_LARGE}) u: {verdict(res_alt['B_type_b'], res_large['B_type_b'])}")
    print(f"  paired C-A u: {verdict(res_alt['C_s_as_u_mean'], res_alt['A_type_a'])}")
    ratios = [c / a for c, a in zip(res_alt["C_s_as_u_mean"], res_alt["A_type_a"])]
    root_n = [math.sqrt(N_ALT)] * len(SEEDS)
    print(f"  hand_calc C/A vs sqrt({N_ALT})={math.sqrt(N_ALT):.10f}: {verdict(ratios, root_n)}")

    print(
        "No winner declared: Type A u of the mean follows official eq (5) and shrinks when n grows; "
        "the Type-B L/sqrt(3) term stays put; using s as if it were s(mean) loses"
    )
    print(
        "Real DMM / calibration laboratory / repeated physical observations: 本页未运行; "
        "NIST Type A statements 以原文为准"
    )


if __name__ == "__main__":
    main()
