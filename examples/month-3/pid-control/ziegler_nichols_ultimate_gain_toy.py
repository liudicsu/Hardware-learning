#!/usr/bin/env python3
"""Ziegler-Nichols ultimate-gain PID tuning toy on a first-order-plus-dead-time
plant: a deterministic discrete linear stand-in, not a physical joint; real
plant / autotune: 本页未运行.

Model: G(s) = K exp(-L s) / (TAU s + 1) with K = 1.0 and TAU = 1.0 s.  Exact
zero-order-hold discretisation with DT = 0.005 s gives
x[k+1] = A*x[k] + K*(1-A)*(u[k-ND] + d[k]), A = exp(-DT/TAU), and ND samples
of pure delay.  The stable step criterion is 0 < A < 1 for any DT > 0.
The controller is a parallel ISA PID, u = Kp*(e + I/Ti + Td*D), with a
forward-Euler integral of e and a derivative on the filtered measurement only
(no setpoint kick), filter time Tf = Td/10; the P-only arm has no Ti or Td.

Common random numbers: one random.Random(f"{regime}/{seed}") stream per
(regime, seed) draws the disturbance amplitude and then one measurement noise
per sample in a fixed order before any arm is evaluated; all arms share them.

Regimes and parameters were written before the first run.  Declared
expectations are printed as they come, without tuning.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

K = 1.0
TAU = 1.0
DT = 0.005
A = math.exp(-DT / TAU)
T_END = 20.0
T_ID = 60.0
T_DIST = 10.0

METRICS = ("overshoot", "iae", "settle")

REGIMES = {
    "lag": {
        "L": 0.1,
        "SIG": 0.002,
        "declared": "A and B may near-tie on iae - keep; C may lose on iae "
                    "(P-only offset) - keep",
    },
    "delay_quiet": {
        "L": 0.5,
        "SIG": 0.0,
        "declared": "A consistently above B on overshoot (classic ZN "
                    "overshoots) - keep",
    },
    "delay_noisy": {
        "L": 0.5,
        "SIG": 0.02,
        "declared": "A consistently above B on overshoot and iae (classic ZN "
                    "loses) - keep",
    },
}

ARMS = ("A_classic", "B_no_overshoot", "C_p_only")
PAIRS = (("B_no_overshoot", "A_classic"), ("C_p_only", "B_no_overshoot"),
         ("C_p_only", "A_classic"))


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


def analytic_ku_tu(L):
    lo, hi = 0.0, 1.0e4
    for _ in range(120):
        mid = 0.5 * (lo + hi)
        if math.atan(mid * TAU) + mid * L < math.pi:
            lo = mid
        else:
            hi = mid
    w = 0.5 * (lo + hi)
    ku = math.sqrt(1.0 + (w * TAU) ** 2) / K
    tu = 2.0 * math.pi / w
    return w, ku, tu


def simulate(nd, kp, ti=None, td=None, tf_div=10.0, r=1.0, d_amp=0.0,
             noise=None, t_end=T_END, t_dist=T_DIST):
    n = int(t_end / DT + 0.5) + 1
    x = 0.0
    integ = 0.0
    yf = 0.0
    u_hist = []
    xs = []
    unstable = False
    tf = None if td is None else td / tf_div
    for k in range(n):
        t = k * DT
        y_meas = x if noise is None else x + noise[k]
        e = r - y_meas
        if td is None:
            d_term = 0.0
        elif k == 0:
            yf = y_meas
            d_term = 0.0
        else:
            alpha = math.exp(-DT / tf)
            yf_new = alpha * yf + (1.0 - alpha) * y_meas
            d_term = -(yf_new - yf) / DT
            yf = yf_new
        if ti is None:
            u = kp * e
        else:
            u = kp * (e + integ / ti + td * d_term)
        ud = u_hist[k - nd] if k >= nd else 0.0
        dd = d_amp if t >= t_dist else 0.0
        xs.append(x)
        u_hist.append(u)
        if ti is not None:
            integ += DT * e
        x_next = A * x + K * (1.0 - A) * (ud + dd)
        if not math.isfinite(x_next) or abs(x_next) > 1.0e9:
            unstable = True
            x = 1.0e9 if x_next >= 0.0 else -1.0e9
            break
        x = x_next
    if len(xs) < n:
        xs.extend([x] * (n - len(xs)))
    return {"y_true": xs, "unstable": unstable}


def is_growing(ys, unstable):
    if unstable:
        return True
    n = len(ys)
    start = int((T_ID - 30.0) / DT + 0.5)
    if start >= n - 1:
        return False
    mu = sum(ys[start:]) / len(ys[start:])
    peaks = []
    for k in range(max(1, start), n - 1):
        if ys[k] > ys[k - 1] and ys[k] >= ys[k + 1] and ys[k] > mu:
            peaks.append(k)
    if len(peaks) < 2:
        return False
    last_amp = ys[peaks[-1]] - mu
    prev_amp = ys[peaks[-2]] - mu
    return last_amp > prev_amp


def peak_spacing_tu(ys):
    n = len(ys)
    start = int((T_ID - 30.0) / DT + 0.5)
    mu = sum(ys[start:]) / len(ys[start:])
    peaks = [k for k in range(max(1, start), n - 1)
             if ys[k] > ys[k - 1] and ys[k] >= ys[k + 1] and ys[k] > mu]
    if len(peaks) < 2:
        start2 = int(5.0 / DT + 0.5)
        peaks = [k for k in range(start2, n - 1)
                 if ys[k] > ys[k - 1] and ys[k] >= ys[k + 1] and ys[k] > mu]
    if len(peaks) < 2:
        return None
    spacings = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
    return sum(spacings) / len(spacings) * DT


def identify(nd, L):
    lo, hi = 0.1, 100.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        res = simulate(nd, mid, t_end=T_ID)
        if is_growing(res["y_true"], res["unstable"]):
            hi = mid
        else:
            lo = mid
    ku = 0.5 * (lo + hi)
    res = simulate(nd, ku, t_end=T_ID)
    tu = peak_spacing_tu(res["y_true"])
    if tu is None:
        tu = analytic_ku_tu(L)[2]
    return ku, tu


def arm_gains(ku, tu):
    return {
        "A_classic": (0.6 * ku, 0.5 * tu, 0.125 * tu),
        "B_no_overshoot": (0.2 * ku, 0.5 * tu, tu / 3.0),
        "C_p_only": (0.5 * ku, None, None),
    }


def metrics_from(xs):
    i10 = int(T_DIST / DT + 0.5)
    overshoot = max(0.0, max(xs[:i10 + 1]) - 1.0) * 100.0
    iae = DT * sum(abs(1.0 - y) for y in xs)
    last_bad = 0.0
    bad = False
    for k in range(i10 + 1):
        if abs(1.0 - xs[k]) > 0.05:
            last_bad = k * DT
            bad = True
    settle = last_bad if bad else 0.0
    stable = all(abs(y) < 10.0 for y in xs)
    return {"overshoot": overshoot, "iae": iae, "settle": settle,
            "stable": stable}


def build_crn():
    crn = {}
    n = int(T_END / DT + 0.5) + 1
    for regime, cfg in REGIMES.items():
        nd = int(cfg["L"] / DT + 0.5)
        for seed in SEEDS:
            rng = random.Random(f"{regime}/{seed}")
            d_amp = rng.uniform(0.2, 0.4)
            noise = [rng.gauss(0.0, cfg["SIG"]) for _ in range(n)]
            crn[(regime, seed)] = (d_amp, noise, nd)
    return crn


def run_gains(crn, regime, gains, tf_div=10.0):
    out = {arm: {m: [] for m in METRICS} for arm in gains}
    events = []
    for seed in SEEDS:
        d_amp, noise, nd = crn[(regime, seed)]
        for arm in gains:
            kp, ti, td = gains[arm]
            res = simulate(nd, kp, ti, td, tf_div=tf_div, d_amp=d_amp,
                           noise=noise, t_end=T_END)
            met = metrics_from(res["y_true"])
            for m in METRICS:
                out[arm][m].append(met[m])
            if not met["stable"]:
                events.append((seed, arm))
    return out, events


def report(regime, ku, tu, gains, res, events):
    print(f"{regime}:")
    print(f"  identified Ku={num(ku)} Tu={num(tu)} (P-only ultimate test, "
          f"noise-free, {num(T_ID)} s)")
    print(f"  declared: {REGIMES[regime]['declared']}")
    for arm in ARMS:
        kp, ti, td = gains[arm]
        if ti is None:
            gtext = f"Kp={num(kp)} (P-only, Ti and Td absent)"
        else:
            gtext = f"Kp={num(kp)} Ti={num(ti)} Td={num(td)}"
        print(f"  {arm} gains: {gtext}")
    for arm in ARMS:
        body = " ".join(
            f"{m} {fmt_pair(*mean_sd(res[arm][m]))}" for m in METRICS)
        print(f"  {arm} {body}")
    for a, b in PAIRS:
        for m in METRICS:
            print(f"  paired {a[0]}-{b[0]} {m}: "
                  f"{verdict(res[a][m], res[b][m])}")
    for seed, arm in events:
        print(f"  unstable: {regime} seed {seed} {arm} |y_true| >= 10")


def main():
    print("Ziegler-Nichols ultimate-gain PID tuning toy on a "
          "first-order-plus-dead-time plant")
    print("deterministic discrete linear stand-in, not a physical joint; real "
          "plant / autotune: 本页未运行")
    print(f"model G(s) = K exp(-L s)/(TAU s + 1), K={num(K)} TAU={num(TAU)} s, "
          f"DT={num(DT)} s, A=exp(-DT/TAU)={num(A)}, "
          f"ND=int(L/DT+0.5) samples of pure delay")
    print("stable-step criterion: 0 < A < 1 for any DT > 0")
    print("controller u = Kp*(e + I/Ti + Td*D); I forward-Euler integral of e; "
          "D = -dy_f/dt on the measurement filter Tf = Td/10; P-only has no "
          "Ti or Td")
    print(f"seeds={len(SEEDS)} T_END={num(T_END)} s T_ID={num(T_ID)} s "
          f"setpoint step r=1 at t=0; load step at t={num(T_DIST)} s with "
          f"d uniform(0.2, 0.4)")
    print("Regimes and parameters were written before the first run")
    for L in (0.1, 0.5):
        w, kua, tua = analytic_ku_tu(L)
        print(f"hand_calc L={num(L)} analytic Ku={num(kua)} Tu={num(tua)} "
              f"(w={num(w)} solves atan(w*TAU)+w*L=pi)")
        print(f"hand_calc L={num(L)} classic PID from analytic Ku,Tu: "
              f"Kp={num(0.6 * kua)} Ti={num(0.5 * tua)} "
              f"Td={num(0.125 * tua)}")
    print("hand_calc note: the discrete delay/ZOH adds phase so the identified "
          "Ku can be lower than the analytic Ku")
    crn = build_crn()
    results = {}
    identified = {}
    gains_by_regime = {}
    for regime, cfg in REGIMES.items():
        nd = int(cfg["L"] / DT + 0.5)
        ku, tu = identify(nd, cfg["L"])
        identified[regime] = (ku, tu)
        gains = arm_gains(ku, tu)
        gains_by_regime[regime] = gains
        res, events = run_gains(crn, regime, gains)
        results[regime] = res
        report(regime, ku, tu, gains, res, events)
    print("alternative parameters (declared before the run, same seeds, not "
          "adopted):")
    ku_n, tu_n = identified["delay_noisy"]
    xg = (ku_n / 3.0, 0.5 * tu_n, tu_n / 3.0)
    resx, evx = run_gains(crn, "delay_noisy", {"X": xg})
    print(f"  delay_noisy some-overshoot row (Kp=Ku/3, Ti=0.5 Tu, Td=Tu/3) "
          f"as X: paired X-A overshoot: "
          f"{verdict(resx['X']['overshoot'], results['delay_noisy']['A_classic']['overshoot'])}")
    print(f"  delay_noisy some-overshoot row as X: paired X-A iae: "
          f"{verdict(resx['X']['iae'], results['delay_noisy']['A_classic']['iae'])}")
    cx = gains_by_regime["delay_noisy"]["A_classic"]
    resx2, evx2 = run_gains(crn, "delay_noisy", {"X": cx}, tf_div=5.0)
    print(f"  delay_noisy classic with Tf=Td/5 as X: paired X-A iae: "
          f"{verdict(resx2['X']['iae'], results['delay_noisy']['A_classic']['iae'])}")
    w, kua, tua = analytic_ku_tu(0.1)
    xg3 = (0.6 * kua, 0.5 * tua, 0.125 * tua)
    resx3, evx3 = run_gains(crn, "lag", {"X": xg3})
    print(f"  lag classic from analytic Ku,Tu as X: paired X-A iae: "
          f"{verdict(resx3['X']['iae'], results['lag']['A_classic']['iae'])}")
    print("No winner beyond the declared expectations: classic ZN trades "
          "overshoot for speed, the conservative row reduces overshoot at "
          "higher iae, and P-only keeps a load offset, with seed scatter")
    print("Real plant / autotune / Microstar or ASME figures: 本页未运行; "
          "Wikipedia table 以原文为准")


if __name__ == "__main__":
    main()
