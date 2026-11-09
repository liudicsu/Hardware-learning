#!/usr/bin/env python3
"""Synthetic gear-efficiency-under-load literacy toy. Stdlib only.

Shared motor τ–ω schedule and gear ratio for every arm. Friction draws
(τ_c, b_v) are **common random numbers**: for a given seed, A/B/C see the
identical Coulomb + viscous pair (arms do not get private friction luck).

Arms:
  A_constant_eta     P_out = η0 · P_in with fixed η0=0.9 (lesson guess)
  B_coulomb_viscous  τ_out = n·τ_in − (τ_c·sign(ω_out) + b_v·ω_out)
  C_heavy_fit_eta    constant η fitted only on the heavy-load operating points of B

Regimes (≥5 seeds):
  heavy_load  — design point used to fit η: A near-ties B on η
  light_load  — same drag at fixed speed; P_in drops so η falls; constant-η diverges

Assumptions (stated for the page): B is a **load-independent drag** loss
τ_loss = τ_c·sign(ω) + b_v·ω with **no τ_in term**. At fixed speed the loss
power is constant, so light-load η falls because P_in drops — not because the
drag grew with torque. Mesh friction ∝ transmitted load is **out of scope**.
Forward driving; back-driving needs a separate η_b / breakaway check.
≠ backlash-in-loop. Not a gearbox dyno. Real dyno: 本页未运行.
"""
from __future__ import annotations

import math
import random

N_RATIO = 25.0  # two 5:1 stages (matches lesson arithmetic)
ETA0 = 0.9  # a-priori constant guess (lesson printed-gear guess)
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_constant_eta", "B_coulomb_viscous", "C_heavy_fit_eta")
# Shared τ–ω operating points (motor shaft). Heavy used to fit C; light shows gap.
OPS = {
    "heavy_load": {"tau_in": 0.050, "omega_in": 628.0},  # ~6000 rpm, lesson load
    "light_load": {"tau_in": 0.008, "omega_in": 628.0},  # same speed, light torque
}
# Nominal friction (perturbed per seed, shared across arms)
TAU_C0 = 0.12  # N·m at output (Coulomb)
B_V0 = 0.00035  # N·m·s/rad at output (viscous)
FRIC_REL_STD = 0.08


def shared_friction(seed: int) -> tuple[float, float]:
    """Common random numbers: identical (τ_c, b_v) for every arm at this seed."""
    rng = random.Random(40_000 + seed)  # seed only — no arm salt
    tau_c = TAU_C0 * (1.0 + FRIC_REL_STD * rng.gauss(0.0, 1.0))
    b_v = B_V0 * (1.0 + FRIC_REL_STD * rng.gauss(0.0, 1.0))
    tau_c = max(1e-6, tau_c)
    b_v = max(1e-9, b_v)
    return tau_c, b_v


def omega_out(omega_in: float) -> float:
    return omega_in / N_RATIO


def power_in(tau_in: float, omega_in: float) -> float:
    return tau_in * omega_in


def arm_B_out(tau_in: float, omega_in: float, tau_c: float, b_v: float) -> tuple[float, float, float]:
    """Return (τ_out, η, heat_W) for load-independent Coulomb+viscous drag at output."""
    w_o = omega_out(omega_in)
    # Load-independent drag at output shaft (no τ_in in τ_loss)
    sign = 1.0 if w_o >= 0.0 else -1.0
    tau_loss = tau_c * sign + b_v * w_o
    tau_out = N_RATIO * tau_in - tau_loss
    p_in = power_in(tau_in, omega_in)
    p_out = tau_out * w_o
    eta = p_out / p_in if p_in > 0.0 else 0.0
    heat = tau_loss * abs(w_o)
    return tau_out, eta, heat


def arm_const_out(tau_in: float, omega_in: float, eta: float) -> tuple[float, float, float]:
    w_o = omega_out(omega_in)
    p_in = power_in(tau_in, omega_in)
    p_out = eta * p_in
    tau_out = p_out / w_o if abs(w_o) > 1e-15 else 0.0
    heat = (1.0 - eta) * p_in
    return tau_out, eta, heat


def fit_eta_heavy(tau_c: float, b_v: float) -> float:
    """Constant η from the single heavy-load truth point (C's only training point)."""
    op = OPS["heavy_load"]
    _, eta, _ = arm_B_out(op["tau_in"], op["omega_in"], tau_c, b_v)
    return eta


def metrics_for(regime: str, arm: str, seed: int) -> tuple[float, float, float, float, float]:
    """Return (eta, p_err_W, heat_W, tau_c, b_v). p_err is |P_out_arm − P_out_B|."""
    tau_c, b_v = shared_friction(seed)
    op = OPS[regime]
    tau_in, omega_in = op["tau_in"], op["omega_in"]
    # Truth B always evaluated with the shared friction
    tau_b, eta_b, heat_b = arm_B_out(tau_in, omega_in, tau_c, b_v)
    p_b = tau_b * omega_out(omega_in)
    if arm == "B_coulomb_viscous":
        return eta_b, 0.0, heat_b, tau_c, b_v
    if arm == "A_constant_eta":
        tau_a, eta_a, heat_a = arm_const_out(tau_in, omega_in, ETA0)
        p_a = tau_a * omega_out(omega_in)
        return eta_a, abs(p_a - p_b), heat_a, tau_c, b_v
    # C: η fitted on heavy only — blind to light-load η drop at fixed drag
    eta_fit = fit_eta_heavy(tau_c, b_v)
    tau_c_arm, eta_c, heat_c = arm_const_out(tau_in, omega_in, eta_fit)
    p_c = tau_c_arm * omega_out(omega_in)
    return eta_c, abs(p_c - p_b), heat_c, tau_c, b_v


def backdrive_threshold(tau_c: float, b_v: float, omega_crawl: float = 1.0) -> float:
    """Output torque to start back-driving at a crawl speed (static Coulomb + viscous)."""
    return abs(tau_c) + abs(b_v * omega_crawl)


def mean_sd(xs: list[float]) -> tuple[float, float]:
    n = len(xs)
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / (n - 1)
    return mu, math.sqrt(var)


def main() -> None:
    print(
        "Synthetic gear η-under-load toy; shared τ–ω / ratio / friction draws; "
        "not a gearbox dyno"
    )
    print(
        f"n={N_RATIO:.0f}:1 ETA0={ETA0} seeds={len(SEEDS)} "
        f"tau_c0={TAU_C0} b_v0={B_V0} (Coulomb+viscous at output)"
    )
    print(
        "model: B load-independent drag τ_loss=τ_c*sign(ω)+b_v*ω (no τ_in); τ_out=n*τ_in−τ_loss; "
        "A uses fixed η0; C fits η on heavy_load only; "
        "backdrive threshold = τ_c+|b_v|·ω_crawl (separate from forward η)"
    )
    print(
        "regime arm eta p_err_W heat_W (mean+-sd over seeds; "
        "p_err = |P_out_arm − P_out_B|)"
    )
    summary: dict[tuple[str, str], tuple[float, float, float]] = {}
    fric_check: dict[int, tuple[float, float]] = {}
    for regime in ("heavy_load", "light_load"):
        for arm in ARMS:
            etas, errs, heats = [], [], []
            for seed in SEEDS:
                eta, err, heat, tau_c, b_v = metrics_for(regime, arm, seed)
                etas.append(eta)
                errs.append(err)
                heats.append(heat)
                if arm == "A_constant_eta":
                    fric_check[seed] = (tau_c, b_v)
                else:
                    assert fric_check[seed] == (tau_c, b_v)
            me, se = mean_sd(etas)
            mr, sr = mean_sd(errs)
            mh, sh = mean_sd(heats)
            summary[(regime, arm)] = (me, mr, mh)
            print(
                f"{regime} {arm} {me:.4f}+-{se:.4f} "
                f"{mr:.4f}+-{sr:.4f} {mh:.4f}+-{sh:.4f}"
            )

    # Heavy: A should near-tie B on η / tiny p_err; C fitted so p_err≈0
    eta_a_h = summary[("heavy_load", "A_constant_eta")][0]
    eta_b_h = summary[("heavy_load", "B_coulomb_viscous")][0]
    err_a_h = summary[("heavy_load", "A_constant_eta")][1]
    err_c_h = summary[("heavy_load", "C_heavy_fit_eta")][1]
    err_a_l = summary[("light_load", "A_constant_eta")][1]
    err_c_l = summary[("light_load", "C_heavy_fit_eta")][1]
    print(
        f"heavy_load: |η_A − η_B| = {abs(eta_a_h - eta_b_h):.4f} "
        f"(near-tie / small gap on design point — A’s η0≈B’s drag-model η; "
        f"p_err_A={err_a_h:.4f} W)"
    )
    print(
        f"heavy_load: C_heavy_fit p_err = {err_c_h:.4e} W "
        f"(fitted on this point — matches B by construction)"
    )
    print(
        f"light_load: p_err_A = {err_a_l:.4f} W, p_err_C = {err_c_l:.4f} W "
        f"(constant η misses fixed-drag heat when P_in drops)"
    )
    # Backdrive literacy (same shared friction, seed 0)
    tc, bv = shared_friction(0)
    thr = backdrive_threshold(tc, bv)
    print(
        f"backdrive threshold (seed0) = {thr:.4f} N*m at output "
        f"(τ_c+|b_v|·1 rad/s; forward η does not equal backdrive η_b)"
    )
    print(
        "No winner declared: heavy-load design point makes constant η look fine; "
        "light load drops P_in against fixed drag so η falls; C’s fit does not transfer"
    )
    print(
        "Real gearbox / dyno lab: 本页未运行; Wikipedia Gear train numbers 以原文为准"
    )


if __name__ == "__main__":
    main()
