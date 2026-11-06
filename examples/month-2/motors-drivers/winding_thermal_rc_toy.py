#!/usr/bin/env python3
"""Synthetic winding thermal RC, NOT harness I2R (11.1) or driver-package thetaJA.
R(T)=R20*(1+0.00393*(T-20)); alpha20 is referenced to 20 degC.
At fixed I, I2R(T) is positive feedback. Steady deltaT=P*Rtheta;
short t<<tau gives deltaT approximately P*t/Ctheta.
All arms share the demanded current profile, plant and integration grid.
Ignore/monitor deliver the same current; derate intentionally changes delivered current.
The plant still heats when its controller ignores heating. Ideal winding temperature
is available to monitor/derate (not inferred from a measured case temperature).
Lesson-defined Rtheta/Ctheta/limits, NOT insulation-class certification. Stdlib only.
"""
from math import expm1, sqrt

AMBIENT = 25.0
R20 = 1.0                 # ohm at 20 degC, synthetic reference resistance
ALPHA20 = 0.00393          # 1/K referenced to 20 degC, not 25 degC
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


def resistance(temp):
    """I2R(T) positive feedback: at fixed I, hotter copper dissipates more."""
    return R20 * (1 + ALPHA20 * (temp - 20.0))


def advance(temp, current, dt):
    copper = current * current * resistance(temp)
    cooling = (temp - AMBIENT) / RTH
    return temp + (copper - cooling) * dt / CTH, copper * dt, cooling * dt


def constant_current_exact(current, seconds):
    """From ambient Ta, constant I: Ctheta*dT/dt =
    I**2*R20*(1+alpha20*(T-20)) - (T-Ta)/Rtheta.
    R(Ta)=R20*(1+alpha20*(Ta-20)); deltaT=T-Ta.
    Below I**2*alpha20*R20 < 1/Rtheta, the stable steady rise is
    deltaT_ss=I**2*R(Ta)*Rtheta/(1-I**2*alpha20*R20*Rtheta).
    At/above the threshold there is no finite physical steady state reached
    by heating from Ta with R(Ta)>0: linear growth at equality, exponential above.
    A formal negative-rise root above threshold has negative R, not a valid
    winding equilibrium. Constant I / linear R(T) only, not a motor rating.
    """
    p0 = current * current * resistance(AMBIENT)
    b = current * current * R20 * ALPHA20 - 1 / RTH
    return AMBIENT + (p0 * seconds / CTH if abs(b) < 1e-12 else p0 / b * expm1(b * seconds / CTH))


def constant_power_rise(power, seconds):
    """Steady deltaT=P*RTH; for t<<tau, deltaT approximately P*t/CTH."""
    return -power * RTH * expm1(-seconds / (RTH * CTH))


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
    print(f"R20_ohm={R20:.3f} alpha20_per_K={ALPHA20:.5f} R_at_25C_ohm={resistance(25):.5f}; I2R(T) positive feedback")
    print(f"I_crit_A={1 / sqrt(ALPHA20 * R20 * RTH):.6f} (synthetic constant-current threshold; not a rating)")
    print(f"constant_P=10W steady_delta_K={10 * RTH:.3f} short_0.1s_exact_K={constant_power_rise(10, .1):.6f} short_approx_K={10 * .1 / CTH:.6f}")
    print(f"shared request samples={len(requests)} dt_s={DT:.2f} duration_s={DURATION:.0f} tau0_s={RTH * CTH:.0f}")
    print("arm physical_peak_C final_C copper_J trips derated_samples above_trip_s estimator")
    for arm in ARMS:
        r = run(arm, requests)
        estimator = "none" if arm == "ignore" else "ideal_winding_T"
        print(f"{arm} {r['peak']:.3f} {r['final']:.3f} {r['copper_j']:.3f} {r['trips']} {r['derate_samples']} {r['above_trip_s']:.1f} {estimator}")
    print("trips count thermal cutoff entries; monitor observes but never intervenes")
    print("Synthetic only; real winding measurement / motor hardware: 本页未运行")


if __name__ == "__main__":
    main()
