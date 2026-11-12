#!/usr/bin/env python3
"""Zener shunt regulator vs LDO headroom.

Synthetic DC model, stdlib only.  Not a TI/NXP datasheet part, not a TVS
clamp, not a bridge rectifier, and not a Wheatstone bridge.
Real regulator bench: 本页未运行.  Wikipedia statements 以原文为准.

A Zener used as a shunt regulator is reverse-biased in parallel with the
load; a series resistor limits current, and once the voltage reaches the
Zener voltage the diode's low impedance holds the node near that value.
An LDO holds Vout while Vin - Vset stays at or above a declared headroom
(the remaining drop of a pass element that can be driven into saturation).
Power in the LDO is (Vin - Vout)*Iout + Vin*Iq.  Headroom and Vz are
declared toy parameters: the LDO article we read does not quote a dropout
in millivolts, so none is invented here.

Common random numbers: one shared Vin and one load per regime and seed.
Arms, shared Vin and load (per regime and seed):
  A_zener_shunt  : stiff Zener (rz = 0) plus series R
  B_ldo          : holds Vset when Vin - Vset >= HEADROOM, else Vin - HEADROOM
  C_uncapped     : same Zener but with only a tiny residual source R
                   (stand-in for a missing series resistor)
The arms differ only in the regulator.  Each seed also draws an independent
Zener and LDO reference tolerance.  No integration step: DC solve, so no
step-size stability criterion applies.

Regimes were written before the first run:
  in_regulation   : Vin well above Vz / headroom, moderate load
                    — A vs B near-tie on Vout
  below_headroom  : Vin - Vset < HEADROOM (and Vin close to / below Vz)
                    — B and A consistent lose (out of regulation); keep
  thermal_small_R : series R sized for a heavy load; Zener dissipation
                    compared with a declared thermal cap (in budget iff
                    P < P_THERMAL, a strict inequality matching
                    I_D * V_B < P_max); keep the loss against the cap
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared model parameters, written before the first run.  Not datasheet mV.
VZ_NOM = 5.0          # V
VSET_NOM = 5.0        # V
HEADROOM = 0.40       # V, toy headroom; not a quoted dropout
IQ = 0.002            # A, LDO quiescent (toy)
R_SERIES = 100.0      # ohm, nominal series R
R_HEAVY = 22.0        # ohm, sized so a 200 mA load still leaves IZ > 0
R_UNCAPPED = 0.05     # ohm, stand-in for a missing series resistor
TOL = 0.05            # V, +/- reference / Vz tolerance, independent per device
VIN_NOM = 12.0        # V, in-regulation and thermal regimes
VIN_LOW = 5.15        # V, 0.15 V above Vset, below HEADROOM 0.40 V
IL_MOD = 0.020        # A, moderate load
IL_HEAVY = 0.200      # A, heavy load the small R was sized for
IL_LIGHT = 0.010      # A, light load on the same small R (printed too)
VIN_SIGMA = 0.10      # V, shared Vin noise
IL_SIGMA = 0.002      # A, shared load noise
P_THERMAL = 0.50      # W, toy cap; in budget iff P < P_THERMAL (strict)

REGIMES = {
    "in_regulation":  {"vin": VIN_NOM, "il": IL_MOD, "r": R_SERIES},
    "below_headroom": {"vin": VIN_LOW, "il": IL_MOD, "r": R_SERIES},
    "thermal_small_R": {"vin": VIN_NOM, "il": IL_HEAVY, "r": R_HEAVY},
}
ARMS = ("A_zener_shunt", "B_ldo", "C_uncapped")


def shared_draw(regime, seed):
    """Common random numbers: one Vin and one load, used by every arm."""
    rng = random.Random(f"{regime}/{seed}")
    cfg = REGIMES[regime]
    return {
        "vin": cfg["vin"] + rng.gauss(0.0, VIN_SIGMA),
        "il": max(0.0, cfg["il"] + rng.gauss(0.0, IL_SIGMA)),
        "r": cfg["r"],
        "vz": VZ_NOM + rng.uniform(-TOL, TOL),
        "vset": VSET_NOM + rng.uniform(-TOL, TOL),
    }


def zener_solve(vin, il, r, vz):
    """Stiff Zener (rz = 0) with series R and a current-sink load."""
    if r <= 0.0:
        raise ValueError("r")
    # If the node can reach vz, Vout = vz and IZ = (vin - vz)/r - il.
    iz = (vin - vz) / r - il
    if iz >= 0.0 and vin >= vz:
        vout = vz
    else:
        vout = max(0.0, vin - il * r)
        iz = 0.0
    p = vz * iz if iz > 0.0 else 0.0
    in_reg = 1.0 if iz > 0.0 else 0.0
    thermal_ok = 1.0 if p < P_THERMAL else 0.0
    return {"vout": vout, "iz": iz, "p": p, "in_reg": in_reg, "thermal_ok": thermal_ok}


def ldo_solve(vin, il, vset):
    """Holds vset iff vin - vset >= HEADROOM (equality allowed)."""
    in_reg = 1.0 if (vin - vset) >= HEADROOM else 0.0
    if in_reg:
        vout = vset
    else:
        vout = max(0.0, vin - HEADROOM)
    iout = il
    p = (vin - vout) * iout + vin * IQ
    return {"vout": vout, "iz": 0.0, "p": p, "in_reg": in_reg, "thermal_ok": 1.0}


def measure(d, arm):
    if arm == "B_ldo":
        return ldo_solve(d["vin"], d["il"], d["vset"])
    r = R_UNCAPPED if arm == "C_uncapped" else d["r"]
    return zener_solve(d["vin"], d["il"], r, d["vz"])


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


def seed_row(regime, seed, arm):
    return measure(shared_draw(regime, seed), arm)


def main():
    print("Synthetic Zener-shunt vs LDO-headroom toy; shared Vin/load; not a datasheet part")
    print(f"seeds={len(SEEDS)} VZ_NOM={VZ_NOM:.1f} V VSET_NOM={VSET_NOM:.1f} V "
          f"HEADROOM={HEADROOM:.2f} V (toy, not a datasheet dropout) IQ={IQ:.3f} A "
          f"TOL=+/-{TOL:.2f} V P_THERMAL={P_THERMAL:.2f} W")
    print("No integration step: DC solve, no time-step criterion")
    print("Regimes, HEADROOM and P_THERMAL were written before the first run")
    print("headroom_rule: in regulation iff Vin - Vset >= HEADROOM (equality allowed)")
    print(f"headroom_boundary: Vin={VSET_NOM + HEADROOM:.10f} V in_reg="
          f"{1.0 if (VSET_NOM + HEADROOM - VSET_NOM) >= HEADROOM else 0.0:.0f}; "
          f"Vin={VSET_NOM + HEADROOM - 0.001:.10f} V in_reg="
          f"{1.0 if ((VSET_NOM + HEADROOM - 0.001) - VSET_NOM) >= HEADROOM else 0.0:.0f}")
    spare = VIN_LOW - VSET_NOM
    print(f"below_headroom_spare: Vin-Vset={spare:.10f} V ({VIN_LOW:.2f}-{VSET_NOM:.1f}), "
          f"below HEADROOM {HEADROOM:.2f} V")
    print("zener_in_reg_rule: in regulation iff I_Z>0 (rz=0 model; not a datasheet knee current I_Z,min)")
    # Hand calc, also printed from the same closed form (rz = 0, nominal values)
    ir = (VIN_NOM - VZ_NOM) / R_SERIES
    iz = ir - IL_MOD
    pz = VZ_NOM * iz
    print(f"hand_calc Vin={VIN_NOM:.1f} V R={R_SERIES:.0f} ohm VZ={VZ_NOM:.1f} V IL={IL_MOD:.3f} A: "
          f"IR=(Vin-VZ)/R={ir:.10f} A; IZ=IR-IL={iz:.10f} A; PZ=VZ*IZ={pz:.10f} W")
    ir_h = (VIN_NOM - VZ_NOM) / R_HEAVY
    iz_h = ir_h - IL_HEAVY
    pz_h = VZ_NOM * iz_h
    print(f"hand_calc thermal heavy: R={R_HEAVY:.0f} ohm IL={IL_HEAVY:.3f} A: "
          f"IR={ir_h:.10f} A IZ={iz_h:.10f} A PZ={pz_h:.10f} W "
          f"P_THERMAL={P_THERMAL:.2f} W thermal_ok={1 if pz_h < P_THERMAL else 0} "
          f"(strict P < P_THERMAL)")
    iz_l = ir_h - IL_LIGHT
    pz_l = VZ_NOM * iz_l
    print(f"hand_calc thermal light on same R: IL={IL_LIGHT:.3f} A: "
          f"IZ={iz_l:.10f} A PZ={pz_l:.10f} W thermal_ok={1 if pz_l < P_THERMAL else 0}")
    print("regime arm vout_V err_vs_5V p_W in_reg thermal_ok  (mean+-sd over seeds)")
    res = {}
    for regime in REGIMES:
        res[regime] = {a: {"vout": [], "err": [], "p": [], "in_reg": [], "thermal_ok": []} for a in ARMS}
        for seed in SEEDS:
            d = shared_draw(regime, seed)
            for a in ARMS:
                m = measure(d, a)
                res[regime][a]["vout"].append(m["vout"])
                res[regime][a]["err"].append(m["vout"] - VSET_NOM)
                res[regime][a]["p"].append(m["p"])
                res[regime][a]["in_reg"].append(m["in_reg"])
                res[regime][a]["thermal_ok"].append(m["thermal_ok"])
        cfg = REGIMES[regime]
        print(f"{regime} (Vin_nom={cfg['vin']:.2f} V, IL_nom={cfg['il']:.3f} A, R={cfg['r']:.2f} ohm)")
        for a in ARMS:
            row = res[regime][a]
            print(f"  {a} vout {fmt_pair(*mean_sd(row['vout']))} "
                  f"err {fmt_pair(*mean_sd(row['err']))} "
                  f"p {fmt_pair(*mean_sd(row['p']))} "
                  f"in_reg {fmt_pair(*mean_sd(row['in_reg']))} "
                  f"thermal_ok {fmt_pair(*mean_sd(row['thermal_ok']))}")
        print(f"  paired A-B vout: {verdict(res[regime]['A_zener_shunt']['vout'], res[regime]['B_ldo']['vout'])}")
        print(f"  paired A-B |err|: {verdict([abs(x) for x in res[regime]['A_zener_shunt']['err']], [abs(x) for x in res[regime]['B_ldo']['err']])}")
        print(f"  paired B in_reg vs 1: {verdict(res[regime]['B_ldo']['in_reg'], [1.0]*len(SEEDS))}")
        print(f"  paired A in_reg vs 1: {verdict(res[regime]['A_zener_shunt']['in_reg'], [1.0]*len(SEEDS))}")
        print(f"  paired C-A p: {verdict(res[regime]['C_uncapped']['p'], res[regime]['A_zener_shunt']['p'])}")
        print(f"  paired A thermal_ok vs 1: {verdict(res[regime]['A_zener_shunt']['thermal_ok'], [1.0]*len(SEEDS))}")
    # Light load on the same small R, same seeds as thermal_small_R (shared Vin, new IL)
    print("thermal_small_R light-load companion (same Vin draws, IL_nom=0.010 A, same R, not a deleted regime):")
    light_p, light_ok = [], []
    for seed in SEEDS:
        d = shared_draw("thermal_small_R", seed)
        d = dict(d)
        rng = random.Random(f"thermal_small_R/{seed}/light")
        d["il"] = max(0.0, IL_LIGHT + rng.gauss(0.0, IL_SIGMA))
        m = zener_solve(d["vin"], d["il"], R_HEAVY, d["vz"])
        light_p.append(m["p"])
        light_ok.append(m["thermal_ok"])
    print(f"  A_zener_shunt light p {fmt_pair(*mean_sd(light_p))} thermal_ok {fmt_pair(*mean_sd(light_ok))}")
    print(f"  paired light thermal_ok vs 1: {verdict(light_ok, [1.0]*len(SEEDS))}")
    # Alternatives on the same seeds
    print("alternative HEADROOM=0.20 V on below_headroom (same seeds):")
    alt_in = []
    base_in = []
    for seed in SEEDS:
        d = shared_draw("below_headroom", seed)
        base_in.append(ldo_solve(d["vin"], d["il"], d["vset"])["in_reg"])
        alt_in.append(1.0 if (d["vin"] - d["vset"]) >= 0.20 else 0.0)
    print(f"  B_ldo in_reg@0.20 {fmt_pair(*mean_sd(alt_in))} (default {fmt_pair(*mean_sd(base_in))})")
    print(f"  paired in_reg@0.20 vs default: {verdict(alt_in, base_in)}")
    print("alternative P_THERMAL=0.80 W on thermal_small_R (same seeds):")
    alt_ok = []
    base_ok = res["thermal_small_R"]["A_zener_shunt"]["thermal_ok"]
    alt_p = res["thermal_small_R"]["A_zener_shunt"]["p"]
    for p in alt_p:
        alt_ok.append(1.0 if p < 0.80 else 0.0)
    print(f"  A thermal_ok@0.80 {fmt_pair(*mean_sd(alt_ok))} (default {fmt_pair(*mean_sd(base_ok))})")
    print(f"  paired thermal_ok@0.80 vs default: {verdict(alt_ok, base_ok)}")
    print("No winner declared: in regulation the two hold nearby voltages; below headroom both drop out; a small series R that can feed a heavy load dumps too much into the Zener against the thermal cap; an uncapped shunt is worse")
    print("Real regulator bench: 本页未运行; Wikipedia statements 以原文为准")


if __name__ == "__main__":
    main()
