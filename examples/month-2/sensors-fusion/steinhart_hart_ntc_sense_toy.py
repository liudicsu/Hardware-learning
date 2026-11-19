#!/usr/bin/env python3
"""Synthetic Steinhart-Hart NTC temperature-sensing toy.

Stdlib only. A shared true temperature list, a shared divider/ADC stand-in
and shared resistance noise are drawn once per (regime, seed) and then read
by every arm (common random numbers).

The true R(T) uses the inverse of 1/T = A + B ln R + C (ln R)^3 taken from
the Steinhart-Hart equation page, with A, B, C solved from three declared
(R, T) points on that same page's three-point formulae. That inverse is the
only R(T) used; the Thermistor page's rearranged inverse is not mixed in.

Arms:
  A_beta_local  — B-parameter model fitted only near 25 C
  B_sh_threepoint — Steinhart-Hart with coefficients from the three declared points
  C_adc_counts — raw ADC counts mapped through a local linear counts-to-C
                 line fitted only near 25 C (the narrow-range Steinhart-Hart
                 solve on this same three-parameter curve recovers the same
                 A, B, C and is printed only as an alternative)

Not a vendor curve, not a calibration bath, not an inrush-limiter plant, and
not a reading of an IMU temperature register. Wikipedia example coefficients
and the 0.02 C error claim are 以原文为准 and are not toy outputs.
Real thermistor / bath / IMU temperature register: 本页未运行.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared toy parameters (not datasheet values, not Wikipedia example coefficients).
K0 = 273.15
T0_C = 25.0
T0_K = T0_C + K0
# Three declared calibration points (R in ohm, T in C) used to solve A, B, C.
CAL_R = (25000.0, 10000.0, 1500.0)
CAL_C = (0.0, 25.0, 80.0)
# Narrow-range points for arm C, in C, clustered near T0_C.
NARROW_C = (24.0, 25.0, 26.0)
# Evaluation lists (C).
MID_C = (20.0, 22.0, 25.0, 28.0, 30.0)
WIDE_C = (0.0, 10.0, 25.0, 50.0, 80.0)
FAR_C = (-5.0, 0.0, 80.0, 90.0)
# Local B-parameter fit uses two temperatures near T0_C.
LOCAL_C = (24.0, 26.0)
VCC = 3.3
R_DIV = 10000.0
ADC_BITS = 12
ADC_COUNTS = 2 ** ADC_BITS - 1  # 4095
SIG_R = 40.0  # ohm, resistance noise, shared

METRICS = ("rmse_C",)
ARMS = ("A_beta_local", "B_sh_threepoint", "C_adc_counts")
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

# name: (temp list C, declared expectation); written before the first run
REGIMES = {
    "mid_range": (MID_C, "A and B may near-tie on rmse_C - keep"),
    "wide_span": (WIDE_C, "B consistently below A on rmse_C (linear-local beta loses on a wide span) - keep"),
    "out_of_range": (FAR_C, "C loses to B on rmse_C (raw ADC counts treated as temperature, far from the local counts-to-C line) - keep"),
}


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
        return format(Decimal(repr(x)), ".3e")
    s = format(Decimal(repr(x)), ".4f")
    return "0.0000" if s == "-0.0000" else s


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


def cbrt(z):
    return math.copysign(abs(z) ** (1.0 / 3.0), z)


def sh_solve(points):
    """A, B, C from three (R, T_kelvin) points, Steinhart-Hart equation page."""
    (R1, T1), (R2, T2), (R3, T3) = points
    L1, L2, L3 = math.log(R1), math.log(R2), math.log(R3)
    Y1, Y2, Y3 = 1.0 / T1, 1.0 / T2, 1.0 / T3
    g2 = (Y2 - Y1) / (L2 - L1)
    g3 = (Y3 - Y1) / (L3 - L1)
    C = ((g3 - g2) / (L3 - L2)) / (L1 + L2 + L3)
    B = g2 - C * (L1 ** 2 + L1 * L2 + L2 ** 2)
    A = Y1 - (B + L1 ** 2 * C) * L1
    return A, B, C


def sh_T_from_R(R, A, B, C):
    lr = math.log(R)
    return 1.0 / (A + B * lr + C * lr ** 3)


def sh_R_from_T(T, A, B, C):
    """Inverse R(T) from the Steinhart-Hart equation page only."""
    x = (1.0 / C) * (A - 1.0 / T)
    y = math.sqrt((B / (3.0 * C)) ** 3 + x ** 2 / 4.0)
    return math.exp(cbrt(y - x / 2.0) - cbrt(y + x / 2.0))


def beta_from_two(R1, T1, R2, T2):
    """B-parameter (kelvin) and R0, T0 from two points; T0 is T1."""
    Bbeta = math.log(R1 / R2) / (1.0 / T1 - 1.0 / T2)
    return Bbeta, R1, T1


def T_from_beta(R, Bbeta, R0, T0):
    return 1.0 / (1.0 / T0 + math.log(R / R0) / Bbeta)


def T_from_linear(R, k, R0, T0):
    return T0 + (R - R0) / k


CAL_POINTS = tuple((r, c + K0) for r, c in zip(CAL_R, CAL_C))
SH_A, SH_B, SH_C = sh_solve(CAL_POINTS)


def true_R(Tc):
    return sh_R_from_T(Tc + K0, SH_A, SH_B, SH_C)


# Narrow and local points are taken from the true inverse (declared, printed).
NARROW_POINTS = tuple((true_R(c), c + K0) for c in NARROW_C)
SH_A_N, SH_B_N, SH_C_N = sh_solve(NARROW_POINTS)
R_LOCAL = (true_R(LOCAL_C[0]), true_R(LOCAL_C[1]))
BBETA, R0_BETA, T0_BETA = beta_from_two(R_LOCAL[0], LOCAL_C[0] + K0, R_LOCAL[1], LOCAL_C[1] + K0)
K_LIN = (R_LOCAL[1] - R_LOCAL[0]) / ((LOCAL_C[1] + K0) - (LOCAL_C[0] + K0))
R0_LIN = true_R(T0_C)
T0_LIN = T0_K


def counts_of_R(R):
    v = VCC * R / (R + R_DIV)
    frac = min(max(v / VCC, 0.0), 1.0)
    counts = int(frac * ADC_COUNTS + 0.5)
    if counts <= 0:
        counts = 1
    if counts >= ADC_COUNTS:
        counts = ADC_COUNTS - 1
    return counts


C24 = counts_of_R(true_R(LOCAL_C[0]))
C26 = counts_of_R(true_R(LOCAL_C[1]))
ADC_Q = (LOCAL_C[1] - LOCAL_C[0]) / (C26 - C24)
ADC_P = LOCAL_C[0] - ADC_Q * C24


def measure(R_true, noise):
    R_noisy = max(R_true + noise, 1e-6)
    v = VCC * R_noisy / (R_noisy + R_DIV)
    frac = min(max(v / VCC, 0.0), 1.0)
    counts = int(frac * ADC_COUNTS + 0.5)
    if counts <= 0:
        counts = 1
    if counts >= ADC_COUNTS:
        counts = ADC_COUNTS - 1
    # Invert the same divider.
    R_meas = R_DIV * counts / (ADC_COUNTS - counts)
    return R_meas, counts


def estimate(arm, R_meas, counts):
    if arm == "A_beta_local":
        return T_from_beta(R_meas, BBETA, R0_BETA, T0_BETA) - K0
    if arm == "B_sh_threepoint":
        return sh_T_from_R(R_meas, SH_A, SH_B, SH_C) - K0
    if arm == "C_adc_counts":
        return ADC_P + ADC_Q * counts
    return sh_T_from_R(R_meas, SH_A_N, SH_B_N, SH_C_N) - K0


def estimate_linear(R_meas):
    return T_from_linear(R_meas, K_LIN, R0_LIN, T0_LIN) - K0


def rmse(errs):
    return math.sqrt(sum(e * e for e in errs) / len(errs))


def run_regime(regime, seed, extra_arms=()):
    temps, _ = REGIMES[regime]
    rng = random.Random(f"{regime}/{seed}")
    noises = [rng.gauss(0.0, SIG_R) for _ in temps]
    arms = list(ARMS) + list(extra_arms)
    out = {arm: {m: 0.0 for m in METRICS} for arm in arms}
    for arm in arms:
        errs = []
        for Tc, noise in zip(temps, noises):
            R_true = true_R(Tc)
            R_meas, counts = measure(R_true, noise)
            if arm == "A_linear":
                that = estimate_linear(R_meas)
            elif arm == "C_sh_narrow":
                that = estimate(arm, R_meas, counts)
            else:
                that = estimate(arm, R_meas, counts)
            errs.append(that - Tc)
        out[arm]["rmse_C"] = rmse(errs)
    return out


def main():
    print("Steinhart-Hart NTC sensing toy: shared temperature list, divider/ADC and resistance noise (synthetic; not a vendor curve, not a bath, not an inrush limiter, not an IMU temperature register)")
    print("Wikipedia example coefficients and the 0.02 C claim 以原文为准; real thermistor / bath / IMU temperature register: 本页未运行")
    print(
        f"seeds={len(SEEDS)} t0_C={num(T0_C)} t0_K={num(T0_K)} k0={num(K0)} "
        f"cal_R={CAL_R[0]:.4f},{CAL_R[1]:.4f},{CAL_R[2]:.4f} "
        f"cal_C={CAL_C[0]:.4f},{CAL_C[1]:.4f},{CAL_C[2]:.4f} "
        f"narrow_C={NARROW_C[0]:.4f},{NARROW_C[1]:.4f},{NARROW_C[2]:.4f} "
        f"local_C={LOCAL_C[0]:.4f},{LOCAL_C[1]:.4f} "
        f"mid_C={','.join(f'{x:.4f}' for x in MID_C)} "
        f"wide_C={','.join(f'{x:.4f}' for x in WIDE_C)} "
        f"far_C={','.join(f'{x:.4f}' for x in FAR_C)} "
        f"vcc={num(VCC)} r_div={num(R_DIV)} adc_bits={ADC_BITS} adc_counts={ADC_COUNTS} "
        f"sig_R={num(SIG_R)} "
        f"sh_A={SH_A:.10e} sh_B={SH_B:.10e} sh_C={SH_C:.10e} "
        f"beta={num(BBETA)} adc_p={num(ADC_P)} adc_q={num(ADC_Q)} "
        f"adc_c_local={C24},{C26} (declared)"
    )
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: the resistance noise draw is shared across arms at each regime and seed")
    print(f"hand_calc 25 C in kelvin = {num(T0_K)}")
    print(f"hand_calc 0 C in kelvin = {num(0.0 + K0)}")
    print(f"hand_calc 80 C in kelvin = {num(80.0 + K0)}")
    print(f"hand_calc 1/T at 25 C = {1.0 / T0_K:.10e}")
    print(f"hand_calc true R at 25 C = {num(true_R(25.0))}")
    v25 = VCC * true_R(25.0) / (true_R(25.0) + R_DIV)
    print(f"hand_calc divider V at 25 C, no noise = {num(v25)}")
    print(f"hand_calc A,B,C from the three declared points = {SH_A:.10e}, {SH_B:.10e}, {SH_C:.10e}")
    print(f"hand_calc card range mid_C = {MID_C[0]:.4f} to {MID_C[-1]:.4f}")
    print(f"hand_calc card range wide_C = {WIDE_C[0]:.4f} to {WIDE_C[-1]:.4f}")
    print(f"hand_calc card range far_C = {FAR_C[0]:.4f} to {FAR_C[-1]:.4f}")
    print(f"hand_calc local R at 24 C and 26 C = {num(R_LOCAL[0])}, {num(R_LOCAL[1])}")
    print(f"hand_calc narrow R at 24, 25, 26 C = {num(NARROW_POINTS[0][0])}, {num(NARROW_POINTS[1][0])}, {num(NARROW_POINTS[2][0])}")
    print(f"hand_calc beta and local T0, R0 = {num(BBETA)}, {num(T0_BETA)}, {num(R0_BETA)}")
    print(f"hand_calc adc counts-to-C line P, Q and counts at 24 C, 26 C = {num(ADC_P)}, {num(ADC_Q)}, {C24}, {C26}")

    for r, (_temps, exp) in REGIMES.items():
        print(f"declared {r}: {exp}")

    EXTRA = ("A_linear", "C_sh_narrow")
    store = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_store = {r: {arm: {m: [] for m in METRICS} for arm in list(ARMS) + list(EXTRA)} for r in REGIMES}
    for seed in SEEDS:
        for r in REGIMES:
            official = run_regime(r, seed)
            alt = run_regime(r, seed, extra_arms=EXTRA)
            for arm in ARMS:
                for m in METRICS:
                    store[r][arm][m].append(official[arm][m])
                    alt_store[r][arm][m].append(alt[arm][m])
            for arm in EXTRA:
                for m in METRICS:
                    alt_store[r][arm][m].append(alt[arm][m])

    for r in REGIMES:
        print(f"regime {r}")
        for arm in ARMS:
            for m in METRICS:
                mu, sd = mean_sd(store[r][arm][m])
                print(f"  {arm} {m}: {num(mu)}+-{num(sd)}")
        for left, right in PAIRS:
            la = [a for a in ARMS if a.startswith(left + "_")][0]
            ra = [a for a in ARMS if a.startswith(right + "_")][0]
            for m in METRICS:
                print(f"  paired {left}-{right} {m}: {verdict(store[r][la][m], store[r][ra][m])}")

    print("alternative A_linear = dR/dT fitted only near 25 C (printed, not adopted)")
    print("alternative C_sh_narrow = Steinhart-Hart coefficients from the three narrow-C points (printed, not adopted; on this three-parameter curve it recovers the same A, B, C as arm B)")
    for r in REGIMES:
        official_ba = verdict(store[r]["B_sh_threepoint"]["rmse_C"], store[r]["A_beta_local"]["rmse_C"])
        alt_ba = verdict(alt_store[r]["B_sh_threepoint"]["rmse_C"], alt_store[r]["A_linear"]["rmse_C"])
        official_cb = verdict(store[r]["C_adc_counts"]["rmse_C"], store[r]["B_sh_threepoint"]["rmse_C"])
        alt_cb = verdict(alt_store[r]["C_sh_narrow"]["rmse_C"], alt_store[r]["B_sh_threepoint"]["rmse_C"])
        print(f"  {r} official B-A rmse_C: {official_ba}")
        print(f"  {r} alternative B-A_linear rmse_C: {alt_ba}")
        print(f"  {r} official C-B rmse_C: {official_cb}")
        print(f"  {r} alternative C_sh_narrow-B rmse_C: {alt_cb}")


if __name__ == "__main__":
    main()
