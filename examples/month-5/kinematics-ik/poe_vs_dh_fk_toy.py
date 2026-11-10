#!/usr/bin/env python3
"""Synthetic forward kinematics: Denavit-Hartenberg vs product of exponentials (PoE). Stdlib only.

Arm: the lesson's three-joint SO-101 model (base yaw q0, shoulder pitch q1, elbow pitch q2; H = 0.1166 m,
L1 = 0.1160 m, L2 = 0.1350 m; positive pitch lifts the arm, q1 = q2 = 0 points it straight out along x).
Truth: the closed-form planar solution of the lesson, r = L1 cos q1 + L2 cos(q1 + q2),
z = H + L1 sin q1 + L2 sin(q1 + q2), tip orientation Rz(q0) Ry'(q1 + q2) (Ry' pitches about -y).
Arms (same joint angles, same geometry):
  A_dh        standard DH rows (theta, d, a, alpha) = (q0, H, 0, +90 deg), (q1, 0, L1, 0), (q2, 0, L2, 0),
              then a fixed tool rotation Rx(-90 deg) so the DH tool frame matches the lesson's tool frame
  B_poe       space-frame PoE T = e^[xi0]q0 e^[xi1]q1 e^[xi2]q2 M with revolute twists xi = (w, -w x q):
              w0 = (0, 0, 1) through the origin, w1 = w2 = (0, -1, 0) through (0, 0, H) and (L1, 0, H),
              M = home pose (L1 + L2, 0, H) with identity rotation; e^[xi]theta from Rodrigues + the
              Wikipedia translation t = (I - e^[w]theta)(w x v) + w w^T v theta
  C_poe_tilt  B with the elbow axis tilted TILT_DEG = 2 deg about x (a wrong twist, everything else equal)
Common random numbers: per (regime, seed) the N joint configurations and the encoder noise are drawn once
and fed to all three arms. No integration step: every pose is a closed-form product of 4 x 4 matrices, so
no step-size stability criterion applies. Correctness criterion instead: on noise-free regimes
max ||T_DH - T_PoE||_F must be below 1e-12 (asserted), and every rotation block must satisfy
||R^T R - I||_F < 1e-12 (asserted).
Metrics per seed (mean over N configurations): pose = ||T_arm - T_truth||_F, pos_mm = tip position error.
Labels: tie = identical on every seed; numerically zero = |paired mean| and sd both < 1e-9 (floating-point
residue, effectively a tie, no sign count); |m| <= sd = near-tie; |m| > sd = consistent gap (small if
|m| < 20 % of the smaller arm mean, else clear), with a sign count.
Not a manipulability / Yoshikawa or DLS redo, not quaternions. Real arm FK check: 本页未运行.
Wikipedia formulas: 以原文为准.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
H, L1, L2 = 0.1166, 0.1160, 0.1350
TILT_DEG = 2.0
N = 200
NUM_ZERO = 1e-9
ARMS = ("A_dh", "B_poe", "C_poe_tilt")
# name: (q1 range deg, q2 range deg, encoder noise sd deg); pre-declared before the first run
REGIMES = {
    "matched": ((-60.0, 90.0), (-135.0, 135.0), 0.0),
    "near_singular": ((-60.0, 90.0), (-1.0, 1.0), 0.0),
    "encoder_noise": ((-60.0, 90.0), (-135.0, 135.0), 0.2),
}


def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def frob(a, b):
    return math.sqrt(sum((a[i][j] - b[i][j]) ** 2 for i in range(4) for j in range(4)))


def rot_z(t):
    c, s = math.cos(t), math.sin(t)
    return [[c, -s, 0.0, 0.0], [s, c, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def rot_x(t):
    c, s = math.cos(t), math.sin(t)
    return [[1.0, 0.0, 0.0, 0.0], [0.0, c, -s, 0.0], [0.0, s, c, 0.0], [0.0, 0.0, 0.0, 1.0]]


def dh_row(theta, d, a, alpha):
    ct, st, ca, sa = math.cos(theta), math.sin(theta), math.cos(alpha), math.sin(alpha)
    return [[ct, -st * ca, st * sa, a * ct], [st, ct * ca, -ct * sa, a * st], [0.0, sa, ca, d], [0.0, 0.0, 0.0, 1.0]]


def fk_dh(q):
    t = dh_row(q[0], H, 0.0, math.pi / 2)
    t = matmul(t, dh_row(q[1], 0.0, L1, 0.0))
    t = matmul(t, dh_row(q[2], 0.0, L2, 0.0))
    return matmul(t, rot_x(-math.pi / 2))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def twist_exp(w, p, theta):
    """e^[xi]theta for a revolute twist with unit axis w through point p; v = -w x p."""
    v = tuple(-x for x in cross(w, p))
    c, s = math.cos(theta), math.sin(theta)
    wh = [[0.0, -w[2], w[1]], [w[2], 0.0, -w[0]], [-w[1], w[0], 0.0]]
    wh2 = [[sum(wh[i][k] * wh[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    r = [[(1.0 if i == j else 0.0) + s * wh[i][j] + (1 - c) * wh2[i][j] for j in range(3)] for i in range(3)]
    wxv = cross(w, v)
    wv = sum(a * b for a, b in zip(w, v))
    t = [sum(((1.0 if i == j else 0.0) - r[i][j]) * wxv[j] for j in range(3)) + w[i] * wv * theta for i in range(3)]
    return [r[0] + [t[0]], r[1] + [t[1]], r[2] + [t[2]], [0.0, 0.0, 0.0, 1.0]]


def axes(arm):
    w2 = (0.0, -1.0, 0.0)
    if arm == "C_poe_tilt":
        g = math.radians(TILT_DEG)
        w2 = (0.0, -math.cos(g), math.sin(g))
    return [((0.0, 0.0, 1.0), (0.0, 0.0, 0.0)), ((0.0, -1.0, 0.0), (0.0, 0.0, H)), (w2, (L1, 0.0, H))]


def fk_poe(q, arm="B_poe"):
    m = [[1.0, 0.0, 0.0, L1 + L2], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, H], [0.0, 0.0, 0.0, 1.0]]
    t = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    for (w, p), th in zip(axes(arm), q):
        t = matmul(t, twist_exp(w, p, th))
    return matmul(t, m)


def truth(q):
    q0, q1, q2 = q
    r = L1 * math.cos(q1) + L2 * math.cos(q1 + q2)
    z = H + L1 * math.sin(q1) + L2 * math.sin(q1 + q2)
    c0, s0, c, s = math.cos(q0), math.sin(q0), math.cos(q1 + q2), math.sin(q1 + q2)
    return [[c0 * c, -s0, -c0 * s, r * c0], [s0 * c, c0, -s0 * s, r * s0], [s, 0.0, c, z], [0.0, 0.0, 0.0, 1.0]]


def fk(arm, q):
    return fk_dh(q) if arm == "A_dh" else fk_poe(q, arm)


def orth_err(t):
    return math.sqrt(sum((sum(t[k][i] * t[k][j] for k in range(3)) - (1.0 if i == j else 0.0)) ** 2 for i in range(3) for j in range(3)))


def shared_draws(regime, seed):
    """Common random numbers: configurations and encoder noise drawn once per (regime, seed)."""
    (a1, b1), (a2, b2), noise = REGIMES[regime]
    rng = random.Random(1000 * seed + len(regime))
    out = []
    for _ in range(N):
        q = (math.radians(rng.uniform(-180.0, 180.0)), math.radians(rng.uniform(a1, b1)), math.radians(rng.uniform(a2, b2)))
        e = tuple(math.radians(rng.gauss(0.0, noise)) for _ in range(3))
        out.append((q, e))
    return out


def evaluate(arm, draws):
    pose = pos = 0.0
    for q, e in draws:
        t = fk(arm, tuple(a + b for a, b in zip(q, e)))
        g = truth(q)
        pose += frob(t, g)
        pos += 1e3 * math.sqrt(sum((t[i][3] - g[i][3]) ** 2 for i in range(3)))
    return {"pose": pose / len(draws), "pos_mm": pos / len(draws)}


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


KEYS = ("pose", "pos_mm")


def main():
    print("Synthetic FK: DH vs product of exponentials vs PoE with a 2 deg wrong elbow twist; SO-101 3-joint model; not a real arm")
    print(f"H={H} L1={L1} L2={L2} m TILT_DEG={TILT_DEG} N={N} configurations per seed seeds={len(SEEDS)}; no integration step (closed-form products)")
    q = tuple(math.radians(x) for x in (30.0, 45.0, -60.0))
    for arm in ARMS:
        t = fk(arm, q)
        print(f"q=[30, 45, -60] deg {arm}: tip=({t[0][3]:.4f}, {t[1][3]:.4f}, {t[2][3]:.4f}) m")
    print("regime arm pose_frob pos_mm  (mean+-sd over seeds)")
    for regime in REGIMES:
        _, _, noise = REGIMES[regime]
        print(f"{regime} (encoder noise sd={noise} deg)")
        draws = [shared_draws(regime, s) for s in SEEDS]
        if noise == 0.0:
            gap = max(frob(fk_dh(qq), fk_poe(qq)) for d in draws for qq, _ in d)
            orth = max(orth_err(fk(arm, qq)) for arm in ARMS for d in draws for qq, _ in d)
            assert gap < 1e-12 and orth < 1e-12
            print(f"  correctness: max ||T_DH - T_PoE||_F = {gap:.3e} < 1e-12; max ||R^T R - I||_F = {orth:.3e} < 1e-12")
        res = {arm: [evaluate(arm, d) for d in draws] for arm in ARMS}
        for arm in ARMS:
            print(f"  {arm} " + " ".join("{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in KEYS))
        for x, y in (("B_poe", "A_dh"), ("C_poe_tilt", "B_poe")):
            for key in KEYS:
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[key] for r in res[x]], [r[key] for r in res[y]])}")
    print("No winner declared: DH and PoE are two parameterisations of the same chain; a wrong twist is a modelling error either way")
    print("Real arm FK check: 本页未运行; Wikipedia formulas 以原文为准")


if __name__ == "__main__":
    main()
