#!/usr/bin/env python3
"""Synthetic PID vs PID + lead-lag on a joint with a compliant mode. Stdlib only.

Plant (linear, LTI, no actuator limit):
  G(s) = 1 / (s (TM s + 1)) * wr^2 / (s^2 + 2 zr wr s + wr^2)
  motor + inertia (TM = 0.05 s), then a compliant transmission mode (wr, zr) between
  motor and the measured link angle (non-collocated sensor). The rigid case drops
  the mode. Torque disturbance enters at the plant input.

Controllers (sampled at TS = 1 ms, every section discretised with Tustin):
  A_pid       Kc * (1 + 1/(TI s) + TD s / (TD/N s + 1))
  B_leadlag   A's shape * lead (s/z+1)/(s/p+1), |z| < |p|, centred on WC with
              PHI = 30 deg (p/z = (1+sin PHI)/(1-sin PHI)) * lag with |z2| > |p2|
              (z2 = WC/10, p2 = z2/3)
  C_swapped   B with the lead's pole and zero swapped (a lag where lead was needed)
  Same design rule for every arm: one fixed recipe (not tuned per regime), and Kc
  is chosen so |L(j WC)| = 1 on the actual plant, so all arms share crossover WC.

Common random numbers: per seed the three reference steps, three load-torque
steps and the measurement-noise sequence (sd 0.5 mrad) are drawn once and fed to
every arm. Integration: RK4 with H = TS/4 under zero-order-hold control. RK4 is
stable for a mode lambda when |R(H lambda)| <= 1, R(z) = 1+z+z^2/2+z^3/6+z^4/24;
the toy prints max |R| over the plant's non-zero modes and asserts it is < 1.

Labels: tie = identical on every seed; |paired mean| <= sd = near-tie / small gap
within seed noise; |m| > sd = consistent gap (small if |m| < 20 % of the smaller
arm mean, else clear), always with a sign count. Margins are a discrete Bode
proxy (Tustin controller x continuous plant x ZOH half-sample delay).
Real servo / motor bench: 本页未运行. Wikipedia definitions: 以原文为准.
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
T_END = 6.0
NOISE = 5e-4  # rad, measurement noise sd
DIVERGED = 10.0  # rad, abort threshold (the references never exceed 3 rad)
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_pid", "B_leadlag", "C_swapped")
# name, wr (0 = rigid), zr
REGIMES = (("well_damped", 0.0, 0.0), ("resonant", 40.0, 0.3), ("resonant_light", 40.0, 0.2))


def sections(arm: str) -> list[tuple[float, float]]:
    """(zero, pole) pairs of the first-order sections cascaded after the PID."""
    if arm == "A_pid":
        return []
    z, p = WC / math.sqrt(ALPHA), WC * math.sqrt(ALPHA)
    if arm == "C_swapped":
        z, p = p, z
    return [(z, p), (WC / 10.0, WC / 10.0 / BETA)]


def plant(w: float, wr: float, zr: float) -> complex:
    s = 1j * w
    g = 1.0 / (s * (TM * s + 1.0))
    return g * wr * wr / (s * s + 2 * zr * wr * s + wr * wr) if wr else g


def shape(arm: str, w: float) -> complex:
    s = 1j * w
    c = 1.0 + 1.0 / (TI * s) + TD * s / (TD / N * s + 1.0)
    for z, p in sections(arm):
        c *= (s / z + 1.0) / (s / p + 1.0)
    return c


def gain(arm: str, wr: float, zr: float) -> float:
    return 1.0 / abs(shape(arm, WC) * plant(WC, wr, zr))


def margins(arm: str, wr: float, zr: float) -> tuple[float, float]:
    """Smallest phase margin over all |L| = 1 crossings and smallest gain margin
    (dB) over -180 deg crossings with |L| < 1; unwrapped phase from 0.1 rad/s."""
    k = gain(arm, wr, zr)
    pms, gms = [], []
    prev = None
    off = 0.0
    n = 20000
    for i in range(n + 1):
        w = 10 ** (-1 + i * (math.log10(math.pi / TS) + 1) / n)
        loop = k * shape(arm, w) * plant(w, wr, zr) * cmath.exp(-0.5j * w * TS)
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


class Controller:
    """PI (trapezoid) + filtered D (Tustin), then Tustin first-order sections."""

    def __init__(self, arm: str, k: float) -> None:
        c = 2.0 / TS
        self.k, self.i, self.e_prev, self.d = k, 0.0, 0.0, 0.0
        tf = TD / N
        self.db0, self.da1 = TD * c / (tf * c + 1.0), (1.0 - tf * c) / (tf * c + 1.0)
        self.secs = []
        for z, p in sections(arm):
            a0 = c / p + 1.0
            self.secs.append([(c / z + 1.0) / a0, (1.0 - c / z) / a0, (1.0 - c / p) / a0, 0.0, 0.0])

    def step(self, e: float) -> float:
        self.i += TS / TI * (e + self.e_prev) / 2.0
        self.d = self.db0 * (e - self.e_prev) - self.da1 * self.d
        self.e_prev = e
        x = e + self.i + self.d
        for sec in self.secs:
            b0, b1, a1, xp, yp = sec
            y = b0 * x + b1 * xp - a1 * yp
            sec[3], sec[4] = x, y
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


def sign_note(diffs: list[float], m: float) -> str:
    """How many seeds disagree in sign with the paired mean (zeros listed apart)."""
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m: float, s: float) -> str:
    """Paired mean+-sd; extra decimals when 4 would print a signed zero such as -0.0000."""
    if m != 0.0 and abs(m) < 5e-5:
        return f"{m:.6f}+-{s:.6f}"
    return f"{m:.4f}+-{s:.4f}"


def verdict(xa: list[float], xb: list[float]) -> str:
    """Paired xa - xb per seed: mean+-sd, then the label and the sign count."""
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(mean_sd(xa)[0], mean_sd(xb)[0]):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def main() -> None:
    print("Synthetic PID vs PID+lead-lag; shared steps / load torques / sensor noise; not a motor bench")
    print(f"TS={TS} s RK4 H={H} s TM={TM} s WC={WC} rad/s TI={TI} s TD={TD} s N={N:.0f} "
          f"lead PHI=30 deg p/z={ALPHA:.3f} lag z2={WC / 10:.1f} p2={WC / 30:.4f} rad/s seeds={len(SEEDS)}")
    print("regime arm Kc PM_deg GM_dB")
    for regime, wr, zr in REGIMES:
        amp = max(rk4_amp(H * lam) for lam in modes(wr, zr))
        h_max = min(rk4_h_max(lam) for lam in modes(wr, zr))
        assert amp < 1.0 and H < h_max
        cells = []
        for arm in ARMS:
            pm, gm = margins(arm, wr, zr)
            cells.append(f"{arm} {gain(arm, wr, zr):.2f} {pm:.1f} {'inf' if math.isinf(gm) else f'{gm:.2f}'}")
        print(f"{regime} (wr={wr:.0f}, zr={zr}) RK4 h_max={h_max * 1e3:.1f} ms > H, max|R(H lambda)|={amp:.6f} < 1: "
              + " | ".join(cells))
    print("regime arm ISE_1e-3rad2s overshoot_% du_rms  (mean+-sd over seeds)")
    draws = [shared_draws(seed) for seed in SEEDS]
    for regime, wr, zr in REGIMES:
        res = {arm: [simulate(arm, wr, zr, dr) for dr in draws] for arm in ARMS}
        for arm in ARMS:
            ok = [r for r in res[arm] if r is not None]
            if len(ok) < len(SEEDS):
                print(f"{regime} {arm} diverged (|y| > {DIVERGED:.0f} rad) on {len(SEEDS) - len(ok)} of {len(SEEDS)} seeds")
                continue
            print(f"{regime} {arm} " + " ".join("{:.4f}+-{:.4f}".format(*mean_sd([r[k] for r in ok]))
                                                 for k in ("ise", "over", "du")))
        for x in ("B_leadlag", "C_swapped"):
            if any(r is None for r in res[x] + res["A_pid"]):
                print(f"{regime} paired {x[0]}-A: not compared ({x} closed loop unstable)")
                continue
            for k in ("ise", "over", "du"):
                print(f"{regime} paired {x[0]}-A {k}: {verdict([r[k] for r in res[x]], [r[k] for r in res['A_pid']])}")
    print("well_damped: PID alone already has margin; the extra lead adds phase it does not need and passes more sensor noise")
    print("resonant: the lead restores phase margin at the same crossover, but its high-frequency gain shrinks the gain margin")
    print("resonant_light: the lead lifts the resonant peak through 0 dB; a lightly damped mode needs a notch, not more lead")
    print("No winner declared; ISE is blind to actuator chatter (du_rms) and to the gain margin")
    print("Real servo / motor bench: 本页未运行; Wikipedia definitions 以原文为准")


if __name__ == "__main__":
    main()
