#!/usr/bin/env python3
"""Synthetic redundant inverse kinematics with a nullspace secondary task.

Stdlib only. A new 4R planar arm with a 2-D tip-position task, so the
Jacobian is 2 by 4 (n > m). This is not the lesson's 3-joint SO-101 model
and is not a rewrite of kinematics.py. That 3 x 3 position Jacobian is not
redundant for a 3-D tip-position task.

The minimum-two-norm primary velocity is theta_dot = J^+ v, Modern Robotics
Dec 2019 preprint Eq. 6.7 (以原文为准). The unweighted update
theta_dot = J^+ v + (I - J^+ J) z is the unweighted specialization of the
Modern Robotics weighted form theta_dot = G Vd + (I - G J) M^{-1} grad h
with G = J^+, plus the Moore-Penrose projector identity I - A^+ A onto
ker(A). It is not a verbatim Modern Robotics equation. MR discusses a
spatial case with n > 6; this toy is a smaller rectangular (n > m) model
for the same projector idea, not a claim that MR requires n > 6 for a
planar example.

Arms:
  A_min_norm -- primary only, theta_dot = J^+ v, no secondary task
  B_projected -- primary plus a nullspace-projected secondary task
  C_unprojected -- the same secondary velocity added without the projector
    (a component in the range of J^T pollutes the primary)

Shared rectangular arm, shared primary target, shared preferred posture,
shared numerical noise under common random numbers.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.

Real arm / MoveIt / TRAC-IK: 本页未运行. Wikipedia and Modern Robotics figures
are 以原文为准 and are not toy outputs.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000
RANK_TOL = 1e-10

# Declared 4R planar geometry and gains (not a datasheet, not the SO-101 model).
LINKS = (0.1000, 0.1000, 0.1000, 0.1000)  # m
N_JOINTS = 4
N_TASK = 2
DT = 0.0200  # s
N_STEP = 80
KP = 4.0000  # 1/s, primary task gain
KS = 2.0000  # 1/s, secondary posture gain
SIG_TIP = 0.0002  # m, shared tip-measurement noise

Q_PREF = (0.6000, 0.7000, 0.5000, 0.4000)  # rad
# mid_workspace starts on the preferred posture (secondary already satisfied).
Q_MID = Q_PREF
# near a joint limit: same first three joints, last joint near +2.0 rad.
Q_LIMIT = (0.6000, 0.7000, 0.5000, 2.0000)
# fully stretched: rank-deficient J for a 2-D position task.
Q_STRETCH = (0.0000, 0.0000, 0.0000, 0.0000)

# Primary targets are declared offsets from the mid-workspace tip, in metres.
MID_OFFSET = (0.0300, -0.0200)
LIMIT_OFFSET = (0.0200, 0.0250)

ARMS = ("A_min_norm", "B_projected", "C_unprojected")
METRICS = ("primary_mm", "secondary_cost")
PAIRS = (("B", "A"), ("C", "A"), ("C", "B"))

# name: (q0, offset, declared expectation); written before the first run
REGIMES = {
    "mid_workspace": (
        Q_MID,
        MID_OFFSET,
        "A and B may near-tie on primary error (secondary already satisfied) - keep",
    ),
    "near_joint_limit": (
        Q_LIMIT,
        LIMIT_OFFSET,
        "B consistent better secondary cost at comparable primary error - keep",
    ),
}


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-5:
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


def matmul(a, b):
    bt = list(zip(*b))
    return [[sum(x * y for x, y in zip(row, col)) for col in bt] for row in a]


def transpose(a):
    return [list(row) for row in zip(*a)]


def matvec(a, x):
    return [sum(aij * xj for aij, xj in zip(row, x)) for row in a]


def add(u, v, s=1.0):
    return [ui + s * vi for ui, vi in zip(u, v)]


def scale(u, s):
    return [s * ui for ui in u]


def ident(n):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def frobenius(a):
    return math.sqrt(sum(x * x for row in a for x in row))


def invert_2x2(m):
    a, b, c, d = m[0][0], m[0][1], m[1][0], m[1][1]
    det = a * d - b * c
    if abs(det) <= RANK_TOL:
        return det, None
    inv_det = 1.0 / det
    return det, [[d * inv_det, -b * inv_det], [-c * inv_det, a * inv_det]]


def pinv_and_rank(j):
    """Right-looking Moore-Penrose inverse of a 2 by n Jacobian.

    Full row rank: J^+ = J^T (J J^T)^{-1}. Rank-deficient: J^+ = J^T (J J^T)^+
    from the 2 x 2 eigendecomposition of J J^T.
    """
    jt = transpose(j)
    jjt = matmul(j, jt)
    det, inv = invert_2x2(jjt)
    if inv is not None:
        return matmul(jt, inv), 2, det
    tr = jjt[0][0] + jjt[1][1]
    # Symmetric 2 x 2: eigenvalues (tr +- sqrt(tr^2 - 4 det))/2, but det ~ 0.
    disc = max(0.0, tr * tr - 4.0 * det)
    root = math.sqrt(disc)
    ev = [(tr + root) / 2.0, (tr - root) / 2.0]
    # Eigenvectors of a symmetric 2 x 2.
    def eigvec(lam):
        a, b = jjt[0][0] - lam, jjt[0][1]
        if abs(b) >= abs(a) and abs(b) > RANK_TOL:
            v = [1.0, -a / b]
        elif abs(a) > RANK_TOL:
            v = [-b / a, 1.0]
        else:
            v = [1.0, 0.0] if lam == ev[0] else [0.0, 1.0]
        nrm = math.hypot(v[0], v[1]) or 1.0
        return [v[0] / nrm, v[1] / nrm]

    u0, u1 = eigvec(ev[0]), eigvec(ev[1])
    # Orthonormalize u1 against u0 if needed.
    dot = u0[0] * u1[0] + u0[1] * u1[1]
    u1 = [u1[0] - dot * u0[0], u1[1] - dot * u0[1]]
    n1 = math.hypot(u1[0], u1[1])
    if n1 > RANK_TOL:
        u1 = [u1[0] / n1, u1[1] / n1]
    else:
        u1 = [-u0[1], u0[0]]
    pinv_jjt = [[0.0, 0.0], [0.0, 0.0]]
    rank = 0
    for lam, u in ((ev[0], u0), (ev[1], u1)):
        if lam > RANK_TOL:
            rank += 1
            inv_lam = 1.0 / lam
            for r in range(2):
                for c in range(2):
                    pinv_jjt[r][c] += inv_lam * u[r] * u[c]
    return matmul(jt, pinv_jjt), rank, det


def nullspace_projector(j, jp):
    n = len(jp)
    jp_j = matmul(jp, j)
    eye = ident(n)
    return [[eye[i][k] - jp_j[i][k] for k in range(n)] for i in range(n)]


def cumulative_angles(q):
    acc = 0.0
    out = []
    for qi in q:
        acc += qi
        out.append(acc)
    return out


def fk(q, links=LINKS):
    x = y = 0.0
    acc = 0.0
    for qi, li in zip(q, links):
        acc += qi
        x += li * math.cos(acc)
        y += li * math.sin(acc)
    return [x, y]


def jacobian(q, links=LINKS):
    """Analytical 2 x 4 position Jacobian of the 4R planar arm."""
    acc = cumulative_angles(q)
    # J[:, k] = d(x,y)/d q_{k+1} = sum_{i>=k} Li * (-sin, cos) of acc_i
    cols_x = [0.0] * len(q)
    cols_y = [0.0] * len(q)
    for i, (ang, li) in enumerate(zip(acc, links)):
        dx, dy = -li * math.sin(ang), li * math.cos(ang)
        for k in range(i + 1):
            cols_x[k] += dx
            cols_y[k] += dy
    return [cols_x, cols_y]


def secondary_cost(q, q_pref=Q_PREF):
    return 0.5 * sum((qi - pi) ** 2 for qi, pi in zip(q, q_pref))


def secondary_velocity(q, ks=KS, q_pref=Q_PREF):
    return [ks * (pi - qi) for qi, pi in zip(q, q_pref)]


def step_arm(arm, q, x_des, noise, ks=KS, links=LINKS):
    x = add(fk(q, links), noise)
    v = scale(add(x_des, x, -1.0), KP)
    j = jacobian(q, links)
    jp, rank, _det = pinv_and_rank(j)
    qdot_p = matvec(jp, v)
    z = secondary_velocity(q, ks)
    if arm == "A_min_norm":
        qdot = qdot_p
    elif arm == "B_projected":
        p = nullspace_projector(j, jp)
        qdot = add(qdot_p, matvec(p, z))
    elif arm == "C_unprojected":
        qdot = add(qdot_p, z)
    else:
        raise ValueError(arm)
    q_next = add(q, scale(qdot, DT))
    return q_next, rank


def rng_for(*parts):
    h = 20261119
    for p in parts:
        if isinstance(p, str):
            for ch in p:
                h = (h * 131 + ord(ch)) & 0xFFFFFFFFFFFFFFFF
        else:
            h = (h * 131 + int(p)) & 0xFFFFFFFFFFFFFFFF
    return random.Random(h)


def shared_noise(seed, n_step=N_STEP, sig=SIG_TIP, tag="official"):
    """Common random numbers: tip-measurement noise shared across arms."""
    rng = rng_for("ik-noise", tag, seed, int(round(sig * 1e9)))
    return [[rng.gauss(0.0, sig), rng.gauss(0.0, sig)] for _ in range(n_step)]


def simulate(arm, q0, x_des, noise, ks=KS, links=LINKS):
    q = list(q0)
    ranks = []
    for eps in noise:
        q, rank = step_arm(arm, q, x_des, eps, ks=ks, links=links)
        ranks.append(rank)
    tip = fk(q, links)
    primary_mm = 1000.0 * math.hypot(tip[0] - x_des[0], tip[1] - x_des[1])
    return {
        "primary_mm": primary_mm,
        "secondary_cost": secondary_cost(q),
        "min_rank": min(ranks) if ranks else 0,
        "q": q,
        "tip": tip,
    }


def run_regime(name, seed, ks=KS, links=LINKS, sig=SIG_TIP):
    q0, offset, _decl = REGIMES[name]
    x0 = fk(q0, links)
    x_des = add(x0, offset)
    noise = shared_noise(seed, sig=sig, tag=name)
    return {arm: simulate(arm, q0, x_des, noise, ks=ks, links=links) for arm in ARMS}


def print_regime(title, rows):
    print(f"regime {title}  (mean+-sd over seeds)")
    for arm in ARMS:
        pri = [r[arm]["primary_mm"] for r in rows]
        sec = [r[arm]["secondary_cost"] for r in rows]
        print(
            f"  {arm} primary_mm {num(mean_sd(pri)[0])}+-{num(mean_sd(pri)[1])} "
            f"secondary_cost {num(mean_sd(sec)[0])}+-{num(mean_sd(sec)[1])}"
        )
    for left, right in PAIRS:
        la = [a for a in ARMS if a.startswith(left)][0]
        ra = [a for a in ARMS if a.startswith(right)][0]
        for key in METRICS:
            xa = [r[la][key] for r in rows]
            xb = [r[ra][key] for r in rows]
            print(f"  paired {left}-{right} {key}: {verdict(xa, xb)}")


def official_rows(name, **kwargs):
    return [run_regime(name, seed, **kwargs) for seed in SEEDS]


def describe_config(label, q, links=LINKS):
    j = jacobian(q, links)
    jp, rank, det = pinv_and_rank(j)
    p = nullspace_projector(j, jp)
    residual = matmul(j, p)
    tip = fk(q, links)
    print(
        f"hand_calc {label} q=({', '.join(num(qi) for qi in q)}) rad "
        f"tip=({num(tip[0])}, {num(tip[1])}) m rank={rank} det(JJt)={num(det)} "
        f"proj_residual_frob={num(frobenius(residual))}"
    )
    return j, jp, rank, det, residual, tip


def main():
    reach = sum(LINKS)
    print("Synthetic 4R planar redundant IK; 2-D tip task; Jacobian is 2 by 4 (n>m)")
    print("Not the lesson 3 x 3 SO-101 position Jacobian; that model is not redundant for a 3-D tip-position task")
    print(
        f"declared LINKS_m={','.join(num(x) for x in LINKS)} reach_max_m={num(reach)} "
        f"DT={num(DT)} N_STEP={N_STEP} KP={num(KP)} KS={num(KS)} SIG_TIP_m={num(SIG_TIP)}"
    )
    print(f"declared Q_PREF_rad={','.join(num(x) for x in Q_PREF)}")
    print(f"declared Q_MID_rad={','.join(num(x) for x in Q_MID)}")
    print(f"declared Q_LIMIT_rad={','.join(num(x) for x in Q_LIMIT)}")
    print(f"declared MID_OFFSET_m={num(MID_OFFSET[0])},{num(MID_OFFSET[1])}")
    print(f"declared LIMIT_OFFSET_m={num(LIMIT_OFFSET[0])},{num(LIMIT_OFFSET[1])}")
    print(f"declared SMALL_FRAC={num(SMALL_FRAC)} seeds={','.join(str(s) for s in SEEDS)}")
    print("unweighted specialization: theta_dot = J^+ v + (I-J^+ J) z of the MR weighted form plus the MP projector; not a verbatim MR equation")
    print("MR Eq. 6.7 and the weighted secondary form, and the Wikipedia projector identities, 以原文为准")
    print("hand_calc reach_max = 4 * 0.1000 = 0.4000 m")
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print(f"hand_calc horizon = N_STEP * DT = {num(N_STEP * DT)} s")
    describe_config("mid_start", Q_MID)
    describe_config("limit_start", Q_LIMIT)
    describe_config("stretched", Q_STRETCH)
    # Stretched arm: print rank and do not invent a secondary-task win.
    j_s = jacobian(Q_STRETCH)
    _jp_s, rank_s, det_s = pinv_and_rank(j_s)
    print(
        f"rank_deficient stretched configuration: rank={rank_s} det(JJt)={num(det_s)}; "
        "no secondary-task win is declared at a rank-deficient J"
    )
    # One step in the unreachable x direction, shared, for disclosure only.
    v_x = [0.0500, 0.0000]
    jp_s, rank_s, _ = pinv_and_rank(j_s)
    qdot_try = matvec(jp_s, v_x)
    dx = matvec(j_s, qdot_try)
    print(
        f"hand_calc stretched v=(0.0500, 0.0000) m/s maps to J J^+ v="
        f"({num(dx[0])}, {num(dx[1])}) m/s; primary x motion cannot be produced"
    )
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: the tip-measurement noise sequence is shared across arms at each regime and seed")
    print("Real arm / MoveIt / TRAC-IK: 本页未运行")
    print("declared mid_workspace: A and B may near-tie on primary error - keep")
    print("declared near_joint_limit: B consistent better secondary cost at comparable primary error - keep")
    print("declared C loses on primary error - keep")

    official = {name: official_rows(name) for name in REGIMES}
    for name, (_q0, _off, decl) in REGIMES.items():
        print(f"declared expectation {name}: {decl}")
        print_regime(name, official[name])

    print("alternative same seeds KS=0.5000 (not adopted)")
    for name in REGIMES:
        print_regime(f"{name} alt_KS=0.5000", official_rows(name, ks=0.5000))

    print("No winner is universal: mid-workspace primary error can tie; the projector is what keeps the secondary task off the primary")


if __name__ == "__main__":
    main()
