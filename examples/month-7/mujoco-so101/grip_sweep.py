#!/usr/bin/env python3
"""grip_sweep.py: 3x3 sweep of MuJoCo timestep x solref timeconst on a soft-contact grip-and-lift.

A two-jaw slider gripper closes on a free cube (gravity off), then lifts with gravity on.
For each (timestep, solref timeconst) pair we report whether the cube was held and the
maximum contact penetration seen during the run. Fixed scene: grip_scene.xml next to this file.

Requires: mujoco (pip install mujoco; Menagerie models need >= 3.1.3). Standard library + mujoco.
usage: python3 grip_sweep.py
"""
from __future__ import annotations

import os
import sys

try:
    import mujoco
    import numpy as np
except ImportError as e:
    sys.stderr.write(
        "grip_sweep.py needs mujoco (and numpy). "
        "Install with: python3 -m pip install mujoco\n"
        f"Import error: {e}\n"
    )
    sys.exit(1)

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.join(HERE, "grip_scene.xml")

# Locked so expected/ stays stable. Soft + large dt → slip; stiff → hold. Penetration grows with timeconst.
TIMESTEPS = (0.002, 0.005, 0.010)
TIMECONSTS = (0.004, 0.020, 0.080)  # solref[0]; dampratio fixed at 1.0
CLOSE = 0.0245
FRICTION = 1.2
CUBE_MASS = 0.15
HOLD_Z = 0.08
LIFT_CTRL = 0.10


def run(timestep: float, timeconst: float) -> tuple[float, float, bool]:
    m = mujoco.MjModel.from_xml_path(SCENE)
    m.opt.timestep = timestep
    m.opt.impratio = 10.0
    m.opt.cone = 1  # elliptic
    for bi in range(m.nbody):
        name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, bi) or ""
        if name == "cube":
            m.body_mass[bi] = CUBE_MASS
            m.body_inertia[bi] = np.array([CUBE_MASS * 8e-5] * 3)
    for gi in range(m.ngeom):
        name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, gi) or ""
        if name in ("left_g", "right_g", "cube_geom"):
            m.geom_solref[gi] = (timeconst, 1.0)
            m.geom_friction[gi] = [FRICTION, 0.005, 0.0001]
    d = mujoco.MjData(m)

    # Close without gravity so the cube stays between the jaws.
    m.opt.gravity[:] = (0.0, 0.0, 0.0)
    d.ctrl[:] = (0.0, CLOSE, -CLOSE)
    for _ in range(max(1, int(0.8 / timestep))):
        mujoco.mj_step(m, d)
    max_pen = 0.0
    for i in range(d.ncon):
        if d.contact[i].dist < 0:
            max_pen = max(max_pen, -d.contact[i].dist)

    # Gravity on, lift the palm.
    m.opt.gravity[:] = (0.0, 0.0, -9.81)
    d.ctrl[:] = (LIFT_CTRL, CLOSE, -CLOSE)
    for _ in range(max(1, int(1.5 / timestep))):
        mujoco.mj_step(m, d)
        for i in range(d.ncon):
            if d.contact[i].dist < 0:
                max_pen = max(max_pen, -d.contact[i].dist)

    cube_z = float(d.qpos[5])  # freejoint xyz after lift/left/right
    held = cube_z > HOLD_Z
    return cube_z, max_pen, held


def main() -> None:
    print(f"scene={os.path.basename(SCENE)}")
    print(f"friction={FRICTION}  cube_mass={CUBE_MASS} kg  close={CLOSE} m")
    print("dt_s   timeconst  cube_z_m  pen_mm  result")
    holds = 0
    for dt in TIMESTEPS:
        for tc in TIMECONSTS:
            z, pen, held = run(dt, tc)
            holds += int(held)
            print(
                f"{dt:5.3f}  {tc:8.3f}  {z:8.4f}  {pen * 1e3:6.2f}  "
                f"{'HOLD' if held else 'SLIP'}"
            )
    print(f"held {holds}/9  (soft + large dt slips; penetration grows with timeconst)")


if __name__ == "__main__":
    main()
