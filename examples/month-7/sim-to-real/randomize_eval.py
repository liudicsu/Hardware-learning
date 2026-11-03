#!/usr/bin/env python3
"""Domain-randomization scan: friction / latency / sensor bias vs grasp success.

A short open-loop close-then-lift schedule that succeeds under nominal
parameters is replayed under friction×{1.0,0.7,0.4}, command delay {0,2,5}
steps, and vertical sensor bias {0, ±1.5 cm}. Per-cell rates use a Wilson
score interval (same idea as month-6 ``eval_report.py``).

Takeaway for lesson 7.4: latency and friction misspecification open the
reality gap even when the policy schedule is unchanged — motivate sysid + DR
before any SO-101 deployment.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

SEED = 13
N_TRIALS = 40
DT = 0.02
HORIZON = 60
LIFT_TARGET = 0.10  # metres
PALM_SPEED = 0.35   # m/s commanded when "lifting"


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n <= 0:
        return 0.0, 0.0, 0.0
    p = successes / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = (z / den) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return p, max(0.0, centre - half), min(1.0, centre + half)


@dataclass
class TrialResult:
    success: bool
    final_z: float
    slipped: bool


def simulate(friction_scale: float, delay: int, z_bias: float, rng: random.Random) -> TrialResult:
    """Kinematic lift with a single slip draw when the lift starts.

    Slip probability rises when friction is low **or** the close command is
    delayed relative to the lift (gripper still open when the palm rises).
    ``z_bias`` affects only the measured height used for the success check.
    """
    true_z = 0.0
    # delayed commands
    close_q = [False] * delay
    lift_q = [0.0] * delay
    closed = False
    lift_started = False
    slipped = False
    for t in range(HORIZON):
        intend_close = t >= 5
        intend_lift = PALM_SPEED if t >= 12 else 0.0
        close_q.append(intend_close)
        lift_q.append(intend_lift)
        do_close = close_q.pop(0)
        lift_cmd = lift_q.pop(0)
        if do_close:
            closed = True
        if lift_cmd > 0.0 and not lift_started:
            lift_started = True
            # one-shot slip draw at lift onset
            # base fail ~ 0.05 at fric=1, delay=0; grows with (1-fric) and delay
            fail_p = 0.05 + 0.55 * (1.0 - friction_scale) + 0.08 * delay
            # if close has not yet arrived when lift starts, almost certain slip
            if not closed:
                fail_p = max(fail_p, 0.9)
            fail_p = max(0.0, min(0.95, fail_p))
            if rng.random() < fail_p:
                slipped = True
        if lift_cmd > 0.0 and closed and not slipped:
            true_z += lift_cmd * DT
        elif slipped:
            true_z = max(0.0, true_z - 0.4 * DT)
    measured = true_z + z_bias
    success = (not slipped) and closed and measured >= LIFT_TARGET
    return TrialResult(success=success, final_z=true_z, slipped=slipped)


def scan_cell(friction_scale: float, delay: int, z_bias: float, seed: int):
    rng = random.Random(seed)
    ok = 0
    for _ in range(N_TRIALS):
        r = random.Random(rng.randint(0, 10**9))
        if simulate(friction_scale, delay, z_bias, r).success:
            ok += 1
    p, lo, hi = wilson(ok, N_TRIALS)
    return ok, p, lo, hi


def main() -> None:
    cells = [
        # fric, delay, bias
        (1.0, 0, 0.0),
        (0.7, 0, 0.0),
        (0.4, 0, 0.0),
        (1.0, 2, 0.0),
        (1.0, 5, 0.0),
        (1.0, 0, -0.015),
        (0.4, 5, -0.015),
    ]
    print("randomize_eval — DR scan friction×delay×z_bias (seed=%d, trials/cell=%d)"
          % (SEED, N_TRIALS))
    print("lift_target=%.2f m  palm_speed=%.2f m/s" % (LIFT_TARGET, PALM_SPEED))
    print("fric  delay  z_bias  ok/%d  rate   wilson95" % N_TRIALS)
    rates = {}
    for i, (fs, dly, zb) in enumerate(cells):
        ok, p, lo, hi = scan_cell(fs, dly, zb, seed=SEED + 19 * i)
        rates[(fs, dly, zb)] = p
        print(" %.1f  %5d  %+6.3f  %3d    %.3f  [%.3f, %.3f]" % (fs, dly, zb, ok, p, lo, hi))
    nom = rates[(1.0, 0, 0.0)]
    assert nom >= 0.85, "nominal success too low: %.3f" % nom
    assert rates[(1.0, 5, 0.0)] < nom - 0.2, "delay=5 should clearly hurt vs nominal"
    assert rates[(0.4, 0, 0.0)] < nom - 0.2, "low friction should clearly hurt"
    assert rates[(0.4, 5, -0.015)] <= 0.15, "worst cell should be near floor"
    print("ok: DR scan shows friction/delay/bias sensitivity (Wilson intervals)")


if __name__ == "__main__":
    main()
