#!/usr/bin/env python3
"""Synthetic ESD / TVS clamp literacy toy. Stdlib only.

Shared HBM-style pulse energy and shared rise for every arm (TI SSYA010A:
HBM uses 100 pF + 1500 ohm). Arms differ only in the protection path at the
pin node:
  A_unprotected   pin capacitance only (no clamp)
  B_tvs           TVS-like clamp to a rail window (SLVAE37: shunt + VCLAMP)
  C_series_tvs    series resistance + same TVS

Metrics: peak pin voltage, energy into clamp (0 for unprotected), residual
energy on the pin capacitance. ≥5 seeds with pulse-charge jitter.
Not an IEC 61000 certification. ESD gun / real TVS lab: 本页未运行.
"""
from __future__ import annotations

import math
import random

# HBM network (SSYA010A): 100 pF, 1500 ohm — cited, then used as the charge source
C_HBM = 100e-12
R_HBM = 1500.0
V_HBM0 = 2000.0  # synthetic precharge; not a pass/fail claim
# Pin / clamp model (synthetic lesson values, not a datasheet part)
C_PIN = 5e-12
R_SERIES = 33.0  # C arm only
V_CLAMP = 8.0  # synthetic VCLAMP window (above a 5 V rail)
R_CLAMP_ON = 1.5  # dynamic resistance while clamping (synthetic)
DT = 0.05e-9  # 50 ps
T_END = 80e-9
SEEDS = (0, 1, 2, 3, 4)
JITTER = 0.08  # ±8 % charge voltage jitter
ARMS = ("A_unprotected", "B_tvs", "C_series_tvs")


def simulate(arm: str, v_hbm: float) -> tuple[float, float, float]:
    """Return (peak_pin_V, clamp_energy_J, pin_resid_energy_J)."""
    n = int(T_END / DT)
    v_c = v_hbm  # HBM capacitor
    v_pin = 0.0
    e_clamp = 0.0
    peak = 0.0
    for _ in range(n):
        # series path into pin
        if arm == "A_unprotected":
            r_series = 0.0
            clamp_on = False
        elif arm == "B_tvs":
            r_series = 0.0
            clamp_on = abs(v_pin) > V_CLAMP
        else:
            r_series = R_SERIES
            clamp_on = abs(v_pin) > V_CLAMP

        # Current from HBM cap through R_HBM (+ optional series) into pin
        r_path = R_HBM + r_series
        i_in = (v_c - v_pin) / r_path
        # Clamp current to ground once above VCLAMP (unidirectional positive model)
        i_clamp = 0.0
        if clamp_on and v_pin > V_CLAMP:
            i_clamp = (v_pin - V_CLAMP) / R_CLAMP_ON
        # Capacitor updates
        dv_c = -i_in * DT / C_HBM
        dv_pin = (i_in - i_clamp) * DT / C_PIN
        v_c += dv_c
        v_pin += dv_pin
        if v_pin < 0:
            v_pin = 0.0
        peak = max(peak, v_pin)
        e_clamp += i_clamp * v_pin * DT
    e_pin = 0.5 * C_PIN * v_pin * v_pin
    return peak, e_clamp, e_pin


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    print(
        "Synthetic ESD/TVS clamp toy; shared HBM-style pulse; not an IEC certification"
    )
    print(
        f"HBM C={C_HBM*1e12:.0f}pF R={R_HBM:.0f}ohm V0={V_HBM0:.0f}V "
        f"(SSYA010A network); C_pin={C_PIN*1e12:.1f}pF "
        f"VCLAMP={V_CLAMP:.1f}V Rseries={R_SERIES:.0f}ohm seeds={len(SEEDS)} "
        f"charge_jitter=±{JITTER:.0%}"
    )
    print(
        "arm peak_pin_V clamp_energy_nJ pin_resid_energy_nJ (mean+-sd over seeds)"
    )
    for arm in ARMS:
        peaks, eclamps, epins = [], [], []
        for seed in SEEDS:
            rng = random.Random(30_000 + seed)
            v0 = V_HBM0 * (1.0 + rng.uniform(-JITTER, JITTER))
            peak, e_c, e_p = simulate(arm, v0)
            peaks.append(peak)
            eclamps.append(e_c * 1e9)
            epins.append(e_p * 1e9)
        cols = [mean_sd(peaks), mean_sd(eclamps), mean_sd(epins)]
        print(f"{arm} " + " ".join(f"{m:.4f}+-{s:.4f}" for m, s in cols))
    print(
        "No winner declared: clamp trades pin peak for clamp energy; "
        "series R further softens the edge"
    )
    print("ESD gun / real TVS / IEC 61000 lab: 本页未运行; TI numbers 以原文为准")


if __name__ == "__main__":
    main()
