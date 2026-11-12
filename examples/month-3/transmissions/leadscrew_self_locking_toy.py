#!/usr/bin/env python3
"""Leadscrew efficiency and self-locking: steep lead vs fine lead vs vibrated fine lead.

Synthetic square-thread statics, stdlib only.  Not a jack, not a printer Z
axis, not a dyno and not the gear-efficiency-under-load toy on this page.
Real leadscrew / jack / printer axis: 本页未运行.  Wikipedia Leadscrew
statements 以原文为准.

What the Wikipedia Leadscrew "Mechanics" / "Efficiency" body says (and what
this toy keeps): unwrap one revolution of a square thread (thread angle 0),
  T_raise = F*dm/2 * tan(phi + lambda)
  T_lower = F*dm/2 * tan(phi - lambda)
with lead angle lambda = atan(l / (pi*dm)) and friction angle phi = atan(mu).
The screw is self-locking when mu > tan(lambda), equivalently phi > lambda.
Efficiency = tan(lambda) / tan(phi + lambda).  The self-locking property is
not absolute: under vibration or shock the effective coefficient of friction
may drop to dynamic levels and the screw can back-drive unexpectedly.

Sign convention: T_lower > 0 means torque must be applied to lower the load,
so the screw holds the load by itself (self-locking).  T_lower < 0 means the
load back-drives the screw.  At T_lower == 0 (phi == lambda exactly) the
screw is on the boundary and is NOT counted as self-locking: holds iff
phi > lambda, strictly.

Common random numbers: for each (regime, seed) one static-mu jitter and one
load jitter are drawn once and shared by every arm.  Arms:
  A_steep    : coarse lead LEAD_A, static mu
  B_fine     : fine lead LEAD_B (designed so phi > lambda at MU_NOM), static mu
  C_vibrated : the same fine lead LEAD_B, effective mu = static mu * VIB_FACTOR
The arms differ only in the lead (A vs B) or only in the effective mu (B vs C).
No integration step: closed-form statics, no ODE, no time step.

Regimes and parameters were written before the first run:
  nominal    : LEAD_A=10 mm, LEAD_B=2 mm
               - B consistent holds where A back-drives (T_lower sign); keep
               - B pays for it in efficiency: a trade, not a universal win
               - C (vibrated mu) consistent loss of the lock vs B; keep
  borderline : LEAD_B chosen so tan(lambda) = MU_NOM exactly (phi = lambda
               at the nominal mu); the hold depends on the sign of the mu
               jitter - B vs A on the hold flag may near-tie; keep
Friction values are declared model parameters, not a measured nut.  MU_NOM
sits inside the steel-on-bronze dry range of Wikipedia's thread-friction
table (以原文为准); VIB_FACTOR is a toy parameter, not a documented value.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared model parameters, written before the first run.  Toy values.
F_NOM = 500.0         # N, axial load
F_JITTER = 0.10       # +/- fraction, uniform, shared across arms
DM = 0.010            # m, mean thread diameter
MU_NOM = 0.15         # static thread friction (toy; inside Wikipedia's 0.15-0.23 dry steel/bronze row)
MU_JITTER = 0.03      # +/- absolute, uniform, shared across arms
VIB_FACTOR = 0.30     # effective mu under vibration = static mu * VIB_FACTOR (toy)
LEAD_A = 0.010        # m, steep lead
LEAD_B = 0.002        # m, fine lead

ARMS = ("A_steep", "B_fine", "C_vibrated")
REGIMES = {
    "nominal": {"lead_a": LEAD_A, "lead_b": LEAD_B},
    "borderline": {"lead_a": LEAD_A, "lead_b": math.pi * DM * MU_NOM},
}


def lead_angle(lead, dm=DM):
    return math.atan(lead / (math.pi * dm))


def screw(force, lead, mu, dm=DM, half_angle=0.0):
    """Square thread (half_angle=0) or Wikipedia's sec(alpha) compensation."""
    lam = lead_angle(lead, dm)
    mus = mu / math.cos(half_angle)
    phi = math.atan(mus)
    t_raise = force * dm / 2.0 * (mus + math.tan(lam)) / (1.0 - mus * math.tan(lam))
    t_lower = force * dm / 2.0 * (mus - math.tan(lam)) / (1.0 + mus * math.tan(lam))
    eta = force * lead / (2.0 * math.pi * t_raise)
    return {"lam": lam, "phi": phi, "t_raise": t_raise, "t_lower": t_lower,
            "eta": eta, "holds": 1.0 if phi > lam else 0.0}


def shared_draws(regime, seed):
    """Common random numbers: one mu jitter and one load jitter per (regime, seed)."""
    rng = random.Random(f"{regime}/{seed}")
    du = rng.uniform(-MU_JITTER, MU_JITTER)
    df = rng.uniform(-F_JITTER, F_JITTER)
    return MU_NOM + du, F_NOM * (1.0 + df)


def run_arm(arm, regime, seed, vib=VIB_FACTOR, half_angle=0.0, mu_nom=MU_NOM):
    mu, force = shared_draws(regime, seed)
    mu += mu_nom - MU_NOM
    cfg = REGIMES[regime]
    if arm == "A_steep":
        return screw(force, cfg["lead_a"], mu, half_angle=half_angle)
    if arm == "B_fine":
        return screw(force, cfg["lead_b"], mu, half_angle=half_angle)
    return screw(force, cfg["lead_b"], mu * vib, half_angle=half_angle)


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


METRICS = ("eta", "t_raise", "t_lower", "holds")


def collect(regime, **kw):
    return {arm: [run_arm(arm, regime, s, **kw) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [r[key] for r in rows]


def report(regime):
    cfg = REGIMES[regime]
    res = collect(regime)
    lam_a, lam_b = math.degrees(lead_angle(cfg["lead_a"])), math.degrees(lead_angle(cfg["lead_b"]))
    mus = [shared_draws(regime, s)[0] for s in SEEDS]
    print(f"{regime} (LEAD_A={cfg['lead_a'] * 1000:.4f} mm lambda_A={lam_a:.4f} deg; "
          f"LEAD_B={cfg['lead_b'] * 1000:.4f} mm lambda_B={lam_b:.4f} deg; tan(lambda_B)={math.tan(math.radians(lam_b)):.4f}):")
    print("  static mu per seed: " + " ".join(f"{m:.4f}" for m in mus))
    for arm in ARMS:
        rows = res[arm]
        parts = []
        for key in METRICS:
            m, s = mean_sd(col(rows, key))
            parts.append(f"{key} {fmt_pair(m, s)}")
        print(f"  {arm} " + " ".join(parts) + f" holds_on {int(sum(col(rows, 'holds')))}/5")
    flag_ok = all((r["phi"] > r["lam"]) == (r["holds"] == 1.0) and ((r["t_lower"] > 0) == (r["holds"] == 1.0))
                  for arm in ARMS for r in res[arm])
    print(f"  self_lock_flag_check: holds == (phi > lambda) == (T_lower > 0) on every arm and seed: {flag_ok}")
    for key in METRICS:
        print(f"  paired B-A {key}: {verdict(col(res['B_fine'], key), col(res['A_steep'], key))}")
    for key in ("t_lower", "holds", "eta"):
        print(f"  paired C-B {key}: {verdict(col(res['C_vibrated'], key), col(res['B_fine'], key))}")
    return res


def main():
    print("Synthetic square-thread leadscrew toy; shared mu/load draws; not a jack or printer axis measurement")
    print(f"seeds={len(SEEDS)} F_NOM={F_NOM:.1f} N (+-{F_JITTER * 100:.0f} %) DM={DM * 1000:.1f} mm "
          f"MU_NOM={MU_NOM:.2f} (+-{MU_JITTER:.2f}) VIB_FACTOR={VIB_FACTOR:.2f} (declared toy parameters, not a measured nut)")
    print("No integration step: closed-form statics, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print("rule: self-locking iff phi > lambda (strict), i.e. mu > tan(lambda); T_lower > 0 holds, T_lower < 0 back-drives")
    # Labelled hand calculation on one (lambda, mu), printed.
    h = screw(F_NOM, LEAD_B, MU_NOM)
    print(f"hand_calc F={F_NOM:.1f} N dm={DM * 1000:.1f} mm l={LEAD_B * 1000:.1f} mm mu={MU_NOM:.2f}: "
          f"lambda=atan({LEAD_B * 1000:.1f}/(pi*{DM * 1000:.1f}))={math.degrees(h['lam']):.4f} deg "
          f"phi=atan({MU_NOM:.2f})={math.degrees(h['phi']):.4f} deg")
    print(f"hand_calc T_raise={F_NOM:.1f}*{DM:.3f}/2*tan({math.degrees(h['phi'] + h['lam']):.4f} deg)={h['t_raise']:.4f} N*m "
          f"T_lower={F_NOM:.1f}*{DM:.3f}/2*tan({math.degrees(h['phi'] - h['lam']):.4f} deg)={h['t_lower']:.4f} N*m "
          f"eta=tan(lambda)/tan(phi+lambda)={h['eta']:.4f}")
    a = screw(F_NOM, LEAD_A, MU_NOM)
    print(f"hand_calc steep l={LEAD_A * 1000:.1f} mm: lambda={math.degrees(a['lam']):.4f} deg > phi -> "
          f"T_lower={a['t_lower']:.4f} N*m (back-drives) eta={a['eta']:.4f}")
    v = screw(F_NOM, LEAD_B, MU_NOM * VIB_FACTOR)
    print(f"hand_calc vibrated mu={MU_NOM * VIB_FACTOR:.4f} < tan(lambda_B)={math.tan(h['lam']):.4f} -> "
          f"T_lower={v['t_lower']:.4f} N*m (back-drives)")
    lb = REGIMES["borderline"]["lead_b"]
    tl = math.tan(lead_angle(lb))
    eq = screw(F_NOM, lb, tl)
    above = screw(F_NOM, lb, tl + 1e-6)
    below = screw(F_NOM, lb, tl - 1e-6)
    print(f"boundary_rule: lead={lb * 1000:.4f} mm, mu=tan(lambda)={tl:.4f}: T_lower={num(abs(eq['t_lower']))} N*m holds={int(eq['holds'])} "
          f"(equality is the boundary, not self-locking); mu+1e-6 holds={int(above['holds'])}; mu-1e-6 holds={int(below['holds'])}")
    for regime in REGIMES:
        report(regime)
    print(f"alternative VIB_FACTOR=0.60 on nominal (same seeds; vibrated mu = 0.60 * static):")
    alt = collect("nominal", vib=0.60)
    base = collect("nominal")
    print(f"  C_vibrated@alt holds_on {int(sum(col(alt['C_vibrated'], 'holds')))}/5 (default {int(sum(col(base['C_vibrated'], 'holds')))}/5)")
    print(f"  paired C-B t_lower@alt: {verdict(col(alt['C_vibrated'], 't_lower'), col(alt['B_fine'], 't_lower'))}")
    print(f"  paired C-B holds@alt: {verdict(col(alt['C_vibrated'], 'holds'), col(alt['B_fine'], 'holds'))}")
    print(f"alternative MU_NOM=0.10 on nominal (same seeds; oiled-thread stand-in):")
    alt = collect("nominal", mu_nom=0.10)
    print(f"  B_fine@alt holds_on {int(sum(col(alt['B_fine'], 'holds')))}/5 C_vibrated@alt holds_on {int(sum(col(alt['C_vibrated'], 'holds')))}/5")
    print(f"  paired B-A holds@alt: {verdict(col(alt['B_fine'], 'holds'), col(alt['A_steep'], 'holds'))}")
    print(f"  paired C-B t_lower@alt: {verdict(col(alt['C_vibrated'], 't_lower'), col(alt['B_fine'], 't_lower'))}")
    alpha = math.radians(15.0)
    print(f"alternative trapezoidal half-angle alpha=15.0 deg on borderline (same seeds; mu*sec(alpha)={MU_NOM / math.cos(alpha):.4f} at MU_NOM):")
    alt = collect("borderline", half_angle=alpha)
    print(f"  B_fine@alt holds_on {int(sum(col(alt['B_fine'], 'holds')))}/5 (square thread default {int(sum(col(collect('borderline')['B_fine'], 'holds')))}/5)")
    print(f"  paired B-A holds@alt: {verdict(col(alt['B_fine'], 'holds'), col(alt['A_steep'], 'holds'))}")
    print("No winner declared: a steep lead is efficient but back-drives, a fine lead holds but wastes most input work, and vibration can undo the hold")
    print("Real leadscrew / jack / printer axis: 本页未运行; Wikipedia Leadscrew statements 以原文为准")


if __name__ == "__main__":
    main()
