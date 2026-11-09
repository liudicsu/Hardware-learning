#!/usr/bin/env python3
"""Synthetic SpatialVLA-style Ego3D + adaptive action-grid literacy toy.

NOT SpatialVLA weights, NOT AX=ZB multi-view chain-closure (that stays in
extrinsics_chain_toy.py on this host), NOT UniVLA/TraceVLA. Stdlib only.

Paper (Qu et al., arXiv 2501.15830; numbers 以论文为准): Ego3D Position
Encoding injects camera-frame 3D without robot–camera extrinsic calibration;
Adaptive Action Grids discretize actions via CDF/PPF (denser bins where the
training actions concentrate) instead of a fixed uniform linear grid.

Shared scene for every arm (no privileged robot-base poses):
  - synthetic object points in the *egocentric camera frame*
  - synthetic translation actions toward the object
Arms differ only in how they encode observations / discretize actions:
  A_2d_only        tokens = projected (u, v); uniform action bins
  B_ego3d          tokens = camera-frame (x, y, z); uniform action bins
  C_adaptive_grids tokens = camera-frame (x, y, z); CDF/PPF adaptive bins
Adaptive bin edges are fit on the train action distribution only.

Primary metric: action reconstruction MAE (m). Secondary: pick-success at a
strict TOL, plus an IID vs shifted-eval MAE pair that shows the adaptive-bin
edge narrowing or vanishing when the test action distribution moves.
≥5 seeds. No unbeatable 1.00 success lead. GPU / SpatialVLA weights 本页未运行.
"""
from __future__ import annotations

import math
import random

FX = FY = 200.0
CX = CY = 0.0
N_TRAIN = 80
N_EVAL = 40
N_BINS = 16
TOL_STRICT = 0.05  # strict success threshold (m); not a ceiling at 0.12
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_2d_only", "B_ego3d", "C_adaptive_grids")
A_LO, A_HI = -0.6, 0.6
# Shifted eval: points farther / more lateral → action deltas outside train mass
SHIFT_XY = 1.6
SHIFT_Z_LO, SHIFT_Z_HI = 1.2, 1.8


def project_uv(p: tuple[float, float, float]) -> tuple[float, float]:
    x, y, z = p
    z = max(z, 1e-3)
    return FX * x / z + CX, FY * y / z + CY


def sample_point(rng: random.Random, shifted: bool = False) -> tuple[float, float, float]:
    if shifted:
        z = rng.uniform(SHIFT_Z_LO, SHIFT_Z_HI)
        x = rng.uniform(-0.35 * SHIFT_XY, 0.35 * SHIFT_XY)
        y = rng.uniform(-0.25 * SHIFT_XY, 0.25 * SHIFT_XY)
    else:
        z = rng.uniform(0.4, 1.4)
        x = rng.uniform(-0.35, 0.35)
        y = rng.uniform(-0.25, 0.25)
    return (x, y, z)


def true_action(p: tuple[float, float, float]) -> tuple[float, float, float]:
    return (0.45 * p[0], 0.45 * p[1], 0.45 * p[2] - 0.15)


def tokens(arm: str, p: tuple[float, float, float]) -> tuple[float, ...]:
    if arm == "A_2d_only":
        u, v = project_uv(p)
        return (u, v)
    return p


def uniform_edges(n: int) -> list[float]:
    return [A_LO + (A_HI - A_LO) * i / n for i in range(n + 1)]


def adaptive_edges(samples: list[float], n: int) -> list[float]:
    xs = sorted(samples)
    if len(xs) < 2:
        return uniform_edges(n)
    edges = []
    for i in range(n + 1):
        q = i / n
        pos = q * (len(xs) - 1)
        lo = int(math.floor(pos))
        hi = min(lo + 1, len(xs) - 1)
        w = pos - lo
        edges.append(xs[lo] * (1 - w) + xs[hi] * w)
    for i in range(1, len(edges)):
        if edges[i] <= edges[i - 1]:
            edges[i] = edges[i - 1] + 1e-9
    return edges


def digitize(v: float, edges: list[float]) -> int:
    n = len(edges) - 1
    if v <= edges[0]:
        return 0
    if v >= edges[-1]:
        return n - 1
    for i in range(n):
        if edges[i] <= v < edges[i + 1]:
            return i
    return n - 1


def bin_center(i: int, edges: list[float]) -> float:
    return 0.5 * (edges[i] + edges[i + 1])


def encode_action(a: tuple[float, float, float], edges: list[list[float]]) -> tuple[int, int, int]:
    return tuple(digitize(a[k], edges[k]) for k in range(3))  # type: ignore


def decode_action(codes: tuple[int, int, int], edges: list[list[float]]) -> tuple[float, float, float]:
    return tuple(bin_center(codes[k], edges[k]) for k in range(3))  # type: ignore


def knn_predict(
    query: tuple[float, ...],
    bank: list[tuple[tuple[float, ...], tuple[int, int, int]]],
    k: int = 5,
) -> tuple[int, int, int]:
    dists = []
    for feat, code in bank:
        d = sum((query[i] - feat[i]) ** 2 for i in range(len(query)))
        dists.append((d, code))
    dists.sort(key=lambda t: t[0])
    votes: dict[tuple[int, int, int], int] = {}
    for _, code in dists[:k]:
        votes[code] = votes.get(code, 0) + 1
    return max(votes.items(), key=lambda kv: kv[1])[0]


def run_arm(arm: str, seed: int) -> dict[str, float]:
    rng_pts = random.Random(2000 + seed)
    train_pts = [sample_point(rng_pts, False) for _ in range(N_TRAIN)]
    train_acts = [true_action(p) for p in train_pts]
    eval_pts = [sample_point(rng_pts, False) for _ in range(N_EVAL)]
    eval_acts = [true_action(p) for p in eval_pts]
    shift_pts = [sample_point(rng_pts, True) for _ in range(N_EVAL)]
    shift_acts = [true_action(p) for p in shift_pts]

    if arm == "C_adaptive_grids":
        edges = [adaptive_edges([a[k] for a in train_acts], N_BINS) for k in range(3)]
    else:
        edges = [uniform_edges(N_BINS) for _ in range(3)]

    bank = [(tokens(arm, p), encode_action(a, edges)) for p, a in zip(train_pts, train_acts)]

    def eval_set(pts, acts):
        maes = []
        hits = 0
        for p, a_true in zip(pts, acts):
            code = knn_predict(tokens(arm, p), bank)
            a_hat = decode_action(code, edges)
            err = math.sqrt(sum((a_hat[k] - a_true[k]) ** 2 for k in range(3)))
            maes.append(err)
            if err <= TOL_STRICT:
                hits += 1
        return sum(maes) / len(maes), hits / len(maes)

    mae_iid, succ_iid = eval_set(eval_pts, eval_acts)
    mae_shift, succ_shift = eval_set(shift_pts, shift_acts)
    return {
        "mae_iid": mae_iid,
        "succ_strict": succ_iid,
        "mae_shift": mae_shift,
        "succ_shift": succ_shift,
    }


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    print(
        "Synthetic SpatialVLA Ego3D/grid toy; shared camera-frame points; "
        "MAE primary; not AX=ZB; not a VLA weight run"
    )
    print(
        f"N_train={N_TRAIN} N_eval={N_EVAL} bins/axis={N_BINS} "
        f"TOL_strict={TOL_STRICT:.2f}m seeds={len(SEEDS)}; "
        f"Ego3D = camera-frame xyz (no robot-camera extrinsic); "
        f"adaptive = empirical CDF/PPF bins fit on train only; "
        f"shift = farther/lateral eval points; paper % 以论文为准"
    )
    print(
        "arm mae_iid_m succ_strict mae_shift_m (mean+-sd over seeds)"
    )
    for arm in ARMS:
        cols = {"mae_iid": [], "succ_strict": [], "mae_shift": []}
        for seed in SEEDS:
            r = run_arm(arm, seed)
            cols["mae_iid"].append(r["mae_iid"])
            cols["succ_strict"].append(r["succ_strict"])
            cols["mae_shift"].append(r["mae_shift"])
        parts = []
        for key in ("mae_iid", "succ_strict", "mae_shift"):
            m, s = mean_sd(cols[key])
            parts.append(f"{m:.4f}+-{s:.4f}")
        print(f"{arm} " + " ".join(parts))
    print(
        "MAE is primary: Ego3D cuts error vs 2D; adaptive bins help on the "
        "IID train mass and the gap narrows under action-distribution shift; "
        "strict TOL is secondary (not a 1.00 ceiling claim)"
    )
    print("GPU / SpatialVLA weights / robot: 本页未运行; Qu et al. 2501.15830 以论文为准")


if __name__ == "__main__":
    main()
