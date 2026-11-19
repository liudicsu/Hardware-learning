#!/usr/bin/env python3
"""Synthetic incremental-encoder speed toy: frequency window vs period.

Stdlib only. A shared shaft motion, a shared A-channel edge train and shared
jitter are drawn once per (regime, seed) and then read by every arm (common
random numbers).

Speed is a derivative of a quantized position. Arm A uses a fixed window of
counts (by frequency). Arm B times full A-channel periods (by period;
measurements at positions, not at clock instants). Arm C times a single
high pulse with no averaging, treating the pulse as if the duty were 0.5000.

The 12.0000 counts-per-motor-turn times 120.0000 gear equals 1440.0000
counts per output-shaft turn is a lesson stand-in, not a vendor fact. The
cited Wikipedia frequency-to-RPM worked example is 以原文为准 and is not a
toy output.

Not a re-teach of the x1/x2/x4 count table, not the existing 50 ms windowed
count worked example, not Z-index homing, not PWM dead time, not a re-run
of one_rev, not a scope capture, and not an FPGA timer-resolution claim.
Real encoder / timer capture: 本页未运行.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared toy parameters (lesson stand-in, not a vendor fact).
MOTOR_CPR = 12.0
GEAR = 120.0
SHAFT_CPR = MOTOR_CPR * GEAR  # 1440 counts per output-shaft turn at x4
PULSES_PER_REV = SHAFT_CPR / 4.0  # 360 A-channel pulses per output-shaft turn
EDGES_PER_REV_A = 2.0 * PULSES_PER_REV  # 720 rising+falling A edges per turn
TIMER_TICK = 1.0e-6
JITTER_FRAC = 0.0200
SYMMETRY = 0.3000
ASSUMED_DUTY_C = 0.5000
N_PERIODS_B = 4
T_END = 2.0
T0 = 0.0

METRICS = ("abs_rpm_err",)
ARMS = ("A_frequency", "B_period", "C_short_pulse")
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

# name: (true_rpm, window_s, declared expectation); written before the first run
REGIMES = {
    "low_speed": (
        10.0,
        0.0200,
        "B consistently below A on abs_rpm_err (period has lower speed error than frequency at low speed, modest jitter) - keep",
    ),
    "high_speed_long_window": (
        300.0,
        0.1000,
        "A and B may near-tie on abs_rpm_err (high speed and a long window) - keep",
    ),
}

REGIME_IDS = {"low_speed": 0, "high_speed_long_window": 1}

C_EXPECT = (
    "C loses to B on abs_rpm_err (single high-pulse period with large declared "
    "symmetry 0.3000 and no averaging) - keep"
)


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
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


def a_period(true_rpm):
    return 60.0 / (true_rpm * PULSES_PER_REV)


def quantize(dt, tick=TIMER_TICK):
    ticks = max(1, int(round(dt / tick)))
    return ticks * tick


def generate_edges(true_rpm, rng, jitter_frac, symmetry, t_end=T_END):
    period = a_period(true_rpm)
    t = rng.uniform(0.0, period)
    rises, falls = [], []
    last = -tick_floor()
    while t < t_end + 2.0 * period:
        tr = t + rng.gauss(0.0, jitter_frac * period)
        tf = t + symmetry * period + rng.gauss(0.0, jitter_frac * period)
        if tr <= last:
            tr = last + TIMER_TICK
        if tf <= tr:
            tf = tr + TIMER_TICK
        rises.append(tr)
        falls.append(tf)
        last = tf
        t += period
    return rises, falls


def tick_floor():
    return TIMER_TICK


def in_window(t, t0, window):
    return t0 <= t < t0 + window


def rpm_frequency(rises, falls, window, t0=T0):
    count = sum(1 for t in rises if in_window(t, t0, window)) + sum(
        1 for t in falls if in_window(t, t0, window)
    )
    rpm = (count / window) / EDGES_PER_REV_A * 60.0
    return rpm, count


def rpm_period(rises, n_periods=N_PERIODS_B, t0=T0, tick=TIMER_TICK):
    after = [t for t in rises if t >= t0]
    intervals = []
    for i in range(n_periods):
        if i + 1 >= len(after):
            break
        intervals.append(quantize(after[i + 1] - after[i], tick))
    mean_i = sum(intervals) / len(intervals)
    return 60.0 / (mean_i * PULSES_PER_REV)


def rpm_short_pulse(rises, falls, assumed_duty=ASSUMED_DUTY_C, t0=T0, tick=TIMER_TICK):
    for tr, tf in zip(rises, falls):
        if tr >= t0 and tf > tr:
            interval = quantize(tf - tr, tick)
            return 60.0 / (interval / assumed_duty * PULSES_PER_REV)
    raise RuntimeError("no high pulse after t0")


def run_regime(regime, seed, jitter_frac=JITTER_FRAC, window_scale=1.0):
    true_rpm, window, _exp = REGIMES[regime]
    window = window * window_scale
    rng = random.Random(seed + 1000 * REGIME_IDS[regime] + int(round(1000 * jitter_frac)) + int(round(100 * window_scale)))
    # Official path must share one stream per (regime, seed). Alternatives use a
    # distinct seed offset so their draws are also deterministic, but official
    # calls always pass the default jitter and window_scale.
    if jitter_frac == JITTER_FRAC and window_scale == 1.0:
        rng = random.Random(seed + 1000 * REGIME_IDS[regime])
    rises, falls = generate_edges(true_rpm, rng, jitter_frac, SYMMETRY)
    rpm_a, _count = rpm_frequency(rises, falls, window)
    rpm_b = rpm_period(rises)
    rpm_c = rpm_short_pulse(rises, falls)
    return {
        "A_frequency": {"abs_rpm_err": abs(rpm_a - true_rpm), "rpm": rpm_a},
        "B_period": {"abs_rpm_err": abs(rpm_b - true_rpm), "rpm": rpm_b},
        "C_short_pulse": {"abs_rpm_err": abs(rpm_c - true_rpm), "rpm": rpm_c},
    }


def main():
    print(
        "Encoder speed toy: frequency window vs period on a shared synthetic "
        "edge train (lesson stand-in 12.0000 x 120.0000 = 1440.0000 counts per "
        "output-shaft turn, not a vendor fact; not a scope capture, not an FPGA "
        "timer-resolution claim, not a re-run of one_rev)"
    )
    print(
        "Wikipedia Incremental encoder speed-measurement claims 以原文为准; "
        "the cited frequency-to-RPM worked example is 以原文为准 and is not a "
        "toy output; real encoder / timer capture: 本页未运行"
    )
    print(
        f"seeds={len(SEEDS)} motor_cpr={num(MOTOR_CPR)} gear={num(GEAR)} "
        f"shaft_cpr={num(SHAFT_CPR)} pulses_per_rev={num(PULSES_PER_REV)} "
        f"edges_per_rev_A={num(EDGES_PER_REV_A)} timer_tick={TIMER_TICK:.10e} "
        f"jitter_frac={num(JITTER_FRAC)} symmetry={num(SYMMETRY)} "
        f"assumed_duty_C={num(ASSUMED_DUTY_C)} n_periods_B={num(float(N_PERIODS_B))} "
        f"t0={num(T0)} t_end={num(T_END)} "
        f"low_speed_rpm={num(REGIMES['low_speed'][0])} "
        f"low_speed_window={num(REGIMES['low_speed'][1])} "
        f"high_speed_rpm={num(REGIMES['high_speed_long_window'][0])} "
        f"high_speed_window={num(REGIMES['high_speed_long_window'][1])}"
    )
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: the shaft motion, A-channel edge train and jitter "
        "draws are shared across arms at each regime and seed"
    )
    print(f"hand_calc motor_cpr * gear = {num(MOTOR_CPR)} * {num(GEAR)} = {num(SHAFT_CPR)}")
    print(
        f"hand_calc pulses_per_rev A-channel = {num(SHAFT_CPR)} / 4.0000 = {num(PULSES_PER_REV)}"
    )
    print(f"hand_calc frequency edges per rev (A rise+fall) = {num(EDGES_PER_REV_A)}")
    print(f"hand_calc timer_tick = {TIMER_TICK:.10e}")
    for name, (rpm, window, _exp) in REGIMES.items():
        period = a_period(rpm)
        expected_edges = window * EDGES_PER_REV_A * rpm / 60.0
        print(
            f"hand_calc {name} true_rpm={num(rpm)} A-period={period:.10e} "
            f"window={num(window)} expected A-edges={num(expected_edges)}"
        )
    print(
        f"hand_calc symmetry {num(SYMMETRY)} vs assumed_duty_C {num(ASSUMED_DUTY_C)}; "
        f"C scale factor {num(SYMMETRY)}/{num(ASSUMED_DUTY_C)} = {num(SYMMETRY / ASSUMED_DUTY_C)}"
    )
    print(f"hand_calc n_periods_B = {num(float(N_PERIODS_B))}")

    for r, (_rpm, _w, exp) in REGIMES.items():
        print(f"declared {r}: {exp}")
        print(f"declared {r} C: {C_EXPECT}")

    store = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_jitter = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_window = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    for seed in SEEDS:
        for r in REGIMES:
            official = run_regime(r, seed)
            jit = run_regime(r, seed, jitter_frac=0.0100)
            win = run_regime(r, seed, window_scale=2.0)
            for arm in ARMS:
                for m in METRICS:
                    store[r][arm][m].append(official[arm][m])
                    alt_jitter[r][arm][m].append(jit[arm][m])
                    alt_window[r][arm][m].append(win[arm][m])

    for r in REGIMES:
        print(f"regime {r}")
        for arm in ARMS:
            for m in METRICS:
                mu, sd = mean_sd(store[r][arm][m])
                print(f"  {arm} {m}: {num(mu)}+-{num(sd)}")
        for left, right in PAIRS:
            la = [a for a in ARMS if a.startswith(left + "_")][0]
            ra = [a for a in ARMS if a.startswith(right + "_")][0]
            for m in METRICS:
                print(f"  paired {left}-{right} {m}: {verdict(store[r][la][m], store[r][ra][m])}")

    print("alternatives on the same seeds (not adopted):")
    print("  alternative jitter_frac=0.0100")
    for r in REGIMES:
        print(f"  regime {r}")
        for left, right in (("B", "A"), ("C", "B")):
            la = [a for a in ARMS if a.startswith(left + "_")][0]
            ra = [a for a in ARMS if a.startswith(right + "_")][0]
            print(
                f"    paired {left}-{right} abs_rpm_err: "
                f"{verdict(alt_jitter[r][la]['abs_rpm_err'], alt_jitter[r][ra]['abs_rpm_err'])}"
            )
    print("  alternative window_scale=2.0000")
    for r in REGIMES:
        print(f"  regime {r}")
        for left, right in (("B", "A"), ("C", "B")):
            la = [a for a in ARMS if a.startswith(left + "_")][0]
            ra = [a for a in ARMS if a.startswith(right + "_")][0]
            print(
                f"    paired {left}-{right} abs_rpm_err: "
                f"{verdict(alt_window[r][la]['abs_rpm_err'], alt_window[r][ra]['abs_rpm_err'])}"
            )


if __name__ == "__main__":
    main()
