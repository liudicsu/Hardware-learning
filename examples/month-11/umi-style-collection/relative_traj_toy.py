#!/usr/bin/env python3
"""relative_traj_toy.py: absolute / delta / relative end-error under SE(2) (stdlib).

Same action sequence, three reconstructions:
  - absolute: global-frame targets with a fixed calibration bias
  - delta: each step is previous + noisy increment (noise accumulates)
  - relative (UMI-style): each action re-expressed vs the current EE
    (here: apply the true relative action from the measured pose → zero end error)

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

print(f"seed={SEED}")
print(f"steps={len(actions_rel)}")
print(f"abs_calib_bias_m={abs_end_err:.6f}")
print(f"delta_accum_err_m={delta_end_err:.6f}")
print(f"relative_err_m={rel_end_err:.6f}")
# UMI paper constants (arXiv 2402.10329 v3 / project page) for prose binding
print(f"umi_cup_throughput_per_h=111")
print(f"spacemouse_throughput_per_h=35")
print(f"hand_throughput_per_h=231")
print(f"umi_field_success_pct=71.7")
print(f"umi_ate_mm=6.1")
print(f"umi_ate_deg=3.5")
