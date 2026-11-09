#!/usr/bin/env python3
"""Synthetic magnetometer hard/soft-iron calibration toy. Stdlib only.

Shared true field magnitude and shared yaw rotation path for every arm.
Measurement model (VectorNav-style): m_tilde = S_soft @ R(yaw) @ B_true + b_hard + noise.
Arms differ only in post-processing of the SAME samples:
  A_raw          heading from uncorrected XY
  B_hard_only    subtract estimated hard-iron bias (sample mean)
  C_hard_soft    bias subtract + diagonal soft-iron scale (axis std → unit circle)

Metrics: heading absolute error (deg) and residual radius RMS after mapping to
a unit circle. ≥5 noise seeds. Not an AHRS certification. Mag hardware: 本页未运行.
"""
from __future__ import annotations

import math
import random

B_TRUE = (1.0, 0.0)  # horizontal field in body-fixed world frame, synthetic units
# Permanent hard-iron bias (sphere/circle centre shift)
B_HARD = (0.35, -0.22)
# Soft-iron stretch (diagonal ellipsoid → circle stretch); off-diagonals omitted for clarity
S_SOFT = (1.35, 0.72)  # sx, sy
N_YAWS = 72  # 5° steps, full rotation
NOISE_SIGMA = 0.03
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_raw", "B_hard_only", "C_hard_soft")


def wrap180(deg: float) -> float:
    while deg > 180.0:
        deg -= 360.0
    while deg <= -180.0:
        deg += 360.0
    return deg


def heading_deg(mx: float, my: float) -> float:
    return math.degrees(math.atan2(my, mx))


def true_path() -> list[tuple[float, float, float]]:
    """Return list of (yaw_deg, mx_world_rot, my_world_rot) without distortion."""
    rows = []
    for i in range(N_YAWS):
        yaw = 360.0 * i / N_YAWS
        c = math.cos(math.radians(yaw))
        s = math.sin(math.radians(yaw))
        # rotate true field into sensor frame as yaw changes (2D)
        mx = c * B_TRUE[0] + s * B_TRUE[1]
        my = -s * B_TRUE[0] + c * B_TRUE[1]
        rows.append((yaw, mx, my))
    return rows


def measure(path, seed: int) -> list[tuple[float, float, float]]:
    rng = random.Random(20_000 + seed)
    out = []
    sx, sy = S_SOFT
    bx, by = B_HARD
    for yaw, mx, my in path:
        # soft stretch then hard bias + noise (VectorNav: m_c = S(m - b) form inverted)
        tx = sx * mx + bx + rng.gauss(0.0, NOISE_SIGMA)
        ty = sy * my + by + rng.gauss(0.0, NOISE_SIGMA)
        out.append((yaw, tx, ty))
    return out


def calibrate_bias(samples):
    mx = sum(p[1] for p in samples) / len(samples)
    my = sum(p[2] for p in samples) / len(samples)
    return mx, my


def calibrate_soft(samples, bias):
    """Diagonal soft scale: map demeaned axes to equal RMS (unit-ish circle)."""
    bx, by = bias
    xs = [p[1] - bx for p in samples]
    ys = [p[2] - by for p in samples]
    rx = math.sqrt(sum(v * v for v in xs) / len(xs)) or 1.0
    ry = math.sqrt(sum(v * v for v in ys) / len(ys)) or 1.0
    # target radius = geometric mean
    target = math.sqrt(rx * ry)
    return target / rx, target / ry


def evaluate(samples, arm: str) -> tuple[float, float, float, float]:
    """Return mean |heading err|, sd, residual radius RMS, residual radius sd."""
    bias = calibrate_bias(samples)
    soft = calibrate_soft(samples, bias)
    errs = []
    radii = []
    for yaw, mx, my in samples:
        if arm == "A_raw":
            cx, cy = mx, my
        elif arm == "B_hard_only":
            cx, cy = mx - bias[0], my - bias[1]
        else:
            cx = soft[0] * (mx - bias[0])
            cy = soft[1] * (my - bias[1])
        est = heading_deg(cx, cy)
        # true heading of horizontal field in sensor frame equals yaw for B_TRUE=(1,0)
        # with our rotation convention: atan2(my,mx) of undistorted = -yaw
        true_h = heading_deg(
            math.cos(math.radians(yaw)) * B_TRUE[0] + math.sin(math.radians(yaw)) * B_TRUE[1],
            -math.sin(math.radians(yaw)) * B_TRUE[0] + math.cos(math.radians(yaw)) * B_TRUE[1],
        )
        errs.append(abs(wrap180(est - true_h)))
        radii.append(math.hypot(cx, cy))
    mu_e = sum(errs) / len(errs)
    # radius residual vs mean radius
    mu_r = sum(radii) / len(radii)
    resid = [abs(r - mu_r) for r in radii]
    rms = math.sqrt(sum(r * r for r in resid) / len(resid))
    sd_e = math.sqrt(sum((e - mu_e) ** 2 for e in errs) / (len(errs) - 1))
    mu_abs = sum(resid) / len(resid)
    sd_r = math.sqrt(sum((r - mu_abs) ** 2 for r in resid) / (len(resid) - 1))
    return mu_e, sd_e, rms, sd_r


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    path = true_path()
    print(
        "Synthetic mag hard/soft-iron toy; shared field/path; not an AHRS certification"
    )
    print(
        f"B_true={B_TRUE} b_hard={B_HARD} S_diag={S_SOFT} "
        f"N_yaws={N_YAWS} noise_sigma={NOISE_SIGMA} seeds={len(SEEDS)}"
    )
    print(
        "model: m_tilde = S_soft * R(yaw)*B_true + b_hard + noise "
        "(VectorNav hard=centre shift, soft=ellipse stretch)"
    )
    print(
        "arm mean_abs_heading_err_deg heading_err_sd_deg "
        "radius_resid_rms radius_resid_sd (mean+-sd over seeds)"
    )
    for arm in ARMS:
        cols_acc = [[] for _ in range(4)]
        for seed in SEEDS:
            samples = measure(path, seed)
            vals = evaluate(samples, arm)
            for i, v in enumerate(vals):
                cols_acc[i].append(v)
        print(
            f"{arm} "
            + " ".join(f"{mean_sd(c)[0]:.4f}+-{mean_sd(c)[1]:.4f}" for c in cols_acc)
        )
    print(
        "No winner declared beyond the defined metric: hard-only recenters; "
        "hard+soft also un-stretches; raw keeps both errors"
    )
    print("Mag turntable / real IMU: 本页未运行; VectorNav/Wikipedia definitions 以原文为准")


if __name__ == "__main__":
    main()
