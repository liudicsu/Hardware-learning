#!/usr/bin/env python3
"""load_contact_sim.py: position tracking vs load-threshold retreat (stdlib).

1-D joint tracks a ramp setpoint. An obstacle at x=OBSTACLE starts opposing
motion; Present Load is synthesised as a duty-cycle proxy in [0, 1000] (1000 =
100 % — Feetech STS3215 Present Load sense, NOT calibrated newtons).

Compares:
  position-only: keep tracking through the obstacle (high peak load, deep
                 penetration past the obstacle face)
  load-retreat:  if load >= LOAD_THRESH, step back and freeze the setpoint at
                 the pre-contact pose (lower peak load, less penetration)

Pinned constants keep expected/ stable. No real STS3215 bus.
usage: python3 load_contact_sim.py
"""
from __future__ import annotations

DT = 0.02  # 50 Hz
HORIZON = 200
X0 = 0.0
V_CMD = 0.25  # m/s commanded toward +x
OBSTACLE = 0.40  # m
K_CONTACT = 500.0  # N/m spring proxy once past obstacle (toy)
LOAD_SCALE = 4.0  # maps force proxy → Present Load units
LOAD_THRESH = 200  # retreat when load >= this (of 1000)
ALPHA = 0.85  # tracking blend toward x_des each tick
RETREAT_STEP = 0.02  # m


def load_from_x(x: float) -> float:
    """Unsigned Present Load proxy in [0, 1000]. Penetration → force → load %."""
    if x <= OBSTACLE:
        return 0.0
    force = K_CONTACT * (x - OBSTACLE)
    return min(1000.0, force * LOAD_SCALE)


def run(retreat: bool) -> tuple[float, float, float]:
    x = X0
    peak_load = 0.0
    max_pen = 0.0
    frozen_des = None  # set when load-retreat first trips
    for t in range(HORIZON):
        x_des_nominal = X0 + V_CMD * (t * DT)
        if retreat:
            if frozen_des is not None:
                x_des = frozen_des
            else:
                x_des = x_des_nominal
            if load_from_x(x) >= LOAD_THRESH:
                if frozen_des is None:
                    frozen_des = x - RETREAT_STEP  # freeze behind contact
                x = x - RETREAT_STEP
            else:
                x = x + ALPHA * (x_des - x)
        else:
            x = x + ALPHA * (x_des_nominal - x)
        if x > 1.0:
            x = 1.0
        if x < 0.0:
            x = 0.0
        load = load_from_x(x)
        peak_load = max(peak_load, load)
        max_pen = max(max_pen, max(0.0, x - OBSTACLE))
    return x, peak_load, max_pen


def main() -> None:
    x_pos, peak_pos, pen_pos = run(retreat=False)
    x_ret, peak_ret, pen_ret = run(retreat=True)
    print(
        f"dt={DT} horizon={HORIZON} obstacle={OBSTACLE} "
        f"load_thresh={LOAD_THRESH} load_fullscale=1000"
    )
    print(f"{'mode':<16} {'x_final':>10} {'peak_load':>10} {'max_pen_m':>10}")
    print(f"{'position_only':<16} {x_pos:10.4f} {peak_pos:10.1f} {pen_pos:10.4f}")
    print(f"{'load_retreat':<16} {x_ret:10.4f} {peak_ret:10.1f} {pen_ret:10.4f}")
    better = peak_ret < peak_pos and pen_ret < pen_pos
    print(
        f"ok: load_retreat peak_load < position_only "
        f"({peak_ret:.1f} < {peak_pos:.1f}) and max_pen "
        f"({pen_ret:.4f} < {pen_pos:.4f}) => {better}"
    )


if __name__ == "__main__":
    main()
