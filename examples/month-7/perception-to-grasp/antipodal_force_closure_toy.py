#!/usr/bin/env python3
"""Synthetic planar two-finger grasps: antipodal force closure and an epsilon proxy. Stdlib only.

Model assumptions (also stated in the lesson prose):
  planar rigid object (a disc = cylinder cross-section, or a box), quasi-static;
  two point contacts with Coulomb friction, the 2D friction cone written as two
  edges n_in +- mu t (normal component 1); the jaws close along a line and the
  fingers land where that line meets the TRUE object outline. Wrench w =
  (fx, fy, tau / L) with L the object's largest radius (the torque scale is a
  choice; the toy also reports how often B's pick changes with L / 2).
  Grasp wrench space with a bounded sum of normal forces (L1): the convex hull
  of the four primitive wrenches. Force closure <=> the origin is strictly inside
  that hull; epsilon = distance from the origin to the nearest hull facet.
  Planar on purpose: with point contacts in 3D two fingers cannot resist torque
  about the grasp axis, so the 6D hull of a two-finger grasp is degenerate.

Arms (common random numbers: per (regime, seed, trial) the perceived pose, the 8
jaw candidates and the disturbance wrench are drawn once and shared):
  A_random      first candidate of the shared list, no antipodal / FC check
  B_antipodal   candidate with the largest epsilon computed on the PERCEIVED
                object (perception error is not removed), executed on the truth
  C_frictionless B's grasp executed with mu = 0 (antipodal but frictionless)

Metrics per seed (means over 40 trials): fc (force-closure rate on the true
object), eps (epsilon proxy, 0 when not force closure), lift (stand-in: can the
grasp resist the shared disturbance wrench with total normal force <= 1?).

Labels: tie = identical on every seed; |m| < 1e-9 and sd < 1e-9 = numerically
zero (floating-point residue), effectively a tie, no sign count; |paired mean| <= sd = near-tie / small
gap within seed noise; |m| > sd = consistent gap (small if |m| < 20 % of the
smaller arm mean, else clear), always with a sign count.
Real gripper / Dex-Net GQ-CNN / GPU: 本页未运行. Paper statements: 以论文为准.
"""
from __future__ import annotations

import itertools
import math
import random

SEEDS = (0, 1, 2, 3, 4)
TRIALS = 40
CANDS = 8
ARMS = ("A_random", "B_antipodal", "C_frictionless")
METRICS = ("fc", "eps", "lift")
# name, shape, half sizes (m), mu, centre sd / half size, angle sd (deg), candidate mode
REGIMES = (
    ("disc_noisy_centre", "disc", (0.04, 0.04), 0.5, 0.25, 0.0, "random"),
    ("box_near_perfect", "box", (0.04, 0.025), 0.5, 0.0, 0.0, "aligned"),
    ("box_pose_error", "box", (0.04, 0.025), 0.3, 0.25, 20.0, "random"),
)


def rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1])


def hit(shape, half, pose, c, d):
    """Entry / exit of the line c + l d through the object at pose (x, y, angle):
    returns ((p1, n1), (p2, n2)) with outward normals, or None if it misses."""
    ox, oy, oa = pose
    lc = rot((c[0] - ox, c[1] - oy), -oa)
    ld = rot(d, -oa)
    if shape == "disc":
        r = half[0]
        b = lc[0] * ld[0] + lc[1] * ld[1]
        q = lc[0] ** 2 + lc[1] ** 2 - r * r
        disc = b * b - q
        if disc <= 0:
            return None
        ls = (-b - math.sqrt(disc), -b + math.sqrt(disc))
        pts = [(lc[0] + l * ld[0], lc[1] + l * ld[1]) for l in ls]
        nrm = [(p[0] / r, p[1] / r) for p in pts]
    else:
        lo, hi, n_lo, n_hi = -math.inf, math.inf, None, None
        for k in range(2):
            if abs(ld[k]) < 1e-12:
                if abs(lc[k]) >= half[k]:
                    return None
                continue
            a1, a2 = (-half[k] - lc[k]) / ld[k], (half[k] - lc[k]) / ld[k]
            e1 = tuple(-1.0 if j == k else 0.0 for j in range(2))
            e2 = tuple(1.0 if j == k else 0.0 for j in range(2))
            if a1 > a2:
                a1, a2, e1, e2 = a2, a1, e2, e1
            if a1 > lo:
                lo, n_lo = a1, e1
            if a2 < hi:
                hi, n_hi = a2, e2
        if lo >= hi:
            return None
        pts = [(lc[0] + lo * ld[0], lc[1] + lo * ld[1]), (lc[0] + hi * ld[0], lc[1] + hi * ld[1])]
        nrm = [n_lo, n_hi]
    out = []
    for p, n in zip(pts, nrm):
        pw = rot(p, oa)
        out.append(((pw[0] + ox, pw[1] + oy), rot(n, oa)))
    return out


def primitive_wrenches(contacts, centre, mu, scale):
    """Two friction-cone edges per contact, normal force 1: w = (f, (p - centre) x f / L)."""
    ws = []
    for p, n in contacts:
        ni = (-n[0], -n[1])
        t = (-ni[1], ni[0])
        for sgn in (1.0, -1.0):
            f = (ni[0] + sgn * mu * t[0], ni[1] + sgn * mu * t[1])
            rx, ry = p[0] - centre[0], p[1] - centre[1]
            ws.append((f[0], f[1], (rx * f[1] - ry * f[0]) / scale))
    return ws


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def epsilon(ws):
    """Origin strictly inside the tetrahedron of the four wrenches -> distance to the
    nearest facet; otherwise 0 (not force closure). Degenerate hull -> 0."""
    vol = dot(sub(ws[1], ws[0]), cross3(sub(ws[2], ws[0]), sub(ws[3], ws[0])))
    if abs(vol) < 1e-12:
        return 0.0
    best = math.inf
    for i in range(4):
        a, b, c = (ws[j] for j in range(4) if j != i)
        nrm = cross3(sub(b, a), sub(c, a))
        ln = math.sqrt(dot(nrm, nrm))
        if dot(nrm, sub(ws[i], a)) > 0:
            nrm = tuple(-x for x in nrm)
        dist = dot(nrm, a) / ln  # outward normal: origin inside <=> n.(0 - a) < 0, so n.a > 0
        if dist <= 0:
            return 0.0
        best = min(best, dist)
    return best


def solve3(m, v):
    d = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
         + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    if abs(d) < 1e-12:
        return None
    out = []
    for k in range(3):
        mk = [[v[i] if j == k else m[i][j] for j in range(3)] for i in range(3)]
        out.append((mk[0][0] * (mk[1][1] * mk[2][2] - mk[1][2] * mk[2][1]) - mk[0][1] * (mk[1][0] * mk[2][2] - mk[1][2] * mk[2][0])
                    + mk[0][2] * (mk[1][0] * mk[2][1] - mk[1][1] * mk[2][0])) / d)
    return out


def resists(ws, w_dist):
    """Is -w_dist in conv({0} U ws), i.e. sum(l_i w_i) = -w_dist, l >= 0, sum(l) <= 1?
    A basic solution uses at most three wrenches, so all triples are tried."""
    q = tuple(-x for x in w_dist)
    for tri in itertools.combinations(ws, 3):
        lam = solve3([[tri[j][i] for j in range(3)] for i in range(3)], q)
        if lam and min(lam) >= -1e-12 and sum(lam) <= 1.0 + 1e-12:
            return True
    return False


def trial_draws(regime, seed, k):
    """Common random numbers for one trial: perceived pose, candidates, disturbance."""
    name, shape, half, mu, c_sd, a_sd, mode = regime
    rng = random.Random(100000 * [r[0] for r in REGIMES].index(name) + 1000 * seed + k)
    true_pose = (0.0, 0.0, rng.uniform(0, math.pi) if shape == "box" else 0.0)
    size = max(half)
    seen = (true_pose[0] + rng.gauss(0, c_sd * size), true_pose[1] + rng.gauss(0, c_sd * size),
            true_pose[2] + math.radians(rng.gauss(0, a_sd)) if a_sd else true_pose[2])
    cands = []
    for _ in range(CANDS):
        if mode == "aligned":
            th = seen[2] + rng.choice((0.0, math.pi / 2)) + math.radians(rng.gauss(0, 2.0))
            off = rng.uniform(-0.1, 0.1) * size
        else:
            th = rng.uniform(0, math.pi)
            off = rng.uniform(-0.7, 0.7) * size
        cands.append((th, off))
    w = (rng.gauss(0, 0.15), -rng.uniform(0.1, 0.4), rng.gauss(0, 0.1))
    return true_pose, seen, cands, w


def jaw(seen, cand):
    th, off = cand
    d = (math.cos(th), math.sin(th))
    return (seen[0] - off * d[1], seen[1] + off * d[0]), d


def quality(shape, half, pose, mu, c, d, scale):
    con = hit(shape, half, pose, c, d)
    if con is None:
        return 0.0, None
    return epsilon(primitive_wrenches(con, pose[:2], mu, scale)), con


def pick_b(regime, seen, cands, scale):
    """Index of the largest epsilon on the perceived object, and that perceived epsilon."""
    _, shape, half, mu, *_ = regime
    scores = [quality(shape, half, seen, mu, *jaw(seen, c), scale)[0] for c in cands]
    best = max(range(len(cands)), key=lambda i: scores[i])
    return best, scores[best]


def run_trial(regime, seed, k):
    _, shape, half, mu, *_ = regime
    true_pose, seen, cands, w = trial_draws(regime, seed, k)
    scale = max(half) if shape == "disc" else math.hypot(*half)
    ib, seen_eps = pick_b(regime, seen, cands, scale)
    flip = ib != pick_b(regime, seen, cands, scale / 2)[0]
    out = {}
    for arm, idx, m in (("A_random", 0, mu), ("B_antipodal", ib, mu), ("C_frictionless", ib, 0.0)):
        c, d = jaw(seen, cands[idx])
        con = hit(shape, half, true_pose, c, d)
        if con is None:
            out[arm] = {"fc": 0.0, "eps": 0.0, "lift": 0.0}
            continue
        ws = primitive_wrenches(con, true_pose[:2], m, scale)
        e = epsilon(ws)
        out[arm] = {"fc": 1.0 if e > 0 else 0.0, "eps": e, "lift": 1.0 if resists(ws, w) else 0.0}
    fooled = seen_eps > 0 and out["B_antipodal"]["fc"] == 0.0
    return out, flip, fooled


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
    if x != 0.0 and abs(x) < 5e-4:
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


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


NUM_ZERO = 1e-9  # |m| and sd both below this: floating-point residue, not a gap


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(mean_sd(xa)[0], mean_sd(xb)[0]):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def main() -> None:
    print("Synthetic planar two-finger grasps; shared perceived poses / jaw candidates / disturbances; not a real gripper")
    print(f"seeds={len(SEEDS)} trials={TRIALS} candidates={CANDS}; wrench (fx, fy, tau/L), L = largest radius; "
          "sum of normal forces <= 1")
    print("regime arm fc eps lift  (mean+-sd over seeds of the per-seed trial means)")
    for regime in REGIMES:
        name, shape, half, mu, c_sd, a_sd, mode = regime
        per = {arm: {k: [] for k in METRICS} for arm in ARMS}
        flips = fooled = 0
        for seed in SEEDS:
            acc = {arm: {k: 0.0 for k in METRICS} for arm in ARMS}
            for k in range(TRIALS):
                out, flip, fool = run_trial(regime, seed, k)
                flips += flip
                fooled += fool
                for arm in ARMS:
                    for m in METRICS:
                        acc[arm][m] += out[arm][m] / TRIALS
            for arm in ARMS:
                for m in METRICS:
                    per[arm][m].append(acc[arm][m])
        print(f"{name} ({shape} {half[0] * 1e3:.0f}x{half[1] * 1e3:.0f} mm half, mu={mu}, centre sd={c_sd} x size, "
              f"angle sd={a_sd:.0f} deg, {mode} candidates)")
        for arm in ARMS:
            print(f"{name} {arm} " + " ".join("{}+-{}".format(*map(num, mean_sd(per[arm][m]))) for m in METRICS))
        for a, b in (("B_antipodal", "A_random"), ("C_frictionless", "B_antipodal")):
            for m in METRICS:
                print(f"{name} paired {a[0]}-{b[0]} {m}: {verdict(per[a][m], per[b][m])}")
        print(f"{name} torque scale L/2 changes B's pick on {flips} of {len(SEEDS) * TRIALS} trials; "
              f"B's pick is force closure on the perceived object but not on the true one in {fooled} of {len(SEEDS) * TRIALS}")
    print("disc_noisy_centre: a random jaw line misses the true centre; ranking by epsilon finds lines near a diameter")
    print("box_near_perfect: every candidate is already face-to-face, so force closure cannot separate A and B")
    print("box_pose_error: B ranks on a wrongly posed box; it still raises fc, but its lift gain stays within seed noise")
    print("C_frictionless: two frictionless point contacts are never force closure in the plane (eps = 0)")
    print("No winner declared; eps is blind to the task's actual disturbance direction and to the torque scale L")
    print("Real gripper / Dex-Net GQ-CNN / GPU: 本页未运行; paper statements 以论文为准")


if __name__ == "__main__":
    main()
