#!/usr/bin/env python3
"""Peukert rate-capacity vs the nameplate clock on a shared (C, H) rating.

Synthetic constant-current discharge, stdlib only.  Not a pack test, not a
BMS, not the C-rate quiz on this page and not the coulomb SoC / temperature
derate toy in the power lesson.  Real pack / BMS / calorimeter: 本页未运行.
Wikipedia "Peukert's law" statements 以原文为准.

What the Wikipedia body says (and what this toy keeps): Peukert's law is an
approximate law for rechargeable lead-acid batteries.  At a known rating
(capacity C at an H-hour rate) the time to discharge at current I is
  t = H * (C / (I * H)) ** k
If k were 1 the delivered capacity would not depend on current; for a real
lead-acid battery k is typically between 1.1 and 1.3.  At the rated current
I = C / H the formula gives t = H, the same as the nameplate clock C / I.
The page also lists limits: temperature is not in the equation, k grows
with age, at low current self-discharge must be taken into account, and at
very high currents practical batteries give less capacity than a fixed
exponent predicts.  Nothing here says k is 1.3 for a LiPo.

Common random numbers: for each (regime, seed) one "true" exponent k_true is
drawn once and shared by every arm; it only feeds the declared generator
(the synthetic pack every arm is scored against).  Arms:
  A_nameplate : t = C / I (the nameplate / Coulomb clock)
  B_peukert   : t = H * (C / (I*H)) ** K_DECL, fixed lead-acid K_DECL
  C_k1        : the same formula with k = 1 (should equal A)
  D_cap       : B times D_DERATE when I > I_KNEE (a declared high-current cap)
The arms differ only in the prediction rule.  No integration step: closed
form, no time stepping, so no step-size criterion applies.

Declared generator (synthetic pack, toy assumptions, not a measured cell):
  lead-acid pack : k_true uniform in [K_LA_LO, K_LA_HI]
  k~1 pack       : k_true uniform in [K_ONE_LO, K_ONE_HI] (a toy stand-in for
                   a pack whose capacity barely depends on current)
  t_true = H * (C / (I_eff * H)) ** k_true, times (I_KNEE / I) ** GAMMA only
  when I > I_KNEE (strict); I_eff = I + I_SD only in the "low" cell.

Regimes and parameters were written before the first run:
  rated      : I = C/H on the lead-acid pack - A vs B tie (t = H exactly)
  high       : I = 4 C/H, lead-acid - A consistent over-predicts vs B
               (nameplate loses on |error|)
  very_high  : I = 20 C/H, lead-acid with the generator's high-current loss -
               fixed-k B over-predicts (signed error > 0) and can lose to the
               cap D on |error|; keep whatever comes out
  low        : I = C/(10 H), lead-acid with self-discharge I_SD - B predicts
               more Ah than the nameplate; B over-predicts vs the generator;
               A vs B on |error| not pre-declared, printed as it comes
  misapplied : I = 4 C/H on the k~1 pack scored with lead-acid K_DECL -
               B consistent loses vs nameplate on |error|; keep
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
C_RATED = 100.0   # Ah at the H-hour rate (Wikipedia's worked-example rating)
H_RATED = 20.0    # h
K_DECL = 1.2      # lead-acid exponent used by B (Wikipedia's worked example; inside 1.1-1.3)
K_LA_LO, K_LA_HI = 1.15, 1.25    # generator lead-acid k_true (toy)
K_ONE_LO, K_ONE_HI = 1.00, 1.03  # generator k~1 pack k_true (toy, not a LiPo datasheet)
I_KNEE = 50.0     # A, generator / D high-current threshold (toy)
GAMMA = 0.25      # generator extra loss exponent above I_KNEE (toy)
D_DERATE = 0.80   # D's fixed cap above I_KNEE (toy rule, not a documented value)
I_SD = 0.05       # A, self-discharge stand-in, "low" cell only (toy)

I_RATED = C_RATED / H_RATED
REGIMES = {
    "rated": {"i": I_RATED, "pack": "lead_acid", "sd": False},
    "high": {"i": 4.0 * I_RATED, "pack": "lead_acid", "sd": False},
    "very_high": {"i": 20.0 * I_RATED, "pack": "lead_acid", "sd": False},
    "low": {"i": 0.1 * I_RATED, "pack": "lead_acid", "sd": True},
    "misapplied": {"i": 4.0 * I_RATED, "pack": "k_one", "sd": False},
}
ARMS = ("A_nameplate", "B_peukert", "C_k1", "D_cap")


def peukert_t(i, k, c=C_RATED, h=H_RATED):
    return h * (c / (i * h)) ** k


def shared_k(regime, seed):
    """Common random numbers: one k_true per (regime, seed), shared by all arms."""
    rng = random.Random(f"{regime}/{seed}")
    lo, hi = (K_LA_LO, K_LA_HI) if REGIMES[regime]["pack"] == "lead_acid" else (K_ONE_LO, K_ONE_HI)
    return rng.uniform(lo, hi)


def true_t(regime, seed, gamma=GAMMA, i_sd=I_SD):
    cfg = REGIMES[regime]
    i = cfg["i"]
    i_eff = i + (i_sd if cfg["sd"] else 0.0)
    t = peukert_t(i_eff, shared_k(regime, seed))
    if i > I_KNEE:
        t *= (I_KNEE / i) ** gamma
    return t


def predict(arm, i, k_decl=K_DECL, derate=D_DERATE):
    if arm == "A_nameplate":
        return C_RATED / i
    if arm == "B_peukert":
        return peukert_t(i, k_decl)
    if arm == "C_k1":
        return peukert_t(i, 1.0)
    t = peukert_t(i, k_decl)
    return t * derate if i > I_KNEE else t


def run_arm(arm, regime, seed, **kw):
    gen = {k: kw.pop(k) for k in ("gamma", "i_sd") if k in kw}
    i = REGIMES[regime]["i"]
    t = predict(arm, i, **kw)
    tt = true_t(regime, seed, **gen)
    return {"t": t, "q": i * t, "err": t - tt, "abs_err": abs(t - tt), "t_true": tt}


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


METRICS = ("t", "q", "err", "abs_err")


def collect(regime, **kw):
    return {arm: [run_arm(arm, regime, s, **dict(kw)) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [r[key] for r in rows]


def report(regime):
    cfg = REGIMES[regime]
    res = collect(regime)
    ks = [shared_k(regime, s) for s in SEEDS]
    tts = col(res["A_nameplate"], "t_true")
    print(f"{regime} (I={num(cfg['i'])} A = {num(cfg['i'] / I_RATED)} x C/H; pack={cfg['pack']}; "
          f"self_discharge={'I_SD' if cfg['sd'] else 'off'}; high_current_loss={'on' if cfg['i'] > I_KNEE else 'off'}):")
    print("  k_true per seed: " + " ".join(num(k) for k in ks))
    print("  t_true per seed (h): " + " ".join(num(t) for t in tts))
    for arm in ARMS:
        rows = res[arm]
        print(f"  {arm} " + " ".join(f"{key} {fmt_pair(*mean_sd(col(rows, key)))}" for key in METRICS))
    for arm in ("A_nameplate", "B_peukert", "D_cap"):
        over = sum(1 for r in res[arm] if r["err"] > 0.0)
        under = sum(1 for r in res[arm] if r["err"] < 0.0)
        print(f"  {arm} over-predicts (err > 0) on {over}/5 seeds, under-predicts on {under}/5")
    for a, b, keys in (("A_nameplate", "B_peukert", ("t", "abs_err")), ("C_k1", "A_nameplate", ("t",)),
                       ("B_peukert", "A_nameplate", ("err",)), ("D_cap", "B_peukert", ("abs_err",))):
        for key in keys:
            print(f"  paired {a[0]}-{b[0]} {key}: {verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("Synthetic Peukert rate-capacity toy; shared (C, H) rating and shared k_true draws; not a pack measurement")
    print(f"seeds={len(SEEDS)} C={num(C_RATED)} Ah H={num(H_RATED)} h (I_rated=C/H={num(I_RATED)} A) K_DECL={num(K_DECL)} "
          f"k_true lead-acid U[{num(K_LA_LO)}, {num(K_LA_HI)}] k~1 pack U[{num(K_ONE_LO)}, {num(K_ONE_HI)}] "
          f"I_KNEE={num(I_KNEE)} A GAMMA={num(GAMMA)} D_DERATE={num(D_DERATE)} I_SD={num(I_SD)} A (declared toy parameters, not a datasheet)")
    print("No integration step: closed form, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print("rule: t = H * (C / (I*H)) ** k; nameplate clock t = C / I; high-current loss and D's cap apply iff I > I_KNEE (strict)")
    # Labelled hand calculation: Wikipedia's worked example (100 Ah, 20 h, k = 1.2, 10 A).
    t_ex = peukert_t(10.0, 1.2)
    print(f"hand_calc C=100.0 Ah H=20.0 h k=1.2 I=10.0 A: t=20*(100/(10*20))^1.2={num(t_ex)} h, "
          f"delivered I*t={num(10.0 * t_ex)} Ah (Wikipedia worked example: about 8.7 h and 87 Ah, 以原文为准); nameplate C/I={num(C_RATED / 10.0)} h")
    print(f"hand_calc rated I=C/H={num(I_RATED)} A: (C/(I*H))={num(C_RATED / (I_RATED * H_RATED))} so t=H={num(peukert_t(I_RATED, K_DECL))} h for any k; "
          f"C/I={num(C_RATED / I_RATED)} h")
    eq, above = predict("D_cap", I_KNEE) / predict("B_peukert", I_KNEE), predict("D_cap", I_KNEE + 1e-6) / predict("B_peukert", I_KNEE + 1e-6)
    print(f"boundary_rule: I=I_KNEE={num(I_KNEE)} A -> D/B={num(eq)} (no cap at equality); I=I_KNEE+1e-6 A -> D/B={num(above)}")
    for regime in REGIMES:
        report(regime)
    print("alternative K_DECL on high (same seeds; B uses the alternative exponent):")
    for k in (1.1, 1.3):
        alt = collect("high", k_decl=k)
        print(f"  K_DECL={num(k)}: paired A-B abs_err@alt: {verdict(col(alt['A_nameplate'], 'abs_err'), col(alt['B_peukert'], 'abs_err'))}")
    print("alternative K_DECL=1.3 on misapplied (same seeds; top of the lead-acid range on the k~1 pack):")
    alt = collect("misapplied", k_decl=1.3)
    print(f"  paired A-B abs_err@alt: {verdict(col(alt['A_nameplate'], 'abs_err'), col(alt['B_peukert'], 'abs_err'))}")
    print("alternative D_DERATE=0.90 and GAMMA=0.10 on very_high (same seeds):")
    alt = collect("very_high", derate=0.90)
    print(f"  D_DERATE=0.90: paired D-B abs_err@alt: {verdict(col(alt['D_cap'], 'abs_err'), col(alt['B_peukert'], 'abs_err'))}")
    alt = collect("very_high", gamma=0.10)
    print(f"  GAMMA=0.10: paired D-B abs_err@alt: {verdict(col(alt['D_cap'], 'abs_err'), col(alt['B_peukert'], 'abs_err'))}")
    print(f"  GAMMA=0.10: paired B-A err@alt: {verdict(col(alt['B_peukert'], 'err'), col(alt['A_nameplate'], 'err'))}")
    print("alternative I_SD=0.0 on low (same seeds; no self-discharge in the generator):")
    alt = collect("low", i_sd=0.0)
    print(f"  B_peukert err@alt {fmt_pair(*mean_sd(col(alt['B_peukert'], 'err')))}")
    print(f"  paired A-B abs_err@alt: {verdict(col(alt['A_nameplate'], 'abs_err'), col(alt['B_peukert'], 'abs_err'))}")
    print("No winner declared: at the rated current every rule agrees; a lead-acid exponent beats the nameplate clock at high current, "
          "over-predicts at very high current, and loses when it is applied to a pack whose capacity barely depends on current")
    print("Real pack / BMS / calorimeter: 本页未运行; Wikipedia Peukert's law statements 以原文为准")


if __name__ == "__main__":
    main()
