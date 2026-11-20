#!/usr/bin/env python3
"""MoveIt Servo collision-proximity scale stand-in.

A planar 1-D jog toward a fixed obstacle compares (A) check_collisions
off with no scale, (B) a linear proximity scale that is 1 at the opened
demo-config threshold and 0 at contact, and (C) an over-conservative
huge threshold.  Synthetic; not live MoveIt, FCL, or a real arm.

The opened panda_simulated_config.yaml distances
self_collision_proximity_threshold = 0.01 m and
scene_collision_proximity_threshold = 0.02 m are demo-config constants,
以文档为准, not vendor-universal defaults and not toy measurements.
check_collisions and collision_check_rate are printed as the same opened
constants.  The stand-in applies the scale every DT seconds; it does not
run a Planning Scene or honour the check rate as a live servo loop.

Common random numbers: the command timeline and obstacle poses are
deterministic and shared across arms.  Five seeds repeat the same
timeline so exact-tie cells can be printed as identical on every seed.
Seeds do not add jitter.

Metrics per seed: progress (metres travelled along the command),
collision_steps (steps with clearance <= 0), min_clearance (metres),
terminal_speed (m/s), max_penetration (metres, 0 if no contact).

Regimes and expectations, written before the first run:
  far_scene        obstacle stays beyond the 0.02 m scene band for the
                   whole jog: A and B may exact-tie or near-tie on
                   progress (keep); C over-conservative loses on
                   progress (keep)
  in_band_scene    a straight jog enters the 0.02 m scene band: B
                   consistent lower collision / penetration counts
                   (keep); A (no scale) loses on collisions (keep)
  in_band_self     a straight jog enters the 0.01 m self-collision
                   envelope: same B-vs-A collision reduction (keep)

Named alternative, same timeline, not adopted: a quadratic scale
(clearance / threshold)^2 between the threshold and contact.

Tutorial wording 以文档为准.  MoveIt / FCL / official keyboard demo:
本页未运行.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Opened panda_simulated_config.yaml demo-config constants (metres, Hz).
SELF_COLLISION_PROXIMITY_THRESHOLD = 0.01
SCENE_COLLISION_PROXIMITY_THRESHOLD = 0.02
CHECK_COLLISIONS_DEMO = True
COLLISION_CHECK_RATE = 10.0

# Declared toy step and command (not vendor-universal defaults).
DT = 0.01
V_CMD = 0.05
# Over-conservative lose-arm threshold (metres), declared, not from the yaml.
C_THRESHOLD = 2.0000

# far_scene: start 1.00 m from the wall, travel 0.05 m (1.0 s), end 0.95 m.
FAR_START_CLEARANCE = 1.0000
FAR_HORIZON_STEPS = 100
# in_band_scene: start 0.030 m from the wall, 1.0 s would travel 0.05 m.
SCENE_START_CLEARANCE = 0.0300
SCENE_HORIZON_STEPS = 100
# in_band_self: start 0.015 m from a self envelope, 1.0 s would travel 0.05 m.
SELF_START_CLEARANCE = 0.0150
SELF_HORIZON_STEPS = 100

ARMS = ("A", "B", "C")
METRICS = ("progress", "collision_steps", "min_clearance", "terminal_speed", "max_penetration")


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
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
    elif abs(m) < SMALL_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def proximity_scale(clearance: float, threshold: float, law: str) -> float:
    """1 at threshold, 0 at contact; 1 when farther than the threshold."""
    if threshold <= 0.0:
        raise ValueError("threshold must be positive")
    if clearance >= threshold:
        return 1.0
    if clearance <= 0.0:
        return 0.0
    frac = clearance / threshold
    if law == "linear":
        return frac
    if law == "quadratic":
        return frac * frac
    raise ValueError(law)


def run_arm(arm: str, start_clearance: float, steps: int, threshold: float, law: str = "linear") -> dict:
    if arm == "A":
        check = False
        used_threshold = threshold
    elif arm == "B":
        check = True
        used_threshold = threshold
    elif arm == "C":
        check = True
        used_threshold = C_THRESHOLD
    elif arm == "B_quad":
        check = True
        used_threshold = threshold
        law = "quadratic"
    else:
        raise ValueError(arm)

    clearance = start_clearance
    min_clearance = clearance
    collision_steps = 0
    max_penetration = 0.0
    speed = V_CMD
    for _ in range(steps):
        if check:
            scale = proximity_scale(clearance, used_threshold, law)
        else:
            scale = 1.0
        speed = scale * V_CMD
        clearance = clearance - speed * DT
        if clearance < min_clearance:
            min_clearance = clearance
        if clearance <= 0.0:
            collision_steps += 1
            pen = -clearance
            if pen > max_penetration:
                max_penetration = pen
    progress = start_clearance - clearance
    return {
        "progress": progress,
        "collision_steps": float(collision_steps),
        "min_clearance": min_clearance,
        "terminal_speed": speed,
        "max_penetration": max_penetration,
        "check_collisions": 1.0 if check else 0.0,
        "used_threshold": used_threshold,
    }


def col(rows, metric):
    return [row[metric] for row in rows]


def print_regime(name: str, expl: str, start_clearance: float, steps: int, threshold: float) -> None:
    print(f"declared expectation {name}: {expl}")
    print(
        f"regime {name}  (mean+-sd over seeds; deterministic jog) "
        f"start_clearance={num(start_clearance)} steps={steps} "
        f"band_threshold={num(threshold)} horizon_s={num(steps * DT)}"
    )
    rows = {arm: [] for arm in ARMS}
    recs0 = {}
    for seed in SEEDS:
        _ = seed
        for arm in ARMS:
            rec = run_arm(arm, start_clearance, steps, threshold)
            rows[arm].append(rec)
        if seed == 0:
            recs0 = {arm: rows[arm][0] for arm in ARMS}

    print(f"  seed 0 (all {len(SEEDS)} seeds identical):")
    for arm in ARMS:
        rec = recs0[arm]
        print(
            f"    {arm}: progress={num(rec['progress'])} collision_steps={num(rec['collision_steps'])} "
            f"min_clearance={num(rec['min_clearance'])} terminal_speed={num(rec['terminal_speed'])} "
            f"max_penetration={num(rec['max_penetration'])} "
            f"check_collisions={int(rec['check_collisions'])} used_threshold={num(rec['used_threshold'])}"
        )
    for arm in ARMS:
        for metric in METRICS:
            print(f"  {arm} {metric} {fmt_pair(*mean_sd(col(rows[arm], metric)))}")
    for metric in METRICS:
        print(f"  paired B-A {metric}: {verdict(col(rows['B'], metric), col(rows['A'], metric))}")
        print(f"  paired C-A {metric}: {verdict(col(rows['C'], metric), col(rows['A'], metric))}")
        print(f"  paired C-B {metric}: {verdict(col(rows['C'], metric), col(rows['B'], metric))}")


def main():
    print("Synthetic Servo collision-proximity stand-in; not MoveIt, FCL, or a real arm")
    print(
        "declared demo-config constants "
        f"self_collision_proximity_threshold={num(SELF_COLLISION_PROXIMITY_THRESHOLD)} "
        f"scene_collision_proximity_threshold={num(SCENE_COLLISION_PROXIMITY_THRESHOLD)} "
        f"check_collisions={str(CHECK_COLLISIONS_DEMO).lower()} "
        f"collision_check_rate={num(COLLISION_CHECK_RATE)}"
    )
    print(
        "declared toy DT="
        + num(DT)
        + " V_CMD="
        + num(V_CMD)
        + " C_THRESHOLD="
        + num(C_THRESHOLD)
        + " FAR_START_CLEARANCE="
        + num(FAR_START_CLEARANCE)
        + " FAR_HORIZON_STEPS="
        + str(FAR_HORIZON_STEPS)
        + " SCENE_START_CLEARANCE="
        + num(SCENE_START_CLEARANCE)
        + " SCENE_HORIZON_STEPS="
        + str(SCENE_HORIZON_STEPS)
        + " SELF_START_CLEARANCE="
        + num(SELF_START_CLEARANCE)
        + " SELF_HORIZON_STEPS="
        + str(SELF_HORIZON_STEPS)
        + " SMALL_FRAC="
        + num(SMALL_FRAC)
        + " seeds="
        + ",".join(str(s) for s in SEEDS)
    )
    print("declared scale law (B): 1 when clearance >= threshold, linear clearance/threshold down to 0 at contact")
    print("declared arm A: check_collisions off, scale = 1, no proximity scale")
    print("declared arm B: check_collisions on, scene 0.02 m or self 0.01 m as the regime's opened demo-config threshold")
    print("declared arm C: check_collisions on, over-conservative C_THRESHOLD (not a demo-config value)")
    print("hand_calc 20 percent small-vs-clear factor = " + num(SMALL_FRAC))
    print(
        "hand_calc far commanded travel = V_CMD * FAR_HORIZON_STEPS * DT = "
        + num(V_CMD)
        + " * "
        + str(FAR_HORIZON_STEPS)
        + " * "
        + num(DT)
        + " = "
        + num(V_CMD * FAR_HORIZON_STEPS * DT)
    )
    print(
        "hand_calc far final clearance if unscaled = FAR_START_CLEARANCE - commanded travel = "
        + num(FAR_START_CLEARANCE)
        + " - "
        + num(V_CMD * FAR_HORIZON_STEPS * DT)
        + " = "
        + num(FAR_START_CLEARANCE - V_CMD * FAR_HORIZON_STEPS * DT)
        + " (still above scene 0.0200 m)"
    )
    print(
        "hand_calc in-band scene unscaled travel = "
        + num(V_CMD * SCENE_HORIZON_STEPS * DT)
        + " from start "
        + num(SCENE_START_CLEARANCE)
        + " would cross the wall by "
        + num(V_CMD * SCENE_HORIZON_STEPS * DT - SCENE_START_CLEARANCE)
    )
    print(
        "hand_calc in-band self unscaled travel = "
        + num(V_CMD * SELF_HORIZON_STEPS * DT)
        + " from start "
        + num(SELF_START_CLEARANCE)
        + " would cross the envelope by "
        + num(V_CMD * SELF_HORIZON_STEPS * DT - SELF_START_CLEARANCE)
    )
    # Linear decay factor when already inside the band: d <- d * (1 - V_CMD*DT/T)
    scene_factor = 1.0 - V_CMD * DT / SCENE_COLLISION_PROXIMITY_THRESHOLD
    self_factor = 1.0 - V_CMD * DT / SELF_COLLISION_PROXIMITY_THRESHOLD
    print(
        "hand_calc in-band scene scale factor once inside the band = 1 - V_CMD*DT/0.0200 = "
        + num(scene_factor)
    )
    print(
        "hand_calc in-band self scale factor once inside the band = 1 - V_CMD*DT/0.0100 = "
        + num(self_factor)
    )
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: deterministic shared jog; seeds repeat the same timeline")
    print("Assumptions: planar 1-D clearance; Euler step x += scale * V_CMD * DT; scale from clearance at the start of the step")
    print("0.01 m / 0.02 m are opened demo-config constants, 以文档为准, not vendor-universal defaults and not toy measurements")
    print("MoveIt / FCL / official keyboard demo: 本页未运行")

    far_expl = (
        "obstacle stays beyond the 0.02 m scene band for the whole jog: "
        "A and B may exact-tie or near-tie on progress - keep; "
        "C over-conservative loses on progress - keep"
    )
    scene_expl = (
        "straight jog enters the 0.02 m scene band: B consistent lower "
        "collision / penetration counts - keep; A (no scale) loses on collisions - keep"
    )
    self_expl = (
        "straight jog enters the 0.01 m self-collision envelope: B consistent "
        "lower collision / penetration counts - keep; A (no scale) loses on collisions - keep"
    )
    print(f"declared far_scene: {far_expl}")
    print(f"declared in_band_scene: {scene_expl}")
    print(f"declared in_band_self: {self_expl}")

    print_regime(
        "far_scene",
        far_expl,
        FAR_START_CLEARANCE,
        FAR_HORIZON_STEPS,
        SCENE_COLLISION_PROXIMITY_THRESHOLD,
    )
    print_regime(
        "in_band_scene",
        scene_expl,
        SCENE_START_CLEARANCE,
        SCENE_HORIZON_STEPS,
        SCENE_COLLISION_PROXIMITY_THRESHOLD,
    )
    print_regime(
        "in_band_self",
        self_expl,
        SELF_START_CLEARANCE,
        SELF_HORIZON_STEPS,
        SELF_COLLISION_PROXIMITY_THRESHOLD,
    )

    print("named alternative B_quad (quadratic scale (clearance/threshold)^2) - not adopted")
    for name, start, steps, thr in (
        ("far_scene", FAR_START_CLEARANCE, FAR_HORIZON_STEPS, SCENE_COLLISION_PROXIMITY_THRESHOLD),
        ("in_band_scene", SCENE_START_CLEARANCE, SCENE_HORIZON_STEPS, SCENE_COLLISION_PROXIMITY_THRESHOLD),
        ("in_band_self", SELF_START_CLEARANCE, SELF_HORIZON_STEPS, SELF_COLLISION_PROXIMITY_THRESHOLD),
    ):
        alt = []
        base = []
        for seed in SEEDS:
            _ = seed
            alt.append(run_arm("B_quad", start, steps, thr))
            base.append(run_arm("B", start, steps, thr))
        rec = alt[0]
        print(
            f"  alt {name}: progress={num(rec['progress'])} collision_steps={num(rec['collision_steps'])} "
            f"min_clearance={num(rec['min_clearance'])} terminal_speed={num(rec['terminal_speed'])} "
            f"max_penetration={num(rec['max_penetration'])}"
        )
        for metric in METRICS:
            print(f"    paired alt-B {metric}: {verdict(col(alt, metric), col(base, metric))}")
    print("No winner declared")


if __name__ == "__main__":
    main()
