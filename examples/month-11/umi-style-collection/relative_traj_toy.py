#!/usr/bin/env python3
"""relative_traj_toy.py: absolute / delta / relative end-error under SE(2) (stdlib).

Same action sequence, three reconstructions:
  - absolute: global-frame targets with a fixed calibration bias
  - delta: each step is previous + noisy increment (noise accumulates)
  - relative (UMI-style): each action re-expressed vs the current EE
    (here: apply the true relative action from the measured pose → zero end error)

Bias demo: the demo was *recorded* with a measured EE pose that carries a
world-frame bias B (rigid SE(2) offset, e.g. a mis-registered SLAM / camera frame)
plus small per-frame noise. Replaying those measured poses as absolute targets
carries B onto the robot; relative actions inv(meas_t) ∘ meas_{t+1} cancel B
exactly (B cancels in the product), leaving only the per-frame noise.

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


# True path: 8 relative actions from the origin
pose = (0.0, 0.0, 0.0)
truth = [pose]
actions_rel = []
for _ in range(8):
    a = (
        0.05 + random.uniform(-0.01, 0.01),
        random.uniform(-0.02, 0.02),
        random.uniform(-0.1, 0.1),
    )
    actions_rel.append(a)
    pose = se2_compose(pose, a)
    truth.append(pose)

# Absolute with a fixed calibration bias in the world frame
calib_err = (0.02, -0.015, 0.05)
abs_end_err = math.hypot(calib_err[0], calib_err[1])  # bias dominates end error

# Delta: each step relative to previous, with per-step measurement noise
delta_pose = truth[0]
noise = 0.003
for a in actions_rel:
    noisy = (
        a[0] + random.uniform(-noise, noise),
        a[1] + random.uniform(-noise, noise),
        a[2] + random.uniform(-noise, noise),
    )
    delta_pose = se2_compose(delta_pose, noisy)
delta_end_err = math.hypot(delta_pose[0] - truth[-1][0], delta_pose[1] - truth[-1][1])

# Relative (UMI): restart each step from the measured current EE — perfect here
rel_pose = truth[0]
for a in actions_rel:
    rel_pose = se2_compose(rel_pose, a)
rel_end_err = math.hypot(rel_pose[0] - truth[-1][0], rel_pose[1] - truth[-1][1])

# Bias demo: world-frame bias on the measured EE during recording
def se2_inv(p):
    c, s_ = math.cos(p[2]), math.sin(p[2])
    return (-c * p[0] - s_ * p[1], s_ * p[0] - c * p[1], -p[2])


def se2_mul(p, q):
    """p ∘ q for poses (q expressed in p's frame)."""
    return se2_compose(p, q)


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
# relative replay: robot starts at its own true start and chains inv(m_t) ∘ m_{t+1}
rb_pose = truth[0]
for k in range(len(meas) - 1):
    rb_pose = se2_mul(rb_pose, se2_mul(se2_inv(meas[k]), meas[k + 1]))
rel_biased_err = math.hypot(rb_pose[0] - truth[-1][0], rb_pose[1] - truth[-1][1])
# same, with zero noise: bias cancels exactly
rb0 = truth[0]
meas0 = [se2_mul(B, T) for T in truth]
for k in range(len(meas0) - 1):
    rb0 = se2_mul(rb0, se2_mul(se2_inv(meas0[k]), meas0[k + 1]))
rel_bias_only_err = math.hypot(rb0[0] - truth[-1][0], rb0[1] - truth[-1][1])

print(f"seed={SEED}")
print(f"steps={len(actions_rel)}")
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
