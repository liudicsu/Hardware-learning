#!/usr/bin/env python3
"""relative_traj_toy.py: absolute / delta / relative end-error under SE(2) (stdlib).

UMI PD2.1 / Fig.6 (arXiv 2402.10329 v3): three action representations.
  - absolute: global-frame targets (needs a shared world frame; calib bias sticks)
  - delta (contrast): each step is relative to the *previous* pose → per-step
    action noise compounds along the chunk
  - relative (UMI): one inference chunk with a *fixed anchor* T0; the *final*
    pose is rebuilt directly as T0 ∘ (T0^{-1} ∘ TN) — not a chain of deltas

Fair noise (endpoint-error demo): the same per-component noise magnitude is
added independently to every step-wise delta; for the fixed-anchor arm the
same magnitude is added *once* to the final T0^{-1} ∘ TN action only
(intermediate relative targets are not noised). Relative end error is
therefore a single draw (~0.001875 at default noise), not zero and not a
compounded pile-up.

Bias demo (a *different* conclusion from error accumulation): a fixed left-
multiplied world-frame bias B on measured poses cancels under relative actions
(T0^{-1} Tk), because B drops out of the product. That is not the same claim as
"relative does not accumulate step noise".

Also prints UMI paper constants used in the lesson prose (throughput, ATE)
— paper numbers, not toy measurements. Take the paper as source of truth.
Buying a GoPro is not required.
"""
import math
import random

SEED = 7
random.seed(SEED)


def se2_compose(p, a):
    """Compose pose p=(x,y,yaw) with body-frame action a=(dx,dy,dyaw)."""
    c, s = math.cos(p[2]), math.sin(p[2])
    return (
        p[0] + c * a[0] - s * a[1],
        p[1] + s * a[0] + c * a[1],
        p[2] + a[2],
    )


def se2_inv(p):
    c, s_ = math.cos(p[2]), math.sin(p[2])
    return (-c * p[0] - s_ * p[1], s_ * p[0] - c * p[1], -p[2])


def se2_mul(p, q):
    """p ∘ q for poses (q expressed in p's frame)."""
    return se2_compose(p, q)


def se2_delta(a, b):
    """Body-frame motion taking pose a to pose b: a^{-1} ∘ b."""
    return se2_mul(se2_inv(a), b)


def add_noise(a, noise):
    return (
        a[0] + random.uniform(-noise, noise),
        a[1] + random.uniform(-noise, noise),
        a[2] + random.uniform(-noise, noise),
    )


# True path: 8 relative actions from the origin
pose = (0.0, 0.0, 0.0)
truth = [pose]
for _ in range(8):
    a = (
        0.05 + random.uniform(-0.01, 0.01),
        random.uniform(-0.02, 0.02),
        random.uniform(-0.1, 0.1),
    )
    pose = se2_compose(pose, a)
    truth.append(pose)

# Absolute with a fixed calibration bias in the world frame
calib_err = (0.02, -0.015, 0.05)
abs_end_err = math.hypot(calib_err[0], calib_err[1])  # bias dominates end error

noise = 0.003
T0 = truth[0]

# True step-wise deltas and fixed-anchor relatives from the clean path
deltas = [se2_delta(truth[k], truth[k + 1]) for k in range(len(truth) - 1)]
rels_from_anchor = [se2_delta(T0, truth[k]) for k in range(1, len(truth))]

# Delta (contrast): compound noisy step-wise deltas — noise accumulates
delta_pose = T0
for d in deltas:
    delta_pose = se2_compose(delta_pose, add_noise(d, noise))
delta_end_err = math.hypot(delta_pose[0] - truth[-1][0], delta_pose[1] - truth[-1][1])

# Relative (UMI PD2.1): fixed-anchor reconstruction of the final pose only.
# One noisy (T0^{-1} ∘ TN); intermediate deltas are never chained.
rel_final_action = add_noise(rels_from_anchor[-1], noise)
rel_pose = se2_compose(T0, rel_final_action)
rel_end_err = math.hypot(rel_pose[0] - truth[-1][0], rel_pose[1] - truth[-1][1])

# Bias demo (separate conclusion): fixed left-multiplied world-frame bias B
B = (0.03, -0.02, 0.08)  # world-frame bias (m, m, rad)
meas_noise = 0.0005
meas = []
for T in truth:
    m = se2_mul(B, T)
    meas.append((m[0] + random.uniform(-meas_noise, meas_noise),
                 m[1] + random.uniform(-meas_noise, meas_noise),
                 m[2]))
# absolute replay: robot drives to the measured (biased) final pose
abs_biased_err = math.hypot(meas[-1][0] - truth[-1][0], meas[-1][1] - truth[-1][1])
# relative (fixed-anchor) replay: T0 ∘ (m0^{-1} ∘ m_N); B cancels in the product
rb_pose = se2_mul(T0, se2_mul(se2_inv(meas[0]), meas[-1]))
rel_biased_err = math.hypot(rb_pose[0] - truth[-1][0], rb_pose[1] - truth[-1][1])
# same, with zero noise: bias cancels exactly
meas0 = [se2_mul(B, T) for T in truth]
rb0 = se2_mul(T0, se2_mul(se2_inv(meas0[0]), meas0[-1]))
rel_bias_only_err = math.hypot(rb0[0] - truth[-1][0], rb0[1] - truth[-1][1])

print(f"seed={SEED}")
print(f"steps={len(deltas)}")
print(f"abs_calib_bias_m={abs_end_err:.6f}")
print(f"delta_accum_err_m={delta_end_err:.6f}")
print(f"relative_err_m={rel_end_err:.6f}")
print(f"abs_from_biased_meas_err_m={abs_biased_err:.6f}")
print(f"rel_from_biased_meas_err_m={rel_biased_err:.6f}")
print(f"rel_bias_only_err_m={rel_bias_only_err:.6f}")
# UMI paper constants (arXiv 2402.10329 v3 / project page) for prose binding
print(f"umi_cup_throughput_per_h=111")
print(f"spacemouse_throughput_per_h=35")
print(f"hand_throughput_per_h=231")
print(f"umi_field_success_pct=71.7")
print(f"umi_ate_mm=6.1")
print(f"umi_ate_deg=3.5")
