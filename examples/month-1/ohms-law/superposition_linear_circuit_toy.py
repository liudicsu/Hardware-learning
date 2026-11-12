#!/usr/bin/env python3
"""Synthetic superposition theorem vs a joint nodal solve vs a nonlinear element.

Stdlib only. Shared linear net: Vs1 -- R1 -- node V -- R2 -- Vs2, with R3 (or a
series ideal-diode + Rf stand-in) from V to ground. Arms:

  A_joint     one KCL nodal solve with both independent sources on
  B_super     sum of the two single-source responses (the other independent
              source is set to zero, i.e. a voltage source is replaced by a short)
  C_nonlinear same topology with R3 replaced by a series ideal diode + Rf; the
              sum of single-source responses is compared with the joint solve

Common random numbers: when a regime has meter noise, the 32 board indices and
the Gaussian draws are shared in a fixed order across arms on each seed (A uses
z0, B uses z1 then z2 on the two single-source readings). Seeds 0-4.

No integration step: DC nodal equation, closed form on the linear net, bisection
on the one-node nonlinear residual. Written before the first run.

Regimes (declared before the first run):
  linear_noiseless  resistors only, no meter noise  -> A vs B numerically zero / tie
  linear_meter      same linear net + tiny meter noise -> A vs B near-tie
  nonlinear_diode   series diode + Rf to ground     -> B (superposition) consistent lose

Not a Thévenin collapse, not a Wheatstone bridge, not a rectifier-ripple toy.
Real breadboard / DMM: 本页未运行. Wikipedia Superposition principle 以原文为准.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
BOARDS = 32
NUM_ZERO = 1e-9
VS1 = 5.0
VS2 = 3.0
R1 = 1000.0
R2 = 2000.0
R3 = 4000.0
VF = 0.7
RF = 2000.0
SIGMA = 0.001  # V, tiny meter noise (linear_meter)
SIGMA_ALT = 0.010  # V, alternative printed on the same seeds
ARMS = ("A_joint", "B_super", "C_nonlinear")
# name: kind; written before the first run
REGIMES = ("linear_noiseless", "linear_meter", "nonlinear_diode")
STREAM = {"linear_noiseless": 0, "linear_meter": 1, "nonlinear_diode": 2}


def g_parallel() -> float:
    return 1.0 / R1 + 1.0 / R2 + 1.0 / R3


def linear_node(vs1: float, vs2: float) -> float:
    """1x1 nodal KCL solve: V * (1/R1+1/R2+1/R3) = vs1/R1 + vs2/R2."""
    return (vs1 / R1 + vs2 / R2) / g_parallel()


def diode_current(v: float, vf: float, rf: float) -> float:
    return 0.0 if v <= vf else (v - vf) / rf


def nonlinear_residual(v: float, vs1: float, vs2: float, vf: float, rf: float) -> float:
    return (v - vs1) / R1 + (v - vs2) / R2 + diode_current(v, vf, rf)


def nonlinear_node(vs1: float, vs2: float, vf: float = VF, rf: float = RF) -> float:
    """Bisection on the one-node KCL residual. No time step."""
    lo, hi = -20.0, 20.0
    flo, fhi = nonlinear_residual(lo, vs1, vs2, vf, rf), nonlinear_residual(hi, vs1, vs2, vf, rf)
    if flo == 0.0:
        return lo
    if fhi == 0.0:
        return hi
    if flo * fhi > 0.0:
        raise RuntimeError("nonlinear bracket failed")
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fmid = nonlinear_residual(mid, vs1, vs2, vf, rf)
        if fmid == 0.0 or 0.5 * (hi - lo) < 1e-15:
            return mid
        if flo * fmid <= 0.0:
            hi, fhi = mid, fmid
        else:
            lo, flo = mid, fmid
    return 0.5 * (lo + hi)


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


def verdict(xa: list[float], xb: list[float]) -> str:
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{num(m)}+-{num(s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{num(m)}+-{num(s)}: {label}; {sign_note(diffs, m)}"


def shared_noise(regime: str, seed: int, sigma: float) -> list[tuple[float, float, float]]:
    rng = random.Random(1000 * STREAM[regime] + seed)
    return [(rng.gauss(0.0, sigma), rng.gauss(0.0, sigma), rng.gauss(0.0, sigma)) for _ in range(BOARDS)]


def arm_voltage(arm: str, kind: str, vs1: float, vs2: float, noise: tuple[float, float, float], vf: float, rf: float) -> float:
    z0, z1, z2 = noise
    if kind == "linear":
        v_joint = linear_node(vs1, vs2)
        v_s1 = linear_node(vs1, 0.0)
        v_s2 = linear_node(0.0, vs2)
    else:
        v_joint = nonlinear_node(vs1, vs2, vf, rf)
        v_s1 = nonlinear_node(vs1, 0.0, vf, rf)
        v_s2 = nonlinear_node(0.0, vs2, vf, rf)
    if arm == "A_joint":
        return v_joint + z0
    if arm == "B_super":
        return (v_s1 + z1) + (v_s2 + z2)
    return v_joint + z0  # C reports the joint nonlinear voltage when kind is nonlinear


def seed_means(kind: str, sigma: float, regime: str, vf: float = VF, rf: float = RF) -> dict[str, list[float]]:
    out = {arm: [] for arm in ARMS}
    for seed in SEEDS:
        if sigma == 0.0:
            draws = [(0.0, 0.0, 0.0)]
        else:
            draws = shared_noise(regime, seed, sigma)
        acc = {arm: 0.0 for arm in ARMS}
        for noise in draws:
            for arm in ARMS:
                acc[arm] += arm_voltage(arm, kind, VS1, VS2, noise, vf, rf)
        n = len(draws)
        for arm in ARMS:
            out[arm].append(acc[arm] / n)
    return out


def main() -> None:
    v_joint = linear_node(VS1, VS2)
    v_s1 = linear_node(VS1, 0.0)
    v_s2 = linear_node(0.0, VS2)
    v_sum = v_s1 + v_s2
    residual = v_joint - v_sum
    i1 = (VS1 - v_joint) / R1
    i2 = (v_joint - VS2) / R2
    i3 = v_joint / R3
    # hand values 26/7, 20/7, 6/7 V
    print("Synthetic superposition toy; shared two-source linear net; not Thevenin, not Wheatstone, not a rectifier")
    print(f"VS1={VS1} V VS2={VS2} V R1={R1:.0f}ohm R2={R2:.0f}ohm R3={R3:.0f}ohm VF={VF} V RF={RF:.0f}ohm")
    print(f"seeds={len(SEEDS)} boards={BOARDS} meter_sigma={SIGMA} V alt_sigma={SIGMA_ALT} V")
    print("no integration step: DC nodal KCL, closed form on the linear net, bisection on the one-node nonlinear residual")
    print(f"linear_hand V_joint={v_joint:.10f} V (hand 26/7 V) V_s1_only={v_s1:.10f} V (hand 20/7 V) V_s2_only={v_s2:.10f} V (hand 6/7 V)")
    print(f"linear_hand V_sum={v_sum:.10f} V residual_A-B={residual:.3e} V I_R1={i1:.10f} A I_R2={i2:.10f} A I_R3={i3:.10f} A")
    print(f"KCL check I_R1-I_R2-I_R3={i1 - i2 - i3:.3e} A")

    v_nl = nonlinear_node(VS1, VS2)
    v_nl_s1 = nonlinear_node(VS1, 0.0)
    v_nl_s2 = nonlinear_node(0.0, VS2)
    print(f"nonlinear_hand V_joint={v_nl:.10f} V V_s1_only={v_nl_s1:.10f} V V_s2_only={v_nl_s2:.10f} V V_sum={v_nl_s1 + v_nl_s2:.10f} V residual_B-A={(v_nl_s1 + v_nl_s2) - v_nl:.10f} V")

    for regime in REGIMES:
        if regime == "linear_noiseless":
            kind, sigma, tag = "linear", 0.0, "linear resistors, no meter noise"
        elif regime == "linear_meter":
            kind, sigma, tag = "linear", SIGMA, f"linear resistors, meter noise N(0, {SIGMA} V)"
        else:
            kind, sigma, tag = "nonlinear", 0.0, f"series ideal diode + Rf, VF={VF} V RF={RF:.0f}ohm"
        print(f"{regime} ({tag})")
        res = seed_means(kind, sigma, regime)
        for arm in ("A_joint", "B_super"):
            m, s = mean_sd(res[arm])
            print(f"  {arm} {num(m)}+-{num(s)} V")
        residual = [b - a for a, b in zip(res["A_joint"], res["B_super"])]
        zeros = [0.0] * len(residual)
        print(f"  residual B-A {num(mean_sd(residual)[0])}+-{num(mean_sd(residual)[1])} V")
        print(f"  paired A-B nodeV: {verdict(res['A_joint'], res['B_super'])}")
        print(f"  paired residual B-A vs 0: {verdict(residual, zeros)}")

    # Alternative meter sigma on the same seeds (linear_meter stream), disclosed
    res_alt = seed_means("linear", SIGMA_ALT, "linear_meter")
    print(f"alternative linear_meter sigma={SIGMA_ALT} V (same seeds, same board indices, rescaled draws)")
    print(f"  paired A-B nodeV: {verdict(res_alt['A_joint'], res_alt['B_super'])}")
    # Alternative Rf on the same nonlinear net (deterministic)
    v_alt = nonlinear_node(VS1, VS2, VF, 1000.0)
    v_alt_s1 = nonlinear_node(VS1, 0.0, VF, 1000.0)
    v_alt_s2 = nonlinear_node(0.0, VS2, VF, 1000.0)
    print(f"alternative nonlinear Rf=1000ohm V_joint={v_alt:.10f} V V_sum={v_alt_s1 + v_alt_s2:.10f} V residual_B-A={(v_alt_s1 + v_alt_s2) - v_alt:.10f} V")
    print("No winner declared: superposition matches the joint solve on a linear net and fails once a diode is in the branch")
    print("Real breadboard / DMM: 本页未运行; Wikipedia Superposition principle 以原文为准")


if __name__ == "__main__":
    main()
