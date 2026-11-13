#!/usr/bin/env python3
"""Synthetic optocoupler (opto-isolator) CTR and galvanic-isolation toy for a
microcontroller digital input. Stdlib only.

Every constant below is a DECLARED TOY PARAMETER, not a datasheet value: no
vendor part, no real isolation rating, no CTR curve. A 24 V field signal reaches
a 3.3 V input pin either directly through a divider that shares ground (A), or
through an optocoupler whose LED is driven at 10 mA (B) or 1 mA (C).

Opto output (inverting, LED on -> pin pulled low):
  I_avail = CTR * I_F, I_sat = (VCC - VCE_SAT) / RL
  V_out = max(VCE_SAT, VCC - min(I_avail, I_sat) * RL) with the LED on, VCC off.
Read rule: pin < V_IL -> 0, pin > V_IH -> 1, in between -> invalid (an error).
The direct pin sees bit*V_FIELD*K_DIV + K_CM*v_cm + noise; the opto pin sees only
K_ISO*v_cm of the field-side common-mode surge v_cm (a stray-capacitance stand-in).
CTR is lumped: one part per (regime, seed), CTR = CTR_NOM * exp(0.3 g), shared by
both opto arms (same part, different LED current); low_ctr ages it by AGE.

Common random numbers: one random.Random(f"{regime}/{seed}") stream per
(regime, seed) draws g, then for every bit the field bit, the pin noise, the
surge flag and the surge amplitude, in that fixed order, before any arm is
evaluated; all arms share them.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.
Not an RS-485 or ADC model. Real coupler / isolation tester: 本页未运行.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

VCC = 3.3
RL = 4700.0
VCE_SAT = 0.2
V_IL = 0.3 * VCC
V_IH = 0.7 * VCC
ABS_MAX = VCC + 0.3
V_FIELD = 24.0
K_DIV = 3.0 / 24.0
K_CM = 0.1
K_ISO = 1e-4
CTR_NOM = 0.5
CTR_SPREAD = 0.3
SIG_PIN = 0.05
N_BITS = 200
P_SURGE = 0.2
SURGE_LO, SURGE_HI = 20.0, 200.0
AGE = 0.25
I_F_B = 10e-3
I_F_C = 1e-3

METRICS = ("logic_err", "overvolt")
ARMS = ("A_direct", "B_opto", "C_underdriven")
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

# name: (surge on?, CTR age factor, declared expectation); written before the first run
REGIMES = {
    "quiet_legal": (False, 1.0, "A vs B may near-tie (or tie) on logic_err - keep; C as it comes"),
    "surge": (True, 1.0, "B consistently below A on overvolt and logic_err (direct GPIO loses) - keep"),
    "low_ctr": (False, AGE, "C consistently above B on logic_err (under-driven coupler loses) and may lose to A on logic_err - keep"),
}


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0  # identical values: no floating residue in mean or sd
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    """Half-up rounding on the shortest decimal repr; tiny non-zero values in scientific form."""
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


def draws(regime, seed):
    rng = random.Random(f"{regime}/{seed}")
    g = rng.gauss(0.0, 1.0)
    bits = []
    for _ in range(N_BITS):
        bit = 1 if rng.random() < 0.5 else 0
        noise = rng.gauss(0.0, SIG_PIN)
        flag = rng.random() < P_SURGE
        v_cm = rng.uniform(SURGE_LO, SURGE_HI)
        bits.append((bit, noise, flag, v_cm))
    return g, bits


def read_pin(v):
    if v < V_IL:
        return 0
    if v > V_IH:
        return 1
    return None


def opto_out(bit, ctr, i_f, rl):
    if not bit:
        return VCC
    i_sat = (VCC - VCE_SAT) / rl
    return max(VCE_SAT, VCC - min(ctr * i_f, i_sat) * rl)


def run_arm(arm, g, bits, surge_on, age, k_cm=K_CM, rl=RL, i_f_c=I_F_C):
    ctr = CTR_NOM * math.exp(CTR_SPREAD * g) * age
    err = over = 0
    for bit, noise, flag, v_cm in bits:
        cm = v_cm if (surge_on and flag) else 0.0
        if arm == "A_direct":
            pin = bit * V_FIELD * K_DIV + k_cm * cm + noise
            got = read_pin(pin)
        else:
            i_f = I_F_B if arm == "B_opto" else i_f_c
            pin = opto_out(bit, ctr, i_f, rl) + K_ISO * cm + noise
            r = read_pin(pin)
            got = None if r is None else 1 - r
        if got != bit:
            err += 1
        if pin > ABS_MAX:
            over += 1
    return {"logic_err": err / N_BITS, "overvolt": over / N_BITS}


def run_regime(regime, **kw):
    surge_on, age, _ = REGIMES[regime]
    out = {a: {m: [] for m in METRICS} for a in ARMS}
    for seed in SEEDS:
        g, bits = draws(regime, seed)
        for a in ARMS:
            r = run_arm(a, g, bits, surge_on, age, **kw)
            for m in METRICS:
                out[a][m].append(r[m])
    return out


def letter(arm):
    return arm[0]


def by_letter(res, x):
    return next(v for k, v in res.items() if letter(k) == x)


def main():
    print("Synthetic optocoupler CTR and isolation toy: direct GPIO vs a well-driven and an under-driven coupler")
    print("every constant is a declared toy parameter, not a datasheet value; real coupler / isolation tester: 本页未运行")
    print(f"VCC={num(VCC)} V RL={num(RL)} ohm VCE_SAT={num(VCE_SAT)} V V_IL={num(V_IL)} V V_IH={num(V_IH)} V ABS_MAX={num(ABS_MAX)} V")
    print(f"V_FIELD={num(V_FIELD)} V K_DIV={num(K_DIV)} K_CM={num(K_CM)} K_ISO={num(K_ISO)} CTR_NOM={num(CTR_NOM)} CTR spread exp(0.3 g) SIG_PIN={num(SIG_PIN)} V")
    print(f"N_BITS={N_BITS} P_SURGE={num(P_SURGE)} v_cm uniform({num(SURGE_LO)}, {num(SURGE_HI)}) V AGE={num(AGE)} I_F B={num(I_F_B * 1e3)} mA C={num(I_F_C * 1e3)} mA")
    print("Regimes and parameters were written before the first run")
    i_sat = (VCC - VCE_SAT) / RL
    print(f"hand_calc I_sat = (3.3 - 0.2)/4700 = {num(i_sat * 1e3)} mA collector current to pull the pin to VCE_SAT")
    print(f"hand_calc minimum I_F at CTR_NOM = I_sat/CTR_NOM = {num(i_sat / CTR_NOM * 1e3)} mA")
    print(f"hand_calc C at nominal CTR: I_C = 0.5 x 1 mA = 0.5000 mA -> V_out = 3.3 - 0.5e-3 x 4700 = {num(VCC - 0.5e-3 * RL)} V against V_IL = {num(V_IL)} V")
    print(f"hand_calc worst surge on the direct pin = 200 x K_CM = {num(SURGE_HI * K_CM)} V against ABS_MAX = {num(ABS_MAX)} V")
    print(f"hand_calc aged C: I_C = 0.25 x 0.5 x 1 mA = {num(AGE * CTR_NOM * 1e-3 * 1e3)} mA -> V_out = {num(VCC - AGE * CTR_NOM * 1e-3 * RL)} V, above V_IH = {num(V_IH)} V")
    for regime, (surge_on, age, declared) in REGIMES.items():
        res = run_regime(regime)
        print(f"{regime}:")
        print(f"  declared: {declared}")
        for a in ARMS:
            print("  " + a + " " + " ".join(f"{m} {fmt_pair(*mean_sd(res[a][m]))}" for m in METRICS))
        for x, y in PAIRS:
            for m in METRICS:
                print(f"  paired {x}-{y} {m}: {verdict(by_letter(res, x)[m], by_letter(res, y)[m])}")
    print("alternative parameters (declared before the run, same seeds, not adopted):")
    r = run_regime("low_ctr", rl=10000.0)
    print(f"  low_ctr with RL = 10000 ohm: paired C-B logic_err: {verdict(r['C_underdriven']['logic_err'], r['B_opto']['logic_err'])}")
    r = run_regime("surge", k_cm=0.02)
    print(f"  surge with K_CM = 0.02: paired B-A overvolt: {verdict(r['B_opto']['overvolt'], r['A_direct']['overvolt'])}")
    r = run_regime("low_ctr", i_f_c=2e-3)
    print(f"  low_ctr with C at I_F = 2 mA: paired C-B logic_err: {verdict(r['C_underdriven']['logic_err'], r['B_opto']['logic_err'])}")
    print("No winner beyond the declared drive: the barrier blocks the surge only when the LED current times CTR still saturates the output")
    print("Real coupler / isolation tester / vendor CTR curve: 本页未运行; Wikipedia figures 以原文为准")


if __name__ == "__main__":
    main()
