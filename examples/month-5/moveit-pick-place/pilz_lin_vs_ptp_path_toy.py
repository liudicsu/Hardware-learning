#!/usr/bin/env python3
"""Synthetic Pilz LIN vs PTP path-shape stand-in.

Stdlib only. No MoveIt process is started. This compares mid-path Cartesian
bow of a PTP-like joint-space path with a LIN-like Cartesian line plus
quaternion slerp, using a thin analytic IK stand-in. It is not a redo of
the 1-D S-curve vs trapezoid time toy, not OMPL RRTConnect, and not Servo.

A shared start and goal pose, a shared 2R-plus-wrist arm, a shared obstacle
and a shared measurement-noise sequence are generated once per (regime,
seed) and then read by every arm (common random numbers).

Arms:
  A_ptp -- synchronized linear interpolation in joint space (the path of a
    fully synchronized PTP move: the lead axis only sets the time law).
  B_lin -- linear interpolation of the position vector plus quaternion
    slerp of orientation, mapped back to joints by the IK stand-in.
  C_lin_blocked -- the same LIN command through a blocking obstacle; the
    straight line is not collision-free. PTP and LIN are not claimed to be
    collision-avoiding planners like RRTConnect.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.

PTP / LIN / CIRC definitions stay 以文档为准.
Real MoveIt / Panda / computeCartesianPath: 本页未运行.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared 2R-plus-wrist stand-in (path shape, not a time law).
L1 = 0.3000  # m
L2 = 0.2500  # m
N_PATH = 41  # samples, inclusive of start and goal
SIG_MEAS = 0.0004  # m, shared Cartesian measurement noise
# Named alternative, same seeds, not adopted: drop the measurement noise.
SIG_MEAS_ALT = 0.0000

# Wrist yaw at the short and reconfiguration starts/goals (rad).
Q3_SHORT_S = 0.1000
Q3_SHORT_G = 0.1400
Q3_RECONFIG_S = 0.2000
Q3_RECONFIG_G = -0.1000
Q3_BLOCKED_S = 0.0000
Q3_BLOCKED_G = 0.2000

# Short, already nearly straight joint move (rad).
SHORT_Q_S = (0.5000, 0.7000, Q3_SHORT_S)
SHORT_Q_G = (0.5200, 0.7200, Q3_SHORT_G)

# Long reconfiguration: modest Cartesian displacement, large joint travel.
# Elbow-up at (0.3500, 0.1500) m to elbow-down at (0.3200, 0.1800) m.
RECONFIG_POS_S = (0.3500, 0.1500, 0.0000)
RECONFIG_POS_G = (0.3200, 0.1800, 0.0000)
RECONFIG_BRANCH_S = 1
RECONFIG_BRANCH_G = -1

# LIN through a blocking obstacle: horizontal approach along y = 0.0500 m.
BLOCKED_POS_S = (0.2000, 0.0500, 0.0000)
BLOCKED_POS_G = (0.4500, 0.0500, 0.0000)
BLOCKED_BRANCH = 1
# Axis-aligned obstacle in the xy plane (m); the start-goal segment
# crosses it. Written before the first run.
OBS_X_LO = 0.3000
OBS_X_HI = 0.3500
OBS_Y_LO = 0.0300
OBS_Y_HI = 0.0700

ARMS = ("A_ptp", "B_lin", "C_lin_blocked")
METRICS = ("bow_m", "n_collide")
PAIRS = (("B", "A"), ("C", "A"), ("C", "B"))

# name: (kind, declared expectation); written before the first run
REGIMES = {
    "short_straight": (
        "short_straight",
        "A and B may near-tie on mid-path Cartesian bow - keep",
    ),
    "long_reconfig": (
        "long_reconfig",
        "B consistent smaller Cartesian bow than A - keep",
    ),
    "lin_blocked": (
        "lin_blocked",
        "C loses as a valid approach path because the line intersects the obstacle - lose kept",
    ),
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


def rng_for(*parts):
    h = 10094444
    for part in parts:
        if isinstance(part, str):
            for ch in part:
                h = (h * 131 + ord(ch)) & 0xFFFFFFFFFFFFFFFF
        else:
            h = (h * 131 + int(part)) & 0xFFFFFFFFFFFFFFFF
    return random.Random(h)


def quat_from_yaw(yaw):
    half = 0.5 * yaw
    return (math.cos(half), 0.0, 0.0, math.sin(half))


def yaw_from_quat(q):
    w, x, y, z = q
    return 2.0 * math.atan2(z, w)


def quat_norm(q):
    n = math.sqrt(sum(c * c for c in q))
    if n == 0.0:
        return (1.0, 0.0, 0.0, 0.0)
    return tuple(c / n for c in q)


def slerp(q0, q1, t):
    """Unit-quaternion slerp, short-arc. t in [0, 1]."""
    a = quat_norm(q0)
    b = quat_norm(q1)
    dot = sum(u * v for u, v in zip(a, b))
    if dot < 0.0:
        b = tuple(-c for c in b)
        dot = -dot
    if dot > 0.9995:
        return quat_norm(tuple(u + t * (v - u) for u, v in zip(a, b)))
    dot = max(-1.0, min(1.0, dot))
    theta = math.acos(dot)
    s0 = math.sin((1.0 - t) * theta) / math.sin(theta)
    s1 = math.sin(t * theta) / math.sin(theta)
    return quat_norm(tuple(s0 * u + s1 * v for u, v in zip(a, b)))


def fk(q):
    q1, q2, q3 = q
    x = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
    y = L1 * math.sin(q1) + L2 * math.sin(q1 + q2)
    yaw = q1 + q2 + q3
    return (x, y, 0.0), quat_from_yaw(yaw)


def ik(pos, quat, branch, q_hint=None):
    """Thin analytic 2R IK plus wrist yaw; optional nearest-branch hint."""
    x, y, _z = pos
    r2 = x * x + y * y
    den = 2.0 * L1 * L2
    c2 = (r2 - L1 * L1 - L2 * L2) / den
    if abs(c2) > 1.0 + 1e-12:
        raise ValueError("unreachable")
    c2 = max(-1.0, min(1.0, c2))
    a2 = math.acos(c2)

    def solve(sign):
        q2 = sign * a2
        q1 = math.atan2(y, x) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
        q3 = yaw_from_quat(quat) - q1 - q2
        return (q1, q2, q3)

    if q_hint is None:
        return solve(branch)
    cand = (solve(1), solve(-1))
    return min(cand, key=lambda q: sum((a - b) ** 2 for a, b in zip(q, q_hint)))


def lerp_tuple(a, b, t):
    return tuple(u + t * (v - u) for u, v in zip(a, b))


def point_line_dist(p, a, b):
    ax, ay, az = a
    bx, by, bz = b
    px, py, pz = p
    vx, vy, vz = bx - ax, by - ay, bz - az
    length = math.sqrt(vx * vx + vy * vy + vz * vz)
    wx, wy, wz = px - ax, py - ay, pz - az
    if length < 1e-15:
        return math.sqrt(wx * wx + wy * wy + wz * wz)
    return math.sqrt((wy * vz - wz * vy) ** 2 + (wz * vx - wx * vz) ** 2 + (wx * vy - wy * vx) ** 2) / length


def in_obstacle(p):
    x, y, _z = p
    return (OBS_X_LO <= x <= OBS_X_HI) and (OBS_Y_LO <= y <= OBS_Y_HI)


def segment_hits_obstacle(a, b):
    """Liang-Barsky clip of the start-goal segment against the obstacle box."""
    ax, ay, _az = a
    bx, by, _bz = b
    dx, dy = bx - ax, by - ay
    t0, t1 = 0.0, 1.0
    for p, q in (
        (-dx, ax - OBS_X_LO),
        (dx, OBS_X_HI - ax),
        (-dy, ay - OBS_Y_LO),
        (dy, OBS_Y_HI - ay),
    ):
        if abs(p) < 1e-18:
            if q < 0.0:
                return False
            continue
        u = q / p
        if p < 0.0:
            if u > t1:
                return False
            if u > t0:
                t0 = u
        else:
            if u < t0:
                return False
            if u < t1:
                t1 = u
    return t0 <= t1


def ptp_path(q_s, q_g):
    path = []
    for i in range(N_PATH):
        t = i / (N_PATH - 1)
        q = lerp_tuple(q_s, q_g, t)
        pos, quat = fk(q)
        path.append((q, pos, quat))
    return path


def lin_path(q_s, pos_s, quat_s, pos_g, quat_g):
    path = []
    q_prev = q_s
    for i in range(N_PATH):
        t = i / (N_PATH - 1)
        pos = lerp_tuple(pos_s, pos_g, t)
        quat = slerp(quat_s, quat_g, t)
        q = ik(pos, quat, branch=1, q_hint=q_prev)
        # Reconstruct from the IK joints so the reported pose is the
        # stand-in's joint trajectory, not the commanded Cartesian sample.
        pos_fk, quat_fk = fk(q)
        path.append((q, pos_fk, quat_fk))
        q_prev = q
    return path


def shared_noise(seed, kind, sig):
    rng = rng_for("meas", kind, seed)
    return [(rng.gauss(0.0, sig), rng.gauss(0.0, sig), 0.0) for _ in range(N_PATH)]


def apply_noise(path, noise):
    out = []
    for (q, pos, quat), n in zip(path, noise):
        out.append((q, (pos[0] + n[0], pos[1] + n[1], pos[2] + n[2]), quat))
    return out


def path_metrics(path, pos_s, pos_g, noisy):
    bow = 0.0
    n_collide = 0
    for (_q, pos, _quat), (_qn, pos_n, _quatn) in zip(path, noisy):
        bow = max(bow, point_line_dist(pos_n, pos_s, pos_g))
        if in_obstacle(pos):
            n_collide += 1
    line_hit = 1.0 if segment_hits_obstacle(pos_s, pos_g) else 0.0
    return {"bow_m": bow, "n_collide": float(n_collide), "line_hit": line_hit}


def joints_for_pose(pos, q3, branch):
    quat = quat_from_yaw(0.0)  # placeholder, overwritten via q3
    # First solve position with yaw 0, then set q3 as declared wrist.
    q = ik((pos[0], pos[1], 0.0), quat, branch=branch)
    q = (q[0], q[1], q3)
    pos_fk, quat_fk = fk(q)
    return q, pos_fk, quat_fk


def shared_problem(seed, kind, sig=SIG_MEAS):
    if kind == "short_straight":
        q_s = SHORT_Q_S
        q_g = SHORT_Q_G
        pos_s, quat_s = fk(q_s)
        pos_g, quat_g = fk(q_g)
    elif kind == "long_reconfig":
        q_s, pos_s, quat_s = joints_for_pose(RECONFIG_POS_S, Q3_RECONFIG_S, RECONFIG_BRANCH_S)
        q_g, pos_g, quat_g = joints_for_pose(RECONFIG_POS_G, Q3_RECONFIG_G, RECONFIG_BRANCH_G)
    elif kind == "lin_blocked":
        q_s, pos_s, quat_s = joints_for_pose(BLOCKED_POS_S, Q3_BLOCKED_S, BLOCKED_BRANCH)
        q_g, pos_g, quat_g = joints_for_pose(BLOCKED_POS_G, Q3_BLOCKED_G, BLOCKED_BRANCH)
    else:
        raise ValueError(kind)
    noise = shared_noise(seed, kind, sig)
    return {
        "q_s": q_s,
        "q_g": q_g,
        "pos_s": pos_s,
        "pos_g": pos_g,
        "quat_s": quat_s,
        "quat_g": quat_g,
        "noise": noise,
    }


def evaluate(arm, problem):
    q_s, q_g = problem["q_s"], problem["q_g"]
    pos_s, pos_g = problem["pos_s"], problem["pos_g"]
    quat_s, quat_g = problem["quat_s"], problem["quat_g"]
    if arm == "A_ptp":
        path = ptp_path(q_s, q_g)
    elif arm in ("B_lin", "C_lin_blocked"):
        path = lin_path(q_s, pos_s, quat_s, pos_g, quat_g)
    else:
        raise ValueError(arm)
    noisy = apply_noise(path, problem["noise"])
    return path_metrics(path, pos_s, pos_g, noisy)


def run_regime(name, seed, sig=SIG_MEAS):
    kind, _decl = REGIMES[name]
    problem = shared_problem(seed, kind, sig=sig)
    row = {
        "pos_s": problem["pos_s"],
        "pos_g": problem["pos_g"],
        "cart_disp": math.sqrt(sum((a - b) ** 2 for a, b in zip(problem["pos_s"], problem["pos_g"]))),
        "joint_travel": math.sqrt(sum((a - b) ** 2 for a, b in zip(problem["q_s"], problem["q_g"]))),
        "line_hit": 1.0 if segment_hits_obstacle(problem["pos_s"], problem["pos_g"]) else 0.0,
    }
    for arm in ARMS:
        # C is the blocked-line LIN arm; A and B still report bow / collisions
        # on the same shared start, goal and obstacle.
        row[arm] = evaluate(arm, problem)
    return row


def official_rows(name, sig=SIG_MEAS):
    return [run_regime(name, seed, sig=sig) for seed in SEEDS]


def print_regime(title, rows):
    print(f"regime {title}  (mean+-sd over seeds)")
    for key, label in (
        ("cart_disp", "cart_disp_m"),
        ("joint_travel", "joint_travel_rad"),
        ("line_hit", "line_hit"),
    ):
        xs = [r[key] for r in rows]
        print(f"  {label} {num(mean_sd(xs)[0])}+-{num(mean_sd(xs)[1])}")
    for arm in ARMS:
        bow = [r[arm]["bow_m"] for r in rows]
        col = [r[arm]["n_collide"] for r in rows]
        print(
            f"  {arm} bow_m {num(mean_sd(bow)[0])}+-{num(mean_sd(bow)[1])} "
            f"n_collide {num(mean_sd(col)[0])}+-{num(mean_sd(col)[1])}"
        )
    for left, right in PAIRS:
        la = [a for a in ARMS if a.startswith(left)][0]
        ra = [a for a in ARMS if a.startswith(right)][0]
        for key in METRICS:
            xa = [r[la][key] for r in rows]
            xb = [r[ra][key] for r in rows]
            print(f"  paired {left}-{right} {key}: {verdict(xa, xb)}")


def main():
    reach = L1 + L2
    fold = abs(L1 - L2)
    print("Synthetic Pilz LIN vs PTP path-shape stand-in; not a real MoveIt plan")
    print(
        f"declared L1={num(L1)} m L2={num(L2)} m N_PATH={N_PATH} "
        f"SIG_MEAS={num(SIG_MEAS)} m SMALL_FRAC={num(SMALL_FRAC)} "
        f"seeds={','.join(str(s) for s in SEEDS)}"
    )
    print(f"hand_calc reach L1+L2 = {num(reach)} m")
    print(f"hand_calc fold abs(L1-L2) = {num(fold)} m")
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print("hand_calc SIG_MEAS = 0.0004 m")
    print(f"hand_calc N_PATH inclusive samples = {N_PATH}")
    print(
        f"hand_calc short_straight q_s={num(SHORT_Q_S[0])},{num(SHORT_Q_S[1])},{num(SHORT_Q_S[2])} "
        f"q_g={num(SHORT_Q_G[0])},{num(SHORT_Q_G[1])},{num(SHORT_Q_G[2])} rad"
    )
    print(
        f"hand_calc long_reconfig pos_s={num(RECONFIG_POS_S[0])},{num(RECONFIG_POS_S[1])},{num(RECONFIG_POS_S[2])} "
        f"pos_g={num(RECONFIG_POS_G[0])},{num(RECONFIG_POS_G[1])},{num(RECONFIG_POS_G[2])} m"
    )
    print(
        f"hand_calc lin_blocked pos_s={num(BLOCKED_POS_S[0])},{num(BLOCKED_POS_S[1])},{num(BLOCKED_POS_S[2])} "
        f"pos_g={num(BLOCKED_POS_G[0])},{num(BLOCKED_POS_G[1])},{num(BLOCKED_POS_G[2])} m"
    )
    print(
        f"hand_calc obstacle box x={num(OBS_X_LO)} to {num(OBS_X_HI)} m, "
        f"y={num(OBS_Y_LO)} to {num(OBS_Y_HI)} m"
    )
    print(
        "declared arms: A_ptp synchronized joint interpolation; "
        "B_lin Cartesian line plus quaternion slerp; "
        "C_lin_blocked the same LIN through a blocking obstacle"
    )
    print(
        "docs_commit=cdee39bbc5746a98630a4d631ab7d0184de2f1e1 "
        "(2024-12-31 20:05:15 UTC = 2025-01-01 04:05:15 Asia/Shanghai)"
    )
    print("docs_blob=54f4ee6cc3379f2198ac5d4a9a26349a1428ade0")
    print("docs_rst_sha256=dff95cb2091f121defb32a7ad90c4a9b34786aa3ce73b283699c19436e71a591")
    print(
        "docs_body=moveit2_tutorials main how-to pilz_industrial_motion_planner.rst "
        "(Jazzy branch of that path returned 404 and is not a body; "
        "docs.ros.org served a challenge page and is not a body)"
    )
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: start and goal poses, the arm, the obstacle "
        "and the measurement-noise sequence are shared across arms at each "
        "regime and seed"
    )
    print(
        "Assumptions: 2R-plus-wrist planar stand-in; PTP path is synchronized "
        "linear joint interpolation; LIN is position lerp plus quaternion slerp "
        "then IK; CIRC is named in the lesson and has no toy arm; no RRTConnect"
    )
    print("PTP / LIN / CIRC definitions 以文档为准")
    print("Real MoveIt / Panda / computeCartesianPath: 本页未运行")
    print("declared short_straight: A and B may near-tie on mid-path Cartesian bow - keep")
    print("declared long_reconfig: B consistent smaller Cartesian bow than A - keep")
    print(
        "declared lin_blocked: C loses as a valid approach path because the "
        "line intersects the obstacle - lose kept"
    )

    official = {name: official_rows(name) for name in REGIMES}
    for name, (_kind, decl) in REGIMES.items():
        print(f"declared expectation {name}: {decl}")
        print_regime(name, official[name])

    print(f"alternative same seeds SIG_MEAS={num(SIG_MEAS_ALT)} m (not adopted)")
    print(f"hand_calc official SIG_MEAS={num(SIG_MEAS)} m vs alternative {num(SIG_MEAS_ALT)} m")
    for name in REGIMES:
        print_regime(f"{name} alt_sig={num(SIG_MEAS_ALT)}", official_rows(name, sig=SIG_MEAS_ALT))

    print("No real MoveIt process was started")
    print(
        "No winner is universal: a short, already nearly straight joint move "
        "may near-tie on bow; a long reconfiguration bows under PTP; a LIN "
        "through a wall is not a valid approach, and neither PTP nor LIN is "
        "a collision-avoiding planner"
    )


if __name__ == "__main__":
    main()
