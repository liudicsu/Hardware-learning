#!/usr/bin/env python3
"""encoder_index_cal_toy.py: mechanical homing via Z-index (stdlib).

This is MECHANICAL HOMING / ZERO via an incremental encoder's index (Z)
pulse — a once-per-revolution reference. It is NOT FOC electrical-angle /
commutation-offset calibration (that lives in 11.2 and the avoid-list).
Magnetic-encoder magnet misalignment is a different failure mode and is
not modelled here.

After power-up an incremental encoder only knows relative counts (boot
count = 0 at a UNKNOWN lab angle). The Z pulse gives a repeatable per-rev
reference. A one-time calibration stores the angular offset from that
index to the machine's mechanical zero (hard stop / fixture):

    est_fixture = (count - count_at_index) * 2π / CPR
                  + (z_lab_at_capture - phi_index)

with phi_index := OFFSET_TRUE after a successful true-index capture
(fixture lab angle relative to disc-Z zero). Uncalibrated keeps
phi_index = 0, so the fixture frame stays shifted.

Arms share ONE motion trajectory; per-arm RNGs come from one master seed:
  uncalibrated   phi_index left at 0 (index still captured for anchoring)
  calibrated     phi_index learned from the first accepted TRUE index
  missed_index   high miss probability — true Z edges dropped (may never home)
  false_index    a spurious pulse is forced BEFORE the first true Z

Metrics at the shared stop-at-fixture:
  stop_err_rad           |est_fixture - true_fixture|
  index_events_accepted  first-capture pulses that set the anchor
  false_index_count      accepted pulses that were noise
  missed_true_index      true Z edges dropped

Real encoder hardware / scope-on-Z: 本页未运行.
usage: python3 encoder_index_cal_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 24
CPR = 1440
DT = 0.001
BOOT_LAB = 1.20                # unknown lab angle at power-up (count resets to 0)
OFFSET_TRUE = 0.35             # fixture (mech zero) lab angle mod 2π vs disc Z at 0
OMEGA = 2.0 * math.pi          # rad/s
T_SPIN = 1.40                  # long enough to pass at least one true Z
T_APPROACH = 0.40
NOISE_COUNT_STD = 0.35
# Stop target: fixture zero on the NEXT turn after boot.
# true lab at stop = OFFSET_TRUE + 2π
STOP_LAB = OFFSET_TRUE + 2.0 * math.pi


def true_lab(t: float) -> float:
    if t <= T_SPIN:
        return BOOT_LAB + OMEGA * t
    tau = t - T_SPIN
    start = BOOT_LAB + OMEGA * T_SPIN
    if tau >= T_APPROACH:
        return STOP_LAB
    return start + (STOP_LAB - start) * (tau / T_APPROACH)


def run_arm(name: str, rng: random.Random, miss_p: float,
            force_false_before_z: bool, do_cal: bool) -> dict:
    n = int(round((T_SPIN + T_APPROACH) / DT)) + 1
    # First true Z after boot: ceil(BOOT_LAB / 2π) * 2π
    next_z = math.ceil(BOOT_LAB / (2.0 * math.pi) - 1e-12) * (2.0 * math.pi)
    if next_z <= BOOT_LAB + 1e-12:
        next_z += 2.0 * math.pi

    phi_index = 0.0
    have_index = False
    count_at_index = 0
    z_lab_at_capture = 0.0
    accepted = 0
    false_acc = 0
    missed_true = 0
    last_lab = BOOT_LAB
    false_injected = False
    est = 0.0
    true_fix = 0.0

    for k in range(n):
        t = k * DT
        lab = true_lab(t)
        # Counts are relative to boot: zero at BOOT_LAB.
        ideal_count = (lab - BOOT_LAB) / (2.0 * math.pi) * CPR
        count = int(round(ideal_count + rng.gauss(0.0, NOISE_COUNT_STD)))

        true_z = False
        if last_lab < next_z <= lab + 1e-12:
            true_z = True
            next_z += 2.0 * math.pi
        last_lab = lab

        saw = False
        is_false = False
        # Force one false pulse shortly after start, before first true Z.
        if force_false_before_z and not false_injected and t >= 0.05 and not have_index:
            saw = True
            is_false = True
            false_injected = True
        elif true_z:
            if rng.random() < miss_p:
                missed_true += 1
            else:
                saw = True

        if saw and not have_index:
            accepted += 1
            if is_false:
                false_acc += 1
            count_at_index = count
            z_lab_at_capture = lab
            have_index = True
            if do_cal and not is_false:
                phi_index = OFFSET_TRUE
            # false capture: phi_index stays 0 (wrong zero claim)

        true_fix = lab - OFFSET_TRUE
        if not have_index:
            # No absolute reference: counts from boot claimed as fixture-frame
            # zero. BOOT_LAB is unknown to the estimator (not added back).
            est = count * 2.0 * math.pi / CPR
        else:
            ang_since = (count - count_at_index) * 2.0 * math.pi / CPR
            est_lab = ang_since + z_lab_at_capture
            est = est_lab - phi_index

    return {
        "name": name,
        "stop_err_rad": abs(est - true_fix),
        "index_events_accepted": accepted,
        "false_index_count": false_acc,
        "missed_true_index": missed_true,
        "phi_index": phi_index,
        "have_index": have_index,
        "final_est": est,
        "final_true": true_fix,
    }


def main() -> None:
    master = random.Random(SEED)
    seeds = [master.randrange(1 << 30) for _ in range(4)]
    arms = [
        ("uncalibrated", seeds[0], 0.0, False, False),
        ("calibrated", seeds[1], 0.0, False, True),
        ("missed_index", seeds[2], 1.0, False, True),   # miss every true Z
        ("false_index", seeds[3], 0.0, True, True),
    ]
    print(f"seed={SEED}")
    print("THIS IS MECHANICAL HOMING / Z-INDEX, NOT FOC commutation offset")
    print(f"CPR={CPR} BOOT_LAB={BOOT_LAB} OFFSET_TRUE_rad={OFFSET_TRUE}")
    print("shared trajectory; arms differ only in cal / miss / false settings")
    print(f"{'arm':<14} {'stop_err_rad':>12} {'accepted':>8} {'false':>6} {'missed':>6} {'phi':>8}")
    results = []
    for name, sd, miss_p, force_false, do_cal in arms:
        r = run_arm(name, random.Random(sd), miss_p, force_false, do_cal)
        results.append(r)
        print(
            f"{r['name']:<14} {r['stop_err_rad']:12.4f} {r['index_events_accepted']:8d} "
            f"{r['false_index_count']:6d} {r['missed_true_index']:6d} {r['phi_index']:8.4f}"
        )
    by = {r["name"]: r for r in results}
    assert by["calibrated"]["stop_err_rad"] < 0.05
    assert by["uncalibrated"]["stop_err_rad"] > 0.2
    assert by["calibrated"]["stop_err_rad"] < by["uncalibrated"]["stop_err_rad"]
    assert by["missed_index"]["missed_true_index"] >= 1
    assert by["missed_index"]["have_index"] is False
    assert by["false_index"]["false_index_count"] >= 1
    assert by["false_index"]["stop_err_rad"] > by["calibrated"]["stop_err_rad"]
    print(
        "ok: mechanical Z-index homing (not FOC); cal beats uncal on clean index; "
        "missed/false index shown as failure modes; encoder hardware 本页未运行"
    )


if __name__ == "__main__":
    main()
