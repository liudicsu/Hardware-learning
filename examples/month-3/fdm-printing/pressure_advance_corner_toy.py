#!/usr/bin/env python3
"""Pressure / linear advance on a shared corner path: K=0 vs tuned K vs over-tuned K.

Synthetic, stdlib only.  Not Marlin's or Klipper's planner, not a bit-exact
stepper ISR, and not the snap_fit strain toy.  Real printer calibration:
本页未运行.  Marlin / Klipper statements are 以原文为准.

Melt stand-in (1-D, compressible):
    ds/dt = feed(t) - q(s)        s = filament compression in the hot end [mm]
    q(s)  = q_ref * (s / s_ref) ** (1 / n),  s_ref = K_true * q_ref,  q(s <= 0) = 0
n = 1 is the linear spring of Marlin's unit "mm of compression per mm/s";
n < 1 is a shear-thinning stand-in, so a single linear K cannot be exact.
Feed with advance K (Klipper's pa_position = nominal + K * nominal_velocity):
    feed step = k_e * v * DT + K * k_e * (v_next - v)
Arms: A_K0 (K = 0), B_tuned (K read off a tuning tower), C_over (3 x B's K).

Common random numbers: per (regime, seed) the melt K_true, the exponent n,
the tower reading error and the filament-diameter sequence are drawn once
and shared by all three arms.  Arms differ only in K.

Explicit Euler is stable for this scalar ODE when DT < 2 / lambda_max with
lambda = dq/ds = q / (n s); the toy records the largest lambda it meets on
every run and asserts DT * lambda_max < 2.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
DT = 1e-4                 # s
K_E = 0.0333              # mm filament per mm of path (0.4 x 0.2 mm bead / 2.405 mm^2 of 1.75 mm filament)
BIN = 0.5                 # mm of path per width bin
CAL_SPEED = 100.0         # mm/s: the tuning tower runs at high flow (Klipper's advice)
TOWER_STEP = 0.005        # s: K resolution of the tower
OVER = 3.0                # C_over uses 3 x the tuned K
NUM_ZERO = 1e-9           # |m| and sd both below this: floating-point residue, not a gap

# name: (cruise mm/s, accel mm/s^2, corner mm/s, corners, edge mm)
REGIMES = {
    "sharp_corner": (100.0, 3000.0, 5.0, 4, 30.0),
    "slow_corner": (25.0, 500.0, 5.0, 4, 30.0),
    "steady_straight": (60.0, 3000.0, 60.0, 1, 120.0),
}
ARMS = ("A_K0", "B_tuned", "C_over")


def shared_draws(regime, seed):
    """Common random numbers: one melt, one tower reading, one filament for all arms."""
    rng = random.Random(f"{regime}/{seed}")
    k_true = rng.uniform(0.04, 0.08)          # s, direct-drive PLA stand-in
    n = rng.uniform(0.75, 1.0)
    read_err = rng.gauss(0.0, 0.15)           # relative error reading the tower
    dia = [rng.gauss(0.0, 0.004) for _ in range(2000)]   # relative filament-diameter error per bin
    return k_true, n, read_err, dia


def tuned_k(k_true, n, read_err):
    # Local slope ds/dq at the tower's flow is n * K_true; the eye adds read_err, the tower quantizes.
    return max(0.0, round(n * k_true * (1.0 + read_err) / TOWER_STEP) * TOWER_STEP)


def speed_profile(cruise, accel, corner, corners, edge):
    """Planner stand-in: per edge accelerate from `corner` (or cruise at the start) to cruise, brake to `corner`."""
    vs = []
    for c in range(corners):
        v = cruise if c == 0 else corner
        end = corner if c < corners - 1 else cruise
        x = 0.0
        while x < edge:
            rem = edge - x
            v_next = min(cruise, v + accel * DT, math.sqrt(end * end + 2.0 * accel * max(rem - v * DT, 0.0)))
            vs.append(v)
            x += v * DT
            v = v_next
    vs.append(v)
    return vs


def flow(s, q_ref, s_ref, n):
    return 0.0 if s <= 0.0 else q_ref * (s / s_ref) ** (1.0 / n)


def run(regime, seed, arm):
    cruise, accel, corner, corners, edge = REGIMES[regime]
    k_true, n, read_err, dia = shared_draws(regime, seed)
    kb = tuned_k(k_true, n, read_err)
    k = {"A_K0": 0.0, "B_tuned": kb, "C_over": OVER * kb}[arm]
    q_ref = K_E * CAL_SPEED
    s_ref = k_true * q_ref
    vs = speed_profile(cruise, accel, corner, corners, edge)
    s = s_ref * ((K_E * vs[0]) / q_ref) ** n   # start in steady state at the first speed
    x, dep, lam_max = 0.0, {}, 0.0
    feed_min, feed_max = float("inf"), float("-inf")
    for i in range(len(vs) - 1):
        v, v_next = vs[i], vs[i + 1]
        feed = K_E * v * DT + k * K_E * (v_next - v)
        feed_min, feed_max = min(feed_min, feed / DT), max(feed_max, feed / DT)
        q = flow(s, q_ref, s_ref, n)
        if s > 0.0:
            lam_max = max(lam_max, q / (n * s))
        b = int(x / BIN)
        dep[b] = dep.get(b, 0.0) + q * DT
        s += feed - q * DT
        x += v * DT
    assert DT * lam_max < 2.0, (regime, seed, arm, lam_max)
    nb = int(x / BIN)
    rel = [dep.get(b, 0.0) * (1.0 + dia[b % len(dia)]) ** 2 / (K_E * BIN) - 1.0 for b in range(nb)]
    return {
        "bulge": 100.0 * max(0.0, max(rel)),
        "starve": 100.0 * max(0.0, -min(rel)),
        "rms": 100.0 * math.sqrt(sum(r * r for r in rel) / len(rel)),
        "lam": lam_max, "k": k, "emin": feed_min, "emax": feed_max,
    }


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
    print("Synthetic 1-D compressible-melt pressure-advance toy; arms differ only in K; shared melt / tower / filament draws; not a real printer")
    print(f"DT={DT} s K_E={K_E} mm/mm bin={BIN} mm; tower at {CAL_SPEED:.0f} mm/s, step {TOWER_STEP} s; C_over = {OVER:.0f} x tuned K; seeds={len(SEEDS)}")
    res = {r: {a: [run(r, s, a) for s in SEEDS] for a in ARMS} for r in REGIMES}
    lam = max(x["lam"] for r in res.values() for a in r.values() for x in a)
    print(f"Euler stability: largest lambda = dq/ds met on any run {lam:.2f} 1/s -> need DT < 2/lambda_max = {2.0 / lam * 1000:.2f} ms; DT={DT * 1000:.1f} ms ok")
    for seed in SEEDS:
        k_true, n, read_err, _ = shared_draws("sharp_corner", seed)
        print(f"  sharp_corner seed {seed}: K_true={k_true:.4f} s n={n:.3f} local slope n*K_true={n * k_true:.4f} s tuned K={tuned_k(k_true, n, read_err):.3f} s")
    print("regime arm bulge_% starve_% rms_width_% K_s  extruder_feed_min..max_mm/s  (mean+-sd over seeds)")
    for r, (cruise, accel, corner, corners, edge) in REGIMES.items():
        print(f"{r} (cruise {cruise:.0f} mm/s, accel {accel:.0f} mm/s^2, corner {corner:.0f} mm/s, {corners} edge(s) x {edge:.0f} mm)")
        for a in ARMS:
            xs = res[r][a]
            cols = " ".join(f"{num(mean_sd([x[m] for x in xs])[0])}+-{num(mean_sd([x[m] for x in xs])[1])}" for m in ("bulge", "starve", "rms"))
            kk = mean_sd([x["k"] for x in xs])[0]
            print(f"  {a} {cols} K={kk:.4f} feed {min(x['emin'] for x in xs):.2f}..{max(x['emax'] for x in xs):.2f}")
        for other in ("A_K0", "C_over"):
            for m in ("bulge", "starve", "rms"):
                xa, xb = [x[m] for x in res[r][other]], [x[m] for x in res[r]["B_tuned"]]
                print(f"  paired {other[0]}-B {m}: {verdict(xa, xb)}")
    print("No winner declared: advance only acts on speed changes; a tuned K shrinks corner bulge and an over-tuned K starves the line; the melt is a 1-D stand-in")
    print("Real printer / tuning tower: 本页未运行; Marlin / Klipper numbers 以原文为准")


if __name__ == "__main__":
    main()
