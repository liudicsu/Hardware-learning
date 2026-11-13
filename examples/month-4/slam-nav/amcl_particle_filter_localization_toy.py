#!/usr/bin/env python3
"""AMCL-style particle filter localization toy against a known 2-D map.

Synthetic stand-in for the Nav2 AMCL particle filter: a 2-D occupancy map of
axis-aligned rectangles, a robot whose heading is known and fixed (declared
IMU stand-in), four axis-aligned range beams, a motion model with scale and
additive noise, a low-variance (systematic) resampler, a KLD-style adaptive
particle count and an augmented-MCL-style random-pose recovery.  This is not
Nav2, not a bag playback, not a real robot and not a live ROS wiki run
(本页未运行).

Every constant in this file is a DECLARED TOY PARAMETER, written before the
first run.  The ROS amcl defaults (min_particles 100, max_particles 5000,
kld_err 0.01, recovery_alpha_slow 0.001, recovery_alpha_fast 0.1) are 以原文为准
and are NOT what this toy uses unless the text here says so; the toy uses
N_MIN = 100, N_MAX = 600, EPS = 0.05, Z_Q = 2.326, A_SLOW = 0.05,
A_FAST = 0.5, and N_C = 30 particles for the small arm.

Map (metres, axis-aligned rectangles).  Room "distinctive": outer walls
0..10 x 0..6 plus three interior boxes (1.5..2.5 x 1..2), (6..7.5 x 3.5..5),
(4..4.5 x 0..2.5).  Room "corridor": outer walls 0..12 x 0..2 with no
interior boxes, so the range pattern is translationally ambiguous along x.
The outer wall rectangle bounds the free space and the interior boxes are
the obstacles, so the free space is the room rectangle minus those boxes.

Robot state (x, y); heading is known and fixed, so the filter tracks x and y
only.  Sensor: four axis-aligned beams (+x, -x, +y, -y) returning the range
to the nearest rectangle edge along that axis (exact axis-aligned ray test),
plus N(0, SIG_Z = 0.1) noise, capped at R_MAX = 8 m.  Motion: each step the
commanded move is a vector (dx, dy) of length 0.3 m in a random free
direction (the direction is redrawn if the move would enter an obstacle or
leave the map, at most 20 redraws, then the robot stays); the true motion is
commanded * (1 + N(0, 0.05)) plus N(0, 0.02) per axis, while odometry
reports the commanded move.

Likelihood per particle: the product over beams of
Z_HIT * N(z; r_hat, SIG_L = 0.2) + Z_RAND / R_MAX with Z_HIT = 0.9 and
Z_RAND = 0.1; particles inside an obstacle or outside the map get weight 0;
log-sum is used for numerical safety.  Low-variance (systematic) resampling
runs every step.  After each resampling the particle count is set by the
KLD-style rule over k occupied 0.5 m x 0.5 m bins,
n = (k-1)/(2*EPS) * (1 - 2/(9(k-1)) + sqrt(2/(9(k-1)))*Z_Q)^3,
clamped to [N_MIN, N_MAX], and N_MIN when k <= 1.  Recovery: w_avg is the mean
raw likelihood, w_slow += A_SLOW * (w_avg - w_slow) and
w_fast += A_FAST * (w_avg - w_fast), both starting at the first w_avg, and at
resampling each particle is replaced by a uniform random free pose with
probability max(0, 1 - w_fast / w_slow).  The estimate is the weighted mean
of the particles.

Arms: A_odom (dead reckoning from the given initial guess, integrating
odometry only), B_amcl (adaptive count N_MIN = 100, N_MAX = 600, recovery
on), C_few (fixed 30 particles, recovery off).  Pairs: B-A, C-B, C-A.

Regimes (25 steps each unless stated):
  distinctive_unknown : distinctive room, true start uniform over free space,
                        A's initial guess is the room centre (5, 3), B starts
                        with N_MAX uniform particles, C with 30 uniform
                        particles.
  known_short         : distinctive room, start known exactly (A's guess is
                        the truth; B starts with N_MAX particles and C with 30
                        particles, each at the truth plus N(0, 0.05)), 6 steps.
  kidnapped           : distinctive room, start known exactly as in
                        known_short; after step 10 the robot is moved to a
                        uniform random free pose without telling odometry.
  corridor_multimodal : corridor room, true start uniform, A's guess is
                        (6, 1).

Per (regime, seed) the metrics are err (mean Euclidean error of the estimate
over the last 5 steps, in metres) and success (1.0 when that mean error is
below 0.5 m, else 0.0); the mean particle count of B is printed as well.

Common random numbers: one random.Random(f"{regime}/{seed}") stream per
(regime, seed) draws, in this fixed order before any arm runs, the true
start, all motion direction candidates and all motion noise, all beam
noises, and the kidnap pose; the true trajectory and the measured ranges are
then precomputed from those draws and shared by every arm.  Filter-internal
randomness (initial particle spread, resampling offset, recovery draws)
uses a separate random.Random(f"{regime}/{seed}/filter") stream per arm, so B
and C use the same filter stream string.

Regimes and parameters were written before the first run.  Declared
expectations (not tuned; printed as they come):
  distinctive_unknown : B consistently lower err than A - keep; C as it comes
  known_short         : A and B may near-tie on err - keep
  kidnapped           : C (too few particles, no recovery) loses to B on err
                        and success - keep; A loses too
  corridor_multimodal : B may fail too (ambiguous along x) - keep as it
                        comes; C as it comes

Alternatives (declared before the run, same seeds, not adopted): kidnapped
with recovery off for B; distinctive_unknown with N_MAX = 300 for B;
kidnapped with C at 30 particles but recovery on.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# ---------------------------------------------------------------------------
# Declared toy parameters (every constant used below).
# ---------------------------------------------------------------------------
STEP_LEN = 0.3          # m, commanded step length
MAX_REDRAWS = 20        # direction redraws before the robot stays
MOT_SCALE_SD = 0.05     # per-axis multiplicative motion noise sd
MOT_ADD_SD = 0.02       # per-axis additive motion noise sd, m
SIG_Z = 0.1             # m, beam range noise sd
SIG_L = 0.2             # m, beam likelihood sd
Z_HIT = 0.9             # likelihood hit weight
Z_RAND = 0.1            # likelihood random weight
R_MAX = 8.0             # m, maximum beam range
EPS = 0.05              # KLD-style target error
Z_Q = 2.326             # KLD-style quantile
BIN_SIZE = 0.5          # m, KLD bin side
A_SLOW = 0.05           # slow recovery rate
A_FAST = 0.5            # fast recovery rate
N_MIN = 100             # minimum particle count (arm B)
N_MAX = 600             # maximum particle count (arm B)
N_C = 30                # fixed particle count (arm C)
N_STEPS = 25            # steps per regime
N_STEPS_SHORT = 6       # steps in the known_short regime
KIDNAP_AFTER = 10       # step after which the robot is moved in the kidnap regime
INIT_SIGMA = 0.05       # m, sd of the initial particle spread around the truth
ERR_TOL = 0.5           # m, success threshold on the mean tail error
TAIL_STEPS = 5          # steps averaged for the error metric
SQRT_2PI = math.sqrt(2.0 * math.pi)
NEG_INF = float("-inf")

ROOMS = {
    "distinctive": ((0.0, 0.0, 10.0, 6.0),
                    ((1.5, 1.0, 2.5, 2.0),
                     (6.0, 3.5, 7.5, 5.0),
                     (4.0, 0.0, 4.5, 2.5))),
    "corridor": ((0.0, 0.0, 12.0, 2.0), ()),
}

REGIMES = ("distinctive_unknown", "known_short", "kidnapped",
           "corridor_multimodal")
REGIME_ROOM = {"distinctive_unknown": "distinctive",
               "known_short": "distinctive",
               "kidnapped": "distinctive",
               "corridor_multimodal": "corridor"}
REGIME_STEPS = {"distinctive_unknown": N_STEPS,
                "known_short": N_STEPS_SHORT,
                "kidnapped": N_STEPS,
                "corridor_multimodal": N_STEPS}
REGIME_GUESS = {"distinctive_unknown": (5.0, 3.0),
                "known_short": None,      # the truth
                "kidnapped": None,        # the truth
                "corridor_multimodal": (6.0, 1.0)}
NEAR_TRUTH_START = ("known_short", "kidnapped")

ARMS = ("A_odom", "B_amcl", "C_few")
METRICS = ("err", "success")
PAIRS = (("B_amcl", "A_odom"), ("C_few", "B_amcl"), ("C_few", "A_odom"))
DECLARED = {
    "distinctive_unknown": "B consistently lower err than A - keep; C as it comes",
    "known_short": "A and B may near-tie on err - keep",
    "kidnapped": "C (too few particles, no recovery) loses to B on err and "
                 "success - keep; A loses too",
    "corridor_multimodal": "B may fail too (ambiguous along x) - keep as it "
                           "comes; C as it comes",
}


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0  # identical values: no floating residue in mean or sd
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    """Half-up rounding on the shortest decimal repr; tiny non-zero values in scientific form."""
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
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


# ---------------------------------------------------------------------------
# Map geometry: exact axis-aligned ray tests against the rectangle list.
# ---------------------------------------------------------------------------
def is_free(room, boxes, x, y):
    """True when the pose is inside the room and outside every interior box."""
    x0, y0, x1, y1 = room
    if x < x0 or x > x1 or y < y0 or y > y1:
        return False
    for bx0, by0, bx1, by1 in boxes:
        if bx0 < x < bx1 and by0 < y < by1:
            return False
    return True


def beam_ranges(room, boxes, x, y):
    """Ranges to the nearest edge along each axis, in the order +x, -x, +y, -y."""
    x0, y0, x1, y1 = room
    rx_p = x1 - x
    rx_m = x - x0
    ry_p = y1 - y
    ry_m = y - y0
    for bx0, by0, bx1, by1 in boxes:
        if by0 <= y <= by1:
            if bx0 > x:
                rx_p = min(rx_p, bx0 - x)
            elif bx1 > x:
                rx_p = min(rx_p, bx1 - x)
            if bx1 < x:
                rx_m = min(rx_m, x - bx1)
            elif bx0 < x:
                rx_m = min(rx_m, x - bx0)
        if bx0 <= x <= bx1:
            if by0 > y:
                ry_p = min(ry_p, by0 - y)
            elif by1 > y:
                ry_p = min(ry_p, by1 - y)
            if by1 < y:
                ry_m = min(ry_m, y - by1)
            elif by0 < y:
                ry_m = min(ry_m, y - by0)
    if rx_p > R_MAX:
        rx_p = R_MAX
    if rx_m > R_MAX:
        rx_m = R_MAX
    if ry_p > R_MAX:
        ry_p = R_MAX
    if ry_m > R_MAX:
        ry_m = R_MAX
    return rx_p, rx_m, ry_p, ry_m


def sample_free(room, boxes, rng, tries=400):
    """Uniform draw over the free space of the map."""
    x0, y0, x1, y1 = room
    for _ in range(tries):
        x = rng.uniform(x0, x1)
        y = rng.uniform(y0, y1)
        if is_free(room, boxes, x, y):
            return x, y
    return (x0 + x1) * 0.5, (y0 + y1) * 0.5


def kld_count(k):
    """KLD-style particle count for k occupied bins (clamped by the caller)."""
    k1 = k - 1
    term = 1.0 - 2.0 / (9.0 * k1) + math.sqrt(2.0 / (9.0 * k1)) * Z_Q
    return (k1 / (2.0 * EPS)) * term * term * term


def occupied_bins(room, particles):
    """Number of occupied 0.5 m x 0.5 m bins over the map extent."""
    x0, y0 = room[0], room[1]
    cells = set()
    for px, py in particles:
        ix = int((px - x0) / BIN_SIZE)
        iy = int((py - y0) / BIN_SIZE)
        if ix < 0:
            ix = 0
        if iy < 0:
            iy = 0
        cells.add((ix, iy))
    return len(cells)


# ---------------------------------------------------------------------------
# Shared draws: the true trajectory and the measured ranges.
# ---------------------------------------------------------------------------
def precompute(regime, seed):
    """Shared random draws for one (regime, seed): trajectory, commands, ranges."""
    rng = random.Random(f"{regime}/{seed}")
    room, boxes = ROOMS[REGIME_ROOM[regime]]
    n_steps = REGIME_STEPS[regime]
    start = sample_free(room, boxes, rng)
    dirs = []
    mnoise = []
    for _ in range(n_steps):
        dirs.append([rng.uniform(0.0, 2.0 * math.pi)
                     for _ in range(MAX_REDRAWS + 1)])
        mnoise.append((rng.gauss(0.0, MOT_SCALE_SD),
                       rng.gauss(0.0, MOT_SCALE_SD),
                       rng.gauss(0.0, MOT_ADD_SD),
                       rng.gauss(0.0, MOT_ADD_SD)))
    bnoise = [[rng.gauss(0.0, SIG_Z) for _ in range(4)] for _ in range(n_steps)]
    kidnap = sample_free(room, boxes, rng) if regime == "kidnapped" else None

    traj = []
    cmds = []
    meas = []
    px, py = start
    for step in range(n_steps):
        dx = 0.0
        dy = 0.0
        for k in range(MAX_REDRAWS + 1):
            ang = dirs[step][k]
            cdx = STEP_LEN * math.cos(ang)
            cdy = STEP_LEN * math.sin(ang)
            if is_free(room, boxes, px + cdx, py + cdy):
                dx = cdx
                dy = cdy
                break
        gsx, gsy, gax, gay = mnoise[step]
        px = px + dx * (1.0 + gsx) + gax
        py = py + dy * (1.0 + gsy) + gay
        r = beam_ranges(room, boxes, px, py)
        zn = bnoise[step]
        z = []
        for i in range(4):
            v = r[i] + zn[i]
            if v < 0.0:
                v = 0.0
            if v > R_MAX:
                v = R_MAX
            z.append(v)
        traj.append((px, py))
        cmds.append((dx, dy))
        meas.append(z)
        if regime == "kidnapped" and step == KIDNAP_AFTER - 1:
            px, py = kidnap
    return room, boxes, start, traj, cmds, meas


# ---------------------------------------------------------------------------
# Arms.
# ---------------------------------------------------------------------------
def run_arm_a(guess, traj, cmds):
    """Dead reckoning: integrate the odometry commands from the given guess."""
    x = guess[0]
    y = guess[1]
    errs = []
    for i in range(len(cmds)):
        x += cmds[i][0]
        y += cmds[i][1]
        errs.append(math.hypot(x - traj[i][0], y - traj[i][1]))
    return errs


def run_filter(room, boxes, traj, cmds, meas, rng, particles, n_min, n_max,
               adaptive, recovery):
    """Particle filter: motion update, weighted likelihood, resampling,
    optional random-pose recovery and optional KLD-style count adaptation."""
    exp = math.exp
    log = math.log
    hypot = math.hypot
    n = len(particles)
    w_slow = 0.0
    w_fast = 0.0
    errs = []
    counts = []
    for step in range(len(cmds)):
        dx = cmds[step][0]
        dy = cmds[step][1]
        xs = [p[0] + dx for p in particles]
        ys = [p[1] + dy for p in particles]
        z = meas[step]
        logw = []
        for i in range(n):
            px = xs[i]
            py = ys[i]
            if not is_free(room, boxes, px, py):
                logw.append(NEG_INF)
                continue
            r = beam_ranges(room, boxes, px, py)
            lw = 0.0
            for b in range(4):
                d = (z[b] - r[b]) / SIG_L
                p = Z_HIT * exp(-0.5 * d * d) / (SIG_L * SQRT_2PI) + Z_RAND / R_MAX
                lw += log(p)
            logw.append(lw)
        mx = max(logw)
        if mx == NEG_INF:
            w = [1.0 / n] * n
            w_avg = 0.0
        else:
            ws = [exp(v - mx) for v in logw]
            s = sum(ws)
            w = [v / s for v in ws]
            w_avg = (s / n) * exp(mx)
        ex = 0.0
        ey = 0.0
        for i in range(n):
            ex += w[i] * xs[i]
            ey += w[i] * ys[i]
        errs.append(hypot(ex - traj[step][0], ey - traj[step][1]))
        if step == 0:
            w_slow = w_avg
            w_fast = w_avg
        else:
            w_slow += A_SLOW * (w_avg - w_slow)
            w_fast += A_FAST * (w_avg - w_fast)
        cum = []
        acc = 0.0
        for i in range(n):
            acc += w[i]
            cum.append(acc)
        u0 = rng.random() / n
        idx = 0
        newx = []
        newy = []
        for j in range(n):
            u = u0 + j / n
            while idx < n - 1 and cum[idx] < u:
                idx += 1
            newx.append(xs[idx])
            newy.append(ys[idx])
        if recovery:
            if w_slow > 0.0:
                p_rec = 1.0 - w_fast / w_slow
                if p_rec < 0.0:
                    p_rec = 0.0
            else:
                p_rec = 1.0
            if p_rec > 0.0:
                for j in range(n):
                    if rng.random() < p_rec:
                        ux, uy = sample_free(room, boxes, rng)
                        newx[j] = ux
                        newy[j] = uy
        particles = list(zip(newx, newy))
        if adaptive:
            k = occupied_bins(room, particles)
            if k <= 1:
                target = n_min
            else:
                target = int(round(kld_count(k)))
                if target < n_min:
                    target = n_min
                if target > n_max:
                    target = n_max
            if target > n:
                for _ in range(target - n):
                    ux, uy = sample_free(room, boxes, rng)
                    particles.append((ux, uy))
            elif target < n:
                keep = rng.sample(range(n), target)
                particles = [particles[i] for i in keep]
            n = len(particles)
        counts.append(n)
    return errs, counts


def initial_particles(room, boxes, start, count, rng, near_truth):
    if near_truth:
        return [(start[0] + rng.gauss(0.0, INIT_SIGMA),
                 start[1] + rng.gauss(0.0, INIT_SIGMA)) for _ in range(count)]
    return [sample_free(room, boxes, rng) for _ in range(count)]


def run_regime(regime, seed, b_recovery=True, b_n_max=N_MAX, c_recovery=False):
    """One (regime, seed): shared trajectory, all three arms scored on it."""
    room, boxes, start, traj, cmds, meas = precompute(regime, seed)
    near = regime in NEAR_TRUTH_START
    guess = start if near else REGIME_GUESS[regime]
    errs_a = run_arm_a(guess, traj, cmds)
    rng_b = random.Random(f"{regime}/{seed}/filter")
    init_b = initial_particles(room, boxes, start, b_n_max, rng_b, near)
    errs_b, counts_b = run_filter(room, boxes, traj, cmds, meas, rng_b, init_b,
                                  N_MIN, b_n_max, True, b_recovery)
    rng_c = random.Random(f"{regime}/{seed}/filter")
    init_c = initial_particles(room, boxes, start, N_C, rng_c, near)
    errs_c, counts_c = run_filter(room, boxes, traj, cmds, meas, rng_c, init_c,
                                  N_C, N_C, False, c_recovery)
    return {"A_odom": errs_a, "B_amcl": errs_b, "C_few": errs_c}, counts_b


def arm_metrics(errs):
    tail = errs[-TAIL_STEPS:]
    e = sum(tail) / len(tail)
    return e, (1.0 if e < ERR_TOL else 0.0)


def collect(regime, **kw):
    """Metrics for every seed of one regime."""
    rows = []
    for seed in SEEDS:
        errs, counts = run_regime(regime, seed, **kw)
        row = {}
        for arm in ARMS:
            e, ok = arm_metrics(errs[arm])
            row[arm] = {"err": e, "success": ok}
        row["npart"] = sum(counts) / len(counts)
        rows.append(row)
    return rows


def col(rows, arm, key):
    return [r[arm][key] for r in rows]


def report(regime, rows):
    print(f"{regime}:")
    print(f"  declared: {DECLARED[regime]}")
    for arm in ARMS:
        print(f"  {arm} " + " ".join(
            f"{key} {fmt_pair(*mean_sd(col(rows, arm, key)))}" for key in METRICS))
    print(f"  B_amcl n_particles {fmt_pair(*mean_sd([r['npart'] for r in rows]))}")
    for a, b in PAIRS:
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: "
                  f"{verdict(col(rows, a, key), col(rows, b, key))}")


def main():
    print("AMCL-style particle filter localization toy against a known 2-D map "
          "(synthetic; not Nav2, not a bag playback, not a real robot run)")
    print("every constant is a declared toy parameter; ROS amcl defaults "
          "(min_particles 100, max_particles 5000, kld_err 0.01, "
          "recovery_alpha_slow 0.001, recovery_alpha_fast 0.1) are 以原文为准 "
          "and are not what this toy uses")
    print(f"seeds={len(SEEDS)} n_min={N_MIN} n_max={N_MAX} n_c={N_C} "
          f"eps={num(EPS)} z_q={num(Z_Q)} a_slow={num(A_SLOW)} "
          f"a_fast={num(A_FAST)} sig_z={num(SIG_Z)} sig_l={num(SIG_L)} "
          f"r_max={num(R_MAX)} step_len={num(STEP_LEN)} "
          f"err_tol={num(ERR_TOL)} (declared)")
    print("Regimes and parameters were written before the first run")
    for k in (2, 10, 50):
        raw = kld_count(k)
        clamped = min(max(raw, N_MIN), N_MAX)
        print(f"hand_calc kld n at k={k}: raw {num(raw)}, clamped to "
              f"[{N_MIN}, {N_MAX}] = {num(clamped)}")
    print(f"hand_calc beam likelihood floor Z_RAND/R_MAX = "
          f"{num(Z_RAND / R_MAX)}")
    drift = math.sqrt(N_STEPS) * math.sqrt((STEP_LEN * MOT_SCALE_SD) ** 2
                                           + MOT_ADD_SD ** 2)
    print(f"hand_calc dead-reckoning drift sd after {N_STEPS} steps per axis "
          f"= sqrt({N_STEPS})*sqrt((0.3*0.05)^2 + 0.02^2) = {num(drift)} m")
    base = {}
    for regime in REGIMES:
        rows = collect(regime)
        base[regime] = rows
        report(regime, rows)
    print("alternative parameters (declared before the run, same seeds, not "
          "adopted):")
    alt = collect("kidnapped", b_recovery=False)
    print(f"  kidnapped with recovery off for B: paired X-B err: "
          f"{verdict(col(alt, 'B_amcl', 'err'), col(base['kidnapped'], 'B_amcl', 'err'))}")
    alt = collect("distinctive_unknown", b_n_max=300)
    print(f"  distinctive_unknown with N_MAX=300 for B: paired X-B err: "
          f"{verdict(col(alt, 'B_amcl', 'err'), col(base['distinctive_unknown'], 'B_amcl', 'err'))}")
    alt = collect("kidnapped", c_recovery=True)
    print(f"  kidnapped with C at 30 particles but recovery on: paired X-C err: "
          f"{verdict(col(alt, 'C_few', 'err'), col(base['kidnapped'], 'C_few', 'err'))}")
    print("No winner beyond the declared toy parameters and the printed "
          "verdicts: a synthetic map, a declared sensor model and seed "
          "scatter, so the numbers show magnitudes only")
    print("Real robot / Nav2 AMCL / live ROS wiki: 本页未运行; Wikipedia and "
          "archived ROS wiki text 以原文为准")


if __name__ == "__main__":
    main()
