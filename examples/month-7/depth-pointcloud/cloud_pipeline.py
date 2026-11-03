#!/usr/bin/env python3
"""cloud_pipeline.py: synthetic RGB-D desk with 3 boxes → back-project → voxel → RANSAC plane → DBSCAN.

Pure standard library (no Open3D / NumPy). Fixed geometry so the centroid table is reproducible.
The lesson maps each step onto the matching Open3D call (voxel_down_sample, segment_plane,
cluster_dbscan, RGBDImage.create_from_color_and_depth).
usage: python3 cloud_pipeline.py
"""
from __future__ import annotations

import math
import random

# Pinhole camera (matches a typical 640x480 depth camera intrinsics, scaled down for speed)
W, H = 160, 120
FX = FY = 120.0
CX, CY = (W - 1) / 2.0, (H - 1) / 2.0
# Desk plane z = 0.40 m in camera frame (camera looks along +z, y down, x right — OpenCV-style)
DESK_Z = 0.40
# Three axis-aligned boxes on the desk: (cx, cy, z_top, sx, sy, sz) in metres
BOXES = (
    (0.00, 0.02, 0.40 - 0.04, 0.06, 0.05, 0.04),   # centre box, 4 cm tall
    (-0.12, -0.05, 0.40 - 0.03, 0.05, 0.04, 0.03), # left
    (0.14, 0.06, 0.40 - 0.05, 0.04, 0.06, 0.05),   # right, taller
)
VOXEL = 0.01          # 1 cm voxels
RANSAC_THRESH = 0.008 # 8 mm
RANSAC_ITERS = 80
DBSCAN_EPS = 0.025
DBSCAN_MIN = 8
SEED = 0


def depth_at(u: int, v: int) -> float:
    """Ray through pixel (u,v): X = (u-cx)/fx * Z, Y = (v-cy)/fy * Z. Closest hit wins."""
    # desk hit
    z_desk = DESK_Z
    x_desk = (u - CX) / FX * z_desk
    y_desk = (v - CY) / FY * z_desk
    best = z_desk
    # boxes: for each, if ray hits the top face (constant z = z_top) within xy footprint
    for cx, cy, z_top, sx, sy, sz in BOXES:
        # hit top face at z_top
        x = (u - CX) / FX * z_top
        y = (v - CY) / FY * z_top
        if abs(x - cx) <= sx / 2 and abs(y - cy) <= sy / 2:
            if z_top < best:
                best = z_top
    return best


def backproject(depth: list[list[float]]) -> list[tuple[float, float, float]]:
    pts = []
    for v in range(H):
        for u in range(W):
            z = depth[v][u]
            if z <= 0:
                continue
            x = (u - CX) / FX * z
            y = (v - CY) / FY * z
            pts.append((x, y, z))
    return pts


def voxel_down(pts: list[tuple[float, float, float]], voxel: float) -> list[tuple[float, float, float]]:
    buckets: dict[tuple[int, int, int], list[tuple[float, float, float]]] = {}
    inv = 1.0 / voxel
    for p in pts:
        key = (math.floor(p[0] * inv), math.floor(p[1] * inv), math.floor(p[2] * inv))
        buckets.setdefault(key, []).append(p)
    out = []
    for group in buckets.values():
        n = len(group)
        out.append((sum(p[0] for p in group) / n, sum(p[1] for p in group) / n, sum(p[2] for p in group) / n))
    return out


def fit_plane(p1, p2, p3):
    # normal from cross product
    ax, ay, az = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
    bx, by, bz = p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]
    nx = ay * bz - az * by
    ny = az * bx - ax * bz
    nz = ax * by - ay * bx
    norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if norm < 1e-12:
        return None
    nx, ny, nz = nx / norm, ny / norm, nz / norm
    d = -(nx * p1[0] + ny * p1[1] + nz * p1[2])
    return nx, ny, nz, d


def segment_plane(pts, thresh=RANSAC_THRESH, iters=RANSAC_ITERS, rng=None):
    rng = rng or random.Random(SEED)
    best_inliers = []
    best_model = None
    n = len(pts)
    if n < 3:
        return best_model, best_inliers
    for _ in range(iters):
        i, j, k = rng.sample(range(n), 3)
        model = fit_plane(pts[i], pts[j], pts[k])
        if model is None:
            continue
        nx, ny, nz, d = model
        inliers = [p for p in pts if abs(nx * p[0] + ny * p[1] + nz * p[2] + d) < thresh]
        if len(inliers) > len(best_inliers):
            best_inliers = inliers
            best_model = model
    return best_model, best_inliers


def dbscan(pts, eps=DBSCAN_EPS, min_pts=DBSCAN_MIN):
    n = len(pts)
    labels = [-1] * n  # -1 unvisited, -2 noise, >=0 cluster
    cluster_id = 0

    def neighbours(i):
        return [j for j in range(n) if (pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2 + (pts[i][2] - pts[j][2]) ** 2 <= eps * eps]

    for i in range(n):
        if labels[i] != -1:
            continue
        nbrs = neighbours(i)
        if len(nbrs) < min_pts:
            labels[i] = -2
            continue
        labels[i] = cluster_id
        seed = [j for j in nbrs if j != i]
        k = 0
        while k < len(seed):
            j = seed[k]
            if labels[j] == -2:
                labels[j] = cluster_id
            if labels[j] == -1:
                labels[j] = cluster_id
                jnbrs = neighbours(j)
                if len(jnbrs) >= min_pts:
                    for q in jnbrs:
                        if q not in seed:
                            seed.append(q)
            k += 1
        cluster_id += 1
    return labels, cluster_id


def centroid(pts):
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)


def main() -> None:
    depth = [[depth_at(u, v) for u in range(W)] for v in range(H)]
    raw = backproject(depth)
    down = voxel_down(raw, VOXEL)
    model, inliers = segment_plane(down, rng=random.Random(SEED))
    inlier_set = set(id(p) for p in inliers)
    rest = [p for p in down if id(p) not in inlier_set]
    # also drop by distance in case of float identity issues
    if model is not None:
        nx, ny, nz, d = model
        rest = [p for p in down if abs(nx * p[0] + ny * p[1] + nz * p[2] + d) >= RANSAC_THRESH]
    labels, ncl = dbscan(rest)
    print(f"image {W}x{H}  fx=fy={FX:.0f}  desk_z={DESK_Z}")
    print(f"raw_points {len(raw)}  after_voxel_{VOXEL*100:.0f}cm {len(down)}")
    print(f"plane_inliers {len(inliers)}  remaining {len(rest)}  clusters {ncl}")
    print("cluster  n_points  centroid_x  centroid_y  centroid_z")
    clusters = []
    for cid in range(ncl):
        members = [rest[i] for i, lab in enumerate(labels) if lab == cid]
        if not members:
            continue
        c = centroid(members)
        clusters.append((len(members), c))
    # sort by x so the table order is stable
    clusters.sort(key=lambda t: t[1][0])
    for i, (n, c) in enumerate(clusters):
        print(f"{i:7d}  {n:8d}  {c[0]:10.4f}  {c[1]:10.4f}  {c[2]:10.4f}")
    # ground-truth box centres (top-face centres) for the lesson
    print("true_box_centres (x, y, z_top):")
    for cx, cy, z_top, sx, sy, sz in sorted(BOXES, key=lambda b: b[0]):
        print(f"  ({cx:+.2f}, {cy:+.2f}, {z_top:.2f})")


if __name__ == "__main__":
    main()
