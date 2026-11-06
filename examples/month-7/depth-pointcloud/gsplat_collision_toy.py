#!/usr/bin/env python3
"""Thresholded synthetic Gaussians; CPU sphere collision literacy, not a planner.
Splat-Nav v1 Theorem 1 / Corollaries 1,3: separation iff some K(s)>1.
Finite samples certify only witnessed separation (conservative in exact arithmetic).
Ground truth is independent Euclidean point-to-solid-ellipsoid distance, solved
by a monotone Lagrange-multiplier root with 100 bisections; not K(s) sampling.
Splat-Nav v2 Sec. IV Eq. (2) uses D^2 <= chi2_3(gamma) for raw covariance C,
then absorbs that quantile into the shape matrix. Our k-sigma convention uses
D^2 <= k^2, shape = k^2 C; matching thresholds means k^2 = chi2_3(gamma).
For an ideal normalized 3-D Gaussian, k=2 encloses about 73.85 %, NOT the 1-D
95.45 % or the paper's gamma=0.99 (k about 3.37). Sec. VI-C2 also studies
chi2_3(gamma)=4; choices/claims are 以论文为准. Here k=2 is a geometric cutoff,
not calibrated occupancy confidence; opacity_min is a separate filter, not gamma.
Floating-point arithmetic here is NOT interval-certified safety software.
"""
from __future__ import annotations

import math
import random

SEED = 75
K_SIGMA = 2.0
OPACITY_MIN = 0.5
RADIUS = 0.12  # m, sphere robot
# mean[m], raw Gaussian standard deviations[m], opacity; axis-aligned for stdlib.
GAUSSIANS = (
    ((-0.65, 0.0, 0.0), (0.34, 0.10, 0.18), 0.9),
    ((0.55, 0.2, 0.15), (0.12, 0.35, 0.16), 0.8),
    ((0.0, -0.7, -0.1), (0.24, 0.15, 0.10), 0.7),
    ((0.0, 0.0, 0.0), (0.5, 0.5, 0.5), 0.2),  # excluded, not physical free-space proof
)
SCENE = tuple((mu, tuple(K_SIGMA * v for v in sigma))
              for mu, sigma, opacity in GAUSSIANS if opacity >= OPACITY_MIN)
SAMPLES = tuple(i / 16 for i in range(1, 16))


def distance_to_ellipsoid(d, axes):
    """Distance from point d to solid ellipsoid, not distance to its AABB.
    Outside: closest y_i=a_i^2*d_i/(a_i^2+lambda), sum(y_i/a_i)^2=1.
    The latter strictly decreases in lambda>=0, so bracket + bisection applies.
    """
    if sum((x / a) ** 2 for x, a in zip(d, axes)) <= 1:
        return 0.0
    def residual(lam):
        return sum((a * x / (a * a + lam)) ** 2
                   for x, a in zip(d, axes)) - 1
    lo, hi = 0.0, 1.0
    while residual(hi) > 0:
        hi *= 2
    for _ in range(100):
        mid = (lo + hi) / 2
        if residual(mid) > 0:
            lo = mid
        else:
            hi = mid
    y = tuple(a * a * x / (a * a + hi) for x, a in zip(d, axes))
    return math.sqrt(sum((x - z) ** 2 for x, z in zip(d, y)))


def truth(point):
    return any(distance_to_ellipsoid(tuple(x - c for x, c in zip(point, mu)), axes)
               <= RADIUS + 1e-12 for mu, axes in SCENE)


def aabb_collision(point):
    # Each ellipsoid lies in its enclosing AABB. Sphere-box distance is exact.
    hits = []
    for mu, axes in SCENE:
        dist2 = sum(max(abs(x - c) - a, 0.0) ** 2
                    for x, c, a in zip(point, mu, axes))
        hits.append(dist2 <= RADIUS ** 2 + 1e-12)
    # No early exits: both arms visit every obstacle on every query.
    return any(hits), len(SCENE) * 3  # axis-kernel evaluations


def sampled_collision(point, samples=SAMPLES):
    hits = []
    for mu, axes in SCENE:
        d = tuple(x - c for x, c in zip(point, mu))
        # Sa=diag(axes^2), Sb=radius^2 I; direct Theorem1 convention.
        values = [sum(x * x / (a * a / (1 - s) + RADIUS ** 2 / s)
                      for x, a in zip(d, axes)) for s in samples]
        # A witness >1 certifies DISJOINT; no witness means possible collision.
        hits.append(not any(v > 1.0 + 1e-10 for v in values))
    return any(hits), len(SCENE) * len(samples) * 3


def self_test():
    axes = (1.0, 0.5, 0.25)
    assert distance_to_ellipsoid((0, 0, 0), axes) == 0
    assert abs(distance_to_ellipsoid((1.2, 0, 0), axes) - 0.2) < 1e-12
    assert abs(distance_to_ellipsoid((0, 0, 0.45), axes) - 0.2) < 1e-12
    assert abs(distance_to_ellipsoid((2, 0, 0), (1, 1, 1)) - 1) < 1e-12
    assert sampled_collision(SCENE[0][0])[0]
    assert not sampled_collision((5, 5, 5))[0]
    # Near tangency is collision under the lesson's tolerance.
    mu, a = SCENE[0]
    tangent = (mu[0] - a[0] - RADIUS, mu[1], mu[2])
    assert truth(tangent) and aabb_collision(tangent)[0] and sampled_collision(tangent)[0]


def main():
    self_test()
    rng = random.Random(SEED)
    points = [tuple(rng.uniform(-1.5, 1.5) for _ in range(3)) for _ in range(2000)]
    # Include known collision, enclosing-box corner, free and tangent queries.
    points += [SCENE[0][0], (-1.30, 0.19, 0.35), (5, 5, 5),
               (-0.65 - 0.68 - RADIUS, 0, 0)]
    actual = [truth(p) for p in points]
    positives, negatives = sum(actual), len(actual) - sum(actual)
    print(f"seed={SEED} k_sigma={K_SIGMA:.1f} opacity_min={OPACITY_MIN:.1f} "
          f"obstacles={len(SCENE)} robot_radius_m={RADIUS:.2f}")
    print(f"shared_queries={len(points)} truth_collision={positives} truth_free={negatives}")
    print("truth=independent_distance_root_100_bisections; touching=collision")
    print("arm false_safe/count_truth_collision false_alarm/count_truth_free axis_kernel_evals/query")
    rows = []
    for name, checker in (("aabb", aabb_collision), ("ellipsoid_s15", sampled_collision)):
        results = [checker(p) for p in points]
        fs = sum(t and not hit for t, (hit, _) in zip(actual, results))
        fa = sum(not t and hit for t, (hit, _) in zip(actual, results))
        cost = sum(c for _, c in results) / len(points)
        print(f"{name} {fs}/{positives}={fs/positives:.6f} "
              f"{fa}/{negatives}={fa/negatives:.6f} {cost:.0f}")
        assert fs == 0
        rows.append(fa)
    assert rows[0] > rows[1]  # measured on this declared scene, not universal ranking
    print("cost=axis_kernel_evaluations_not_wallclock; kernels_have_different_operations")
    print("finite_s: witness_K_gt_1=separate; no_witness=collision; exact_arithmetic_conservative")
    print("float_not_certified; Gaussian_threshold_not_physical_surface; GPU_not_run")


if __name__ == "__main__":
    main()
