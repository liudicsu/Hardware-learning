#!/usr/bin/env python3
"""NTC thermistor as an inrush-current limiter on a robot's 24 V DC bus.

Synthetic lumped electrical + one-node thermal model, stdlib only,
deterministic.  Not a manufacturer NTC curve, not SPICE, not an IEC 61000 lab.
Every value is a declared toy parameter, not a datasheet value.  A real PSU /
NTC disc / fuse: 本页未运行.  Not the lesson's fuse I2t certification text and
not the coulomb SoC + derate toy.  Wikipedia "Inrush current" and "Inrush
current limiter" statements are 以原文为准 and are not toy outputs.

Model.  V_S = 24.0 V ideal DC source switched on at t = 0; R_SRC = 0.05 ohm
(source + wiring + capacitor ESR); C_BUS = 2200e-6 F initially discharged; a
resistive load R_LOAD = 12.0 ohm across the capacitor.  The limiter resistance
R_lim is in series between source and capacitor.  Each electrical step holds
R_lim constant: R_s = R_SRC + R_lim; v_inf = V_S*R_LOAD/(R_s + R_LOAD);
tau = C_BUS*R_s*R_LOAD/(R_s + R_LOAD); v_c <- v_inf + (v_c - v_inf) *
exp(-DT/tau); line current i = (V_S - v_c)/R_s.  The NTC is
R(T) = R25*exp(BETA*(1/T - 1/T25)) with R25 = 5.0 ohm, BETA = 3500 K,
T25 = 298.15 K.  One thermal node: C_TH dT/dt = i^2 R(T) - (T - T_amb)/R_TH
with R_TH = 60.0 K/W, C_TH = 0.5 J/K, Euler on the same DT.  DT = 2e-6 s for
WINDOW = 0.05 s.  Peak current is the largest line current in the window and
the first sample at t = 0 counts.  I2t is the trapezoid integral of i^2 over
the window; a declared fuse budget I2T_BUDGET = 1.0 A^2 s gives fuse_ok = 1 if
I2t <= budget else 0.  Steady state solves T = T_amb + I^2 R(T) R_TH with
I = V_S/(R_SRC + R(T) + R_LOAD) by bisection on T in [T_amb, 800 K], then
v_drop_ss = I*R_lim_ss and p_ss = I^2*R_lim_ss.

Arms:
  A_none     : no limiter (R_lim = 0).
  B_ntc      : series NTC, R(T) from its temperature.
  C_fixed    : fixed resistor equal to the NTC cold resistance (R25 times the
               same tolerance factor), never falls.
  D_bypass   : the same NTC, switched out by a relay after start (ideal short
               in steady state: v_drop_ss = 0, p_ss = 0).  Declared model
               assumption: the bypassed NTC carries no current and has cooled
               to ambient before any restart.

Common random numbers: for each (regime, seed) draw ONCE from
random.Random(f"{regime}/{seed}") a capacitor factor uniform(0.9, 1.1), a
source-resistance factor uniform(0.8, 1.2), an NTC/fixed-resistor tolerance
factor uniform(0.9, 1.1) (applied to R25 for B, C and D) and an ambient
temperature T_amb = 298.15 + uniform(-3, 3) K; shared by all arms.

Regimes: "cold_start" (NTC starts at T_amb); "hot_restart" (declared model
assumption, not a Wikipedia value: supply off and on again with the capacitor
discharged but no cooling time, so B's NTC starts at its steady-state
temperature, while D's NTC starts at T_amb because it was bypassed and C has no
temperature dependence); "heavy_load" (cold start with R_LOAD = 6.0 ohm).

Metrics per seed: peak_a, i2t, fuse_ok, v_drop_ss, p_ss.

Pairs, every metric in every regime: A-B, C-B, B-D.

Regimes and parameters were written before the first run.  Pre-declared
expectations (not tuned; print whatever comes):
  cold_start  : A consistently higher peak than B and A fails the fuse budget;
                C vs B peak may near-tie; C consistently wastes more p_ss than
                B - keep; B keeps a residual v_drop_ss and p_ss above D's
                bypass - keep.
  hot_restart : B's peak rises toward A and B may fail the fuse budget - keep
                as it comes; D keeps its cold-start peak.
  heavy_load  : A fails the fuse budget; C consistently wastes more p_ss than
                B - keep; B residual above D - keep.

Alternatives (same seeds, declared before the run, not adopted):
  cold_start with R25 = 10.0 ohm (paired C-B p_ss);
  hot_restart with R_TH = 30.0 K/W (paired A-B peak_a);
  cold_start with I2T_BUDGET = 0.25 (paired A-B fuse_ok).
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
V_S = 24.0
R_SRC = 0.05
C_BUS = 2200e-6
R_LOAD = 12.0
R_LOAD_HEAVY = 6.0
R25 = 5.0
BETA = 3500.0
T25 = 298.15
T_AMB_NOM = 298.15
R_TH = 60.0
C_TH = 0.5
DT = 2e-6
WINDOW = 0.05
I2T_BUDGET = 1.0
STEPS = int(WINDOW / DT)

REGIMES = ("cold_start", "hot_restart", "heavy_load")
ARMS = ("A_none", "B_ntc", "C_fixed", "D_bypass")

DECLARED = {
    "cold_start": "A consistently higher peak than B and A fails the fuse "
                  "budget; C vs B peak may near-tie; C consistently wastes "
                  "more p_ss than B - keep; B keeps a residual v_drop_ss and "
                  "p_ss above D's bypass - keep",
    "hot_restart": "B's peak rises toward A and B may fail the fuse budget - "
                   "keep as it comes; D keeps its cold-start peak",
    "heavy_load": "A fails the fuse budget; C consistently wastes more p_ss "
                  "than B - keep; B residual above D - keep",
}

METRICS = ("peak_a", "i2t", "fuse_ok", "v_drop_ss", "p_ss")
PAIRS = (("A_none", "B_ntc"),
         ("C_fixed", "B_ntc"),
         ("B_ntc", "D_bypass"))


def shared_draws(regime, seed):
    """Common random numbers: one shared draw set per (regime, seed)."""
    rng = random.Random(f"{regime}/{seed}")
    cap_f = rng.uniform(0.9, 1.1)
    src_f = rng.uniform(0.8, 1.2)
    tol = rng.uniform(0.9, 1.1)
    t_amb = T_AMB_NOM + rng.uniform(-3.0, 3.0)
    return cap_f, src_f, tol, t_amb


def ntc_r(t, r25_eff):
    return r25_eff * math.exp(BETA * (1.0 / t - 1.0 / T25))


def steady_ntc(t_amb, r25_eff, r_load, r_src, r_th):
    lo, hi = t_amb, 800.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        r = ntc_r(mid, r25_eff)
        i = V_S / (r_src + r + r_load)
        if mid - t_amb - i * i * r * r_th > 0.0:
            hi = mid
        else:
            lo = mid
    t_eq = 0.5 * (lo + hi)
    r_eq = ntc_r(t_eq, r25_eff)
    i_eq = V_S / (r_src + r_eq + r_load)
    return t_eq, r_eq, i_eq


def simulate(kind, r25_eff, t_start, t_amb, r_load, cap, r_src, r_th):
    v_c = 0.0
    t = t_start
    peak = 0.0
    i2t = 0.0
    for _ in range(STEPS):
        if kind == "ntc":
            r_lim = ntc_r(t, r25_eff)
        elif kind == "fixed":
            r_lim = r25_eff
        else:
            r_lim = 0.0
        r_s = r_src + r_lim
        i_start = (V_S - v_c) / r_s
        if i_start > peak:
            peak = i_start
        v_inf = V_S * r_load / (r_s + r_load)
        tau = cap * r_s * r_load / (r_s + r_load)
        v_next = v_inf + (v_c - v_inf) * math.exp(-DT / tau)
        i_next = (V_S - v_next) / r_s
        if i_next > peak:
            peak = i_next
        i2t += 0.5 * DT * (i_start * i_start + i_next * i_next)
        if kind == "ntc":
            t += DT * (i_start * i_start * r_lim - (t - t_amb) / r_th) / C_TH
        v_c = v_next
    return peak, i2t


def run_arm(arm, regime, seed, r25=R25, r_th=R_TH, budget=I2T_BUDGET):
    cap_f, src_f, tol, t_amb = shared_draws(regime, seed)
    r_load = R_LOAD_HEAVY if regime == "heavy_load" else R_LOAD
    cap = C_BUS * cap_f
    r_src = R_SRC * src_f
    r25_eff = r25 * tol
    if arm == "A_none":
        peak, i2t = simulate("none", r25_eff, t_amb, t_amb,
                             r_load, cap, r_src, r_th)
        v_drop, p_ss = 0.0, 0.0
    elif arm == "C_fixed":
        peak, i2t = simulate("fixed", r25_eff, t_amb, t_amb,
                             r_load, cap, r_src, r_th)
        i_ss = V_S / (r_src + r25_eff + r_load)
        v_drop = i_ss * r25_eff
        p_ss = i_ss * i_ss * r25_eff
    else:
        if regime == "hot_restart" and arm == "B_ntc":
            t_start = steady_ntc(t_amb, r25_eff, r_load, r_src, r_th)[0]
        else:
            t_start = t_amb
        peak, i2t = simulate("ntc", r25_eff, t_start, t_amb,
                             r_load, cap, r_src, r_th)
        if arm == "B_ntc":
            _, r_eq, i_eq = steady_ntc(t_amb, r25_eff, r_load, r_src, r_th)
            v_drop = i_eq * r_eq
            p_ss = i_eq * i_eq * r_eq
        else:
            v_drop, p_ss = 0.0, 0.0
    fuse_ok = 1 if i2t <= budget else 0
    return {"peak_a": peak, "i2t": i2t, "fuse_ok": fuse_ok,
            "v_drop_ss": v_drop, "p_ss": p_ss}


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


def collect(regime, **kw):
    return {arm: [run_arm(arm, regime, s, **kw) for s in SEEDS] for arm in ARMS}


def arm_col(regime, arm, **kw):
    return [run_arm(arm, regime, s, **kw) for s in SEEDS]


def col(rows, key):
    return [x[key] for x in rows]


def report(regime):
    res = collect(regime)
    print(f"{regime}:")
    print(f"  declared: {DECLARED[regime]}")
    for arm in ARMS:
        print(f"  {arm} " + " ".join(
            f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS))
    for a, b in PAIRS:
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: {verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("Synthetic NTC inrush-limiter toy; shared capacitor, source, tolerance and ambient "
          "draws; lumped electrical + one-node thermal model, not a manufacturer NTC curve, "
          "not SPICE, not an IEC 61000 lab")
    print(f"seeds={len(SEEDS)} V_S={num(V_S)} V R_SRC={num(R_SRC)} ohm C_BUS={num(C_BUS)} F "
          f"R25={num(R25)} ohm BETA={num(BETA)} K T25={num(T25)} K R_TH={num(R_TH)} K/W "
          f"C_TH={num(C_TH)} J/K (declared toy parameters, not datasheet values)")
    print("Every value is a declared toy parameter, not a datasheet value; "
          "real PSU / NTC disc / fuse: 本页未运行")
    print("Regimes and parameters were written before the first run")
    print("rule: R_s=R_SRC+R_lim; v_inf=V_S*R_LOAD/(R_s+R_LOAD); "
          "tau=C_BUS*R_s*R_LOAD/(R_s+R_LOAD); v_c<-v_inf+(v_c-v_inf)*exp(-DT/tau); "
          "i=(V_S-v_c)/R_s; C_TH*dT/dt=i^2*R(T)-(T-T_amb)/R_TH")
    print(f"hand_calc first-instant peak unprotected: V_S/R_SRC = 24/0.05 = "
          f"{num(V_S / R_SRC)} A")
    print(f"hand_calc first-instant peak cold NTC: V_S/(R_SRC+R25) = 24/5.05 = "
          f"{num(V_S / (R_SRC + R25))} A")
    print(f"hand_calc capacitor-charging I2t unprotected: V^2*C/(2R) = "
          f"24^2*0.0022/(2*0.05) = {num(V_S * V_S * C_BUS / (2.0 * R_SRC))} A^2 s")
    print(f"hand_calc capacitor-charging I2t through 5.05 ohm: V^2*C/(2R) = "
          f"24^2*0.0022/(2*5.05) = "
          f"{num(V_S * V_S * C_BUS / (2.0 * (R_SRC + R25)))} A^2 s")
    print(f"hand_calc energy into the capacitor: 0.5*C*V^2 = 0.5*0.0022*24^2 = "
          f"{num(0.5 * C_BUS * V_S * V_S)} J")
    print(f"hand_calc steady load current without a limiter: 24/(0.05+12) = "
          f"{num(V_S / (R_SRC + R_LOAD))} A")
    for regime in REGIMES:
        report(regime)
    print("alternative parameters (declared before the run, same seeds, not adopted):")
    alt_c = arm_col("cold_start", "C_fixed", r25=10.0)
    alt_b = arm_col("cold_start", "B_ntc", r25=10.0)
    print(f"  cold_start R25=10.0 ohm: paired C-B p_ss: "
          f"{verdict(col(alt_c, 'p_ss'), col(alt_b, 'p_ss'))}")
    alt_a = arm_col("hot_restart", "A_none", r_th=30.0)
    alt_b2 = arm_col("hot_restart", "B_ntc", r_th=30.0)
    print(f"  hot_restart R_TH=30.0 K/W: paired A-B peak_a: "
          f"{verdict(col(alt_a, 'peak_a'), col(alt_b2, 'peak_a'))}")
    alt_a2 = arm_col("cold_start", "A_none", budget=0.25)
    alt_b3 = arm_col("cold_start", "B_ntc", budget=0.25)
    print(f"  cold_start I2T_BUDGET=0.25: paired A-B fuse_ok: "
          f"{verdict(col(alt_a2, 'fuse_ok'), col(alt_b3, 'fuse_ok'))}")
    print("No universal winner: the NTC cuts the cold turn-on peak at a small steady cost, "
          "a fixed resistor cuts it at a large one, and a hot NTC limits little unless it has "
          "cooled or was bypassed")
    print("Real PSU / NTC disc / fuse: 本页未运行; Wikipedia Inrush current and Inrush current "
          "limiter statements 以原文为准; every value is a declared toy parameter")


if __name__ == "__main__":
    main()
