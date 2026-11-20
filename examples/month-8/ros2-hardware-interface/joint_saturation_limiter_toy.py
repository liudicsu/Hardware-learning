#!/usr/bin/env python3
"""JointLimiter enable-scope and coupled-saturation contract stand-in.

This is a standard-library CPU toy. It is a labeled stand-in of the opened
Jazzy controller-manager userdoc and JointSaturationLimiter doxygen
wording, not a bit-identical port of joint_saturation_limiter.cpp or
joint_limits_helpers.cpp, and not a run of the official plugin or
ros2_control_node. Official plugin / controller manager: 本页未运行.

The official concept page still marks Configuration of Limits and
Description of the Limiter Algorithms as tba; those sections are not
invented here.

Arms:
  A  limits not enforced (enforce_command_limits false, or per-joint
     limits enable="false"): commands pass through
  B  naive independent clamp of each commanded quantity to the declared
     box, ignoring remaining-distance coupling
  C  saturation-style contract stand-in: first tighten allowed velocity
     from remaining position room and dt, then apply the velocity box,
     then the acceleration box, following the opened doxygen order
     (position first to adjust desired velocity, then velocity, then
     acceleration)

Named alternative, same streams, not adopted: ALT_VEL_BOX_ONLY, which
clamps only the commanded velocity to the velocity box.

Metrics (lower is better): pos_violation is how far the one-dt step
state.pos + v_applied * dt would land outside the position box, or n/a
when the joint has no position limits; vel_box_violation is
max(0, |v_applied| - v_max) when a velocity box is declared.

Regimes and expectations, written before the first run:
  far_modest                 far from position limits, modest velocity:
                             B and C may exact-tie or near-tie (keep)
  near_limit_large_v         near a position limit with a large
                             commanded velocity: C consistently better
                             satisfaction of the remaining-distance /
                             "reduced accordingly" contract than B;
                             B may still command a step that cannot
                             stay inside the position box in one dt
                             (lose kept against C); A loses on the
                             same cell (keep)
  continuous_no_pos_limits   no position box is invented; B and C apply
                             the velocity / acceleration boxes only
                             (keep)
  actual_pos_out_of_bounds   when commanding position, C may raise if
                             the actual position is already out of
                             bounds (doxygen std::runtime_error
                             stand-in); keep

Opened documentation-log constants such as position [-1, 1], velocity 1
and effort 100 stay 以文档为准 and are not toy measurements. Lesson-chosen
toy limits and dt are named below and in the printed header. Official
plugin numerics stay 以文档为准 and are not toy outputs.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Lesson-chosen toy limits and dt, named before the first official run.
# These are not the opened documentation-log constants.
DT = 0.1000
POS_MIN = -0.5000
POS_MAX = 0.5000
V_MAX = 1.0000
A_MAX = 5.0000

# Opened startup-log constants, 以文档为准, not used as toy limits.
DOC_POS_MIN = -1.0
DOC_POS_MAX = 1.0
DOC_VEL = 1
DOC_EFFORT = 100

# Regime cells (shared across arms and seeds; no jitter).
FAR = dict(
    pos=0.0000,
    vel=0.0000,
    p_cmd=0.2000,
    v_cmd=0.3000,
    a_cmd=0.0000,
    has_pos_limits=True,
    has_vel_limits=True,
    has_acc_limits=True,
    command_position=True,
)
NEAR = dict(
    pos=0.4600,
    vel=0.0000,
    p_cmd=0.7000,
    v_cmd=1.5000,
    a_cmd=0.0000,
    has_pos_limits=True,
    has_vel_limits=True,
    has_acc_limits=True,
    command_position=True,
)
CONTINUOUS = dict(
    pos=0.4600,
    vel=0.8000,
    p_cmd=0.0000,
    v_cmd=1.5000,
    a_cmd=0.0000,
    has_pos_limits=False,
    has_vel_limits=True,
    has_acc_limits=True,
    command_position=False,
)
OUT_OF_BOUNDS = dict(
    pos=0.6000,
    vel=0.0000,
    p_cmd=0.4000,
    v_cmd=0.0000,
    a_cmd=0.0000,
    has_pos_limits=True,
    has_vel_limits=True,
    has_acc_limits=True,
    command_position=True,
)

ARMS = ("A", "B", "C")
REGIMES = (
    "far_modest",
    "near_limit_large_v",
    "continuous_no_pos_limits",
    "actual_pos_out_of_bounds",
)
REGIME_CELLS = {
    "far_modest": FAR,
    "near_limit_large_v": NEAR,
    "continuous_no_pos_limits": CONTINUOUS,
    "actual_pos_out_of_bounds": OUT_OF_BOUNDS,
}


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


def fmt_minus(a, b):
    """ASCII subtraction typography: 0.2000-(-2.0000), never 0.2000--2.0000."""
    right = num(b)
    if right.startswith("-"):
        return f"{num(a)}-({right})"
    return f"{num(a)}-{right}"


def sign_note(diffs, m):
    n = len(diffs)
    opp = sum(1 for d in diffs if d * m < 0)
    zero = sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def fmt_mean(xs):
    m, s = mean_sd(xs)
    return fmt_pair(m, s)


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


def clamp(x, lo, hi):
    return min(max(x, lo), hi)


class OutOfBounds(RuntimeError):
    """Stand-in of doxygen std::runtime_error when actual position is out of bounds
    and a position command is requested. Not a run of the official plugin."""


def pos_violation(pos, v_applied, dt, has_pos_limits):
    if not has_pos_limits:
        return None
    nxt = pos + v_applied * dt
    return max(0.0, nxt - POS_MAX, POS_MIN - nxt)


def vel_box_violation(v_applied, has_vel_limits):
    if not has_vel_limits:
        return None
    return max(0.0, abs(v_applied) - V_MAX)


def apply_A(cell):
    return dict(p=cell["p_cmd"], v=cell["v_cmd"], a=cell["a_cmd"])


def apply_B(cell):
    p, v, a = cell["p_cmd"], cell["v_cmd"], cell["a_cmd"]
    if cell["has_pos_limits"] and cell["command_position"]:
        p = clamp(p, POS_MIN, POS_MAX)
    if cell["has_vel_limits"]:
        v = clamp(v, -V_MAX, V_MAX)
    if cell["has_acc_limits"]:
        a = clamp(a, -A_MAX, A_MAX)
    return dict(p=p, v=v, a=a)


def apply_C(cell):
    """Labeled contract stand-in of the opened doxygen order.

    Position limits first adjust desired velocity from remaining room and
    dt; then the velocity box; then the acceleration box. Values may end
    lower than the declared box. Partial limits (no position box for a
    continuous joint) are supported. If the actual position is already
    out of bounds while commanding position, raise.
    """
    if cell["command_position"] and cell["has_pos_limits"]:
        if cell["pos"] < POS_MIN or cell["pos"] > POS_MAX:
            raise OutOfBounds(
                "actual position is out of bounds when commanding position"
            )
    v_des = cell["v_cmd"]
    if cell["has_pos_limits"]:
        room_hi = POS_MAX - cell["pos"]
        room_lo = cell["pos"] - POS_MIN
        v_hi = room_hi / DT
        v_lo = -room_lo / DT
        v_des = clamp(v_des, v_lo, v_hi)
    if cell["has_vel_limits"]:
        v_des = clamp(v_des, -V_MAX, V_MAX)
    a_des = cell["a_cmd"]
    if cell["has_acc_limits"]:
        a_req = (v_des - cell["vel"]) / DT
        a_des = clamp(a_req, -A_MAX, A_MAX)
        v_des = cell["vel"] + a_des * DT
    p_des = cell["p_cmd"]
    if cell["command_position"] and cell["has_pos_limits"]:
        p_des = clamp(p_des, POS_MIN, POS_MAX)
    return dict(p=p_des, v=v_des, a=a_des)


def apply_ALT(cell):
    """Named alternative, not adopted: velocity box only."""
    v = cell["v_cmd"]
    if cell["has_vel_limits"]:
        v = clamp(v, -V_MAX, V_MAX)
    return dict(p=cell["p_cmd"], v=v, a=cell["a_cmd"])


APPLY = {"A": apply_A, "B": apply_B, "C": apply_C, "ALT": apply_ALT}


def room_lines(cell):
    if not cell["has_pos_limits"]:
        return [
            "pos_limits=none (continuous joint: no position box is invented)",
            f"setup pos={num(cell['pos'])} vel={num(cell['vel'])} "
            f"p_cmd={num(cell['p_cmd'])} v_cmd={num(cell['v_cmd'])} "
            f"a_cmd={num(cell['a_cmd'])} dt={num(DT)}",
        ]
    room_hi = POS_MAX - cell["pos"]
    room_lo = cell["pos"] - POS_MIN
    return [
        f"setup pos={num(cell['pos'])} vel={num(cell['vel'])} "
        f"p_cmd={num(cell['p_cmd'])} v_cmd={num(cell['v_cmd'])} "
        f"a_cmd={num(cell['a_cmd'])} dt={num(DT)}",
        f"hand_calc room_hi = POS_MAX-pos = {fmt_minus(POS_MAX, cell['pos'])} = {num(room_hi)}",
        f"hand_calc room_lo = pos-POS_MIN = {fmt_minus(cell['pos'], POS_MIN)} = {num(room_lo)}",
        f"hand_calc room_hi/dt = {num(room_hi)}/{num(DT)} = {num(room_hi / DT)}",
        f"hand_calc room_lo/dt = {num(room_lo)}/{num(DT)} = {num(room_lo / DT)}",
    ]


def result_for(arm, cell):
    try:
        out = APPLY[arm](cell)
    except OutOfBounds as exc:
        return dict(throws=1, message=str(exc), p=None, v=None, a=None,
                    next_pos=None, pos_violation=None, vel_box_violation=None)
    nxt = cell["pos"] + out["v"] * DT
    return dict(
        throws=0,
        message="",
        p=out["p"],
        v=out["v"],
        a=out["a"],
        next_pos=nxt,
        pos_violation=pos_violation(cell["pos"], out["v"], DT, cell["has_pos_limits"]),
        vel_box_violation=vel_box_violation(out["v"], cell["has_vel_limits"]),
    )


def fmt_metric(value):
    if value is None:
        return "n/a"
    return num(value)


def print_arm_row(name, res):
    if res["throws"]:
        print(
            f"{name} throws=1 message={res['message']}"
        )
        return
    print(
        f"{name} p={num(res['p'])} v={num(res['v'])} a={num(res['a'])} "
        f"next_pos={num(res['next_pos'])} "
        f"pos_violation={fmt_metric(res['pos_violation'])} "
        f"vel_box_violation={fmt_metric(res['vel_box_violation'])}"
    )


def collect_metric(regime, arm, key):
    cell = REGIME_CELLS[regime]
    # Five seeds, common random numbers, no jitter: the shared cell is
    # identical across arms and seeds, so exact-tie cells stay identical.
    values = []
    for _seed in SEEDS:
        res = result_for(arm, cell)
        if res["throws"] or res[key] is None:
            return None
        values.append(res[key])
    return values


def print_regime(name, expectation):
    cell = REGIME_CELLS[name]
    print(f"regime {name}")
    print(expectation)
    for line in room_lines(cell):
        print(line)
    results = {arm: result_for(arm, cell) for arm in ("A", "B", "C", "ALT")}
    for arm in ("A", "B", "C"):
        print_arm_row(arm, results[arm])
    print_arm_row("ALT_VEL_BOX_ONLY", results["ALT"])
    print("adopted=C not_adopted=ALT_VEL_BOX_ONLY")
    if name == "actual_pos_out_of_bounds":
        print(
            "C is a labeled doxygen exception stand-in on this cell; "
            "paired command metrics are omitted because C issues no command"
        )
        return
    for key in ("pos_violation", "vel_box_violation"):
        series = {}
        skip = False
        for arm in ("A", "B", "C", "ALT"):
            xs = collect_metric(name, arm, key)
            if xs is None:
                skip = True
                break
            series[arm] = xs
            label = "ALT_VEL_BOX_ONLY" if arm == "ALT" else arm
            print(f"{label} {key} {fmt_mean(xs)}")
        if skip:
            print(f"{key}=n/a (no position box is invented)" if key == "pos_violation" else f"{key}=n/a")
            continue
        print(f"paired B-A {key}: {verdict(series['B'], series['A'])}")
        print(f"paired C-A {key}: {verdict(series['C'], series['A'])}")
        print(f"paired C-B {key}: {verdict(series['C'], series['B'])}")
        print(f"paired ALT-C {key}: {verdict(series['ALT'], series['C'])} (not adopted)")


def main():
    print("joint_saturation_limiter_toy")
    print(
        "stdlib CPU contract stand-in, not the official plugin, "
        "not a port of the .cpp helpers"
    )
    print(
        f"seeds={','.join(str(s) for s in SEEDS)} n_seeds={len(SEEDS)} "
        f"small_frac={num(SMALL_FRAC)}"
    )
    print(
        f"setup DT={num(DT)} POS_MIN={num(POS_MIN)} POS_MAX={num(POS_MAX)} "
        f"V_MAX={num(V_MAX)} A_MAX={num(A_MAX)}"
    )
    print(
        "doc_log_constants (opened startup log, 以文档为准, not toy limits): "
        f"position [{DOC_POS_MIN:.0f}, {DOC_POS_MAX:.0f}], velocity {DOC_VEL}, "
        f"effort {DOC_EFFORT}"
    )
    print(
        "Common random numbers: the shared current state, commanded "
        "trajectory, dt and lesson-chosen limits are identical across "
        "arms; five seeds repeat the same deterministic tables so "
        "exact-tie cells are identical on every seed. Seeds do not add jitter."
    )
    print("official plugin / controller manager: 本页未运行")
    print("hand_calc 20 percent small-vs-clear factor = " + num(SMALL_FRAC))
    print("hand_calc work_plan 30+25+50+40+35=180")
    print("hand_calc DT = 0.1000")
    print("hand_calc POS_MIN = -0.5000")
    print("hand_calc POS_MAX = 0.5000")
    print("hand_calc V_MAX = 1.0000")
    print("hand_calc A_MAX = 5.0000")
    # Far cell hand-calc of the next step under a modest command.
    print(
        "hand_calc far next_pos if v=0.3000 = 0.0000+0.3000*0.1000 = 0.0300"
    )
    print(
        "hand_calc far pos_violation = max(0, 0.0300-0.5000, -0.5000-0.0300) = 0.0000"
    )
    print("hand_calc far C a_req = (0.3000-0.0000)/0.1000 = 3.0000")
    # Near cell remaining-distance arithmetic.
    print("hand_calc near room_hi = 0.5000-0.4600 = 0.0400")
    print("hand_calc near room_hi/dt = 0.0400/0.1000 = 0.4000")
    print("hand_calc near A next_pos = 0.4600+1.5000*0.1000 = 0.6100")
    print("hand_calc near A pos_violation = 0.6100-0.5000 = 0.1100")
    print("hand_calc near B v = clamp(1.5000, -1.0000, 1.0000) = 1.0000")
    print("hand_calc near B next_pos = 0.4600+1.0000*0.1000 = 0.5600")
    print("hand_calc near B pos_violation = 0.5600-0.5000 = 0.0600")
    print(
        "hand_calc near C v after position room = "
        "clamp(1.5000, -0.9600/0.1000, 0.0400/0.1000) = 0.4000"
    )
    print("hand_calc near C v after velocity box = clamp(0.4000, -1.0000, 1.0000) = 0.4000")
    print("hand_calc near C a_req = (0.4000-0.0000)/0.1000 = 4.0000")
    print("hand_calc near C a after box = clamp(4.0000, -5.0000, 5.0000) = 4.0000")
    print("hand_calc near C v after acceleration = 0.0000+4.0000*0.1000 = 0.4000")
    print("hand_calc near C next_pos = 0.4600+0.4000*0.1000 = 0.5000")
    print("hand_calc near C pos_violation = 0.0000")
    print("hand_calc near ALT_VEL_BOX_ONLY v = clamp(1.5000, -1.0000, 1.0000) = 1.0000")
    print("hand_calc near ALT next_pos = 0.4600+1.0000*0.1000 = 0.5600")
    print("hand_calc near ALT pos_violation = 0.0600")
    print("hand_calc continuous room is not computed; no position box is invented")
    print("hand_calc continuous B,C v = clamp(1.5000, -1.0000, 1.0000) = 1.0000")
    print("hand_calc continuous C a_req = (1.0000-0.8000)/0.1000 = 2.0000")
    print("hand_calc continuous C v after acceleration = 0.8000+2.0000*0.1000 = 1.0000")
    print("hand_calc continuous A vel_box_violation = 1.5000-1.0000 = 0.5000")
    print("hand_calc out_of_bounds actual pos 0.6000 > POS_MAX 0.5000")

    print()
    print_regime(
        "far_modest",
        "far from position limits, modest velocity; B and C may exact-tie or near-tie (keep)",
    )
    print()
    print_regime(
        "near_limit_large_v",
        "near a position limit with a large commanded velocity; "
        "C consistently better remaining-distance contract than B; "
        "B may still step outside the position box in one dt (lose kept); "
        "A loses on the same cell (keep)",
    )
    print()
    print_regime(
        "continuous_no_pos_limits",
        "continuous joint: no position box is invented (keep)",
    )
    print()
    print_regime(
        "actual_pos_out_of_bounds",
        "actual position already out of bounds while commanding position; "
        "C may raise (doxygen exception stand-in; keep)",
    )


if __name__ == "__main__":
    main()
