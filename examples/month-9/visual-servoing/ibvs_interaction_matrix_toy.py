#!/usr/bin/env python3
"""ibvs_interaction_matrix_toy.py: PBVS vs IBVS with one shared estimate (stdlib).

Synthetic free-flying camera, four coplanar points (0.20 m square). Both arms
get the SAME noisy normalized image points, the SAME assumed target model
(scale k), hence the SAME planar pose estimate and depth estimate, the SAME
lambda, step, iteration cap and field-of-view limit.
  PBVS: e = (t, theta*u) of current camera w.r.t. the desired camera, from the
        estimated pose; v = -lambda*R^T t, w = -lambda*theta*u.
  IBVS: e = s - s*, per-point L (2x6) with the estimated depth Zhat,
        v_c = -lambda * L^+ e   (L^+ = (L^T L)^-1 L^T, 8x6 stack).
Point interaction matrix (normalized x, y; depth Z), as in the ViSP tutorial:
  [ -1/Z   0   x/Z   x*y   -(1+x^2)   y ]
  [   0  -1/Z  y/Z  1+y^2   -x*y     -x ]
k = 1 is a correct model; k = 1.5 is a wrong-depth/scale assumption shared by
both arms. A run that loses any point outside |x|,|y| <= FOV stops as lost.
All values synthetic; no OpenCV, camera or robot.
usage: python3 ibvs_interaction_matrix_toy.py
"""
from __future__ import annotations

import math
import random
import statistics

LAMBDA = 0.5      # 1/s, shared gain
DT = 0.1          # s per control step
STEPS = 300       # shared iteration cap
SIGMA = 0.002     # normalized-coordinate noise (about 1.6 px at f=800 px)
FOV = 0.40        # normalized half field of view
SEEDS = (0, 1, 2, 3, 4)
HALF = 0.10       # m, half side of the square target
OBJ = [(-HALF, -HALF, 0.0), (HALF, -HALF, 0.0), (HALF, HALF, 0.0), (-HALF, HALF, 0.0)]
Z_DES = 0.50      # desired camera: identity rotation, 0.5 m in front of target
# name: (camera position in target frame, roll/pitch/yaw degrees, model scale k)
SCENARIOS = {
    "nominal": ((0.05, -0.04, -0.80), (4.0, -3.0, 40.0), 1.0),
    "wrong_Z_k1.5": ((0.05, -0.04, -0.80), (4.0, -3.0, 40.0), 1.5),
    "near_edge": ((-0.12, 0.08, -0.74), (-19.0, 1.0, -79.0), 1.0),
    "roll_170": ((0.00, 0.00, -0.60), (0.0, 0.0, 170.0), 1.0),
}


# ---------- small linear algebra ----------
def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def transpose(a):
    return [list(r) for r in zip(*a)]


def matvec(a, v):
    return [sum(x * y for x, y in zip(row, v)) for row in a]


def solve(a, b):
    """Gaussian elimination with partial pivoting; a is n x n."""
    n = len(a)
    m = [list(a[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        if abs(m[p][c]) < 1e-14:
            raise ValueError("singular")
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                for k in range(c, n + 1):
                    m[r][k] -= f * m[c][k]
    return [m[i][n] / m[i][i] for i in range(n)]


def pinv_apply(L, e):
    """L^+ e via normal equations (L has full column rank 6 for 4 points)."""
    lt = transpose(L)
    return solve(matmul(lt, L), matvec(lt, e))


def jacobi_eigs(s):
    """Eigenvalues of a symmetric matrix (cyclic Jacobi)."""
    a = [list(r) for r in s]
    n = len(a)
    for _ in range(60):
        off = sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off < 1e-22:
            break
        for p in range(n):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-30:
                    continue
                th = 0.5 * math.atan2(2 * a[p][q], a[q][q] - a[p][p])
                c, s_ = math.cos(th), math.sin(th)
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s_ * akq, s_ * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s_ * aqk, s_ * apk + c * aqk
    return sorted(a[i][i] for i in range(n))


def rot_rpy(r, p, y):
    r, p, y = (math.radians(v) for v in (r, p, y))
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return [[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr]]


def expmap(w):
    th = math.sqrt(sum(x * x for x in w))
    if th < 1e-12:
        return [[1.0, -w[2], w[1]], [w[2], 1.0, -w[0]], [-w[1], w[0], 1.0]]
    k = [x / th for x in w]
    c, s = math.cos(th), math.sin(th)
    K = [[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]]
    KK = matmul(K, K)
    return [[(i == j) + s * K[i][j] + (1 - c) * KK[i][j] for j in range(3)] for i in range(3)]


def theta_u(R):
    c = max(-1.0, min(1.0, (R[0][0] + R[1][1] + R[2][2] - 1) / 2))
    th = math.acos(c)
    if th < 1e-9:
        return [0.0, 0.0, 0.0]
    if math.pi - th < 1e-6:  # pick an axis for the 180-degree case
        d = [math.sqrt(max(0.0, (R[i][i] + 1) / 2)) for i in range(3)]
        return [th * x for x in d]
    s = 2 * math.sin(th)
    return [th * (R[2][1] - R[1][2]) / s, th * (R[0][2] - R[2][0]) / s, th * (R[1][0] - R[0][1]) / s]


def orthonormalize(R):
    c0 = R_col(R, 0)
    n0 = math.sqrt(sum(x * x for x in c0))
    c0 = [x / n0 for x in c0]
    c1 = R_col(R, 1)
    d = sum(a * b for a, b in zip(c0, c1))
    c1 = [b - d * a for a, b in zip(c0, c1)]
    n1 = math.sqrt(sum(x * x for x in c1))
    c1 = [x / n1 for x in c1]
    c2 = [c0[1] * c1[2] - c0[2] * c1[1], c0[2] * c1[0] - c0[0] * c1[2], c0[0] * c1[1] - c0[1] * c1[0]]
    return [[c0[i], c1[i], c2[i]] for i in range(3)]


def R_col(R, j):
    return [R[i][j] for i in range(3)]


# ---------- camera geometry ----------
def project(Rw, tw):
    """Camera pose (Rw, tw) in target frame -> normalized points and depths."""
    rt = transpose(Rw)
    pts = []
    for X in OBJ:
        pc = matvec(rt, [X[i] - tw[i] for i in range(3)])
        pts.append((pc[0] / pc[2], pc[1] / pc[2], pc[2]))
    return pts


def interaction(x, y, Z):
    return [[-1 / Z, 0.0, x / Z, x * y, -(1 + x * x), y],
            [0.0, -1 / Z, y / Z, 1 + y * y, -x * y, -x]]


def estimate_pose(meas, k):
    """Planar homography (DLT, h33=1) from the assumed model k*OBJ -> c_R_o, c_t_o."""
    A, b = [], []
    for (X, Y, _), (u, v) in zip(OBJ, meas):
        X, Y = k * X, k * Y
        A.append([X, Y, 1, 0, 0, 0, -u * X, -u * Y]); b.append(u)
        A.append([0, 0, 0, X, Y, 1, -v * X, -v * Y]); b.append(v)
    h = solve(A, b) + [1.0]
    H = [h[0:3], h[3:6], h[6:9]]
    h1, h2, h3 = R_col(H, 0), R_col(H, 1), R_col(H, 2)
    s = 1.0 / math.sqrt(sum(x * x for x in h1))
    if h3[2] * s < 0:
        s = -s
    r1 = [s * x for x in h1]
    r2 = [s * x for x in h2]
    r3 = [r1[1] * r2[2] - r1[2] * r2[1], r1[2] * r2[0] - r1[0] * r2[2], r1[0] * r2[1] - r1[1] * r2[0]]
    R = orthonormalize([[r1[i], r2[i], r3[i]] for i in range(3)])
    return R, [s * x for x in h3]


def run(arm, scenario, seed):
    pos, rpy, k = SCENARIOS[scenario]
    Rw, tw = rot_rpy(*rpy), list(pos)
    desired = project([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0.0, 0.0, -Z_DES])
    s_star = [c for p in desired for c in p[:2]]
    rng = random.Random(1000 * seed + 7)  # same draw sequence for both arms
    path, lost, steps = 0.0, False, 0
    depth0, retreat = -tw[2], 0.0
    for steps in range(1, STEPS + 1):
        true_pts = project(Rw, tw)
        if any(abs(x) > FOV or abs(y) > FOV or Z <= 0 for x, y, Z in true_pts):
            lost = True
            break
        meas = [(x + rng.gauss(0, SIGMA), y + rng.gauss(0, SIGMA)) for x, y, _ in true_pts]
        cRo, cto = estimate_pose(meas, k)
        if arm == "PBVS":
            # desired camera sees the target at c*_R_o = I, c*_t_o = (0,0,Z_DES)
            # current camera w.r.t. desired: c*_R_c = cRo^T, c*_t_c = t* - cRo^T cto
            R_dc = transpose(cRo)
            t_dc = [[0.0, 0.0, Z_DES][i] - matvec(R_dc, cto)[i] for i in range(3)]
            v = [-LAMBDA * x for x in matvec(cRo, t_dc)]
            w = [-LAMBDA * x for x in theta_u(R_dc)]
            vel = v + w
        else:
            zhat = [matvec(cRo, [k * X[0], k * X[1], 0.0])[2] + cto[2] for X in OBJ]
            L = [row for (x, y), Z in zip(meas, zhat) for row in interaction(x, y, Z)]
            e = [m - s for m, s in zip([c for p in meas for c in p], s_star)]
            vel = [-LAMBDA * x for x in pinv_apply(L, e)]
        dv = matvec(Rw, [vel[i] * DT for i in range(3)])
        tw = [tw[i] + dv[i] for i in range(3)]
        Rw = orthonormalize(matmul(Rw, expmap([vel[i] * DT for i in range(3, 6)])))
        path += math.sqrt(sum(x * x for x in dv))
        retreat = max(retreat, -tw[2] - depth0)  # backing away beyond the start
    final = project(Rw, tw)
    sse = sum((a - b) ** 2 for p, q in zip(final, desired) for a, b in zip(p[:2], q[:2]))
    t_err = math.sqrt(tw[0] ** 2 + tw[1] ** 2 + (tw[2] + Z_DES) ** 2)
    return {"sse": sse, "path": path, "lost": lost, "steps": steps, "t_err": t_err, "retreat": retreat}


def fmt(vals, f):
    return f"{statistics.mean(vals):{f}}±{statistics.pstdev(vals):{f}}"


def main():
    print(f"Synthetic: lambda={LAMBDA} dt={DT}s cap={STEPS} sigma={SIGMA} FOV=±{FOV} "
          f"seeds={len(SEEDS)} target=0.20 m square Z*={Z_DES} m")
    L0 = interaction(0.2, 0.2, Z_DES)
    print("L(x=0.2,y=0.2,Z=0.5) rows:")
    for row in L0:
        print("  " + " ".join(f"{v:7.3f}" for v in row))
    desired = project([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0.0, 0.0, -Z_DES])
    Ld = [row for x, y, Z in desired for row in interaction(x, y, Z)]
    ev = jacobi_eigs(matmul(transpose(Ld), Ld))
    print(f"4-point stack at s*: eig(L^T L) min={ev[0]:.4f} max={ev[-1]:.2f} cond={ev[-1] / ev[0]:.1f}")
    two = [row for x, y, Z in desired[:2] for row in interaction(x, y, Z)]
    ev2 = jacobi_eigs(matmul(transpose(two), two))
    print(f"2-point stack: rank<6, eig min={abs(ev2[0]):.1e} (null directions={sum(1 for v in ev2 if abs(v) < 1e-9)})")
    print("scenario arm lost/5 feat_SSE path_m t_err_m extra_retreat_m")
    for sc in SCENARIOS:
        for arm in ("PBVS", "IBVS"):
            rs = [run(arm, sc, s) for s in SEEDS]
            print(f"{sc} {arm} {sum(r['lost'] for r in rs)}/5 {fmt([r['sse'] for r in rs], '.2e')} "
                  f"{fmt([r['path'] for r in rs], '.3f')} {fmt([r['t_err'] for r in rs], '.3f')} "
                  f"{fmt([r['retreat'] for r in rs], '.3f')}")
    print("Shared estimate: same noisy points, model scale k, lambda, cap and FOV for both arms.")
    print("No winner is declared; real camera/OpenCV/robot runs: 本页未运行.")


if __name__ == "__main__":
    main()
