#!/usr/bin/env python3
"""Rolling shutter vs global shutter: one frame of a moving vertical edge.

Synthetic row-scan stand-in, stdlib only.  Not a real CMOS sensor, not a
camera driver, not the eight-point toy and not the stereo-sigma toy on this
page.  Real camera / rolling-shutter lab: 本页未运行.  Wikipedia Rolling
shutter statements 以原文为准.

What the Wikipedia "Rolling shutter" body says (and what this toy keeps): a
rolling shutter captures a frame by scanning across the scene, so not all
parts of the image are recorded at the same instant, although playback shows
the whole frame at once; this gives predictable distortions of fast-moving
objects (skew, wobble).  A global shutter captures the entire frame at the
same instant.  The result depends on the readout speed of the sensor.

Model: an image of H rows sees one vertical edge that moves horizontally at
v px/s.  The frame is stamped t0.  Row r is sampled at
  A_global  : t0                      (every row at one instant)
  B_rolling : t0 + r * DT_ROW         (declared row readout time)
  C_slow    : t0 + r * DT_ROW * SLOW  (a much slower readout)
The detected edge column in row r is x0 + v * t_r + noise_r.  Every arm is
read by the same naive estimator that treats the frame as global: edge
position at t0 = mean column over rows, skew = |fitted slope| * (H - 1).
Metrics: pos_err_px = |estimate - true x(t0)|, skew_px.

Common random numbers: for each (regime, seed) the start column x0, the
speed jitter and the per-row detection noise are drawn once and shared by
every arm.  A, B and C differ only in the row timestamps.
No integration step: closed-form positions, no ODE, no time-step criterion.

Regimes and parameters were written before the first run:
  static   : v = 0 px/s; A, B, C must tie (a static scene cannot invent
             motion); keep
  moderate : v = 300 px/s; B consistent warp (skew, pos_err) vs A; C
             consistent lose vs B; keep
  fast     : v = 1500 px/s; same expectations, larger; keep
Alternatives, also written before the first run and run on the same seeds:
  DT_ROW = 15 us (a faster readout) on moderate;
  an RS-aware estimator (line-fit intercept at row 0, i.e. at t0) on fast.
H, DT_ROW, SLOW, SIGMA_PX and the speeds are declared toy parameters, not a
datasheet or a measured sensor.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
H = 480                 # rows (toy)
DT_ROW = 30e-6          # s per row (toy readout)
SLOW = 4                # C reads out SLOW times slower (toy)
SIGMA_PX = 0.3          # per-row edge detection noise, px (toy)
V_JITTER = 0.10         # +-10 % speed jitter per seed
ARMS = ("A_global", "B_rolling", "C_slow")
REGIMES = {"static": 0.0, "moderate": 300.0, "fast": 1500.0}


def shared_draws(regime, seed):
    """Common random numbers for one (regime, seed): x0, speed, row noise."""
    rng = random.Random(f"rs|{regime}|{seed}")
    x0 = rng.uniform(200.0, 440.0)
    v = REGIMES[regime] * (1.0 + rng.uniform(-V_JITTER, V_JITTER))
    noise = [rng.gauss(0.0, SIGMA_PX) for _ in range(H)]
    return x0, v, noise


def row_time(arm, r, dt_row=DT_ROW):
    if arm == "A_global":
        return 0.0
    if arm == "B_rolling":
        return r * dt_row
    return r * dt_row * SLOW


def capture(arm, regime, seed, dt_row=DT_ROW):
    x0, v, noise = shared_draws(regime, seed)
    cols = [x0 + v * row_time(arm, r, dt_row) + noise[r] for r in range(H)]
    return x0, cols


def fit_line(cols):
    n = len(cols)
    rbar = (n - 1) / 2.0
    cbar = sum(cols) / n
    sxx = sum((r - rbar) ** 2 for r in range(n))
    sxy = sum((r - rbar) * (c - cbar) for r, c in enumerate(cols))
    b = sxy / sxx
    return cbar - b * rbar, b, cbar


def measure(arm, regime, seed, dt_row=DT_ROW, rs_aware=False):
    x0, cols = capture(arm, regime, seed, dt_row)
    a, b, cbar = fit_line(cols)
    est = a if rs_aware else cbar
    return {"pos_err": abs(est - x0), "skew": abs(b) * (H - 1)}


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


METRICS = ("pos_err", "skew")


def collect(regime, **kw):
    return {arm: [measure(arm, regime, s, **kw) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [r[key] for r in rows]


def report(regime):
    res = collect(regime)
    vs = [shared_draws(regime, s)[1] for s in SEEDS]
    print(f"{regime} (V_NOM={REGIMES[regime]:.1f} px/s):")
    print("  speed per seed px/s: " + " ".join(f"{v:.4f}" for v in vs))
    for arm in ARMS:
        parts = [f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS]
        print(f"  {arm} " + " ".join(parts))
    for key in METRICS:
        print(f"  paired B-A {key}: {verdict(col(res['B_rolling'], key), col(res['A_global'], key))}")
    for key in METRICS:
        print(f"  paired C-B {key}: {verdict(col(res['C_slow'], key), col(res['B_rolling'], key))}")
    return res


def main():
    print("Synthetic row-scan toy: one moving vertical edge, global vs rolling vs slow rolling readout; not a real CMOS")
    print(f"seeds={len(SEEDS)} H={H} rows DT_ROW={DT_ROW * 1e6:.1f} us SLOW={SLOW} SIGMA_PX={SIGMA_PX:.1f} px "
          f"V_JITTER=+-{V_JITTER * 100:.0f} % (declared toy parameters, not datasheet values)")
    print("No integration step: closed-form positions, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print(f"row_stamp rule: row r sampled at t0 + r*DT_ROW; r=0 -> {row_time('B_rolling', 0) * 1e3:.4f} ms, "
          f"r=1 -> {row_time('B_rolling', 1) * 1e3:.4f} ms, r={H - 1} -> {row_time('B_rolling', H - 1) * 1e3:.4f} ms "
          f"(C: r={H - 1} -> {row_time('C_slow', H - 1) * 1e3:.4f} ms; A: every row at t0)")
    ro = (H - 1) * DT_ROW
    v = REGIMES["moderate"]
    print(f"hand_calc readout=(H-1)*DT_ROW={H - 1}*{DT_ROW * 1e6:.1f} us={ro * 1e3:.4f} ms; "
          f"skew at v={v:.1f} px/s = v*readout = {v * ro:.4f} px; "
          f"naive mean-row bias = v*(H-1)/2*DT_ROW = {v * ro / 2:.4f} px")
    vf = REGIMES["fast"]
    print(f"hand_calc fast v={vf:.1f} px/s: skew={vf * ro:.4f} px bias={vf * ro / 2:.4f} px; "
          f"C (SLOW={SLOW}) at v={v:.1f} px/s: skew={v * ro * SLOW:.4f} px")
    print("estimator: every arm is read as if global (mean column over rows = position at t0)")
    for regime in REGIMES:
        report(regime)
    print("alternative DT_ROW=15.0 us on moderate (same seeds):")
    alt = collect("moderate", dt_row=15e-6)
    for key in METRICS:
        print(f"  paired B-A {key}@alt: {verdict(col(alt['B_rolling'], key), col(alt['A_global'], key))}")
    print("alternative RS-aware estimator on fast (same seeds; line-fit intercept at row 0 = position at t0):")
    alt = collect("fast", rs_aware=True)
    for arm in ARMS:
        print(f"  {arm}@rs_aware pos_err {fmt_pair(*mean_sd(col(alt[arm], 'pos_err')))}")
    print(f"  paired B-A pos_err@rs_aware: {verdict(col(alt['B_rolling'], 'pos_err'), col(alt['A_global'], 'pos_err'))}")
    print(f"  paired C-B pos_err@rs_aware: {verdict(col(alt['C_slow'], 'pos_err'), col(alt['B_rolling'], 'pos_err'))}")
    print("No winner declared: a global shutter freezes motion; a rolling shutter warps it in proportion to speed times readout time and ties on a static scene")
    print("Real camera / rolling-shutter lab: 本页未运行; Wikipedia Rolling shutter statements 以原文为准")


if __name__ == "__main__":
    main()
