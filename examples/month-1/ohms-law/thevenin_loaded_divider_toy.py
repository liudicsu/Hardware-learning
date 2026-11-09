#!/usr/bin/env python3
"""Synthetic Thevenin / Norton equivalent of a loaded divider. Stdlib only.

Network (linear resistors, ideal 5 V source, no source resistance):
  Vs --R1-- out --R2-- GND, load RL from out to GND. Nominal R1 = 10 kOhm,
  R2 = 4.7 kOhm (the lesson's divider), so Vth = 1.5986 V, Rth = R1||R2 = 3197 Ohm.

Truth: KCL at node out with the ACTUAL (toleranced) parts:
  (Vs - V)/R1 = V/R2 + V/RL   ->   V = (Vs/R1) / (1/R1 + 1/R2 + 1/RL)

Every arm predicts the loaded voltage from bench measurements of the unloaded
network, then is scored against that truth:
  A_voc_only   V_L = Voc                       (ignores Rth)
  B_thevenin   Vth = Voc; Rth from a second reading with a known 10 kOhm test
               resistor: Rth = Rtest_nominal * (Voc/Vtest - 1);
               V_L = Vth * RL / (Rth + RL)
  C_norton     In = short-circuit current read through an ammeter with a
               100 Ohm burden; Rn = Voc / In; V_L = In * (Rn || RL)

Common random numbers: per (seed, board) the actual R1, R2, RL and Rtest (1 %
parts, uniform) and the meter noise draws z1 (Voc), z2 (Vtest / Isc) are drawn
once and shared by every arm. The meter is otherwise ideal (no input loading).

Regimes (5 seeds x 32 boards): heavy_load RL = 3.3 kOhm (about Rth),
lesson_load RL = 10 kOhm, light_load RL = 10 MOhm (A is a near-tie / small gap).
No presumed winner. Real DMM / bench Thevenin lab: 本页未运行.
"""
from __future__ import annotations

import math
import random

VS = 5.0  # V, ideal source
R1_NOM = 10_000.0  # Ohm
R2_NOM = 4_700.0  # Ohm
RTEST_NOM = 10_000.0  # Ohm, known test resistor for the two-reading Rth method
TOL = 0.01  # 1 % parts, uniform
V_NOISE = 1e-3  # V, meter reading sd (about one count on a 2 V range)
I_NOISE = 1e-6  # A, meter reading sd (about one count on a 2 mA range)
R_BURDEN = 100.0  # Ohm, ammeter burden in series during the short-circuit reading
SEEDS = (0, 1, 2, 3, 4)
BOARDS = 32
ARMS = ("A_voc_only", "B_thevenin", "C_norton")
REGIMES = (("heavy_load", 3_300.0), ("lesson_load", 10_000.0), ("light_load", 10_000_000.0))


def thevenin(vs: float, r1: float, r2: float) -> tuple[float, float]:
    """Open-circuit voltage and resistance seen at `out` with the source zeroed."""
    return vs * r2 / (r1 + r2), r1 * r2 / (r1 + r2)


def truth_kcl(vs: float, r1: float, r2: float, rl: float) -> float:
    """Loaded node voltage from KCL, independent of the equivalent circuits."""
    return (vs / r1) / (1.0 / r1 + 1.0 / r2 + 1.0 / rl)


def parallel(a: float, b: float) -> float:
    return a * b / (a + b)


def shared_board(seed: int, board: int, rl_nom: float) -> dict:
    """Common random numbers: one draw per (seed, board), shared by every arm."""
    rng = random.Random(1_000_003 * seed + 7_919 * board + int(rl_nom) % 100_003)
    tol = lambda nom: nom * (1.0 + rng.uniform(-TOL, TOL))  # noqa: E731
    return {
        "r1": tol(R1_NOM),
        "r2": tol(R2_NOM),
        "rl": tol(rl_nom),
        "rtest": tol(RTEST_NOM),
        "z1": rng.gauss(0.0, 1.0),
        "z2": rng.gauss(0.0, 1.0),
    }


def predict(arm: str, b: dict) -> float:
    vth, rth = thevenin(VS, b["r1"], b["r2"])
    voc = vth + V_NOISE * b["z1"]  # same reading for every arm
    if arm == "A_voc_only":
        return voc
    if arm == "B_thevenin":
        vtest = truth_kcl(VS, b["r1"], b["r2"], b["rtest"]) + V_NOISE * b["z2"]
        rth_hat = RTEST_NOM * (voc / vtest - 1.0)  # uses the NOMINAL test value
        return voc * b["rl"] / (rth_hat + b["rl"])
    if arm == "C_norton":
        isc = vth / (rth + R_BURDEN) + I_NOISE * b["z2"]  # burden lowers the reading
        rn_hat = voc / isc
        return isc * parallel(rn_hat, b["rl"])
    raise ValueError(arm)


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def run_regime(rl_nom: float) -> dict:
    """Per arm: per-seed mean |V_pred - V_true| over the boards, in mV."""
    out = {arm: [] for arm in ARMS}
    for seed in SEEDS:
        boards = [shared_board(seed, i, rl_nom) for i in range(BOARDS)]
        for arm in ARMS:
            errs = [abs(predict(arm, b) - truth_kcl(VS, b["r1"], b["r2"], b["rl"])) for b in boards]
            out[arm].append(1e3 * sum(errs) / len(errs))
    return out


def main() -> None:
    vth, rth = thevenin(VS, R1_NOM, R2_NOM)
    print("Synthetic Thevenin/Norton toy; shared parts and meter-noise draws; not a bench lab")
    print(
        f"nominal Vs={VS}V R1={R1_NOM:.0f}ohm R2={R2_NOM:.0f}ohm -> Vth={vth:.4f}V Rth={rth:.1f}ohm; "
        f"tol={TOL * 100:.0f}% V_noise={V_NOISE * 1e3:.0f}mV I_noise={I_NOISE * 1e6:.0f}uA "
        f"burden={R_BURDEN:.0f}ohm seeds={len(SEEDS)} boards={BOARDS}"
    )
    print(
        f"nominal check: RL=10k -> V_L = Vth*RL/(Rth+RL) = {vth * 1e4 / (rth + 1e4):.4f} V; "
        f"KCL = {truth_kcl(VS, R1_NOM, R2_NOM, 1e4):.4f} V; Norton In=Vth/Rth={vth / rth * 1e3:.4f} mA"
    )
    print("regime RL_ohm arm |V_pred-V_true|_mV (mean+-sd over seeds)")
    summary = {}
    paired = {}
    for name, rl in REGIMES:
        res = run_regime(rl)
        paired[name] = mean_sd([x - y for x, y in zip(res["A_voc_only"], res["B_thevenin"])])
        for arm in ARMS:
            m, s = mean_sd(res[arm])
            summary[(name, arm)] = (m, s)
            print(f"{name} {rl:.0f} {arm} {m:.4f}+-{s:.4f}")
    a, b, c = (summary[("light_load", x)] for x in ARMS)
    print(
        f"light_load: A {a[0]:.4f}+-{a[1]:.4f} mV vs B {b[0]:.4f}+-{b[1]:.4f} mV vs "
        f"C {c[0]:.4f}+-{c[1]:.4f} mV (near-tie / small gap: A's bias Vth*Rth/(Rth+RL) "
        f"is about {vth * rth / (rth + 1e7) * 1e3:.2f} mV, the same order as the 1 mV meter noise)"
    )
    pm, ps = paired["light_load"]
    print(f"light_load paired per-seed A-B = {pm:.4f}+-{ps:.4f} mV (A still slightly worse; not a tie)")
    a, b, c = (summary[("heavy_load", x)] for x in ARMS)
    print(
        f"heavy_load: A {a[0]:.1f} mV >> B {b[0]:.2f} mV; C {c[0]:.2f} mV "
        f"(Norton = Thevenin on paper; C's extra error is the ammeter burden, a measurement cost)"
    )
    print("No winner declared: Voc alone is fine only when RL >> Rth; B and C differ only by how they were measured")
    print("Real DMM / bench Thevenin lab: 本页未运行; Wikipedia numbers 以原文为准")


if __name__ == "__main__":
    main()
