#!/usr/bin/env python3
"""Kelvin (four-terminal) sensing vs two-wire resistance measurement.

Synthetic DC model, stdlib only.  Not a real meter, not a Fluke/Keysight
specification, not a Wheatstone bridge and not a Thevenin source.
Real 4-wire bench measurement: 本页未运行.  Wikipedia statements 以原文为准.

The meter forces a test current I through the force pair and reads a
voltage V; the reading is R_meas = V / I.
  A_two_wire : one pair does both, so V includes 2 * (r_lead + r_contact).
  B_kelvin   : force pair carries I; a separate sense pair (r_sense in series
               with the voltmeter input R_IN) touches the DUT itself.
  C_nulled   : two-wire after a REL / null taken with the tips shorted: the
               null removes the leads as they were at the short, but the
               contacts at the DUT are new contacts and the leads have warmed.
Shared by every arm (common random numbers, per regime, seed and part):
DUT value, lead and contact resistances, lead warming, meter gain error,
thermal EMF and voltage noise.  Arms differ only in how the leads are wired.
The model is DC steady state: no time stepping, so no integration-step
criterion applies.  Lead resistance in the GUM toy above is not simulated;
this toy simulates only lead / contact resistance, not temperature or
loading of the circuit under test.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
PARTS = 20
R_IN = 1e10            # ohm, voltmeter input in the ohms converter
ALPHA_CU = 0.00393     # 1/K, copper lead tempco
NUM_ZERO = 1e-9        # |m| and sd both below this: floating-point residue, not a gap

# name: (DUT low ohm, DUT high ohm, test current A, lead ohm range, contact ohm range)
REGIMES = {
    "shunt_small_dut": (0.005, 0.020, 0.1, (0.02, 0.05), (0.001, 0.010)),
    "large_dut": (5e3, 2e4, 1e-4, (0.02, 0.05), (0.001, 0.010)),
    "zero_lead": (0.005, 0.020, 0.1, (0.0, 0.0), (0.0, 0.0)),
}
ARMS = ("A_two_wire", "B_kelvin", "C_nulled")


def shared_part(regime, seed, part):
    """Common random numbers: one DUT, one set of leads, one meter error, used by all arms."""
    lo, hi, _, (l0, l1), (c0, c1) = REGIMES[regime]
    rng = random.Random(f"{regime}/{seed}/{part}")
    return {
        "R": rng.uniform(lo, hi),
        "lead": [rng.uniform(l0, l1) for _ in range(4)],      # force+, force-, sense+, sense-
        "contact": [rng.uniform(c0, c1) for _ in range(4)],   # at the DUT
        "null_contact": [rng.uniform(c0, c1) for _ in range(2)],  # at the shorted tips
        "warm": rng.uniform(0.0, 5.0),                        # K the leads warm after the null
        "gain": rng.uniform(-100e-6, 100e-6),                 # meter reading error, shared
        "emf": rng.uniform(-2e-6, 2e-6),                      # V thermal EMF, shared
        "noise": rng.gauss(0.0, 0.5e-6),                      # V on the reading
        "null_noise": rng.gauss(0.0, 0.5e-6),                 # V on the null reading
    }


def par(a, b):
    return a * b / (a + b)


def reading(v, d):
    return v * (1.0 + d["gain"]) + d["emf"] + d["noise"]


def measure(regime, d, arm):
    current = REGIMES[regime][2]
    warm = 1.0 + ALPHA_CU * d["warm"]
    if arm == "B_kelvin":
        r_sense = d["lead"][2] + d["lead"][3] + d["contact"][2] + d["contact"][3]
        v_dut = current * par(d["R"], R_IN + r_sense)
        return reading(v_dut * (R_IN / (R_IN + r_sense)), d) / current
    loop = (d["lead"][0] + d["lead"][1]) * warm + d["contact"][0] + d["contact"][1]
    r_meas = reading(current * par(d["R"] + loop, R_IN), d) / current
    if arm == "A_two_wire":
        return r_meas
    null_loop = d["lead"][0] + d["lead"][1] + d["null_contact"][0] + d["null_contact"][1]
    null = (current * par(null_loop, R_IN) * (1.0 + d["gain"]) + d["emf"] + d["null_noise"]) / current
    return r_meas - null


def seed_metrics(regime, seed, arm):
    errs = []
    for part in range(PARTS):
        d = shared_part(regime, seed, part)
        errs.append((measure(regime, d, arm) - d["R"]) / d["R"] * 100.0)
    return {"abs": sum(abs(e) for e in errs) / PARTS, "bias": sum(errs) / PARTS}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
        return f"{x:.3e}"
    return f"{x:.4f}"


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


def main():
    print("Synthetic DC Kelvin toy; arms differ only in lead wiring; shared DUT / lead / contact / meter draws; not a real meter")
    print(f"seeds={len(SEEDS)} parts={PARTS} R_IN={R_IN:.0e} ohm; gain +-100 ppm, thermal EMF +-2 uV, noise 0.5 uV rms (shared); DC steady state, no time step")
    d = shared_part("shunt_small_dut", 0, 0)
    loop = d["lead"][0] + d["lead"][1] + d["contact"][0] + d["contact"][1]
    print(f"shunt_small_dut seed 0 part 0: R={d['R'] * 1000:.3f} mOhm, force loop leads+contacts={loop * 1000:.3f} mOhm -> two-wire adds {loop / d['R'] * 100:.1f} %")
    print("regime arm abs_err_% bias_%  (mean+-sd over seeds of the per-seed part means)")
    res = {r: {a: [seed_metrics(r, s, a) for s in SEEDS] for a in ARMS} for r in REGIMES}
    for r, (lo, hi, cur, lead, cont) in REGIMES.items():
        print(f"{r} (DUT {lo:g}..{hi:g} ohm, I={cur:g} A, lead {lead[0]:g}..{lead[1]:g} ohm, contact {cont[0]:g}..{cont[1]:g} ohm)")
        for a in ARMS:
            xs = res[r][a]
            print(f"  {a} " + " ".join(f"{num(mean_sd([x[m] for x in xs])[0])}+-{num(mean_sd([x[m] for x in xs])[1])}" for m in ("abs", "bias")))
        for other in ("A_two_wire", "C_nulled"):
            for m in ("abs", "bias"):
                xa, xb = [x[m] for x in res[r][other]], [x[m] for x in res[r]["B_kelvin"]]
                print(f"  paired {other[0]}-B {m}: {verdict(xa, xb)}")
    print("No winner declared: Kelvin removes lead and contact resistance, not gain error or thermal EMF; at 10 kOhm the leads hide under the meter's own error")
    print("Real 4-wire bench: 本页未运行; Wikipedia statements 以原文为准")


if __name__ == "__main__":
    main()
