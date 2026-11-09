#!/usr/bin/env python3
"""Synthetic Nyquist / aliasing toy: sample shared tones, read the spectrum. Stdlib only.

Ideal impulse sampling of a sum of sinusoids over a 1 s window, then a plain DFT
(1 Hz bins). Tones sit on integer Hz, so a tone below fs/2 lands on one bin with
no leakage; a tone above fs/2 lands on its alias bin |f - k fs|.

Arms (one shared signal per trial):
  A_low     fs = FS_LOW = 50 Hz, no prefilter (below 2B in every regime except slow_tone)
  B_aaf     fs = FS_HIGH (above 2B) with an analog anti-alias prefilter before sampling:
            4th-order Butterworth magnitude |H(f)| = 1 / sqrt(1 + (f / FC)^8), FC = 0.25 fs,
            applied to each tone's amplitude (steady state; phase delay not modelled,
            the metrics are spectral magnitudes)
  C_raw     fs = FS_HIGH, no prefilter

slow_tone was added after the first run (the other regimes and every parameter are unchanged).

Common random numbers: per seed and trial the tone frequencies, amplitudes, phases
and the ADC noise sequence (sd 0.01, added after the prefilter, drawn once at the
longest record and truncated) are shared by every arm. No integration step: the
signal is evaluated in closed form at each sample instant.

Metrics per trial, averaged over TRIALS per seed: freq_err = |strongest DFT peak -
wanted tone| in Hz; false_peaks = bins above THRESH that are not the wanted tone
(+-1 bin); amp_err = |amplitude at the strongest peak - wanted amplitude| in %.
Safe sampling: fs > 2B and no tone above fs/2 left above THRESH after the declared
prefilter. Labels: tie = identical on every seed; numerically zero = |paired mean|
and sd both < 1e-9 (effectively a tie, no sign count); |m| <= sd = near-tie;
|m| > sd = consistent gap (small if |m| < 20 % of the smaller arm mean, else clear),
with a sign count. Real scope / ADC: 本页未运行. Wikipedia definitions: 以原文为准.
"""
import cmath
import math
import random

SEEDS = (0, 1, 2, 3, 4)
TRIALS = 8
FS_LOW, FS_HIGH = 50, 200  # Hz, 1 s records -> 1 Hz DFT bins
FC_RATIO = 0.25  # prefilter corner FC = FC_RATIO * fs
ORDER = 4
THRESH = 0.05  # peak threshold (amplitude units; full-scale tone = 1)
NOISE = 0.01
NUM_ZERO = 1e-9
ARMS = ("A_low", "B_aaf", "C_raw")
# name: wanted tone range (Hz), wanted amplitude range, interferer range (Hz) or None, interferer amplitude
REGIMES = {
    "slow_tone": ((2, 8), (0.5, 1.0), None, 0.0),
    "single_tone": ((35, 45), (0.5, 1.0), None, 0.0),
    "interferer": ((10, 30), (0.5, 1.0), (120, 180), 0.5),
    "near_edge": ((70, 90), (0.5, 1.0), None, 0.0),
}
ARM_FS = {"A_low": FS_LOW, "B_aaf": FS_HIGH, "C_raw": FS_HIGH}


def prefilter(f, fs):
    return 1.0 / math.sqrt(1.0 + (f / (FC_RATIO * fs)) ** (2 * ORDER))


def alias(f, fs):
    """Apparent frequency of a real tone f after sampling at fs (folding about fs/2)."""
    r = f % fs
    return min(r, fs - r)


def shared_trial(regime, seed, trial):
    """Common random numbers: one signal + one noise record per (regime, seed, trial)."""
    (lo, hi), (alo, ahi), intr, iamp = REGIMES[regime]
    rng = random.Random(f"{regime}-{seed}-{trial}")
    tones = [(rng.randint(lo, hi), rng.uniform(alo, ahi), rng.uniform(0.0, 2 * math.pi))]
    if intr:
        tones.append((rng.randint(*intr), iamp, rng.uniform(0.0, 2 * math.pi)))
    noise = [rng.gauss(0.0, NOISE) for _ in range(FS_HIGH)]
    return tones, noise


def sample(arm, tones, noise):
    fs = ARM_FS[arm]
    gains = [prefilter(f, fs) if arm == "B_aaf" else 1.0 for f, _, _ in tones]
    return [sum(g * a * math.sin(2 * math.pi * f * n / fs + p) for g, (f, a, p) in zip(gains, tones)) + noise[n]
            for n in range(fs)]


def spectrum(x):
    """One-sided amplitude spectrum, bins 1..N/2-1 (1 Hz apart for a 1 s record)."""
    n = len(x)
    return {k: 2.0 / n * abs(sum(v * cmath.exp(-2j * math.pi * k * i / n) for i, v in enumerate(x)))
            for k in range(1, n // 2)}


def trial_metrics(arm, tones, noise):
    spec = spectrum(sample(arm, tones, noise))
    f0, a0, _ = tones[0]
    peak = max(spec, key=lambda k: (spec[k], -k))
    false = sum(1 for k, v in spec.items() if v > THRESH and abs(k - f0) > 1)
    return {"freq": float(abs(peak - f0)), "false": float(false), "amp": 100.0 * abs(spec[peak] - a0) / a0}


def safe(arm, tones):
    fs = ARM_FS[arm]
    g = (lambda f: prefilter(f, fs)) if arm == "B_aaf" else (lambda f: 1.0)
    left = [f for f, a, _ in tones if f >= fs / 2 and g(f) * a > THRESH]
    return fs > 2 * tones[0][0] and not left


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-5:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs, m):
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def verdict(xa, xb):
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


def main():
    print("Synthetic sampling toy; ideal impulse sampling + plain DFT; shared tones / phases / ADC noise; not a real ADC")
    print(f"seeds={len(SEEDS)} trials={TRIALS} record=1 s fs_low={FS_LOW} Hz fs_high={FS_HIGH} Hz "
          f"prefilter Butterworth order {ORDER} FC={FC_RATIO} fs threshold={THRESH} noise sd={NOISE}; no time step (closed-form samples)")
    print(f"folding check: fs=100 Hz, tone 49 Hz -> {alias(49, 100)} Hz, tone 51 Hz -> {alias(51, 100)} Hz, "
          f"tone 150 Hz -> {alias(150, 100)} Hz; fs=200 Hz, tone 150 Hz -> {alias(150, 200)} Hz")
    print(f"prefilter gain at fs=200 Hz: 30 Hz {prefilter(30, 200):.4f}, 45 Hz {prefilter(45, 200):.4f}, "
          f"80 Hz {prefilter(80, 200):.4f}, 120 Hz {prefilter(120, 200):.4f}, 180 Hz {prefilter(180, 200):.4f}")
    print("regime arm freq_err_Hz false_peaks amp_err_%  safe_trials  (mean+-sd over seeds of per-seed trial means)")
    for regime in REGIMES:
        (lo, hi), _, intr, iamp = REGIMES[regime]
        print(f"{regime} (wanted {lo}..{hi} Hz" + (f", interferer {intr[0]}..{intr[1]} Hz amp {iamp}" if intr else "") + ")")
        res = {a: [] for a in ARMS}
        nsafe = {a: 0 for a in ARMS}
        for seed in SEEDS:
            per = {a: [] for a in ARMS}
            for trial in range(TRIALS):
                tones, noise = shared_trial(regime, seed, trial)
                for a in ARMS:
                    per[a].append(trial_metrics(a, tones, noise))
                    nsafe[a] += safe(a, tones)
            for a in ARMS:
                res[a].append({k: sum(t[k] for t in per[a]) / TRIALS for k in ("freq", "false", "amp")})
        for a in ARMS:
            cells = " ".join("{}+-{}".format(*map(num, mean_sd([r[k] for r in res[a]]))) for k in ("freq", "false", "amp"))
            print(f"  {a} fs={ARM_FS[a]} {cells}  safe {nsafe[a]}/{len(SEEDS) * TRIALS}")
        for x, y in (("A_low", "B_aaf"), ("C_raw", "B_aaf")):
            for k in ("freq", "false", "amp"):
                print(f"  paired {x[0]}-{y[0]} {k}: {verdict([r[k] for r in res[x]], [r[k] for r in res[y]])}")
    print("slow_tone: 50 Hz is already above 2B, so the low rate reads the tone as well as the high one")
    print("single_tone: below 2B the tone folds to fs - f; above 2B the prefilter costs passband droop at 35..45 Hz")
    print("interferer: without a prefilter the 120..180 Hz tone folds into 20..80 Hz and reads as a real peak")
    print("near_edge: a corner at 0.25 fs eats a 70..90 Hz wanted tone; fs > 2B is not enough with a real filter")
    print("No winner declared: an anti-alias filter needs fs well above 2B so its corner clears the band you want")
    print("Real scope / ADC: 本页未运行; Wikipedia definitions 以原文为准")


if __name__ == "__main__":
    main()
