#!/usr/bin/env python3
"""Interference (press / shrink) fit vs clearance fit on one shared shaft and hub.

Synthetic, stdlib only.  Not this lesson's CAD *interference check* (that finds overlapping
volume in an assembly and treats it as a clash to fix); here the overlap is the design intent,
the allowance.  Not the GD&T tolerance-stack toy above (no dimension chain, no RSS).  Real press,
oven, strain gauges or a torque test: 本页未运行.  Wikipedia "Interference fit" statements are
以原文为准; the pressure / stress formulas below are a textbook-style stand-in, not a design code.

Part: steel shaft, nominal diameter D_NOM mm, in a steel hub of outer diameter D_OUT mm over an
engaged length L_ENG mm.  Diameters are measured at the same (room) temperature after assembly.
Model assumptions (a stand-in):
  delta = d_shaft - d_hole                     (> 0 interference, < 0 clearance)
  p     = E * delta / (2 * D_NOM) * (1 - (D_NOM / D_OUT)^2)   contact pressure, MPa
          (thick-walled hub on a solid shaft of the same material, elastic)
  hoop  = p * (D_OUT^2 + D_NOM^2) / (D_OUT^2 - D_NOM^2)       hub bore hoop stress, MPa
  F     = MU * p * pi * D_NOM * L_ENG                          axial force to press / to slide, N
  T     = F * D_NOM / 2 / 1000                                 friction holding torque, N m
If hoop > SIGMA_Y the hub yields: the pressure that the joint keeps is capped at the value that
gives hoop = SIGMA_Y, and the part is counted as yielded (a stand-in for a damaged hub).
Shrink fitting: the hub is heated by DT_OVEN before assembly; its bore grows by
ALPHA * DT_OVEN * D_NOM.  The press force is computed from the interference that remains while
hot, max(0, delta - ALPHA * DT_OVEN * D_NOM); once the hub cools back, delta is the full value.
No integration step: every quantity is a closed-form value per part and per load cycle; there is
no time stepping, so there is no step-size criterion to state (a test checks that the output does
not depend on any step).
Arms (same nominal size, same tolerance draws):
  A_clear   clearance fit, hole ALLOW_A larger than the shaft; held by a set screw whose friction
            torque is drawn per part (N(SET_MEAN, SET_SD) N m); no oven.
  B_fit     specified light interference ALLOW_B, shrink-fitted with the regime's DT_OVEN.
  C_heavy   excessive interference ALLOW_C, same DT_OVEN as B.
Common random numbers: for each (regime, seed), PARTS parts are drawn once: a uniform position in
the tolerance band for the shaft and for the hole (each +-TOL mm around its arm's nominal), the
set-screw torque, and CYCLES load torques per part from N(load mean, load sd) clipped at 0.  The
same draws are used by all three arms.
Metrics per seed: slip % (load cycles whose torque exceeds the holding torque), press force in kN
(mean over parts), hoop / SIGMA_Y (mean over parts), yielded % of parts.
Regimes and expectations, written before the first run:
  loaded_vibration  load 30 +- 15 N m, DT_OVEN 150 K   B consistent win over A on slip
  no_load           load 0,            DT_OVEN 150 K   A and B tie on slip and press force
  press_no_oven     load 30 +- 15 N m, DT_OVEN 0 K     B loses to A on press force (pressed cold);
                                                       C loses to B on stress (yields) and force
  C never beats B on stress or press force.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
D_NOM = 20.0      # mm
D_OUT = 40.0      # mm
L_ENG = 15.0      # mm
E = 200000.0      # MPa
MU = 0.15
SIGMA_Y = 250.0   # MPa, hub yield stand-in
ALPHA = 12e-6     # 1/K, steel
TOL = 0.005       # mm, +- band on each diameter
ALLOW_A = -0.020  # mm, clearance (hole larger)
ALLOW_B = 0.025   # mm, light interference
ALLOW_C = 0.070   # mm, excessive interference
SET_MEAN, SET_SD = 40.0, 8.0  # N m, set screw friction torque
PARTS = 20
CYCLES = 200
NUM_ZERO = 1e-9
ARMS = ("A_clear", "B_fit", "C_heavy")
ALLOW = {"A_clear": ALLOW_A, "B_fit": ALLOW_B, "C_heavy": ALLOW_C}
# name: (load mean N m, load sd N m, DT_OVEN K); written before the first run
REGIMES = {
    "loaded_vibration": (30.0, 15.0, 150.0),
    "no_load": (0.0, 0.0, 150.0),
    "press_no_oven": (30.0, 15.0, 0.0),
}
STREAM = {"loaded_vibration": 0, "no_load": 1, "press_no_oven": 2}

K_P = E / (2.0 * D_NOM) * (1.0 - (D_NOM / D_OUT) ** 2)          # MPa per mm of interference
K_HOOP = (D_OUT ** 2 + D_NOM ** 2) / (D_OUT ** 2 - D_NOM ** 2)  # hoop / p
P_YIELD = SIGMA_Y / K_HOOP                                       # pressure at first yield


def pressure(delta):
    return K_P * delta if delta > 0.0 else 0.0


def axial_force(p):
    return MU * p * math.pi * D_NOM * L_ENG


def torque(p):
    return axial_force(p) * D_NOM / 2.0 / 1000.0


def shared_draws(regime, seed):
    rng = random.Random(1000 * STREAM[regime] + seed)
    mean, sd, _ = REGIMES[regime]
    parts = []
    for _ in range(PARTS):
        u_shaft, u_hole = rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)
        t_set = max(0.0, rng.gauss(SET_MEAN, SET_SD))
        loads = [max(0.0, rng.gauss(mean, sd)) if sd > 0 else mean for _ in range(CYCLES)]
        parts.append((u_shaft, u_hole, t_set, loads))
    return parts


def part_result(arm, part, dt_oven):
    u_shaft, u_hole, t_set, loads = part
    d_shaft = D_NOM + ALLOW[arm] / 2.0 + TOL * u_shaft
    d_hole = D_NOM - ALLOW[arm] / 2.0 + TOL * u_hole
    delta = d_shaft - d_hole                      # after the hub has cooled back
    oven = dt_oven if arm != "A_clear" else 0.0
    hot_delta = delta - ALPHA * oven * D_NOM      # interference left while the hub is hot
    press = axial_force(pressure(hot_delta))
    p = pressure(delta)
    hoop = K_HOOP * p
    yielded = hoop > SIGMA_Y
    hold = t_set if delta <= 0.0 else torque(min(p, P_YIELD))
    slips = sum(1 for q in loads if q > hold)
    return {"delta": delta, "hot": hot_delta, "slip": 100.0 * slips / len(loads), "press": press / 1000.0,
            "stress": hoop / SIGMA_Y, "yield": 100.0 if yielded else 0.0}


def evaluate(arm, regime, parts):
    dt_oven = REGIMES[regime][2]
    rs = [part_result(arm, pt, dt_oven) for pt in parts]
    out = {k: sum(r[k] for r in rs) / len(rs) for k in ("slip", "press", "stress", "yield")}
    out["dmin"] = min(r["delta"] for r in rs)
    out["dmax"] = max(r["delta"] for r in rs)
    out["hotmax"] = max(r["hot"] for r in rs)
    return out


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
    print("Synthetic shaft-hub fit: clearance + set screw vs light shrink fit vs excessive interference; not a CAD clash check, not GD&T")
    print(f"D_NOM={D_NOM} mm D_OUT={D_OUT} mm L_ENG={L_ENG} mm E={E:.0f} MPa MU={MU} SIGMA_Y={SIGMA_Y} MPa ALPHA={ALPHA} 1/K TOL=+-{TOL} mm parts={PARTS} cycles={CYCLES} seeds={len(SEEDS)}")
    print(f"allowance A={ALLOW_A} B={ALLOW_B} C={ALLOW_C} mm; p per mm of interference {K_P:.1f} MPa; hoop/p {K_HOOP:.4f}; p at first yield {P_YIELD:.2f} MPa")
    print(f"oven growth at 150 K: ALPHA*DT*D_NOM = {ALPHA * 150.0 * D_NOM:.4f} mm")
    print("no integration step: closed-form pressure, force and torque per part and per load cycle")
    print("regime arm slip_% press_kN hoop/yield yielded_% delta_min..max_mm hot_delta_max_mm  (mean+-sd over seeds)")
    for regime, (mean, sd, dt_oven) in REGIMES.items():
        print(f"{regime} (load {mean} +- {sd} N m; oven {dt_oven} K)")
        draws = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [evaluate(arm, regime, d) for d in draws] for arm in ARMS}
        for arm in ARMS:
            cols = ["{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in ("slip", "press", "stress", "yield")]
            dmin = min(r["dmin"] for r in res[arm])
            dmax = max(r["dmax"] for r in res[arm])
            hot = max(r["hotmax"] for r in res[arm])
            sign = "interference" if dmin > 0 else ("clearance" if dmax < 0 else "mixed")
            print(f"  {arm} " + " ".join(cols) + f" {dmin:+.4f}..{dmax:+.4f} ({sign}) {hot:+.4f}")
        for x, y in (("B_fit", "A_clear"), ("C_heavy", "B_fit")):
            for key in ("slip", "press", "stress"):
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[key] for r in res[x]], [r[key] for r in res[y]])}")
    print("No winner declared: interference holds by friction under load, costs press force without an oven, and too much of it yields the hub")
    print("Real press / oven / torque test: 本页未运行; Wikipedia Interference fit 以原文为准")


if __name__ == "__main__":
    main()
