#!/usr/bin/env python3
"""Stdlib stand-in of fixed-rate chunks vs motion-dependent splines.

Stdlib only. Not a GPU LIBERO-X / EBench / real cooking run, and not a
redo of RTC seam-smoothing, FORGE-Tree, or pi0 / flow-matching already
on this page or on flow-matching-policies. GPU / real cooking / EBench:
本页未运行.

Vela (Li, Wang, Wu, et al., arXiv 2610.05230 v1) represents future
robot behaviour as continuous trajectories: a compact spline-based
action with motion-dependent temporal support, so a fixed output budget
can trade horizon against local resolution instead of emitting a
fixed-rate action chunk. The visible title spelling is Parametrization.
Paper scores on LIBERO-X, EBench, and the real egg-cake cooking and
potato-shredding tasks are 以论文为准 and are not toy outputs.

Shared continuous reference motions (a long smooth move and a short
precise move), a shared output-budget K, and a shared query grid are
generated once per (regime, seed) and then read by every arm (common
random numbers).

Arms:
  A_fixed     fixed-rate action chunk of length K (uniform temporal grid)
  B_spline    compact spline / control-point curve with motion-dependent
              temporal support, evaluated on the same query grid
  C_lose      the same K budget spread so a long horizon becomes too
              coarse (official). A spline queried on a dropped-knot
              support is a named alternative on the same seeds.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean|
and sd both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap
(small if |m| < 20 % of the smaller arm mean, else clear), with a
sign count. ROUND_HALF_UP output. Lower tracking error is better.

Vela paper: body read; 以论文为准.
"""
from __future__ import annotations

import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared stand-in parameters. Written before the first run.
# These are toy tracking errors, not paper success rates.
K = 8
N_QUERY = 121
T_SHORT = 1.0000
T_LONG = 4.0000
T_PRECISE = 1.0000
# Mixed motion lives on [0, T_LONG + T_PRECISE].
T_MIXED = T_LONG + T_PRECISE
# C official: stretch the same K over a longer horizon, which coarsens
# the precise part. Named alternative (same seeds, not adopted): drop
# the knot nearest the precise peak.
C_STRETCH = 2.0000
BUMP_AMP = 1.0000
BUMP_WIDTH = 0.1600

ARMS = ("A_fixed", "B_spline", "C_lose")

REGIMES = {
    "short_smooth": (
        "short, already-smooth move whose uniform grid is fine enough; "
        "A and B may near-tie on tracking error - keep"
    ),
    "mixed_motion": (
        "long smooth + short precise under the same K; B consistent "
        "lower error than A - keep"
    ),
    "coarse_horizon": (
        "C spreads the same K over a longer horizon and loses - keep"
    ),
}


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
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


def rng_for(*parts):
    material = "vela-spline|" + "|".join(str(p) for p in parts)
    return random.Random(material)


def linspace(a, b, n):
    if n == 1:
        return [a]
    step = (b - a) / (n - 1)
    return [a + i * step for i in range(n)]


def query_grid(horizon):
    return linspace(0.0, horizon, N_QUERY)


def bump(t, center, amp=BUMP_AMP, width=BUMP_WIDTH):
    """A compact smooth bump (not a toy paper score)."""
    u = (t - center) / width
    return amp * math.exp(-0.5 * u * u)


def reference(regime, t):
    """Shared continuous reference. 2-D path (x, y)."""
    if regime == "short_smooth":
        # Already-smooth unit-time line; a uniform grid is exact.
        return (t, t)
    # Long smooth transport on [0, T_LONG], then a short precise bump.
    x = t
    if t <= T_LONG:
        y = 0.0
    else:
        y = bump(t, T_LONG + 0.5 * T_PRECISE)
    return (x, y)


def curvature_weight(regime, t, dt=0.0100):
    """Local motion variation used only to place B's temporal support."""
    horizon = T_SHORT if regime == "short_smooth" else T_MIXED
    t0 = t - dt
    t1 = t + dt
    if t0 < 0.0 or t1 > horizon:
        # One-sided speed only; an uneven stencil would invent curvature
        # at the endpoints of a straight move.
        t0 = max(0.0, t0)
        t1 = min(horizon, t1)
        x0, y0 = reference(regime, t0)
        x1, y1 = reference(regime, t1)
        speed = math.hypot(x1 - x0, y1 - y0) / max(t1 - t0, 1e-12)
        return 0.0500 + speed
    x0, y0 = reference(regime, t0)
    x1, y1 = reference(regime, t1)
    xm, ym = reference(regime, t)
    speed = math.hypot(x1 - x0, y1 - y0) / max(t1 - t0, 1e-12)
    second = math.hypot(x0 - 2.0 * xm + x1, y0 - 2.0 * ym + y1) / max((t1 - t0) ** 2, 1e-12)
    return 0.0500 + speed + 8.0000 * second


def invert_cdf(dense, cdf, frac):
    if frac <= 0.0:
        return dense[0]
    if frac >= 1.0:
        return dense[-1]
    i = 1
    while i < len(cdf) - 1 and cdf[i] < frac:
        i += 1
    t0, t1 = dense[i - 1], dense[i]
    c0, c1 = cdf[i - 1], cdf[i]
    if c1 == c0:
        return t1
    return t0 + (frac - c0) / (c1 - c0) * (t1 - t0)


def motion_dependent_times(regime, horizon, k=K):
    """Place K strictly increasing support times by local variation."""
    dense = linspace(0.0, horizon, 400)
    weights = [curvature_weight(regime, t) for t in dense]
    total = sum(weights)
    acc = 0.0
    cdf = []
    for w in weights:
        acc += w
        cdf.append(acc / total)
    raw = [invert_cdf(dense, cdf, j / (k - 1)) for j in range(k)]
    raw[0] = 0.0
    raw[-1] = horizon
    min_gap = horizon / (8.0 * (k - 1))
    times = [0.0]
    n_left = k - 2  # remaining interior + we add them one by one
    for idx, t in enumerate(raw[1:-1]):
        remain = k - 1 - (idx + 1)  # points still to place after this one, including end
        latest = horizon - min_gap * remain
        t = min(max(t, times[-1] + min_gap), latest)
        times.append(t)
    times.append(horizon)
    if not all(times[i] > times[i - 1] for i in range(1, len(times))):
        times = linspace(0.0, horizon, k)
    return times


def piecewise_linear(ts, xs, ys, query):
    out = []
    i = 0
    for t in query:
        while i + 1 < len(ts) - 1 and ts[i + 1] < t:
            i += 1
        t0, t1 = ts[i], ts[i + 1]
        if t1 == t0:
            out.append((xs[i], ys[i]))
            continue
        a = (t - t0) / (t1 - t0)
        a = 0.0 if a < 0.0 else 1.0 if a > 1.0 else a
        out.append((xs[i] + a * (xs[i + 1] - xs[i]), ys[i] + a * (ys[i + 1] - ys[i])))
    return out


def finite_slopes(ts, vs):
    """Finite-difference tangents for a cubic Hermite / Catmull-Rom curve."""
    n = len(ts)
    s = [0.0] * n
    s[0] = (vs[1] - vs[0]) / (ts[1] - ts[0])
    s[-1] = (vs[-1] - vs[-2]) / (ts[-1] - ts[-2])
    for i in range(1, n - 1):
        s[i] = (vs[i + 1] - vs[i - 1]) / (ts[i + 1] - ts[i - 1])
    return s


def eval_hermite(ts, vs, slopes, query):
    out = []
    i = 0
    for t in query:
        while i + 1 < len(ts) - 1 and ts[i + 1] < t:
            i += 1
        t0, t1 = ts[i], ts[i + 1]
        h = t1 - t0
        if h == 0.0:
            out.append(vs[i])
            continue
        u = (t - t0) / h
        u = 0.0 if u < 0.0 else 1.0 if u > 1.0 else u
        h00 = 2.0 * u ** 3 - 3.0 * u ** 2 + 1.0
        h10 = u ** 3 - 2.0 * u ** 2 + u
        h01 = -2.0 * u ** 3 + 3.0 * u ** 2
        h11 = u ** 3 - u ** 2
        out.append(h00 * vs[i] + h10 * h * slopes[i] + h01 * vs[i + 1] + h11 * h * slopes[i + 1])
    return out


def spline_path(ts, xs, ys, query):
    """Cubic Hermite curve through the control points, same query grid."""
    sx = finite_slopes(ts, xs)
    sy = finite_slopes(ts, ys)
    qx = eval_hermite(ts, xs, sx, query)
    qy = eval_hermite(ts, ys, sy, query)
    return list(zip(qx, qy))


def rmse(pred, truth):
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(pred, truth):
        acc += (x0 - x1) ** 2 + (y0 - y1) ** 2
    return math.sqrt(acc / len(truth))


def sample_at(regime, times):
    xs, ys = [], []
    for t in times:
        x, y = reference(regime, t)
        xs.append(x)
        ys.append(y)
    return xs, ys


def dropped_knot_times(times, regime):
    """Drop the support time nearest the precise peak (broken support)."""
    if regime == "short_smooth":
        # Still drop an interior knot so C is a broken support on the
        # same short move (declared lose arm).
        peak = 0.5 * T_SHORT
    else:
        peak = T_LONG + 0.5 * T_PRECISE
    interior = list(range(1, len(times) - 1))
    drop = min(interior, key=lambda i: abs(times[i] - peak))
    return [t for i, t in enumerate(times) if i != drop]


def evaluate(regime, seed, stretch=None, drop_knot=False, k=K):
    # Seed is part of the CRN contract even when the official geometry
    # is deterministic: the shared bank is reserved for alternatives.
    _ = rng_for(regime, seed, "bank")
    if regime == "short_smooth":
        horizon = T_SHORT
        ref_regime = "short_smooth"
        official_stretch = 1.0000
    else:
        # mixed_motion and coarse_horizon share the mixed reference.
        horizon = T_MIXED
        ref_regime = "mixed_motion"
        official_stretch = C_STRETCH
    query = query_grid(horizon)
    truth = [reference(ref_regime, t) for t in query]

    # A: fixed-rate chunk of length K on the true horizon.
    a_times = linspace(0.0, horizon, k)
    ax, ay = sample_at(ref_regime, a_times)
    a_pred = piecewise_linear(a_times, ax, ay, query)

    # B: cubic Hermite curve on motion-dependent support, same K, same query.
    b_times = motion_dependent_times(ref_regime, horizon, k=k)
    bx, by = sample_at(ref_regime, b_times)
    b_pred = spline_path(b_times, bx, by, query)

    # C official: the same K spread over a longer horizon (too coarse).
    # Alternative (drop_knot=True): query a spline on a dropped-knot support.
    if drop_knot:
        c_times = dropped_knot_times(b_times, ref_regime)
        cx, cy = sample_at(ref_regime, c_times)
        c_pred = spline_path(c_times, cx, cy, query)
    else:
        use_stretch = official_stretch if stretch is None else stretch
        c_times = [t for t in linspace(0.0, horizon * use_stretch, k) if t <= horizon + 1e-12]
        if not c_times:
            c_times = [0.0, horizon]
        if c_times[0] != 0.0:
            c_times = [0.0] + c_times
        if c_times[-1] < horizon:
            c_times.append(horizon)
        cx, cy = sample_at(ref_regime, c_times)
        c_pred = piecewise_linear(c_times, cx, cy, query)

    return {
        "k": k,
        "n_query": N_QUERY,
        "horizon": horizon,
        "A_rmse": rmse(a_pred, truth),
        "B_rmse": rmse(b_pred, truth),
        "C_rmse": rmse(c_pred, truth),
        "A_n": len(a_times),
        "B_n": len(b_times),
        "C_n": len(c_times),
    }


def official_rows(name, stretch=None, drop_knot=False, k=K):
    return [evaluate(name, seed, stretch=stretch, drop_knot=drop_knot, k=k) for seed in SEEDS]


def print_regime(title, rows):
    print(f"regime {title}  (mean+-sd over seeds)")
    print(
        f"  k={rows[0]['k']} n_query={rows[0]['n_query']} "
        f"horizon={num(rows[0]['horizon'])} "
        f"A_n={rows[0]['A_n']} B_n={rows[0]['B_n']} C_n={rows[0]['C_n']}"
    )
    a = [r["A_rmse"] for r in rows]
    b = [r["B_rmse"] for r in rows]
    c = [r["C_rmse"] for r in rows]
    print(f"  A_fixed rmse {num(mean_sd(a)[0])}+-{num(mean_sd(a)[1])}")
    print(f"  B_spline rmse {num(mean_sd(b)[0])}+-{num(mean_sd(b)[1])}")
    print(f"  C_lose rmse {num(mean_sd(c)[0])}+-{num(mean_sd(c)[1])}")
    print(f"  paired B-A rmse: {verdict(b, a)}")
    print(f"  paired C-B rmse: {verdict(c, b)}")
    print(f"  paired C-A rmse: {verdict(c, a)}")


def main():
    print("Stdlib stand-in of fixed-rate chunks vs motion-dependent splines; not a Vela eval")
    print(
        f"declared K={K} N_QUERY={N_QUERY} T_SHORT={num(T_SHORT)} "
        f"T_LONG={num(T_LONG)} T_PRECISE={num(T_PRECISE)} "
        f"T_MIXED={num(T_MIXED)} BUMP_AMP={num(BUMP_AMP)} "
        f"BUMP_WIDTH={num(BUMP_WIDTH)} C_STRETCH={num(C_STRETCH)} "
        f"SMALL_FRAC={num(SMALL_FRAC)} "
        f"seeds={','.join(str(s) for s in SEEDS)}"
    )
    print(
        "declared arms: A_fixed uniform temporal grid of length K; "
        "B_spline compact cubic Hermite curve with motion-dependent temporal support; "
        "C_lose official stretch of the same K over a longer horizon; "
        "dropped-knot support is a named alternative"
    )
    print(f"hand_calc T_LONG + T_PRECISE = {num(T_LONG + T_PRECISE)}")
    print(f"hand_calc query spacing on short = {num(T_SHORT / (N_QUERY - 1))}")
    print(f"hand_calc query spacing on mixed = {num(T_MIXED / (N_QUERY - 1))}")
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print("paper_figure LIBERO-X / EBench / real cooking scores 以论文为准, not a toy output")
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: reference motions, output-budget K and the "
        "query grid are shared across arms at each regime and seed"
    )
    print(
        "Assumptions: stdlib tracking-error stand-in, not LIBERO-X eval, "
        "not EBench, not real cooking, not RTC seams, not FORGE-Tree, "
        "not pi0 flow-matching"
    )
    print("Paper LIBERO-X / EBench / cooking scores 以论文为准")
    print("GPU / real cooking / EBench: 本页未运行")
    print(f"declared short_smooth: {REGIMES['short_smooth']}")
    print_regime("short_smooth", official_rows("short_smooth"))
    print(f"declared expectation mixed_motion: {REGIMES['mixed_motion']}")
    print_regime("mixed_motion", official_rows("mixed_motion"))
    print(f"declared expectation coarse_horizon: {REGIMES['coarse_horizon']}")
    print_regime("coarse_horizon", official_rows("coarse_horizon"))

    print("alternative same seeds dropped-knot support (not adopted)")
    print_regime(
        "mixed_motion alt_dropped_knot",
        official_rows("mixed_motion", drop_knot=True),
    )

    print("No GPU eval was started")
    print(
        "No winner is universal: a short already-smooth move may near-tie; "
        "do not retune K so the spline must win every cell"
    )


if __name__ == "__main__":
    main()
