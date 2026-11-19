#!/usr/bin/env python3
"""Stdlib stand-in of the documented MuJoCo elliptic and pyramidal
friction-cone inequalities.

Stdlib only. Not mujoco.step, not a redo of grip_sweep (timestep x solref
on a soft-contact lift), and not a third invented cone. Real MuJoCo /
mujoco.step: 本页未运行.

Pinned source: MuJoCo Computation, Friction cones, tag 4.0.1 (readthedocs
4.0.1 and the 4.0.1 doc/computation/index.rst body). Inequalities
以文档为准. This stand-in uses the same contact-frame force components for
both tests; the pyramidal set is the non-negative span of the documented
edge basis (each edge combines a normal component and one frictional
component, scaled so the edges lie in the elliptic cone).

For condim n=1 both documented cones are the non-negative ray. For
n=3 (regular frictional contact) the docs give 3 elliptic constraint
dimensions and 4 pyramidal constraint dimensions.

Arms:
  A_elliptic   membership in the documented elliptic cone
  B_pyramid    membership in the documented pyramidal cone, mapped
               to the same contact-frame force
  C_unbounded  lose arm: treats friction as unbounded (admits any
               sample with a non-negative normal component; drops the
               normal-component coupling of the pyramid edges)

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean|
and sd both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap
(small if |m| < 20 % of the smaller arm mean, else clear), with a
sign count. ROUND_HALF_UP output.

MuJoCo Computation documentation: body read; 以文档为准.
"""
from __future__ import annotations

import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared stand-in parameters (not a solver default, not a retune after
# seeing official output). Written before the first run.
MU_Y = 0.5000
MU_Z = 0.5000
N_SAMPLE = 40
FN_SCALE = 1.0000
# Official condim for mid and high regimes (regular frictional contact).
CONDIM_FRIC = 3
# Frictionless regime uses condim=1, both cones the non-negative ray.
CONDIM_FREE = 1

ARMS = ("A_elliptic", "B_pyramid", "C_unbounded")
METRICS = ("admit_rate", "illegal_admit_rate")
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

# name: declared expectation; written before the first run
REGIMES = {
    "frictionless": (
        "condim=1; both documented cones are the non-negative ray; "
        "A and B may tie or near-tie on admission - keep"
    ),
    "mid_tangential": (
        "condim=3; some shared samples lie inside the elliptic cone and "
        "outside the pyramid (or vice versa if the documented sets say so); "
        "print the discrepancy and keep the sign; do not retune to force "
        "the pyramid to be always more conservative - keep"
    ),
    "high_tangential": (
        "high tangential demand; C loses (unbounded friction admits "
        "forces outside both documented cones) - keep"
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
    material = "friction-cone|" + "|".join(str(p) for p in parts)
    return random.Random(material)


def elliptic_dims(condim):
    return 1 if condim == 1 else condim


def pyramidal_dims(condim):
    # Documented: 1 for n=1; 2(n-1) edges for n>1 (n=3 -> 4).
    return 1 if condim == 1 else 2 * (condim - 1)


def in_elliptic(fn, fy, fz, mu_y, mu_z, condim):
    """Documented elliptic cone, n = condim.

    For n=1: the non-negative ray. For n>1:
    f1 >= 0 and f1^2 >= sum_{i=2..n} f_i^2 / mu_{i-1}^2.
    This stand-in uses regular frictional contact (n=3), so only the
    two tangential coefficients appear.
    """
    if fn < 0.0:
        return False
    if condim == 1:
        return True
    return fn * fn >= (fy * fy) / (mu_y * mu_y) + (fz * fz) / (mu_z * mu_z)


def in_pyramid(fn, fy, fz, mu_y, mu_z, condim):
    """Documented pyramidal cone, mapped to contact-frame force.

    For n=1: the non-negative ray. For n>1 the documented set is
    non-negative edge coefficients in R^{2(n-1)}. Each edge combines a
    normal component and one frictional component, scaled to lie in the
    elliptic cone. For n=3 the four edges are the directions
    (1, +-mu_y, 0) and (1, 0, +-mu_z). A contact-frame force is in the
    pyramid iff fn >= 0 and |fy|/mu_y + |fz|/mu_z <= fn.
    """
    if fn < 0.0:
        return False
    if condim == 1:
        return True
    return (abs(fy) / mu_y) + (abs(fz) / mu_z) <= fn


def in_unbounded(fn, fy, fz, mu_y, mu_z, condim):
    """Lose arm: friction treated as unbounded; only fn >= 0 is required.

    Drops the normal-component coupling of the pyramid edges. The
    tangential components and condim are ignored.
    """
    del fy, fz, mu_y, mu_z, condim
    return fn >= 0.0


MEMBER = {
    "A_elliptic": in_elliptic,
    "B_pyramid": in_pyramid,
    "C_unbounded": in_unbounded,
}


def shared_samples(regime, seed, mu_y=MU_Y, mu_z=MU_Z, n_sample=N_SAMPLE):
    """Shared candidate contact-frame forces and slip velocities (CRN)."""
    rng = rng_for(regime, seed, "samples")
    samples = []
    if regime == "frictionless":
        # Scalar normal samples only; documented n=1 cone is the ray.
        for i in range(n_sample):
            # Mix of positive, near-zero and a few negative normals.
            bucket = i % 8
            if bucket == 0:
                fn = -abs(rng.uniform(0.05, 0.80)) * FN_SCALE
            else:
                fn = abs(rng.uniform(0.05, 1.40)) * FN_SCALE
            # Tangential slots are unused at condim=1; still drawn and shared.
            # Tangential slots and slip are unused at condim=1; drawn as zero
            # so they are still shared, but they do not enter the ray test.
            fy = 0.0
            fz = 0.0
            vy = 0.0
            vz = 0.0
            samples.append((fn, fy, fz, vy, vz))
        return samples

    for i in range(n_sample):
        fn = abs(rng.uniform(0.40, 1.60)) * FN_SCALE
        # Shared slip velocity (tag only; membership is on force).
        angle_v = rng.uniform(0.0, 2.0 * math.pi)
        speed = rng.uniform(0.00, 1.20)
        vy = speed * math.cos(angle_v)
        vz = speed * math.sin(angle_v)
        if regime == "mid_tangential":
            bucket = i % 5
            # 0: clearly inside both (axis-aligned, small tangent)
            # 1: elliptic-in, pyramid-out (diagonal, between L1 and L2)
            # 2: well inside both on a diagonal (below the L1 bound)
            # 3: outside both (beyond the ellipse)
            # 4: negative normal (outside both)
            if bucket == 4:
                fn = -abs(rng.uniform(0.20, 1.00)) * FN_SCALE
                radius = rng.uniform(0.10, 0.40)
                ang = rng.uniform(0.0, 2.0 * math.pi)
                fy = radius * mu_y * abs(fn) * math.cos(ang)
                fz = radius * mu_z * abs(fn) * math.sin(ang)
            elif bucket == 0:
                # Axis-aligned, 0.30..0.70 of the axial friction limit.
                axis = rng.choice((-1, 1))
                frac = rng.uniform(0.30, 0.70)
                if rng.random() < 0.5:
                    fy, fz = axis * frac * mu_y * fn, 0.0
                else:
                    fy, fz = 0.0, axis * frac * mu_z * fn
            elif bucket == 1:
                # 45-degree diagonal, radius in (0.5*sqrt(2), 1) of the
                # elliptic bound so L2 holds and L1 fails.
                # |fy|/(mu_y fn) = |fz|/(mu_z fn) = r / sqrt(2);
                # L2: r <= 1; L1: 2*(r/sqrt(2)) = r*sqrt(2) <= 1 => r <= 1/sqrt(2).
                r = rng.uniform(0.78, 0.96)
                sign_y = rng.choice((-1, 1))
                sign_z = rng.choice((-1, 1))
                u = r / math.sqrt(2.0)
                fy = sign_y * u * mu_y * fn
                fz = sign_z * u * mu_z * fn
            elif bucket == 2:
                r = rng.uniform(0.20, 0.55)
                ang = rng.uniform(0.0, 2.0 * math.pi)
                fy = r * mu_y * fn * math.cos(ang)
                fz = r * mu_z * fn * math.sin(ang)
            else:
                r = rng.uniform(1.15, 1.80)
                ang = rng.uniform(0.0, 2.0 * math.pi)
                fy = r * mu_y * fn * math.cos(ang)
                fz = r * mu_z * fn * math.sin(ang)
        else:
            # high_tangential: mostly outside both documented cones.
            bucket = i % 6
            if bucket == 0:
                # a few legal, small-tangent holds
                r = rng.uniform(0.10, 0.40)
                ang = rng.uniform(0.0, 2.0 * math.pi)
                fy = r * mu_y * fn * math.cos(ang)
                fz = r * mu_z * fn * math.sin(ang)
            else:
                r = rng.uniform(1.40, 2.80)
                ang = rng.uniform(0.0, 2.0 * math.pi)
                fy = r * mu_y * fn * math.cos(ang)
                fz = r * mu_z * fn * math.sin(ang)
        samples.append((fn, fy, fz, vy, vz))
    return samples


def classify_sample(fn, fy, fz, mu_y, mu_z, condim):
    return {
        "A_elliptic": in_elliptic(fn, fy, fz, mu_y, mu_z, condim),
        "B_pyramid": in_pyramid(fn, fy, fz, mu_y, mu_z, condim),
        "C_unbounded": in_unbounded(fn, fy, fz, mu_y, mu_z, condim),
    }


def evaluate(regime, seed, mu_y=MU_Y, mu_z=MU_Z, n_sample=N_SAMPLE):
    condim = CONDIM_FREE if regime == "frictionless" else CONDIM_FRIC
    samples = shared_samples(regime, seed, mu_y=mu_y, mu_z=mu_z, n_sample=n_sample)
    rows = {arm: {"admit": 0, "illegal_admit": 0} for arm in ARMS}
    n_ell_in_pyr_out = 0
    n_pyr_in_ell_out = 0
    example = None
    n_sliding = 0
    for fn, fy, fz, vy, vz in samples:
        if (vy * vy + vz * vz) ** 0.5 > 1e-9:
            n_sliding += 1
        flags = classify_sample(fn, fy, fz, mu_y, mu_z, condim)
        ell, pyr = flags["A_elliptic"], flags["B_pyramid"]
        if ell and not pyr:
            n_ell_in_pyr_out += 1
            if example is None:
                example = ("ell_in_pyr_out", fn, fy, fz)
        if pyr and not ell:
            n_pyr_in_ell_out += 1
            if example is None or example[0] != "ell_in_pyr_out":
                example = ("pyr_in_ell_out", fn, fy, fz)
        for arm in ARMS:
            admitted = flags[arm]
            if admitted:
                rows[arm]["admit"] += 1
                if not ell:
                    rows[arm]["illegal_admit"] += 1
    n = len(samples)
    out = {
        "condim": condim,
        "n_sample": n,
        "n_sliding": n_sliding,
        "n_ell_in_pyr_out": n_ell_in_pyr_out,
        "n_pyr_in_ell_out": n_pyr_in_ell_out,
        "example": example,
        "arms": {},
    }
    for arm in ARMS:
        admit = rows[arm]["admit"]
        illegal = rows[arm]["illegal_admit"]
        out["arms"][arm] = {
            "admit": admit,
            "admit_rate": admit / n,
            "illegal_admit": illegal,
            "illegal_admit_rate": illegal / n,
        }
    return out


def run_regime(name, seed, mu_y=MU_Y, mu_z=MU_Z, n_sample=N_SAMPLE):
    ev = evaluate(name, seed, mu_y=mu_y, mu_z=mu_z, n_sample=n_sample)
    ev["seed"] = seed
    ev["mu_y"] = mu_y
    ev["mu_z"] = mu_z
    return ev


def official_rows(name, mu_y=MU_Y, mu_z=MU_Z, n_sample=N_SAMPLE):
    return [run_regime(name, seed, mu_y=mu_y, mu_z=mu_z, n_sample=n_sample) for seed in SEEDS]


def print_regime(title, rows):
    print(f"regime {title}  (mean+-sd over seeds)")
    condim = rows[0]["condim"]
    print(
        f"  condim={condim} elliptic_dims={elliptic_dims(condim)} "
        f"pyramidal_dims={pyramidal_dims(condim)} "
        f"n_sample={rows[0]['n_sample']}"
    )
    ell_out = [r["n_ell_in_pyr_out"] for r in rows]
    pyr_out = [r["n_pyr_in_ell_out"] for r in rows]
    sliding = [r["n_sliding"] for r in rows]
    print(
        f"  discrepancy ell_in_pyr_out {num(mean_sd(ell_out)[0])}+-{num(mean_sd(ell_out)[1])} "
        f"pyr_in_ell_out {num(mean_sd(pyr_out)[0])}+-{num(mean_sd(pyr_out)[1])} "
        f"n_sliding {num(mean_sd(sliding)[0])}+-{num(mean_sd(sliding)[1])}"
    )
    # Print one documented discrepancy sample from seed 0, if any.
    ex = rows[0]["example"]
    if ex is not None:
        kind, fn, fy, fz = ex
        mu_y, mu_z = rows[0]["mu_y"], rows[0]["mu_z"]
        print(
            f"  example {kind} seed=0 fn={num(fn)} fy={num(fy)} fz={num(fz)} "
            f"ell={int(in_elliptic(fn, fy, fz, mu_y, mu_z, condim))} "
            f"pyr={int(in_pyramid(fn, fy, fz, mu_y, mu_z, condim))}"
        )
    else:
        print("  example none")
    for arm in ARMS:
        admit = [r["arms"][arm]["admit_rate"] for r in rows]
        illegal = [r["arms"][arm]["illegal_admit_rate"] for r in rows]
        ac, asd = mean_sd(admit)
        ic, isd = mean_sd(illegal)
        print(
            f"  {arm} admit_rate {num(ac)}+-{num(asd)} "
            f"illegal_admit_rate {num(ic)}+-{num(isd)}"
        )
    for left, right in PAIRS:
        la = {"A": "A_elliptic", "B": "B_pyramid", "C": "C_unbounded"}[left]
        ra = {"A": "A_elliptic", "B": "B_pyramid", "C": "C_unbounded"}[right]
        for key in METRICS:
            xa = [r["arms"][la][key] for r in rows]
            xb = [r["arms"][ra][key] for r in rows]
            print(f"  paired {left}-{right} {key}: {verdict(xa, xb)}")


def main():
    print("Stdlib stand-in of documented elliptic vs pyramidal friction cones; not mujoco.step")
    print(
        f"declared MU_Y={num(MU_Y)} MU_Z={num(MU_Z)} N_SAMPLE={N_SAMPLE} "
        f"FN_SCALE={num(FN_SCALE)} SMALL_FRAC={num(SMALL_FRAC)} "
        f"seeds={','.join(str(s) for s in SEEDS)}"
    )
    print(
        "declared arms: A_elliptic documented elliptic inequality; "
        "B_pyramid documented pyramid edge span; "
        "C_unbounded friction treated as unbounded (fn >= 0 only)"
    )
    print(
        f"declared condim frictional {CONDIM_FRIC}: elliptic_dims="
        f"{elliptic_dims(CONDIM_FRIC)} pyramidal_dims={pyramidal_dims(CONDIM_FRIC)}"
    )
    print(
        f"declared condim frictionless {CONDIM_FREE}: elliptic_dims="
        f"{elliptic_dims(CONDIM_FREE)} pyramidal_dims={pyramidal_dims(CONDIM_FREE)}"
    )
    print(f"hand_calc pyramid edges 2*(condim-1) at condim=3 = {num(float(2 * (CONDIM_FRIC - 1)))}")
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    # Worked mid-diagonal membership, 以文档为准 inequalities, not a toy measurement.
    fn_h, u_h = 1.0000, 0.8500 / math.sqrt(2.0)
    fy_h = u_h * MU_Y * fn_h
    fz_h = u_h * MU_Z * fn_h
    ell_lhs = (fy_h / MU_Y) ** 2 + (fz_h / MU_Z) ** 2
    pyr_lhs = abs(fy_h) / MU_Y + abs(fz_h) / MU_Z
    print(
        f"hand_calc mid-diagonal fn={num(fn_h)} mu={num(MU_Y)} r=0.8500 "
        f"fy={num(fy_h)} fz={num(fz_h)} "
        f"elliptic_sum_sq={num(ell_lhs)} pyramid_l1={num(pyr_lhs)} "
        f"ell_in={int(ell_lhs <= fn_h * fn_h)} pyr_in={int(pyr_lhs <= fn_h)}"
    )
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: the force and slip-velocity samples are shared across arms at each regime and seed")
    print("Assumptions: stdlib inequality stand-in, not mujoco.step, not a redo of grip_sweep, not a third cone")
    print("Documented cone sets and condim dimensions 以文档为准")
    print("Real MuJoCo / mujoco.step / second grip scene: 本页未运行")
    print("declared frictionless: A and B may tie or near-tie on admission - keep")
    print("declared mid_tangential: print elliptic-vs-pyramid discrepancy and keep the sign - keep")
    print("declared high_tangential: C loses (unbounded friction) - keep")
    for name, decl in REGIMES.items():
        print(f"declared expectation {name}: {decl}")
        print_regime(name, official_rows(name))

    print("alternative same seeds MU_Y=MU_Z=1.0000 (not adopted)")
    for name in REGIMES:
        print_regime(f"{name} alt_MU=1.0000", official_rows(name, mu_y=1.0000, mu_z=1.0000))

    print("No mujoco.step was called")
    print("No winner is universal: frictionless admission can tie; a documented elliptic-in pyramid-out sample is a set difference, not a ranking")


if __name__ == "__main__":
    main()
