#!/usr/bin/env python3
"""Mask + depth → camera point → base frame grasp pose (stdlib).

Minimal perception-to-grasp pipe for lesson 7.6:
  1. Build a synthetic depth image and a binary mask (stand-in for SAM2 /
     open-vocab segmentation — those stay「本页未运行」, Apache-2.0 for SAM2).
  2. Back-project mask pixels with the pinhole model to a camera-frame centroid.
  3. Apply a known eye-in-hand cam2gripper and gripper2base to get a base-frame
     grasp point (top-down approach along -Z_base).
  4. Emit a grasp candidate: (xyz, approach, width_est).

Classical GraspNet 6-DoF representations are cited in the MDX; this toy only
needs a point + approach so CI stays free of torch / Open3D.
"""
from __future__ import annotations

import math

SEED_NOTE = "deterministic synthetic grid (no RNG)"
FX = FY = 320.0
CX, CY = 160.0, 120.0
WIDTH, HEIGHT = 320, 240
# cube sits at camera-frame centre-ish
CUBE_Z = 0.42  # metres
CUBE_U0, CUBE_V0 = 140, 100
CUBE_U1, CUBE_V1 = 180, 140


def mat_vec(R, t, p):
    return [
        R[0][0] * p[0] + R[0][1] * p[1] + R[0][2] * p[2] + t[0],
        R[1][0] * p[0] + R[1][1] * p[1] + R[1][2] * p[2] + t[1],
        R[2][0] * p[0] + R[2][1] * p[1] + R[2][2] * p[2] + t[2],
    ]


def make_synth():
    """Return depth (list of rows) and mask (0/1)."""
    depth = [[0.0] * WIDTH for _ in range(HEIGHT)]
    mask = [[0] * WIDTH for _ in range(HEIGHT)]
    for v in range(HEIGHT):
        for u in range(WIDTH):
            # background plane at 1.2 m
            depth[v][u] = 1.2
            if CUBE_U0 <= u < CUBE_U1 and CUBE_V0 <= v < CUBE_V1:
                depth[v][u] = CUBE_Z
                mask[v][u] = 1
    return depth, mask


def backproject_centroid(depth, mask):
    xs, ys, zs = [], [], []
    for v in range(HEIGHT):
        for u in range(WIDTH):
            if not mask[v][u]:
                continue
            z = depth[v][u]
            x = (u - CX) / FX * z
            y = (v - CY) / FY * z
            xs.append(x)
            ys.append(y)
            zs.append(z)
    n = len(xs)
    assert n > 0, "empty mask"
    return [sum(xs) / n, sum(ys) / n, sum(zs) / n], n


def estimate_width_m(depth, mask):
    """Axis-aligned mask width at the median depth → metres."""
    us = [u for v in range(HEIGHT) for u in range(WIDTH) if mask[v][u]]
    zs = [depth[v][u] for v in range(HEIGHT) for u in range(WIDTH) if mask[v][u]]
    zs_sorted = sorted(zs)
    z_med = zs_sorted[len(zs_sorted) // 2]
    u_span = max(us) - min(us) + 1
    return (u_span / FX) * z_med


def main() -> None:
    depth, mask = make_synth()
    p_cam, n_pix = backproject_centroid(depth, mask)
    width = estimate_width_m(depth, mask)

    # Fixed eye-in-hand extrinsics (as if from handeye_toy) + one gripper pose
    R_c2g = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    t_c2g = [0.02, -0.01, 0.05]
    R_g2b = [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]]  # cam looks along +X_base
    t_g2b = [0.25, 0.0, 0.20]

    p_grip = mat_vec(R_c2g, t_c2g, p_cam)
    p_base = mat_vec(R_g2b, t_g2b, p_grip)

    # top-down approach in base: -Z
    approach = [0.0, 0.0, -1.0]
    # grasp point slightly above centroid
    grasp = [p_base[0], p_base[1], p_base[2] + 0.02]

    print("grasp_from_mask — synth mask+depth → base grasp (%s)" % SEED_NOTE)
    print("intrinsics fx=fy=%.1f cx=%.1f cy=%.1f" % (FX, CX, CY))
    print("mask_pixels=%d  width_est_m=%.4f" % (n_pix, width))
    print("p_cam_m = [%.4f, %.4f, %.4f]" % tuple(p_cam))
    print("p_base_m = [%.4f, %.4f, %.4f]" % tuple(p_base))
    print("grasp_xyz = [%.4f, %.4f, %.4f]  approach=%s" % (grasp[0], grasp[1], grasp[2], approach))
    # expected geometry: cube centre in pixels → cam
    u_c = 0.5 * (CUBE_U0 + CUBE_U1 - 1)
    v_c = 0.5 * (CUBE_V0 + CUBE_V1 - 1)
    expect_x = (u_c - CX) / FX * CUBE_Z
    expect_y = (v_c - CY) / FY * CUBE_Z
    assert abs(p_cam[0] - expect_x) < 1e-6
    assert abs(p_cam[1] - expect_y) < 1e-6
    assert abs(p_cam[2] - CUBE_Z) < 1e-9
    assert width > 0.04
    print("ok: centroid back-projects; grasp candidate in base frame")


if __name__ == "__main__":
    main()
