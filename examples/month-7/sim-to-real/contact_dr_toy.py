#!/usr/bin/env python3
"""contact_dr_toy.py: contact-parameter domain randomisation vs latency-only (stdlib).

A force-limited pusher drives a block along a line at a commanded speed v_cmd
(the ONE controller parameter tuned here). The release mark is planned from
the NOMINAL model (slide v^2 / (2 mu0 g) plus the mean latency travel); the
stop command lands L seconds late. The block then slides with a Coulomb
friction proxy (deceleration mu * g) until it rests. Success: final position
within TOL of X_TARGET and at rest by T_MAX. A heavier block accelerates more
slowly under the same force limit; lower friction slides further.

Two arms tune v_cmd on the SAME budget: the same candidate grid, the same
number of training episodes and the SAME noise seed stream (episode k of every
arm and every candidate uses the same latency draw, friction jitter and
uniforms). Score = successes, ties broken by the shorter mean cycle time.
  latency_only  randomises latency only; mu and mass stay nominal
  contact_dr    randomises the same latency AND mu, mass (contact parameters)
Both are evaluated on shared eval episodes: nominal mu / mass (in-distribution
for latency_only), shifted mu, shifted mass, and a mu outside the DR range.
No universal "DR wins": here it pays in nominal cycle time.
Not system identification: nothing is fitted (7.4's sysid_fit owns tau; 5.1
owns PE). The friction model is a toy proxy, not the MuJoCo contact solver.
Real pushing on an SO-101 is not run on this page (本页未运行).
usage: python3 contact_dr_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 74
G = 9.81
DT = 0.001
X_TARGET = 0.30     # m
TOL = 0.015         # m
T_MAX = 1.5         # s, cycle-time limit (push + slide)
K_V, F_MAX = 40.0, 5.0          # N per m/s, N (force-limited pusher)
MU0, M0 = 0.40, 0.50            # nominal friction coefficient, kg
MU_RANGE, M_RANGE = (0.25, 0.60), (0.30, 0.90)   # contact DR ranges
LAT_RANGE = (0.0, 0.03)         # s, randomised in both arms
JITTER = 0.03                   # +-3 % per-episode friction jitter (both arms)
GRID = [round(0.20 + 0.02 * i, 2) for i in range(41)]   # v_cmd candidates 0.20..1.00
N_TRAIN, N_EVAL = 200, 200


def release_mark(v_cmd):
    """Release planned from the NOMINAL model: slide v^2/(2 mu0 g) plus mean latency travel."""
    return X_TARGET - v_cmd ** 2 / (2 * MU0 * G) - v_cmd * sum(LAT_RANGE) / 2


def episode(v_cmd, mu, m, lat):
    """(final position, time to rest) for one push-release-slide episode."""
    x_rel = release_mark(v_cmd)
    x, v, t_rel = 0.0, 0.0, None
    t = 0.0
    while True:
        pushing = t_rel is None or t < t_rel
        if pushing:
            f = max(0.0, min(F_MAX, K_V * (v_cmd - v)))
            a = (f - mu * m * G) / m
            if v <= 0.0 and a < 0.0:
                a = 0.0
        else:
            a = -mu * G
        v = max(0.0, v + a * DT)
        x += v * DT
        t += DT
        if t_rel is None and x >= x_rel:
            t_rel = t + lat
        if t_rel is not None and t >= t_rel and v <= 0.0:
            return x, t
        if t > 10.0:
            return x, t


def draws(seed, n):
    """Shared noise stream: (latency, jitter, u_mu, u_m) per episode."""
    rng = random.Random(seed)
    return [(rng.uniform(*LAT_RANGE), rng.uniform(-JITTER, JITTER), rng.random(), rng.random())
            for _ in range(n)]


def params(arm, d, mu=None, m=None):
    lat, jit, u_mu, u_m = d
    if arm == "contact_dr":
        mu = MU_RANGE[0] + u_mu * (MU_RANGE[1] - MU_RANGE[0])
        m = M_RANGE[0] + u_m * (M_RANGE[1] - M_RANGE[0])
    return mu * (1.0 + jit), m, lat


def score(v_cmd, eps):
    """(successes, mean |err| m, mean cycle time s); success = within TOL and by T_MAX."""
    runs = [episode(v_cmd, mu, m, lat) for mu, m, lat in eps]
    errs = [abs(x - X_TARGET) for x, _ in runs]
    ok = sum(e <= TOL and t <= T_MAX for e, (_, t) in zip(errs, runs))
    return ok, sum(errs) / len(errs), sum(t for _, t in runs) / len(runs)


def tune(arm, train):
    eps = [params(arm, d, MU0, M0) for d in train]
    best = None
    for v in GRID:
        ok, mae, cyc = score(v, eps)
        if best is None or (ok, -cyc) > (best[1], -best[3]):   # success first, then faster cycle
            best = (v, ok, mae, cyc)
    return best


def main() -> None:
    train = draws(SEED, N_TRAIN)
    evals = draws(SEED + 1, N_EVAL)
    print(f"seed={SEED} target={X_TARGET} m tol=+-{TOL} m t_max={T_MAX} s "
          f"latency~U{LAT_RANGE} s jitter=+-{JITTER:.0%} F_max={F_MAX} N")
    print(f"budget per arm: {len(GRID)} v_cmd candidates x {N_TRAIN} train episodes, same seed stream")
    print(f"nominal mu={MU0} m={M0} kg; contact DR mu~U{MU_RANGE} m~U{M_RANGE} kg")
    tuned = {}
    for arm in ("latency_only", "contact_dr"):
        v, ok, mae, cyc = tune(arm, train)
        tuned[arm] = v
        print(f"tuned {arm:<12} v_cmd={v:.2f} m/s release_mark={release_mark(v):.3f} m  "
              f"train success={ok}/{N_TRAIN} mean|err|={mae * 1000:.1f} mm cycle={cyc:.2f} s")
    conds = (("nominal", MU0, M0), ("mu_low_0.28", 0.28, M0), ("mu_high_0.55", 0.55, M0),
             ("mass_0.85", MU0, 0.85), ("mu_out_0.15", 0.15, M0))
    print(f"{'eval (shared episodes)':<22} {'latency_only':>23} {'contact_dr':>23}")
    res = {}
    for name, mu, m in conds:
        cells = []
        eps = [params("eval", d, mu, m) for d in evals]
        for arm in ("latency_only", "contact_dr"):
            ok, mae, cyc = score(tuned[arm], eps)
            res[(name, arm)] = (ok, cyc)
            cells.append(f"{ok:3d}/{N_EVAL} {mae * 1000:5.1f}mm {cyc:4.2f}s")
        print(f"{name:<22} {cells[0]:>23} {cells[1]:>23}")
    lo, dr = "latency_only", "contact_dr"
    assert res[("nominal", lo)][0] >= res[("nominal", dr)][0], "latency_only should not lose in-distribution"
    assert res[("nominal", lo)][1] < res[("nominal", dr)][1], "DR pays cycle time at nominal"
    assert res[("mu_high_0.55", dr)][0] > res[("mu_high_0.55", lo)][0], "DR should help at shifted mu"
    assert res[("mass_0.85", dr)][0] > res[("mass_0.85", lo)][0], "DR should help at shifted mass"
    assert res[("mu_out_0.15", dr)][0] <= N_EVAL // 20, "outside the DR range DR is not a cure"
    print("ok: same budget / seed stream; DR trades nominal cycle time for shifted mu/mass; "
          "mu outside the DR range still fails; toy friction != MuJoCo; SO-101 本页未运行")


if __name__ == "__main__":
    main()
