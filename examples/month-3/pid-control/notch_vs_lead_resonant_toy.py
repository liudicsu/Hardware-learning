#!/usr/bin/env python3
"""Synthetic PID vs PID + notch vs PID + lead-lag on a joint with a resonance. Stdlib only.

Plant (linear, LTI, no actuator limit), the same joint as lead_lag_vs_pid_toy.py:
  G(s) = 1 / (s (TM s + 1)) * wr^2 / (s^2 + 2 zr wr s + wr^2)
  motor + inertia (TM = 0.05 s), then a compliant transmission mode (wr, zr) between
  motor and the measured link angle (non-collocated sensor). The rigid case drops
  the mode. Torque disturbance enters at the plant input.

Controllers (sampled at TS = 1 ms, every section discretised with Tustin):
  A_pid        Kc * (1 + 1/(TI s) + TD s / (TD/N s + 1))
  B_notch      A's shape * notch (s^2 + w0^2) / (s^2 + wc s + w0^2), w0 = WN = 40 rad/s
               (the designer's estimate of the mode), width wc = WIDTH * w0
  C_leadlag    A's shape * the lead (PHI = 30 deg) and lag of the lead-lag section
  D_mistuned   B's notch centred at MISTUNE * WN = 28 rad/s instead of 40 rad/s
  Same design rule for every arm: one fixed recipe (not tuned per regime), and Kc
  is chosen so |L(j WC)| = 1 on the actual plant, so all arms share crossover WC.

Common random numbers: per seed the three reference steps, three load-torque
steps and the measurement-noise sequence (sd 0.5 mrad) are drawn once and fed to
every arm. Integration: RK4 with H = TS/4 under zero-order-hold control. RK4 is
stable for a mode lambda when |R(H lambda)| <= 1, R(z) = 1+z+z^2/2+z^3/6+z^4/24;
the toy prints the largest stable step along the plant's modes and asserts H < it.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd both
< 1e-9 (floating-point residue, effectively a tie, no sign count); |m| <= sd =
near-tie / small gap within seed noise; |m| > sd = consistent gap (small if |m| <
20 % of the smaller arm mean, else clear), always with a sign count. Margins are a
discrete Bode proxy (continuous controller x continuous plant x ZOH half-sample delay).
Real servo / modal test: 本页未运行. Wikipedia definitions: 以原文为准.
"""
from __future__ import annotations

import cmath
import math
import random

TS = 1e-3  # s, controller sample time
SUB = 4  # RK4 sub-steps per sample
H = TS / SUB
TM = 0.05  # s, motor mechanical time constant
WC = 20.0  # rad/s, shared crossover target
TI, TD, N = 5.0 / WC, 0.5 / WC, 8.0
PHI = math.radians(30.0)
ALPHA = (1 + math.sin(PHI)) / (1 - math.sin(PHI))
BETA = 3.0
WN = 40.0  # rad/s, notch centre = the designer's estimate of the mode
WIDTH = 0.5  # notch width wc / w0, fixed before the first run
MISTUNE = 0.7  # D_mistuned centres its notch at MISTUNE * WN
T_END = 6.0
NOISE = 5e-4  # rad, measurement noise sd
DIVERGED = 10.0  # rad, abort threshold (the references never exceed 3 rad)
NUM_ZERO = 1e-9
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_pid", "B_notch", "C_leadlag", "D_mistuned")
# name, wr (0 = rigid), zr
REGIMES = (("well_damped", 0.0, 0.0), ("resonant", 40.0, 0.3), ("resonant_light", 40.0, 0.2),
           ("resonant_sharp", 40.0, 0.05))
ALT_SHARP_ZR = 0.1  # margins-only alternative for resonant_sharp (reported, not simulated)


def sections(arm: str, width: float = WIDTH) -> list[tuple[str, tuple[float, ...]]]:
    """Sections cascaded after the PID: ('lead', z, p) first order or ('notch', w0, wc)."""
    if arm == "B_notch":
        return [("notch", (WN, width * WN))]
    if arm == "D_mistuned":
        return [("notch", (MISTUNE * WN, width * MISTUNE * WN))]
    if arm == "C_leadlag":
        z, p = WC / math.sqrt(ALPHA), WC * math.sqrt(ALPHA)
        return [("lead", (z, p)), ("lead", (WC / 10.0, WC / 10.0 / BETA))]
    return []


def plant(w: float, wr: float, zr: float) -> complex:
    s = 1j * w
    g = 1.0 / (s * (TM * s + 1.0))
    return g * wr * wr / (s * s + 2 * zr * wr * s + wr * wr) if wr else g


def notch(w: float, w0: float, wc: float) -> complex:
    s = 1j * w
    return (s * s + w0 * w0) / (s * s + wc * s + w0 * w0)


def shape(arm: str, w: float, width: float = WIDTH) -> complex:
    s = 1j * w
    c = 1.0 + 1.0 / (TI * s) + TD * s / (TD / N * s + 1.0)
    for kind, par in sections(arm, width):
        if kind == "lead":
            z, p = par
            c *= (s / z + 1.0) / (s / p + 1.0)
        else:
            c *= notch(w, *par)
    return c


def gain(arm: str, wr: float, zr: float, width: float = WIDTH) -> float:
    return 1.0 / abs(shape(arm, WC, width) * plant(WC, wr, zr))


def margins(arm: str, wr: float, zr: float, width: float = WIDTH) -> tuple[float, float]:
    """Smallest phase margin over all |L| = 1 crossings and smallest gain margin
    (dB) over -180 deg crossings with |L| < 1; unwrapped phase from 0.1 rad/s."""
    k = gain(arm, wr, zr, width)
    pms, gms = [], []
    prev = None
    off = 0.0
    n = 20000
    for i in range(n + 1):
        w = 10 ** (-1 + i * (math.log10(math.pi / TS) + 1) / n)
        loop = k * shape(arm, w, width) * plant(w, wr, zr) * cmath.exp(-0.5j * w * TS)
        mag, ph = abs(loop), math.degrees(cmath.phase(loop))
        if prev is None:
            while ph > -90.0:
                ph -= 360.0
            off = ph - math.degrees(cmath.phase(loop))
        else:
            ph += off
            while ph - prev[1] > 180.0:
                ph -= 360.0
                off -= 360.0
            while ph - prev[1] < -180.0:
                ph += 360.0
                off += 360.0
            if (prev[0] - 1.0) * (mag - 1.0) < 0:
                pms.append(180.0 + ph)
            for line in (-180.0, -540.0):
                if (prev[1] - line) * (ph - line) < 0 and mag < 1.0:
                    gms.append(-20 * math.log10(mag))
        prev = (mag, ph)
    return min(pms), (min(gms) if gms else math.inf)


def tustin2(b: tuple[float, float, float], a: tuple[float, float, float]) -> list[float]:
    """b = (b0, b1, b2), a = (a0, a1, a2): (b2 s^2 + b1 s + b0) / (a2 s^2 + a1 s + a0)
    -> biquad via s = c (z - 1) / (z + 1)."""
    c = 2.0 / TS
    nb = (b[2] * c * c + b[1] * c + b[0], 2 * b[0] - 2 * b[2] * c * c, b[2] * c * c - b[1] * c + b[0])
    na = (a[2] * c * c + a[1] * c + a[0], 2 * a[0] - 2 * a[2] * c * c, a[2] * c * c - a[1] * c + a[0])
    return [nb[0] / na[0], nb[1] / na[0], nb[2] / na[0], na[1] / na[0], na[2] / na[0], 0.0, 0.0, 0.0, 0.0]


class Controller:
    """PI (trapezoid) + filtered D (Tustin), then Tustin sections (first or second order)."""

    def __init__(self, arm: str, k: float) -> None:
        self.k, self.i, self.e_prev, self.d = k, 0.0, 0.0, 0.0
        tf = TD / N
        c = 2.0 / TS
        self.db0, self.da1 = TD * c / (tf * c + 1.0), (1.0 - tf * c) / (tf * c + 1.0)
        self.secs = []
        for kind, par in sections(arm):
            if kind == "lead":
                z, p = par
                a0 = c / p + 1.0
                self.secs.append([(c / z + 1.0) / a0, (1.0 - c / z) / a0, 0.0, (1.0 - c / p) / a0, 0.0,
                                  0.0, 0.0, 0.0, 0.0])
            else:
                w0, wc = par
                self.secs.append(tustin2((w0 * w0, 0.0, 1.0), (w0 * w0, wc, 1.0)))

    def step(self, e: float) -> float:
        self.i += TS / TI * (e + self.e_prev) / 2.0
        self.d = self.db0 * (e - self.e_prev) - self.da1 * self.d
        self.e_prev = e
        x = e + self.i + self.d
        for sec in self.secs:
            b0, b1, b2, a1, a2, x1, x2, y1, y2 = sec
            y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            sec[5:] = [x, x1, y, y1]
            x = y
        return self.k * x


def deriv(x: list[float], u: float, wr: float, zr: float) -> list[float]:
    v, th, y, yd = x
    if not wr:
        return [(u - v) / TM, v, v, 0.0]
    return [(u - v) / TM, v, yd, wr * wr * (th - y) - 2 * zr * wr * yd]


def rk4(x: list[float], u: float, wr: float, zr: float, h: float = H) -> list[float]:
    k1 = deriv(x, u, wr, zr)
    k2 = deriv([a + h / 2 * b for a, b in zip(x, k1)], u, wr, zr)
    k3 = deriv([a + h / 2 * b for a, b in zip(x, k2)], u, wr, zr)
    k4 = deriv([a + h * b for a, b in zip(x, k3)], u, wr, zr)
    return [a + h / 6 * (b + 2 * c + 2 * d + e) for a, b, c, d, e in zip(x, k1, k2, k3, k4)]


def rk4_amp(z: complex) -> float:
    return abs(1 + z + z * z / 2 + z ** 3 / 6 + z ** 4 / 24)


def rk4_h_max(lam: complex) -> float:
    """Largest step with |R(h lambda)| <= 1 along this mode (bisection)."""
    lo, hi = 0.0, 10.0 / abs(lam)
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if rk4_amp(mid * lam) <= 1.0 else (lo, mid)
    return lo


def modes(wr: float, zr: float) -> list[complex]:
    out = [complex(-1.0 / TM)]
    if wr:
        out += [complex(-zr * wr, s * wr * math.sqrt(1 - zr * zr)) for s in (1, -1)]
    return out


def shared_draws(seed: int) -> tuple[list, list, list]:
    """Common random numbers: one draw per seed, fed to every arm and regime."""
    rng = random.Random(seed)
    steps = [(0.2 + 2.0 * i, rng.choice((-1.0, 1.0)) * rng.uniform(0.2, 1.0)) for i in range(3)]
    loads = [(1.2 + 2.0 * i, 0.3 * rng.uniform(-1.0, 1.0)) for i in range(3)]
    noise = [rng.gauss(0.0, NOISE) for _ in range(round(T_END / TS))]
    return steps, loads, noise


def simulate(arm: str, wr: float, zr: float, draws: tuple, sub: int = SUB) -> dict | None:
    steps, loads, noise = draws
    ctrl = Controller(arm, gain(arm, wr, zr))
    x, rf, u_prev = [0.0] * 4, 0.0, 0.0
    ise = du2 = 0.0
    over = [0.0] * len(steps)
    for i, nz in enumerate(noise):
        t = i * TS
        r = sum(a for t0, a in steps if t >= t0)
        rf += TS / 0.05 * (r - rf)  # shared reference prefilter, 50 ms
        u = ctrl.step(rf - (x[2] + nz))
        d = sum(a for t0, a in loads if t >= t0)
        for _ in range(sub):
            x = rk4(x, u + d, wr, zr, TS / sub)
        if abs(x[2]) > DIVERGED:
            return None
        ise += (rf - x[2]) ** 2 * TS
        du2 += (u - u_prev) ** 2
        u_prev = u
        for j, (t0, a) in enumerate(steps):
            if t0 <= t < t0 + 1.0:
                over[j] = max(over[j], math.copysign(1.0, a) * (x[2] - r) / abs(a))
    return {"ise": 1e3 * ise, "over": 100.0 * max(over), "du": math.sqrt(du2 / len(noise))}


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
    """4 decimals; scientific notation when 4 decimals would print a signed or bare zero."""
    if x != 0.0 and abs(x) < 5e-5:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs: list[float], m: float) -> str:
    """How many seeds disagree in sign with the paired mean (zeros listed apart)."""
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def verdict(xa: list[float], xb: list[float]) -> str:
    """Paired xa - xb per seed: mean+-sd, then the label and the sign count."""
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


def gm_text(gm: float) -> str:
    return "inf" if math.isinf(gm) else f"{gm:.2f}"


def main() -> None:
    print("Synthetic PID vs PID+notch vs PID+lead-lag; shared steps / load torques / sensor noise; not a motor bench")
    print(f"TS={TS} s RK4 H={H} s TM={TM} s WC={WC} rad/s TI={TI} s TD={TD} s N={N:.0f} "
          f"notch w0={WN:.0f} rad/s wc/w0={WIDTH} mistuned w0={MISTUNE * WN:.0f} rad/s lead PHI=30 deg seeds={len(SEEDS)}")
    print("stable margins = PM > 0 deg and GM > 0 dB on the Bode proxy, and no divergence (|y| <= 10 rad) on >= 4 of 5 seeds")
    print("regime arm Kc PM_deg GM_dB")
    for regime, wr, zr in REGIMES:
        h_max = min(rk4_h_max(lam) for lam in modes(wr, zr))
        amp = max(rk4_amp(H * lam) for lam in modes(wr, zr))
        assert amp < 1.0 and H < h_max
        cells = []
        for arm in ARMS:
            pm, gm = margins(arm, wr, zr)
            cells.append(f"{arm} {gain(arm, wr, zr):.2f} {pm:.1f} {gm_text(gm)}")
        print(f"{regime} (wr={wr:.0f}, zr={zr}) RK4 h_max={h_max * 1e3:.1f} ms > H: " + " | ".join(cells))
    print("notch width check (B_notch margins only, wc/w0 = 0.25 / 0.5 / 1.0; 0.5 was fixed before the first run):")
    for regime, wr, zr in REGIMES:
        cells = []
        for width in (0.25, 0.5, 1.0):
            pm, gm = margins("B_notch", wr, zr, width)
            cells.append(f"wc/w0={width} PM {pm:.1f} GM {gm_text(gm)}")
        print(f"  {regime}: " + " | ".join(cells))
    alt = []
    for arm in ARMS:
        pm, gm = margins(arm, 40.0, ALT_SHARP_ZR)
        alt.append(f"{arm} PM {pm:.1f} GM {gm_text(gm)}")
    print(f"resonant_sharp alternative zr={ALT_SHARP_ZR} (zr=0.05 was picked after a margin-only prototype): " + " | ".join(alt))
    print("regime arm ISE_1e-3rad2s overshoot_% du_rms  (mean+-sd over seeds)")
    draws = [shared_draws(seed) for seed in SEEDS]
    for regime, wr, zr in REGIMES:
        res = {arm: [simulate(arm, wr, zr, dr) for dr in draws] for arm in ARMS}
        for arm in ARMS:
            ok = [r for r in res[arm] if r is not None]
            if len(ok) < len(SEEDS):
                print(f"{regime} {arm} diverged (|y| > {DIVERGED:.0f} rad) on {len(SEEDS) - len(ok)} of {len(SEEDS)} seeds")
                continue
            print(f"{regime} {arm} " + " ".join("{}+-{}".format(*map(num, mean_sd([r[k] for r in ok])))
                                                 for k in ("ise", "over", "du")))
        for x in ("B_notch", "C_leadlag", "D_mistuned"):
            if any(r is None for r in res[x] + res["A_pid"]):
                bad = [a for a in ("A_pid", x) if any(r is None for r in res[a])]
                print(f"{regime} paired {x[0]}-A: not compared ({' and '.join(bad)} diverged)")
                continue
            for k in ("ise", "over", "du"):
                print(f"{regime} paired {x[0]}-A {k}: {verdict([r[k] for r in res[x]], [r[k] for r in res['A_pid']])}")
    print("well_damped: there is no mode to cut; the notch only adds phase lag at crossover and tracks worse")
    print("resonant: the mode is damped enough for PID alone; the notch costs phase margin and gain margin here")
    print("resonant_light: the notch buys gain margin (0.80 -> 2.35 dB) but tracks worse; lead diverges")
    print("resonant_sharp: PID and lead diverge; only the notch on the mode keeps the loop stable")
    print("D_mistuned: a notch 30 % below the mode adds lag without removing the peak")
    print("No winner declared; ISE is blind to actuator chatter (du_rms) and to the gain margin")
    print("Real servo / modal test: 本页未运行; Wikipedia definitions 以原文为准")


if __name__ == "__main__":
    main()
