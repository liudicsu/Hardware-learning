#!/usr/bin/env python3
"""Synthetic winding thermal RC, NOT harness I2R (11.1) or driver-package thetaJA.
All arms share the demanded current profile, plant and integration grid.
Ignore/monitor deliver the same current; derate intentionally changes delivered current.
The plant still heats when its controller ignores heating. Ideal winding temperature
is available to monitor/derate (not inferred from a measured case temperature).
Lesson-defined Rtheta/Ctheta/limits, NOT insulation-class certification. Stdlib only.
"""
from math import expm1

AMBIENT = 25.0
R25 = 1.0                 # ohm, synthetic winding resistance at ambient
ALPHA = 0.00393            # 1/K, illustrative linear copper tempco
RTH = 4.0                 # K/W, lesson-defined winding-to-ambient path
CTH = 12.0                # J/K, lesson-defined winding heat capacity
DT = 0.1                  # s; tau = RTH * CTH = 48 s
DURATION = 480.0
DERATE_C = 50.0
TRIP_C = 70.0
RESET_C = 45.0
DERATED_A = 3.5
ARMS = ("ignore", "monitor_rc", "derate_trip")


def current_profile(dt=DT):
    """One shared request: free run, intermittent stalls, prolonged stalls, cool."""
    result = []
    for k in range(round(DURATION / dt)):
        t = k * dt
        stall = (30 <= t < 150 and (t - 30) % 10 < 4) or 150 <= t < 240 or 360 <= t < 420
        result.append(5.0 if stall else 1.0)
    return tuple(result)


def advance(temp, current, dt):
    copper = current * current * R25 * (1 + ALPHA * (temp - AMBIENT))
    cooling = (temp - AMBIENT) / RTH
    return temp + (copper - cooling) * dt / CTH, copper * dt, cooling * dt


def constant_current_exact(current, seconds):
    """Independent closed-form check of the linear-in-temperature ODE."""
    p0 = current * current * R25
    b = p0 * ALPHA - 1 / RTH
    return AMBIENT + (p0 * seconds / CTH if abs(b) < 1e-12 else p0 / b * expm1(b * seconds / CTH))


def run(arm, requests, dt=DT):
    if arm not in ARMS:
        raise ValueError("unknown arm")
    temp = peak = AMBIENT
    copper_j = cooling_j = above_trip_s = 0.0
    trips = derate_samples = 0
    cooling_off = False
    for requested in requests:
        current = requested
        if arm == "derate_trip":
            if cooling_off and temp <= RESET_C:
                cooling_off = False
            if not cooling_off and temp >= TRIP_C:
                cooling_off = True
                trips += 1
            if cooling_off:
                current = 0.0
            elif temp > DERATE_C:
                current = min(current, DERATED_A)
                derate_samples += int(current < requested)
        above_trip_s += dt * (temp >= TRIP_C)
        temp, heat, rejected = advance(temp, current, dt)
        copper_j += heat
        cooling_j += rejected
        peak = max(peak, temp)
    return dict(peak=peak, final=temp, copper_j=copper_j, cooling_j=cooling_j,
                trips=trips, derate_samples=derate_samples, above_trip_s=above_trip_s)


def main():
    requests = current_profile()
    print("Synthetic winding RC; ideal winding T; no insulation/driver-package rating")
    print(f"shared request samples={len(requests)} dt_s={DT:.2f} duration_s={DURATION:.0f} tau_s={RTH * CTH:.0f}")
    print("arm physical_peak_C final_C copper_J trips derated_samples above_trip_s estimator")
    for arm in ARMS:
        r = run(arm, requests)
        estimator = "none" if arm == "ignore" else "ideal_winding_T"
        print(f"{arm} {r['peak']:.3f} {r['final']:.3f} {r['copper_j']:.3f} {r['trips']} {r['derate_samples']} {r['above_trip_s']:.1f} {estimator}")
    print("trips count thermal cutoff entries; monitor warns but never intervenes")
    print("Synthetic only; real winding measurement / motor hardware: 本页未运行")


if __name__ == "__main__":
    main()
