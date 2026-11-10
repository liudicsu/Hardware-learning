#!/usr/bin/env python3
"""MolmoAct-style action reasoning: depth tokens -> editable 2-D visual trace -> action, vs a direct policy.

Synthetic, stdlib only.  Not ThinkAct (language reasoning plans), not CoT-VLA (one predicted
subgoal image), not TraceVLA (trace drawn as a visual prompt from a tracker).  Real MolmoAct
(7B, 100 depth tokens from a VQVAE, LIBERO / SimplerEnv) / GPU: 本页未运行.  Paper numbers are
以论文为准 (arXiv 2508.07917).

World: a front camera sees the image plane (u = left-right, v = height); z is depth (distance
from the camera).  Coordinates are in [0, 1].  A gripper starts at a random point and must pick an
object resting on the table (v = V_TABLE) and place it in a bin, within T_MAX steps.  In wall
regimes a wall (thickness WALL_T, height WALL_H, all depths) stands between object and bin, so
the gripper must lift over it; touching the wall fails the episode.  A step moves the gripper by
at most V towards the commanded point.  No integration step: the gripper is kinematic; every step's
segment is checked for the wall at SUB points, and V / SUB < WALL_T is asserted so a step cannot
tunnel through the wall.
Perception, shared by every arm (common random numbers): the object, bin and wall positions are
seen with pixel noise PIX_SD in u, v and depth noise Z_SD in z.
Arms:
  A_direct     k-nearest-neighbour policy (K_NN = 3) from observation features straight to the
               action, learned from DEMOS in-task demonstrations (state-action pairs of a noisy
               demonstrator on random scenes of the same regime).
  B_trace      MolmoAct-style: depth perception tokens (observed depth quantised to N_DEPTH
               levels), then a visual reasoning trace of at most 5 image-plane points (gripper,
               object, lift, over, bin, as in the paper's 1 <= L <= 5 polyline), then a
               trajectory-conditioned action: step towards the next trace point, at the depth
               read from the depth token under that point.  The trace is built by a fixed rule
               from the perceived scene: it stands in for a trace head trained on plenty of
               trace data, so this toy measures what a correct, editable trace buys and what a
               wrong one costs, not how hard a trace is to predict.
  C_wrong      B with the trace mirrored left-right (u -> 1 - u): a wrong / frozen trace.
Steering regimes: the instruction names no bin and there are two bins.  The intended bin is
drawn per episode.  A cannot be steered (its features see both bins).  B's trace is edited by
the user to end at the intended bin (the edit is 2-D: image-plane points only).  C keeps the
trace to the other bin.
Regimes and expectations, written before the first run:
  multi_stage_few     wall, DEMOS = 5      B consistent win over A
  multi_stage_many    wall, DEMOS = 200    near-tie (A has enough in-task data)
  single_step         no wall, DEMOS = 5   near-tie (B may lose a little to depth quantisation)
  steer_in_plane      two bins left / right, edited trace: B beats A and the frozen C
  steer_depth         two bins at the same (u, v), one behind the other: a 2-D edit cannot say
                      which; B ties or loses (the paper's out-of-plane limitation)
Metrics per seed (TESTS episodes): success %, final 3-D distance to the intended bin (x100), and
for B / C the 2-D distance from the trace end to the intended bin (x100).
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
V = 0.05            # max step length
SUB = 10            # wall check points per step
R = 0.06            # pick / place tolerance (3-D)
R_TRACE = 0.04      # advance to the next trace point within this distance
T_MAX = 80
V_TABLE = 0.05
WALL_T = 0.06
WALL_H = 0.45
LIFT = 0.12         # demonstrator / trace clearance above the wall
PIX_SD = 0.01
Z_SD = 0.02
N_DEPTH = 16        # depth token levels (the paper uses a 128-code VQVAE; a coarse stand-in)
A_SD = 0.005        # demonstrator action noise
K_NN = 3
TESTS = 40
NUM_ZERO = 1e-9
ARMS = ("A_direct", "B_trace", "C_wrong")
# name: (wall, in-task demos, steering: None / "plane" / "depth")
REGIMES = {
    "multi_stage_few": (True, 5, None),
    "multi_stage_many": (True, 200, None),
    "single_step": (False, 5, None),
    "steer_in_plane": (False, 5, "plane"),
    "steer_depth": (False, 5, "depth"),
}


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def scene(rng, wall, steer):
    """True scene: object, bins (one or two), wall u; the object is left of the bin."""
    obj = [rng.uniform(0.1, 0.3), V_TABLE, rng.uniform(0.3, 0.7)]
    if steer == "plane":
        bins = [[rng.uniform(0.45, 0.6), V_TABLE, rng.uniform(0.3, 0.7)], [rng.uniform(0.75, 0.9), V_TABLE, 0.0]]
        bins[1][2] = rng.uniform(0.3, 0.7)
    elif steer == "depth":
        u, z = rng.uniform(0.6, 0.9), rng.uniform(0.25, 0.4)
        bins = [[u, V_TABLE, z], [u, V_TABLE, z + 0.3]]
    else:
        bins = [[rng.uniform(0.7, 0.9), V_TABLE, rng.uniform(0.3, 0.7)]]
    wall_u = rng.uniform(0.45, 0.55) if wall else None
    return {"obj": obj, "bins": bins, "wall": wall_u}


def hits_wall(p, q, wall_u):
    if wall_u is None:
        return False
    for i in range(SUB + 1):
        u = p[0] + (q[0] - p[0]) * i / SUB
        v = p[1] + (q[1] - p[1]) * i / SUB
        if abs(u - wall_u) <= WALL_T / 2 and v <= WALL_H:
            return True
    return False


def step_to(g, target):
    d = sub(target, g)
    n = norm(d)
    if n <= V:
        return list(target)
    return [x + V * y / n for x, y in zip(g, d)]


def waypoints(sc, b, wall_u):
    """Demonstrator / trace points after the object: lift, over, bin (lift only with a wall)."""
    o, k = sc["obj"], sc["bins"][b]
    if wall_u is None:
        return [k]
    top = WALL_H + LIFT
    return [[o[0], top, o[2]], [k[0], top, k[2]], k]


def features(g, held, sc, wall_u):
    """A's observation features, relative to the gripper; with two bins both are seen."""
    f = [float(held)]
    if not held:
        f += sub(sc["obj"], g)
    else:
        f += [0.0, 0.0, 0.0]
    for k in sc["bins"]:
        f += sub(k, g) if held else [0.0, 0.0, 0.0]
    if wall_u is not None:
        f += [wall_u - g[0], WALL_H - g[1]]
    return f


def demos(rng, wall, steer, n):
    """State-action pairs from a noisy demonstrator; in steering regimes the bin is 50/50."""
    data = []
    for _ in range(n):
        sc = scene(rng, wall, steer)
        b = rng.randrange(len(sc["bins"]))
        g = [rng.uniform(0.05, 0.35), rng.uniform(0.2, 0.4), rng.uniform(0.3, 0.7)]
        plan = [sc["obj"]] + waypoints(sc, b, sc["wall"])
        held, i = 0, 0
        for _ in range(T_MAX):
            nxt = step_to(g, plan[i])
            a = [x - y + rng.gauss(0.0, A_SD) for x, y in zip(nxt, g)]
            data.append((features(g, held, sc, sc["wall"]), a))
            g = [x + y for x, y in zip(g, a)]
            if norm(sub(g, plan[i])) <= R / 2:
                if i == 0:
                    held = 1
                i += 1
                if i == len(plan):
                    break
    return data


def perceive(sc, rng):
    def p(x):
        return [x[0] + rng.gauss(0.0, PIX_SD), x[1] + rng.gauss(0.0, PIX_SD), x[2] + rng.gauss(0.0, Z_SD)]
    return {"obj": p(sc["obj"]), "bins": [p(k) for k in sc["bins"]], "wall": None if sc["wall"] is None else sc["wall"] + rng.gauss(0.0, PIX_SD)}


def depth_token(z):
    lvl = min(N_DEPTH - 1, max(0, int(z * N_DEPTH)))
    return (lvl + 0.5) / N_DEPTH


def depth_under(seen, uv):
    """Depth token at an image point: the nearest surface (smallest z) among scene items there."""
    zs = [x[2] for x in [seen["obj"]] + seen["bins"] if abs(x[0] - uv[0]) < 0.05 and abs(x[1] - uv[1]) < 0.05]
    return depth_token(min(zs)) if zs else None


def trace(seen, g, b, mirror):
    pts = [seen["obj"]] + waypoints(seen, b, seen["wall"])
    uv = [[p[0], p[1]] for p in [g] + pts][:5]
    if mirror:
        uv = [uv[0]] + [[1.0 - u, v] for u, v in uv[1:]]
    return uv


def run_trace(sc, seen, g, b_trace, mirror):
    """B / C: follow the 2-D trace; depth from the depth token under each point (else hold depth)."""
    uv = trace(seen, g, b_trace, mirror)
    zt = depth_token(seen["obj"][2])
    pts = []
    for i, (u, v) in enumerate(uv[1:]):
        z = depth_under(seen, (u, v))
        if z is None:
            z = depth_token(seen["obj"][2]) if i == 0 else zt
        zt = z
        pts.append([u, v, z])
    return pts, uv[-1]


def episode(arm, sc, seen, g, want, wall, table, mirror_other):
    held, i = 0, 0
    if arm != "A_direct":
        b_trace = mirror_other if (arm == "C_wrong" and mirror_other is not None) else want
        pts, end = run_trace(sc, seen, g, b_trace, arm == "C_wrong" and mirror_other is None)
    for _ in range(T_MAX):
        if arm == "A_direct":
            f = features(g, held, seen, seen["wall"])
            near = nearest(table, f)
            a = [sum(r[j] for r in near) / K_NN for j in range(3)]
            n = norm(a)
            q = [x + y * (min(1.0, V / n) if n > 0 else 0.0) for x, y in zip(g, a)]
        else:
            q = step_to(g, pts[i])
            if norm(sub(q, pts[i])) <= R_TRACE and i < len(pts) - 1:
                i += 1
        if hits_wall(g, q, sc["wall"]):
            return 0.0, norm(sub(g, sc["bins"][want])), None if arm == "A_direct" else norm(sub(end, sc["bins"][want][:2]))
        g = q
        if not held and norm(sub(g, sc["obj"])) <= R:
            held = 1
        if held and norm(sub(g, sc["bins"][want])) <= R:
            return 1.0, norm(sub(g, sc["bins"][want])), None if arm == "A_direct" else norm(sub(end, sc["bins"][want][:2]))
    return 0.0, norm(sub(g, sc["bins"][want])), None if arm == "A_direct" else norm(sub(end, sc["bins"][want][:2]))


def shared_draws(regime, seed):
    """Common random numbers: demos, scenes, perception noise, starts and intended bins drawn once."""
    wall, n, steer = REGIMES[regime]
    rng = random.Random(1000 * seed + sorted(REGIMES).index(regime))
    table = demos(rng, wall, steer, n)
    tests = []
    for _ in range(TESTS):
        sc = scene(rng, wall, steer)
        seen = perceive(sc, rng)
        g = [rng.uniform(0.05, 0.35), rng.uniform(0.2, 0.4), rng.uniform(0.3, 0.7)]
        want = rng.randrange(len(sc["bins"]))
        tests.append((sc, seen, g, want))
    return table, tests


def evaluate(arm, regime, draw):
    wall, _, steer = REGIMES[regime]
    table, tests = draw
    succ, err, terr = [], [], []
    for sc, seen, g, want in tests:
        other = None if steer is None else 1 - want
        s, e, t = episode(arm, sc, seen, list(g), want, wall, table, other)
        succ.append(s)
        err.append(e)
        if t is not None:
            terr.append(t)
    out = {"succ": 100.0 * sum(succ) / len(succ), "err": 100.0 * sum(err) / len(err)}
    out["trace"] = 100.0 * sum(terr) / len(terr) if terr else None
    return out


def nearest(table, f):
    """The K_NN rows nearest to f, ordered by (distance, row index): same as heapq.nsmallest, with early exit."""
    best = []
    worst = float("inf")
    for idx, (row, act) in enumerate(table):
        d = 0.0
        for x, y in zip(row, f):
            d += (x - y) * (x - y)
            if d >= worst:
                break
        else:
            best.append((d, idx, act))
            best.sort(key=lambda b: (b[0], b[1]))
            if len(best) > K_NN:
                best.pop()
            if len(best) == K_NN:
                worst = best[-1][0]
    return [b[2] for b in best]


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
    assert V / SUB < WALL_T
    print("Synthetic MolmoAct-style depth tokens -> 2-D trace -> action vs a direct kNN policy vs a mirrored trace; not a 7B model")
    print(f"V={V} SUB={SUB} R={R} T_MAX={T_MAX} WALL_T={WALL_T} WALL_H={WALL_H} PIX_SD={PIX_SD} Z_SD={Z_SD} N_DEPTH={N_DEPTH} K_NN={K_NN} tests={TESTS} seeds={len(SEEDS)}")
    print(f"no integration step: kinematic steps of at most V, wall checked at {SUB} points per step (V/SUB={V / SUB:.3f} < WALL_T={WALL_T})")
    print("regime arm success_% final_err_x100 trace_end_err_x100  (mean+-sd over seeds)")
    for regime, (wall, n, steer) in REGIMES.items():
        print(f"{regime} (wall {'yes' if wall else 'no'}; in-task demos {n}; steering {steer or 'none'})")
        draws = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [evaluate(arm, regime, d) for d in draws] for arm in ARMS}
        for arm in ARMS:
            cols = ["{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in ("succ", "err")]
            cols.append("n/a" if res[arm][0]["trace"] is None else "{}+-{}".format(*map(num, mean_sd([r["trace"] for r in res[arm]]))))
            print(f"  {arm} " + " ".join(cols))
        for x, y in (("B_trace", "A_direct"), ("C_wrong", "B_trace")):
            for key in ("succ", "err"):
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[key] for r in res[x]], [r[key] for r in res[y]])}")
    print("No winner declared: a correct, editable trace helps where the path has stages; a 2-D edit cannot choose along depth")
    print("MolmoAct-7B / LIBERO / SimplerEnv / GPU: 本页未运行; paper numbers 以论文为准")


if __name__ == "__main__":
    main()
