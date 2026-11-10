#!/usr/bin/env python3
"""Seven-segment jerk-limited S-curve vs trapezoidal velocity profile on one shared 1-D move.

Synthetic, stdlib only.  Not MoveIt's velocity / acceleration *scaling factors* (those shrink
the limits; they do not add a jerk limit), not a Pilz LIN or OMPL redo, one axis only (a
per-joint decoupled profile).  Real arm or real controller: 本页未运行.  Wikipedia "Jerk
(physics)" statements (the seven segments, shortening rules) are 以原文为准; the plant below is
a stand-in.

Profiles (shared start 0, goal DIST, shared VMAX and AMAX):
  A_trap   trapezoid: acceleration jumps between 0 and +-AMAX (jerk unbounded at 4 corners)
  B_scurve seven segments with jerk limit JMAX: +j, 0, -j, cruise, -j, 0, +j
  C_slowj  the same seven segments with a too-small jerk limit JMAX_C
Short moves: if the full limits do not fit, the cruise is dropped and the peak speed is lowered
(found by bisection), which shortens the constant-acceleration segments first and then the jerk
segments, as the Wikipedia section describes.
Bounds checked on every profile: |v| <= VMAX, |a| <= AMAX, |j| <= jerk limit (B, C), and at the
end position DIST, v = 0, a = 0.
Plant (a stand-in for a flexible arm or belt axis): the tool y follows the command r through a
spring-damper,  y'' = -2 ZETA W (y' - r') - W^2 (y - r),  W = 2 pi f.
Integration: semi-implicit Euler at fixed step DT: v += DT * y''; y += DT * v.  Stable-step
criterion (damped oscillator, this scheme): DT < H_STAR = 2 (sqrt(1 + ZETA^2) - ZETA) / W.  The
largest W in any regime sets the limit; the run uses DT far below it.  Printed checks: spectral
radius and a free run at 0.98 x and 1.02 x H_STAR, and the whole table again at DT / 2.
Metrics per seed: residual = max |y - DIST| after the command stops (mm), profile time (s),
cycle time = profile time plus settle time (first time after which |y - DIST| stays within
SETTLE_TOL in the observation window; s).
Common random numbers: per (regime, seed) the plant frequency f is drawn once and used by all
three arms.
Regimes and expectations, written before the first run:
  flexible     DIST 0.30 m, f in U(3, 5) Hz   B consistent win over A on residual and cycle
                                              time; B loses to A on profile time
  rigid_short  DIST 0.02 m, f in U(30, 50) Hz B loses to A on profile time and cycle time
  C misses the time window T_WIN in both regimes and loses to B on cycle time.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
VMAX = 0.5      # m/s
AMAX = 2.0      # m/s^2
JMAX = 8.0      # m/s^3, B
JMAX_C = 2.0    # m/s^3, C (too small)
ZETA = 0.05
DT = 5e-4       # s
T_OBS = 6.0     # s observed after the command stops
SETTLE_TOL = 1e-4   # m (0.1 mm)
NUM_ZERO = 1e-9
ARMS = ("A_trap", "B_scurve", "C_slowj")
# name: (DIST m, f low Hz, f high Hz, T_WIN s); written before the first run
REGIMES = {
    "flexible": (0.30, 3.0, 5.0, 1.5),
    "rigid_short": (0.02, 30.0, 50.0, 0.5),
}
STREAM = {"flexible": 0, "rigid_short": 1}


def h_star(w, zeta=ZETA):
    return 2.0 * (math.sqrt(1.0 + zeta * zeta) - zeta) / w


def spectral_radius(w, h, zeta=ZETA):
    det = 1.0 - 2.0 * zeta * w * h
    tr = 2.0 - 2.0 * zeta * w * h - (w * h) ** 2
    disc = tr * tr - 4.0 * det
    if disc >= 0.0:
        r = math.sqrt(disc)
        return max(abs((tr + r) / 2.0), abs((tr - r) / 2.0))
    return math.sqrt(abs(det))


def free_run(w, h, steps=2000, zeta=ZETA):
    y, v = 1.0, 0.0
    for _ in range(steps):
        v += h * (-2.0 * zeta * w * v - w * w * y)
        y += h * v
    return abs(y) + abs(v) / w


def accel_time(v, amax, jmax):
    """Time to go from rest to speed v with limits amax, jmax (zero accel at both ends)."""
    if jmax is None:
        return v / amax
    if v >= amax * amax / jmax:
        return v / amax + amax / jmax
    return 2.0 * math.sqrt(v / jmax)


def peak_speed(dist, amax, jmax):
    """Largest v <= VMAX with accel + decel distance v * accel_time(v) <= dist (bisection)."""
    if VMAX * accel_time(VMAX, amax, jmax) <= dist:
        return VMAX
    lo, hi = 0.0, VMAX
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if mid * accel_time(mid, amax, jmax) <= dist:
            lo = mid
        else:
            hi = mid
    return lo


def segments(dist, jmax):
    """List of (duration, a0, jerk) pieces; jmax None means trapezoid."""
    v = peak_speed(dist, AMAX, jmax)
    if jmax is None:
        ta = v / AMAX
        acc = [(ta, AMAX, 0.0)]
        dec = [(ta, -AMAX, 0.0)]
    else:
        if v >= AMAX * AMAX / jmax:
            tj, ap = AMAX / jmax, AMAX
            tc = v / AMAX - tj
        else:
            tj = math.sqrt(v / jmax)
            ap, tc = jmax * tj, 0.0
        acc = [(tj, 0.0, jmax), (tc, ap, 0.0), (tj, ap, -jmax)]
        dec = [(tj, 0.0, -jmax), (tc, -ap, 0.0), (tj, -ap, jmax)]
    t_acc = sum(s[0] for s in acc)
    cruise = (dist - v * t_acc) / v
    return [s for s in acc + [(cruise, 0.0, 0.0)] + dec if s[0] > 0.0], v


class Profile:
    def __init__(self, dist, jmax):
        self.segs, self.vpeak = segments(dist, jmax)
        self.starts = []
        p = vel = 0.0
        t = 0.0
        for dur, a0, j in self.segs:
            self.starts.append((t, p, vel))
            p += vel * dur + a0 * dur * dur / 2.0 + j * dur ** 3 / 6.0
            vel += a0 * dur + j * dur * dur / 2.0
            t += dur
        self.total = t
        self.end = (p, vel)

    def at(self, t):
        """(position, velocity, acceleration, jerk) at time t."""
        if t >= self.total:
            return self.end[0], 0.0, 0.0, 0.0
        k = 0
        while k + 1 < len(self.segs) and self.starts[k + 1][0] <= t:
            k += 1
        t0, p0, v0 = self.starts[k]
        _, a0, j = self.segs[k]
        s = t - t0
        return (p0 + v0 * s + a0 * s * s / 2.0 + j * s ** 3 / 6.0, v0 + a0 * s + j * s * s / 2.0, a0 + j * s, j)


def bounds(prof, jlim, dist):
    vmax = amax = jmax = 0.0
    for dur, a0, j in prof.segs:
        amax = max(amax, abs(a0), abs(a0 + j * dur))
        jmax = max(jmax, abs(j))
    n = int(prof.total / 1e-4) + 1
    for i in range(n + 1):
        vmax = max(vmax, abs(prof.at(min(i * 1e-4, prof.total))[1]))
    ok = vmax <= VMAX * (1 + 1e-9) and amax <= AMAX * (1 + 1e-9) and (jlim is None or jmax <= jlim * (1 + 1e-9))
    end_ok = abs(prof.end[0] - dist) < 1e-12 and abs(prof.end[1]) < 1e-12
    a_end = prof.segs[-1][1] + prof.segs[-1][2] * prof.segs[-1][0]
    return vmax, amax, jmax, ok, end_ok, abs(a_end) < 1e-12


def simulate(prof, dist, w, dt):
    y = yv = 0.0
    n_move = int(math.ceil(prof.total / dt))
    n_all = n_move + int(round(T_OBS / dt))
    resid = 0.0
    last_out = None
    for i in range(1, n_all + 1):
        t = (i - 1) * dt
        r, rv, _, _ = prof.at(t)
        yv += dt * (-2.0 * ZETA * w * (yv - rv) - w * w * (y - r))
        y += dt * yv
        if i >= n_move:
            err = abs(y - dist)
            resid = max(resid, err)
            if err > SETTLE_TOL:
                last_out = i
    settled = last_out is None or last_out < n_all
    settle_t = (last_out if last_out is not None else n_move) * dt
    return resid * 1000.0, prof.total, max(settle_t, prof.total), settled


def plant_freqs(regime):
    _, lo, hi, _ = REGIMES[regime]
    return [random.Random(1000 * STREAM[regime] + s).uniform(lo, hi) for s in SEEDS]


def run(dt):
    table = {}
    for regime, (dist, _, _, _) in REGIMES.items():
        profs = {"A_trap": Profile(dist, None), "B_scurve": Profile(dist, JMAX), "C_slowj": Profile(dist, JMAX_C)}
        freqs = plant_freqs(regime)
        table[regime] = {arm: [simulate(profs[arm], dist, 2.0 * math.pi * f, dt) for f in freqs] for arm in ARMS}
        table[regime]["_profs"] = profs
        table[regime]["_freqs"] = freqs
    return table


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-5:
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


def verdict(xa, xb):
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


def main():
    print("Synthetic 1-D move: trapezoid vs 7-segment jerk-limited S-curve vs S-curve with too-small jerk limit; not MoveIt scaling, not Pilz/OMPL")
    print(f"VMAX={VMAX} m/s AMAX={AMAX} m/s^2 JMAX={JMAX} m/s^3 JMAX_C={JMAX_C} m/s^3 ZETA={ZETA} DT={DT} s T_OBS={T_OBS} s SETTLE_TOL={SETTLE_TOL * 1000:.1f} mm seeds={len(SEEDS)}")
    w_max = 2.0 * math.pi * max(hi for _, _, hi, _ in REGIMES.values())
    hs = h_star(w_max)
    print(f"stable step (semi-implicit Euler, damped oscillator): H_STAR = 2*(sqrt(1+ZETA^2)-ZETA)/W = {hs * 1000:.4f} ms at f = {w_max / 2 / math.pi:.0f} Hz; DT/H_STAR = {DT / hs:.4f}")
    for k in (0.98, 1.02):
        print(f"  {k:.2f} x H_STAR: spectral radius {spectral_radius(w_max, k * hs):.6f}; free run |y|+|v|/W after 2000 steps from 1: {free_run(w_max, k * hs):.4e} ({'decays' if free_run(w_max, k * hs) < 1.0 else 'grows'})")
    tab = run(DT)
    half = run(DT / 2.0)
    print("regime arm vpeak_m/s profile_s bound_ok end_p_v_ok a_reaches_0_continuously max|v| max|a| max|j|  (deterministic)")
    for regime in REGIMES:
        dist = REGIMES[regime][0]
        for arm, jl in (("A_trap", None), ("B_scurve", JMAX), ("C_slowj", JMAX_C)):
            prof = tab[regime]["_profs"][arm]
            vm, am, jm, ok, end_ok, a_zero = bounds(prof, jl, dist)
            jtxt = "unbounded (a steps by AMAX at 4 corners)" if jl is None else f"{jm:.4f}"
            print(f"  {regime} {arm} {prof.vpeak:.4f} {prof.total:.4f} {ok} {end_ok} {a_zero} {vm:.4f} {am:.4f} {jtxt}")
    print("regime arm residual_mm profile_s cycle_s settled  (mean+-sd over seeds)")
    for regime, (dist, lo, hi, twin) in REGIMES.items():
        freqs = tab[regime]["_freqs"]
        print(f"{regime} (DIST {dist} m; f in U({lo}, {hi}) Hz, drawn {', '.join(f'{f:.3f}' for f in freqs)}; T_WIN {twin} s)")
        res = tab[regime]
        for arm in ARMS:
            cols = ["{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in (0, 1, 2)]
            settled = sum(1 for r in res[arm] if r[3])
            within = "within T_WIN" if res[arm][0][1] <= twin else "misses T_WIN"
            print(f"  {arm} " + " ".join(cols) + f" {settled}/{len(SEEDS)} ({within})")
        for x, y in (("B_scurve", "A_trap"), ("C_slowj", "B_scurve")):
            for k, key in ((0, "residual"), (1, "profile"), (2, "cycle")):
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[k] for r in res[x]], [r[k] for r in res[y]])}")
    dres = max(abs(a[0] - b[0]) / max(abs(b[0]), 1e-12) for rg in REGIMES for arm in ARMS for a, b in zip(tab[rg][arm], half[rg][arm]))
    dcyc = max(abs(a[2] - b[2]) for rg in REGIMES for arm in ARMS for a, b in zip(tab[rg][arm], half[rg][arm]))
    print(f"half-step check (DT/2): max relative residual change {dres:.4f}; max cycle-time change {dcyc * 1000:.2f} ms")
    print("No winner declared: the jerk limit buys less ringing on a flexible axis and costs time on a stiff short move")
    print("Real arm / controller: 本页未运行; Wikipedia Jerk (physics) 以原文为准")


if __name__ == "__main__":
    main()
