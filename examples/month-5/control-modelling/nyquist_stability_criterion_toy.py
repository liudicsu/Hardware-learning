#!/usr/bin/env python3
"""Synthetic Nyquist stability-criterion toy.

Stdlib only. Shared declared linear plants, a shared controller (already
absorbed as a loop gain K in each open-loop G), and a shared omega grid.
The contour is deterministic: every seed sees the same plants and the same
grid. Seeds are still printed (five) so the verdict helpers stay uniform.

Arms:
  A_bode_first — accept the loop if the first gain-crossover phase margin
                 is at least the declared threshold; ignore other crossings
                 and open-loop right-half-plane poles
  B_nyquist — accept iff Z = N + P equals 0, with N the clockwise
              encirclements of -1+j0 and P the open-loop RHP pole count
  C_bode_any — accept if any one gain-crossover phase margin looks healthy,
               and treat P as 0 (a still-weaker Bode-only call)

Not a rewrite of the page's Bode helpers, not a Smith/computed-torque
re-teach, and not the sampling Nyquist frequency (fs/2) used by the existing
helper. Real plant / analyzer: 本页未运行.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.
"""
import cmath
import math
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared contour and Bode-threshold parameters.
PTS_PER_DEC = 80
LOG_W_MIN = -3  # 10^-3
LOG_W_MAX = 4   # 10^4
PM_MIN_DEG = 30.0
# Step diagnostic (plant-level, not an arm metric). Euler integration bound.
DT = 0.001
T_END = 20.0
Y_CLIP = 20.0

METRICS = ("call", "miss")
ARMS = ("A_bode_first", "B_nyquist", "C_bode_any")
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

# Plants: (name, num, den, declared_P, declared expectation)
# num/den are highest-power first. Delay is not used in the official plants.
PLANTS = {
    "ol_stable_joint": {
        "num": (72.0,),           # 2 * 6^2
        "den": (1.0, 6.0, 36.0),  # s^2 + 2*0.5*6 s + 6^2
        "P": 0,
        "expect": "A and B agree on call and may near-tie - keep",
    },
    "ol_unstable": {
        "num": (8.0, 1.6),        # 8*(s + 0.2000)
        "den": (1.0, 3.0, -4.0),  # (s - 1)*(s + 4)
        "P": 1,
        "expect": "A's single-margin stable call loses; B flags the missing encirclement (Z = N + P != 0) - keep",
    },
    "nmp_encircle": {
        "num": (-5.0, 1.0),       # 1 - s/0.2000
        "den": (1.0, 3.0, 2.0),   # (s + 1)*(s + 2)
        "P": 0,
        "expect": "C loses (one healthy phase margin, but the plot encircles -1) - keep",
    },
}

# Alternative coarser grid (printed, not adopted).
ALT_PTS_PER_DEC = 20


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    x = float(x)
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


def poly_eval(coeffs, s):
    acc = 0j
    for a in coeffs:
        acc = acc * s + a
    return acc


def G_jw(numc, denc, w):
    s = 1j * w
    return poly_eval(numc, s) / poly_eval(denc, s)


def omega_grid(pts_per_dec, log_min=LOG_W_MIN, log_max=LOG_W_MAX):
    # Inclusive end: (log_max-log_min)*pts_per_dec + 1 points.
    n = (log_max - log_min) * pts_per_dec
    return [10 ** (log_min + i * (log_max - log_min) / n) for i in range(n + 1)]


def unwrap_phase(angles):
    out = []
    prev = None
    acc = 0.0
    for a in angles:
        if prev is None:
            acc = a
        else:
            d = a - prev
            while d > math.pi:
                d -= 2 * math.pi
            while d < -math.pi:
                d += 2 * math.pi
            acc += d
        out.append(acc)
        prev = a
    return out


def bode_margins(numc, denc, grid):
    mag = []
    raw = []
    for w in grid:
        g = G_jw(numc, denc, w)
        mag.append(abs(g))
        raw.append(cmath.phase(g))
    un = unwrap_phase(raw)
    pms = []
    gms = []
    for i in range(len(grid) - 1):
        if (mag[i] - 1.0) * (mag[i + 1] - 1.0) <= 0 and mag[i] != mag[i + 1]:
            t = (1.0 - mag[i]) / (mag[i + 1] - mag[i])
            ph = un[i] + t * (un[i + 1] - un[i])
            # log interpolation of omega
            w = grid[i] * (grid[i + 1] / grid[i]) ** t
            pms.append((ph * 180.0 / math.pi + 180.0, w))
        # phase crossing of -180 deg on the unwrapped branch nearest odd multiples
        # GM at the first phase == -pi (plus 2pi k) crossing.
        target = -math.pi
        # search nearest odd-pi using the unwrapped value crossing -pi, -3pi, ...
        for k in range(-6, 7):
            tgt = -math.pi + 2 * math.pi * k
            if (un[i] - tgt) * (un[i + 1] - tgt) <= 0 and un[i] != un[i + 1]:
                t = (tgt - un[i]) / (un[i + 1] - un[i])
                w = grid[i] * (grid[i + 1] / grid[i]) ** t
                magc = mag[i] + t * (mag[i + 1] - mag[i])
                if magc > 1e-18:
                    gm_db = -20.0 * math.log10(magc)
                    gms.append((gm_db, w, magc))
                break
    return pms, gms


def winding_N(numc, denc, grid):
    # D-contour image: omega from -inf to +inf, then close through the origin
    # (strictly proper G(j inf) = 0). Clockwise encirclements of -1.
    pos = [G_jw(numc, denc, w) for w in grid]
    neg = [G_jw(numc, denc, -w) for w in grid[::-1]]
    curve = neg + pos
    rel = [z + 1.0 for z in curve]
    dang = 0.0
    for a, b in zip(rel, rel[1:] + rel[:1]):
        if abs(a) < 1e-18 or abs(b) < 1e-18:
            continue
        q = b / a
        dang += math.atan2(q.imag, q.real)
    return -dang / (2.0 * math.pi)


def rhp_poles_quadratic(denc):
    # den = s^2 + a s + b, roots of s^2 + a s + b = 0.
    if len(denc) != 3 or denc[0] != 1.0:
        raise ValueError("official plants are monic second-order")
    a, b = denc[1], denc[2]
    disc = a * a - 4.0 * b
    if disc >= 0:
        r1 = (-a + math.sqrt(disc)) / 2.0
        r2 = (-a - math.sqrt(disc)) / 2.0
        return int(r1.real > 0) + int(r2.real > 0), (r1, r2)
    real = -a / 2.0
    imag = math.sqrt(-disc) / 2.0
    return int(real > 0) + int(real > 0), (complex(real, imag), complex(real, -imag))


def simulate_step(numc, denc, dt=DT, t_end=T_END, y_clip=Y_CLIP):
    """Unity-feedback step, controllable canonical form, forward Euler.

    Closed-loop input is r - y. |y| is clipped at y_clip; ISE is integrated
    to t_end. The clip is the declared step-stability bound.
    """
    # Plant: strictly proper monic second order, y = C x, ẋ = A x + B u
    # Companion: ẋ1 = x2, ẋ2 = -a0 x1 - a1 x2 + u, y = b0 x1 + b1 x2
    # den = [1, a1, a0], num padded to [b1, b0]
    a1, a0 = denc[1], denc[2]
    if len(numc) == 1:
        b1, b0 = 0.0, numc[0]
    else:
        b1, b0 = numc[0], numc[1]
    x1 = 0.0
    x2 = 0.0
    ise = 0.0
    clipped = 0
    nstep = int(round(t_end / dt))
    y = 0.0
    for _ in range(nstep):
        u = 1.0 - y
        dx1 = x2
        dx2 = -a0 * x1 - a1 * x2 + u
        x1 += dt * dx1
        x2 += dt * dx2
        y = b0 * x1 + b1 * x2
        if y > y_clip:
            y = y_clip
            clipped = 1
        elif y < -y_clip:
            y = -y_clip
            clipped = 1
        ise += (y - 1.0) ** 2 * dt
    return ise, clipped, y


def analyze(plant, pts_per_dec):
    numc = plant["num"]
    denc = plant["den"]
    grid = omega_grid(pts_per_dec)
    pms, gms = bode_margins(numc, denc, grid)
    N_raw = winding_N(numc, denc, grid)
    N = int(round(N_raw))
    P_calc, roots = rhp_poles_quadratic(denc)
    P = plant["P"]
    if P_calc != P:
        # still use the declared P; surface the check in the printed line
        pass
    Z = N + P
    first_pm = pms[0][0] if pms else None
    any_healthy = any(pm >= PM_MIN_DEG for pm, _w in pms)
    first_healthy = (first_pm is not None) and (first_pm >= PM_MIN_DEG)
    ise, clipped, y_end = simulate_step(numc, denc)
    return {
        "pms": pms,
        "gms": gms,
        "N_raw": N_raw,
        "N": N,
        "P": P,
        "P_calc": P_calc,
        "roots": roots,
        "Z": Z,
        "first_pm": first_pm,
        "first_healthy": first_healthy,
        "any_healthy": any_healthy,
        "ise": ise,
        "clipped": clipped,
        "y_end": y_end,
        "n_grid": len(grid),
    }


def arm_scores(info):
    A_call = 1.0 if info["first_healthy"] else 0.0
    B_call = 1.0 if info["Z"] == 0 else 0.0
    C_call = 1.0 if info["any_healthy"] else 0.0
    truth_stable = info["Z"] == 0
    def miss(call):
        return 1.0 if (call == 1.0 and not truth_stable) else 0.0
    return {
        "A_bode_first": {"call": A_call, "miss": miss(A_call)},
        "B_nyquist": {"call": B_call, "miss": miss(B_call)},
        "C_bode_any": {"call": C_call, "miss": miss(C_call)},
    }


def fmt_pms(pms):
    if not pms:
        return "none"
    return ";".join(f"{num(pm)}deg@w={num(w)}" for pm, w in pms)


def fmt_gms(gms):
    if not gms:
        return "none"
    # unique-ish by omega
    seen = []
    for gm, w, magc in gms:
        rec = f"{num(gm)}dB@w={num(w)}"
        if rec not in seen:
            seen.append(rec)
    return ";".join(seen)


def main():
    print("Nyquist stability-criterion toy: shared declared linear plants and a shared omega grid (synthetic; not a rewrite of the Bode helpers, not Smith, not computed torque, not the sampling Nyquist frequency)")
    print("Real plant / analyzer: 本页未运行")
    print(
        f"seeds={len(SEEDS)} pts_per_dec={PTS_PER_DEC} log_w={LOG_W_MIN}_to_{LOG_W_MAX} "
        f"pm_min_deg={num(PM_MIN_DEG)} dt={num(DT)} t_end={num(T_END)} y_clip={num(Y_CLIP)} "
        f"alt_pts_per_dec={ALT_PTS_PER_DEC} (declared)"
    )
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: none; the contour is deterministic and every seed sees the same plants and the same omega grid")
    print(f"hand_calc Z = N + P, closed-loop stable iff Z = 0")
    print(f"hand_calc step-stability bound: |y| clipped at {num(Y_CLIP)}; ISE integrated to t_end={num(T_END)} with Euler step dt={num(DT)}")
    print(f"hand_calc ol_stable_joint wn=6.0000 zeta=0.5000 K=2.0000")
    print(f"hand_calc card range omega = {10 ** LOG_W_MIN:.4f} to {10 ** LOG_W_MAX:.4f}")
    print("hand_calc ol_unstable factor 0.2000")
    print("hand_calc nmp_encircle factor 0.2000")
    for name, plant in PLANTS.items():
        print(
            f"declared {name}: num={plant['num']} den={plant['den']} P={plant['P']}: {plant['expect']}"
        )

    official = {name: analyze(plant, PTS_PER_DEC) for name, plant in PLANTS.items()}
    alternative = {name: analyze(plant, ALT_PTS_PER_DEC) for name, plant in PLANTS.items()}

    for name, plant in PLANTS.items():
        info = official[name]
        print(f"plant {name}")
        print(
            f"  N_raw={num(info['N_raw'])} N={info['N']} P={info['P']} P_calc={info['P_calc']} "
            f"Z={info['Z']} first_pm={num(info['first_pm']) if info['first_pm'] is not None else 'none'} "
            f"pms={fmt_pms(info['pms'])} gms={fmt_gms(info['gms'])} "
            f"n_grid={info['n_grid']} step_ise={num(info['ise'])} clipped={info['clipped']} "
            f"y_end={num(info['y_end'])}"
        )
        scores = arm_scores(info)
        # Deterministic: repeat the same scores on every seed.
        store = {arm: {m: [scores[arm][m]] * len(SEEDS) for m in METRICS} for arm in ARMS}
        for arm in ARMS:
            for m in METRICS:
                mu, sd = mean_sd(store[arm][m])
                print(f"  {arm} {m}: {num(mu)}+-{num(sd)}")
        for left, right in PAIRS:
            la = [a for a in ARMS if a.startswith(left + "_")][0]
            ra = [a for a in ARMS if a.startswith(right + "_")][0]
            for m in METRICS:
                print(f"  paired {left}-{right} {m}: {verdict(store[la][m], store[ra][m])}")

    print("alternative pts_per_dec=20 (printed, not adopted)")
    for name in PLANTS:
        o, a = official[name], alternative[name]
        o_scores, a_scores = arm_scores(o), arm_scores(a)
        print(
            f"  {name} official N={o['N']} Z={o['Z']} first_pm={num(o['first_pm']) if o['first_pm'] is not None else 'none'}; "
            f"alternative N={a['N']} Z={a['Z']} first_pm={num(a['first_pm']) if a['first_pm'] is not None else 'none'}"
        )
        for arm in ARMS:
            same = o_scores[arm] == a_scores[arm]
            print(
                f"  {name} {arm} official call={num(o_scores[arm]['call'])} miss={num(o_scores[arm]['miss'])}; "
                f"alternative call={num(a_scores[arm]['call'])} miss={num(a_scores[arm]['miss'])}; same_labels={'yes' if same else 'no'}"
            )


if __name__ == "__main__":
    main()
