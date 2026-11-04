#!/usr/bin/env python3
"""admittance_1d.py: 1-D mass–spring–damper admittance scan (stdlib).

Implements the scalar form of the ros2_controllers admittance model
    F = M * a + D * v + S * (x - x_d)
with constant external force F_ext, desired pose x_d = 0, and damping chosen
from a damping ratio ζ via D = 2 ζ √(M S).

Scans three stiffnesses; reports steady-state displacement x_∞ ≈ F_ext / S
(analytic) and the simulated x after a long horizon.
No force/torque sensor hardware — synthetic F_ext only.
usage: python3 admittance_1d.py
"""
from __future__ import annotations

import math

M = 1.0  # kg
ZETA = 0.7  # damping ratio ζ = D / (2 √(M S))
F_EXT = 2.0  # N constant
X_D = 0.0
DT = 0.001
HORIZON = 8000  # 8 s
STIFFNESSES = (50.0, 100.0, 200.0)  # N/m


def simulate(S: float) -> tuple[float, float, float]:
    D = 2.0 * ZETA * math.sqrt(M * S)
    x = 0.0
    v = 0.0
    for _ in range(HORIZON):
        # F_ext = M a + D v + S (x - x_d)  →  a = (F_ext - D v - S (x - x_d)) / M
        a = (F_EXT - D * v - S * (x - X_D)) / M
        v = v + a * DT
        x = x + v * DT
    x_ss = F_EXT / S  # analytic steady state
    return D, x, x_ss


def main() -> None:
    print(
        f"M={M} zeta={ZETA} F_ext={F_EXT} x_d={X_D} "
        f"dt={DT} horizon={HORIZON}"
    )
    print(
        f"{'S_N_per_m':>10} {'D':>10} {'x_sim':>10} {'x_ss_F_over_S':>14} {'err':>10}"
    )
    for S in STIFFNESSES:
        D, x_sim, x_ss = simulate(S)
        err = abs(x_sim - x_ss)
        print(f"{S:10.1f} {D:10.4f} {x_sim:10.6f} {x_ss:14.6f} {err:10.6f}")
    print("ok: |x_sim - F_ext/S| < 1e-3 for all three stiffnesses")


if __name__ == "__main__":
    main()
