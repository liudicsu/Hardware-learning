#!/usr/bin/env python3
"""Synthetic power-on pose toy: absolute vs incremental encoders after a power
glitch. NOT a Feetech/Dynamixel driver, NOT the Z-index calibration toy from
2.4 (encoder_index_cal_toy.py); homing here is only a time cost. Stdlib only.

All arms read the SAME true shaft angle, the SAME glitch times, the SAME
unpowered drift (gravity sag / a hand moving the joint while the power is off)
and the SAME +-1 count read noise, with 4096 counts per encoder revolution.
  A_single_abs   single-turn absolute (12-bit): wakes with the angle modulo one
                 turn and maps it into the configured joint range
  B_incremental  counter restarts at 0 after power-on (read as the
                 calibration zero, 0 deg) and is trusted as is
  C_incr_home    incremental, then a homing move (search the hard stop, then
                 the index pulse within one turn) before the pose is trusted
  D_multi_batt   multi-turn absolute with battery-backed turn counter; if the
                 battery is flat it raises an alarm and homes like C
Scenarios: a joint whose range fits inside one encoder turn, a shaft whose
range spans three turns, and the same shaft with a flat backup battery.
"""
import math
import random

CPR = 4096
DEG_PER_COUNT = 360.0 / CPR
SEEDS = (0, 1, 2, 3, 4)
EVENTS = 20                 # power glitches per seed
CAL_ZERO = 0.0              # deg: pose that 0 counts meant at calibration
HOME_SPEED = 90.0           # deg/s of encoder shaft during homing
SETTLE_S = 0.5
TOL_DEG = 1.0
SCENARIOS = (
    # name, range_lo_deg, range_hi_deg, drift_sigma_deg, battery_ok
    ("single_turn_joint", -150.0, 150.0, 8.0, True),
    ("three_turn_shaft", 0.0, 1080.0, 60.0, True),
    ("three_turn_flat_battery", 0.0, 1080.0, 60.0, False),
)
ARMS = ("A_single_abs", "B_incremental", "C_incr_home", "D_multi_batt")


def read_counts(angle, rng):
    """Quantise to the encoder grid with +-1 count noise."""
    return round(angle / DEG_PER_COUNT) + rng.choice((-1, 0, 1))


def single_turn_map(counts, lo, hi):
    """Single-turn absolute: only counts mod CPR survive power-off. Pick the
    representative closest to the middle of [lo, hi]; unique when the range
    is shorter than one turn, a guess between turns when it is longer."""
    frac = (counts % CPR) * DEG_PER_COUNT
    k = round(((lo + hi) / 2 - frac) / 360.0)
    return frac + 360.0 * k


def homing_time(true_angle, lo):
    """Drive to the low hard stop, then one full turn (worst case) to the index pulse."""
    return (abs(true_angle - lo) + 360.0) / HOME_SPEED + SETTLE_S


def episode(arm, lo, hi, drift_sigma, battery_ok, rng_state, rng_noise):
    before = rng_state.uniform(lo, hi)
    drift = rng_state.gauss(0.0, drift_sigma)
    true = min(max(before + drift, lo), hi)
    counts = read_counts(true, rng_noise)
    if arm == "A_single_abs":
        est, t_valid, alarm = single_turn_map(counts, lo, hi), 0.0, False
    elif arm == "B_incremental":
        est, t_valid, alarm = CAL_ZERO, 0.0, False     # counter restarts: 0 counts = calibration zero
    elif arm == "C_incr_home":
        est, t_valid, alarm = counts * DEG_PER_COUNT, homing_time(true, lo), False
    else:
        if battery_ok:
            est, t_valid, alarm = counts * DEG_PER_COUNT, 0.0, False
        else:
            est, t_valid, alarm = counts * DEG_PER_COUNT, homing_time(true, lo), True
    err = abs(est - true)
    silent_wrong = err > TOL_DEG and t_valid == 0.0
    return err, t_valid, silent_wrong, alarm


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def main():
    print("Synthetic absolute vs incremental power-on toy; not a servo driver; homing = time cost only")
    print(f"CPR={CPR} deg_per_count={DEG_PER_COUNT:.4f} read_noise=+-1count seeds={len(SEEDS)} glitches_per_seed={EVENTS} "
          f"home_speed={HOME_SPEED:.0f}deg/s settle={SETTLE_S}s tol={TOL_DEG}deg")
    print("shared: true angle, glitch, unpowered drift and read-noise streams per seed")
    print("scenario arm wake_err_deg max_err_deg within_tol_% silent_wrong_% time_to_valid_s alarms (mean+-sd over seeds)")
    for name, lo, hi, sigma, battery in SCENARIOS:
        for arm in ARMS:
            errs, maxes, within, silent, tval, alarms = [], [], [], [], [], []
            for seed in SEEDS:
                rs = random.Random(100 + seed)        # same states for every arm
                rn = random.Random(200 + seed)        # same read noise for every arm
                rows = [episode(arm, lo, hi, sigma, battery, rs, rn) for _ in range(EVENTS)]
                errs.append(sum(r[0] for r in rows) / EVENTS)
                maxes.append(max(r[0] for r in rows))
                within.append(100.0 * sum(r[0] <= TOL_DEG for r in rows) / EVENTS)
                silent.append(100.0 * sum(r[2] for r in rows) / EVENTS)
                tval.append(sum(r[1] for r in rows) / EVENTS)
                alarms.append(sum(r[3] for r in rows))
            cols = [mean_sd(x) for x in (errs, maxes, within, silent, tval, alarms)]
            print(f"{name} {arm} " + " ".join(f"{m:.2f}+-{s:.2f}" for m, s in cols))
    print("single-turn absolute is exact only when the range fits one turn; multi-turn needs a kept turn count")
    print("XL330 Extended Position: power-off resets Present Position to one turn (e-Manual, 以原文为准)")
    print("No winner is declared; real servos / encoders / battery packs: 本页未运行")


if __name__ == "__main__":
    main()
