#!/usr/bin/env python3
"""HAMSTER-style hierarchy: a high-level 2-D path, then a path-conditioned 3-D low-level policy.

Synthetic, stdlib only.  Not an ACT / Diffusion Policy head (earlier sections), not MolmoAct's
depth tokens and trace (Month 6 vla-models), not an OpenVLA-OFT fine-tune.  Real HAMSTER
(VILA-1.5-13B path VLM, RVT-2 / 3D-DA low level, real robot) / GPU: 本页未运行.  Paper numbers
are 以论文为准 (arXiv 2502.05485).

World: a front camera sees the image plane (u, v); z is depth.  The gripper must pick the named
object (on the table) and place it in the bin within T_MAX steps; a distractor object also sits
on the table.  A step moves the gripper by at most V.  No integration step: the gripper is
kinematic and there are no obstacles, so a step's length is the only motion constraint.
Appearance: every scene has a background appearance vector (APP numbers: texture, lighting,
colour).  In-domain demonstrations have background N(0, BG_SD); test scenes have N(SHIFT, BG_SD)
per number, the visual domain gap.
Data, shared by every arm (common random numbers): DEMOS in-domain demonstrations (state-action
pairs of a noisy demonstrator on random in-domain scenes), test scenes, starts, perception noise
and high-level path noise are drawn once per (regime, seed).
Arms:
  A_mono    monolithic policy: k-nearest-neighbour (K_NN = 3) from all observation features
            (object and bin position relative to the gripper, held flag, and the background
            appearance numbers, as an image-in policy sees them) to the action.
  B_hier    high level: a coarse 2-D path [(u, v, gripper)] = start, object (close), bin (open),
            each point off by PATH_SD (the VLM's coarseness; it is trained off-domain, so its
            error does not depend on SHIFT; a stand-in, not a trained VLM).  Low level: the same
            kNN learner on path-relative features only (next path point minus gripper in u, v;
            the point's depth from the 3-D observation minus gripper depth; held flag), learned
            from the same DEMOS with oracle paths, as in the paper.
  C_wrong   B's low level given an off-task path: start, distractor (close), bin (open).
Regimes and expectations, written before the first run:
  visual_shift   SHIFT 0.5, DEMOS 20, PATH_SD 0.02   B consistent win over A
  matched_easy   SHIFT 0,   DEMOS 200, PATH_SD 0.02  near-tie
  coarse_path    SHIFT 0,   DEMOS 200, PATH_SD 0.06  B loses (path error the low level follows)
  C loses to B in every regime.
Added after the first run (none of the three regimes above gave B a tie or a loss):
  no_appearance  SHIFT 0,   DEMOS 200, PATH_SD 0.02, BG_SD 0  near-tie or B loses (without
                 appearance numbers A sees the same geometry as B's low level, and B adds path
                 error); written down before this regime was run.  The three regimes above are
                 unchanged (each keeps its own random stream) and still printed.
Metrics per seed (TESTS episodes): success %, final 3-D distance to the bin (x100), path ADE
(mean 2-D distance of the path points to the true ones, x100; B and C only) and tracking error
(mean 2-D distance from the gripper to its path polyline, x100; B and C only).
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
V = 0.05
R = 0.06
T_MAX = 60
V_TABLE = 0.05
PIX_SD = 0.01
Z_SD = 0.02
APP = 4
BG_SD = 0.1
A_SD = 0.005
K_NN = 3
TESTS = 40
NUM_ZERO = 1e-9
ARMS = ("A_mono", "B_hier", "C_wrong")
# name: (SHIFT, DEMOS, PATH_SD, background sd); the first three were declared before the first run
REGIMES = {
    "visual_shift": (0.5, 20, 0.02, BG_SD),
    "matched_easy": (0.0, 200, 0.02, BG_SD),
    "coarse_path": (0.0, 200, 0.06, BG_SD),
    "no_appearance": (0.0, 200, 0.02, 0.0),  # added after the first run
}
STREAM = {"coarse_path": 0, "matched_easy": 1, "visual_shift": 2, "no_appearance": 3}  # random stream per regime


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def norm(a):
    return math.sqrt(sum(x * x for x in a))


def scene(rng, shift, bg_sd=BG_SD):
    obj = [rng.uniform(0.1, 0.4), V_TABLE, rng.uniform(0.3, 0.7)]
    dis = [rng.uniform(0.1, 0.4), V_TABLE, rng.uniform(0.3, 0.7)]
    while norm(sub(dis, obj)) < 0.15:
        dis = [rng.uniform(0.1, 0.4), V_TABLE, rng.uniform(0.3, 0.7)]
    bin_ = [rng.uniform(0.6, 0.9), V_TABLE, rng.uniform(0.3, 0.7)]
    bg = [rng.gauss(shift, bg_sd) for _ in range(APP)]
    return {"obj": obj, "dis": dis, "bin": bin_, "bg": bg}


def start(rng):
    return [rng.uniform(0.05, 0.45), rng.uniform(0.25, 0.45), rng.uniform(0.3, 0.7)]


def step_to(g, target):
    d = sub(target, g)
    n = norm(d)
    return list(target) if n <= V else [x + V * y / n for x, y in zip(g, d)]


def mono_features(g, held, sc):
    tgt = sc["bin"] if held else sc["obj"]
    return [float(held)] + sub(tgt, g) + list(sc["bg"])


def low_features(g, held, point_uv, depth):
    return [float(held), point_uv[0] - g[0], point_uv[1] - g[1], depth - g[2]]


def demos(rng, n, bg_sd):
    mono, low = [], []
    for _ in range(n):
        sc = scene(rng, 0.0, bg_sd)
        g = start(rng)
        held = 0
        for _ in range(T_MAX):
            tgt = sc["bin"] if held else sc["obj"]
            nxt = step_to(g, tgt)
            a = [x - y + rng.gauss(0.0, A_SD) for x, y in zip(nxt, g)]
            mono.append((mono_features(g, held, sc), a))
            low.append((low_features(g, held, tgt[:2], tgt[2]), a))
            g = [x + y for x, y in zip(g, a)]
            if norm(sub(g, tgt)) <= R / 2:
                if held:
                    break
                held = 1
    return mono, low


def knn_step(table, f, g):
    near = nearest(table, f)
    a = [sum(r[j] for r in near) / K_NN for j in range(3)]
    n = norm(a)
    return [x + y * (min(1.0, V / n) if n > 0 else 0.0) for x, y in zip(g, a)]


def seg_dist(p, a, b):
    d = sub(b, a)
    L = d[0] * d[0] + d[1] * d[1]
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * d[0] + (p[1] - a[1]) * d[1]) / L))
    return norm([p[0] - a[0] - t * d[0], p[1] - a[1] - t * d[1]])


def episode(arm, sc, seen, g, path, tables):
    mono, low = tables
    held, track = 0, []
    for _ in range(T_MAX):
        if arm == "A_mono":
            q = knn_step(mono, mono_features(g, held, seen), g)
        else:
            k = 2 if held else 1
            pick = seen["dis"] if arm == "C_wrong" else seen["obj"]
            depth = seen["bin"][2] if held else pick[2]
            q = knn_step(low, low_features(g, held, path[k][:2], depth), g)
            track.append(min(seg_dist(g, path[i], path[i + 1]) for i in range(2)))
        g = q
        if not held and norm(sub(g, sc["obj"])) <= R:
            held = 1
        if held and norm(sub(g, sc["bin"])) <= R:
            return 1.0, norm(sub(g, sc["bin"])), track
    return 0.0, norm(sub(g, sc["bin"])), track


def shared_draws(regime, seed):
    """Common random numbers: demos, scenes, perception, starts and path noise drawn once."""
    shift, n, path_sd, bg_sd = REGIMES[regime]
    rng = random.Random(1000 * seed + STREAM[regime])
    tables = demos(rng, n, bg_sd)
    tests = []
    for _ in range(TESTS):
        sc = scene(rng, shift, bg_sd)
        seen = {k: [x + rng.gauss(0.0, s) for x, s in zip(sc[k], (PIX_SD, PIX_SD, Z_SD))] for k in ("obj", "dis", "bin")}
        seen["bg"] = sc["bg"]
        g = start(rng)
        noise = [[rng.gauss(0.0, path_sd), rng.gauss(0.0, path_sd)] for _ in range(2)]
        tests.append((sc, seen, g, noise))
    return tables, tests


def make_path(arm, seen, g, noise):
    pick = seen["dis"] if arm == "C_wrong" else seen["obj"]
    return [[g[0], g[1], 1], [pick[0] + noise[0][0], pick[1] + noise[0][1], 0], [seen["bin"][0] + noise[1][0], seen["bin"][1] + noise[1][1], 1]]


def evaluate(arm, regime, draw):
    tables, tests = draw
    succ, err, ade, trk = [], [], [], []
    for sc, seen, g, noise in tests:
        path = make_path(arm, seen, g, noise)
        s, e, track = episode(arm, sc, seen, list(g), path, tables)
        succ.append(s)
        err.append(e)
        if arm != "A_mono":
            ade.append((norm(sub(path[1][:2], sc["obj"][:2])) + norm(sub(path[2][:2], sc["bin"][:2]))) / 2)
            trk.append(sum(track) / len(track))
    out = {"succ": 100.0 * sum(succ) / len(succ), "err": 100.0 * sum(err) / len(err)}
    out["ade"] = 100.0 * sum(ade) / len(ade) if ade else None
    out["trk"] = 100.0 * sum(trk) / len(trk) if trk else None
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
    print("Synthetic HAMSTER-style 2-D path + path-conditioned low level vs a monolithic kNN policy vs an off-task path; not a VLM")
    print(f"V={V} R={R} T_MAX={T_MAX} PIX_SD={PIX_SD} Z_SD={Z_SD} APP={APP} BG_SD={BG_SD} K_NN={K_NN} tests={TESTS} seeds={len(SEEDS)}")
    print("no integration step: kinematic steps of at most V, no obstacles")
    print("regime arm success_% final_err_x100 path_ade_x100 track_err_x100  (mean+-sd over seeds)")
    for regime, (shift, n, path_sd, bg_sd) in REGIMES.items():
        print(f"{regime} (background shift {shift}; background sd {bg_sd}; in-domain demos {n}; path sd {path_sd})")
        draws = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [evaluate(arm, regime, d) for d in draws] for arm in ARMS}
        for arm in ARMS:
            cols = []
            for k in ("succ", "err", "ade", "trk"):
                cols.append("n/a" if res[arm][0][k] is None else "{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))))
            print(f"  {arm} " + " ".join(cols))
        for x, y in (("B_hier", "A_mono"), ("C_wrong", "B_hier")):
            for key in ("succ", "err"):
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[key] for r in res[x]], [r[key] for r in res[y]])}")
    print("No winner declared: the path helps when appearance shifts; a coarse or off-task path is followed faithfully")
    print("HAMSTER VLM / RVT-2 / 3D-DA / real robot / GPU: 本页未运行; paper numbers 以论文为准")


if __name__ == "__main__":
    main()
