#!/usr/bin/env python3
"""URDF <inertial><origin> and the parallel-axis theorem, on a shared chassis box.

Synthetic rigid-body bookkeeping, stdlib only.  Not Gazebo, not a URDF
parser, not inertia_check.py and not the "inertia without guessing" macros
(this toy reuses their box formula).  Gazebo / a real inertia measurement:
本页未运行.  Wikipedia "Parallel axis theorem" statements 以原文为准.

What the Wikipedia body says (and what this toy keeps): for an axis z'
parallel to an axis z through the centre of mass and a perpendicular
distance d away, I = I_cm + m d^2.  The tensor form moves the whole inertia
tensor from the centre of mass to a new point at displacement R:
  J = I + m [ (R . R) E3 - R (x) R ]
so a shift along an axis does not change the moment about that axis, and a
shift in two directions creates a product of inertia J_xy = -m R_x R_y.

The URDF convention used by the lesson: <inertial><origin> is the centre of
mass, and ixx..izz are taken about that origin.  The "engine" below does what
any physics engine has to do with that pair: it moves the written matrix
from the written origin to the joint point with the tensor form.

Common random numbers: for each (regime, seed) the chassis mass and its
three sizes are drawn once (manufacturing tolerance) and shared by all three
arms.  The true centre of mass sits at the regime's offset r from the joint.
Arms (how the <inertial> is written):
  A_com      : origin = r (the COM), matrix = I_cm         (correct URDF)
  B_typo     : origin = 0 (the joint), matrix = I_cm        (the common typo)
  C_shifted  : origin = 0 (the joint), matrix = I_cm moved to the joint
               with the tensor form (J at the joint)
Metrics: J_zz, J_xx and J_xy about the joint point, alpha_z = TAU / J_zz,
and the static gravity torque about the joint's y axis, m g x_origin (it
depends only on where the origin says the mass is).
No integration step: closed form, no time stepping.

Regimes and parameters were written before the first run:
  zero       : r = (0, 0, 0)        - A, B, C tie on every metric
  small      : r = (0.01, 0, 0)     - B under-estimates J_zz; may near-tie
                                      (kept as it comes)
  large      : r = (0.15, 0, 0)     - pivot at the rear edge: B consistent
                                      under-estimates J_zz and over-estimates
                                      alpha_z (typo loses); C ties A on J_zz;
                                      C loses to A on gravity torque (it puts
                                      the mass at the joint); keep
  along_axis : r = (0, 0, 0.04)     - B ties A on J_zz (shift along z), B
                                      under-estimates J_xx
  diagonal   : r = (0.10, 0.08, 0)  - B misses the product J_xy; C ties A
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
MASS = 2.0                    # kg, the lesson's m4bot chassis
SIZE = (0.30, 0.24, 0.08)     # m, x y z, the lesson's chassis box
MASS_TOL = 0.03               # +-3 % uniform (toy tolerance)
SIZE_TOL = 0.02               # +-2 % uniform per side (toy tolerance)
TAU = 0.05                    # N m, shared yaw torque at the joint (toy)
G = 9.81                      # m/s^2

REGIMES = {
    "zero": (0.0, 0.0, 0.0),
    "small": (0.01, 0.0, 0.0),
    "large": (0.15, 0.0, 0.0),
    "along_axis": (0.0, 0.0, 0.04),
    "diagonal": (0.10, 0.08, 0.0),
}
ARMS = ("A_com", "B_typo", "C_shifted")


def box_icm(m, x, y, z):
    """The lesson's inertial_box macro: diagonal, about the centre of mass."""
    return [[m / 12 * (y * y + z * z), 0.0, 0.0],
            [0.0, m / 12 * (x * x + z * z), 0.0],
            [0.0, 0.0, m / 12 * (x * x + y * y)]]


def shift(mat, m, r):
    """Tensor parallel-axis form: J = I + m[(R.R)E3 - R(x)R]."""
    rr = r[0] * r[0] + r[1] * r[1] + r[2] * r[2]
    return [[mat[i][j] + m * ((rr if i == j else 0.0) - r[i] * r[j]) for j in range(3)] for i in range(3)]


def shared_body(regime, seed):
    """Common random numbers: one mass and one set of sizes per (regime, seed)."""
    rng = random.Random(f"{regime}/{seed}")
    m = MASS * rng.uniform(1 - MASS_TOL, 1 + MASS_TOL)
    dims = [s * rng.uniform(1 - SIZE_TOL, 1 + SIZE_TOL) for s in SIZE]
    return m, dims


def written(arm, m, icm, r):
    """(origin, matrix) as the arm writes them in <inertial>."""
    if arm == "A_com":
        return list(r), icm
    if arm == "B_typo":
        return [0.0, 0.0, 0.0], icm
    return [0.0, 0.0, 0.0], shift(icm, m, r)


def run_arm(arm, regime, seed, r=None):
    r = REGIMES[regime] if r is None else r
    m, dims = shared_body(regime, seed)
    icm = box_icm(m, *dims)
    origin, mat = written(arm, m, icm, r)
    j = shift(mat, m, origin)  # the engine: move the written matrix to the joint point
    return {"J_zz": j[2][2], "J_xx": j[0][0], "J_xy": j[0][1], "alpha_z": TAU / j[2][2],
            "tau_g": m * G * origin[0], "m": m}


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


METRICS = ("J_zz", "J_xx", "J_xy", "alpha_z", "tau_g")


def collect(regime, r=None):
    return {arm: [run_arm(arm, regime, s, r) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [x[key] for x in rows]


def report(regime):
    r = REGIMES[regime]
    res = collect(regime)
    print(f"{regime} (COM offset r = ({num(r[0])}, {num(r[1])}, {num(r[2])}) m from the joint):")
    print("  mass per seed (kg): " + " ".join(num(m) for m in col(res["A_com"], "m")))
    for arm in ARMS:
        print(f"  {arm} " + " ".join(f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS))
    for a, b in (("B_typo", "A_com"), ("C_shifted", "A_com")):
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: {verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("Synthetic URDF parallel-axis toy; shared chassis mass and size draws; not a Gazebo run")
    print(f"seeds={len(SEEDS)} mass={num(MASS)} kg +-{num(100 * MASS_TOL)} % size={num(SIZE[0])} x {num(SIZE[1])} x {num(SIZE[2])} m "
          f"+-{num(100 * SIZE_TOL)} % TAU={num(TAU)} N m g={num(G)} m/s^2 (declared toy parameters, not a measured robot)")
    print("No integration step: closed form, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print("rule: engine J = M + m[(o.o)E3 - o(x)o] from the written origin o to the joint; gravity torque = m g x_o")
    # Labelled hand calculation on the nominal chassis (no tolerance draw).
    icm = box_icm(MASS, *SIZE)
    md2 = MASS * 0.15 ** 2
    print(f"hand_calc nominal chassis m=2.0 kg 0.30 x 0.24 x 0.08 m: Izz_cm=2.0/12*(0.30^2+0.24^2)={num(icm[2][2])} kg m^2; "
          f"radius of gyration sqrt(Izz_cm/m)={num(math.sqrt(icm[2][2] / MASS))} m")
    print(f"hand_calc d=0.15 m: m d^2=2.0*0.15^2={num(md2)} kg m^2; I=Izz_cm+m d^2={num(icm[2][2] + md2)} kg m^2; "
          f"typo/true={num(icm[2][2] / (icm[2][2] + md2))}")
    print(f"hand_calc d=0.01 m: m d^2=2.0*0.01^2={num(MASS * 0.01 ** 2)} kg m^2 ({num(100 * MASS * 0.01 ** 2 / icm[2][2])} % of Izz_cm)")
    print(f"hand_calc r=(0.10, 0.08, 0): J_xy=-m*0.10*0.08={num(-MASS * 0.10 * 0.08)} kg m^2")
    for regime in REGIMES:
        report(regime)
    print("alternative offsets (post-hoc check of the declared d; same seeds):")
    for regime, r in (("large", (0.10, 0.0, 0.0)), ("large", (0.20, 0.0, 0.0)), ("small", (0.005, 0.0, 0.0))):
        alt = collect(regime, r)
        print(f"  {regime} with r=({num(r[0])}, 0, 0): paired B-A J_zz@alt: {verdict(col(alt['B_typo'], 'J_zz'), col(alt['A_com'], 'J_zz'))}")
    print("No winner declared beyond the bookkeeping: writing the origin at the COM (A) is the URDF convention; "
          "a shifted matrix at the joint (C) gives the same inertia about the joint but puts the mass at the joint for gravity")
    print("Gazebo / a real inertia measurement: 本页未运行; Wikipedia Parallel axis theorem statements 以原文为准")


if __name__ == "__main__":
    main()
