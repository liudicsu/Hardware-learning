#!/usr/bin/env python3
"""Synthetic Wheatstone bridge vs single-ended sense literacy toy. Stdlib only.

Shared excitation, gauge R0 and fractional ΔR within each regime for every arm.
Arms differ only in how the same resistors are read:
  A_single_ended   one active divider vs mid-rail reference, then gain G
  B_bridge_ideal   quarter-bridge differential V_G then ideal gain G
  C_bridge_offset  same bridge + input-referred offset (INA-like) then G

Regimes (shared ΔR + CM schedule per regime; ≥5 seeds):
  small_delta_noisy_cm  — small ΔR, large CM: bridge SNR wins
  large_delta_quiet_cm  — large ΔR, tiny CM: single-ended SNR ties ideal bridge
No presumed winner across regimes. Not a strain-gauge lab.
Real bridge / INA hardware: 本页未运行.
"""
from __future__ import annotations

import math
import random

VEXC = 5.0  # synthetic excitation
R0 = 350.0  # synthetic gauge ohms (TI SLOA034-style order)
G_AMP = 100.0  # post gain (synthetic; INA126 G=5+80k/Rg can hit ~100)
VOS_NOM = 250e-6  # INA126-class input offset, synthetic RTI max order
DIFF_NOISE = 5.0e-5  # independent residual after differencing, V
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_single_ended", "B_bridge_ideal", "C_bridge_offset")
_ARM_SALT = {"A_single_ended": 11, "B_bridge_ideal": 22, "C_bridge_offset": 33}
# (name, delta, cm_noise_V) — CM is part of the shared regime schedule
REGIMES = (
    ("small_delta_noisy_cm", 0.002, 2.0e-3),
    ("large_delta_quiet_cm", 0.20, 4.0e-5),
)


def quarter_bridge_nodes(delta: float) -> tuple[float, float]:
    """Left mid (fixed R0/R0) and right mid (R0 over R0*(1+delta))."""
    v_left = VEXC * 0.5
    r_g = R0 * (1.0 + delta)
    v_right = VEXC * r_g / (R0 + r_g)
    return v_left, v_right


def v_bridge(delta: float) -> float:
    v_l, v_r = quarter_bridge_nodes(delta)
    return v_r - v_l


def v_single_ended(delta: float) -> float:
    _, v_r = quarter_bridge_nodes(delta)
    return v_r - VEXC * 0.5


def apply_arm(delta: float, cm_sigma: float, arm: str, seed: int) -> float:
    rng = random.Random(30_000 + seed * 17 + _ARM_SALT[arm])
    cm = rng.gauss(0.0, cm_sigma)
    diff_n = rng.gauss(0.0, DIFF_NOISE)
    if arm == "A_single_ended":
        raw = v_single_ended(delta) + cm + diff_n
        return G_AMP * raw
    if arm == "B_bridge_ideal":
        raw = v_bridge(delta) + diff_n  # shared CM cancels differentially
        return G_AMP * raw
    if arm == "C_bridge_offset":
        vos = VOS_NOM * (0.6 + 0.8 * rng.random())
        if rng.random() < 0.5:
            vos = -vos
        raw = v_bridge(delta) + vos + diff_n
        return G_AMP * raw
    raise ValueError(arm)


def metrics_for(
    delta: float, cm_sigma: float, arm: str, seed: int
) -> tuple[float, float, float]:
    y0 = apply_arm(0.0, cm_sigma, arm, seed)
    y1 = apply_arm(delta, cm_sigma, arm, seed)
    signal = y1 - y0
    offset_err = abs(y0)
    if arm == "A_single_ended":
        noise_floor = max(abs(y0), G_AMP * cm_sigma * 0.5, G_AMP * DIFF_NOISE)
    else:
        noise_floor = max(G_AMP * DIFF_NOISE, abs(y0) * 0.25 + G_AMP * DIFF_NOISE)
    snr = 20.0 * math.log10(max(abs(signal), 1e-30) / max(noise_floor, 1e-30))
    sens = signal / delta if delta else 0.0
    return sens, offset_err, snr


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    print(
        "Synthetic Wheatstone/INA sense toy; shared ΔR/excitation; not a strain-gauge lab"
    )
    print(
        f"Vexc={VEXC}V R0={R0}ohm G={G_AMP} Vos_nom={VOS_NOM*1e6:.0f}uV "
        f"seeds={len(SEEDS)}"
    )
    print(
        "model: quarter-bridge V_G=Vexc*(r_g/(R0+r_g)-1/2); "
        "single-ended uses gauge divider vs mid-rail; "
        "C adds INA-like RTI offset (TI INA126 G=5+80k/Rg literacy; SLOA034 bridge)"
    )
    print(
        "regime arm sens_V_per_delta offset_err_V snr_dB (mean+-sd over seeds)"
    )
    summary = {}
    for reg_name, delta, cm in REGIMES:
        for arm in ARMS:
            sens_l, off_l, snr_l = [], [], []
            for seed in SEEDS:
                s, o, sn = metrics_for(delta, cm, arm, seed)
                sens_l.append(s)
                off_l.append(o)
                snr_l.append(sn)
            sm, ss = mean_sd(sens_l)
            om, os_ = mean_sd(off_l)
            nm, ns = mean_sd(snr_l)
            summary[(reg_name, arm)] = (nm, om)
            print(
                f"{reg_name} {arm} {sm:.4f}+-{ss:.4f} "
                f"{om:.4f}+-{os_:.4f} {nm:.4f}+-{ns:.4f}"
            )
    a_s, b_s = summary[("small_delta_noisy_cm", "A_single_ended")][0], summary[
        ("small_delta_noisy_cm", "B_bridge_ideal")
    ][0]
    a_l, b_l = summary[("large_delta_quiet_cm", "A_single_ended")][0], summary[
        ("large_delta_quiet_cm", "B_bridge_ideal")
    ][0]
    print(
        f"small_delta_noisy_cm: bridge SNR advantage B-A = {b_s - a_s:.2f} dB "
        f"(bridge wins on CM rejection)"
    )
    print(
        f"large_delta_quiet_cm: |SNR_A - SNR_B| = {abs(a_l - b_l):.2f} dB "
        f"(single-ended ties ideal bridge — CM tiny, no presumed winner)"
    )
    c_off = summary[("small_delta_noisy_cm", "C_bridge_offset")][1]
    b_off = summary[("small_delta_noisy_cm", "B_bridge_ideal")][1]
    print(
        f"small_delta offset: C_bridge_offset {c_off:.4f} V > "
        f"B_bridge_ideal {b_off:.4f} V (INA RTI offset cost)"
    )
    print(
        "No winner declared: quiet high-ΔR single-ended can match bridge SNR; "
        "noisy small-ΔR needs the bridge; C's offset is a real INA cost"
    )
    print(
        "Real Wheatstone / INA / strain-gauge lab: 本页未运行; "
        "TI/Wikipedia numbers 以原文为准"
    )


if __name__ == "__main__":
    main()
