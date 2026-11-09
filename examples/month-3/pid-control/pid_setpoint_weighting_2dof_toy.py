#!/usr/bin/env python3
"""Synthetic 1DOF PID vs 2DOF PID with setpoint weighting on one joint. Stdlib only.

Plant (linear, LTI, no actuator limit): G(s) = 1 / (s (TM s + 1)), TM = 0.05 s, a motor +
inertia measured at the motor angle; a load torque enters at the plant input.
Controller (ISA form, sampled at TS = 1 ms, trapezoid I, Tustin-filtered D, D filter TD/N):
  u = Kc [ (b r - y) + 1/TI * integral(r - y) + TD d/dt (c r - y) ]
The integral always acts on the true error r - y. Arms (gains fixed before any run):
  A_1dof     b = 1,   c = 1   (plain PID on the error: P and D both kick on a step)
  B_2dof     b = 0.5, c = 0   (setpoint weighting; D on the measurement)
  C_aggr     b = 1,   c = 0   (same gains, full P kick; only the D kick removed)
All three share Kc, TI, TD, N, so they share the loop transfer function, the closed-loop
poles and the margins (b and c only enter through r). Kc gives |L(j WC)| = 1 at WC = 20 rad/s.
Regime tiny_b changes the shared recipe on purpose (B uses b = 0.1 and every arm uses a slower
integral TI x 4): the pre-declared case where 2DOF may lose on rise time.
Common random numbers: per seed the setpoint steps, load-torque steps and sensor noise
(sd 0.5 mrad) are drawn once and fed to every arm. Integration: RK4 with H = TS/4 under
zero-order-hold control. RK4 is stable for a mode lambda when |R(H lambda)| <= 1,
R(z) = 1+z+z^2/2+z^3/6+z^4/24; the toy prints h_max and max |R| for the plant mode -1/TM
and asserts both; the tests check |R| at 0.98x and 1.02x of h_max.
Metrics: overshoot (% of each setpoint step, worst step), ISE_sp (1e-3 rad^2 s, windows after
setpoint steps), ISE_load (1e-3 rad^2 s, windows after load steps), rise (ms, 10-90 %, mean
over steps), du_rms. Pass rule: no divergence (|y| < 10 rad) and the same PM / GM as the earlier
pid toys print; 2DOF load ISE must stay within 5 % of A's (or be a tie / numerically zero).
Labels: tie = identical on every seed; numerically zero = |paired mean| and sd both < 1e-9
(effectively a tie, no sign count); |m| <= sd = near-tie; |m| > sd = consistent gap (small if
|m| < 20 % of the smaller arm mean, else clear), with a sign count.
Not a notch, not a lead-lag, not a Smith predictor. Real servo bench: 本页未运行.
Wikipedia PID controller (setpoint weighting): 以原文为准.
"""
import cmath
import math
import random

TS = 1e-3
SUB = 4
H = TS / SUB
TM = 0.05
WC = 20.0
TI0, TD, N = 5.0 / WC, 0.5 / WC, 8.0
T_END = 6.0
NOISE = 5e-4
DIVERGED = 10.0
LOAD_BAND = 0.05
NUM_ZERO = 1e-9
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_1dof", "B_2dof", "C_aggr")
# name: (setpoint steps?, load steps?, noise?, B's b, TI multiplier); pre-declared before the first run
REGIMES = {
    "setpoint_large": (True, False, False, 0.5, 1.0),
    "load_step": (False, True, False, 0.5, 1.0),
    "mixed_noise": (True, True, True, 0.5, 1.0),
    "tiny_b": (True, False, False, 0.1, 4.0),
}


def weights(arm, b_b):
    return {"A_1dof": (1.0, 1.0), "B_2dof": (b_b, 0.0), "C_aggr": (1.0, 0.0)}[arm]


def plant(w):
    s = 1j * w
    return 1.0 / (s * (TM * s + 1.0))


def shape(w, ti):
    s = 1j * w
    return 1.0 + 1.0 / (ti * s) + TD * s / (TD / N * s + 1.0)


def gain(ti):
    return 1.0 / abs(shape(WC, ti) * plant(WC))


def margins(ti):
    """Phase margin at |L| = 1 and gain margin (dB) at -180 deg, discrete Bode proxy (ZOH delay)."""
    k = gain(ti)
    pm, gm, prev = None, math.inf, None
    n = 20000
    for i in range(n + 1):
        w = 10 ** (-1 + i * (math.log10(math.pi / TS) + 1) / n)
        loop = k * shape(w, ti) * plant(w) * cmath.exp(-0.5j * w * TS)
        mag = abs(loop)
        ph = math.degrees(cmath.phase(loop))
        ph = ph - 360.0 if ph > 0 else ph
        if prev is not None:
            if pm is None and (prev[0] - 1.0) * (mag - 1.0) < 0:
                pm = 180.0 + ph
            if prev[1] > -180.0 >= ph and mag < 1.0:
                gm = min(gm, -20 * math.log10(mag))
        prev = (mag, ph)
    return pm, gm


class Controller:
    def __init__(self, k, ti, b, c):
        cc = 2.0 / TS
        tf = TD / N
        self.k, self.ti, self.b, self.c = k, ti, b, c
        self.i, self.e_prev, self.dprev, self.d = 0.0, 0.0, 0.0, 0.0
        self.db0, self.da1 = TD * cc / (tf * cc + 1.0), (1.0 - tf * cc) / (tf * cc + 1.0)

    def preset(self, r, y):
        """Start in steady state at r = y: the integral cancels the constant (b - 1) r term."""
        self.i = -(self.b * r - y)
        self.e_prev = r - y
        self.dprev = self.c * r - y

    def step(self, r, y):
        e = r - y
        self.i += TS / self.ti * (e + self.e_prev) / 2.0
        self.e_prev = e
        ed = self.c * r - y
        self.d = self.db0 * (ed - self.dprev) - self.da1 * self.d
        self.dprev = ed
        return self.k * ((self.b * r - y) + self.i + self.d)


def deriv(x, u):
    v, th = x
    return [(u - v) / TM, v]


def rk4(x, u, h=H):
    k1 = deriv(x, u)
    k2 = deriv([a + h / 2 * b for a, b in zip(x, k1)], u)
    k3 = deriv([a + h / 2 * b for a, b in zip(x, k2)], u)
    k4 = deriv([a + h * b for a, b in zip(x, k3)], u)
    return [a + h / 6 * (p + 2 * q + 2 * r + s) for a, p, q, r, s in zip(x, k1, k2, k3, k4)]


def rk4_amp(z):
    return abs(1 + z + z * z / 2 + z ** 3 / 6 + z ** 4 / 24)


def rk4_h_max(lam):
    lo, hi = 0.0, 10.0 / abs(lam)
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if rk4_amp(mid * lam) <= 1.0 else (lo, mid)
    return lo


def shared_draws(seed):
    """Common random numbers: one draw per seed, fed to every arm and regime."""
    rng = random.Random(seed)
    r0 = rng.uniform(-0.5, 0.5)
    steps = [(0.2 + 2.0 * i, rng.choice((-1.0, 1.0)) * rng.uniform(0.5, 1.5)) for i in range(3)]
    loads = [(1.2 + 2.0 * i, 0.3 * rng.choice((-1.0, 1.0)) * rng.uniform(0.3, 1.0)) for i in range(3)]
    noise = [rng.gauss(0.0, NOISE) for _ in range(round(T_END / TS))]
    return r0, steps, loads, noise


def simulate(arm, regime, draws, sub=SUB):
    use_sp, use_load, use_noise, b_b, ti_mult = REGIMES[regime]
    r0, steps, loads, noise = draws
    steps = steps if use_sp else []
    loads = loads if use_load else []
    ti = TI0 * ti_mult
    b, c = weights(arm, b_b)
    ctrl = Controller(gain(ti), ti, b, c)
    ctrl.preset(r0, r0)
    x = [0.0, r0]
    ise_sp = ise_ld = du2 = 0.0
    u_prev = 0.0
    over = [0.0] * len(steps)
    t10 = [None] * len(steps)
    t90 = [None] * len(steps)
    for i, nz in enumerate(noise):
        t = i * TS
        r = r0 + sum(a for t0, a in steps if t >= t0)
        u = ctrl.step(r, x[1] + (nz if use_noise else 0.0))
        d = sum(a for t0, a in loads if t >= t0)
        for _ in range(sub):
            x = rk4(x, u + d, TS / sub)
        y = x[1]
        if abs(y) > DIVERGED:
            return None
        if any(t0 <= t < t0 + 1.0 for t0, _ in steps):
            ise_sp += (r - y) ** 2 * TS
        if any(t0 <= t < t0 + 0.8 for t0, _ in loads):
            ise_ld += (r - y) ** 2 * TS
        if i:
            du2 += (u - u_prev) ** 2
        u_prev = u
        for j, (t0, a) in enumerate(steps):
            if t0 <= t < t0 + 1.0:
                base = r - a
                frac = (y - base) / a
                over[j] = max(over[j], frac - 1.0)
                if t10[j] is None and frac >= 0.1:
                    t10[j] = t
                if t90[j] is None and frac >= 0.9:
                    t90[j] = t
    rise = [(b9 - a1) for a1, b9 in zip(t10, t90) if a1 is not None and b9 is not None]
    out = {"over": 100.0 * max(over) if over else 0.0, "ise_sp": 1e3 * ise_sp, "ise_load": 1e3 * ise_ld,
           "rise": 1e3 * sum(rise) / len(rise) if rise else 0.0, "du": math.sqrt(du2 / (len(noise) - 1))}
    if steps and len(rise) < len(steps):
        out["rise"] = 1e3  # a step that never reached 90 % inside 1 s counts as 1000 ms
    return out


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


KEYS = ("over", "ise_sp", "ise_load", "rise", "du")


def main():
    print("Synthetic 1DOF PID vs 2DOF setpoint weighting; shared steps / load torques / sensor noise; not a motor bench")
    lam = -1.0 / TM
    h_max = rk4_h_max(complex(lam))
    amp = rk4_amp(H * lam)
    assert H < h_max and amp < 1.0
    print(f"TS={TS} s RK4 H={H} s TM={TM} s WC={WC} rad/s TI={TI0} s TD={TD} s N={N:.0f} seeds={len(SEEDS)}")
    print(f"RK4 mode -1/TM: h_max={h_max * 1e3:.2f} ms > H, |R(H lambda)|={amp:.6f} < 1")
    for mult in sorted({v[4] for v in REGIMES.values()}):
        pm, gm = margins(TI0 * mult)
        print(f"TI x{mult:.0f}: Kc={gain(TI0 * mult):.4f} PM={pm:.1f} deg GM={'inf' if math.isinf(gm) else f'{gm:.2f}'} dB (shared by all arms: b, c do not enter the loop)")
    print("regime arm overshoot_% ISE_sp ISE_load rise_ms du_rms  (mean+-sd over seeds)")
    draws = [shared_draws(s) for s in SEEDS]
    for regime, (_, _, _, b_b, mult) in REGIMES.items():
        print(f"{regime} (B uses b={b_b}, c=0; TI x{mult:.0f})")
        res = {arm: [simulate(arm, regime, d) for d in draws] for arm in ARMS}
        if any(r is None for arm in ARMS for r in res[arm]):
            print(f"  diverged (|y| > {DIVERGED:.0f} rad); not compared")
            continue
        for arm in ARMS:
            print(f"  {arm} " + " ".join("{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in KEYS))
        for x, y in (("B_2dof", "A_1dof"), ("B_2dof", "C_aggr"), ("C_aggr", "A_1dof")):
            for k in KEYS:
                print(f"  paired {x[0]}-{y[0]} {k}: {verdict([r[k] for r in res[x]], [r[k] for r in res[y]])}")
        la, lb = mean_sd([r["ise_load"] for r in res["A_1dof"]])[0], mean_sd([r["ise_load"] for r in res["B_2dof"]])[0]
        if la > 0:
            rel = abs(lb - la) / la
            print(f"  load band: |ISE_load B - A| / A = {100 * rel:.4f} % -> {'within' if rel <= LOAD_BAND else 'outside'} 5 %")
        else:
            print("  load band: no load steps in this regime")
    print("setpoint_large: b < 1 and c = 0 remove the proportional and derivative kicks, so B overshoots less at the same loop")
    print("load_step: with r constant the weights only shift a constant the integral absorbs, so load rejection is unchanged")
    print("tiny_b: with b = 0.1 and a slow integral the setpoint is reached mostly through I, so rise time suffers")
    print("No winner declared; the weights trade setpoint overshoot against rise time and leave the loop untouched")
    print("Real servo / motor bench: 本页未运行; Wikipedia PID setpoint weighting 以原文为准")


if __name__ == "__main__":
    main()
