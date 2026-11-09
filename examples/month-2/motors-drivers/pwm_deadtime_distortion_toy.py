#!/usr/bin/env python3
"""Synthetic PWM dead-time toy: one half-bridge leg driving an R-L load to the
bus midpoint (so the current changes sign). NOT FOC, NOT a thermal model, NOT a
gate-driver certificate. Stdlib only.

Ideal complementary PWM switches the leg between +Vdc/2 and -Vdc/2.
Dead time td delays each turn-on edge (both switches OFF for td). While both
are OFF the load current picks the freewheel diode: i>0 -> lower diode ->
-Vdc/2, i<0 -> upper diode -> +Vdc/2, i=0 -> no conduction (the current stays
at zero until the next switch turns on). Two dead intervals per period, one of
which is 'lost', give the average error  dV ~ -sign(i) * td/Ts * Vdc.

All arms share the SAME reference, Vdc, load, PWM carrier and seeds:
  A_ideal  td = 0
  B_td     td = 1 us with per-period jitter (shared random draws)
  C_td_comp same dead time + crude feed-forward duty correction
           d' = d + sign(i_meas) * td_nom/Ts, using a noisy current sample at
           the period start (same Vdc, duty clipped to [0, 1])
Two scenarios: a 'normal' load current well above the ripple, and a 'light'
load where the current is comparable to the ripple (compensation sign errors).
Near-zero parasitic-capacitance effects (see Daido & Hayashi) are NOT modelled.
"""
import math
import random

VDC = 24.0
FSW = 20000.0
TS = 1.0 / FSW
TD = 1.0e-6
TD_JITTER = 0.10      # +-10 % uniform per period, shared by B and C
F0 = 50.0
R = 2.0
L = 2.0e-3
TAU = L / R
CYCLES = 6
WARM = 1              # discard the first cycle
SENSE_SIGMA = 0.05    # A, current-sense noise used only by the compensator
SUBSTEPS = 8          # sub-steps inside each dead interval
SEEDS = (0, 1, 2, 3, 4)
SCENARIOS = (("normal", 0.30), ("light", 0.05))
ARMS = ("A_ideal", "B_td", "C_td_comp")


def rl_step(i, v, h):
    """Exact R-L response over h seconds with constant applied voltage v."""
    if h <= 0:
        return i, 0.0
    target = v / R
    e = math.exp(-h / TAU)
    i_new = target + (i - target) * e
    # integral of i over the step (for average-current bookkeeping)
    integ = target * h + (i - target) * TAU * (1 - e)
    return i_new, integ


def dead_interval(i, h):
    """Both switches OFF for h seconds: diode clamps by current sign.
    Returns new current and volt-seconds applied."""
    vs = 0.0
    dt = h / SUBSTEPS
    for _ in range(SUBSTEPS):
        if i > 0:
            v = -VDC / 2
        elif i < 0:
            v = VDC / 2
        else:
            continue   # no conduction, leg floats to the load voltage (0 V here)
        i_new, _ = rl_step(i, v, dt)
        if (i > 0) != (i_new > 0) or i_new == 0:
            # current reaches zero inside the sub-step: clamp, conduction stops
            frac = math.log((i - v / R) / (0 - v / R)) * TAU / dt if i - v / R != 0 else 1.0
            frac = min(max(frac, 0.0), 1.0)
            vs += v * dt * frac
            i = 0.0
            continue
        vs += v * dt
        i = i_new
    return i, vs


def run(arm, m, seed):
    rng_td = random.Random(1000 + seed)      # shared jitter stream (B and C)
    rng_sense = random.Random(2000 + seed)   # sense noise (used by C only)
    periods = int(round(CYCLES * FSW / F0))
    i = 0.0
    out = []
    for k in range(periods):
        t = k * TS
        ref = m * (VDC / 2) * math.sin(2 * math.pi * F0 * (t + TS / 2))
        d = 0.5 + ref / VDC
        jitter = 1 + TD_JITTER * (2 * rng_td.random() - 1)
        sense = i + rng_sense.gauss(0.0, SENSE_SIGMA)
        td = 0.0 if arm == "A_ideal" else TD * jitter
        if arm == "C_td_comp":
            d = d + (1 if sense > 0 else -1) * TD / TS
        d = min(max(d, 0.0), 1.0)
        t1 = (1 - d) * TS / 2
        t2 = (1 + d) * TS / 2
        i_start = i
        vs = 0.0
        # low on [0,t1), dead [t1,t1+td), high on [t1+td,t2), dead [t2,t2+td), low on [t2+td,Ts)
        hi_on = max(t2 - (t1 + td), 0.0)
        lo_first = t1
        lo_last = max(TS - (t2 + td), 0.0)
        i, _ = rl_step(i, -VDC / 2, lo_first); vs += -VDC / 2 * lo_first
        dead1 = min(td, t2 - t1)
        i, dv = dead_interval(i, dead1); vs += dv
        i, _ = rl_step(i, VDC / 2, hi_on); vs += VDC / 2 * hi_on
        dead2 = min(td, TS - t2)
        i, dv = dead_interval(i, dead2); vs += dv
        i, _ = rl_step(i, -VDC / 2, lo_last); vs += -VDC / 2 * lo_last
        if k >= WARM * FSW / F0:
            out.append((ref, vs / TS, 0.5 * (i_start + i)))
    return out


def harmonic(xs, n):
    """Amplitude of the n-th harmonic of the fundamental over whole cycles."""
    N = len(xs)
    cycles = CYCLES - WARM
    c = sum(x * math.cos(2 * math.pi * n * cycles * j / N) for j, x in enumerate(xs))
    s = sum(x * math.sin(2 * math.pi * n * cycles * j / N) for j, x in enumerate(xs))
    return 2 * math.hypot(c, s) / N


def stats(vals):
    mu = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / (len(vals) - 1)) if len(vals) > 1 else 0.0
    return mu, sd


def main():
    print("Synthetic half-bridge dead-time toy; Vdc/R/L/td are lesson values, not a driver datasheet")
    print(f"Vdc_V={VDC:.0f} fsw_kHz={FSW / 1e3:.0f} Ts_us={TS * 1e6:.0f} td_us={TD * 1e6:.1f} jitter=+-{TD_JITTER * 100:.0f}% "
          f"R_ohm={R:.0f} L_mH={L * 1e3:.0f} f0_Hz={F0:.0f} seeds={len(SEEDS)}")
    print(f"predicted |dV| = td/Ts*Vdc = {TD / TS * VDC:.3f} V, sign opposite to i (positive i loses volts)")
    print("shared: reference, Vdc, load, carrier, jitter stream; C only adds a sign(i_meas) duty term")
    print("scenario arm mean_err_i_pos_V mean_err_i_neg_V fund_V I1_A I3_over_I1_% irms_err_vs_A_A zero_dwell_% (mean+-sd over seeds)")
    for name, m in SCENARIOS:
        ideal = {seed: run("A_ideal", m, seed) for seed in SEEDS}
        for arm in ARMS:
            pos, neg, fund, i1, i3r, rms, dwell = [], [], [], [], [], [], []
            for seed in SEEDS:
                rows = ideal[seed] if arm == "A_ideal" else run(arm, m, seed)
                ref_rows = ideal[seed]
                ep = [v - r for (r, v, i) in rows if i > 0.05]
                en = [v - r for (r, v, i) in rows if i < -0.05]
                pos.append(sum(ep) / len(ep))
                neg.append(sum(en) / len(en))
                fund.append(harmonic([v for _, v, _ in rows], 1))
                cur = [i for _, _, i in rows]
                a1 = harmonic(cur, 1)
                i1.append(a1)
                i3r.append(100 * harmonic(cur, 3) / a1)
                rms.append(math.sqrt(sum((a[2] - b[2]) ** 2 for a, b in zip(rows, ref_rows)) / len(rows)))
                dwell.append(100 * sum(abs(x) < 0.02 for x in cur) / len(cur))
            cols = [stats(x) for x in (pos, neg, fund, i1, i3r, rms, dwell)]
            print(f"{name} {arm} " + " ".join(
                f"{mu:+.3f}+-{sd:.3f}" if j < 2 else f"{mu:.3f}+-{sd:.3f}" for j, (mu, sd) in enumerate(cols)))
        print(f"{name} reference_fund_V={m * VDC / 2:.3f}")
    print("No winner is declared: compare the normal and light rows before trusting the compensator")
    print("Real half-bridge, gate driver and scope: 本页未运行; driver/app-note numbers 以原文为准")


if __name__ == "__main__":
    main()
