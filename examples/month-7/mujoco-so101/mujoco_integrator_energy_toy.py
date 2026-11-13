#!/usr/bin/env python3
"""Synthetic energy-drift comparison of explicit, semi-implicit and
implicit-in-velocity Euler, as a stdlib stand-in of the updates in the
MuJoCo Computation documentation (Integrators).

Stdlib only. Not mujoco.step, not a redo of grip_sweep (timestep x solref
on a soft-contact lift), and not a rewrite of the Menagerie implicitfast
one-liner. Real MuJoCo / Menagerie: 本页未运行.

Two shared plants, same h grid idea, initial energy printed:
  pendulum  simple pendulum with light linear damping (position-dependent
            gravity + velocity-dependent damping)
  spinner   torque-free rigid body with asymmetric inertia (gyroscopic
            bias; energy is 1/2 w·I w; no quaternion is used)

Arms:
  A_explicit     v_{t+h}=v_t+h a_t,      q_{t+h}=q_t+h v_t
  B_semimpl      v_{t+h}=v_t+h a_t,      q_{t+h}=q_t+h v_{t+h}
  C_implvel      implicit-in-velocity: v_{t+h}=v_t+h Mhat^{-1} M a_t,
                 Mhat=M+h D, D = -d(forces)/dv; then q uses v_{t+h}
  C_bad          same as C but with a sign-flipped D (inconsistent
                 linearization; declared fail arm; kept)

For the spinner, energy depends only on w, so A and B use the same
velocity update (the documented difference is the position step).

Regimes (declared before the first run):
  moderate_h     lightly damped pendulum, moderate h -> B,C consistent
                 lower |dE| than A
  tiny_h         very small h -> A,B,C may near-tie on |dE|
  large_h_spin   large h and/or a fast tumble -> A consistent lose
                 (energy gain or blow-up)
  inconsistent_D flipped gyro D -> C_bad may lose (energy gain); kept

Stable-step criterion (mandatory): for the undamped linear oscillator
x''+w0^2 x=0, semi-implicit Euler has amplification trace 2-h^2 w0^2
and stays on the unit circle iff h < h* = 2/w0. At h = h* the trace
is -2, so -1 is a repeated eigenvalue in a Jordan block and the
solution grows linearly (analytic; not printed). The default moderate
h is below h*. The toy prints a time-domain energy-bounded run and the
spectral radius at 0.50x, 0.98x and 1.02x h*.

Damped criterion (this toy's update: damping sits in a_t, i.e. the old
velocity): v_n=(1-h c)v - h w0^2 x, x_n=x+h v_n, c=2 zeta w0. Jury:
asymptotically stable iff (w0 h)^2 + 4 zeta w0 h < 4 (strict). The toy
prints zeta, h_star_damped and spectral radii at 0.98x / 1.02x, plus a
small (zeta, h) table. At equality a simple eigenvalue is -1 when
zeta>0 (analytic; the Jordan block is only the zeta=0 case).

Common random numbers: per-seed initial-condition jitter is drawn once
and reused by every arm. Seeds 0-4.
MuJoCo Computation documentation: body read; 以原文为准.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
# pendulum (written before the first run)
G = 9.81
L = 1.0
MASS = 1.0
INERTIA_P = MASS * L * L
C_DAMP = 0.05
OMEGA0 = math.sqrt(G / L)
H_STAR = 2.0 / OMEGA0
H_MOD = 0.15
H_TINY = 0.005
H_LARGE = 0.55
T_PEND = 20.0
TH0 = 0.40
# spinner
I_DIAG = (1.0, 2.0, 3.0)
W_SPIN = (0.40, 5.00, 0.30)  # perturbation off the intermediate axis
H_SPIN = 0.08
T_SPIN = 6.0
BLOW = 100.0
ARMS = ("A_explicit", "B_semimpl", "C_implvel", "C_bad")
# written before the first run
REGIMES = ("moderate_h", "tiny_h", "large_h_spin", "inconsistent_D")
STREAM = {"pendulum": 0, "spinner": 1}


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    if len(xs) == 1:
        return mu, 0.0
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
    if not math.isfinite(x):
        return "nan"
    if x != 0.0 and abs(x) < 5e-5:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs: list[float], m: float) -> str:
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def verdict(xa: list[float], xb: list[float]) -> str:
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


def pend_energy(th: float, w: float) -> float:
    return 0.5 * INERTIA_P * w * w + MASS * G * L * (1.0 - math.cos(th))


def pend_acc(th: float, w: float, damp: float = C_DAMP) -> float:
    return -(G / L) * math.sin(th) - (damp / INERTIA_P) * w


def tiny_step_ref(th: float, w: float, t_end: float, damp: float = C_DAMP) -> tuple[float, float, float]:
    # semi-implicit at a very small step, for trajectory and energy error
    h = 1e-4
    n = int(round(t_end / h))
    for _ in range(n):
        a = pend_acc(th, w, damp)
        w = w + h * a
        th = th + h * w
    return th, w, pend_energy(th, w)


def step_pend(th: float, w: float, h: float, arm: str, damp: float = C_DAMP) -> tuple[float, float]:
    a = pend_acc(th, w, damp)
    if arm == "A_explicit":
        th_n = th + h * w
        w_n = w + h * a
        return th_n, w_n
    if arm == "B_semimpl":
        w_n = w + h * a
        th_n = th + h * w_n
        return th_n, w_n
    # implicit-in-velocity: D = damp, M = INERTIA_P
    # a = M^{-1}(tau_grav - damp w), da/dw = -M^{-1} D with D = damp
    sign = -1.0 if arm == "C_bad" else 1.0
    D = sign * damp
    mhat = INERTIA_P + h * D
    w_n = w + h * (INERTIA_P / mhat) * a
    th_n = th + h * w_n
    return th_n, w_n


def run_pend(th0: float, w0: float, h: float, t_end: float, arm: str, damp: float = C_DAMP) -> dict:
    th, w = th0, w0
    e0 = pend_energy(th, w)
    e_max, e_last = e0, e0
    n = int(round(t_end / h))
    blow = False
    for _ in range(n):
        th, w = step_pend(th, w, h, arm, damp)
        if not math.isfinite(th) or not math.isfinite(w):
            blow = True
            e_last = float("inf")
            break
        e = pend_energy(th, w)
        e_last = e
        if e > e_max:
            e_max = e
        if e > BLOW * e0 or e < -BLOW * e0:
            blow = True
            break
    dE = e_last - e0
    th_r, w_r, e_ref = tiny_step_ref(th0, w0, t_end, damp)
    err = abs((th - th_r + math.pi) % (2 * math.pi) - math.pi) if math.isfinite(th) else float("inf")
    e_err = abs(e_last - e_ref) if math.isfinite(e_last) else float("inf")
    return {"dE": dE, "absdE": abs(dE) if math.isfinite(dE) else float("inf"), "emax": e_max, "e0": e0, "blow": int(blow), "traj_err": err, "e_err": e_err, "e_ref": e_ref}


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def imul(w):
    return (I_DIAG[0] * w[0], I_DIAG[1] * w[1], I_DIAG[2] * w[2])


def spin_energy(w) -> float:
    iw = imul(w)
    return 0.5 * (w[0] * iw[0] + w[1] * iw[1] + w[2] * iw[2])


def spin_acc(w):
    # I wdot = - w x (I w)
    tau = cross(w, imul(w))  # w x I w
    return (-tau[0] / I_DIAG[0], -tau[1] / I_DIAG[1], -tau[2] / I_DIAG[2])


def add(a, b, s=1.0):
    return (a[0] + s * b[0], a[1] + s * b[1], a[2] + s * b[2])


def D_gyro(w):
    # derivative of (w x I w) applied to basis; D = d(w x I w)/dw
    # J(u) = u x (I w) + w x (I u)
    rows = []
    for k in range(3):
        u = (1.0 if k == 0 else 0.0, 1.0 if k == 1 else 0.0, 1.0 if k == 2 else 0.0)
        ju = add(cross(u, imul(w)), cross(w, imul(u)))
        rows.append(ju)
    # rows are J(e_k); we want columns = J(e_k)
    return [[rows[k][i] for k in range(3)] for i in range(3)]


def solve3(A, b):
    # Gaussian elimination with partial pivot
    M = [A[i][:] + [b[i]] for i in range(3)]
    for k in range(3):
        piv = max(range(k, 3), key=lambda r: abs(M[r][k]))
        M[k], M[piv] = M[piv], M[k]
        if abs(M[k][k]) < 1e-18:
            return None
        inv = 1.0 / M[k][k]
        for j in range(k, 4):
            M[k][j] *= inv
        for i in range(3):
            if i == k:
                continue
            f = M[i][k]
            for j in range(k, 4):
                M[i][j] -= f * M[k][j]
    return (M[0][3], M[1][3], M[2][3])


def step_spin(w, h, arm: str):
    a = spin_acc(w)
    if arm in ("A_explicit", "B_semimpl"):
        return add(w, a, h)
    # implicit-in-velocity, eq. (6): (I + h D) (w' - w) = h I a
    # a = I^{-1}(- w x I w), D = d(w x I w)/dw  so da/dw = -I^{-1} D
    Dg = D_gyro(w)
    sign = -1.0 if arm == "C_bad" else 1.0
    Mhat = [[(I_DIAG[i] if i == j else 0.0) + h * sign * Dg[i][j] for j in range(3)] for i in range(3)]
    rhs = (h * I_DIAG[0] * a[0], h * I_DIAG[1] * a[1], h * I_DIAG[2] * a[2])
    dw = solve3(Mhat, rhs)
    if dw is None:
        return (float("inf"), float("inf"), float("inf"))
    return add(w, dw)


def run_spin(w0, h, t_end, arm: str) -> dict:
    w = w0
    e0 = spin_energy(w)
    e_last, e_max = e0, e0
    blow = False
    n = int(round(t_end / h))
    for _ in range(n):
        w = step_spin(w, h, arm)
        if not all(math.isfinite(x) for x in w):
            blow = True
            e_last = float("inf")
            break
        e = spin_energy(w)
        e_last = e
        if e > e_max:
            e_max = e
        if e > BLOW * e0:
            blow = True
            break
    dE = e_last - e0
    return {"dE": dE, "absdE": abs(dE) if math.isfinite(dE) else float("inf"), "emax": e_max, "e0": e0, "blow": int(blow)}


def ic_pend(seed: int) -> tuple[float, float]:
    rng = random.Random(1000 * STREAM["pendulum"] + seed)
    return TH0 + rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)


def ic_spin(seed: int) -> tuple[float, float, float]:
    rng = random.Random(1000 * STREAM["spinner"] + seed)
    return (W_SPIN[0] + rng.uniform(-0.05, 0.05), W_SPIN[1] + rng.uniform(-0.05, 0.05), W_SPIN[2] + rng.uniform(-0.05, 0.05))


def amp_matrix(h: float, omega: float, c: float = 0.0) -> list[list[float]]:
    # semi-implicit; damping (if any) is evaluated at the old velocity:
    # v_n = (1 - h c) v - h omega^2 x; x_n = x + h v_n
    # c = 0 recovers the undamped map used by the h* tests above
    w2 = omega * omega
    return [[1.0 - h * h * w2, h * (1.0 - h * c)], [-h * w2, 1.0 - h * c]]


def spectral_radius(M: list[list[float]]) -> float:
    # 2x2 eigenvalues
    tr = M[0][0] + M[1][1]
    det = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    disc = tr * tr - 4.0 * det
    if disc >= 0:
        s = math.sqrt(disc)
        evs = [abs(0.5 * (tr + s)), abs(0.5 * (tr - s))]
    else:
        r = math.sqrt(abs(det))  # for this symplectic map det=1, |λ|=1
        evs = [r, r]
    return max(evs)


def energy_bounded_run(h: float, t_end: float) -> int:
    # undamped linear oscillator, semi-implicit, unit energy
    # x'' + OMEGA0^2 x = 0, E = 0.5 (v^2 + w0^2 x^2)
    x, v = 1.0, 0.0
    e0 = 0.5 * OMEGA0 * OMEGA0 * x * x
    n = int(round(t_end / h))
    for _ in range(n):
        v = v - h * OMEGA0 * OMEGA0 * x
        x = x + h * v
        if not math.isfinite(x) or not math.isfinite(v):
            return 0
        e = 0.5 * (v * v + OMEGA0 * OMEGA0 * x * x)
        if e > BLOW * e0:
            return 0
    return 1


def main() -> None:
    print("mujoco_integrator_energy_toy")
    print(f"seeds={len(SEEDS)} omega0={OMEGA0:.10f} rad/s h_star={H_STAR:.10f} s  (semi-implicit linear oscillator, h < 2/omega0)")
    print(f"default moderate h={H_MOD:.4f} s  h/h_star={H_MOD/H_STAR:.4f}  assert_below_hstar={int(H_MOD < H_STAR)}")
    print(f"pendulum C_damp={C_DAMP} I={INERTIA_P} L={L} T={T_PEND}")
    print(f"spinner I={I_DIAG} H_spin={H_SPIN} T_spin={T_SPIN}")
    print("regimes declared before the first run: " + ", ".join(REGIMES))
    print("common random numbers: per-seed IC jitter reused by every arm")
    print("stdlib ODE stand-in of documented updates, not mujoco.step; ≠ grip_sweep")
    print("MuJoCo Euler is semi-implicit; implicit/implicitfast are implicit only in velocity-dependent forces")
    print("explicit Euler is described but not implemented in MuJoCo; 本页未运行")
    # stable-step tests
    print()
    print("stable-step criterion tests (semi-implicit, undamped linear oscillator, T=40 s):")
    for tag, h in (
        ("0.50x_hstar", 0.50 * H_STAR),
        ("0.98x_hstar", 0.98 * H_STAR),
        ("1.02x_hstar", 1.02 * H_STAR),
        ("half_default", 0.50 * H_MOD),
        ("default_h", H_MOD),
    ):
        rho = spectral_radius(amp_matrix(h, OMEGA0))
        bounded = energy_bounded_run(h, 40.0)
        print(f"  {tag} h={h:.10f} spectral_radius={rho:.6f} energy_bounded={bounded}")
    print(f"  above_hstar_grows={int(energy_bounded_run(1.02 * H_STAR, 40.0) == 0)}  below_hstar_bounded={int(energy_bounded_run(0.98 * H_STAR, 40.0) == 1)}")

    # pendulum regimes
    configs = {
        "moderate_h": ("pendulum", H_MOD, T_PEND),
        "tiny_h": ("pendulum", H_TINY, T_PEND),
        "large_h_spin": ("both", None, None),
        "inconsistent_D": ("spinner", H_SPIN, T_SPIN),
    }
    for regime in REGIMES:
        print()
        if regime == "large_h_spin":
            # large-h pendulum + fast spinner
            print(f"{regime} (pendulum h={H_LARGE} and spinner h={H_SPIN}, declared lose for A):")
            pend = {arm: [run_pend(*ic_pend(s), H_LARGE, T_PEND, arm) for s in SEEDS] for arm in ("A_explicit", "B_semimpl", "C_implvel")}
            spin = {arm: [run_spin(ic_spin(s), H_SPIN, T_SPIN, arm) for s in SEEDS] for arm in ARMS}
            for plant, bag, arms in (("pendulum_large_h", pend, ("A_explicit", "B_semimpl", "C_implvel")), ("spinner_fast", spin, ARMS)):
                print(f"  {plant}:")
                for arm in arms:
                    dE = [r["dE"] for r in bag[arm]]
                    adE = [r["absdE"] for r in bag[arm]]
                    blow = [r["blow"] for r in bag[arm]]
                    extra = ""
                    if plant.startswith("pendulum"):
                        err = [r["traj_err"] for r in bag[arm]]
                        eer = [r["e_err"] for r in bag[arm]]
                        extra = f"  traj_err {num(mean_sd(err)[0])}+-{num(mean_sd(err)[1])} rad  |E-Eref| {num(mean_sd(eer)[0])}+-{num(mean_sd(eer)[1])}"
                    print(f"    {arm} dE {num(mean_sd(dE)[0])}+-{num(mean_sd(dE)[1])}  |dE| {num(mean_sd(adE)[0])}+-{num(mean_sd(adE)[1])}  blow {sum(blow)}/5{extra}")
                adA = [r["absdE"] for r in bag["A_explicit"]]
                adB = [r["absdE"] for r in bag["B_semimpl"]]
                adC = [r["absdE"] for r in bag["C_implvel"]]
                print(f"    paired A-B |dE|: {verdict(adA, adB)}")
                print(f"    paired A-C |dE|: {verdict(adA, adC)}")
                print(f"    paired B-C |dE|: {verdict(adB, adC)}")
                if plant.startswith("pendulum"):
                    erA = [r["e_err"] for r in bag["A_explicit"]]
                    erB = [r["e_err"] for r in bag["B_semimpl"]]
                    erC = [r["e_err"] for r in bag["C_implvel"]]
                    print(f"    paired A-B |E-Eref|: {verdict(erA, erB)}")
                    print(f"    paired A-C |E-Eref|: {verdict(erA, erC)}")
                    print(f"    paired B-C |E-Eref|: {verdict(erB, erC)}")
                if plant.startswith("spinner"):
                    adBad = [r["absdE"] for r in bag["C_bad"]]
                    print(f"    paired C_bad-C |dE|: {verdict(adBad, adC)}")
            continue
        kind, h, t_end = configs[regime]
        if kind == "pendulum":
            print(f"{regime} (pendulum h={h} T={t_end}):")
            bag = {arm: [run_pend(*ic_pend(s), h, t_end, arm) for s in SEEDS] for arm in ("A_explicit", "B_semimpl", "C_implvel")}
            arms = ("A_explicit", "B_semimpl", "C_implvel")
        else:
            print(f"{regime} (spinner h={h} T={t_end}, inconsistent D sign-flipped):")
            bag = {arm: [run_spin(ic_spin(s), h, t_end, arm) for s in SEEDS] for arm in ARMS}
            arms = ARMS
        for arm in arms:
            dE = [r["dE"] for r in bag[arm]]
            adE = [r["absdE"] for r in bag[arm]]
            blow = [r["blow"] for r in bag[arm]]
            extra = ""
            if kind == "pendulum":
                err = [r["traj_err"] for r in bag[arm]]
                eer = [r["e_err"] for r in bag[arm]]
                extra = f"  traj_err {num(mean_sd(err)[0])}+-{num(mean_sd(err)[1])} rad  |E-Eref| {num(mean_sd(eer)[0])}+-{num(mean_sd(eer)[1])}"
            print(f"  {arm} dE {num(mean_sd(dE)[0])}+-{num(mean_sd(dE)[1])}  |dE| {num(mean_sd(adE)[0])}+-{num(mean_sd(adE)[1])}  blow {sum(blow)}/5{extra}")
        adA = [r["absdE"] for r in bag["A_explicit"]]
        adB = [r["absdE"] for r in bag["B_semimpl"]]
        adC = [r["absdE"] for r in bag["C_implvel"]]
        print(f"  paired A-B |dE|: {verdict(adA, adB)}")
        print(f"  paired A-C |dE|: {verdict(adA, adC)}")
        print(f"  paired B-C |dE|: {verdict(adB, adC)}")
        if kind == "pendulum":
            erA = [r["e_err"] for r in bag["A_explicit"]]
            erB = [r["e_err"] for r in bag["B_semimpl"]]
            erC = [r["e_err"] for r in bag["C_implvel"]]
            print(f"  paired A-B |E-Eref|: {verdict(erA, erB)}")
            print(f"  paired A-C |E-Eref|: {verdict(erA, erC)}")
            print(f"  paired B-C |E-Eref|: {verdict(erB, erC)}")
        if kind != "pendulum":
            adBad = [r["absdE"] for r in bag["C_bad"]]
            print(f"  paired C_bad-C |dE|: {verdict(adBad, adC)}")
            print(f"  A vs B on spinner velocity update: {verdict(adA, adB)}")

    print()
    print("alternative C_damp=0.0 on moderate_h (same seeds):")
    bag = {arm: [run_pend(*ic_pend(s), H_MOD, T_PEND, arm, 0.0) for s in SEEDS] for arm in ("A_explicit", "B_semimpl", "C_implvel")}
    for arm in ("A_explicit", "B_semimpl", "C_implvel"):
        dE = [r["dE"] for r in bag[arm]]
        adE = [r["absdE"] for r in bag[arm]]
        eer = [r["e_err"] for r in bag[arm]]
        blow = [r["blow"] for r in bag[arm]]
        print(f"  {arm} dE {num(mean_sd(dE)[0])}+-{num(mean_sd(dE)[1])}  |dE| {num(mean_sd(adE)[0])}+-{num(mean_sd(adE)[1])}  |E-Eref| {num(mean_sd(eer)[0])}+-{num(mean_sd(eer)[1])}  blow {sum(blow)}/5")
    adA = [r["absdE"] for r in bag["A_explicit"]]
    adB = [r["absdE"] for r in bag["B_semimpl"]]
    adC = [r["absdE"] for r in bag["C_implvel"]]
    print(f"  paired A-B |dE|: {verdict(adA, adB)}")
    print(f"  paired A-C |dE|: {verdict(adA, adC)}")
    print(f"  paired B-C |dE|: {verdict(adB, adC)}")

    # Damped Jury criterion for this toy's B_semimpl update (added after the original regimes).
    zeta = C_DAMP / (2.0 * OMEGA0 * INERTIA_P)
    c_lin = 2.0 * zeta * OMEGA0
    h_star_d = 2.0 / (OMEGA0 * (zeta + math.sqrt(zeta * zeta + 1.0)))

    def jury_lhs(h: float, z: float) -> float:
        return (OMEGA0 * h) ** 2 + 4.0 * z * OMEGA0 * h

    print()
    print("damped semi-implicit criterion (added after the original regimes; not a pre-declared regime):")
    print("  toy update: damping in a_t (old velocity), then x += h v_new; c = 2 zeta omega0")
    print("  Jury: asymptotically stable iff (omega0 h)^2 + 4 zeta omega0 h < 4 (strict)")
    print(
        f"  zeta={zeta:.10f} c={c_lin:.10f} h_star_damped={h_star_d:.10f} s  "
        f"(equals 2/omega0 at zeta=0)"
    )
    print(
        f"  default moderate h={H_MOD:.4f} s  h/h_star_damped={H_MOD / h_star_d:.4f}  "
        f"assert_below_hstar_damped={int(H_MOD < h_star_d)}"
    )
    print("  spectral-radius checks at this page's zeta:")
    for tag, h in (
        ("0.98x_hstar_damped", 0.98 * h_star_d),
        ("1.00x_hstar_damped", 1.00 * h_star_d),
        ("1.02x_hstar_damped", 1.02 * h_star_d),
        ("default_h", H_MOD),
    ):
        rr = spectral_radius(amp_matrix(h, OMEGA0, c_lin))
        lhs = jury_lhs(h, zeta)
        print(
            f"    {tag} h={h:.10f} spectral_radius={rr:.6f} "
            f"jury_lhs={lhs:.6f} rho_lt_one={int(rr < 1.0 - 1e-12)}"
        )
    r098 = spectral_radius(amp_matrix(0.98 * h_star_d, OMEGA0, c_lin))
    r102 = spectral_radius(amp_matrix(1.02 * h_star_d, OMEGA0, c_lin))
    req = spectral_radius(amp_matrix(h_star_d, OMEGA0, c_lin))
    print(
        f"  below_hstar_damped_rho_lt_one={int(r098 < 1.0 - 1e-12)}  "
        f"above_hstar_damped_rho_gt_one={int(r102 > 1.0 + 1e-12)}"
    )
    print(
        f"  at_hstar_damped spectral_radius={req:.6f}  "
        f"(simple eigenvalue -1 when zeta>0; Jordan block only at zeta=0; analytic)"
    )
    print("  (zeta, h) spectral-radius table (0.98x / 1.02x of that zeta's h_star_damped):")
    for z in (0.0, 0.05, 0.20, 1.00):
        hs = 2.0 / (OMEGA0 * (z + math.sqrt(z * z + 1.0)))
        cz = 2.0 * z * OMEGA0
        for scale, tag in ((0.98, "0.98x"), (1.02, "1.02x")):
            h = scale * hs
            rr = spectral_radius(amp_matrix(h, OMEGA0, cz))
            lhs = jury_lhs(h, z)
            print(
                f"    zeta={z:.2f} {tag} h_star_damped={hs:.10f} h={h:.10f} "
                f"spectral_radius={rr:.6f} jury_lhs={lhs:.6f}"
            )
    print("Real MuJoCo / Menagerie: 本页未运行; MuJoCo Computation documentation 以原文为准")


if __name__ == "__main__":
    main()
