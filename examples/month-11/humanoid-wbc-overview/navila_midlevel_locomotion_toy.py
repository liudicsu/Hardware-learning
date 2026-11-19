#!/usr/bin/env python3
"""Synthetic mid-level language plus visual locomotion stand-in.

Stdlib only. Shared instruction, occupancy / clutter and mid-level command
vocabulary are drawn once per (regime, seed, scene) and then read by every
arm (common random numbers).

Arm A is a flat low-level go-to-goal policy that only sidesteps opaque
obstacles and then resumes the center lane. Arm B emits mid-level language
actions and a vision-using locomotion stand-in that can sidestep every
obstacle, including transparent ones. Arm C ignores mid-level commands and
follows a blind constant heading bias.

This is a 2-D kinematic / reactive lane stand-in, not Isaac, not Nav2, and
not a real Unitree Go2 / H1 / Booster T1. It is not LIPM / ZMP /
capture-point, not a hierarchical manipulation VLA, not a dual-system VLA,
not AMCL, and not a wheeled nav-then-pick compose contract. Paper VLN
success-rate lift and real-world instruction success figures are 以论文为准
and are not toy outputs. IsaacLab / real Unitree or Booster / GPU: 本页未运行.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000

LEN = 8.0000
HALF_W = 1.2000
ROBOT_R = 0.1500
OBS_R = 0.2500
GOAL_TOL = 0.4000
SIDE = 0.5000
MID_FWD = 0.7500
MID_TURN_DEG = 30.0000
N_SCENES = 25
N_OBS_CLUTTER = 4
N_TRANSPARENT = 2
C_YAW_BIAS = 0.2000
WALL_CLEAR = HALF_W - ROBOT_R
HIT_CLEAR = ROBOT_R + OBS_R

ALT_SIDE = 0.3000
ALT_C_YAW_BIAS = 0.1000

OX_LO = ROBOT_R + OBS_R + 0.2000
OX_HI = LEN - GOAL_TOL - 0.2000

METRICS = ("success", "collisions")
ARMS = ("A_flat_lowlevel", "B_midlevel_visual", "C_blind_ignored")
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

REGIMES = {
    "open_corridor": "A and B may near-tie on success and collisions (open corridor, no clutter) - keep",
    "clutter_transparent": "B consistently above A on success and consistently below A on collisions (cluttered / transparent-obstacle stand-in) - keep",
}
C_EXPECT = "C loses to B on success (mid-level commands ignored, blind heading bias 0.2000 rad) - keep"
REGIME_IDS = {"open_corridor": 0, "clutter_transparent": 1}


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


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def dist_point_to_seg(px, py, x0, y0, x1, y1):
    vx, vy = x1 - x0, y1 - y0
    wx, wy = px - x0, py - y0
    denom = vx * vx + vy * vy
    if denom == 0.0:
        return math.hypot(wx, wy)
    t = (wx * vx + wy * vy) / denom
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    return math.hypot(px - (x0 + t * vx), py - (y0 + t * vy))


def draw_obstacles(regime, seed, scene_index):
    if regime == "open_corridor":
        return []
    rng = random.Random(seed + 1000 * REGIME_IDS[regime] + scene_index)
    obs = []
    for i in range(N_OBS_CLUTTER):
        ox = 1.8000 + i * 1.4000 + rng.uniform(-0.2000, 0.2000)
        ox = clamp(ox, OX_LO, OX_HI)
        if i < N_TRANSPARENT:
            oy = rng.uniform(-0.0500, 0.0500)
            trans = True
        elif i == N_TRANSPARENT:
            oy = rng.uniform(-0.0500, 0.0500)
            trans = False
        else:
            oy = 0.8000 + rng.uniform(-0.1000, 0.1000)
            trans = False
        obs.append((ox, oy, trans))
    return obs


def visible_of(obstacles, see_transparent):
    if see_transparent:
        return list(obstacles)
    return [o for o in obstacles if not o[2]]


def lane_free(y_lane, obstacles, x0, x1, hit_clear):
    if abs(y_lane) > WALL_CLEAR:
        return False
    lo, hi = (x0, x1) if x0 <= x1 else (x1, x0)
    for ox, oy, _trans in obstacles:
        if lo <= ox <= hi and abs(oy - y_lane) < hit_clear:
            return False
    return True


def long_hits(x0, x1, y, obstacles, hit_clear):
    lo, hi = (x0, x1) if x0 <= x1 else (x1, x0)
    hits = []
    for i, (ox, oy, _trans) in enumerate(obstacles):
        if lo <= ox <= hi and abs(oy - y) < hit_clear:
            hits.append(i)
    return hits


def lateral_hits(x, y0, y1, obstacles, hit_clear):
    lo, hi = (y0, y1) if y0 <= y1 else (y1, y0)
    hits = []
    for i, (ox, oy, _trans) in enumerate(obstacles):
        if abs(ox - x) < hit_clear and lo <= oy <= hi:
            hits.append(i)
        elif abs(ox - x) < hit_clear and min(abs(oy - y0), abs(oy - y1)) < hit_clear:
            hits.append(i)
    return hits


def choose_lane(x, x_next, y, visible, hit_clear, side):
    for y_new in (side, -side):
        if lane_free(y_new, visible, x, x_next, hit_clear):
            return y_new
    return y


def follow_lanes(obstacles, see_transparent, resume_center_always, side, hit_clear):
    """Return (success, collision_count) for an A/B lane-following policy."""
    visible = visible_of(obstacles, see_transparent)
    x = 0.0
    y = 0.0
    hit = set()
    wall = False

    def bump_long(x0, x1, yy):
        if abs(yy) > WALL_CLEAR:
            return True
        hit.update(long_hits(x0, x1, yy, obstacles, hit_clear))
        return False

    def bump_lat(xx, y0, y1):
        if abs(y0) > WALL_CLEAR or abs(y1) > WALL_CLEAR:
            return True
        hit.update(lateral_hits(xx, y0, y1, obstacles, hit_clear))
        return False

    while x < LEN - 1e-15:
        x_next = min(x + MID_FWD, LEN)
        look = min(LEN, x_next + hit_clear)
        blockers = [o for o in visible if x < o[0] <= look and abs(o[1] - y) < hit_clear]
        if blockers:
            o = min(blockers, key=lambda t: t[0])
            # Sidestep just before the open hit interval. Subtract a tiny
            # numerical guard so ox - x_sw is not slightly < hit_clear by rounding.
            x_sw = o[0] - hit_clear - 1e-12
            if x_sw < x:
                x_sw = x
            if x_sw > x:
                if bump_long(x, x_sw, y):
                    wall = True
                x = x_sw
            y_new = choose_lane(x, LEN, y, visible, hit_clear, side)
            if y_new != y:
                if bump_lat(x, y, y_new):
                    wall = True
                y = y_new
            x_pass = max(x_next, o[0] + hit_clear)
            if x_pass > LEN:
                x_pass = LEN
            if x_pass > x:
                if bump_long(x, x_pass, y):
                    wall = True
                x = x_pass
            if abs(y) > 0.0 and x + 1e-15 >= o[0] + hit_clear:
                following = min(x + MID_FWD, LEN)
                center_clear = lane_free(0.0, visible, x, following, hit_clear)
                lat_clear = not lateral_hits(x, y, 0.0, obstacles, hit_clear)
                if (resume_center_always or center_clear) and lat_clear:
                    if bump_lat(x, y, 0.0):
                        wall = True
                    y = 0.0
        else:
            if bump_long(x, x_next, y):
                wall = True
            x = x_next

    if abs(y) > 0.0:
        if bump_lat(LEN, y, 0.0):
            wall = True
        y = 0.0

    collisions = float(len(hit) + (1 if wall else 0))
    success = 1.0 if (not wall and not hit and abs(y) <= GOAL_TOL and x >= LEN - 1e-15) else 0.0
    return success, collisions


def follow_c(obstacles, yaw_bias, hit_clear):
    tan_b = math.tan(yaw_bias)
    x_wall = WALL_CLEAR / tan_b if tan_b > 0.0 else LEN + 1.0
    wall = x_wall <= LEN
    x_end = min(LEN, x_wall)
    y_end = x_end * tan_b
    hit = set()
    for i, (ox, oy, _trans) in enumerate(obstacles):
        if dist_point_to_seg(ox, oy, 0.0, 0.0, x_end, y_end) < hit_clear:
            hit.add(i)
    collisions = float(len(hit) + (1 if wall else 0))
    success = 1.0 if (not wall and not hit and abs(y_end) <= GOAL_TOL and x_end >= LEN - 1e-15) else 0.0
    return success, collisions


def run_scene(obstacles, side, yaw_bias, hit_clear):
    a = follow_lanes(obstacles, False, True, side, hit_clear)
    b = follow_lanes(obstacles, True, False, side, hit_clear)
    c = follow_c(obstacles, yaw_bias, hit_clear)
    return {
        "A_flat_lowlevel": {"success": a[0], "collisions": a[1]},
        "B_midlevel_visual": {"success": b[0], "collisions": b[1]},
        "C_blind_ignored": {"success": c[0], "collisions": c[1]},
    }


def run_regime(regime, seed, side=SIDE, yaw_bias=C_YAW_BIAS):
    acc = {arm: {m: 0.0 for m in METRICS} for arm in ARMS}
    for scene_index in range(N_SCENES):
        obs = draw_obstacles(regime, seed, scene_index)
        out = run_scene(obs, side, yaw_bias, HIT_CLEAR)
        for arm in ARMS:
            for m in METRICS:
                acc[arm][m] += out[arm][m]
    n = float(N_SCENES)
    return {arm: {m: acc[arm][m] / n for m in METRICS} for arm in ARMS}


def main():
    tan_b = math.tan(C_YAW_BIAS)
    y_at_len = LEN * tan_b
    x_wall = WALL_CLEAR / tan_b
    print(
        "Mid-level language locomotion toy: 2-D synthetic corridor under "
        "common random numbers (kinematic / reactive lane stand-in, not "
        "Isaac, not a real Unitree or Booster)"
    )
    print(
        "Paper VLN success-rate lift and real-world instruction success "
        "figures 以论文为准 and are not toy outputs; IsaacLab / real Unitree "
        "or Booster / GPU: 本页未运行"
    )
    print(
        f"seeds={len(SEEDS)} n_scenes={num(float(N_SCENES))} len={num(LEN)} "
        f"half_w={num(HALF_W)} robot_r={num(ROBOT_R)} obs_r={num(OBS_R)} "
        f"goal_tol={num(GOAL_TOL)} side={num(SIDE)} mid_fwd={num(MID_FWD)} "
        f"mid_turn_deg={num(MID_TURN_DEG)} n_obs_clutter={num(float(N_OBS_CLUTTER))} "
        f"n_transparent={num(float(N_TRANSPARENT))} c_yaw_bias={num(C_YAW_BIAS)} "
        f"wall_clear={num(WALL_CLEAR)} hit_clear={num(HIT_CLEAR)} "
        f"small_frac={num(SMALL_FRAC)}"
    )
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: the instruction, occupancy / clutter and "
        "mid-level command vocabulary are shared across arms at each regime "
        "and seed"
    )
    print(f"hand_calc n_scenes = {num(float(N_SCENES))}")
    print(f"hand_calc wall_clear = {num(HALF_W)} - {num(ROBOT_R)} = {num(WALL_CLEAR)}")
    print(f"hand_calc hit_clear = {num(ROBOT_R)} + {num(OBS_R)} = {num(HIT_CLEAR)}")
    print(
        f"hand_calc mid-level vocabulary forward {num(MID_FWD)} m, sidestep "
        f"{num(SIDE)} m, turn {num(MID_TURN_DEG)} deg"
    )
    print(
        f"hand_calc C yaw bias {num(C_YAW_BIAS)} rad, tan = {num(tan_b)}, "
        f"y at LEN = {num(LEN)} * tan({num(C_YAW_BIAS)}) = {num(y_at_len)}, "
        f"which is > {num(WALL_CLEAR)} so C hits the wall"
    )
    print(f"hand_calc C wall x = {num(WALL_CLEAR)} / tan({num(C_YAW_BIAS)}) = {num(x_wall)}")
    print(
        f"hand_calc n_obs open = {num(0.0)}; clutter n_obs = "
        f"{num(float(N_OBS_CLUTTER))} of which n_transparent = {num(float(N_TRANSPARENT))}"
    )
    print(f"hand_calc small-gap threshold = {num(SMALL_FRAC)} of the smaller arm mean")

    for r, exp in REGIMES.items():
        print(f"declared {r}: {exp}")
        print(f"declared {r} C: {C_EXPECT}")

    store = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_side = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_bias = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    for seed in SEEDS:
        for r in REGIMES:
            official = run_regime(r, seed)
            side_run = run_regime(r, seed, side=ALT_SIDE)
            bias_run = run_regime(r, seed, yaw_bias=ALT_C_YAW_BIAS)
            for arm in ARMS:
                for m in METRICS:
                    store[r][arm][m].append(official[arm][m])
                    alt_side[r][arm][m].append(side_run[arm][m])
                    alt_bias[r][arm][m].append(bias_run[arm][m])

    def arm_of(letter):
        return [a for a in ARMS if a.startswith(letter + "_")][0]

    for r in REGIMES:
        print(f"regime {r}")
        for arm in ARMS:
            for m in METRICS:
                mu, sd = mean_sd(store[r][arm][m])
                print(f"  {arm} {m}: {num(mu)}+-{num(sd)}")
        for left, right in PAIRS:
            for m in METRICS:
                print(
                    f"  paired {left}-{right} {m}: "
                    f"{verdict(store[r][arm_of(left)][m], store[r][arm_of(right)][m])}"
                )

    print("alternatives on the same seeds (not adopted):")
    print(f"  alternative side={num(ALT_SIDE)}")
    for r in REGIMES:
        print(f"  regime {r}")
        for left, right in (("B", "A"), ("C", "B")):
            for m in METRICS:
                print(
                    f"    paired {left}-{right} {m}: "
                    f"{verdict(alt_side[r][arm_of(left)][m], alt_side[r][arm_of(right)][m])}"
                )
    print(f"  alternative c_yaw_bias={num(ALT_C_YAW_BIAS)}")
    for r in REGIMES:
        print(f"  regime {r}")
        for left, right in (("B", "A"), ("C", "B")):
            for m in METRICS:
                print(
                    f"    paired {left}-{right} {m}: "
                    f"{verdict(alt_bias[r][arm_of(left)][m], alt_bias[r][arm_of(right)][m])}"
                )


if __name__ == "__main__":
    main()
