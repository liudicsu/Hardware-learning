#!/usr/bin/env python3
"""Synthetic ADC ENOB / front-end noise toy. Stdlib only.

Shared analog tone and shared sample aperture for every arm. Arms differ only
in front-end corruption before an ideal mid-riser n-bit quantizer:
  A_ideal       quantizer alone (quantization noise only)
  B_noise       same quantizer + additive front-end Gaussian noise
  C_distort     same noise + mild odd cubic nonlinearity

Metrics: SNR and SINAD from a coherent DFT tone bin, then
ENOB = (SINAD_dB - 1.76) / 6.02 (Wikipedia ENOB; TI SLAA013 ideal SNR
6.02n + 1.76 dB). Not a SAR datasheet measurement. Real ADC lab: 本页未运行.
"""
from __future__ import annotations

import cmath
import math
import random

N_BITS = 10
N_LEVELS = 1 << N_BITS
VREF = 5.0
LSB = VREF / N_LEVELS
FS_AMP = 0.95 * (VREF / 2.0)  # stay off the rails
N_SAMPLES = 1024
TONE_BIN = 17  # coherent: cycles = TONE_BIN over N_SAMPLES
NOISE_SIGMA = 3.5 * LSB  # front-end noise, synthetic
DISTORT_K3 = 0.045  # mild cubic on normalized swing, synthetic
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_ideal", "B_noise", "C_distort")


def ideal_snr_db(n: int) -> float:
    return 6.02 * n + 1.76


def quantize(v: float) -> float:
    """Ideal mid-riser midtread-style clip to [0, VREF], return reconstructed volts."""
    code = int(math.floor(v / LSB))
    if code < 0:
        code = 0
    elif code > N_LEVELS - 1:
        code = N_LEVELS - 1
    # reconstruct at code centre
    return (code + 0.5) * LSB


def tone_samples() -> list[float]:
    """Shared clean full-scale-ish sine centered at VREF/2."""
    mid = VREF / 2.0
    out = []
    for k in range(N_SAMPLES):
        phase = 2.0 * math.pi * TONE_BIN * k / N_SAMPLES
        out.append(mid + FS_AMP * math.sin(phase))
    return out


def apply_arm(clean: list[float], arm: str, seed: int) -> list[float]:
    rng = random.Random(10_000 + seed)
    mid = VREF / 2.0
    out = []
    for v in clean:
        x = v
        if arm in ("B_noise", "C_distort"):
            x = x + rng.gauss(0.0, NOISE_SIGMA)
        if arm == "C_distort":
            # odd cubic on swing about mid; shared coefficient, not a datasheet INL
            u = (x - mid) / (VREF / 2.0)
            x = mid + (VREF / 2.0) * (u + DISTORT_K3 * (u ** 3))
        out.append(quantize(x))
    return out


def dft_bin(xs: list[float], bin_k: int) -> complex:
    n = len(xs)
    acc = 0j
    for k, x in enumerate(xs):
        acc += x * cmath.exp(-2j * math.pi * bin_k * k / n)
    return acc


def snr_sinad(xs: list[float]) -> tuple[float, float]:
    """Return (SNR_dB, SINAD_dB) from coherent single-tone DFT."""
    n = len(xs)
    # remove DC
    mean = sum(xs) / n
    yc = [x - mean for x in xs]
    # positive bins 1 .. n/2-1; tone at TONE_BIN; image at n-TONE_BIN ignored as conjugate
    tone = dft_bin(yc, TONE_BIN)
    # power: |X|^2 for one-sided use 2*|X|^2/n^2 for sinusoid amplitude^2/2
    tone_p = 2.0 * (abs(tone) ** 2) / (n * n)
    # noise+distortion: all other bins except DC and Nyquist twin
    nd_p = 0.0
    noise_only_p = 0.0
    harmonics = {2 * TONE_BIN, 3 * TONE_BIN, 4 * TONE_BIN, 5 * TONE_BIN}
    harmonics = {h for h in harmonics if 0 < h < n // 2}
    for k in range(1, n // 2):
        if k == TONE_BIN:
            continue
        p = 2.0 * (abs(dft_bin(yc, k)) ** 2) / (n * n)
        nd_p += p
        if k not in harmonics:
            noise_only_p += p
    # floor guards
    snr = 10.0 * math.log10(tone_p / max(noise_only_p, 1e-30))
    sinad = 10.0 * math.log10(tone_p / max(nd_p, 1e-30))
    return snr, sinad


def enob(sinad_db: float) -> float:
    return (sinad_db - 1.76) / 6.02


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    clean = tone_samples()
    print(
        "Synthetic ADC ENOB toy; shared tone/aperture; not a datasheet SAR measurement"
    )
    print(
        f"n_bits={N_BITS} Vref={VREF:.1f}V LSB={LSB*1e3:.4f}mV N={N_SAMPLES} "
        f"tone_bin={TONE_BIN} fs_amp={FS_AMP:.4f}V "
        f"noise_sigma={NOISE_SIGMA/LSB:.2f}LSB distort_k3={DISTORT_K3} seeds={len(SEEDS)}"
    )
    print(
        f"ideal_SNR_formula={ideal_snr_db(N_BITS):.2f}dB "
        f"(TI SLAA013 / Wikipedia: 6.02n+1.76); ENOB=(SINAD-1.76)/6.02"
    )
    print("arm SNR_dB SINAD_dB ENOB_bits (mean+-sd over seeds)")
    for arm in ARMS:
        snrs, sinads, enobs = [], [], []
        for seed in SEEDS:
            xs = apply_arm(clean, arm, seed)
            snr, sinad = snr_sinad(xs)
            snrs.append(snr)
            sinads.append(sinad)
            enobs.append(enob(sinad))
        cols = [mean_sd(snrs), mean_sd(sinads), mean_sd(enobs)]
        print(
            f"{arm} "
            + " ".join(f"{m:.3f}+-{s:.3f}" for m, s in cols)
        )
    print(
        "No winner declared: noise and distortion trade differently; "
        "toy ENOB is not a measured chip rating"
    )
    print("Real ADC / scope / INA lab: 本页未运行; Wikipedia+TI numbers 以原文为准")


if __name__ == "__main__":
    main()
