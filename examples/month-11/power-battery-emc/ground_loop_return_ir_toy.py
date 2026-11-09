#!/usr/bin/env python3
"""Synthetic shared-return ground-loop IR toy. Stdlib only.

Shared motor pulse current waveform and shared resistance map for every arm
(TI SLYT512: large return loops / star-ground joining). Arms differ only in
how the sense/ADC reference returns to the supply entry:
  A_shared_return   motor return shares the sense ground conductor (loop IR)
  B_star            star/single-point at supply entry (sense return separate)
  C_star_kelvin     star + kelvin sense pair (sense wires carry negligible I)

Metrics: peak sense-node bounce (mV), false ADC counts (10-bit, 5 V, LSB).
≥5 seeds with pulse-amplitude jitter. Not an EMC chamber certification.
Chassis wiring 本页未运行.
"""
from __future__ import annotations

import math
import random

# Shared resistance map (synthetic lesson ohms, not a chassis measurement)
R_MOTOR_FEED = 0.020
R_SHARED_RETURN = 0.045  # shared segment used by A
R_STAR_RETURN = 0.008  # short star return at entry
R_SENSE_LEAD = 0.120  # sense wire (kelvin: current ~0)
# Shared motor current pulse (A), triangular-ish burst
I_PEAK0 = 8.0
PULSE_SAMPLES = 40
SEEDS = (0, 1, 2, 3, 4)
JITTER = 0.10
VREF = 5.0
N_BITS = 10
LSB = VREF / (1 << N_BITS)
ARMS = ("A_shared_return", "B_star", "C_star_kelvin")


def pulse(i_peak: float) -> list[float]:
    """Deterministic shared shape: rise, hold, fall."""
    rise, hold, fall = 8, 16, 16
    assert rise + hold + fall == PULSE_SAMPLES
    out = []
    for k in range(rise):
        out.append(i_peak * (k + 1) / rise)
    out.extend([i_peak] * hold)
    for k in range(fall):
        out.append(i_peak * (fall - k) / fall)
    return out


def run(arm: str, i_peak: float) -> tuple[float, float, int]:
    """Return peak |bounce| V, mean |bounce| V, false ADC counts over pulse."""
    i_wave = pulse(i_peak)
    peaks = []
    false = 0
    # Ideal sense voltage is mid-rail stub; bounce adds series IR on the return
    v_true = 2.5
    for i in i_wave:
        if arm == "A_shared_return":
            # motor current through shared return; sense references that node
            v_bounce = i * R_SHARED_RETURN
        elif arm == "B_star":
            # motor return goes to star; sense still shares a tiny star impedance
            v_bounce = i * R_STAR_RETURN
        else:
            # kelvin: sense pair carries ~0 motor current
            v_bounce = i * 0.0 + (0.001 * i * R_SENSE_LEAD)  # residual coupling, tiny
        peaks.append(abs(v_bounce))
        v_sense = v_true + v_bounce
        code = int(min(max(v_sense / LSB, 0), (1 << N_BITS) - 1))
        true_code = int(v_true / LSB)
        if code != true_code:
            false += 1
    peak = max(peaks)
    mean = sum(peaks) / len(peaks)
    return peak, mean, false


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    print(
        "Synthetic ground-loop return IR toy; shared motor pulses + R map; "
        "not an EMC certification"
    )
    print(
        f"R_shared={R_SHARED_RETURN*1e3:.1f}mohm R_star={R_STAR_RETURN*1e3:.1f}mohm "
        f"I_peak0={I_PEAK0:.1f}A samples={PULSE_SAMPLES} "
        f"ADC {N_BITS}-bit Vref={VREF:.1f}V LSB={LSB*1e3:.4f}mV "
        f"seeds={len(SEEDS)} amp_jitter=±{JITTER:.0%}"
    )
    print(
        "arm peak_bounce_mV mean_bounce_mV false_adc_counts "
        "(mean+-sd over seeds)"
    )
    for arm in ARMS:
        peaks, means, falses = [], [], []
        for seed in SEEDS:
            rng = random.Random(40_000 + seed)
            ip = I_PEAK0 * (1.0 + rng.uniform(-JITTER, JITTER))
            peak, mean, false = run(arm, ip)
            peaks.append(peak * 1e3)
            means.append(mean * 1e3)
            falses.append(float(false))
        cols = [mean_sd(peaks), mean_sd(means), mean_sd(falses)]
        print(f"{arm} " + " ".join(f"{m:.4f}+-{s:.4f}" for m, s in cols))
    print(
        "No winner declared beyond the defined metric: star shrinks IR bounce; "
        "kelvin removes sense-lead drop; shared return couples motor I into ADC"
    )
    print("Chassis wiring / scope-on-a-loop: 本页未运行; TI SLYT512 以原文为准")


if __name__ == "__main__":
    main()
