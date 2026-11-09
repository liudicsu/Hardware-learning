#!/usr/bin/env python3
"""Synthetic local-controller toy: Regulated Pure Pursuit vs the Dynamic Window Approach. Stdlib only.

A circular unicycle robot (radius R_ROBOT) drives from (0, 0) to GOAL along a shared global
path. Obstacles are circles. Clutter obstacles are NOT on the global plan (they stand for
things only the local costmap sees), so the global path may run straight through them.
Every arm sees the same obstacles within SENSE metres and gets the same carrot: the first
path point at least LOOKAHEAD metres ahead of the closest path point. Every arm plans with
each obstacle grown by PAD (chosen after the first run; ALT_PADS printed); collisions and
the safety metrics use the true radii. Regimes: empty, open_slow (obstacles 1.2-2.0 m to the
side), clutter_slow / clutter_fast (the same six obstacles within 0.6 m of the path, unknown to
the global plan), narrow_gap (a known wall of 0.15 m posts with an opening at least 0.9 m wide on the path), winding (a known
corridor around a curved path; added after the first run, the first geometry is printed).

Arms (one shared world, one shared slip-noise record per trial):
  A_rpp     Regulated-Pure-Pursuit-style tracker (Macenski et al.): curvature to the carrot
            k = 2 y / L^2, linear speed cut by a curvature rule (radius below R_MIN) and a
            proximity rule (obstacle closer than D_PROX), the smaller of the two kept, never
            below V_REG_MIN; the arc of the command is projected T_COLL seconds ahead
            (at most L metres) and the robot is told to stop if that arc hits something.
            Commands ignore the acceleration limits; the base enforces them.
  B_dwa     Dynamic Window Approach (Fox, Burgard, Thrun 1997): search (v, w) in the window
            reachable in one control period, keep only admissible pairs
            v <= sqrt(2 * dist(v, w) * B_V) (can stop before the first obstacle on the arc),
            maximise G = 2.0 heading + 0.2 dist + 0.2 vel (weights from the paper, no smoothing).
  C_window  the same search and objective as B without the admissibility filter.
  D_dwa_dt  B with the control period counted: v <= sqrt(2 * B_V * (dist - v * DT_CTRL)), because the
            chosen command is held for DT_CTRL before the next decision can brake (added after
            the first run showed B colliding).
When no pair passes the filter, B and D brake as hard as the window allows and straighten.

Base model shared by every arm: |dv/dt| <= A_V, |dw/dt| <= A_W, |w| <= W_MAX; each
integration step H = DT_CTRL / SUBSTEPS moves along a circular arc with the step-average
v and w times (1 + slip), one slip factor for v and one for w per control period, each N(0, SLIP);
the record is drawn once per trial and shared by every arm (common random numbers).
The arc update is exact for constant-deceleration straight braking and has no step-size
stability limit (no feedback inside a step); H vs H / 2 accuracy is printed.
Safety criterion (Fox): a velocity is admissible iff v <= sqrt(2 * dist * B_V); the braking
check is printed at 0.98x and 1.02x of that limit.

Metrics per trial, averaged over TRIALS per seed: success (goal within GOAL_TOL before
T_MAX), collision, time (s; a failed trial counts as T_MAX), clearance (smallest gap to an
obstacle surface, m, 0 after a collision), viol (share of control periods in which the
robot's actual speed was not admissible on its actual arc), sat (share of control periods
whose command lay outside the dynamic window, so the base clipped it).
Labels: tie = identical on every seed; numerically zero = |paired mean| and sd both < 1e-9
(effectively a tie, no sign count); |m| <= sd = near-tie; |m| > sd = consistent gap (small if
|m| < 20 % of the smaller arm mean, else clear), with a sign count.
Real Nav2 / DWB / RPP plugins, real lidar, real robot: 本页未运行. Paper values: 以原文为准.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
TRIALS = 6
R_ROBOT = 0.2
GOAL = (10.0, 0.0)
GOAL_TOL = 0.25
DT_CTRL = 0.25  # control period (Fox et al. use 0.25 s)
SUBSTEPS = 5  # integration step H = 0.05 s
T_MAX = 60.0
SENSE = 3.0  # local-costmap stand-in radius
A_V, A_W = 0.5, 1.5  # base acceleration limits (m/s^2, rad/s^2)
B_V = 0.5  # braking deceleration used in the admissibility test (= A_V)
W_MAX = 1.5
SLIP = 0.03
LOOKAHEAD = 0.9
D_CAP = 3.0  # dist(v, w) when nothing is hit within this arc length
N_V, N_W = 7, 15  # DWA velocity samples
W_HEAD, W_DIST, W_VEL = 2.0, 0.2, 0.2
R_MIN, D_PROX, V_REG_MIN, T_COLL = 0.9, 0.6, 0.25, 1.0
PAD = 0.05  # planning margin added to every obstacle by every arm (chosen after the first run, see ALT_PADS)
ALT_PADS = (0.0, 0.1)
NUM_ZERO = 1e-9
ARMS = ("A_rpp", "B_dwa", "C_window", "D_dwa_dt")
TEST = {"B_dwa": "fox", "C_window": "none", "D_dwa_dt": "dt"}
# name: (v_max, obstacle field)
REGIMES = {
    "empty": (0.4, "none"),
    "open_slow": (0.4, "side"),
    "clutter_slow": (0.4, "clutter"),
    "clutter_fast": (1.2, "clutter"),
    "narrow_gap": (0.8, "gap"),
    "winding": (1.0, "winding"),
}
# winding corridor (regime added after the first run): centreline y = AMP (1 - cos(2 pi x / WAVE)), walls at +-HALF_W
AMP, WAVE, HALF_W = 0.5, 5.0, 0.7
# the first winding geometry tried, kept as a printed alternative: y = 1.0 sin(2 pi x / 5), walls at +-0.6
ALT_WINDING = (1.0, "winding_first")


def world(field, seed, trial):
    """Common random numbers: one obstacle field and global path per (field, seed, trial)."""
    rng = random.Random(f"{field}-{seed}-{trial}")
    path = [(0.0, 0.0), GOAL]
    obs = []
    if field == "side":
        for _ in range(5):
            obs.append((rng.uniform(2.0, 8.0), rng.choice((-1, 1)) * rng.uniform(1.2, 2.0), rng.uniform(0.2, 0.35)))
    elif field == "clutter":
        for _ in range(6):
            obs.append((rng.uniform(2.0, 8.5), rng.uniform(-0.6, 0.6), rng.uniform(0.2, 0.35)))
    elif field in ("winding", "winding_first"):
        if field == "winding":
            path, half_w = [(x, AMP * (1.0 - math.cos(2 * math.pi * x / WAVE))) for x in [i * 0.25 for i in range(41)]], HALF_W
        else:
            path, half_w = [(x, 1.0 * math.sin(2 * math.pi * x / 5.0)) for x in [i * 0.25 for i in range(41)]], 0.6
        dense = densify(path, 0.3)
        for (x0, y0), (x1, y1) in zip(dense, dense[1:]):
            nx, ny = -(y1 - y0), x1 - x0
            n = math.hypot(nx, ny)
            for side in (1, -1):
                obs.append((x0 + side * half_w * nx / n, y0 + side * half_w * ny / n, 0.15))
    elif field == "gap":
        yc, half = rng.uniform(-0.4, 0.4), 0.45
        y = -4.0
        while y <= 4.0:
            if abs(y - yc) > half + 0.15:
                obs.append((5.0, y, 0.15))
            y += 0.25
        path = [(0.0, 0.0), (4.0, yc), (6.0, yc), GOAL]
    return obs, densify(path)


def densify(pts, step=0.05):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        out += [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n)]
    return out + [pts[-1]]


def arc_pose(x, y, th, v, w, t):
    """Exact unicycle pose after t seconds at constant (v, w)."""
    if abs(w) < 1e-9:
        return x + v * t * math.cos(th), y + v * t * math.sin(th), th
    r = v / w
    return (x + r * (math.sin(th + w * t) - math.sin(th)),
            y - r * (math.cos(th + w * t) - math.cos(th)), th + w * t)


def local(x, y, th, obs, pad):
    """Obstacles in the robot frame, inflated by the robot radius and the planning pad."""
    c, s = math.cos(th), math.sin(th)
    loc = [((ox - x) * c + (oy - y) * s, -(ox - x) * s + (oy - y) * c, r + R_ROBOT + pad) for ox, oy, r in obs]
    return sorted(loc, key=lambda o: o[0] * o[0] + o[1] * o[1] - o[2] * o[2])  # nearest first, so the pruning below bites early


def arc_hit_local(v, w, loc, cap=D_CAP):
    """Arc length along the (v, w) curvature from the robot-frame origin to the first inflated obstacle, capped."""
    if v <= 1e-9:
        return cap
    best = cap
    k = w / v
    for px, py, rho in loc:
        d2 = px * px + py * py
        if d2 <= rho * rho:
            return 0.0
        if d2 > (best + rho) * (best + rho):  # an arc is never shorter than the straight line: cannot beat best
            continue
        if abs(k) < 1e-9:
            if abs(py) < rho and px > 0.0:
                best = min(best, px - math.sqrt(rho * rho - py * py))
            continue
        rr = 1.0 / abs(k)
        cy = 1.0 / k  # turning centre (0, cy)
        dx, dy = px, py - cy
        d = math.hypot(dx, dy)
        if d > rr + rho or d < abs(rr - rho) or d == 0.0:
            continue
        a = (rr * rr - rho * rho + d * d) / (2 * d)
        h = math.sqrt(max(0.0, rr * rr - a * a))
        start = math.atan2(-cy, 0.0)
        for sgn in (1, -1):
            ix = a * dx / d - sgn * h * dy / d
            iy = cy + a * dy / d + sgn * h * dx / d
            ang = math.atan2(iy - cy, ix)
            sweep = (ang - start) % (2 * math.pi) if k > 0 else (start - ang) % (2 * math.pi)
            best = min(best, rr * sweep)
    return best


def arc_hit(x, y, th, v, w, obs, cap=D_CAP, pad=0.0):
    """Arc length from the pose along the (v, w) curvature to the first inflated obstacle, capped."""
    return arc_hit_local(v, w, local(x, y, th, obs, pad), cap)


def clearance(x, y, obs):
    return min((math.hypot(ox - x, oy - y) - r - R_ROBOT for ox, oy, r in obs), default=D_CAP)


def carrot(path, idx, x, y, look):
    while idx + 1 < len(path) and math.hypot(path[idx + 1][0] - x, path[idx + 1][1] - y) <= math.hypot(path[idx][0] - x, path[idx][1] - y):
        idx += 1
    j = idx
    while j < len(path) - 1 and math.hypot(path[j][0] - x, path[j][1] - y) < look:
        j += 1
    return idx, path[j]


def rpp(state, tgt, vis, vmax, pad):
    x, y, th, v, w = state
    dx, dy = tgt[0] - x, tgt[1] - y
    ly = -dx * math.sin(th) + dy * math.cos(th)
    L2 = max(dx * dx + dy * dy, 1e-9)
    k = 2.0 * ly / L2
    vc = vmax
    if abs(k) > 1.0 / R_MIN:
        vc = min(vc, vmax / (R_MIN * abs(k)))
    d_o = clearance(x, y, vis) - pad
    if d_o <= D_PROX:
        vc = min(vc, vmax * d_o / D_PROX)
    vc = max(vc, V_REG_MIN)
    wc = max(-W_MAX, min(W_MAX, vc * k))
    if arc_hit(x, y, th, vc, wc, vis, cap=min(vc * T_COLL, math.sqrt(L2)), pad=pad) < min(vc * T_COLL, math.sqrt(L2)):
        return 0.0, 0.0
    return vc, wc


def dwa(state, tgt, vis, vmax, test, pad):
    x, y, th, v, w = state
    vlo, vhi = max(0.0, v - A_V * DT_CTRL), min(vmax, v + A_V * DT_CTRL)
    wlo, whi = max(-W_MAX, w - A_W * DT_CTRL), min(W_MAX, w + A_W * DT_CTRL)
    best, cmd = None, None
    loc = local(x, y, th, vis, pad)
    for i in range(N_V):
        vc = vlo + (vhi - vlo) * i / (N_V - 1)
        for j in range(N_W):
            wc = wlo + (whi - wlo) * j / (N_W - 1)
            dist = arc_hit_local(vc, wc, loc)
            if test == "fox" and vc > math.sqrt(2.0 * dist * B_V):
                continue
            if test == "dt" and vc > math.sqrt(2.0 * max(0.0, dist - vc * DT_CTRL) * B_V):
                continue
            px, py, pth = arc_pose(x, y, th, vc, wc, DT_CTRL)
            err = math.atan2(tgt[1] - py, tgt[0] - px) - pth
            err = abs((err + math.pi) % (2 * math.pi) - math.pi)
            g = W_HEAD * (math.pi - err) / math.pi + W_DIST * dist / D_CAP + W_VEL * vc / vmax
            if best is None or g > best:
                best, cmd = g, (vc, wc)
    if cmd is None:  # nothing admissible: brake as hard as the base allows and straighten
        cmd = (vlo, 0.0 if wlo <= 0.0 <= whi else (wlo if abs(wlo) < abs(whi) else whi))
    return cmd


def run(arm, regime, seed, trial, substeps=SUBSTEPS, pad=PAD, spec=None):
    vmax, field = spec or REGIMES[regime]
    obs, path = world(field, seed, trial)
    rng = random.Random(f"slip-{regime}-{seed}-{trial}")
    n_ctrl = int(T_MAX / DT_CTRL)
    slip = [(rng.gauss(0.0, SLIP), rng.gauss(0.0, SLIP)) for _ in range(n_ctrl)]
    h = DT_CTRL / substeps
    x, y, th, v, w = 0.0, 0.0, 0.0, 0.0, 0.0
    idx, gap, viol, sat = 0, D_CAP, 0, 0
    for n in range(n_ctrl):
        vis = [o for o in obs if math.hypot(o[0] - x, o[1] - y) - o[2] <= SENSE]
        idx, tgt = carrot(path, idx, x, y, LOOKAHEAD)
        if arm == "A_rpp":
            vc, wc = rpp((x, y, th, v, w), tgt, vis, vmax, pad)
        else:
            vc, wc = dwa((x, y, th, v, w), tgt, vis, vmax, TEST[arm], pad)
        if abs(vc - v) > A_V * DT_CTRL + 1e-12 or abs(wc - w) > A_W * DT_CTRL + 1e-12:
            sat += 1
        if v > math.sqrt(2.0 * arc_hit(x, y, th, v, w, obs) * B_V) + 1e-12:
            viol += 1
        sv, sw = slip[n]
        for _ in range(substeps):
            v1 = v + max(-A_V * h, min(A_V * h, vc - v))
            w1 = w + max(-A_W * h, min(A_W * h, wc - w))
            x, y, th = arc_pose(x, y, th, 0.5 * (v + v1) * (1 + sv), 0.5 * (w + w1) * (1 + sw), h)
            v, w = v1, w1
            gap = min(gap, clearance(x, y, obs))
            if gap <= 0.0:
                return {"success": 0.0, "collision": 1.0, "time": T_MAX, "clearance": 0.0, "viol": viol / (n + 1), "sat": sat / (n + 1)}
            if math.hypot(GOAL[0] - x, GOAL[1] - y) < GOAL_TOL:
                return {"success": 1.0, "collision": 0.0, "time": (n + 1) * DT_CTRL, "clearance": gap, "viol": viol / (n + 1), "sat": sat / (n + 1)}
    return {"success": 0.0, "collision": 0.0, "time": T_MAX, "clearance": gap, "viol": viol / n_ctrl, "sat": sat / n_ctrl}


def open_loop(substeps):
    """Fixed command sequence (no slip, no obstacles): the base-model integration alone."""
    h = DT_CTRL / substeps
    x = y = th = v = w = 0.0
    for n in range(40):
        vc, wc = min(1.0, 0.1 * n), 1.2 * math.sin(0.3 * n)
        for _ in range(substeps):
            v1 = v + max(-A_V * h, min(A_V * h, vc - v))
            w1 = w + max(-A_W * h, min(A_W * h, wc - w))
            x, y, th = arc_pose(x, y, th, 0.5 * (v + v1), 0.5 * (w + w1), h)
            v, w = v1, w1
    return x, y, th


def brake_stop(v0, h=DT_CTRL / SUBSTEPS):
    """Straight-line stopping distance from v0 at full deceleration B_V with the toy's step."""
    d, v = 0.0, v0
    while v > 0.0:
        v1 = max(0.0, v - B_V * h)
        d += 0.5 * (v + v1) * h if v1 > 0.0 else v * v / (2 * B_V)
        v = v1
    return d


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


KEYS = ("success", "collision", "time", "clearance", "viol", "sat")
PAIRS = ((("B_dwa", "A_rpp"), ("success", "collision", "time", "clearance")),
         (("D_dwa_dt", "A_rpp"), ("success", "collision", "time", "clearance")),
         (("C_window", "B_dwa"), ("collision", "viol")),
         (("D_dwa_dt", "B_dwa"), ("success", "collision")))


def table(regime, pad=PAD, spec=None):
    """Per-seed trial means for every arm (the same worlds and slip records for every arm)."""
    res = {arm: [] for arm in ARMS}
    for seed in SEEDS:
        for arm in ARMS:
            per = [run(arm, regime, seed, t, pad=pad, spec=spec) for t in range(TRIALS)]
            res[arm].append({k: sum(r[k] for r in per) / TRIALS for k in KEYS})
    return res


def main():
    print("Synthetic local-controller toy; unicycle + circular obstacles; shared worlds / carrot / slip noise; not Nav2")
    print(f"seeds={len(SEEDS)} trials={TRIALS} control={DT_CTRL} s step H={DT_CTRL / SUBSTEPS} s accel {A_V} m/s^2 {A_W} rad/s^2 "
          f"brake B_V={B_V} lookahead={LOOKAHEAD} m sense={SENSE} m pad={PAD} m T_max={T_MAX} s")
    for d in (0.5, 1.0, 2.0):
        lim = math.sqrt(2 * B_V * d)
        print(f"admissibility check: obstacle at {d} m, limit sqrt(2*dist*B_V)={lim:.4f} m/s; "
              f"0.98x stops at {brake_stop(0.98 * lim):.4f} m (before), 1.02x stops at {brake_stop(1.02 * lim):.4f} m (hits)")
    lim = math.sqrt(2 * B_V * 1.0)
    print(f"control-period check: at {lim:.4f} m/s the command is held {DT_CTRL} s before the next decision, "
          f"so the robot covers {lim * DT_CTRL + brake_stop(lim):.4f} m before it can stop (D_dwa_dt subtracts v*dt from dist)")
    a, b = open_loop(SUBSTEPS), open_loop(2 * SUBSTEPS)
    print(f"step check (open loop, fixed command ramp, 10 s): H vs H/2 pose gap {math.hypot(a[0] - b[0], a[1] - b[1]):.3e} m, "
          f"heading gap {abs(a[2] - b[2]):.3e} rad")
    for arm, regime in (("A_rpp", "winding"), ("D_dwa_dt", "clutter_fast")):
        a, b = run(arm, regime, 0, 0), run(arm, regime, 0, 0, substeps=2 * SUBSTEPS)
        print(f"step check: {arm} {regime} seed 0 trial 0, H vs H/2: success {num(a['success'])} vs {num(b['success'])}, "
              f"time {num(a['time'])} vs {num(b['time'])}, clearance {num(a['clearance'])} vs {num(b['clearance'])}")
    print("regime arm success collision time_s clearance_m viol sat  (mean+-sd over seeds of per-seed trial means)")
    for regime, (vmax, field) in REGIMES.items():
        print(f"{regime} (v_max={vmax} m/s, field={field})")
        res = table(regime)
        for arm in ARMS:
            cells = " ".join("{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in KEYS)
            print(f"  {arm} {cells}")
        for (x, y), keys in PAIRS:
            for k in keys:
                print(f"  paired {x[0]}-{y[0]} {k}: {verdict([r[k] for r in res[x]], [r[k] for r in res[y]])}")
    print("alternatives (choices made after the first run; success / collision means over all seeds and trials):")
    for pad in ALT_PADS:
        for regime in ("clutter_slow", "clutter_fast", "narrow_gap", "winding"):
            res = table(regime, pad=pad)
            cells = " ".join(f"{arm} {num(mean_sd([r['success'] for r in res[arm]])[0])}/{num(mean_sd([r['collision'] for r in res[arm]])[0])}" for arm in ARMS)
            print(f"  pad={pad} {regime}: {cells}")
    res = table("winding", spec=ALT_WINDING)
    cells = " ".join(f"{arm} {num(mean_sd([r['success'] for r in res[arm]])[0])}/{num(mean_sd([r['collision'] for r in res[arm]])[0])}" for arm in ARMS)
    print(f"  first winding geometry (y = sin, walls +-0.6 m): {cells}")
    print("No winner declared: RPP tracks a known path, DWA avoids what the path does not know; admissibility needs the control period")
    print("Real Nav2 / DWB / RPP plugins, lidar, robot: 本页未运行; Fox et al. and Macenski et al. values 以原文为准")


if __name__ == "__main__":
    main()
