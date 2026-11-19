#!/usr/bin/env python3
"""Synthetic jamming-gripper holding-force stand-in.

Stdlib only. Evaluates the friction and membrane-seal holding-force model
from Brown, Rodenberg, Amend, Mozeika, Steltz, Zakin, Lipson, Jaeger,
arXiv 1009.4444 v2 (submitted 2010-09-22, this version 2010-11-05).
No real vacuum pump, bag, or Instron is started.

A shared sphere radius and shared contact-angle draws are generated once
per (regime, seed) and then read by every arm (common random numbers).
Declared material constants are shared across arms; only confinement and
whether a membrane seal is allowed change.

Arms:
  A_unjammed -- no confinement, sigma_star = 0.
  B_friction -- jammed, porous / friction-only, Eq. 1.
  C_seal -- jammed, friction plus membrane-seal suction when a seal is
    allowed, Eq. 2. The paper's suction is a membrane seal that holds a
    gap vacuum while the object is lifted after jamming has pinched the
    bag; it is not an industrial vacuum cup.

When theta is below theta_c = arctan(1/mu), both Eq. 1 and Eq. 2 are
clamped to zero: the interface slips for any confinement.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.

Paper fits, the < 0.5 % volume-change remark, and the order-of-magnitude
suction enhancement stay 以论文为准 and are not toy measurements.
Real jamming bag / vacuum pump / Instron: 本页未运行.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared sphere and official material constants (paper-like; printed).
R = 0.0125  # m, declared sphere radius
MU = 1.04  # official toy mu; paper fit 1.04 +- 0.06 以论文为准
SIGMA_STAR = 50_000.0  # Pa; paper fit 50 +- 4 kPa 以论文为准
D = 0.00107  # m; paper fit 1.07 +- 0.07 mm 以论文为准
SIGMA_UNJAMMED = 0.0

# Named alternative, same seeds, not adopted: independent inclined-plane mu
# from the paper Methods (1.10 +- 0.03 以论文为准), used only as a named alt.
MU_ALT = 1.10

ARMS = ("A_unjammed", "B_friction", "C_seal")
METRICS = ("F_h",)
PAIRS = (("B", "A"), ("C", "A"), ("C", "B"))

# theta draws, written before the first run
THETA_BELOW_LO = 0.0500  # rad, still positive so sin(theta) is defined
THETA_BELOW_HI_FRAC = 0.9000  # fraction of theta_c
THETA_MODEST_LO = math.pi / 4.0  # rad; pi/4 < theta < pi/2
THETA_MODEST_HI = math.pi / 2.0
THETA_DISK_LO = 0.0200
THETA_DISK_HI = 0.1000

# name: (kind, declared expectation); written before the first run
REGIMES = {
    "below_theta_c": (
        "below_theta_c",
        "friction and seal holding force is zero regardless of sigma_star - lose kept",
    ),
    "modest_seal": (
        "modest_seal",
        "C consistent higher F_h than friction-only B - keep",
    ),
    "good_theta_unjammed": (
        "good_theta",
        "unjammed A loses hold against jammed B and C - keep",
    ),
    "thin_disk": (
        "thin_disk",
        "insufficient wrap loses hold - keep",
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


def theta_c(mu):
    return math.atan(1.0 / mu)


def holding_force(theta, sigma_star, mu, radius, width, seal):
    """Eq. 1 (seal=False) or Eq. 2 (seal=True); clamp to 0 at or below theta_c."""
    if sigma_star <= 0.0 or theta <= 0.0:
        return 0.0
    s = math.sin(theta)
    c = math.cos(theta)
    factor = mu * s - c
    if factor <= 0.0 or s <= 0.0:
        return 0.0
    if not seal:
        return 2.0 * math.pi * radius * width * sigma_star * factor * (s ** 2)
    return math.pi * (radius ** 2) * sigma_star * factor * (s ** 3) * (
        1.0 + 2.0 * width / (radius * s)
    )


def rng_for(*parts):
    h = 10094444
    for part in parts:
        if isinstance(part, str):
            for ch in part:
                h = (h * 131 + ord(ch)) & 0xFFFFFFFFFFFFFFFF
        else:
            h = (h * 131 + int(part)) & 0xFFFFFFFFFFFFFFFF
    return random.Random(h)


def shared_theta(seed, kind, mu):
    """Common random numbers: one contact angle per regime and seed, all arms."""
    rng = rng_for("theta", kind, seed)
    if kind == "below_theta_c":
        lo = THETA_BELOW_LO
        hi = THETA_BELOW_HI_FRAC * theta_c(mu)
        return rng.uniform(lo, hi)
    if kind in ("modest_seal", "good_theta"):
        return rng.uniform(THETA_MODEST_LO, THETA_MODEST_HI)
    if kind == "thin_disk":
        return rng.uniform(THETA_DISK_LO, THETA_DISK_HI)
    raise ValueError(kind)


def evaluate(arm, theta, mu=MU):
    if arm == "A_unjammed":
        fh = holding_force(theta, SIGMA_UNJAMMED, mu, R, D, seal=False)
    elif arm == "B_friction":
        fh = holding_force(theta, SIGMA_STAR, mu, R, D, seal=False)
    elif arm == "C_seal":
        fh = holding_force(theta, SIGMA_STAR, mu, R, D, seal=True)
    else:
        raise ValueError(arm)
    return {"F_h": fh, "theta": theta}


def run_regime(name, seed, mu=MU):
    kind, _decl = REGIMES[name]
    theta = shared_theta(seed, kind, mu)
    row = {"theta": theta}
    for arm in ARMS:
        row[arm] = evaluate(arm, theta, mu=mu)
    return row


def print_regime(title, rows):
    print(f"regime {title}  (mean+-sd over seeds)")
    thetas = [r["theta"] for r in rows]
    print(f"  theta_rad {num(mean_sd(thetas)[0])}+-{num(mean_sd(thetas)[1])}")
    for arm in ARMS:
        fh = [r[arm]["F_h"] for r in rows]
        print(f"  {arm} F_h_N {num(mean_sd(fh)[0])}+-{num(mean_sd(fh)[1])}")
    for left, right in PAIRS:
        la = [a for a in ARMS if a.startswith(left)][0]
        ra = [a for a in ARMS if a.startswith(right)][0]
        for key in METRICS:
            xa = [r[la][key] for r in rows]
            xb = [r[ra][key] for r in rows]
            print(f"  paired {left}-{right} {key}: {verdict(xa, xb)}")


def official_rows(name, mu=MU):
    return [run_regime(name, seed, mu=mu) for seed in SEEDS]


def main():
    tc = theta_c(MU)
    tc_alt = theta_c(MU_ALT)
    print("Synthetic jamming-gripper holding-force stand-in; not a real bag or pump")
    print(
        f"declared R={num(R)} m MU={num(MU)} SIGMA_STAR={num(SIGMA_STAR)} Pa "
        f"D=0.00107 m SIGMA_UNJAMMED={num(SIGMA_UNJAMMED)} Pa "
        f"SMALL_FRAC={num(SMALL_FRAC)} seeds={','.join(str(s) for s in SEEDS)}"
    )
    print("hand_calc D=1.0700 mm, SIGMA_STAR=50.0000 kPa")
    print(
        "declared arms: A_unjammed sigma_star=0; B_friction jammed Eq. 1; "
        "C_seal jammed Eq. 2 when a membrane seal is allowed"
    )
    print(f"hand_calc theta_c = arctan(1/MU) = {num(tc)} rad")
    print(f"hand_calc pi/4 = {num(math.pi / 4.0)} rad")
    print(f"hand_calc pi/2 = {num(math.pi / 2.0)} rad")
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print(
        "paper_fit mu=1.04 +- 0.06, sigma_star=50 +- 4 kPa, d=1.07 +- 0.07 mm "
        "(arXiv 1009.4444 v2; 以论文为准)"
    )
    print("paper_volume_change_less_than=0.5 % (arXiv 1009.4444 v2 abs / p.1; 以论文为准)")
    print(
        "paper_suction_enhancement_order=10 times for spheres that form a seal "
        "(arXiv 1009.4444 v2; 以论文为准, not a toy output)"
    )
    print(
        "paper_authors=Eric Brown, Nicholas Rodenberg, John Amend, Annan Mozeika, "
        "Erik Steltz, Mitchell R. Zakin, Hod Lipson, Heinrich M. Jaeger "
        "(abs / title-page order; 以论文为准)"
    )
    print("paper_version=arXiv 1009.4444 v2, submitted 2010-09-22, this version 2010-11-05")
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: the contact angle is shared across arms at each "
        "regime and seed"
    )
    print(
        "Assumptions: Eqs. 1-2 with F_h clamped to 0 at or below theta_c; "
        "no interlocking yield law; no real bag"
    )
    print("Paper figures (fits, 0.5 %, 10 times, authorship) 以论文为准")
    print("Real jamming bag / vacuum pump / Instron: 本页未运行")
    print("declared below_theta_c: friction and seal holding force is zero regardless of sigma_star - lose kept")
    print("declared modest_seal: C consistent higher F_h than friction-only B - keep")
    print("declared good_theta_unjammed: unjammed A loses hold against jammed B and C - keep")
    print("declared thin_disk: insufficient wrap loses hold - keep")

    official = {name: official_rows(name) for name in REGIMES}
    for name, (_kind, decl) in REGIMES.items():
        print(f"declared expectation {name}: {decl}")
        print_regime(name, official[name])

    print(f"alternative same seeds MU={num(MU_ALT)} (not adopted)")
    print(f"hand_calc theta_c at MU_ALT = arctan(1/MU_ALT) = {num(tc_alt)} rad")
    print(
        "paper_independent_mu=1.10 +- 0.03 from the inclined-plane test "
        "(arXiv 1009.4444 v2 Methods; 以论文为准, named alternative only)"
    )
    for name in REGIMES:
        print_regime(f"{name} alt_mu={num(MU_ALT)}", official_rows(name, mu=MU_ALT))

    print("No real vacuum pump or bag was started")
    print(
        "No winner is universal: below theta_c both jammed arms lose hold; "
        "a membrane seal can raise F_h only when theta exceeds theta_c and a seal is allowed"
    )


if __name__ == "__main__":
    main()
