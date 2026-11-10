#!/usr/bin/env python3
"""Synthetic half-wave vs diode-bridge rectifier with a smoothing capacitor. Stdlib only.

Source: v(t) = VPK sin(2 pi F t) behind a winding resistance RS (no transformer regulation,
no leakage inductance). Diodes are ideal switches with a series forward drop VF each:
  A_half     one diode then C || R            rectified source = v - VF when v > VF
  B_bridge   four-diode bridge then C || R    rectified source = |v| - 2 VF (two diodes conduct)
  C_noC      the same bridge, no capacitor    v_out = max(0, |v| - 2 VF) R / (R + RS)
Capacitor node (A, B): C dV/dt = i_d - V / R, with i_d = max(0, v_rect - V) / RS while the
diodes conduct. Integrated with forward Euler at step DT. Euler is stable for this linear node
when DT <= 2 / (1/(RS C) + 1/(R C)) (the conducting phase is the stiff one); the toy prints the
limit for every regime and asserts DT is far below it; the tests check decay at 0.98x and
growth at 1.02x of that limit, and that DT and DT/2 agree.
Correctness criterion: with ripple pp small, the linear-discharge law V_pp ~= I / (k F C)
(k = 1 half-wave, k = 2 full-wave; Wikipedia Ripple (electrical): V_pp = I / (2 f C) for
full-wave) must agree with the simulated pp within 25 % (the law ignores the conduction time,
so it over-predicts). A run whose ripple pp exceeds 10 % of its mean is labelled "not DC".
Common random numbers: per seed the line amplitude (+-5 %), the capacitor tolerance (+-20 %),
the load (+-10 %) and VF (0.65-0.75 V) are drawn once and shared by every arm and regime
(each regime scales the nominal C and R). Metrics over the last 10 cycles of 20:
vdc (mean output, V), ripple (pp, V), ipk (peak diode current, A; stress proxy).
Labels: tie = identical on every seed; numerically zero = |paired mean| and sd both < 1e-9
(effectively a tie, no sign count); |m| <= sd = near-tie; |m| > sd = consistent gap (small if
|m| < 20 % of the smaller arm mean, else clear), with a sign count.
Not a Wheatstone bridge (a measurement bridge) and not TVS surge clamping.
Real mains / transformer / PSU bench: 本页未运行. Wikipedia formulas: 以原文为准.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
F = 50.0  # Hz line frequency
VPK = 12.0 * math.sqrt(2.0)  # V, 12 V rms secondary
RS = 0.5  # ohm, winding + wiring resistance
DT = 5e-6  # s, Euler step
CYCLES, MEASURE = 20, 10
TOL_LAW = 0.25
DC_LIMIT = 0.10
NUM_ZERO = 1e-9
ARMS = ("A_half", "B_bridge", "C_noC")
# name: (nominal C in uF, nominal R in ohm); pre-declared before the first run
REGIMES = {
    "small_C_heavy": (470.0, 20.0),
    "medium": (1000.0, 50.0),
    "large_C_light": (4700.0, 200.0),
    "tiny_C_heavy": (220.0, 15.0),
}


def shared_draws(seed):
    """Common random numbers: one draw per seed, shared by every arm and regime."""
    rng = random.Random(seed)
    return {"amp": rng.uniform(0.95, 1.05), "c": rng.uniform(0.8, 1.2), "r": rng.uniform(0.9, 1.1), "vf": rng.uniform(0.65, 0.75)}


def euler_h_max(c, r):
    return 2.0 / (1.0 / (RS * c) + 1.0 / (r * c))


def euler_amp(h, c, r):
    """Growth factor of one Euler step on the conducting node, |1 - h (1/(RS C) + 1/(R C))|."""
    return abs(1.0 - h * (1.0 / (RS * c) + 1.0 / (r * c)))


def simulate(arm, regime, draws, dt=DT):
    c_nom, r_nom = REGIMES[regime]
    c, r = c_nom * 1e-6 * draws["c"], r_nom * draws["r"]
    vpk, vf = VPK * draws["amp"], draws["vf"]
    n = round(CYCLES / F / dt)
    start = round((CYCLES - MEASURE) / F / dt)
    v = 0.0
    vs, ipk = [], 0.0
    for i in range(n):
        src = vpk * math.sin(2.0 * math.pi * F * i * dt)
        rect = src - vf if arm == "A_half" else abs(src) - 2.0 * vf
        if arm == "C_noC":
            v = max(0.0, rect) * r / (r + RS)
            i_d = v / r
        else:
            i_d = max(0.0, rect - v) / RS
            v += dt * (i_d - v / r) / c
        if i >= start:
            vs.append(v)
            ipk = max(ipk, i_d)
    vdc = sum(vs) / len(vs)
    return {"vdc": vdc, "ripple": max(vs) - min(vs), "ipk": ipk, "c": c, "r": r}


def law(arm, res):
    k = 1.0 if arm == "A_half" else 2.0
    return (res["vdc"] / res["r"]) / (k * F * res["c"])


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-5:
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


def verdict(xa, xb):
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


KEYS = ("vdc", "ripple", "ipk")


def main():
    print("Synthetic half-wave vs bridge rectifier with C || R; ideal diodes + series VF; not a PSU bench, not a Wheatstone bridge")
    print(f"F={F} Hz VPK={VPK:.4f} V RS={RS} ohm DT={DT * 1e6:.0f} us cycles={CYCLES} (last {MEASURE} measured) seeds={len(SEEDS)}")
    draws = [shared_draws(s) for s in SEEDS]
    for regime, (c_nom, r_nom) in REGIMES.items():
        c_min = c_nom * 1e-6 * 0.8
        h = euler_h_max(c_min, r_nom * 0.9)
        assert DT < 0.05 * h
        print(f"Euler limit {regime}: h_max={h * 1e6:.1f} us at the smallest C and R drawn; DT={DT * 1e6:.0f} us; |1 - DT/tau|={euler_amp(DT, c_min, r_nom * 0.9):.6f} < 1")
    print("regime arm vdc_V ripple_pp_V ipk_A  (mean+-sd over seeds)")
    for regime, (c_nom, r_nom) in REGIMES.items():
        print(f"{regime} (C={c_nom:.0f} uF, R={r_nom:.0f} ohm nominal)")
        res = {arm: [simulate(arm, regime, d) for d in draws] for arm in ARMS}
        for arm in ARMS:
            cells = " ".join("{}+-{}".format(*map(num, mean_sd([x[k] for x in res[arm]]))) for k in KEYS)
            share = max(x["ripple"] / x["vdc"] for x in res[arm])
            tag = "DC" if share <= DC_LIMIT else "not DC (ripple > 10 % of vdc)"
            print(f"  {arm} {cells}; worst ripple/vdc {100 * share:.1f} % -> {tag}")
        for arm in ("A_half", "B_bridge"):
            ratios = [x["ripple"] / law(arm, x) for x in res[arm]]
            lo, hi = min(ratios), max(ratios)
            ok = all(abs(q - 1.0) <= TOL_LAW for q in ratios)
            small = all(x["ripple"] / x["vdc"] <= DC_LIMIT for x in res[arm])
            state = "within 25 %" if ok else ("outside 25 %" + ("" if small else " (ripple not small; law not expected to hold)"))
            print(f"  law {arm}: simulated / (I/({1 if arm == 'A_half' else 2} F C)) = {lo:.4f}..{hi:.4f} -> {state}")
        for x, y in (("B_bridge", "A_half"), ("C_noC", "B_bridge")):
            for k in KEYS:
                print(f"  paired {x[0]}-{y[0]} {k}: {verdict([r[k] for r in res[x]], [r[k] for r in res[y]])}")
    d0 = draws[0]
    a, b = simulate("B_bridge", "medium", d0), simulate("B_bridge", "medium", d0, DT / 2)
    print(f"step check (B, medium, seed 0): DT vs DT/2 vdc {abs(a['vdc'] - b['vdc']):.3e} V, ripple {abs(a['ripple'] - b['ripple']):.3e} V")
    print("No winner declared: the bridge halves the ripple period and the charge per refill, but pays a second diode drop; without C the output is not DC")
    print("Real mains / transformer / PSU bench: 本页未运行; Wikipedia formulas 以原文为准")


if __name__ == "__main__":
    main()
