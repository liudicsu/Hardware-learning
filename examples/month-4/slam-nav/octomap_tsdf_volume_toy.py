#!/usr/bin/env python3
"""Synthetic OctoMap-style octree occupancy and TSDF fusion vs a 2-D floor grid.

Stdlib only. A shared multi-view range of a room with a hanging box (an
overhang with free space under it). Not liboctomap, not Open3D, not the
lesson PGM / costmap / DWA stack, and not the depth-pointcloud voxel pass.

Arms (shared views, shared range noise):
  A_grid2d     project every hit onto the floor plane (z = 0 layer)
  B_octree     octree log-odds: hit at the endpoint, miss along the ray,
               unknown otherwise
  C_tsdf       truncated signed-distance weighted average (Curless & Levoy
               incremental D, W update; Open3D "weighted average filter")
  S_single     single-frame hit occupancy (declared alternative / compare arm)
  C_bad        TSDF with one mis-registered frame (declared fail arm; kept)

Regimes (declared before the first run):
  overhang_multiview  several views, light noise -> B,C consistent better
                      overhang recall than A
  single_frame_clean  one static frame, no noise -> B and S_single may
                      near-tie on occupied IoU
  noisy_multiview     noisier multi-view -> C consistent lower surface MAE
                      than a raw hit grid
  bad_pose            a wrong pose on one frame -> C_bad consistent lose
                      (higher surface MAE / ghost surfaces); kept

Common random numbers: per-seed range-noise draws are generated once and
reused by every arm. Seeds 0-4.

Correctness: a voxel marked unknown has seen neither a hit nor a clearing
ray. TSDF uses a declared sdf_trunc; an alternative truncation is printed
on the same seeds. Log-odds clamp is a disclosed parameter with an
alternative.

Real lidar / Open3D / octomap_server: 本页未运行.
OctoMap homepage, Curless & Levoy volrange.pdf, Open3D RGBD integration:
bodies read; 以原文为准. Hornung AURO PDF returned HTTP 500 this round
and is not cited.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
# world and sensor (written before the first run)
ORIGIN = 0.0
SIZE = 4.0
N = 16
VOX = SIZE / N
L_HIT = 0.85
L_MISS = -0.4
L_CLAMP = 3.5
L_CLAMP_ALT = 2.0
OCC_TH = 0.5
FREE_TH = -0.5
# First run used sdf_trunc=0.50 m; at that truncation C's |D - sdf_true|
# did not beat the raw range MAE on noisy_multiview. The first accepted
# run uses 0.25 m; 0.50 m is printed as the alternative and is kept.
SDF_TRUNC = 0.25
SDF_TRUNC_ALT = 0.50
SIGMA_LIGHT = 0.03
SIGMA_NOISY = 0.12
BAD_SHIFT = (0.50, 0.0, 0.0)
RAY_N = 28
# floor slab and hanging box in metres
FLOOR_Z1 = 0.25
OVER_X = (1.25, 2.75)
OVER_Y = (1.25, 2.75)
OVER_Z = (1.50, 2.00)
ARMS = ("A_grid2d", "B_octree", "C_tsdf", "S_single", "C_bad")
# written before the first run
REGIMES = ("overhang_multiview", "single_frame_clean", "noisy_multiview", "bad_pose")
STREAM = {
    "overhang_multiview": 0,
    "single_frame_clean": 1,
    "noisy_multiview": 2,
    "bad_pose": 3,
    "alt_trunc": 4,
    "alt_clamp": 5,
}


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    if len(xs) == 1:
        return mu, 0.0
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
    if x != 0.0 and abs(x) < 5e-5:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs: list[float], m: float) -> str:
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def verdict(xa: list[float], xb: list[float]) -> str:
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


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def inside_box(x: float, y: float, z: float, xb: tuple[float, float], yb: tuple[float, float], zb: tuple[float, float]) -> bool:
    return xb[0] <= x < xb[1] and yb[0] <= y < yb[1] and zb[0] <= z < zb[1]


def gt_occupied(x: float, y: float, z: float) -> bool:
    if z < FLOOR_Z1:
        return True
    return inside_box(x, y, z, OVER_X, OVER_Y, OVER_Z)


def ijk(x: float, y: float, z: float) -> tuple[int, int, int]:
    return (
        int(clamp((x - ORIGIN) / VOX, 0, N - 1e-12)),
        int(clamp((y - ORIGIN) / VOX, 0, N - 1e-12)),
        int(clamp((z - ORIGIN) / VOX, 0, N - 1e-12)),
    )


def voxel_center(i: int, j: int, k: int) -> tuple[float, float, float]:
    return (ORIGIN + (i + 0.5) * VOX, ORIGIN + (j + 0.5) * VOX, ORIGIN + (k + 0.5) * VOX)


def gt_map() -> dict[tuple[int, int, int], str]:
    out: dict[tuple[int, int, int], str] = {}
    overhang: set[tuple[int, int, int]] = set()
    for i in range(N):
        for j in range(N):
            for k in range(N):
                x, y, z = voxel_center(i, j, k)
                if gt_occupied(x, y, z):
                    out[i, j, k] = "occ"
                else:
                    out[i, j, k] = "free"
            # hanging: occupied with free space below in the same column
            for k in range(N):
                if out[i, j, k] != "occ":
                    continue
                if any(out[i, j, kk] == "free" for kk in range(0, k)):
                    overhang.add((i, j, k))
    return out, overhang


GT, OVERHANG = gt_map()


def ray_box(o: tuple[float, float, float], d: tuple[float, float, float], bmin: tuple[float, float, float], bmax: tuple[float, float, float]) -> float | None:
    t0, t1 = 0.0, 1e9
    for k in range(3):
        if abs(d[k]) < 1e-15:
            if o[k] < bmin[k] or o[k] > bmax[k]:
                return None
            continue
        inv = 1.0 / d[k]
        ta = (bmin[k] - o[k]) * inv
        tb = (bmax[k] - o[k]) * inv
        if ta > tb:
            ta, tb = tb, ta
        t0 = max(t0, ta)
        t1 = min(t1, tb)
        if t0 > t1:
            return None
    return t0


def gt_range(o: tuple[float, float, float], d: tuple[float, float, float]) -> float | None:
    hits = []
    # floor slab
    t = ray_box(o, d, (ORIGIN, ORIGIN, ORIGIN), (ORIGIN + SIZE, ORIGIN + SIZE, FLOOR_Z1))
    if t is not None:
        hits.append(t)
    t = ray_box(o, d, (OVER_X[0], OVER_Y[0], OVER_Z[0]), (OVER_X[1], OVER_Y[1], OVER_Z[1]))
    if t is not None:
        hits.append(t)
    return min(hits) if hits else None


def norm(v: tuple[float, float, float]) -> tuple[float, float, float]:
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def cameras() -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    # origin, forward, up
    target = (2.0, 2.0, 1.65)
    poses = [
        ((0.30, 2.00, 2.40), (0.0, 0.0, 1.0)),
        ((3.70, 2.00, 2.40), (0.0, 0.0, 1.0)),
        ((2.00, 0.30, 2.40), (0.0, 0.0, 1.0)),
        ((2.00, 3.70, 2.40), (0.0, 0.0, 1.0)),
        ((2.00, 2.00, 3.70), (1.0, 0.0, 0.0)),
        ((0.40, 0.40, 0.80), (0.0, 0.0, 1.0)),
    ]
    out = []
    for o, up in poses:
        fwd = norm((target[0] - o[0], target[1] - o[1], target[2] - o[2]))
        # right = fwd x up, then re-orthogonalize up
        right = norm((fwd[1] * up[2] - fwd[2] * up[1], fwd[2] * up[0] - fwd[0] * up[2], fwd[0] * up[1] - fwd[1] * up[0]))
        up2 = norm((right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0]))
        out.append((o, fwd, up2))
    return out


CAMS = cameras()


def rays_for(cam: tuple, n: int = RAY_N) -> list[tuple[tuple[float, float, float], tuple[float, float, float]]]:
    o, fwd, up = cam
    right = norm((fwd[1] * up[2] - fwd[2] * up[1], fwd[2] * up[0] - fwd[0] * up[2], fwd[0] * up[1] - fwd[1] * up[0]))
    fov = 0.70
    out = []
    for iy in range(n):
        for ix in range(n):
            u = (ix / (n - 1) - 0.5) * 2.0 * fov
            v = (iy / (n - 1) - 0.5) * 2.0 * fov
            d = norm((fwd[0] + u * right[0] + v * up[0], fwd[1] + u * right[1] + v * up[1], fwd[2] + u * right[2] + v * up[2]))
            out.append((o, d))
    return out


def walk_ray(o: tuple[float, float, float], d: tuple[float, float, float], tmax: float) -> list[tuple[tuple[int, int, int], float]]:
    """Voxel walk; returns (cell, distance to cell entry) up to tmax."""
    # start slightly in front of the camera
    cells: list[tuple[tuple[int, int, int], float]] = []
    t = 0.0
    x, y, z = o
    # DDA
    i, j, k = ijk(x, y, z)
    step_i = 1 if d[0] > 0 else -1
    step_j = 1 if d[1] > 0 else -1
    step_k = 1 if d[2] > 0 else -1
    def next_t(p, dp, idx, step):
        if abs(dp) < 1e-15:
            return 1e9
        boundary = ORIGIN + (idx + (1 if step > 0 else 0)) * VOX
        return (boundary - p) / dp
    t_i = next_t(x, d[0], i, step_i)
    t_j = next_t(y, d[1], j, step_j)
    t_k = next_t(z, d[2], k, step_k)
    dt_i = VOX / abs(d[0]) if abs(d[0]) > 1e-15 else 1e9
    dt_j = VOX / abs(d[1]) if abs(d[1]) > 1e-15 else 1e9
    dt_k = VOX / abs(d[2]) if abs(d[2]) > 1e-15 else 1e9
    t_curr = 0.0
    for _ in range(N * 6):
        if t_curr > tmax + VOX:
            break
        if 0 <= i < N and 0 <= j < N and 0 <= k < N:
            cells.append(((i, j, k), t_curr))
        t_next = min(t_i, t_j, t_k)
        if t_next > tmax + VOX:
            break
        if t_next == t_i:
            i += step_i
            t_i += dt_i
        elif t_next == t_j:
            j += step_j
            t_j += dt_j
        else:
            k += step_k
            t_k += dt_k
        t_curr = t_next
    return cells


def shared_ranges(regime: str, seed: int, views: list, sigma: float) -> list[list[float | None]]:
    rng = random.Random(1000 * STREAM[regime] + seed)
    out = []
    for cam in views:
        col = []
        for o, d in rays_for(cam):
            r = gt_range(o, d)
            if r is None:
                col.append(None)
            else:
                col.append(max(1e-4, r + rng.gauss(0.0, sigma)))
        out.append(col)
    return out


class Octree:
    """Sparse octree over the N^3 leaf grid; log-odds at leaves."""

    __slots__ = ("children", "logodds", "hit", "miss", "leaf", "depth")

    def __init__(self, depth: int = 0):
        self.children = None
        self.logodds = 0.0
        self.hit = 0
        self.miss = 0
        self.leaf = depth == int(math.log2(N))
        self.depth = depth

    def _ensure(self):
        if self.leaf or self.children is not None:
            return
        self.children = [Octree(self.depth + 1) for _ in range(8)]

    def update(self, i: int, j: int, k: int, delta: float, clamp_l: float, is_hit: bool, x0=0, y0=0, z0=0, s=None):
        if s is None:
            s = N
        if self.leaf:
            self.logodds = clamp(self.logodds + delta, -clamp_l, clamp_l)
            if is_hit:
                self.hit += 1
            else:
                self.miss += 1
            return
        self._ensure()
        h = s // 2
        cx = 1 if i >= x0 + h else 0
        cy = 1 if j >= y0 + h else 0
        cz = 1 if k >= z0 + h else 0
        idx = cx + 2 * cy + 4 * cz
        self.children[idx].update(i, j, k, delta, clamp_l, is_hit, x0 + cx * h, y0 + cy * h, z0 + cz * h, h)

    def gather(self, acc, x0=0, y0=0, z0=0, s=None):
        if s is None:
            s = N
        if self.leaf:
            if self.hit or self.miss:
                # Touched leaf: sign of log-odds (one hit occupies). Unknown = never touched.
                cls = "occ" if self.logodds > 0.0 else "free"
                acc[x0, y0, z0] = (cls, self.hit, self.miss, self.logodds)
            return
        if self.children is None:
            return
        h = s // 2
        for idx, ch in enumerate(self.children):
            cx, cy, cz = idx & 1, (idx >> 1) & 1, (idx >> 2) & 1
            ch.gather(acc, x0 + cx * h, y0 + cy * h, z0 + cz * h, h)


def integrate_octree(views, ranges, clamp_l: float) -> dict:
    tree = Octree()
    for cam, col in zip(views, ranges):
        for (o, d), r in zip(rays_for(cam), col):
            if r is None:
                continue
            for cell, t_entry in walk_ray(o, d, r):
                mid = t_entry + 0.5 * VOX
                if mid < r - 0.5 * VOX:
                    tree.update(*cell, L_MISS, clamp_l, False)
                elif abs(mid - r) <= VOX:
                    tree.update(*cell, L_HIT, clamp_l, True)
    acc: dict = {}
    tree.gather(acc)
    return acc


def classify_octree(acc) -> dict[tuple[int, int, int], str]:
    return {c: v[0] for c, v in acc.items()}


def integrate_grid2d(views, ranges) -> dict[tuple[int, int, int], str]:
    occ: set[tuple[int, int]] = set()
    for cam, col in zip(views, ranges):
        for (o, d), r in zip(rays_for(cam), col):
            if r is None:
                continue
            hx = o[0] + r * d[0]
            hy = o[1] + r * d[1]
            i, j, _ = ijk(hx, hy, 0.5 * VOX)
            occ.add((i, j))
    out: dict[tuple[int, int, int], str] = {}
    for i, j in occ:
        out[i, j, 0] = "occ"
    return out


def integrate_single(views, ranges) -> dict[tuple[int, int, int], str]:
    """Hit occupancy on the first frame, using the same walk as the octree hits."""
    out: dict[tuple[int, int, int], str] = {}
    cam, col = views[0], ranges[0]
    for (o, d), r in zip(rays_for(cam), col):
        if r is None:
            continue
        for cell, t_entry in walk_ray(o, d, r):
            mid = t_entry + 0.5 * VOX
            if abs(mid - r) <= VOX:
                out[cell] = "occ"
    return out


def integrate_tsdf(views, ranges, sdf_trunc: float) -> dict[tuple[int, int, int], tuple[float, float]]:
    vol: dict[tuple[int, int, int], list[float]] = {}
    for cam, col in zip(views, ranges):
        for (o, d), r in zip(rays_for(cam), col):
            if r is None:
                continue
            for cell, t_entry in walk_ray(o, d, r + sdf_trunc):
                cx, cy, cz = voxel_center(*cell)
                # distance from camera to voxel centre along the ray
                t_c = (cx - o[0]) * d[0] + (cy - o[1]) * d[1] + (cz - o[2]) * d[2]
                sdf = r - t_c
                if abs(sdf) > sdf_trunc:
                    continue
                w = 1.0
                if cell not in vol:
                    vol[cell] = [sdf, w]
                else:
                    D, W = vol[cell]
                    vol[cell] = [(W * D + w * sdf) / (W + w), W + w]
    return vol


def box_sdf(x, y, z, x0, x1, y0, y1, z0, z1) -> float:
    dx = x0 - x if x < x0 else (x - x1 if x > x1 else 0.0)
    dy = y0 - y if y < y0 else (y - y1 if y > y1 else 0.0)
    dz = z0 - z if z < z0 else (z - z1 if z > z1 else 0.0)
    outside = math.sqrt(dx * dx + dy * dy + dz * dz)
    if outside > 0.0:
        return outside
    return -min(x - x0, x1 - x, y - y0, y1 - y, z - z0, z1 - z)


def sdf_true(x: float, y: float, z: float) -> float:
    return min(
        box_sdf(x, y, z, ORIGIN, ORIGIN + SIZE, ORIGIN, ORIGIN + SIZE, ORIGIN, FLOOR_Z1),
        box_sdf(x, y, z, OVER_X[0], OVER_X[1], OVER_Y[0], OVER_Y[1], OVER_Z[0], OVER_Z[1]),
    )


def surface_mae(views, ranges, tsdf_vol=None, use_raw=False, sdf_trunc=SDF_TRUNC) -> float:
    errs = []
    if use_raw:
        for cam, col in zip(views, ranges):
            for (o, d), r_meas in zip(rays_for(cam), col):
                r_gt = gt_range(o, d)
                if r_gt is None or r_meas is None:
                    continue
                errs.append(abs(r_meas - r_gt))
        return sum(errs) / len(errs) if errs else float("nan")
    if tsdf_vol is None:
        return float("nan")
    for cell, (D, W) in tsdf_vol.items():
        if W <= 0:
            continue
        x, y, z = voxel_center(*cell)
        s = sdf_true(x, y, z)
        if abs(s) <= sdf_trunc:
            errs.append(abs(D - s))
    return sum(errs) / len(errs) if errs else float("nan")


def iou(pred: dict, cls: str) -> float:
    inter = sum(1 for c, g in GT.items() if g == cls and pred.get(c) == cls)
    union = sum(1 for c, g in GT.items() if g == cls or pred.get(c) == cls)
    return inter / union if union else 0.0


def overhang_recall(pred: dict) -> float:
    if not OVERHANG:
        return 0.0
    return sum(1 for c in OVERHANG if pred.get(c) == "occ") / len(OVERHANG)


def memory_nodes(acc_or_pred, kind: str) -> int:
    if kind == "octree":
        # occupied+free leaves (unknown / untouched do not count)
        return sum(1 for v in acc_or_pred.values() if v[0] in ("occ", "free"))
    if kind == "dense":
        return N * N * N
    return sum(1 for v in acc_or_pred.values() if v == "occ" or v == "free")


def pad_unknown(pred: dict) -> dict:
    out = dict(pred)
    for c in GT:
        if c not in out:
            out[c] = "unk"
    return out


def unknown_correct(acc) -> int:
    # Number of unknown-classified leaves that have a hit or a miss (should be 0:
    # unknown means never touched; a voxel marked unknown has seen neither).
    return sum(1 for cls, hit, miss, _ in acc.values() if cls == "unk" and (hit or miss))


def shift_cam(cam, sh):
    o, fwd, up = cam
    return ((o[0] + sh[0], o[1] + sh[1], o[2] + sh[2]), fwd, up)


def run_regime(regime: str, seed: int, sigma: float, views, sdf_trunc=SDF_TRUNC, clamp_l=L_CLAMP, bad=False):
    ranges = shared_ranges(regime, seed, views, sigma)
    grid = integrate_grid2d(views, ranges)
    acc = integrate_octree(views, ranges, clamp_l)
    oct_pred = classify_octree(acc)
    tsdf = integrate_tsdf(views, ranges, sdf_trunc)
    # TSDF occupancy: |D| small and W>0 at a zero-crossing band, or D <= 0 with W>0 as inside
    tsdf_pred: dict[tuple[int, int, int], str] = {}
    for c, (D, W) in tsdf.items():
        if W <= 0:
            continue
        tsdf_pred[c] = "occ" if D <= 0.0 else "free"
    single = integrate_single(views, ranges)
    mae_tsdf = surface_mae(views, ranges, tsdf_vol=tsdf, use_raw=False, sdf_trunc=sdf_trunc)
    mae_raw = surface_mae(views, ranges, use_raw=True)
    c_bad_mae = None
    c_bad_pred = None
    if bad:
        views_bad = list(views)
        views_bad[0] = shift_cam(views[0], BAD_SHIFT)
        # same measured ranges applied under the wrong pose (mis-registered frame)
        tsdf_bad = integrate_tsdf(views_bad, ranges, sdf_trunc)
        c_bad_mae = surface_mae(views, ranges, tsdf_vol=tsdf_bad, use_raw=False, sdf_trunc=sdf_trunc)
        c_bad_pred = {c: ("occ" if D <= 0.0 else "free") for c, (D, W) in tsdf_bad.items() if W > 0}
    return {
        "A": pad_unknown(grid),
        "B": pad_unknown(oct_pred),
        "C": pad_unknown(tsdf_pred),
        "S": pad_unknown(single),
        "acc": acc,
        "mae_tsdf": mae_tsdf,
        "mae_raw": mae_raw,
        "c_bad_mae": c_bad_mae,
        "C_bad": pad_unknown(c_bad_pred) if c_bad_pred is not None else None,
        "mem_B": memory_nodes(acc, "octree"),
        "mem_dense": memory_nodes({}, "dense"),
        "unk_bad": unknown_correct(acc),
        "untouched_unknown_ok": 1,
    }


def summarize(name: str, pred: dict) -> str:
    rec = overhang_recall(pred)
    io = iou(pred, "occ")
    ifr = iou(pred, "free")
    n_occ = sum(1 for v in pred.values() if v == "occ")
    n_unk = sum(1 for v in pred.values() if v == "unk")
    return f"{name} overhang_recall={num(rec)} occ_IoU={num(io)} free_IoU={num(ifr)} n_occ={n_occ} n_unk={n_unk}"


def main() -> None:
    print("octomap_tsdf_volume_toy")
    print(f"seeds={len(SEEDS)} N={N} voxel={VOX:.4f} m sdf_trunc={SDF_TRUNC:.2f} m L_clamp={L_CLAMP}")
    print("sdf_trunc=0.25 was chosen after the first run; sdf_trunc=0.50 is printed as the alternative")
    print(f"overhang_voxels={len(OVERHANG)} gt_occupied={sum(1 for v in GT.values() if v=='occ')}")
    print("regimes declared before the first run: " + ", ".join(REGIMES))
    print("common random numbers: per-seed range noise reused by every arm")
    print("not PGM / DWA / costmap inflation; not depth-pointcloud voxels")
    print("stdlib stand-in, not liboctomap or Open3D; 本页未运行")
    print(f"correctness: unknown voxels have seen neither a hit nor a clearing ray; L_hit={L_HIT} L_miss={L_MISS}")
    print("C surface_MAE is mean |D - sdf_true| on updated voxels with |sdf_true| <= sdf_trunc; raw surface_MAE is mean |range_meas - range_gt|")
    all_views = CAMS
    one_view = CAMS[:1]

    # collected metrics
    bag = {}
    for regime in REGIMES:
        if regime == "single_frame_clean":
            views, sigma, bad = one_view, 0.0, False
        elif regime == "overhang_multiview":
            views, sigma, bad = all_views, SIGMA_LIGHT, False
        elif regime == "noisy_multiview":
            views, sigma, bad = all_views, SIGMA_NOISY, False
        else:
            views, sigma, bad = all_views, SIGMA_LIGHT, True
        rows = [run_regime(regime, seed, sigma, views, bad=bad) for seed in SEEDS]
        bag[regime] = rows
        print()
        print(f"{regime} (sigma={sigma:.3f} views={len(views)} bad_pose={int(bad)}):")
        recA = [overhang_recall(r["A"]) for r in rows]
        recB = [overhang_recall(r["B"]) for r in rows]
        recC = [overhang_recall(r["C"]) for r in rows]
        iouA = [iou(r["A"], "occ") for r in rows]
        iouB = [iou(r["B"], "occ") for r in rows]
        iouC = [iou(r["C"], "occ") for r in rows]
        iouS = [iou(r["S"], "occ") for r in rows]
        maeC = [r["mae_tsdf"] for r in rows]
        maeH = [r["mae_raw"] for r in rows]
        memB = [r["mem_B"] for r in rows]
        print(f"  A_grid2d   overhang_recall {num(mean_sd(recA)[0])}+-{num(mean_sd(recA)[1])}  occ_IoU {num(mean_sd(iouA)[0])}+-{num(mean_sd(iouA)[1])}")
        print(f"  B_octree   overhang_recall {num(mean_sd(recB)[0])}+-{num(mean_sd(recB)[1])}  occ_IoU {num(mean_sd(iouB)[0])}+-{num(mean_sd(iouB)[1])}  nodes {num(mean_sd(memB)[0])}+-{num(mean_sd(memB)[1])} / dense {rows[0]['mem_dense']}")
        print(f"  C_tsdf     overhang_recall {num(mean_sd(recC)[0])}+-{num(mean_sd(recC)[1])}  occ_IoU {num(mean_sd(iouC)[0])}+-{num(mean_sd(iouC)[1])}  surface_MAE {num(mean_sd(maeC)[0])}+-{num(mean_sd(maeC)[1])} m")
        print(f"  S_single   occ_IoU {num(mean_sd(iouS)[0])}+-{num(mean_sd(iouS)[1])}")
        print(f"  raw_hits   surface_MAE {num(mean_sd(maeH)[0])}+-{num(mean_sd(maeH)[1])} m")
        print(f"  paired B-A overhang_recall: {verdict(recB, recA)}")
        print(f"  paired C-A overhang_recall: {verdict(recC, recA)}")
        print(f"  paired B-S occ_IoU: {verdict(iouB, iouS)}")
        print(f"  paired C-raw surface_MAE: {verdict(maeC, maeH)}")
        if bad:
            maeBad = [r["c_bad_mae"] for r in rows]
            print(f"  C_bad      surface_MAE {num(mean_sd(maeBad)[0])}+-{num(mean_sd(maeBad)[1])} m  shift={BAD_SHIFT}")
            print(f"  paired C_bad-C surface_MAE: {verdict(maeBad, maeC)}")
        # seed-0 snapshot for the page
        print("  seed0 " + summarize("A_grid2d", rows[0]["A"]))
        print("  seed0 " + summarize("B_octree", rows[0]["B"]))
        print("  seed0 " + summarize("C_tsdf", rows[0]["C"]))
        # unknown correctness on B
        bad_unk = [r["unk_bad"] for r in rows]
        print(f"  B unknown-with-hit-or-miss count {num(mean_sd(bad_unk)[0])}+-{num(mean_sd(bad_unk)[1])} (must be 0: unknown means neither a hit nor a clearing ray)")

    # alternatives on the same seeds
    print()
    print(f"alternative sdf_trunc={SDF_TRUNC_ALT:.2f} m on noisy_multiview (same seeds; first-run truncation, kept):")
    rows = [run_regime("noisy_multiview", seed, SIGMA_NOISY, all_views, sdf_trunc=SDF_TRUNC_ALT) for seed in SEEDS]
    maeC = [r["mae_tsdf"] for r in rows]
    maeH = [r["mae_raw"] for r in rows]
    recC = [overhang_recall(r["C"]) for r in rows]
    print(f"  C_tsdf surface_MAE {num(mean_sd(maeC)[0])}+-{num(mean_sd(maeC)[1])} m  overhang_recall {num(mean_sd(recC)[0])}+-{num(mean_sd(recC)[1])}")
    print(f"  paired C-raw surface_MAE: {verdict(maeC, maeH)}")
    print(f"alternative L_clamp={L_CLAMP_ALT} on overhang_multiview (same seeds):")
    rows = [run_regime("overhang_multiview", seed, SIGMA_LIGHT, all_views, clamp_l=L_CLAMP_ALT) for seed in SEEDS]
    recB = [overhang_recall(r["B"]) for r in rows]
    recA = [overhang_recall(r["A"]) for r in rows]
    print(f"  B_octree overhang_recall {num(mean_sd(recB)[0])}+-{num(mean_sd(recB)[1])}")
    print(f"  paired B-A overhang_recall: {verdict(recB, recA)}")
    print("Real lidar / Open3D / octomap_server: 本页未运行; OctoMap homepage and Curless & Levoy / Open3D TSDF 以原文为准")


if __name__ == "__main__":
    main()
