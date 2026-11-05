#!/usr/bin/env python3
"""tag_error_jog.py: tag pose error → limited Twist-style jog (stdlib).

Eye-in-hand toy geometry: fixed seed synthesises a tag pose in the camera
frame and a current EE pose in the base frame. Converts tag→base (simple
fixed cam-in-EE extrinsic), builds a pose error (position + small-angle
axis-angle proxy), scales to a Twist (vx..wz), then applies deadzone +
per-axis clamps. No OpenCV / ROS / real camera.
usage: python3 tag_error_jog.py
"""
from __future__ import annotations

import math
import random

SEED = 98
# Proportional gains (toy defaults, not vendor numbers).
KP_LIN = 0.80  # 1/s
KP_ANG = 1.20  # 1/s
DEADZONE_POS = 0.005  # m
DEADZONE_ANG = 0.020  # rad
V_MAX = 0.12  # m/s
W_MAX = 0.40  # rad/s
# Fixed cam→EE extrinsic (eye-in-hand): cam origin in EE, identity rotation.
CAM_IN_EE = (0.00, 0.00, 0.08)  # m, camera ahead of flange along +z_ee


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def axis_angle_from_small_rot(rx: float, ry: float, rz: float) -> tuple[float, float, float, float]:
    """Treat (rx,ry,rz) as a small-angle rotation vector → axis * angle."""
    ang = math.sqrt(rx * rx + ry * ry + rz * rz)
    if ang < 1e-12:
        return 0.0, 0.0, 1.0, 0.0
    return rx / ang, ry / ang, rz / ang, ang


def main() -> None:
    rng = random.Random(SEED)
    # Synthetic tag pose in camera frame (metres, small-angle rad).
    tag_cam = (
        rng.uniform(-0.04, 0.04),
        rng.uniform(-0.03, 0.03),
        rng.uniform(0.25, 0.45),
        rng.uniform(-0.15, 0.15),
        rng.uniform(-0.15, 0.15),
        rng.uniform(-0.20, 0.20),
    )
    # Current EE pose in base (position + small-angle orientation).
    ee_base = (
        rng.uniform(0.20, 0.35),
        rng.uniform(-0.10, 0.10),
        rng.uniform(0.15, 0.30),
        rng.uniform(-0.05, 0.05),
        rng.uniform(-0.05, 0.05),
        rng.uniform(-0.10, 0.10),
    )
    # Desired: drive tag to a fixed look-at in camera (0,0,z_des,0,0,0).
    z_des = 0.30
    # Tag in EE ≈ cam_in_ee + R≈I * tag_cam (identity rotation toy).
    tag_ee = (
        CAM_IN_EE[0] + tag_cam[0],
        CAM_IN_EE[1] + tag_cam[1],
        CAM_IN_EE[2] + tag_cam[2],
        tag_cam[3],
        tag_cam[4],
        tag_cam[5],
    )
    # Tag in base ≈ ee_base ⊕ tag_ee (small-angle add for orientation).
    tag_base = (
        ee_base[0] + tag_ee[0],
        ee_base[1] + tag_ee[1],
        ee_base[2] + tag_ee[2],
        ee_base[3] + tag_ee[3],
        ee_base[4] + tag_ee[4],
        ee_base[5] + tag_ee[5],
    )
    # Target EE: keep orientation aligned with tag, place EE so tag sits at
    # (0,0,z_des) in camera → EE should sit tag_base shifted by -cam_in_ee
    # along the approach, with zero relative orientation error goal.
    goal_ee = (
        tag_base[0] - CAM_IN_EE[0],
        tag_base[1] - CAM_IN_EE[1],
        tag_base[2] - CAM_IN_EE[2] - (tag_cam[2] - z_des),
        tag_base[3],
        tag_base[4],
        tag_base[5],
    )
    err_p = (
        goal_ee[0] - ee_base[0],
        goal_ee[1] - ee_base[1],
        goal_ee[2] - ee_base[2],
    )
    err_r = (
        goal_ee[3] - ee_base[3],
        goal_ee[4] - ee_base[4],
        goal_ee[5] - ee_base[5],
    )
    pos_norm = math.sqrt(err_p[0] ** 2 + err_p[1] ** 2 + err_p[2] ** 2)
    _, _, _, ang = axis_angle_from_small_rot(*err_r)
    in_deadzone = pos_norm < DEADZONE_POS and ang < DEADZONE_ANG

    if in_deadzone:
        twist = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    else:
        raw = (
            KP_LIN * err_p[0],
            KP_LIN * err_p[1],
            KP_LIN * err_p[2],
            KP_ANG * err_r[0],
            KP_ANG * err_r[1],
            KP_ANG * err_r[2],
        )
        twist = (
            clamp(raw[0], -V_MAX, V_MAX),
            clamp(raw[1], -V_MAX, V_MAX),
            clamp(raw[2], -V_MAX, V_MAX),
            clamp(raw[3], -W_MAX, W_MAX),
            clamp(raw[4], -W_MAX, W_MAX),
            clamp(raw[5], -W_MAX, W_MAX),
        )

    print(
        f"seed={SEED} eye_in_hand cam_in_ee={CAM_IN_EE} "
        f"kp_lin={KP_LIN:.2f} kp_ang={KP_ANG:.2f} "
        f"deadzone_pos={DEADZONE_POS:.3f} deadzone_ang={DEADZONE_ANG:.3f} "
        f"v_max={V_MAX:.2f} w_max={W_MAX:.2f}"
    )
    print(
        f"tag_cam=({tag_cam[0]:.4f},{tag_cam[1]:.4f},{tag_cam[2]:.4f},"
        f"{tag_cam[3]:.4f},{tag_cam[4]:.4f},{tag_cam[5]:.4f})"
    )
    print(
        f"ee_base=({ee_base[0]:.4f},{ee_base[1]:.4f},{ee_base[2]:.4f},"
        f"{ee_base[3]:.4f},{ee_base[4]:.4f},{ee_base[5]:.4f})"
    )
    print(
        f"err_pos=({err_p[0]:.4f},{err_p[1]:.4f},{err_p[2]:.4f}) "
        f"|e_p|={pos_norm:.4f} |e_r|={ang:.4f} in_deadzone={in_deadzone}"
    )
    print(
        f"{'vx':>8} {'vy':>8} {'vz':>8} {'wx':>8} {'wy':>8} {'wz':>8}"
    )
    print(
        f"{twist[0]:8.4f} {twist[1]:8.4f} {twist[2]:8.4f} "
        f"{twist[3]:8.4f} {twist[4]:8.4f} {twist[5]:8.4f}"
    )
    limited = any(
        abs(t) >= V_MAX - 1e-9 if i < 3 else abs(t) >= W_MAX - 1e-9
        for i, t in enumerate(twist)
    )
    print(
        f"ok: twist_limited={limited} in_deadzone={in_deadzone} "
        f"(Servo singularity/collision still Servo's job)"
    )


if __name__ == "__main__":
    main()
