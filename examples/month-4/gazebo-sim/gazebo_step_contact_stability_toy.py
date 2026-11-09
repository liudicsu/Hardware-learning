#!/usr/bin/env python3
"""Synthetic physics step-size (max_step_size) vs contact stability toy. Stdlib only.

Stand-in, NOT Gazebo/DART: a 1 kg box falls onto the ground through a linear
Kelvin-Voigt contact (spring k in parallel with damper c, active only while the
box penetrates the ground). Every arm uses the SAME semi-implicit (symplectic)
Euler integrator; only the step dt changes, like <max_step_size>.

  v[n+1] = v[n] + dt * a(x[n], v[n], t[n])
  x[n+1] = x[n] + dt * v[n+1]

Stability criterion of this integrator on the contact spring-damper
(omega = sqrt(k/m), zeta = c / (2 sqrt(k m))):
  (omega*dt)^2 + 4*zeta*(omega*dt) < 4   <=>   omega*dt < 2*(sqrt(zeta^2+1) - zeta)
Explicit (forward) Euler needs |1 + lambda*dt| < 1, i.e. omega*dt < 2*zeta.

Arms (shared plant, shared drop heights and shared disturbance force f(t)):
  A_coarse_3ms   dt = 3 ms   (stable, but only about two steps per contact)
  B_default_1ms  dt = 1 ms   (the lesson world's max_step_size)
  C_fine_0.1ms   dt = 0.1 ms (ten times the steps of B)
Reference: the same integrator at dt = 10 us (not an arm).

Common random numbers: per seed, one drop height and one disturbance sequence
f(t) (zero-order hold on a 0.1 ms grid) are drawn once; every arm and the
reference apply the SAME f(t), averaged over their own step so that every arm
receives the same impulse (integral of f) over any whole step.

Regimes (5 seeds): impact_drop (coarse loses) and gentle_rest (no impact:
near-tie / small gap). No presumed winner. Real Gazebo / DART: 本页未运行.
"""
from __future__ import annotations

import math
import random

M = 1.0  # kg
G = 9.81  # m/s^2
K = 2.5e5  # N/m contact stiffness (synthetic)
ZETA = 0.2  # contact damping ratio (synthetic)
C = 2.0 * ZETA * math.sqrt(K * M)  # N s/m
OMEGA = math.sqrt(K / M)  # rad/s
NOISE_DT = 1e-4  # disturbance grid, s
NOISE_SIGMA = 0.5  # N, disturbance force sd
LIFTOFF_V = math.sqrt(2.0 * G * 1e-3)  # count a bounce if it would rise >= 1 mm
SEEDS = (0, 1, 2, 3, 4)
ARMS = (("A_coarse_3ms", 3e-3), ("B_default_1ms", 1e-3), ("C_fine_0.1ms", 1e-4))
REF_DT = 1e-5
REGIMES = (("impact_drop", 0.6), ("gentle_rest", 0.2))  # (name, simulated seconds)


def si_euler_limit(zeta: float = ZETA) -> float:
    """Largest stable omega*dt for semi-implicit Euler on m x'' + c x' + k x = 0."""
    return 2.0 * (math.sqrt(zeta * zeta + 1.0) - zeta)


def explicit_euler_limit(zeta: float = ZETA) -> float:
    """Largest stable omega*dt for explicit Euler (|1 + lambda dt| < 1)."""
    return 2.0 * zeta


def spectral_radius_si(dt: float) -> float:
    """|largest eigenvalue| of the semi-implicit Euler step on the contact spring-damper."""
    a = dt * C / M
    b = dt * dt * K / M
    tr = 2.0 - a - b
    det = 1.0 - a
    disc = tr * tr - 4.0 * det
    if disc >= 0.0:
        r = math.sqrt(disc)
        return max(abs((tr + r) / 2.0), abs((tr - r) / 2.0))
    return math.sqrt(det)  # complex pair: |lambda|^2 = det


def spectral_radius_explicit(dt: float) -> float:
    """|1 + lambda dt| for explicit Euler on the same spring-damper."""
    wd = OMEGA * math.sqrt(1.0 - ZETA * ZETA)
    re = 1.0 - ZETA * OMEGA * dt
    return math.hypot(re, wd * dt)


def shared_draws(seed: int, regime: str, t_end: float) -> tuple[float, list[float]]:
    """Common random numbers: identical for every arm and the reference."""
    rng = random.Random(9_000 + 31 * seed + (0 if regime == "impact_drop" else 7))
    h0 = 0.10 + rng.uniform(-0.02, 0.02) if regime == "impact_drop" else 0.0
    n = int(round(t_end / NOISE_DT)) + 2
    force = [rng.gauss(0.0, NOISE_SIGMA) for _ in range(n)]
    return h0, force


def impulse_prefix(force: list[float]) -> list[float]:
    """P[i] = integral of the zero-order-hold f(t) from 0 to i*NOISE_DT."""
    p = [0.0]
    for f in force:
        p.append(p[-1] + f * NOISE_DT)
    return p


def impulse_until(force: list[float], prefix: list[float], t: float) -> float:
    """Integral of f from 0 to t (exact for the zero-order-hold grid)."""
    i = min(int(t / NOISE_DT + 1e-9), len(force) - 1)
    return prefix[i] + force[i] * (t - i * NOISE_DT)


def simulate(dt: float, regime: str, h0: float, force: list[float], t_end: float) -> dict:
    """Integrate one run. x is the box bottom height (negative = penetration)."""
    if regime == "impact_drop":
        x, v = h0, 0.0
    else:
        x, v = -M * G / K, 0.0  # resting exactly at static equilibrium
    steps = int(round(t_end / dt))
    max_pen = max(0.0, -x)
    bounces = 0
    in_contact = x < 0.0
    first_apex = None  # highest point after the first liftoff, before the next touch
    tracking_apex = False
    prefix = impulse_prefix(force)
    for n in range(steps):
        t = n * dt
        # step-averaged disturbance: same impulse per whole step for every dt
        f_ext = (impulse_until(force, prefix, t + dt) - impulse_until(force, prefix, t)) / dt
        f_contact = (-K * x - C * v) if x < 0.0 else 0.0
        a = (f_contact + f_ext) / M - G
        v = v + dt * a
        x = x + dt * v
        if x < 0.0 and not in_contact:
            in_contact = True
            tracking_apex = False
        elif x >= 0.0 and in_contact:
            in_contact = False
            if v >= LIFTOFF_V:
                bounces += 1
                if bounces == 1:
                    tracking_apex = True
                    first_apex = x
        if tracking_apex:
            first_apex = max(first_apex, x)
        max_pen = max(max_pen, -x)
    # Coefficient of restitution from heights: e = sqrt(h_apex / h_drop) (energy ratio e^2)
    first_cor = math.sqrt(first_apex / h0) if (first_apex is not None and h0 > 0.0) else None
    return {"max_pen": max_pen, "bounces": bounces, "cor": first_cor, "steps": steps}


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def run_regime(regime: str, t_end: float) -> dict:
    """Per arm: lists over seeds of |max_pen - ref| (um), bounces, |COR - ref|, max_pen."""
    out = {name: {"pen_err_um": [], "bounces": [], "cor_err": [], "pen_um": []} for name, _ in ARMS}
    refs = []
    for seed in SEEDS:
        h0, force = shared_draws(seed, regime, t_end)
        ref = simulate(REF_DT, regime, h0, force, t_end)
        refs.append(ref)
        for name, dt in ARMS:
            r = simulate(dt, regime, h0, force, t_end)
            out[name]["pen_err_um"].append(abs(r["max_pen"] - ref["max_pen"]) * 1e6)
            out[name]["pen_um"].append(r["max_pen"] * 1e6)
            out[name]["bounces"].append(float(r["bounces"]))
            if ref["cor"] is not None and r["cor"] is not None:
                out[name]["cor_err"].append(abs(r["cor"] - ref["cor"]))
    out["_ref"] = refs
    return out


def main() -> None:
    print("Synthetic Kelvin-Voigt contact stand-in (not DART); semi-implicit Euler; shared drop heights and f(t)")
    lim = si_euler_limit()
    print(
        f"m={M}kg k={K:.0f}N/m zeta={ZETA} omega={OMEGA:.1f}rad/s seeds={len(SEEDS)} "
        f"noise_sd={NOISE_SIGMA}N ref_dt=10us"
    )
    print(
        f"criterion semi-implicit Euler: omega*dt < 2*(sqrt(zeta^2+1)-zeta) = {lim:.4f} "
        f"-> dt < {lim / OMEGA * 1e3:.3f} ms; explicit Euler: omega*dt < 2*zeta = "
        f"{explicit_euler_limit():.4f} -> dt < {explicit_euler_limit() / OMEGA * 1e3:.3f} ms"
    )
    print("dt_ms omega_dt rho_semi_implicit rho_explicit")
    for dt in (1e-4, 1e-3, 3e-3, 3.2e-3, 3.4e-3, 4e-3):
        rs, re_ = spectral_radius_si(dt), spectral_radius_explicit(dt)
        print(
            f"{dt * 1e3:.1f} {OMEGA * dt:.3f} {rs:.4f}{' UNSTABLE' if rs >= 1 else ''} "
            f"{re_:.4f}{' UNSTABLE' if re_ >= 1 else ''}"
        )
    print("regime arm steps_per_sim_s max_pen_um |pen-ref|_um bounces |COR-ref| (mean+-sd over seeds)")
    summary = {}
    for regime, t_end in REGIMES:
        res = run_regime(regime, t_end)
        refs = res["_ref"]
        rp = mean_sd([r["max_pen"] * 1e6 for r in refs])
        rb = mean_sd([float(r["bounces"]) for r in refs])
        line = f"{regime} reference_10us {1 / REF_DT:.0f} {rp[0]:.2f}+-{rp[1]:.2f} - {rb[0]:.2f}+-{rb[1]:.2f}"
        cors = [r["cor"] for r in refs if r["cor"] is not None]
        if cors:
            rc = mean_sd(cors)
            line += f" COR={rc[0]:.4f}+-{rc[1]:.4f}"
        print(line)
        for name, dt in ARMS:
            d = res[name]
            pm, ps = mean_sd(d["pen_um"])
            em, es = mean_sd(d["pen_err_um"])
            bm, bs = mean_sd(d["bounces"])
            cor = "-"
            if len(d["cor_err"]) == len(SEEDS):
                cm, cs = mean_sd(d["cor_err"])
                cor = f"{cm:.4f}+-{cs:.4f}"
            summary[(regime, name)] = (em, es, pm, ps)
            print(
                f"{regime} {name} {1 / dt:.0f} {pm:.2f}+-{ps:.2f} {em:.2f}+-{es:.2f} "
                f"{bm:.2f}+-{bs:.2f} {cor}"
            )
    ia, ib, ic = (summary[("impact_drop", n)] for n, _ in ARMS)
    print(
        f"impact_drop: |pen-ref| A {ia[0]:.2f}+-{ia[1]:.2f} um, B {ib[0]:.2f}+-{ib[1]:.2f} um, "
        f"C {ic[0]:.2f}+-{ic[1]:.2f} um (A is stable, rho<1, yet about two steps per contact: coarse loses)"
    )
    ga, gb, gc = (summary[("gentle_rest", n)] for n, _ in ARMS)
    print(
        f"gentle_rest: |pen-ref| A {ga[0]:.3f}+-{ga[1]:.3f} um, B {gb[0]:.3f}+-{gb[1]:.3f} um, "
        f"C {gc[0]:.3f}+-{gc[1]:.3f} um on a {M * G / K * 1e6:.2f} um static sag; "
        f"near-tie / small gap, not a tie (bounce counts are identical: 0)"
    )
    print("No winner declared: smaller steps cost compute (steps per simulated second); a step past the criterion diverges however cheap it is")
    print("Real Gazebo / DART contact solver: 本页未运行; SDFormat/Gazebo docs 以原文为准")


if __name__ == "__main__":
    main()
