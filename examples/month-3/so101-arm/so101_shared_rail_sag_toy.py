#!/usr/bin/env python3
"""Voltage sag on the SO-101 follower arm's shared 5 V servo rail: a toy.

Six bus servos are daisy-chained on one 5 V supply, so the voltage seen at a
servo is the supply voltage minus the I*R drops along the shared wiring
(Wikipedia "Voltage drop": V = I R, drops in the supply and return conductors
and connectors; 以原文为准).  This is a lumped-resistance stand-in, not SPICE
and not a bench scope on a real arm.  It is not the components-lesson MCU
brownout example.

Where the inputs come from:
  * the per-servo currents are the lesson's ST-3215-C001 figures (rated 0.5 A,
    stall 2.0 A, both given at 6 V; 以该课已引用规格为准) used as constant
    currents;
  * the 4 V floor is the lower end of Feetech's 4-7.4 V input range quoted in
    the lesson;
  * 4 A is the nameplate of the 5 V supply the lesson's BOM links;
  * the wiring resistances are declared toy parameters, not measured.
Real arm / PSU / stall test: 本页未运行.

Chain order from the supply: servo 1 shoulder_pan, 2 shoulder_lift,
3 elbow_flex, 4 wrist_flex, 5 wrist_roll, 6 gripper.  A supply lead (both
conductors, R_LEAD) feeds servo 1 and carries the total current; link k
(k = 1..5, servo k to servo k+1, both conductors, R_SEG) carries the sum of
the currents of servos k+1..6, hence
  V_k = V_SUP - R_LEAD*I_sum - sum over links j < k of R_SEG_j * I_downstream(j)
and V_min = min over k of V_k (the far end).

Common random numbers: for each (regime, seed) the six resistance jitter
factors (lead + five links) and the six current jitter factors are drawn once
from random.Random(f"{regime}/{seed}") and shared by all three arms.

Arms:
  A_ideal : no wiring resistance (all R = 0).
  B_wired : R_LEAD and R_SEG as declared (times the jitter).
  C_thick : a thicker, shorter supply lead and thicker links:
            R_LEAD_C = 0.03 ohm and R_SEG_C = 0.025 ohm (the SAME jitter).

Metrics per seed: v_min (V), i_sum (A), v_ok (1 if v_min >= V_FLOOR else 0),
i_ok (1 if i_sum <= I_NAMEPLATE else 0).  Pairs B-A and C-B on every metric
in every regime.  An alternatives block is declared before the run and is
not adopted.

Regimes and parameters were written before the first run:
  rated       : none stalled -> B sags below A but v_ok of B vs A may near-tie
                or tie (the rail stays valid); i_ok all 1
  one_stall   : gripper, servo 6 -> B's v_min near or below 4 V, kept as it
                comes
  multi_stall : servos 2, 3 and 6 -> B consistently drops below 4 V (v_ok
                loses to A) and i_sum exceeds 4 A for every arm, so "a 4 A
                supply is enough" loses; C keeps v_min at or above 4 V - keep
  all_stall   : all six -> every arm exceeds 4 A; C may also fall below 4 V
                - keep as it comes
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
V_SUP = 5.0                     # V, the lesson's 5 V rail
I_RATED = 0.5                   # A, ST-3215-C001 rated current at 6 V
I_STALL = 2.0                   # A, ST-3215-C001 stall current at 6 V
V_FLOOR = 4.0                   # V, lower end of Feetech's 4-7.4 V input range
I_NAMEPLATE = 4.0               # A, nameplate of the 5 V supply in the BOM
R_LEAD = 0.10                   # ohm, supply lead, both conductors (toy)
R_SEG = 0.05                    # ohm, each link, both conductors (toy)
R_LEAD_C = 0.03                 # ohm, thicker/shorter supply lead (toy)
R_SEG_C = 0.025                 # ohm, thicker links (toy)
R_JITTER = 0.2                  # each wiring resistance times uniform(0.8, 1.2)
I_JITTER = 0.1                  # each servo current times uniform(0.9, 1.1)

JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex",
          "wrist_flex", "wrist_roll", "gripper")
ARMS = ("A_ideal", "B_wired", "C_thick")
METRICS = ("v_min", "i_sum", "v_ok", "i_ok")
ARM_R = {"A_ideal": (0.0, 0.0), "B_wired": (R_LEAD, R_SEG),
         "C_thick": (R_LEAD_C, R_SEG_C)}
STALLED = {"rated": (), "one_stall": (6,), "multi_stall": (2, 3, 6),
           "all_stall": (1, 2, 3, 4, 5, 6)}
DECLARED = {
    "rated": "B sags below A but v_ok of B vs A may near-tie or tie (the rail stays valid); i_ok all 1",
    "one_stall": "B's v_min near or below 4 V, kept as it comes",
    "multi_stall": "B consistently drops below 4 V (v_ok loses to A) and i_sum exceeds 4 A for every arm, "
                   "so \"a 4 A supply is enough\" loses; C keeps v_min at or above 4 V - keep",
    "all_stall": "every arm exceeds 4 A; C may also fall below 4 V - keep as it comes",
}


def shared_draw(regime, seed):
    """Common random numbers: six resistance jitter factors and six current jitter factors, once per (regime, seed)."""
    rng = random.Random(f"{regime}/{seed}")
    rj = [rng.uniform(1 - R_JITTER, 1 + R_JITTER) for _ in range(6)]
    ij = [rng.uniform(1 - I_JITTER, 1 + I_JITTER) for _ in range(6)]
    return rj, ij


def run_arm(arm, regime, seed, lead=None, seg=None):
    rj, ij = shared_draw(regime, seed)
    stalls = STALLED[regime]
    base_lead, base_seg = ARM_R[arm]
    lead = base_lead if lead is None else lead
    seg = base_seg if seg is None else seg
    r_lead = 0.0 if arm == "A_ideal" else lead * rj[0]
    r_link = [0.0] * 5 if arm == "A_ideal" else [seg * f for f in rj[1:]]
    cur = [(I_STALL if (k + 1) in stalls else I_RATED) * ij[k] for k in range(6)]
    i_sum = sum(cur)
    down = [sum(cur[j + 1:]) for j in range(5)]
    drop, v_min = 0.0, V_SUP
    for k in range(6):
        if k > 0:
            drop += r_link[k - 1] * down[k - 1]
        v_min = min(v_min, V_SUP - r_lead * i_sum - drop)
    return {"v_min": v_min, "i_sum": i_sum,
            "v_ok": 1 if v_min >= V_FLOOR else 0,
            "i_ok": 1 if i_sum <= I_NAMEPLATE else 0}


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0  # identical values: no floating residue in mean or sd
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    """Half-up rounding on the shortest decimal repr; tiny non-zero values in scientific form."""
    if x != 0.0 and abs(x) < 5e-4:
        return format(Decimal(repr(x)), ".3e")
    s = format(Decimal(repr(x)), ".4f")
    return "0.0000" if s == "-0.0000" else s


def sign_note(diffs, m):
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def collect(regime, lead=None, seg=None):
    return {arm: [run_arm(arm, regime, s, lead, seg) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [x[key] for x in rows]


def report(regime):
    stalls = STALLED[regime]
    res = collect(regime)
    txt = ", ".join(f"{k} {JOINTS[k - 1]}" for k in stalls)
    desc = f"stalled: {txt}; the rest draw rated current" if txt else "no stalled servo; all six draw rated current"
    print(f"{regime} ({desc}):")
    print("  declared: " + DECLARED[regime])
    print("  i_sum per seed (A, shared currents): " + " ".join(num(x) for x in col(res["A_ideal"], "i_sum")))
    for arm in ARMS:
        print(f"  {arm} " + " ".join(f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS))
    for a, b in (("B_wired", "A_ideal"), ("C_thick", "B_wired")):
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: {verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("SO-101 shared 5 V servo rail voltage sag toy; lumped-resistance stand-in for the daisy-chained bus servos")
    print(f"seeds={len(SEEDS)} V_SUP={num(V_SUP)} V V_floor={num(V_FLOOR)} V I_nameplate={num(I_NAMEPLATE)} A "
          f"rated={num(I_RATED)} A stall={num(I_STALL)} A R_lead={num(R_LEAD)} ohm R_seg={num(R_SEG)} ohm "
          f"jitter +-{num(100 * R_JITTER)} % on each R and +-{num(100 * I_JITTER)} % on each I "
          "(declared toy parameters, not measured)")
    print("chain from the supply: lead -> 1 shoulder_pan -> 2 shoulder_lift -> 3 elbow_flex -> 4 wrist_flex -> 5 wrist_roll -> 6 gripper; "
          "the lead carries the total current and link k carries the sum of the currents downstream of it")
    print("Common random numbers: one resistance-jitter draw and one current-jitter draw per (regime, seed), shared by all three arms")
    print("Not SPICE and not a bench scope on a real arm; not the components-lesson MCU brownout example")
    print("Regimes and parameters were written before the first run")
    print("rule: V_k = V_SUP - R_LEAD*I_sum - sum over links j < k of R_SEG_j * I_downstream(j); V_min = min over the six servos; "
          "V = I R in the supply and return conductors and connectors")
    # Labelled hand calculation on the nominal chain (no jitter draw).
    print(f"hand_calc nominal currents: rated 6 x {num(I_RATED)} = {num(6 * I_RATED)} A; stall 6 x {num(I_STALL)} = "
          f"{num(6 * I_STALL)} A (the lesson's existing totals, echoed)")
    print(f"hand_calc one IR drop: {num(6 * I_STALL)} A x {num(R_LEAD)} ohm = {num(6 * I_STALL * R_LEAD)} V on the supply lead")
    print(f"hand_calc nominal B_wired v_min in all_stall = 5.0 - 1.2 - 0.05*(10+8+6+4+2) = {num(V_SUP - 6 * I_STALL * R_LEAD - R_SEG * 30)} V")
    print(f"hand_calc nominal B_wired v_min in rated = 5.0 - 0.3 - 0.05*(2.5+2.0+1.5+1.0+0.5) = "
          f"{num(V_SUP - 6 * I_RATED * R_LEAD - R_SEG * 7.5)} V")
    for regime in STALLED:
        report(regime)
    print("alternatives (declared before the run, not adopted; same seeds):")
    alt = collect("multi_stall", seg=0.03)
    print(f"  multi_stall with R_SEG={num(0.03)} ohm: paired B-A v_ok@alt: "
          f"{verdict(col(alt['B_wired'], 'v_ok'), col(alt['A_ideal'], 'v_ok'))}")
    alt = collect("rated", lead=0.20)
    print(f"  rated with R_LEAD={num(0.20)} ohm: paired B-A v_ok@alt: "
          f"{verdict(col(alt['B_wired'], 'v_ok'), col(alt['A_ideal'], 'v_ok'))}")
    alt = collect("multi_stall", lead=0.05)
    std = collect("multi_stall")
    print(f"  multi_stall with C_thick R_LEAD_C={num(0.05)} ohm: paired C-B v_ok@alt: "
          f"{verdict(col(alt['C_thick'], 'v_ok'), col(std['B_wired'], 'v_ok'))}")
    print("No winner beyond the arithmetic: thicker, shorter wiring keeps the far-end voltage legal under several stalls, "
          "but no wiring change makes 4 A cover them")
    print("Real SO-101 arm / PSU / stall test: 本页未运行; per-servo currents 以该课已引用规格为准; "
          "Wikipedia Voltage drop statements 以原文为准")


if __name__ == "__main__":
    main()
