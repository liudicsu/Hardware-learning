#!/usr/bin/env python3
"""Lidar realism vs ideal rays: what a simulated scan does and does not predict.

Synthetic 2D ray casting, stdlib only.  Not `gz sim`, not gpu_lidar, not the
OctoMap/TSDF toy (slam-nav), not DWA and not the physics-step-size section
on this page.  Real lidar / Gazebo run: 本页未运行.  SDFormat lidar / noise
spec and gz-sensors Lidar.cc statements 以文档为准.

What the bodies we read say (and what this toy keeps):
  SDFormat 1.11 lidar.sdf: <range><min>/<max> are "the minimum / maximum
    distance for each lidar ray"; <noise> type "gaussian" draws noise values
    independently for each beam (mean, stddev); visibility_mask decides
    which objects' visibility_flags the lidar sees.
  gz-sensors Lidar.cc: the lidar only supports Gaussian noise; after noise
    every finite range is clamped to [RangeMin, RangeMax] (std::clamp), NaN
    becomes RangeMax.
  This lesson's "simulation versus the datasheet" prose: gpu_lidar rays hit
    the visual geometry, not collision shapes; no dust / glass multipath /
    glossy drop-outs / blind zone unless modelled.

Scene: sensor at the origin facing +x, N_BEAMS beams from -30 to +30 deg.
Surfaces are segments x = d, y in [y0, y1], each flagged visual / collision
/ glossy.  "Geometric truth" is the nearest physical (collision) surface.

Real-unit stand-in R (the reference the sims try to predict; a declared toy,
not a datasheet unit): physical surfaces, range bias R_BIAS, Gaussian noise
R_SIGMA from its OWN random stream, glossy beams drop out with probability
P_DROP_R, and nothing is returned inside the blind zone (true range < MIN).

Common random numbers: one sim noise stream per (regime, seed) shared by
every sim arm; R uses a separate stream that no arm sees.  Arms:
  A_ideal   : visual geometry, no noise, no blind zone (reports the true
              range even below MIN), no drop-outs
  B_lesson  : visual geometry + Gaussian SIGMA (the lesson's 0.01 m knob),
              then the gz-sensors clamp to [MIN, MAX]
  C_realism : physical geometry + declared bias C_BIAS + Gaussian SIGMA,
              glossy drop-out with probability P_DROP_C, blind zone = no
              return.  C's parameters are guesses, not R's true values.
No integration step: one static scan per seed, no time step.

Metrics per arm and seed:
  mean_err : mean(sim range - geometric truth) over beams where both exist (m)
  ret_err  : |returns(sim) - returns(R)| / N_BEAMS  (scan-level count error)
  mismatch : beams where sim and R disagree: one returns and the other does
             not, or both return but differ by more than TOL (beam-level)
  near_err : |nearest return(sim) - nearest return(R)| (m), no return -> MAX

Regimes and parameters were written before the first run:
  clear_wall  : matte wall at 1.68 m (the lesson's 1.80 - 0.12 check)
                - A vs B near-tie on mean_err; C consistent worse than A on
                  mean_err (it adds a bias the geometry does not have); keep
  glossy      : glossy panel at 1.20 m in front of a 2.50 m wall
                - A consistent lose to C on ret_err; keep.  Beam-level
                  mismatch is NOT declared a C win: a drop-out rate cannot
                  say which beam drops
  min_range   : a 4 cm post at 0.12 m (below MIN) in front of the 1.68 m wall
                - A and B consistent lose to C on mismatch and near_err; keep
  visual_only : a visual-only banner at 0.90 m and a collision-only box at
                1.00 m in front of a 2.50 m wall
                - A and B consistent lose to C on mismatch and near_err; keep
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared model parameters, written before the first run.  MIN / MAX / SIGMA
# are this lesson's sensors.gazebo.xacro values; the rest are toy values.
N_BEAMS = 61
FOV_DEG = 30.0
MIN = 0.20            # m, <range><min> in this lesson's xacro
MAX = 8.0             # m, <range><max> in this lesson's xacro
SIGMA = 0.01          # m, <noise><stddev> in this lesson's xacro (teaching knob)
C_BIAS = 0.015        # m, C's guess of the range bias (toy)
P_DROP_C = 0.5        # C's guess of the glossy drop-out probability (toy)
R_BIAS = 0.02         # m, real-unit stand-in bias (toy, not a datasheet value)
R_SIGMA = 0.012       # m, real-unit stand-in noise (toy)
P_DROP_R = 0.6        # real-unit stand-in glossy drop-out probability (toy)
TOL = 0.10            # m, beam-level agreement tolerance

ARMS = ("A_ideal", "B_lesson", "C_realism")
# (x, y0, y1, visual, collision, glossy)
REGIMES = {
    "clear_wall": [(1.68, -1.5, 1.5, True, True, False)],
    "glossy": [(1.20, -0.35, 0.35, True, True, True), (2.50, -2.0, 2.0, True, True, False)],
    "min_range": [(0.12, -0.02, 0.02, True, True, False), (1.68, -1.5, 1.5, True, True, False)],
    "visual_only": [(0.90, 0.30, 0.60, True, False, False), (1.00, -0.50, -0.20, False, True, False),
                    (2.50, -2.0, 2.0, True, True, False)],
}


def beam_angles():
    step = 2.0 * FOV_DEG / (N_BEAMS - 1)
    return [math.radians(-FOV_DEG + i * step) for i in range(N_BEAMS)]


def cast(theta, surfaces, use):
    """Nearest surface hit along the beam; use='visual' or 'collision'."""
    best, glossy = None, False
    c, s = math.cos(theta), math.sin(theta)
    for x, y0, y1, vis, col, gl in surfaces:
        if (use == "visual" and not vis) or (use == "collision" and not col):
            continue
        r = x / c
        y = r * s
        if y0 <= y <= y1 and (best is None or r < best):
            best, glossy = r, gl
    return best, glossy


def shared_draws(regime, seed):
    """Common random numbers: one sim stream shared by every arm; R has its own."""
    rs = random.Random(f"{regime}/{seed}/sim")
    rr = random.Random(f"{regime}/{seed}/real")
    sim = [(rs.gauss(0.0, 1.0), rs.random()) for _ in range(N_BEAMS)]
    real = [(rr.gauss(0.0, 1.0), rr.random()) for _ in range(N_BEAMS)]
    return sim, real


def scan(arm, regime, draws, c_bias=C_BIAS, p_drop_c=P_DROP_C):
    surf = REGIMES[regime]
    out = []
    for theta, (z, u) in zip(beam_angles(), draws):
        if arm == "R":
            r, gl = cast(theta, surf, "collision")
            if r is None or r < MIN or (gl and u < P_DROP_R):
                out.append(None)
                continue
            r = r + R_BIAS + R_SIGMA * z
            out.append(r if r <= MAX else None)
            continue
        if arm == "A_ideal":
            r, _ = cast(theta, surf, "visual")
            out.append(r if r is not None and r <= MAX else None)
        elif arm == "B_lesson":
            r, _ = cast(theta, surf, "visual")
            out.append(None if r is None else min(max(r + SIGMA * z, MIN), MAX))
        else:
            r, gl = cast(theta, surf, "collision")
            if r is None or r < MIN or (gl and u < p_drop_c):
                out.append(None)
                continue
            r = r + c_bias + SIGMA * z
            out.append(r if r <= MAX else None)
    return out


def truth(regime):
    return [cast(t, REGIMES[regime], "collision")[0] for t in beam_angles()]


def metrics(sim, real, geo, tol=TOL):
    errs = [s - g for s, g in zip(sim, geo) if s is not None and g is not None]
    n_sim = sum(1 for s in sim if s is not None)
    n_real = sum(1 for r in real if r is not None)
    mism = sum(1 for s, r in zip(sim, real)
               if (s is None) != (r is None) or (s is not None and abs(s - r) > tol))
    near = lambda xs: min([x for x in xs if x is not None], default=MAX)
    return {"mean_err": sum(errs) / len(errs), "ret_err": abs(n_sim - n_real) / N_BEAMS,
            "mismatch": float(mism), "near_err": abs(near(sim) - near(real)),
            "returns": float(n_sim)}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
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
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


KEYS = ("mean_err", "ret_err", "mismatch", "near_err")


def collect(regime, **kw):
    geo = truth(regime)
    res = {arm: [] for arm in ARMS + ("R",)}
    for seed in SEEDS:
        sim_d, real_d = shared_draws(regime, seed)
        real = scan("R", regime, real_d)
        for arm in ARMS:
            res[arm].append(metrics(scan(arm, regime, sim_d, **kw), real, geo))
        res["R"].append(metrics(real, real, geo))
    return res


def col(rows, key):
    return [r[key] for r in rows]


def report(regime):
    res = collect(regime)
    geo = truth(regime)
    hit = [g for g in geo if g is not None]
    below = sum(1 for g in hit if g < MIN)
    print(f"{regime} (beams {N_BEAMS}; geometric hits {len(hit)}; true range below MIN on {below} beams; "
          f"nearest true {min(hit):.4f} m):")
    r_ret = col(res["R"], "returns")
    print(f"  R_real_unit returns {fmt_pair(*mean_sd(r_ret))} mean_err {fmt_pair(*mean_sd(col(res['R'], 'mean_err')))}")
    for arm in ARMS:
        rows = res[arm]
        print(f"  {arm} returns {fmt_pair(*mean_sd(col(rows, 'returns')))} "
              + " ".join(f"{k} {fmt_pair(*mean_sd(col(rows, k)))}" for k in KEYS))
    for k in KEYS:
        print(f"  paired B-A {k}: {verdict(col(res['B_lesson'], k), col(res['A_ideal'], k))}")
    for k in KEYS[1:]:
        print(f"  paired A-C {k}: {verdict(col(res['A_ideal'], k), col(res['C_realism'], k))}")
        print(f"  paired B-C {k}: {verdict(col(res['B_lesson'], k), col(res['C_realism'], k))}")
    if regime == "clear_wall":
        print(f"  paired C-A mean_err: {verdict(col(res['C_realism'], 'mean_err'), col(res['A_ideal'], 'mean_err'))}")
    return res


def main():
    print("Synthetic 2D lidar realism toy; shared sim noise stream; real-unit stand-in R on its own stream; not gz sim")
    print(f"seeds={len(SEEDS)} N_BEAMS={N_BEAMS} FOV=+-{FOV_DEG:.1f} deg MIN={MIN:.2f} m MAX={MAX:.1f} m SIGMA={SIGMA:.2f} m "
          f"(MIN/MAX/SIGMA from this lesson's sensors.gazebo.xacro)")
    print(f"C_BIAS={C_BIAS:.3f} m P_DROP_C={P_DROP_C:.2f}; R_BIAS={R_BIAS:.3f} m R_SIGMA={R_SIGMA:.3f} m P_DROP_R={P_DROP_R:.2f}; "
          f"TOL={TOL:.2f} m (declared toy parameters, not datasheet values)")
    print("No integration step: one static scan per seed, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print("clamp_rule (gz-sensors Lidar::Clamp): finite range -> clamp to [MIN, MAX]; B reports MIN for a surface closer than MIN")
    print("blind_rule (R and C, toy): true range < MIN -> no return; A (ideal) reports the true range")
    for x, label in ((0.12, "below"), (0.20, "at"), (0.2001, "above")):
        b = min(max(x, MIN), MAX)
        c = None if x < MIN else x
        print(f"  boundary {label} MIN: true={x:.4f} m -> A {x:.4f} B {b:.4f} C {'none' if c is None else f'{c:.4f}'} (no noise, no bias)")
    print(f"hand_calc straight-ahead wall: 1.80 - 0.12 = {1.80 - 0.12:.2f} m; beam at 30 deg: 1.68 / cos(30 deg) = {1.68 / math.cos(math.radians(30)):.4f} m")
    for regime in REGIMES:
        report(regime)
    print("alternative TOL=0.05 m (same seeds) on min_range, visual_only and clear_wall:")
    for regime in ("min_range", "visual_only", "clear_wall"):
        geo = truth(regime)
        rows = {arm: [] for arm in ARMS}
        for seed in SEEDS:
            sim_d, real_d = shared_draws(regime, seed)
            real = scan("R", regime, real_d)
            for arm in ARMS:
                rows[arm].append(metrics(scan(arm, regime, sim_d), real, geo, tol=0.05))
        print(f"  {regime} paired A-C mismatch@TOL0.05: {verdict(col(rows['A_ideal'], 'mismatch'), col(rows['C_realism'], 'mismatch'))}")
    print("alternative P_DROP_C=0.90 on glossy (same seeds; C over-estimates drop-outs):")
    alt = collect("glossy", p_drop_c=0.90)
    print(f"  paired A-C ret_err@alt: {verdict(col(alt['A_ideal'], 'ret_err'), col(alt['C_realism'], 'ret_err'))}")
    print("alternative C_BIAS=0.000 on clear_wall (same seeds; C without the bias guess):")
    alt = collect("clear_wall", c_bias=0.0)
    print(f"  paired C-A mean_err@alt: {verdict(col(alt['C_realism'], 'mean_err'), col(alt['A_ideal'], 'mean_err'))}")
    print("No winner declared: ideal rays match geometry best on a clear wall, and lose where the real unit drops, clips or sees other geometry")
    print("Real lidar / Gazebo run: 本页未运行; SDFormat lidar spec and gz-sensors Lidar.cc statements 以文档为准")


if __name__ == "__main__":
    main()
