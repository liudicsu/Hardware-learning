#!/usr/bin/env python3
"""Synthetic shared-return ground-loop IR toy. Stdlib only.

Shared motor pulse current waveform and shared resistance map for every arm
(TI SLYT512: large return loops / star-ground joining). Arms differ only in
how the sense/ADC reference returns to the supply entry:
  A_shared_return   motor return shares the sense ground conductor (loop IR)
  B_star            star/single-point at supply entry (sense return separate)
  C_star_kelvin     star + kelvin sense pair (sense wires carry ADC bias only)

Literacy: A vs B is V = I·R on the chosen return R (shared vs star), not a
chassis measurement. R_MOTOR_FEED drop is reported separately and does NOT
enter the sense bounce (feed IR ≠ return IR into the ADC). Kelvin residual is
physical I_ADC_BIAS × R_SENSE_LEAD (no fudge factor). L·di/dt is not modelled.

Metrics: peak sense-node bounce (mV), false ADC counts (10-bit, 5 V, LSB),
peak feed drop (mV, informational). ≥5 seeds with pulse-amplitude jitter.
Not an EMC chamber certification. Chassis wiring 本页未运行.
"""
from __future__ import annotations

import math
import random

# Shared resistance map (synthetic lesson ohms, not a chassis measurement)
R_MOTOR_FEED = 0.020  # feed-side IR; reported, not added to sense bounce
R_SHARED_RETURN = 0.045  # shared segment used by A
R_STAR_RETURN = 0.008  # short star return at entry
R_SENSE_LEAD = 0.120  # sense wire resistance
I_ADC_BIAS = 50e-6  # physical ADC/sense bias through kelvin leads (A)
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


def run(arm: str, i_peak: float) -> tuple[float, float, int, float]:
    """Return peak |bounce| V, mean |bounce| V, false ADC counts, peak feed drop V."""
    i_wave = pulse(i_peak)
    peaks = []
    false = 0
    feed_peaks = []
    # Ideal sense voltage is mid-rail stub; bounce adds series IR on the return
    v_true = 2.5
    for i in i_wave:
        # Feed-side drop is always I * R_MOTOR_FEED; never added to sense bounce.
        v_feed = i * R_MOTOR_FEED
        feed_peaks.append(abs(v_feed))
        if arm == "A_shared_return":
            # motor current through shared return; sense references that node
            v_bounce = i * R_SHARED_RETURN
        elif arm == "B_star":
            # motor return goes to star; sense still shares a tiny star impedance
            v_bounce = i * R_STAR_RETURN
        else:
            # kelvin: sense pair carries ADC bias only (physical I_bias * R_lead)
            v_bounce = I_ADC_BIAS * R_SENSE_LEAD
        peaks.append(abs(v_bounce))
        v_sense = v_true + v_bounce
        code = int(min(max(v_sense / LSB, 0), (1 << N_BITS) - 1))
        true_code = int(v_true / LSB)
        if code != true_code:
            false += 1
    peak = max(peaks)
    mean = sum(peaks) / len(peaks)
    return peak, mean, false, max(feed_peaks)


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
        f"R_feed={R_MOTOR_FEED*1e3:.1f}mohm (reported, not in bounce) "
        f"R_sense={R_SENSE_LEAD*1e3:.1f}mohm I_bias={I_ADC_BIAS*1e6:.0f}uA "
        f"I_peak0={I_PEAK0:.1f}A samples={PULSE_SAMPLES} "
        f"ADC {N_BITS}-bit Vref={VREF:.1f}V LSB={LSB*1e3:.4f}mV "
        f"seeds={len(SEEDS)} amp_jitter=±{JITTER:.0%}; "
        f"A vs B = V=I*R on chosen return R (literacy, not a measurement); "
        f"L*di/dt not modelled"
    )
    print(
        "arm peak_bounce_mV mean_bounce_mV false_adc_counts peak_feed_mV "
        "(mean+-sd over seeds)"
    )
    for arm in ARMS:
        peaks, means, falses, feeds = [], [], [], []
        for seed in SEEDS:
            rng = random.Random(40_000 + seed)
            ip = I_PEAK0 * (1.0 + rng.uniform(-JITTER, JITTER))
            peak, mean, false, feed = run(arm, ip)
            peaks.append(peak * 1e3)
            means.append(mean * 1e3)
            falses.append(float(false))
            feeds.append(feed * 1e3)
        cols = [mean_sd(peaks), mean_sd(means), mean_sd(falses), mean_sd(feeds)]
        print(f"{arm} " + " ".join(f"{m:.4f}+-{s:.4f}" for m, s in cols))
    print(
        "No winner declared beyond the defined metric: A vs B is literacy V=I*R "
        "on chosen R; kelvin residual is I_bias*R_sense; feed IR stays off the "
        "sense node; L*di/dt not modelled"
    )
    print("Chassis wiring / scope-on-a-loop: 本页未运行; TI SLYT512 以原文为准")


if __name__ == "__main__":
    main()
