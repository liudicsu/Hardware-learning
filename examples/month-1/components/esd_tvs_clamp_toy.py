#!/usr/bin/env python3
"""Synthetic ESD / TVS clamp literacy toy. Stdlib only.

Shared HBM-style pulse (TI SSYA010A: 100 pF + 1500 ohm). Short-circuit peak
is about V/1500 ohm (~1.33 A at 2 kV). Arms share that source; protection
topology differs:

  A_unprotected  connector/IC pin are the same node; C_pin only (no clamp)
  B_tvs          TVS at the connector (= IC pin); clamp VBR + I*RDYN
  C_series_tvs   TVS at the connector, then series R, then an IC-pin node
                 with its own internal clamp (SSYA010-style primary/secondary)

Integration: backward Euler with DT=1 ps (clamp tau = RDYN*C_pin = 7.5 ps).
Window T_END >= 5*R_HBM*C_HBM. Most HBM energy dissipates in the 1500 ohm;
clamp energy is a small slice. Not an IEC 61000 certification.
ESD gun / real TVS lab: 本页未运行.
"""
from __future__ import annotations

import math
import random

# HBM network (SSYA010A)
C_HBM = 100e-12
R_HBM = 1500.0
V_HBM0 = 2000.0  # synthetic precharge; not a pass/fail claim
E_HBM0 = 0.5 * C_HBM * V_HBM0 * V_HBM0  # 200 uJ at nominal

# Synthetic clamp / pin (lesson values, not a datasheet part)
C_PIN = 5e-12
C_CONN = 5e-12  # connector node capacitance on arm C
R_SERIES = 33.0
VBR = 8.0  # synthetic breakdown / knee (SLVAE37 VBR)
RDYN = 1.5  # synthetic dynamic resistance (SLVAE37 RDYN)
# IC secondary clamp (arm C): same knee model, synthetic
VBR_IC = 8.0
RDYN_IC = 1.5

DT = 1e-12  # 1 ps; clamp tau = RDYN*C_PIN = 7.5 ps
T_END = 1.0e-6  # >= 5 * 150 ns HBM tau
SEEDS = (0, 1, 2, 3, 4)
JITTER = 0.08
ARMS = ("A_unprotected", "B_tvs", "C_series_tvs")


def _clamp_current(v: float, vbr: float, rdyn: float) -> float:
    if v > vbr:
        return (v - vbr) / rdyn
    return 0.0


def simulate(arm: str, v_hbm: float, dt: float = DT, t_end: float = T_END) -> dict:
    """Backward-Euler HBM discharge. Returns peak/energy metrics."""
    n = int(t_end / dt)
    v_c = v_hbm
    # connector / pin state
    v_conn = 0.0
    v_ic = 0.0
    e_tvs = 0.0
    e_ic = 0.0
    e_rhbm = 0.0
    peak_conn = 0.0
    peak_ic = 0.0
    peak_i_ic = 0.0
    peak_i_tvs = 0.0

    for _ in range(n):
        if arm == "A_unprotected":
            # Single node: pin = connector. No clamp.
            # BE: C_pin/dt*(v_new-v_old) = (v_c_new - v_new)/R_HBM
            #     C_hbm/dt*(v_c_new-v_c) = -(v_c_new - v_new)/R_HBM
            a11 = C_HBM / dt + 1.0 / R_HBM
            a12 = -1.0 / R_HBM
            a21 = -1.0 / R_HBM
            a22 = C_PIN / dt + 1.0 / R_HBM
            b1 = C_HBM / dt * v_c
            b2 = C_PIN / dt * v_conn
            det = a11 * a22 - a12 * a21
            v_c_new = (b1 * a22 - a12 * b2) / det
            v_new = (a11 * b2 - a21 * b1) / det
            i_in = (v_c_new - v_new) / R_HBM
            i_tvs = 0.0
            i_ic = 0.0
            v_conn = v_new
            v_ic = v_new
            v_c = v_c_new
        elif arm == "B_tvs":
            # Single node with TVS: i_tvs = max(0,(v-VBR)/RDYN)
            # Solve assuming clamp on, then fall back if v_new <= VBR.
            def solve(clamp_on: bool):
                g_c = C_HBM / dt
                g_p = C_PIN / dt
                g_r = 1.0 / R_HBM
                g_d = (1.0 / RDYN) if clamp_on else 0.0
                # g_c*(vc'-vc) = -(vc'-v)/R
                # g_p*(v'-v) = (vc'-v)/R - g_d*(v'-VBR)   [if clamp: i=(v'-VBR)/RDYN]
                # Rearrange:
                # (g_c+g_r) vc' - g_r v' = g_c vc
                # -g_r vc' + (g_p+g_r+g_d) v' = g_p v + g_d*VBR
                a11 = g_c + g_r
                a12 = -g_r
                a21 = -g_r
                a22 = g_p + g_r + g_d
                b1 = g_c * v_c
                b2 = g_p * v_conn + (g_d * VBR)
                det = a11 * a22 - a12 * a21
                vc = (b1 * a22 - a12 * b2) / det
                vv = (a11 * b2 - a21 * b1) / det
                return vc, vv

            v_c_new, v_new = solve(True)
            if v_new <= VBR:
                v_c_new, v_new = solve(False)
                i_tvs = 0.0
            else:
                i_tvs = (v_new - VBR) / RDYN
            i_in = (v_c_new - v_new) / R_HBM
            i_ic = 0.0  # no separate IC clamp; TVS is at the pin
            v_conn = v_new
            v_ic = v_new
            v_c = v_c_new
        else:
            # C: connector (TVS) -- R_SERIES -- ic_pin (IC clamp)
            # Three unknowns: vc, vconn, vic. Try both clamps on, then relax.
            def solve(tvs_on: bool, ic_on: bool):
                g_c = C_HBM / dt
                g_n = C_CONN / dt
                g_p = C_PIN / dt
                g_r = 1.0 / R_HBM
                g_s = 1.0 / R_SERIES
                g_t = (1.0 / RDYN) if tvs_on else 0.0
                g_i = (1.0 / RDYN_IC) if ic_on else 0.0
                # eqs:
                # (g_c+g_r) vc - g_r vconn = g_c v_c
                # -g_r vc + (g_n+g_r+g_s+g_t) vconn - g_s vic = g_n v_conn + g_t VBR
                # -g_s vconn + (g_p+g_s+g_i) vic = g_p v_ic + g_i VBR_IC
                a11, a12, a13 = g_c + g_r, -g_r, 0.0
                a21, a22, a23 = -g_r, g_n + g_r + g_s + g_t, -g_s
                a31, a32, a33 = 0.0, -g_s, g_p + g_s + g_i
                b1 = g_c * v_c
                b2 = g_n * v_conn + g_t * VBR
                b3 = g_p * v_ic + g_i * VBR_IC
                # 3x3 solve
                det = (
                    a11 * (a22 * a33 - a23 * a32)
                    - a12 * (a21 * a33 - a23 * a31)
                    + a13 * (a21 * a32 - a22 * a31)
                )
                vc = (
                    b1 * (a22 * a33 - a23 * a32)
                    - a12 * (b2 * a33 - a23 * b3)
                    + a13 * (b2 * a32 - a22 * b3)
                ) / det
                vn = (
                    a11 * (b2 * a33 - a23 * b3)
                    - b1 * (a21 * a33 - a23 * a31)
                    + a13 * (a21 * b3 - b2 * a31)
                ) / det
                vi = (
                    a11 * (a22 * b3 - b2 * a32)
                    - a12 * (a21 * b3 - b2 * a31)
                    + b1 * (a21 * a32 - a22 * a31)
                ) / det
                return vc, vn, vi

            tvs_on, ic_on = True, True
            v_c_new, v_conn_new, v_ic_new = solve(tvs_on, ic_on)
            if v_conn_new <= VBR:
                tvs_on = False
                v_c_new, v_conn_new, v_ic_new = solve(tvs_on, ic_on)
            if v_ic_new <= VBR_IC:
                ic_on = False
                v_c_new, v_conn_new, v_ic_new = solve(tvs_on, ic_on)
            i_tvs = _clamp_current(v_conn_new, VBR, RDYN) if tvs_on else 0.0
            i_ic = _clamp_current(v_ic_new, VBR_IC, RDYN_IC) if ic_on else 0.0
            i_in = (v_c_new - v_conn_new) / R_HBM
            v_c, v_conn, v_ic = v_c_new, v_conn_new, v_ic_new

        e_rhbm += i_in * i_in * R_HBM * dt
        e_tvs += i_tvs * v_conn * dt
        e_ic += i_ic * v_ic * dt
        peak_conn = max(peak_conn, v_conn)
        peak_ic = max(peak_ic, v_ic)
        peak_i_tvs = max(peak_i_tvs, i_tvs)
        peak_i_ic = max(peak_i_ic, i_ic)

    return {
        "peak_conn_V": peak_conn,
        "peak_ic_V": peak_ic,
        "peak_i_tvs_A": peak_i_tvs,
        "peak_i_ic_A": peak_i_ic,
        "e_tvs_J": e_tvs,
        "e_ic_J": e_ic,
        "e_rhbm_J": e_rhbm,
        "e_stored_J": 0.5 * C_HBM * v_hbm * v_hbm,
        "v_hbm_final": v_c,
    }


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    i_sc = V_HBM0 / R_HBM
    print(
        "Synthetic ESD/TVS clamp toy; shared HBM-style pulse; not an IEC certification"
    )
    print(
        f"HBM C={C_HBM*1e12:.0f}pF R={R_HBM:.0f}ohm V0={V_HBM0:.0f}V "
        f"E0={E_HBM0*1e6:.1f}uJ Isc≈{i_sc:.3f}A (SSYA010A); "
        f"VBR={VBR:.1f}V RDYN={RDYN:.1f}ohm (SLVAE37 VCLAMP=VBR+I*RDYN); "
        f"Rseries={R_SERIES:.0f}ohm DT={DT*1e12:.1f}ps T_end={T_END*1e6:.1f}us "
        f"(>=5*tau_HBM) seeds={len(SEEDS)} charge_jitter=±{JITTER:.0%}"
    )
    print(
        "arm peak_conn_V peak_ic_V peak_i_tvs_A peak_i_ic_A "
        "e_tvs_uJ e_ic_uJ e_rhbm_uJ (mean+-sd over seeds)"
    )
    for arm in ARMS:
        cols_acc = [[] for _ in range(7)]
        for seed in SEEDS:
            rng = random.Random(30_000 + seed)
            v0 = V_HBM0 * (1.0 + rng.uniform(-JITTER, JITTER))
            r = simulate(arm, v0)
            vals = [
                r["peak_conn_V"],
                r["peak_ic_V"],
                r["peak_i_tvs_A"],
                r["peak_i_ic_A"],
                r["e_tvs_J"] * 1e6,
                r["e_ic_J"] * 1e6,
                r["e_rhbm_J"] * 1e6,
            ]
            for i, v in enumerate(vals):
                cols_acc[i].append(v)
        print(
            f"{arm} "
            + " ".join(f"{mean_sd(c)[0]:.4f}+-{mean_sd(c)[1]:.4f}" for c in cols_acc)
        )
    print(
        "Energy note: most of the HBM 1/2 C V^2 is dissipated in the 1500 ohm; "
        "TVS/IC clamp energies are a small slice (~uJ)"
    )
    print(
        "No winner declared: unprotected vs TVS vs series+IC-clamp trade peak "
        "and clamp current; not an IEC result"
    )
    print("ESD gun / real TVS / IEC 61000 lab: 本页未运行; TI numbers 以原文为准")


if __name__ == "__main__":
    main()
