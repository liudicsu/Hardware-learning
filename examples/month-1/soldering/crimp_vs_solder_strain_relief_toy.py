#!/usr/bin/env python3
"""Crimp versus solder on a stranded wire lead, with strain relief.

Synthetic mechanical / resistance stand-in, stdlib only, deterministic.  Not an
IPC-A-610 inspection and not a pull tester.  Not the thermal-window / cold-joint
toy.  A real crimp tool / IPC inspection: 本页未运行.  Wikipedia "Crimp
(joining)" statements (solderless, gas-tight, no solder wicking, "mechanically
stronger") are 以原文为准 and are not toy outputs.

Model.  One stranded lead with N_STRANDS = 19 strands of diameter
D_STRAND = 0.16 mm (declared toy values, roughly a 22 AWG 19-strand wire, not a
datasheet).  Each flex cycle bends the strands at the joint's stiff-to-flexible
transition with outer-fibre strain eps = D_STRAND / (2 * rho), where rho is the
bend radius at that transition.  Strand fatigue life (cycles) is
N_i = N_REF * (EPS_REF / eps) ** K_FAT * z_i with N_REF = 2000, EPS_REF = 0.02,
K_FAT = 2.0, and z_i = exp(gauss(0, SIGMA_LIFE)) with SIGMA_LIFE = 0.3 per
strand.  A strand is intact at the end if N_i > cycles.  Contact resistance is
R_c = R_C0 * u * (base multiplier) * (1 + growth), R_C0 = 0.50 milliohm,
u = uniform(0.9, 1.1).

Arms:
  A_solder_bare   : soldered tinned strand, no strain relief; solder wicks into
                    the strands and the bend concentrates at the wick edge:
                    rho = 3.0 mm; gas-tight (solder fills the joint): growth 0;
                    base multiplier 1.0.
  B_crimp_good    : correctly sized gas-tight crimp, no solder, no extra sleeve:
                    rho = 6.0 mm (bellmouth at the barrel edge, no wicking);
                    growth 0; base multiplier 1.0.
  C_crimp_under   : under-crimp / wrong barrel: same rho = 6.0 mm as B, NOT
                    gas-tight and the strands can fret: base multiplier
                    UNDER_X = 3.0 and
                    growth = FRET_PER_KCYCLE * cycles / 1000
                             + OX_PER_KHOUR * hours / 1000
                    with FRET_PER_KCYCLE = 0.5, OX_PER_KHOUR = 0.5.
  D_solder_relief : soldered joint WITH the lesson's strain relief (cable fixed
                    close to the joint): rho = 12.0 mm; gas-tight; growth 0;
                    base multiplier 1.0.

Common random numbers: for each (regime, seed) draw ONCE from
random.Random(f"{regime}/{seed}") the 19 strand factors z_i and the contact
factor u, shared by all four arms.

Regimes (cycles, hours):
  flex       : (1500, 0)
  light_flex : (300, 0)
  static     : (0, 2000) - a short, well-supported pigtail that never flexes but
               sits in humid air.

Metrics per seed: intact (count of intact strands at the end), life_half
(cycles at which the 10th strand breaks = the 10th smallest N_i, independent of
the schedule), contact_mohm (R_c), gas_tight (1 or 0).

Pairs, every metric in every regime: B-A, C-D, C-B.

Regimes and parameters were written before the first run.  Pre-declared
expectations (not tuned; print whatever comes):
  flex       : A consistently loses to B on intact and life_half; C is not
               gas-tight and loses to D (D = soldered with strain relief) on
               contact_mohm - keep.
  light_flex : A vs B may near-tie on intact - keep.
  static     : A vs B may near-tie or tie (pigtail never flexes); C loses to D
               on contact_mohm - keep.

The ordering of arms follows from the declared bend radii and contact-growth
parameters; the toy shows magnitudes and seed scatter, not evidence that one
method always wins.

Alternatives (same seeds, declared before the run, not adopted):
  flex with K_FAT = 3.0 (paired B-A intact);
  flex with A's rho = 4.0 mm (paired B-A intact);
  static with OX_PER_KHOUR = 0.1 (paired C-D contact_mohm).
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
N_STRANDS = 19
D_STRAND = 0.16              # mm, toy value roughly a 22 AWG 19-strand wire
N_REF = 2000                 # cycles
EPS_REF = 0.02
K_FAT = 2.0
SIGMA_LIFE = 0.3
R_C0 = 0.50                  # milliohm
U_LOW, U_HIGH = 0.9, 1.1
UNDER_X = 3.0
FRET_PER_KCYCLE = 0.5
OX_PER_KHOUR = 0.5

REGIMES = {
    "flex": (1500, 0),
    "light_flex": (300, 0),
    "static": (0, 2000),
}
ARMS = ("A_solder_bare", "B_crimp_good", "C_crimp_under", "D_solder_relief")
RHO = {"A_solder_bare": 3.0, "B_crimp_good": 6.0,
       "C_crimp_under": 6.0, "D_solder_relief": 12.0}
BASE = {"A_solder_bare": 1.0, "B_crimp_good": 1.0,
        "C_crimp_under": UNDER_X, "D_solder_relief": 1.0}
GAS = {"A_solder_bare": 1, "B_crimp_good": 1,
       "C_crimp_under": 0, "D_solder_relief": 1}

DECLARED = {
    "flex": "A consistently loses to B on intact and life_half; C is not "
            "gas-tight and loses to D (D = soldered with strain relief) on "
            "contact_mohm - keep",
    "light_flex": "A vs B may near-tie on intact - keep",
    "static": "A vs B may near-tie or tie (pigtail never flexes); C loses to D "
              "on contact_mohm - keep",
}


def shared_draws(regime, seed):
    """Common random numbers: one set of strands and one contact factor per (regime, seed)."""
    rng = random.Random(f"{regime}/{seed}")
    z = [math.exp(rng.gauss(0.0, SIGMA_LIFE)) for _ in range(N_STRANDS)]
    u = rng.uniform(U_LOW, U_HIGH)
    return z, u


def run_arm(arm, regime, seed, k_fat=K_FAT, rho=None, ox=OX_PER_KHOUR):
    cycles, hours = REGIMES[regime]
    z, u = shared_draws(regime, seed)
    r = RHO[arm] if rho is None else rho
    eps = D_STRAND / (2.0 * r)
    lives = sorted(N_REF * (EPS_REF / eps) ** k_fat * zi for zi in z)
    intact = sum(1 for n in lives if n > cycles)
    if arm == "C_crimp_under":
        growth = FRET_PER_KCYCLE * cycles / 1000.0 + ox * hours / 1000.0
    else:
        growth = 0.0
    contact = R_C0 * u * BASE[arm] * (1.0 + growth)
    return {"intact": intact, "life_half": lives[9],
            "contact_mohm": contact, "gas_tight": GAS[arm]}


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


METRICS = ("intact", "life_half", "contact_mohm", "gas_tight")
PAIRS = (("B_crimp_good", "A_solder_bare"),
         ("C_crimp_under", "D_solder_relief"),
         ("C_crimp_under", "B_crimp_good"))


def collect(regime, **kw):
    return {arm: [run_arm(arm, regime, s, **kw) for s in SEEDS] for arm in ARMS}


def arm_col(regime, arm, **kw):
    return [run_arm(arm, regime, s, **kw) for s in SEEDS]


def col(rows, key):
    return [x[key] for x in rows]


def report(regime):
    cycles, hours = REGIMES[regime]
    res = collect(regime)
    print(f"{regime} (cycles={cycles}, hours={hours}):")
    print(f"  declared: {DECLARED[regime]}")
    for arm in ARMS:
        print(f"  {arm} " + " ".join(
            f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS))
    for a, b in PAIRS:
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: {verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("Synthetic crimp-versus-solder strain-relief toy; shared strand and contact draws; "
          "not an IPC-A-610 inspection or pull tester")
    print(f"seeds={len(SEEDS)} strands={N_STRANDS} d={num(D_STRAND)} mm N_REF={num(N_REF)} "
          f"EPS_REF={num(EPS_REF)} K_FAT={num(K_FAT)} SIGMA_LIFE={num(SIGMA_LIFE)} "
          f"R_C0={num(R_C0)} mOhm (declared toy values, not a datasheet)")
    print("No pull test and no thermal cycle: closed-form strand life and contact resistance")
    print("Regimes and parameters were written before the first run")
    print("rule: eps=d/(2*rho); N_i=N_REF*(EPS_REF/eps)^K_FAT*z_i; intact if N_i>cycles; "
          "R_c=R_C0*u*base*(1+growth)")
    for rho in (3.0, 6.0, 12.0):
        eps = D_STRAND / (2.0 * rho)
        life = N_REF * (EPS_REF / eps) ** K_FAT
        print(f"hand_calc rho={rho:.1f} mm: eps=0.16/(2*{rho:.1f})={num(eps)}; "
              f"median life N_REF*(EPS_REF/eps)^2={num(life)} cycles")
    print(f"hand_calc if only 3 of 19 strands remain the strand part of the resistance is "
          f"19/3 = {num(N_STRANDS / 3.0)} times the intact value")
    for regime in REGIMES:
        report(regime)
    print("alternative parameters (declared before the run, same seeds, not adopted):")
    alt_a = arm_col("flex", "A_solder_bare", k_fat=3.0)
    alt_b = arm_col("flex", "B_crimp_good", k_fat=3.0)
    print(f"  flex K_FAT=3.0: paired B-A intact: "
          f"{verdict(col(alt_b, 'intact'), col(alt_a, 'intact'))}")
    alt_a4 = arm_col("flex", "A_solder_bare", rho=4.0)
    alt_b2 = arm_col("flex", "B_crimp_good")
    print(f"  flex A rho=4.0 mm: paired B-A intact: "
          f"{verdict(col(alt_b2, 'intact'), col(alt_a4, 'intact'))}")
    alt_c = arm_col("static", "C_crimp_under", ox=0.1)
    alt_d = arm_col("static", "D_solder_relief")
    print(f"  static OX_PER_KHOUR=0.1: paired C-D contact_mohm: "
          f"{verdict(col(alt_c, 'contact_mohm'), col(alt_d, 'contact_mohm'))}")
    print("No universal winner: a good crimp and a relieved solder joint both survive this flex; "
          "the unrelieved solder joint and the under-crimp are the losers here")
    print("Crimp tool / IPC-A-610 inspection / pull test: 本页未运行; "
          "Wikipedia Crimp (joining) statements 以原文为准")


if __name__ == "__main__":
    main()
