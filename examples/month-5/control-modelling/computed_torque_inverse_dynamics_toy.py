#!/usr/bin/env python3
"""Computed torque (inverse dynamics in the loop) vs PD + gravity compensation on one shared 2R arm.

Synthetic, stdlib only.  Not this lesson's single-joint gravity feedforward (that is the g(q)
term alone, kept here as arm A); not discrete LQR / MPC, not the Smith predictor, not 2-DOF
setpoint weighting, not a humanoid whole-body controller.  Real arm or identification lab:
本页未运行.  Wikipedia "Inverse dynamics" statements (robot motor torques from a prescribed
motion and the inertial properties) are 以原文为准; the arm model and the control law below are
a textbook-style stand-in.

Plant: planar 2R arm moving in a vertical plane, point masses at the link ends (M1 at the elbow,
M2 + payload at the tip), link lengths L1, L2.  With c2 = cos q2, s2 = sin q2:
  M11 = (m1 + m2) L1^2 + m2 L2^2 + 2 m2 L1 L2 c2,  M12 = m2 L2^2 + m2 L1 L2 c2,  M22 = m2 L2^2
  C   = (-m2 L1 L2 s2 (2 q1' q2' + q2'^2),  m2 L1 L2 s2 q1'^2)
  g   = ((m1 + m2) G L1 cos q1 + m2 G L2 cos(q1 + q2),  m2 G L2 cos(q1 + q2))
  M q'' + C + g = tau - friction,  friction = FC tanh(q' / 0.02) per joint (in no arm's model).
Controllers (e = q_d - q measured, KP, KD per joint in 1/s^2 and 1/s):
  A_pdg     tau = D0 (KP e + KD e') + g_hat(q)          D0 = diag of M at the start pose,
                                                         correct payload (PD + gravity)
  B_ct      tau = M_hat(q) (q_d'' + KP e + KD e') + C_hat + g_hat   matched model (computed torque)
  C_ctwrong the same law with the payload left out of M_hat, C_hat, g_hat (wrong inertia)
Integration: semi-implicit Euler at step DT, the controller is evaluated every step.  Stable-step
criterion: with a matched model and no friction or noise, the error obeys e'' + KD e' + KP e = 0
integrated by this scheme, which is stable for DT < H_STAR = 2 (sqrt(1 + Z^2) - Z) / W with
W = sqrt(KP), Z = KD / (2 W).  Printed checks: matched arm from a 0.05 rad error at 0.98 x and
1.02 x H_STAR, and the whole table again at DT / 2.  A and C have nonlinear error dynamics; they
are covered by the half-step check only.
Measurement noise (q and q') is drawn per 1 ms sample and held, so DT / 2 sees the same noise.
Metrics per seed: rms tracking error (mrad, both joints), peak error (mrad), rms feedback torque
(N m, the part of tau that comes from e and e').
Common random numbers: per (regime, seed) the trajectory amplitude scale, both phases and the
noise sequence are drawn once and used by all three arms.
Regimes and expectations, written before the first run:
  fast_coupled       f 1.0 Hz, payload 0.5 kg   B consistent win over A on rms error
  slow_quasi_static  f 0.05 Hz, payload 0.5 kg  A and B near-tie (gravity dominates, both have it)
  payload_mismatch   f 0.25 Hz, payload 2.0 kg  C (computed torque, wrong inertia) loses to A
                                                 (PD + gravity with the right payload), consistent
  C loses to B in every regime.
The FC=0 sensitivity block and the centre-pose stiffness lines were added after
the first run; they are not pre-declared regimes.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
L1, L2 = 0.30, 0.25        # m
M1, M2 = 1.5, 1.0          # kg, point masses at elbow and tip (tip mass without payload)
G = 9.81
FC = 0.3                   # N m, Coulomb-like friction, unmodelled
KP, KD = 400.0, 40.0       # 1/s^2, 1/s
DT = 1e-3                  # s
SAMPLE = 1e-3              # s, noise sample period
SIG_Q, SIG_QD = 2e-4, 0.01  # rad, rad/s
Q0 = (0.3, 0.8)            # rad, centre pose
AMP = (0.8, 1.0)           # rad
NUM_ZERO = 1e-9
ARMS = ("A_pdg", "B_ct", "C_ctwrong")
# name: (f Hz, duration s, real payload kg, payload in C's model kg); written before the first run
REGIMES = {
    "fast_coupled": (1.0, 4.0, 0.5, 0.0),
    "slow_quasi_static": (0.05, 6.0, 0.5, 0.0),
    "payload_mismatch": (0.25, 6.0, 2.0, 0.0),
}
STREAM = {"fast_coupled": 0, "slow_quasi_static": 1, "payload_mismatch": 2}


def h_star(kp=KP, kd=KD):
    w = math.sqrt(kp)
    z = kd / (2.0 * w)
    return 2.0 * (math.sqrt(1.0 + z * z) - z) / w


def dyn(q, qd, payload):
    m2 = M2 + payload
    c2, s2 = math.cos(q[1]), math.sin(q[1])
    m11 = (M1 + m2) * L1 * L1 + m2 * L2 * L2 + 2.0 * m2 * L1 * L2 * c2
    m12 = m2 * L2 * L2 + m2 * L1 * L2 * c2
    m22 = m2 * L2 * L2
    h = m2 * L1 * L2 * s2
    cv = (-h * (2.0 * qd[0] * qd[1] + qd[1] * qd[1]), h * qd[0] * qd[0])
    c12 = math.cos(q[0] + q[1])
    gv = ((M1 + m2) * G * L1 * math.cos(q[0]) + m2 * G * L2 * c12, m2 * G * L2 * c12)
    return (m11, m12, m22), cv, gv


def desired(t, f, scale, ph):
    w = 2.0 * math.pi * f
    q = [Q0[i] + scale * AMP[i] * math.sin(w * t + ph[i]) for i in (0, 1)]
    qd = [scale * AMP[i] * w * math.cos(w * t + ph[i]) for i in (0, 1)]
    qdd = [-scale * AMP[i] * w * w * math.sin(w * t + ph[i]) for i in (0, 1)]
    return q, qd, qdd


def shared_draws(regime, seed):
    rng = random.Random(1000 * STREAM[regime] + seed)
    scale = rng.uniform(0.8, 1.0)
    ph = (rng.uniform(0.0, 2.0 * math.pi), rng.uniform(0.0, 2.0 * math.pi))
    n = int(round(REGIMES[regime][1] / SAMPLE)) + 1
    noise = [(rng.gauss(0.0, SIG_Q), rng.gauss(0.0, SIG_Q), rng.gauss(0.0, SIG_QD), rng.gauss(0.0, SIG_QD)) for _ in range(n)]
    return scale, ph, noise


def control(arm, qm, qdm, qr, qdr, qddr, payload_real, payload_c, d0):
    e = (qr[0] - qm[0], qr[1] - qm[1])
    ed = (qdr[0] - qdm[0], qdr[1] - qdm[1])
    v = (KP * e[0] + KD * ed[0], KP * e[1] + KD * ed[1])
    if arm == "A_pdg":
        _, _, gh = dyn(qm, qdm, payload_real)
        fb = (d0[0] * v[0], d0[1] * v[1])
        return (fb[0] + gh[0], fb[1] + gh[1]), fb
    mh, ch, gh = dyn(qm, qdm, payload_real if arm == "B_ct" else payload_c)
    a = (qddr[0] + v[0], qddr[1] + v[1])
    tau = (mh[0] * a[0] + mh[1] * a[1] + ch[0] + gh[0], mh[1] * a[0] + mh[2] * a[1] + ch[1] + gh[1])
    fb = (mh[0] * v[0] + mh[1] * v[1], mh[1] * v[0] + mh[2] * v[1])
    return tau, fb


def step_plant(q, qd, tau, payload, dt, friction=True, fc=None):
    m, cv, gv = dyn(q, qd, payload)
    # plant friction is FC * math.tanh(qd / 0.02) per joint (unmodelled); fc overrides FC
    fval = 0.0 if not friction else (FC if fc is None else fc)
    f = (fval * math.tanh(qd[0] / 0.02), fval * math.tanh(qd[1] / 0.02)) if fval else (0.0, 0.0)
    r0 = tau[0] - cv[0] - gv[0] - f[0]
    r1 = tau[1] - cv[1] - gv[1] - f[1]
    det = m[0] * m[2] - m[1] * m[1]
    a0 = (m[2] * r0 - m[1] * r1) / det
    a1 = (-m[1] * r0 + m[0] * r1) / det
    qd = [qd[0] + dt * a0, qd[1] + dt * a1]
    q = [q[0] + dt * qd[0], q[1] + dt * qd[1]]
    return q, qd


def run_arm(arm, regime, draws, dt, fc=None):
    f, dur, payload, payload_c = REGIMES[regime]
    scale, ph, noise = draws
    q, qd, _ = desired(0.0, f, scale, ph)
    m0, _, _ = dyn(desired(0.0, f, scale, ph)[0], (0.0, 0.0), payload)
    d0 = (m0[0], m0[2])
    n = int(round(dur / dt))
    se = peak = sfb = 0.0
    for k in range(n):
        t = k * dt
        qr, qdr, qddr = desired(t, f, scale, ph)
        nz = noise[int(t / SAMPLE + 1e-9)]
        qm = (q[0] + nz[0], q[1] + nz[1])
        qdm = (qd[0] + nz[2], qd[1] + nz[3])
        tau, fb = control(arm, qm, qdm, qr, qdr, qddr, payload, payload_c, d0)
        e2 = (qr[0] - q[0]) ** 2 + (qr[1] - q[1]) ** 2
        se += e2
        peak = max(peak, math.sqrt(e2))
        sfb += fb[0] ** 2 + fb[1] ** 2
        q, qd = step_plant(q, qd, tau, payload, dt, fc=fc)
    return {"rms": 1000.0 * math.sqrt(se / n), "peak": 1000.0 * peak, "fb": math.sqrt(sfb / n)}


def matched_error_run(h, steps=300):
    """B_ct with a constant target, no friction, no noise, 0.05 rad start error; |e| at the end."""
    qr = list(Q0)
    q, qd = [Q0[0] - 0.05, Q0[1] - 0.05], [0.0, 0.0]
    for _ in range(steps):
        tau, _ = control("B_ct", q, qd, qr, (0.0, 0.0), (0.0, 0.0), 0.5, 0.5, None)
        q, qd = step_plant(q, qd, tau, 0.5, h, friction=False)
    return math.hypot(qr[0] - q[0], qr[1] - q[1])



def centre_pose_stiffness(payload=0.5):
    """M, (M^{-1})22 and joint-2 stiffness at Q0; used by the post-hoc FC=0 block."""
    m, _, _ = dyn(Q0, (0.0, 0.0), payload)
    det = m[0] * m[2] - m[1] * m[1]
    minv22 = m[0] / det
    inv_m22 = 1.0 / m[2]
    k_ct = KP / minv22
    k_pd = m[2] * KP
    e_ct = 1000.0 * FC / k_ct
    e_pd = 1000.0 * FC / k_pd
    return m, minv22, inv_m22, k_ct, k_pd, e_ct, e_pd


def run(dt):
    out = {}
    for regime in REGIMES:
        draws = [shared_draws(regime, s) for s in SEEDS]
        out[regime] = {arm: [run_arm(arm, regime, d, dt) for d in draws] for arm in ARMS}
    return out


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-5:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs, m):
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{num(m)}+-{num(s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{num(m)}+-{num(s)}: {label}; {sign_note(diffs, m)}"


def main():
    print("Synthetic 2R arm: PD + gravity vs computed torque (matched) vs computed torque with the payload left out; not LQR, Smith or 2-DOF")
    print(f"L1={L1} L2={L2} m M1={M1} M2={M2} kg FC={FC} N m KP={KP} KD={KD} DT={DT} s noise q {SIG_Q} rad q' {SIG_QD} rad/s seeds={len(SEEDS)}")
    hs = h_star()
    print(f"stable step (matched error dynamics, semi-implicit Euler): H_STAR = 2*(sqrt(1+Z^2)-Z)/W = {hs * 1000:.4f} ms (W={math.sqrt(KP):.1f} rad/s, Z={KD / 2 / math.sqrt(KP):.2f}); DT/H_STAR = {DT / hs:.4f}")
    for k in (0.98, 1.02):
        e = matched_error_run(k * hs)
        print(f"  {k:.2f} x H_STAR: matched arm, |e| after 300 steps from 0.0707 rad: {e:.4e} rad ({'decays' if e < 0.0707 else 'grows'})")
    tab = run(DT)
    half = run(DT / 2.0)
    print("regime arm rms_mrad peak_mrad fb_torque_rms_Nm  (mean+-sd over seeds)")
    for regime, (f, dur, payload, payload_c) in REGIMES.items():
        print(f"{regime} (f {f} Hz, {dur} s; payload {payload} kg, C models {payload_c} kg)")
        res = tab[regime]
        for arm in ARMS:
            cols = ["{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in ("rms", "peak", "fb")]
            print(f"  {arm} " + " ".join(cols))
        for x, y in (("B_ct", "A_pdg"), ("C_ctwrong", "B_ct"), ("C_ctwrong", "A_pdg")):
            for key in ("rms", "fb"):
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[key] for r in res[x]], [r[key] for r in res[y]])}")
    drel = max(abs(a["rms"] - b["rms"]) / b["rms"] for rg in REGIMES for arm in ARMS for a, b in zip(tab[rg][arm], half[rg][arm]))
    print(f"half-step check (DT/2): max relative change in rms error {drel:.4f}")
    print("No winner declared: the model helps when inertia and coupling matter, adds little when gravity dominates, and hurts when the payload is wrong")
    print("Real arm / identification lab: 本页未运行; Wikipedia Inverse dynamics 以原文为准")
    # FC=0 sensitivity, added after the first run (not a pre-declared regime).
    print("FC=0 sensitivity (added after the first run; not a pre-declared regime)")
    m, minv22, inv_m22, k_ct, k_pd, e_ct, e_pd = centre_pose_stiffness()
    print(f"centre pose q=({Q0[0]}, {Q0[1]}) rad, payload 0.5 kg:")
    print(f"  M11={m[0]:.4f} M12={m[1]:.4f} M22={m[2]:.5f}")
    print(f"  (M⁻¹)22={num(minv22)}  1/M22={num(inv_m22)}")
    print(f"  stiffness KP/(M⁻¹)22={num(k_ct)} N m/rad vs D0 KP=M22 KP={num(k_pd)} N m/rad")
    print(f"  0.3 N m friction leaves {num(e_ct)} mrad vs {num(e_pd)} mrad")
    for regime in ("slow_quasi_static", "payload_mismatch"):
        draws = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [run_arm(arm, regime, d, DT, fc=0.0) for d in draws] for arm in ("A_pdg", "B_ct")}
        print(f"{regime} FC=0")
        print(f"  paired B-A rms: {verdict([r['rms'] for r in res['B_ct']], [r['rms'] for r in res['A_pdg']])}")


if __name__ == "__main__":
    main()
