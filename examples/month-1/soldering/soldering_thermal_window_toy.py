#!/usr/bin/env python3
"""Synthetic thermal window of a hand-soldered through-hole joint. Stdlib only.

Lumped RC stand-in (two nodes, linear conductances, explicit Euler):
  tip   C_TIP dTt/dt = P - G_c (Tt - Tj) - G_AIR (Tt - T_AMB)
        P = clip(K_HEAT (T_set - Tt), 0, P_MAX)   (station regulates on the tip node)
  joint C_j   dTj/dt = G_c (Tt - Tj) - G_loss (Tj - T_AMB)   while the iron touches,
        C_j   dTj/dt = -G_loss (Tj - T_AMB)                  after it is lifted.
  G_c = G_CLEAN * (1 - oxide) * flux: tip oxide cuts contact conductance; the tin
  bridge / flux is a scalar. Latent heat of the solder, wetting chemistry and
  intermetallic growth are not modelled.

Cold joint: the joint spends less than its wetting time t_wet above T_liq + 20 C.
Pad lift: the damage dose, integral of max(0, Tj - T_DMG) dt, exceeds the pad's
adhesion budget D_crit. Both thresholds are toy stand-ins, not IPC criteria.

Arms differ ONLY in iron-on dwell: A_short 1 s, B_lesson 3 s, C_long 8 s.
Common random numbers: per (regime, seed, joint) the pad heat capacity, pad loss
to the board, tip oxide, t_wet and D_crit are drawn once and shared by all arms.

Stability: explicit Euler on dx/dt = -M x needs DT < 2 / lambda_max(M); the toy
prints lambda_max for the stiffest joint (heater gain counted as a conductance)
and asserts the bound. Labels: tie = identical on every seed; |paired mean| <= sd
= near-tie / small gap within seed noise; |m| > sd = consistent gap (small if
|m| < 20 % of the smaller arm mean, else clear), always with a sign count.
Real iron / reflow oven: 本页未运行. Wikipedia / SparkFun numbers: 以原文为准.
"""
from __future__ import annotations

import math
import random

T_AMB = 25.0  # C
C_TIP = 1.2  # J/K, tip + heater lump
G_AIR = 0.01  # W/K, tip to air
K_HEAT = 4.0  # W/K, proportional heater gain on the tip node
P_MAX = 60.0  # W, heater limit (tip recovery)
G_CLEAN = 0.30  # W/K, clean tinned tip with a solder bridge
T_DMG = 260.0  # C, pad adhesive damage onset (toy stand-in)
DT = 0.001  # s, explicit Euler step
T_COOL = 6.0  # s simulated after the iron is lifted
SEEDS = (0, 1, 2, 3, 4)
JOINTS = 40
ARMS = (("A_short", 1.0), ("B_lesson", 3.0), ("C_long", 8.0))
# name, solder, T_liq, T_set, C_j range, G_loss range, oxide range, flux
REGIMES = (
    ("heavy_pad_underheat", "63/37", 183.0, 340.0, (0.30, 0.50), (0.05, 0.10), (0.0, 0.5), 1.0),
    ("small_pad_overheat", "SAC305", 217.0, 380.0, (0.10, 0.18), (0.02, 0.04), (0.0, 0.1), 1.0),
    ("matched_clean", "63/37", 183.0, 340.0, (0.12, 0.16), (0.02, 0.03), (0.0, 0.0), 1.0),
)


def shared_joint(regime: str, seed: int, j: int, spec: tuple) -> dict:
    """Common random numbers: one draw per (regime, seed, joint), shared by every arm."""
    _, _, _, _, cj, gl, ox, _ = spec
    rng = random.Random(f"{regime}|{seed}|{j}")
    return {
        "c_j": rng.uniform(*cj),
        "g_loss": rng.uniform(*gl),
        "oxide": rng.uniform(*ox),
        "t_wet": rng.uniform(0.3, 0.8),
        "d_crit": rng.uniform(300.0, 600.0),
    }


def lambda_max(c_j: float, g_c: float, g_loss: float) -> float:
    """Largest eigenvalue of M for the linearised two-node system (heater unsaturated)."""
    a = (g_c + G_AIR + K_HEAT) / C_TIP
    b = -g_c / C_TIP
    c = -g_c / c_j
    d = (g_c + g_loss) / c_j
    tr, det = a + d, a * d - b * c
    return tr / 2 + math.sqrt(max(tr * tr / 4 - det, 0.0))


def solder(dwell: float, t_liq: float, t_set: float, flux: float, jt: dict) -> dict:
    g_c = G_CLEAN * (1.0 - jt["oxide"]) * flux
    tt, tj = t_set, T_AMB
    above = dose = peak = 0.0
    n_on, n_tot = round(dwell / DT), round((dwell + T_COOL) / DT)
    for k in range(n_tot):
        touching = k < n_on
        q = g_c * (tt - tj) if touching else 0.0
        p = min(max(K_HEAT * (t_set - tt), 0.0), P_MAX)
        tt += DT * (p - q - G_AIR * (tt - T_AMB)) / C_TIP
        tj += DT * (q - jt["g_loss"] * (tj - T_AMB)) / jt["c_j"]
        if tj > t_liq + 20.0:
            above += DT
        dose += DT * max(0.0, tj - T_DMG)
        peak = max(peak, tj)
    return {"cold": above < jt["t_wet"], "lift": dose > jt["d_crit"], "dose": dose, "peak": peak}


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def sign_note(diffs: list[float], m: float) -> str:
    """How many seeds disagree in sign with the paired mean (zeros listed apart)."""
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m: float, s: float) -> str:
    """Paired mean+-sd; extra decimals when 4 would print a signed zero such as -0.0000."""
    if m != 0.0 and abs(m) < 5e-5:
        return f"{m:.6f}+-{s:.6f}"
    return f"{m:.4f}+-{s:.4f}"


def verdict(xa: list[float], xb: list[float]) -> str:
    """Paired xa - xb per seed: mean+-sd, then the label and the sign count."""
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(mean_sd(xa)[0], mean_sd(xb)[0]):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def reflow_reading(name: str, pts: list[tuple[float, float]], t_liq: float) -> str:
    """Read a piecewise-linear oven profile (time s, temp C): the four zones."""
    def temp(t: float) -> float:
        for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
            if t0 <= t <= t1:
                return y0 + (y1 - y0) * (t - t0) / (t1 - t0)
        return pts[-1][1]
    ts = [0.1 * i for i in range(int(pts[-1][0] / 0.1) + 1)]
    ys = [temp(t) for t in ts]
    ramp = max((y1 - y0) / 0.1 for y0, y1 in zip(ys, ys[1:]) if y0 < 150.0)
    soak = sum(0.1 for y in ys if 150.0 <= y < 200.0 and y < t_liq)
    tal = sum(0.1 for y in ys if y > t_liq)
    peak = max(ys)
    cool = -min((y1 - y0) / 0.1 for y0, y1 in zip(ys, ys[1:]))
    flags = []
    if ramp > 3.0:
        flags.append("ramp > 3 C/s")
    if not 60.0 <= soak <= 120.0:
        flags.append("soak outside 60-120 s")
    if tal < 30.0:
        flags.append("TAL < 30 s: cold/dull joint and void risk")
    if tal > 60.0:
        flags.append("TAL > 60 s: intermetallic / brittleness risk")
    if not 20.0 <= peak - t_liq <= 40.0:
        flags.append("peak not 20-40 C above liquidus")
    return (f"{name}: ramp {ramp:.2f} C/s, soak(150-200 C) {soak:.0f} s, TAL {tal:.0f} s, "
            f"peak {peak:.0f} C (+{peak - t_liq:.0f} over liquidus), cooling {cool:.2f} C/s -> "
            + ("; ".join(flags) if flags else "inside the guide windows"))


def main() -> None:
    print("Synthetic lumped-RC solder-joint toy; arms differ only in dwell; shared pad / tip draws; not a real iron")
    print(f"tip C={C_TIP} J/K K_heat={K_HEAT} W/K P_max={P_MAX:.0f} W G_clean={G_CLEAN} W/K; "
          f"T_dmg={T_DMG:.0f} C; wet above T_liq+20 C; DT={DT} s; seeds={len(SEEDS)} joints={JOINTS}")
    lam = lambda_max(0.10, G_CLEAN, 0.04)
    print(f"Euler stability: stiffest joint (C_j=0.10, G_c={G_CLEAN}, G_loss=0.04) lambda_max={lam:.3f} 1/s "
          f"-> need DT < 2/lambda_max = {2 / lam:.3f} s; DT={DT} s ok")
    assert DT < 2.0 / lam
    print("regime arm cold_joint_rate pad_lift_rate dose_Cs peak_C  (mean+-sd over seeds)")
    for spec in REGIMES:
        regime, alloy, t_liq, t_set, _, _, _, flux = spec
        per = {a: {"cold": [], "lift": [], "dose": [], "peak": []} for a, _ in ARMS}
        ox_cold, ox_good = [], []
        for seed in SEEDS:
            joints = [shared_joint(regime, seed, j, spec) for j in range(JOINTS)]
            for arm, dwell in ARMS:
                rs = [solder(dwell, t_liq, t_set, flux, jt) for jt in joints]
                if arm == "B_lesson":
                    for r, jt in zip(rs, joints):
                        (ox_cold if r["cold"] else ox_good).append(jt["oxide"])
                per[arm]["cold"].append(sum(r["cold"] for r in rs) / JOINTS)
                per[arm]["lift"].append(sum(r["lift"] for r in rs) / JOINTS)
                per[arm]["dose"].append(sum(r["dose"] for r in rs) / JOINTS)
                per[arm]["peak"].append(sum(r["peak"] for r in rs) / JOINTS)
        print(f"{regime} ({alloy}, T_liq={t_liq:.0f} C, set {t_set:.0f} C)")
        for arm, _ in ARMS:
            cells = [mean_sd(per[arm][k]) for k in ("cold", "lift", "dose", "peak")]
            print(f"  {arm} " + " ".join(f"{m:.4f}+-{s:.4f}" if k < 2 else f"{m:.2f}+-{s:.2f}"
                                         for k, (m, s) in enumerate(cells)))
        if ox_cold:
            print(f"  B_lesson cold joints: mean tip oxide {sum(ox_cold) / len(ox_cold):.3f} on {len(ox_cold)} cold "
                  f"vs {sum(ox_good) / len(ox_good):.3f} on {len(ox_good)} good joints (oxide cuts G_c)")
        for x, y in (("A_short", "B_lesson"), ("C_long", "B_lesson")):
            for k in ("cold", "lift", "dose"):
                print(f"  paired {x[0]}-{y[0]} {k}: {verdict(per[x][k], per[y][k])}")
    print("reflow profile reading (oven, not a hand iron; SAC305 T_liq=217 C; guide windows from Wikipedia, 以原文为准):")
    good = [(0, 25), (60, 150), (150, 180), (185, 245), (200, 245), (225, 210), (260, 90)]
    short = [(0, 25), (40, 150), (90, 180), (110, 232), (115, 232), (125, 210), (160, 90)]
    print("  " + reflow_reading("profile_ok", good, 217.0))
    print("  " + reflow_reading("profile_short", short, 217.0))
    print("No winner declared: the right dwell depends on the pad; a longer dwell rescues heavy pads but lifts small ones; "
          "rates are blind to fillet shape, intermetallic growth and component heating")
    print("Real iron / reflow oven: 本页未运行; Wikipedia / SparkFun numbers 以原文为准")


if __name__ == "__main__":
    main()
