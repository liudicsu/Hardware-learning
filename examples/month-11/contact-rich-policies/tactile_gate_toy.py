#!/usr/bin/env python3
"""tactile_gate_toy.py: 1-D peg insertion, vision-only vs vision + gated tactile (stdlib).

The hole is at 0 mm. A vision policy aims with a fixed lateral bias plus noise.
Insertion succeeds if the lateral error is within TOL_MM.

  - vision only: one try at the vision estimate
  - + tactile (gated): on contact the skin reports a shear proportional to the
    lateral error (plus noise). Only if |shear| > GATE the policy shifts by
    -shear / ASSUMED_GAIN; up to MAX_PROBES contacts per trial
  - + tactile, swapped skin: same policy, but the replacement skin's true gain
    differs from the gain the policy was trained with (no re-calibration)

Fixed seed; all trials share the same vision draws. This is a toy, not AnySkin.
Also prints AnySkin (arXiv 2409.08276) insertion constants used in the lesson
prose — paper numbers, not toy measurements. Take the paper as source of truth.
"""
import random

SEED = 17
TRIALS = 200
BIAS_MM = 1.5
VISION_NOISE_MM = 0.6
TOL_MM = 0.5
SHEAR_NOISE = 0.3
GATE = 0.4
ASSUMED_GAIN = 1.0
SWAPPED_GAIN = 0.6
MAX_PROBES = 2

rng = random.Random(SEED)
vision = [BIAS_MM + rng.gauss(0.0, VISION_NOISE_MM) for _ in range(TRIALS)]
shear_noise = [[rng.gauss(0.0, SHEAR_NOISE) for _ in range(MAX_PROBES)] for _ in range(TRIALS)]


def run(true_gain, use_touch):
    ok, probes = 0, 0
    for i in range(TRIALS):
        err = vision[i]  # if |err| <= TOL_MM the peg slides in and we stop
        if use_touch:
            for k in range(MAX_PROBES):
                if abs(err) <= TOL_MM:
                    break
                shear = true_gain * err + shear_noise[i][k]
                probes += 1
                if abs(shear) > GATE:
                    err -= shear / ASSUMED_GAIN
        if abs(err) <= TOL_MM:
            ok += 1
    return ok / TRIALS, probes / TRIALS


succ_vis, _ = run(ASSUMED_GAIN, False)
succ_tac, probes_tac = run(ASSUMED_GAIN, True)
succ_swap, probes_swap = run(SWAPPED_GAIN, True)

print(f"seed={SEED}")
print(f"trials={TRIALS}")
print(f"tol_mm={TOL_MM}")
print(f"success_vision_only={succ_vis:.3f}")
print(f"success_tactile_gated={succ_tac:.3f}")
print(f"success_tactile_swapped={succ_swap:.3f}")
print(f"mean_probes_tactile={probes_tac:.2f}")
print(f"mean_probes_swapped={probes_swap:.2f}")
# AnySkin paper constants (arXiv 2409.08276, insertion, successes out of 10)
print("anyskin_plug_cam=1.7")
print("anyskin_plug_skin=6.7")
print("anyskin_plug_swap=5.3")
