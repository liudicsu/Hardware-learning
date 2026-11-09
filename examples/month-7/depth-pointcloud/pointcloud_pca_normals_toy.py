#!/usr/bin/env python3
"""Synthetic PCA normal estimation on a depth-camera height field. Stdlib only.

Model (stated in the lesson prose too): camera at the origin looking along +z; the
surface is a height field z = 0.40 m - A sin(2 pi x / LAM) sin(2 pi y / LAM) on a
41 x 41 grid with 5 mm spacing (x, y jittered by +-1.25 mm); depth noise is
Gaussian along z only (a stand-in for noise along the ray); no outliers, no
missing pixels, one viewpoint. True normal of z = f(x, y): (f_x, f_y, -1)
normalised, which already faces the camera.

Arms (each gives a unit normal at every query point):
  A_global_plane  no per-point normals: one PCA plane fitted to the whole cloud
  B_pca_k20       local PCA: covariance of the k = 20 nearest neighbours (query
                  included), eigenvector of the smallest eigenvalue
  C_pca_k4        the same with k = 4
Every normal is then flipped toward the viewpoint (0, 0, 0): if n . (vp - p) < 0,
n = -n. Raw PCA signs are arbitrary (the eigen-solver returns either sign).

Common random numbers: per (regime, seed) the grid jitter, the depth-noise draw of
every point and the 60 interior query points are drawn once; all arms see the same
noisy cloud and the same queries.
Metrics per seed: mean angle to the true normal after orientation (deg); local
plane residual = RMS distance of the query's 12 nearest noisy points (a fixed
evaluation neighbourhood shared by all arms) to the plane through their centroid
with the arm's normal (mm). The residual still rewards fitting the noise; the
angle metric is blind to run time, to multi-view orientation and to outliers.
No presumed winner. Open3D / PCL on a real sensor: 本页未运行.
"""
from __future__ import annotations

import math
import random

Z0 = 0.40  # m, desk depth
N_GRID = 41
SPACING = 0.005  # m
QUERIES = 60
K_EVAL = 12
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_global_plane", "B_pca_k20", "C_pca_k4")
K_OF = {"B_pca_k20": 20, "C_pca_k4": 4}
# regime, amplitude A (m), wavelength LAM (m), depth-noise sd (m)
REGIMES = (("flat_low_noise", 0.0, 0.10, 0.0003), ("ripple_noisy", 0.008, 0.10, 0.002),
           ("fine_ripple_low_noise", 0.004, 0.04, 0.0001))


def height(a: float, lam: float, x: float, y: float) -> tuple[float, float, float]:
    k = 2 * math.pi / lam
    z = Z0 - a * math.sin(k * x) * math.sin(k * y)
    return z, -a * k * math.cos(k * x) * math.sin(k * y), -a * k * math.sin(k * x) * math.cos(k * y)


def unit(v: tuple[float, float, float]) -> tuple[float, float, float]:
    n = math.sqrt(sum(c * c for c in v))
    return (v[0] / n, v[1] / n, v[2] / n)


def covariance(pts: list[tuple[float, float, float]]) -> tuple[list[list[float]], tuple[float, float, float]]:
    n = len(pts)
    c = tuple(sum(p[i] for p in pts) / n for i in range(3))
    m = [[sum((p[i] - c[i]) * (p[j] - c[j]) for p in pts) / n for j in range(3)] for i in range(3)]
    return m, c


def jacobi_eig(m: list[list[float]]) -> tuple[list[float], list[list[float]]]:
    """Cyclic Jacobi for a symmetric 3x3 matrix: eigenvalues and eigenvectors (columns)."""
    a = [row[:] for row in m]
    v = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _ in range(50):
        off = a[0][1] ** 2 + a[0][2] ** 2 + a[1][2] ** 2
        if off < 1e-30:
            break
        for p, q in ((0, 1), (0, 2), (1, 2)):
            if abs(a[p][q]) < 1e-300:
                continue
            theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
            t = math.copysign(1.0, theta) / (abs(theta) + math.sqrt(theta * theta + 1))
            c = 1 / math.sqrt(t * t + 1)
            s = t * c
            for k in range(3):  # A <- A G
                akp, akq = a[k][p], a[k][q]
                a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
            for k in range(3):  # A <- G^T A
                apk, aqk = a[p][k], a[q][k]
                a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
            for k in range(3):
                vkp, vkq = v[k][p], v[k][q]
                v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    return [a[i][i] for i in range(3)], v


def pca_normal(pts: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    """Eigenvector of the smallest covariance eigenvalue, with whatever sign Jacobi returns."""
    m, _ = covariance(pts)
    vals, vecs = jacobi_eig(m)
    i = min(range(3), key=lambda j: vals[j])
    return unit((vecs[0][i], vecs[1][i], vecs[2][i]))


def orient(n: tuple[float, float, float], p: tuple[float, float, float]) -> tuple[tuple[float, float, float], bool]:
    """Flip n toward the viewpoint at the origin; report whether it was flipped."""
    if -(n[0] * p[0] + n[1] * p[1] + n[2] * p[2]) < 0:
        return (-n[0], -n[1], -n[2]), True
    return n, False


def knn(cloud: list[tuple[float, float, float]], p: tuple[float, float, float], k: int) -> list[tuple[float, float, float]]:
    return sorted(cloud, key=lambda c: (c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 + (c[2] - p[2]) ** 2)[:k]


def shared_scene(regime: str, a: float, lam: float, sd: float, seed: int):
    rng = random.Random(f"{regime}:{seed}")
    half = (N_GRID - 1) / 2
    cloud, truth = [], []
    for i in range(N_GRID):
        for j in range(N_GRID):
            x = (i - half) * SPACING + rng.uniform(-SPACING / 4, SPACING / 4)
            y = (j - half) * SPACING + rng.uniform(-SPACING / 4, SPACING / 4)
            z, fx, fy = height(a, lam, x, y)
            cloud.append((x, y, z + rng.gauss(0.0, sd)))
            truth.append(unit((fx, fy, -1.0)))
    interior = [i * N_GRID + j for i in range(5, N_GRID - 5) for j in range(5, N_GRID - 5)]
    return cloud, truth, rng.sample(interior, QUERIES)


def angle_deg(n: tuple[float, float, float], t: tuple[float, float, float]) -> float:
    return math.degrees(math.acos(max(-1.0, min(1.0, n[0] * t[0] + n[1] * t[1] + n[2] * t[2]))))


def evaluate(regime: str, a: float, lam: float, sd: float, seed: int) -> dict:
    cloud, truth, queries = shared_scene(regime, a, lam, sd, seed)
    g = pca_normal(cloud)
    out = {arm: {"ang": 0.0, "res": 0.0, "flip": 0} for arm in ARMS}
    for qi in queries:
        p = cloud[qi]
        ev = knn(cloud, p, K_EVAL)
        _, c = covariance(ev)
        for arm in ARMS:
            raw = g if arm == "A_global_plane" else pca_normal(knn(cloud, p, K_OF[arm]))
            n, flipped = orient(raw, p)
            r2 = sum(((e[0] - c[0]) * n[0] + (e[1] - c[1]) * n[1] + (e[2] - c[2]) * n[2]) ** 2 for e in ev) / len(ev)
            out[arm]["ang"] += angle_deg(n, truth[qi]) / QUERIES
            out[arm]["res"] += math.sqrt(r2) * 1e3 / QUERIES
            out[arm]["flip"] += flipped
    return out


def ms(xs: list[float]) -> tuple[float, float]:
    m = sum(xs) / len(xs)
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def verdict(xa: list[float], xb: list[float]) -> str:
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "tie: identical on every seed"
    m, s = ms(diffs)
    if abs(m) <= s:
        return "near-tie / small gap, within seed noise"
    if abs(m) < 0.2 * min(ms(xa)[0], ms(xb)[0]):
        return "small but consistent gap, not a tie"
    return "clear gap, not a tie"


def main() -> None:
    print(f"height field z=0.40-A*sin(2pi x/LAM)*sin(2pi y/LAM); grid {N_GRID}x{N_GRID} spacing 5 mm; "
          f"queries={QUERIES} k_eval={K_EVAL} seeds={len(SEEDS)}")
    print("sign check: PCA of an exact z=0.40 plane ->", ", ".join(
        f"{v:.6f}" for v in pca_normal([(0.01 * i, 0.01 * j, Z0) for i in range(5) for j in range(5)])),
          "(either sign is a valid eigenvector; orient toward the viewpoint)")
    print("regime arm angle_deg residual_mm raw_sign_flipped/queries  (mean+-sd over seeds)")
    for regime, a, lam, sd in REGIMES:
        per = {arm: {"ang": [], "res": [], "flip": []} for arm in ARMS}
        for seed in SEEDS:
            out = evaluate(regime, a, lam, sd, seed)
            for arm in ARMS:
                for k in ("ang", "res", "flip"):
                    per[arm][k].append(out[arm][k])
        for arm in ARMS:
            (am, asd), (rm, rsd) = ms(per[arm]["ang"]), ms(per[arm]["res"])
            print(f"{regime} {arm} {am:.4f}+-{asd:.4f} {rm:.4f}+-{rsd:.4f} {sum(per[arm]['flip'])}/{QUERIES * len(SEEDS)}")
        for x, y in (("B_pca_k20", "A_global_plane"), ("B_pca_k20", "C_pca_k4")):
            for k, name in (("ang", "angle_deg"), ("res", "residual_mm")):
                d = ms([u - v for u, v in zip(per[x][k], per[y][k])])
                print(f"{regime} paired {x[0]}-{y[0]} {name} {d[0]:.4f}+-{d[1]:.4f}: {verdict(per[x][k], per[y][k])}")
    print("flat_low_noise: one global plane is already the right normal everywhere; local PCA only adds noise")
    print("ripple_noisy: k=4 is noise-dominated, the global plane ignores curvature; k=20 averages the noise")
    print("fine_ripple_low_noise: k=20 spans a large part of a 40 mm ripple and smooths the curvature; k=4 resolves it")
    print("No winner declared: k trades noise averaging against curvature smoothing; the scale is a task choice")
    print("Open3D estimate_normals / PCL NormalEstimation on a real sensor: 本页未运行; tutorial text 以原文为准")


if __name__ == "__main__":
    main()
