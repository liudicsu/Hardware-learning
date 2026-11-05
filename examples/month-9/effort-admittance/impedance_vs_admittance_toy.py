#!/usr/bin/env python3
"""Effort-out impedance vs motion-out admittance on one mechanical plant.
Same mass/damper/spring/wall, disturbance schedule and measurement noise.
Admittance output goes through an explicitly modelled motion-tracking servo;
impedance requires an effort-capable actuator. Not a safety ranking.
Synthetic N only: no STS3215 Present Load conversion, no F/T hardware.
"""
import math
import random

SEED = 37
DT, STEPS = 0.001, 6000
M, B, K = 1.0, 4.0, 20.0
WALL, K_WALL = 0.04, 1800.0
EFFORT_LIMIT = 20.0
RELEASE = 2.5


def clamp(x, limit):
    return max(-limit, min(limit, x))


def simulate(mode, noise):
    x = v = y = vy = 0.0
    peak = penetration = 0.0
    last_unsettled = RELEASE
    for k, (nx, nv, nf) in enumerate(noise):
        t = k * DT
        ref = 0.065 if 0.5 <= t < RELEASE else 0.0
        disturbance = 2.0 if 1.2 <= t < 1.4 else 0.0
        wall_force = -K_WALL * max(0.0, x - WALL)
        xm, vm = x + nx, v + nv
        measured_external = wall_force + disturbance + nf
        if mode == "impedance":
            # Effort command from motion error, not a position interface.
            effort_command = 120.0 * (ref - xm) - 16.0 * vm
        else:
            # Virtual mass/damper/spring offset driven by measured external force.
            ay = (measured_external - 25.0 * vy - 100.0 * y) / 1.5
            vy += ay * DT
            y += vy * DT
            motion_command = ref + y
            # Separate inner motion servo converts motion command into effort.
            effort_command = 300.0 * (motion_command - xm) + 30.0 * (vy - vm)
        u = clamp(effort_command, EFFORT_LIMIT)  # same actuator effort limit
        # Common physical plant; semi-implicit Euler, not ideal motion tracking.
        a = (u + disturbance + wall_force - B * v - K * x) / M
        v += a * DT
        x += v * DT
        pen = max(0.0, x - WALL)
        peak = max(peak, K_WALL * pen)
        penetration = max(penetration, pen)
        if t >= RELEASE and (abs(x) > 0.001 or abs(v) > 0.005):
            last_unsettled = t + DT
    settled = abs(x) <= 0.001 and abs(v) <= 0.005
    return peak, penetration, last_unsettled - RELEASE if settled else None


def main():
    rng = random.Random(SEED)
    noise = [(rng.gauss(0, 0.0001), rng.gauss(0, 0.0005), rng.gauss(0, 0.02))
             for _ in range(STEPS)]
    print(f"seed={SEED} dt_s={DT} plant_mass_kg={M} shared_noise=True")
    print("mode peak_contact_N max_penetration_m settling_after_release_s")
    for mode in ("impedance", "admittance"):
        force, pen, settling = simulate(mode, noise)
        assert math.isfinite(force) and pen >= 0
        settling_text = f"{settling:.3f}" if settling is not None else "not_settled"
        print(f"{mode} {force:.6f} {pen:.6f} {settling_text}")
    print("impedance_output=effort admittance_output=motion safety_ranking=none")


if __name__ == "__main__":
    main()
