#!/usr/bin/env python3
"""lipm_track_toy.py: planar linear inverted pendulum (LIPM) CoM tracking (stdlib).

The CoM moves as  x'' = omega^2 * (x - p),  omega = sqrt(g / z_c),
where p is the ZMP (centre of pressure). p can only sit inside the foot,
here |p| <= FOOT_HALF_M. A PD + feed-forward controller picks the p it wants;
if that p is outside the foot it is clipped, and tracking degrades.

Two lateral sway references with the same amplitude:
  - slow (0.5 Hz): the ZMP it needs stays inside the foot
  - fast (1.0 Hz): the ZMP it needs leaves the foot -> clipping; once the
    capture point x + v/omega leaves the foot, no in-foot ZMP can stop the CoM
    and the robot must step (here: the run stops and reports a fall)
CoM measurements carry seeded Gaussian noise (SEED) so the run is repeatable.

Also prints ASAP (arXiv 2502.01143) Table V constants used in the lesson prose —
paper numbers, not toy measurements. Take the paper as source of truth.
No humanoid purchase is required; Isaac / MuJoCo training is not run on this page.
"""
import math
import random

SEED = 2
G = 9.81
Z_C = 0.8          # CoM height (m)
FOOT_HALF_M = 0.10  # ZMP limit (m)
AMP_M = 0.05        # sway amplitude (m)
DT = 0.005
T_END = 4.0
KP, KD = 40.0, 12.0
NOISE_M = 0.002

omega = math.sqrt(G / Z_C)


def run(freq_hz, rng):
    w = 2 * math.pi * freq_hz
    x, v = 0.0, AMP_M * w  # start on the reference
    err_sum, n, clipped = 0.0, 0, 0
    t = 0.0
    t_fall = None
    while t < T_END - 1e-9:
        x_des = AMP_M * math.sin(w * t)
        v_des = AMP_M * w * math.cos(w * t)
        a_des = -AMP_M * w * w * math.sin(w * t)
        x_meas = x + rng.gauss(0.0, NOISE_M)
        u = a_des + KP * (x_des - x_meas) + KD * (v_des - v)
        p = x_meas - u / (omega * omega)
        if abs(p) > FOOT_HALF_M:
            p = math.copysign(FOOT_HALF_M, p)
            clipped += 1
        acc = omega * omega * (x - p)
        v += acc * DT
        x += v * DT
        t += DT
        err_sum += abs(x - AMP_M * math.sin(w * t))
        n += 1
        if abs(x + v / omega) > FOOT_HALF_M:  # capture point left the foot
            t_fall = t
            break
    return err_sum / n, clipped / n, t_fall


rng = random.Random(SEED)
need_slow = AMP_M * (1 + (2 * math.pi * 0.5) ** 2 / omega ** 2)
need_fast = AMP_M * (1 + (2 * math.pi * 1.0) ** 2 / omega ** 2)
# peak capture point of the reference itself: A * sqrt(1 + (w/omega)^2)
cp_slow = AMP_M * math.sqrt(1 + (2 * math.pi * 0.5 / omega) ** 2)
cp_fast = AMP_M * math.sqrt(1 + (2 * math.pi * 1.0 / omega) ** 2)
mae_slow, clip_slow, fall_slow = run(0.5, rng)
_, _, fall_fast = run(1.0, rng)

print(f"seed={SEED}")
print(f"z_c={Z_C}")
print(f"omega={omega:.4f}")
print(f"foot_half_m={FOOT_HALF_M:.2f}")
print(f"zmp_needed_slow_m={need_slow:.4f}")
print(f"zmp_needed_fast_m={need_fast:.4f}")
print(f"cp_peak_ref_slow_m={cp_slow:.4f}")
print(f"cp_peak_ref_fast_m={cp_fast:.4f}")
print(f"com_mae_slow_m={mae_slow:.6f}")
print(f"clip_frac_slow={clip_slow:.3f}")
print(f"fell_slow={fall_slow is not None}")
print(f"fell_fast={fall_fast is not None}")
print(f"fall_time_fast_s={fall_fast:.3f}" if fall_fast is not None else "fall_time_fast_s=none")
# ASAP paper constants (arXiv 2502.01143 Table V / Sec. IV-C) for prose binding
print("asap_kick_gmpjpe_vanilla_mm=61.2")
print("asap_kick_gmpjpe_asap_mm=50.2")
print("asap_lebron_gmpjpe_vanilla_mm=159")
print("asap_lebron_gmpjpe_asap_mm=112")
print("asap_real_delta_dof=4")
