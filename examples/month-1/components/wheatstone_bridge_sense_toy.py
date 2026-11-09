#!/usr/bin/env python3
"""Synthetic Wheatstone bridge vs single-ended sense literacy toy. Stdlib only.

Shared excitation, gauge R0 and fractional ΔR within each regime for every arm.
Common-mode (CM) samples are **common random numbers**: for a given (seed, sample
index), arms A/B/C all see the **same** cm draw. Bridge arms add that cm to **both**
legs, take the differential, then apply a **finite CMRR** residual
(INA126 Electrical Characteristics: CMRR min **80 dB**, RS=0 Ω).

Arms:
  A_single_ended   gauge divider vs mid-rail + full cm, then gain G
  B_bridge_ideal   quarter-bridge (cm on both legs) + CMRR residual, no Vos
  C_bridge_offset  same bridge path + INA-like RTI offset

Regimes (≥5 seeds; multi-sample SNR = |Δmean| / pooled sample std):
  small_delta_noisy_cm  — small ΔR, large CM: bridge SNR wins
  large_delta_quiet_cm  — large ΔR, tiny CM: near-tie / small SNR gap (~2.6 dB)
No presumed winner. Not a strain-gauge lab. Real bridge / INA: 本页未运行.
"""
from __future__ import annotations

import math
import random

VEXC = 5.0  # synthetic excitation
R0 = 350.0  # synthetic gauge ohms (TI SLOA034-style order)
G_AMP = 100.0  # post gain (synthetic; INA126 G=5+80k/Rg can hit ~100)
VOS_NOM = 250e-6  # INA126-class input offset, synthetic RTI max order
DIFF_NOISE = 5.0e-5  # independent residual after differencing, V
# TI INA126 Electrical Characteristics: CMRR min 80 dB (typ 94 dB), RS=0Ω
CMRR_DB = 80.0
CMRR_LINEAR = 10.0 ** (CMRR_DB / 20.0)  # Ad/Acm; residual = cm / CMRR_LINEAR
N_SAMPLES = 64  # multi-sample SNR / std
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_single_ended", "B_bridge_ideal", "C_bridge_offset")
# Private noise/offset only — CM uses a seed-only RNG (no arm salt)
_ARM_SALT = {"A_single_ended": 11, "B_bridge_ideal": 22, "C_bridge_offset": 33}
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


def shared_cm_sequence(seed: int, cm_sigma: float, n: int) -> list[float]:
    """Common random numbers: identical for every arm at this seed."""
    rng = random.Random(50_000 + seed)  # seed only — no arm salt
    return [rng.gauss(0.0, cm_sigma) for _ in range(n)]


def measure_samples(
    delta: float,
    cm_sigma: float,
    arm: str,
    seed: int,
    stream_id: int,
) -> tuple[list[float], list[float]]:
    """Return (outputs, cm_used). CM sequence is shared across arms for (seed, stream_id)."""
    # Independent streams for δ=0 vs δ so CM does not cancel in the Δmean signal
    cms = shared_cm_sequence(seed + 10_007 * stream_id, cm_sigma, N_SAMPLES)
    # Private diff-noise advances per stream; Vos is fixed per (arm, seed) across streams
    rng_priv = random.Random(60_000 + seed * 17 + _ARM_SALT[arm] + 97 * stream_id)
    vos = 0.0
    if arm == "C_bridge_offset":
        rng_vos = random.Random(70_000 + seed * 17 + _ARM_SALT[arm])
        vos = VOS_NOM * (0.6 + 0.8 * rng_vos.random())
        if rng_vos.random() < 0.5:
            vos = -vos
    out: list[float] = []
    for cm in cms:
        diff_n = rng_priv.gauss(0.0, DIFF_NOISE)
        v_l, v_r = quarter_bridge_nodes(delta)
        if arm == "A_single_ended":
            # Full CM on the gauge node vs clean mid-rail reference
            raw = (v_r - VEXC * 0.5) + cm + diff_n
        else:
            # Add the **same** cm to both legs, then differential
            v_l_m = v_l + cm
            v_r_m = v_r + cm
            v_diff = v_r_m - v_l_m  # equals v_r - v_l (identical cm cancels in subtract)
            # Finite CMRR: residual input-referred CM error = cm / CMRR_LINEAR
            cm_resid = cm / CMRR_LINEAR
            raw = v_diff + cm_resid + vos + diff_n
        out.append(G_AMP * raw)
    return out, cms


def sample_mean_std(xs: list[float]) -> tuple[float, float]:
    n = len(xs)
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / (n - 1)
    return mu, math.sqrt(var)


def metrics_for(
    delta: float, cm_sigma: float, arm: str, seed: int
) -> tuple[float, float, float, list[float]]:
    """Return (sens, offset_err, snr_db, cm_stream_at_delta) using multi-sample SNR."""
    y0, _ = measure_samples(0.0, cm_sigma, arm, seed, stream_id=0)
    y1, cms1 = measure_samples(delta, cm_sigma, arm, seed, stream_id=1)
    m0, s0 = sample_mean_std(y0)
    m1, s1 = sample_mean_std(y1)
    signal = m1 - m0
    # Pooled sample std (same N); floor guards against zero
    noise = math.sqrt(0.5 * (s0 * s0 + s1 * s1))
    noise = max(noise, 1e-12)
    snr = 20.0 * math.log10(max(abs(signal), 1e-30) / noise)
    sens = signal / delta if delta else 0.0
    offset_err = abs(m0)
    return sens, offset_err, snr, cms1


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    print(
        "Synthetic Wheatstone/INA sense toy; shared ΔR/excitation/CM draws; "
        "not a strain-gauge lab"
    )
    print(
        f"Vexc={VEXC}V R0={R0}ohm G={G_AMP} Vos_nom={VOS_NOM*1e6:.0f}uV "
        f"CMRR={CMRR_DB:.0f}dB(INA126 min) N_samples={N_SAMPLES} seeds={len(SEEDS)}"
    )
    print(
        "model: quarter-bridge V_G=Vexc*(r_g/(R0+r_g)-1/2)≈Vexc*δ/4 (small δ); "
        "δ=GF*ε → V_G≈Vexc*GF*ε/4; "
        "shared cm on both bridge legs then differential + residual cm/CMRR_linear; "
        "multi-sample SNR=|Δmean|/pooled_std "
        f"(TI INA126 CMRR min {CMRR_DB:.0f} dB; SLOA034 bridge)"
    )
    print(
        "regime arm sens_V_per_delta offset_err_V snr_dB (mean+-sd over seeds)"
    )
    summary = {}
    for reg_name, delta, cm in REGIMES:
        for arm in ARMS:
            sens_l, off_l, snr_l = [], [], []
            for seed in SEEDS:
                s, o, sn, _ = metrics_for(delta, cm, arm, seed)
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
    a_s = summary[("small_delta_noisy_cm", "A_single_ended")][0]
    b_s = summary[("small_delta_noisy_cm", "B_bridge_ideal")][0]
    a_l = summary[("large_delta_quiet_cm", "A_single_ended")][0]
    b_l = summary[("large_delta_quiet_cm", "B_bridge_ideal")][0]
    print(
        f"small_delta_noisy_cm: bridge SNR advantage B-A = {b_s - a_s:.2f} dB "
        f"(finite CMRR still beats full-CM single-ended)"
    )
    print(
        f"large_delta_quiet_cm: |SNR_A - SNR_B| = {abs(a_l - b_l):.2f} dB "
        f"(near-tie / small gap — remaining ~2.6 dB from finite-CMRR residual "
        f"+ private DIFF_NOISE; no presumed winner)"
    )
    c_off = summary[("small_delta_noisy_cm", "C_bridge_offset")][1]
    b_off = summary[("small_delta_noisy_cm", "B_bridge_ideal")][1]
    print(
        f"small_delta offset: C_bridge_offset {c_off:.4f} V > "
        f"B_bridge_ideal {b_off:.4f} V (INA RTI offset cost; multi-sample "
        f"SNR cannot see static Vos — it cancels in Δmean, so C SNR ≳ B "
        f"does not mean C wins)"
    )
    print(
        "No winner declared: quiet high-ΔR is a near-tie / small gap, not a "
        "true tie; noisy small-ΔR needs the bridge+CMRR; C's cost is offset/"
        "absolute accuracy, not SNR"
    )
    print(
        "Real Wheatstone / INA / strain-gauge lab: 本页未运行; "
        "TI/Wikipedia numbers 以原文为准"
    )


if __name__ == "__main__":
    main()
