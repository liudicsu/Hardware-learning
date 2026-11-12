#!/usr/bin/env python3
"""FDM build-orientation anisotropy: flatwise vs upright vs an isotropic guess.

Synthetic three-point-bending beam, stdlib only.  Not a tensile lab, not an
Instron run, not a modal-hammer test, not the pressure-advance corner toy on
this page and not a moisture / wet-nylon section.
Real printer / Instron / modal hammer: 本页未运行.  Rajkumar (arXiv
2202.05692) statements and MPa / GPa values 以论文为准; none of them is
reprinted below as a toy output.

What the cited paper body says (and what this toy keeps): PLA beams printed
flatwise, edgewise and upright were tested in three-point bending.  Upright
tends to much lower maximum flexural stress (the load opens the layer
lines, so the inter-layer bond carries it); flatwise tends to higher median
maximum flexural stress and higher flexural modulus; one edgewise cell
(zigzag infill) has the lowest flexural modulus.  The paper's beam-theory
equations, with P the load, L the span, w the width and t the thickness:
  sigma = 3 P L / (2 w t^2)        d = P L^3 / (48 E I)        I = w t^3 / 12

Common random numbers: for each (regime, seed) one load jitter, one shared
print-quality factor on strength and one on modulus are drawn once and
shared by every arm (same spool, same printer, same day).  Arms:
  A_flatwise  : strength S_FLAT, modulus E_FLAT
  B_upright   : strength S_UP (inter-layer bond), modulus E_UP
  C_isotropic : one number for every orientation (S_FLAT, E_FLAT) used to
                predict the upright part - the naive "datasheet" guess
  D_edgewise  : strength S_EDGE, modulus E_EDGE (the "print it on its side" rule)
The arms differ only in the orientation-dependent strength and modulus;
geometry and load are shared, so the peak stress is the same for every arm.
A part snaps iff sigma >= S; it survives iff sigma < S (strict).
No integration step: closed-form statics, no time stepping.

Regimes and parameters were written before the first run:
  light   : load well below every strength - A vs B snap flag tie (both
            survive); keep
  mid     : load between the upright and flatwise strengths - B consistent
            snaps where A holds; C (isotropic) misses the snap
  modulus : zigzag-like parameter set, light load - the edgewise rule D can
            lose on stiffness (deflects more than A); keep
All strengths and moduli are declared toy parameters, ordered after the
paper's qualitative statements; they are not the paper's measured values.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.  Toy values.
SPAN = 80.0       # mm, support span (toy)
WIDTH = 15.0      # mm, beam width (Rajkumar's 100 x 15 x 5 mm beam; 以论文为准)
THICK = 5.0       # mm, beam thickness
P_JITTER = 0.05   # +/- fraction on the load, shared
Q_JITTER = 0.08   # +/- fraction print quality on strength, shared
R_JITTER = 0.05   # +/- fraction print quality on modulus, shared
SETS = {
    # strengths in MPa, moduli in GPa (toy stand-ins, not paper values)
    "default": {"S": {"flat": 90.0, "edge": 85.0, "up": 55.0}, "E": {"flat": 3.2, "edge": 3.0, "up": 2.7}},
    "zigzag_like": {"S": {"flat": 80.0, "edge": 78.0, "up": 50.0}, "E": {"flat": 3.0, "edge": 2.2, "up": 2.5}},
}
REGIMES = {
    "light": {"p": 100.0, "set": "default"},
    "mid": {"p": 220.0, "set": "default"},
    "modulus": {"p": 100.0, "set": "zigzag_like"},
}
ARMS = ("A_flatwise", "B_upright", "C_isotropic", "D_edgewise")
ORIENT = {"A_flatwise": "flat", "B_upright": "up", "C_isotropic": "flat", "D_edgewise": "edge"}


def second_moment(w=WIDTH, t=THICK):
    return w * t ** 3 / 12.0


def peak_stress(p, span=SPAN, w=WIDTH, t=THICK):
    return 3.0 * p * span / (2.0 * w * t ** 2)


def deflection(p, e_gpa, span=SPAN, w=WIDTH, t=THICK):
    return p * span ** 3 / (48.0 * e_gpa * 1000.0 * second_moment(w, t))


def shared_draws(regime, seed):
    """Common random numbers: one load, one strength factor, one modulus factor."""
    rng = random.Random(f"{regime}/{seed}")
    dp = rng.uniform(-P_JITTER, P_JITTER)
    q = 1.0 + rng.uniform(-Q_JITTER, Q_JITTER)
    r = 1.0 + rng.uniform(-R_JITTER, R_JITTER)
    return REGIMES[regime]["p"] * (1.0 + dp), q, r


def run_arm(arm, regime, seed, span=SPAN, p_scale=1.0, s_up=None):
    p, q, r = shared_draws(regime, seed)
    p *= p_scale
    params = SETS[REGIMES[regime]["set"]]
    o = ORIENT[arm]
    s = params["S"][o]
    if o == "up" and s_up is not None:
        s = s_up
    strength, modulus = s * q, params["E"][o] * r
    sigma = peak_stress(p, span)
    return {"sigma": sigma, "util": sigma / strength, "snap": 1.0 if sigma >= strength else 0.0,
            "defl": deflection(p, modulus, span)}


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


METRICS = ("sigma", "util", "snap", "defl")


def collect(regime, **kw):
    return {arm: [run_arm(arm, regime, s, **kw) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [r[key] for r in rows]


def report(regime):
    cfg = REGIMES[regime]
    res = collect(regime)
    print(f"{regime} (P_nom={num(cfg['p'])} N, sigma_nom={num(peak_stress(cfg['p']))} MPa, parameter set {cfg['set']}):")
    for arm in ARMS:
        rows = res[arm]
        print(f"  {arm} " + " ".join(f"{key} {fmt_pair(*mean_sd(col(rows, key)))}" for key in METRICS)
              + f" snaps_on {int(sum(col(rows, 'snap')))}/5")
    for a, b, keys in (("B_upright", "A_flatwise", ("snap", "util")), ("B_upright", "C_isotropic", ("snap", "util")),
                       ("D_edgewise", "A_flatwise", ("defl", "util")), ("A_flatwise", "B_upright", ("sigma",))):
        for key in keys:
            print(f"  paired {a[0]}-{b[0]} {key}: {verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("Synthetic FDM build-orientation toy; shared geometry, load and print-quality draws; not a lab measurement")
    print(f"seeds={len(SEEDS)} SPAN={num(SPAN)} mm WIDTH={num(WIDTH)} mm THICK={num(THICK)} mm P_JITTER=+-{num(P_JITTER)} "
          f"Q_JITTER=+-{num(Q_JITTER)} R_JITTER=+-{num(R_JITTER)} (declared toy parameters)")
    for name, ps in SETS.items():
        print(f"set {name}: S flat/edge/up = {num(ps['S']['flat'])}/{num(ps['S']['edge'])}/{num(ps['S']['up'])} MPa; "
              f"E flat/edge/up = {num(ps['E']['flat'])}/{num(ps['E']['edge'])}/{num(ps['E']['up'])} GPa (toy stand-ins, not paper values)")
    print("No integration step: closed-form statics, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print("rule: snaps iff sigma >= S; survives iff sigma < S (strict); sigma = 3PL/(2wt^2), d = PL^3/(48EI), I = wt^3/12")
    # Labelled hand calculation on one orientation, printed.
    i2 = second_moment()
    print(f"hand_calc flatwise P=220.0 N L=80.0 mm w=15.0 mm t=5.0 mm: sigma=3*220*80/(2*15*5^2)={num(peak_stress(220.0))} MPa; "
          f"util vs S_FLAT 90.0 MPa = {num(peak_stress(220.0) / 90.0)}; vs S_UP 55.0 MPa = {num(peak_stress(220.0) / 55.0)}")
    print(f"hand_calc I=15*5^3/12={num(i2)} mm^4; d at P=100.0 N, E=3.2 GPa: 100*80^3/(48*3200*{num(i2)})={num(deflection(100.0, 3.2))} mm")
    s_eq = peak_stress(220.0)
    print(f"boundary_rule: S=sigma={num(s_eq)} MPa -> snap={1 if s_eq >= s_eq else 0} (equality snaps); "
          f"S=sigma+1e-6 -> snap={1 if s_eq >= s_eq + 1e-6 else 0}")
    for regime in REGIMES:
        report(regime)
    base = collect("mid")
    print("alternative SPAN=60.0 mm on mid (same seeds; lower peak stress at the same load):")
    alt = collect("mid", span=60.0)
    print(f"  B_upright@alt snaps_on {int(sum(col(alt['B_upright'], 'snap')))}/5 (default {int(sum(col(base['B_upright'], 'snap')))}/5)")
    print(f"  paired B-A snap@alt: {verdict(col(alt['B_upright'], 'snap'), col(alt['A_flatwise'], 'snap'))}")
    print("alternative S_UP=65.0 MPa on mid (same seeds; a better inter-layer bond):")
    alt = collect("mid", s_up=65.0)
    print(f"  B_upright@alt snaps_on {int(sum(col(alt['B_upright'], 'snap')))}/5")
    print(f"  paired B-A snap@alt: {verdict(col(alt['B_upright'], 'snap'), col(alt['A_flatwise'], 'snap'))}")
    print("alternative load x0.80 on mid (same seeds; P_nom 176.0 N):")
    alt = collect("mid", p_scale=0.80)
    print(f"  B_upright@alt snaps_on {int(sum(col(alt['B_upright'], 'snap')))}/5")
    print(f"  paired B-A snap@alt: {verdict(col(alt['B_upright'], 'snap'), col(alt['A_flatwise'], 'snap'))}")
    print("No winner declared: flatwise is the safer default for bending here, upright snaps first at the layer lines, "
          "an isotropic guess hides that, and the side-on rule can cost stiffness")
    print("Real printer / Instron / modal hammer: 本页未运行; Rajkumar (arXiv 2202.05692) values 以论文为准")


if __name__ == "__main__":
    main()
