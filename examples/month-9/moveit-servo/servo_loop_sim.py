#!/usr/bin/env python3
"""servo_loop_sim.py: scale Cartesian speed near singularity (stdlib).

Discrete-time toy of a MoveIt Servo-style loop: each control cycle consumes a
Cartesian twist. When the planar 2-link Jacobian condition number κ exceeds
KAPPA_THRESH, scale the twist so the end-effector speed norm drops
(unscaled vs scaled table).

Pinned constants keep expected/ stable. No ROS / MoveIt runtime.
usage: python3 servo_loop_sim.py
"""
from __future__ import annotations

import math

L1 = 0.30  # m
L2 = 0.25  # m
THETA1 = 0.40  # rad, fixed
# Sweep θ2 from a comfortable bend toward a stretch singularity (θ2 → 0).
THETA2_START = 1.20
THETA2_END = 0.05
N_STEPS = 8
V_CMD = (0.10, 0.00)  # m/s desired Cartesian twist (vx, vy)
KAPPA_THRESH = 12.0  # condition-number threshold → start scaling
EPS = 1e-12


def jacobian(theta1: float, theta2: float) -> list[list[float]]:
    """2×2 planar RR geometric Jacobian mapping dq → [vx, vy]."""
    s1 = math.sin(theta1)
    c1 = math.cos(theta1)
    s12 = math.sin(theta1 + theta2)
    c12 = math.cos(theta1 + theta2)
    return [
        [-L1 * s1 - L2 * s12, -L2 * s12],
        [L1 * c1 + L2 * c12, L2 * c12],
    ]


def condition_number(J: list[list[float]]) -> float:
    """κ = σ_max / σ_min via eigenvalues of JᵀJ (2×2)."""
    a, b = J[0][0], J[0][1]
    c, d = J[1][0], J[1][1]
    g00 = a * a + c * c
    g01 = a * b + c * d
    g11 = b * b + d * d
    tr = g00 + g11
    det = g00 * g11 - g01 * g01
    disc = max(0.0, tr * tr - 4.0 * det)
    root = math.sqrt(disc)
    lam1 = 0.5 * (tr + root)
    lam2 = 0.5 * (tr - root)
    sig1 = math.sqrt(max(lam1, 0.0))
    sig2 = math.sqrt(max(lam2, 0.0))
    sig_max = max(sig1, sig2)
    sig_min = min(sig1, sig2)
    if sig_min < EPS:
        return float("inf")
    return sig_max / sig_min


def speed_norm(vx: float, vy: float) -> float:
    return math.hypot(vx, vy)


def main() -> None:
    vx0, vy0 = V_CMD
    v_des = speed_norm(vx0, vy0)
    print(
        f"L1={L1:.2f} L2={L2:.2f} theta1={THETA1:.2f} "
        f"theta2=[{THETA2_START:.2f}..{THETA2_END:.2f}] steps={N_STEPS} "
        f"v_cmd=({vx0:.2f},{vy0:.2f}) kappa_thresh={KAPPA_THRESH:.1f}"
    )
    print(
        f"{'step':>4} {'theta2':>8} {'kappa':>10} "
        f"{'v_unscaled':>12} {'scale':>8} {'v_scaled':>10}"
    )
    scaled_rows = 0
    for i in range(N_STEPS):
        t = i / (N_STEPS - 1)
        theta2 = THETA2_START + t * (THETA2_END - THETA2_START)
        kappa = condition_number(jacobian(THETA1, theta2))
        if kappa == float("inf"):
            scale = 0.0
            kappa_s = f"{'inf':>10}"
        elif kappa > KAPPA_THRESH:
            scale = KAPPA_THRESH / kappa
            kappa_s = f"{kappa:10.4f}"
        else:
            scale = 1.0
            kappa_s = f"{kappa:10.4f}"
        if scale < 0.0:
            scale = 0.0
        if scale > 1.0:
            scale = 1.0
        v_un = v_des
        v_sc = v_des * scale
        if scale < 1.0:
            scaled_rows += 1
        print(
            f"{i:4d} {theta2:8.4f} {kappa_s} "
            f"{v_un:12.4f} {scale:8.4f} {v_sc:10.4f}"
        )
    print(
        f"ok: scaled_rows={scaled_rows} "
        f"(near singularity v_scaled < v_unscaled)"
    )


if __name__ == "__main__":
    main()
