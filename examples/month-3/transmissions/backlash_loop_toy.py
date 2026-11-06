#!/usr/bin/env python3
"""Two output-referred inertias, elastic backlash, load Coulomb/stiction, PID.
ALL angles rad, torques N*m, inertias kg*m^2. Ideal encoders (noise=0), same
initial state and reference per arm. Load encoder adds information, NOT an
information-equal algorithm contest. D uses motor velocity in every arm.
Gear torque = KG * sign(qm-ql) * max(abs(qm-ql)-b/2,0).
Jm*am=u-tau-DM*vm; Jl*al=tau-DL*vl-friction. At rest static friction holds
up to FS; sliding Coulomb magnitude FC<FS; velocity crossing zero can re-stick.
P/I see error deadband only in deadband arm; D remains unmodified. In the band
I leaks at 2/s, explicitly preventing stored I from continuing to push (Wescott
Sec.3.2 caveat). Integrator clamps +/-0.2 rad*s; torque saturates +/-2 N*m.
A hunting/limit-cycle CANDIDATE means tail load p-p>.005 rad, >=3 direction
reversals, and p-p>.002 in BOTH halves of the last40s. Finite simulation is not
a proof of an attracting periodic orbit. Selected no-friction/no-I controls do
not hunt; friction+integral can, not every backlash PID inevitably does.
Real reducer/torque sensors 本页未运行; no FOC/Z-homing/AGMA claims.
"""
import math

DT, SECONDS = .002, 120.
B, KG = .04, 30.
JM, JL, DM, DL = .01, .03, .5, .2
FS, FC = .4, .02  # deliberately strong stiction drop, synthetic, not typical spec
KP, KI, KD = 8., 3., 1.


def reference(t):
    return .12 if t < 30 else -.08 if t < 60 else .06


def simulate(sensor="motor", b_hat=None, friction=True, integral=True, dt=DT):
    qm = ql = vm = vl = accum = 0.
    history = []
    for n in range(round(SECONDS / dt)):
        t = n * dt
        r = reference(t)
        error = r - (ql if sensor == "load" else qm)
        half_band = 0. if b_hat is None else b_hat / 2
        pi_error = math.copysign(max(abs(error)-half_band, 0.), error)
        if b_hat is not None and abs(error) <= half_band:
            accum *= max(0., 1 - 2*dt)
        else:
            accum = max(-.2, min(.2, accum + pi_error*dt))
        u = max(-2., min(2., KP*pi_error + (KI*accum if integral else 0.) - KD*vm))
        gap = qm-ql
        tau = KG * math.copysign(max(abs(gap)-B/2, 0.), gap)
        force = tau-DL*vl
        fs, fc = (FS, FC) if friction else (0., 0.)
        if abs(vl) < 1e-6 and abs(force) <= fs:
            vl = 0.
        else:
            prev = vl
            sign = math.copysign(1., vl if abs(vl) > 1e-6 else force)
            vl += (force - fc*sign) / JL * dt
            if prev*vl < 0 and abs(force) <= fs:
                vl = 0.
        vm += (u-tau-DM*vm)/JM*dt
        qm += vm*dt
        ql += vl*dt
        history.append((t, r-qm, r-ql, vl))
    tail = [h for h in history if h[0] >= SECONDS-40]
    errors = [h[2] for h in tail]
    pp = lambda xs: max(xs)-min(xs)
    signs = [1 if h[3] > 1e-5 else -1 for h in tail if abs(h[3]) > 1e-5]
    reversals = sum(a != b for a, b in zip(signs, signs[1:]))
    half = len(errors)//2
    hunting = pp(errors) > .005 and reversals >= 3 and min(pp(errors[:half]), pp(errors[half:])) > .002
    # Remain within +/-0.01 rad for the rest of final step; report not_settled.
    bad = [h[0] for h in history if h[0] >= 60 and abs(h[2]) > .01]
    settle = "not_settled" if bad and bad[-1] >= SECONDS-dt*1.1 else f"{max(bad, default=60.)+dt-60:.3f}"
    return (math.sqrt(sum(h[2]**2 for h in history)/len(history)),
            math.sqrt(sum(h[1]**2 for h in tail)/len(tail)),
            min(errors), max(errors), pp(errors), reversals, hunting, settle)


def main():
    print(f"b={B} rad KG={KG} N*m/rad FS={FS} FC={FC} N*m; dt={DT} s; ideal encoder noise=0")
    print("shared reference 0.12/-0.08/0.06 rad at 0/30/60s; P/I deadband only; D motor velocity unchanged; in-band I leak=2/s")
    print("arm load_RMSE_rad tail_motor_RMSE_rad tail_load_error_min max pp reversals hunting_candidate settle_s")
    results = {}
    for name, kwargs in (("motor_PID", {}), ("load_PID_extra_sensor", {"sensor": "load"}),
                         ("deadband_b_correct", {"b_hat": B}),
                         ("deadband_b_too_small", {"b_hat": .004}),
                         ("deadband_b_too_large", {"b_hat": .12}),
                         ("load_no_friction", {"sensor": "load", "friction": False}),
                         ("load_no_integral", {"sensor": "load", "integral": False})):
        result = simulate(**kwargs)
        results[name] = result
        rmse, motor, low, high, pp, rev, hunt, settle = result
        print(f"{name} {rmse:.6f} {motor:.6f} {low:.6f} {high:.6f} {pp:.6f} {rev} {int(hunt)} {settle}")
    assert results["load_PID_extra_sensor"][6]
    assert not results["load_no_friction"][6] and not results["load_no_integral"][6]
    # Refine timestep: do not mistake Euler timestep chatter for hunting.
    assert simulate("load", dt=DT/2)[6]
    allowance = B/2+B/2+FS/KG
    print(f"correct deadband conditional static load-error allowance=+/-{allowance:.6f} rad (bhat/2+b/2+FS/KG)")
    print("measured tail error band above is NOT a zero-error guarantee; wrong b hides precision or leaves unmodelled play")
    print("load encoder has more information; no universal winner; finite-window candidate, not periodic-orbit proof; hardware 本页未运行")


if __name__ == "__main__":
    main()
