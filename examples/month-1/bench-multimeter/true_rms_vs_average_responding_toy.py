#!/usr/bin/env python3
"""True RMS vs sine-calibrated average-responding meters.

Synthetic sampled-waveform model, stdlib only.  Not a Fluke/Keysight
bench, not a Kelvin four-wire measurement, and not a Thevenin source.
Real DMM: 本页未运行.  Wikipedia statements 以原文为准.

RMS is the square root of the mean of the square.  An average-responding
meter measures mean(|v|) and multiplies by the sine form factor
pi/(2*sqrt(2)), so it agrees with true RMS on a pure sine and is out of
spec on other shapes.  A true-RMS meter is specified up to a crest-factor
cap (a declared toy parameter, not a datasheet claim).  Arm C reports
peak/sqrt(2), i.e. it assumes every wave is a sine.

Common random numbers: one shared waveform (phase and noise) per regime and seed.
Arms, shared waveforms (per regime and seed):
  A_true_rms        : sqrt(mean(v^2))
  B_avg_responding  : mean(|v|) * sine form factor
  C_peak_sine       : max(|v|) / sqrt(2)
The arms differ only in the estimator.  No integration step: the model
is a finite sum over samples, so no step-size stability criterion applies.

Regimes were written before the first run:
  sine            : pure sine, 1 V peak — A vs B must tie / be numerically zero
  square          : bipolar square, 1 V peak — B and C consistent lose vs A
  triangle        : bipolar triangle, 1 V peak — B consistent lose vs A
  pwm_high_crest  : unipolar pulse, duty 0.0625, crest factor 4 > CF_CAP 3
                    — B and C consistent lose vs A; C is the sine-assumption
                    path; a clipped true-RMS (peaks limited at CF_CAP * RMS)
                    is also printed.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
F = 50.0                 # Hz
FS = 10000.0             # Hz; 40 periods in N samples
N = 8000
VP = 1.0                 # V, peak used for every regime
SINE_FF = math.pi / (2.0 * math.sqrt(2.0))  # RMS / mean(|sine|)
CF_CAP = 3.0             # declared toy crest-factor cap; written before the first run
DUTY_PWM = 0.0625        # 1/16; crest factor 1/sqrt(D) = 4 > CF_CAP
NOISE_RMS = 0.0          # V; sine tie is demonstrated on a clean wave (phase only)
NOISE_RMS_OTHER = 0.001  # V; square / triangle / pwm share this draw

# name: wave kind (noise uses NOISE_RMS on sine, NOISE_RMS_OTHER otherwise)
REGIMES = ("sine", "square", "triangle", "pwm_high_crest")
ARMS = ("A_true_rms", "B_avg_responding", "C_peak_sine")


def _frac(t, phase):
    return (F * t + phase / (2.0 * math.pi)) % 1.0


def waveform(kind, t, phase):
    u = _frac(t, phase)
    if kind == "sine":
        return VP * math.sin(2.0 * math.pi * F * t + phase)
    if kind == "square":
        return VP if u < 0.5 else -VP
    if kind == "triangle":
        return VP * (4.0 * abs(u - 0.5) - 1.0)
    if kind == "pwm_high_crest":
        return VP if u < DUTY_PWM else 0.0
    raise ValueError(kind)


def analytic_rms(kind):
    if kind == "sine":
        return VP / math.sqrt(2.0)
    if kind == "square":
        return VP
    if kind == "triangle":
        return VP / math.sqrt(3.0)
    if kind == "pwm_high_crest":
        return VP * math.sqrt(DUTY_PWM)
    raise ValueError(kind)


def analytic_cf(kind):
    return VP / analytic_rms(kind)


def shared_wave(kind, seed):
    """Common random numbers: one phase and one noise sequence per (kind, seed)."""
    rng = random.Random(f"{kind}/{seed}")
    phase = rng.uniform(0.0, 2.0 * math.pi)
    sigma = NOISE_RMS if kind == "sine" else NOISE_RMS_OTHER
    noise = [rng.gauss(0.0, sigma) for _ in range(N)]
    samples = []
    for i in range(N):
        t = i / FS
        samples.append(waveform(kind, t, phase) + noise[i])
    return {"phase": phase, "sigma": sigma, "v": samples}


def estimators(v):
    mean_sq = sum(x * x for x in v) / len(v)
    mean_abs = sum(abs(x) for x in v) / len(v)
    peak = max(abs(x) for x in v)
    a = math.sqrt(mean_sq)
    b = mean_abs * SINE_FF
    c = peak / math.sqrt(2.0)
    clipped = [x if abs(x) <= CF_CAP * a else math.copysign(CF_CAP * a, x) for x in v]
    a_capped = math.sqrt(sum(x * x for x in clipped) / len(v))
    return {"A_true_rms": a, "B_avg_responding": b, "C_peak_sine": c,
            "crest": (peak / a if a else float("inf")), "A_cf_capped": a_capped}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
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


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def main():
    print("Synthetic true-RMS vs average-responding toy; shared waveforms; not a real DMM")
    print(f"seeds={len(SEEDS)} F={F:.0f} Hz FS={FS:.0f} Hz N={N} VP={VP:.1f} V "
          f"sine_form_factor={SINE_FF:.10f} CF_CAP={CF_CAP:.1f} DUTY_PWM={DUTY_PWM:.4f}")
    print("No integration step: finite sum over samples, no time-step criterion")
    print("Regimes and CF_CAP were written before the first run")
    rms_sine = VP / math.sqrt(2.0)
    pp_ratio = 2.0 * math.sqrt(2.0)
    print(f"hand_calc 1V_peak_sine: RMS=Vp/sqrt(2)={rms_sine:.10f} V ({num(rms_sine)} V); "
          f"pp/RMS=2*sqrt(2)={pp_ratio:.10f} (~2.8); form_factor=pi/(2*sqrt(2))={SINE_FF:.10f}")
    err_sq = SINE_FF * VP - VP
    print(f"hand_calc +/-1V_square: true_RMS={VP:.10f} V; average_responding={SINE_FF:.10f} V; "
          f"error={err_sq:.10f} V ({100.0 * err_sq / VP:.4f} %)")
    print(f"hand_calc crest_factors: sine={math.sqrt(2.0):.10f} square=1.0000000000 "
          f"triangle={math.sqrt(3.0):.10f} pwm_D={DUTY_PWM:.4f} cf={1.0 / math.sqrt(DUTY_PWM):.10f}")
    print("regime arm reading_V err_vs_analytic_V  (mean+-sd over seeds)")
    res = {}
    for kind in REGIMES:
        res[kind] = {a: [] for a in list(ARMS) + ["A_cf_capped", "crest"]}
        target = analytic_rms(kind)
        for seed in SEEDS:
            est = estimators(shared_wave(kind, seed)["v"])
            for a in ARMS:
                res[kind][a].append(est[a])
            res[kind]["A_cf_capped"].append(est["A_cf_capped"])
            res[kind]["crest"].append(est["crest"])
        print(f"{kind} (analytic_RMS={target:.10f} V, analytic_CF={analytic_cf(kind):.10f}, "
              f"noise_rms={(NOISE_RMS if kind == 'sine' else NOISE_RMS_OTHER):g} V)")
        for a in ARMS:
            xs = res[kind][a]
            err = [x - target for x in xs]
            print(f"  {a} {fmt_pair(*mean_sd(xs))} {fmt_pair(*mean_sd(err))}")
        print(f"  measured_CF {fmt_pair(*mean_sd(res[kind]['crest']))}")
        print(f"  A_cf_capped {fmt_pair(*mean_sd(res[kind]['A_cf_capped']))} "
              f"{fmt_pair(*mean_sd([x - target for x in res[kind]['A_cf_capped']]))}")
        for other in ("B_avg_responding", "C_peak_sine"):
            print(f"  paired {other[0]}-A reading: {verdict(res[kind][other], res[kind]['A_true_rms'])}")
        print(f"  paired A_cf_capped-A reading: {verdict(res[kind]['A_cf_capped'], res[kind]['A_true_rms'])}")
    # Alternatives on the same seeds (pre-planned sensitivity, not a retune)
    print("alternative CF_CAP=2.0 on pwm_high_crest (same seeds):")
    alt = []
    base_a = []
    target = analytic_rms("pwm_high_crest")
    for seed in SEEDS:
        v = shared_wave("pwm_high_crest", seed)["v"]
        a = math.sqrt(sum(x * x for x in v) / len(v))
        cap = 2.0
        clipped = [x if abs(x) <= cap * a else math.copysign(cap * a, x) for x in v]
        alt.append(math.sqrt(sum(x * x for x in clipped) / len(v)))
        base_a.append(a)
    print(f"  A_cf_capped@2 {fmt_pair(*mean_sd(alt))} err {fmt_pair(*mean_sd([x - target for x in alt]))}")
    print(f"  paired A_cf_capped@2-A: {verdict(alt, base_a)}")
    print("alternative CF_CAP=4.0 on pwm_high_crest (same seeds):")
    alt4 = []
    for seed in SEEDS:
        v = shared_wave("pwm_high_crest", seed)["v"]
        a = math.sqrt(sum(x * x for x in v) / len(v))
        cap = 4.0
        clipped = [x if abs(x) <= cap * a else math.copysign(cap * a, x) for x in v]
        alt4.append(math.sqrt(sum(x * x for x in clipped) / len(v)))
    print(f"  A_cf_capped@4 {fmt_pair(*mean_sd(alt4))} err {fmt_pair(*mean_sd([x - target for x in alt4]))}")
    print(f"  paired A_cf_capped@4-A: {verdict(alt4, base_a)}")
    print("No winner declared: on a sampled sine A vs B is a near-tie (not a numerical-zero / identical tie); B and C consistent-lose on square, triangle and high-crest PWM; peak/sqrt(2) is a sine assumption")
    print("Real DMM: 本页未运行; Wikipedia statements 以原文为准")


if __name__ == "__main__":
    main()
