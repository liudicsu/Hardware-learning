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

Metrics: action reconstruction MAE after decode, and a pick-success proxy
(decoded action lands within TOL of the true 3D delta). ≥5 seeds. No winner
is presumed. GPU / SpatialVLA weights 本页未运行.
"""
from __future__ import annotations

import math
import random

# Synthetic camera / scene (lesson values, not a datasheet)
FX = FY = 200.0
CX = CY = 0.0
N_TRAIN = 80
N_EVAL = 40
N_BINS = 16  # per axis; synthetic resolution, not the paper's 16/32/8 product
TOL = 0.12  # pick-success proxy radius (m, synthetic)
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_2d_only", "B_ego3d", "C_adaptive_grids")
# Action range used for uniform grids (covers the synthetic deltas)
A_LO, A_HI = -0.6, 0.6


def project_uv(p: tuple[float, float, float]) -> tuple[float, float]:
    x, y, z = p
    z = max(z, 1e-3)
    return FX * x / z + CX, FY * y / z + CY


def sample_point(rng: random.Random) -> tuple[float, float, float]:
    # Camera-frame points in front of the camera; no robot-base frame involved.
    z = rng.uniform(0.4, 1.4)
    x = rng.uniform(-0.35, 0.35)
    y = rng.uniform(-0.25, 0.25)
    return (x, y, z)


def true_action(p: tuple[float, float, float]) -> tuple[float, float, float]:
    # Move a fraction of the way to the point (synthetic pick approach).
    return (0.45 * p[0], 0.45 * p[1], 0.45 * p[2] - 0.15)


def tokens(arm: str, p: tuple[float, float, float]) -> tuple[float, ...]:
    if arm == "A_2d_only":
        u, v = project_uv(p)
        return (u, v)
    # B and C: Ego3D camera-frame xyz — no robot–camera extrinsic.
    return p


def uniform_edges(n: int) -> list[float]:
    return [A_LO + (A_HI - A_LO) * i / n for i in range(n + 1)]


def adaptive_edges(samples: list[float], n: int) -> list[float]:
    """CDF/PPF-style bins: equal mass in the empirical distribution."""
    xs = sorted(samples)
    if len(xs) < 2:
        return uniform_edges(n)
    edges = []
    for i in range(n + 1):
        q = i / n
        # linear interpolation percentile
        pos = q * (len(xs) - 1)
        lo = int(math.floor(pos))
        hi = min(lo + 1, len(xs) - 1)
        w = pos - lo
        edges.append(xs[lo] * (1 - w) + xs[hi] * w)
    # ensure strictly increasing edges for stable digitize
    for i in range(1, len(edges)):
        if edges[i] <= edges[i - 1]:
            edges[i] = edges[i - 1] + 1e-9
    return edges


def digitize(v: float, edges: list[float]) -> int:
    # bin index in [0, n-1]
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
    """Majority vote among k nearest token neighbours (shared BC budget)."""
    dists = []
    for feat, code in bank:
        d = sum((query[i] - feat[i]) ** 2 for i in range(len(query)))
        dists.append((d, code))
    dists.sort(key=lambda t: t[0])
    votes: dict[tuple[int, int, int], int] = {}
    for _, code in dists[:k]:
        votes[code] = votes.get(code, 0) + 1
    return max(votes.items(), key=lambda kv: kv[1])[0]


def run_arm(arm: str, seed: int) -> tuple[float, float]:
    rng = random.Random(1000 + seed)
    # Shared train/eval geometry streams per seed (re-derived identically per arm
    # from the same RNG schedule by resetting).
    rng_pts = random.Random(2000 + seed)
    train_pts = [sample_point(rng_pts) for _ in range(N_TRAIN)]
    train_acts = [true_action(p) for p in train_pts]
    eval_pts = [sample_point(rng_pts) for _ in range(N_EVAL)]
    eval_acts = [true_action(p) for p in eval_pts]

    if arm == "C_adaptive_grids":
        edges = [
            adaptive_edges([a[k] for a in train_acts], N_BINS) for k in range(3)
        ]
    else:
        edges = [uniform_edges(N_BINS) for _ in range(3)]

    bank = []
    for p, a in zip(train_pts, train_acts):
        bank.append((tokens(arm, p), encode_action(a, edges)))

    maes = []
    hits = 0
    for p, a_true in zip(eval_pts, eval_acts):
        code = knn_predict(tokens(arm, p), bank)
        a_hat = decode_action(code, edges)
        err = math.sqrt(sum((a_hat[k] - a_true[k]) ** 2 for k in range(3)))
        maes.append(err)
        if err <= TOL:
            hits += 1
    return sum(maes) / len(maes), hits / len(maes)


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    var = sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)
    return mu, math.sqrt(var)


def main() -> None:
    print(
        "Synthetic SpatialVLA Ego3D/grid toy; shared camera-frame points; "
        "not AX=ZB; not a VLA weight run"
    )
    print(
        f"N_train={N_TRAIN} N_eval={N_EVAL} bins/axis={N_BINS} tol={TOL:.2f}m "
        f"seeds={len(SEEDS)}; Ego3D = camera-frame xyz (no robot-camera extrinsic); "
        f"adaptive = empirical CDF/PPF bins; paper % 以论文为准"
    )
    print("arm action_mae_m pick_success (mean+-sd over seeds)")
    for arm in ARMS:
        maes, succs = [], []
        for seed in SEEDS:
            mae, succ = run_arm(arm, seed)
            maes.append(mae)
            succs.append(succ)
        m_mae, s_mae = mean_sd(maes)
        m_s, s_s = mean_sd(succs)
        print(f"{arm} {m_mae:.4f}+-{s_mae:.4f} {m_s:.4f}+-{s_s:.4f}")
    print(
        "No winner declared: 2D vs Ego3D vs adaptive grids trade mae/success; "
        "not a SpatialVLA benchmark"
    )
    print("GPU / SpatialVLA weights / robot: 本页未运行; Qu et al. 2501.15830 以论文为准")


if __name__ == "__main__":
    main()
