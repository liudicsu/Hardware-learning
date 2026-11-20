#!/usr/bin/env python3
"""Synthetic Y-Δ / Δ-Y reduction of two-terminal resistor networks.

Stdlib only. Real positive resistances. Arms:

  A_series_parallel  series-parallel only. On a ladder it finishes and returns
                     Req. On a five-resistor bridge it uses the documented naive
                     shortcut of ignoring the cross edge and treating the two
                     remaining paths as parallel (always a number).
  B_official         official Y-Δ (formulae with the article's labels R1, R2, R3
                     / Ra, Rb, Rc) that eliminates one star node, then
                     series-parallel to a single Req.
  C_swapped          same skeleton as B, but uses the Δ-Y formulae where the
                     step is Y-Δ. Pre-declared lose, kept.

Common random numbers: seeds 0-4. Every regime is deterministic (fixed positive
resistances; the five seeds repeat the same DC value). No integration step:
algebraic series-parallel and the official transform, closed form.

Truth for error metrics is Arm B's official reduction on that net. An independent
nodal test-source check is printed as hand_calc only; it is not a taught
mesh/nodal unit and is not used to retune B.

Regimes (declared before the first run):
  series_parallel_ladder  no cross edge              -> A vs B exact tie
  large_cross_bridge      cross resistance very large -> A vs B near-tie or small
  moderate_bridge         cross comparable to the arms -> B clearly better than A
                                                     (20 % of the smaller-arm mean);
                                                     C loses on the same bridge

This is a two-terminal reduction example, not the Wheatstone measurement bridge
from the components lesson. Real breadboard / DMM: 本页未运行.
Wikipedia Y-Δ transform 以原文为准.
"""
from __future__ import annotations

import math

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
CLEAR_FRAC = 0.2000  # small-vs-clear factor; printed before the first official run
VTEST = 1.0  # V, nodal test-source check only (hand_calc)
# Ladder, P to Q: P--RS1--N1--RS2--N2--RS3--Q, RP1 from N1 to Q, RP2 from N2 to Q.
RS1 = 1000.0
RP1 = 2000.0
RS2 = 3000.0
RP2 = 4000.0
RS3 = 5000.0
# Bridge, terminals P and Q, internal nodes L and R:
# RPL = P-L, RPR = P-R, RQL = L-Q, RQR = R-Q, RX = L-R (the cross edge).
RPL = 100.0
RPR = 10000.0
RQL = 10000.0
RQR = 100.0
RX_LARGE = 1000000.0
RX_MODERATE = 100.0
RX_ALT_LARGE = 10000000.0  # disclosed alternative, same bridge arms, not adopted
ARMS = ("A_series_parallel", "B_official", "C_swapped")
REGIMES = ("series_parallel_ladder", "large_cross_bridge", "moderate_bridge")


def par(*rs: float) -> float:
    return 1.0 / sum(1.0 / r for r in rs)


def delta_from_wye(r1: float, r2: float, r3: float) -> tuple[float, float, float]:
    """Official Y → Δ, article labels. Ra opposite R1, Rb opposite R2, Rc opposite R3."""
    p = r1 * r2 + r2 * r3 + r3 * r1
    ra = p / r1  # = r2 + r3 + (r2 * r3) / r1
    rb = p / r2
    rc = p / r3
    return ra, rb, rc


def wye_from_delta(ra: float, rb: float, rc: float) -> tuple[float, float, float]:
    """Official Δ → Y, article labels."""
    s = ra + rb + rc
    r1 = (rb * rc) / s
    r2 = (ra * rc) / s
    r3 = (ra * rb) / s
    return r1, r2, r3


def solve2(a11: float, a12: float, a21: float, a22: float, b1: float, b2: float) -> tuple[float, float]:
    det = a11 * a22 - a12 * a21
    return (b1 * a22 - a12 * b2) / det, (a11 * b2 - b1 * a21) / det


def series_parallel_ladder() -> float:
    return RS1 + par(RP1, RS2 + par(RP2, RS3))


def official_ladder(transform) -> float:
    """Y at N1: R1=RS1 to P, R2=RS2 to N2, R3=RP1 to Q; then series-parallel."""
    ra, rb, rc = transform(RS1, RS2, RP1)
    # Ra between N2-Q, Rb between P-Q, Rc between P-N2; RP2 and RS3 remain N2-Q.
    return par(rb, rc + par(ra, RP2, RS3))


def series_parallel_bridge_shortcut() -> float:
    """Naive shortcut: ignore the cross edge; two series paths in parallel."""
    return par(RPL + RQL, RPR + RQR)


def official_bridge(rx: float, transform) -> float:
    """Y at L: R1=RPL to P, R2=RQL to Q, R3=RX to R; then series-parallel."""
    ra, rb, rc = transform(RPL, RQL, rx)
    # Ra between Q-R, Rb between P-R, Rc between P-Q; RPR remains P-R, RQR remains R-Q.
    return par(rc, par(rb, RPR) + par(ra, RQR))


def nodal_ladder(vtest: float = VTEST) -> float:
    """Two-node test-source check, hand_calc only."""
    a11 = 1.0 / RS1 + 1.0 / RP1 + 1.0 / RS2
    a12 = -1.0 / RS2
    a21 = -1.0 / RS2
    a22 = 1.0 / RS2 + 1.0 / RP2 + 1.0 / RS3
    v1, _v2 = solve2(a11, a12, a21, a22, vtest / RS1, 0.0)
    return vtest / ((vtest - v1) / RS1)


def nodal_bridge(rx: float, vtest: float = VTEST) -> float:
    """Two-node test-source check, hand_calc only."""
    a11 = 1.0 / RPL + 1.0 / RQL + 1.0 / rx
    a12 = -1.0 / rx
    a21 = -1.0 / rx
    a22 = 1.0 / RPR + 1.0 / RQR + 1.0 / rx
    vl, vr = solve2(a11, a12, a21, a22, vtest / RPL, vtest / RPR)
    current = (vtest - vl) / RPL + (vtest - vr) / RPR
    return vtest / current


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
    elif abs(m) < CLEAR_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{num(m)}+-{num(s)}: {label}; {sign_note(diffs, m)}"


def seed_values(req: dict[str, float]) -> dict[str, list[float]]:
    return {arm: [req[arm]] * len(SEEDS) for arm in ARMS}


def print_regime(name: str, tag: str, req: dict[str, float]) -> None:
    res = seed_values(req)
    print(f"{name} ({tag})")
    for arm in ARMS:
        m, s = mean_sd(res[arm])
        print(f"  {arm} {num(m)}+-{num(s)} ohm")
    err_a = [a - b for a, b in zip(res["A_series_parallel"], res["B_official"])]
    err_c = [c - b for c, b in zip(res["C_swapped"], res["B_official"])]
    zeros = [0.0] * len(SEEDS)
    print(f"  residual A-B {num(mean_sd(err_a)[0])}+-{num(mean_sd(err_a)[1])} ohm")
    print(f"  residual C-B {num(mean_sd(err_c)[0])}+-{num(mean_sd(err_c)[1])} ohm")
    print(f"  paired A-B Req: {verdict(res['A_series_parallel'], res['B_official'])}")
    print(f"  paired C-B Req: {verdict(res['C_swapped'], res['B_official'])}")
    print(f"  paired residual A-B vs 0: {verdict(err_a, zeros)}")
    print(f"  paired residual C-B vs 0: {verdict(err_c, zeros)}")


def main() -> None:
    ra_l, rb_l, rc_l = delta_from_wye(RS1, RS2, RP1)
    ra_l_rw = RS2 + RP1 + (RS2 * RP1) / RS1
    req_a_l = series_parallel_ladder()
    req_b_l = official_ladder(delta_from_wye)
    req_c_l = official_ladder(wye_from_delta)
    nod_l = nodal_ladder()

    ra_m, rb_m, rc_m = delta_from_wye(RPL, RQL, RX_MODERATE)
    ra_m_rw = RQL + RX_MODERATE + (RQL * RX_MODERATE) / RPL
    req_a_b = series_parallel_bridge_shortcut()
    req_b_m = official_bridge(RX_MODERATE, delta_from_wye)
    req_c_m = official_bridge(RX_MODERATE, wye_from_delta)
    nod_m = nodal_bridge(RX_MODERATE)

    ra_g, rb_g, rc_g = delta_from_wye(RPL, RQL, RX_LARGE)
    req_b_g = official_bridge(RX_LARGE, delta_from_wye)
    req_c_g = official_bridge(RX_LARGE, wye_from_delta)
    nod_g = nodal_bridge(RX_LARGE)

    req_b_alt = official_bridge(RX_ALT_LARGE, delta_from_wye)
    req_c_alt = official_bridge(RX_ALT_LARGE, wye_from_delta)
    nod_alt = nodal_bridge(RX_ALT_LARGE)

    print("Synthetic Y-delta / delta-Y reduction toy; two-terminal networks; not a Wheatstone measurement bridge")
    print(
        f"ladder RS1={RS1:.0f}ohm RP1={RP1:.0f}ohm RS2={RS2:.0f}ohm RP2={RP2:.0f}ohm RS3={RS3:.0f}ohm"
    )
    print(
        f"bridge RPL={RPL:.0f}ohm RPR={RPR:.0f}ohm RQL={RQL:.0f}ohm RQR={RQR:.0f}ohm "
        f"RX_LARGE={RX_LARGE:.0f}ohm RX_MODERATE={RX_MODERATE:.0f}ohm"
    )
    print(
        f"seeds={len(SEEDS)} VTEST={VTEST} V clear_frac={CLEAR_FRAC:.4f} "
        f"hand_calc work_plan 30+25+50+40+35=180"
    )
    print("no integration step: algebraic series-parallel and official Y-delta, closed form")
    print(
        f"hand_calc ladder Y_to_delta R1={RS1:.0f} R2={RS2:.0f} R3={RP1:.0f} "
        f"Ra={ra_l:.10f}ohm Rb={rb_l:.10f}ohm Rc={rc_l:.10f}ohm "
        f"Ra_rewritten={ra_l_rw:.10f}ohm"
    )
    print(
        f"hand_calc ladder Req_A={req_a_l:.10f}ohm Req_B={req_b_l:.10f}ohm "
        f"Req_C={req_c_l:.10f}ohm residual_A-B={req_a_l - req_b_l:.3e}ohm "
        f"nodal={nod_l:.10f}ohm residual_B-nodal={req_b_l - nod_l:.3e}ohm"
    )
    print(
        f"hand_calc moderate Y_to_delta R1={RPL:.0f} R2={RQL:.0f} R3={RX_MODERATE:.0f} "
        f"Ra={ra_m:.10f}ohm Rb={rb_m:.10f}ohm Rc={rc_m:.10f}ohm "
        f"Ra_rewritten={ra_m_rw:.10f}ohm"
    )
    print(
        f"hand_calc moderate Req_A={req_a_b:.10f}ohm Req_B={req_b_m:.10f}ohm "
        f"Req_C={req_c_m:.10f}ohm residual_A-B={req_a_b - req_b_m:.10f}ohm "
        f"nodal={nod_m:.10f}ohm residual_B-nodal={req_b_m - nod_m:.3e}ohm"
    )
    print(
        f"hand_calc large_cross Y_to_delta R1={RPL:.0f} R2={RQL:.0f} R3={RX_LARGE:.0f} "
        f"Ra={ra_g:.10f}ohm Rb={rb_g:.10f}ohm Rc={rc_g:.10f}ohm"
    )
    print(
        f"hand_calc large_cross Req_A={req_a_b:.10f}ohm Req_B={req_b_g:.10f}ohm "
        f"Req_C={req_c_g:.10f}ohm residual_A-B={req_a_b - req_b_g:.10f}ohm "
        f"nodal={nod_g:.10f}ohm residual_B-nodal={req_b_g - nod_g:.3e}ohm"
    )

    print_regime(
        "series_parallel_ladder",
        "no cross edge, series-parallel ladder",
        {
            "A_series_parallel": req_a_l,
            "B_official": req_b_l,
            "C_swapped": req_c_l,
        },
    )
    print_regime(
        "large_cross_bridge",
        f"five-resistor bridge, RX={RX_LARGE:.0f}ohm very large",
        {
            "A_series_parallel": req_a_b,
            "B_official": req_b_g,
            "C_swapped": req_c_g,
        },
    )
    print_regime(
        "moderate_bridge",
        f"five-resistor bridge, RX={RX_MODERATE:.0f}ohm comparable to the arms",
        {
            "A_series_parallel": req_a_b,
            "B_official": req_b_m,
            "C_swapped": req_c_m,
        },
    )

    print(
        f"alternative large_cross RX={RX_ALT_LARGE:.0f}ohm (same bridge arms, not adopted) "
        f"Req_A={req_a_b:.10f}ohm Req_B={req_b_alt:.10f}ohm Req_C={req_c_alt:.10f}ohm "
        f"nodal={nod_alt:.10f}ohm residual_B-nodal={req_b_alt - nod_alt:.3e}ohm"
    )
    print(
        "  paired A-B Req: "
        + verdict([req_a_b] * len(SEEDS), [req_b_alt] * len(SEEDS))
    )
    print(
        "No winner declared: series-parallel ties the official transform on a ladder "
        "and is only close when the ignored cross is very large; on a moderate bridge "
        "the official Y-delta reduction is clearly better, and the swapped-direction formulae lose"
    )
    print("Real breadboard / DMM: 本页未运行; Wikipedia Y-delta transform 以原文为准")


if __name__ == "__main__":
    main()
