#!/usr/bin/env python3
"""Synthetic first-order form-closure vs force-closure on a shared 2-D square.

Stdlib only. The object is a square of half-width 1 centred at the origin.
Frictionless contact wrenches are w = (nx, ny, px*ny - py*nx) with inward
normals. A first-order escape twist t exists iff some t != 0 has w_i · t >= 0
for every wrench (the gap-function test psi(u+du, q) >= 0 not implying du = 0).
Force-closure uses the two Coulomb cone-edge wrenches at each contact.

Arms (shared polygon; contact jitter along the edges is shared):
  A_three       3 contacts (right, top, left) — under-constrained at mu=0
  B_four        4 edge contacts, cyclically offset from the mid-points — form-closing at mu=0
  C_two_finger  2 antipodal contacts (left, right) — force-closure with mu>0,
                not form-closure (escapes at mu=0)

Regimes (declared before the first run):
  mu0_form         mu=0; B immobilizes, A and C escape  -> B consistent win
  large_mu_force   mu=1; C may tie A/B on force-closure; form-closure still fails for C
  aligned_normals  4 contacts on only the left and right edges (aligned normals);
                   4 is necessary, not sufficient -> this 4-contact set loses form-closure

Common random numbers: per-seed edge fractions are drawn once and reused by
every arm on that seed. Seeds 0-4.

No integration step: first-order algebraic wrench test, no time discretisation.
Not the Ferrari-Canny epsilon / antipodal force-closure toy on perception-to-grasp.
Not fingertip material, not a press-fit. Real gripper: 本页未运行.
Paper contact counts 以论文为准 (Carpin, Liu, Falco, Van Wyk, arXiv 1607.06620 §2.5;
Zhang, Tang, Sun, Lan, arXiv 2202.03631 Def. 1).
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
HALF = 1.0
JITTER = 0.15  # fraction units about the nominal edge parameter
JITTER_ALT = 0.05
MU = 1.0
MU_ALT = 0.2
EPS = 1e-12
ARMS = ("A_three", "B_four", "C_two_finger")
# written before the first run
REGIMES = ("mu0_form", "large_mu_force", "aligned_normals")
STREAM = {"layout_abc": 0, "aligned_normals": 1, "jitter_alt": 2, "mid_edge_posthoc": 3}
# mu0_form and large_mu_force share layout_abc so only mu changes
# paper counts, not measured by this planar toy
PAPER_MIN_2D = 4
PAPER_MIN_3D = 7

# edge name -> (origin_point, tangent, inward normal, length)
# parameter s in [0, 1] runs along the tangent; s=0.5 is the midpoint.
EDGES = {
    "right":  ((HALF, -HALF), (0.0, 2.0 * HALF), (-1.0, 0.0)),
    "top":    ((-HALF, HALF), (2.0 * HALF, 0.0), (0.0, -1.0)),
    "left":   ((-HALF, HALF), (0.0, -2.0 * HALF), (1.0, 0.0)),
    "bottom": ((-HALF, -HALF), (2.0 * HALF, 0.0), (0.0, 1.0)),
}


def contact(edge: str, s: float) -> tuple[tuple[float, float], tuple[float, float]]:
    (ox, oy), (tx, ty), n = EDGES[edge]
    return (ox + s * tx, oy + s * ty), n


def wrench(p: tuple[float, float], fxy: tuple[float, float]) -> tuple[float, float, float]:
    fx, fy = fxy
    px, py = p
    return (fx, fy, px * fy - py * fx)


def frictionless_wrenches(contacts: list[tuple[tuple[float, float], tuple[float, float]]]):
    return [wrench(p, n) for p, n in contacts]


def cone_wrenches(contacts, mu: float):
    out = []
    for p, n in contacts:
        nx, ny = n
        # tangent: rotate the inward normal 90 deg
        tx, ty = -ny, nx
        if mu == 0.0:
            out.append(wrench(p, n))
        else:
            out.append(wrench(p, (nx + mu * tx, ny + mu * ty)))
            out.append(wrench(p, (nx - mu * tx, ny - mu * ty)))
    return out


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(a):
    return math.sqrt(dot(a, a))


def escape_twist(wrenches, eps: float = EPS):
    """Return a unit first-order escape twist, or None if the cone is {0}."""
    n = len(wrenches)
    if n == 0:
        return (1.0, 0.0, 0.0)
    # Rank-deficient: a direction orthogonal to span(w_i) has all gap rates 0.
    # Build an orthonormal basis of the span via Gram-Schmidt, then take a
    # complement if the span is not all of R^3.
    basis = []
    for w in wrenches:
        v = list(w)
        for b in basis:
            s = dot(v, b)
            v = [v[k] - s * b[k] for k in range(3)]
        nv = norm(v)
        if nv > eps:
            basis.append(tuple(x / nv for x in v))
    if len(basis) < 3:
        # a complement vector
        for e in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)):
            v = list(e)
            for b in basis:
                s = dot(v, b)
                v = [v[k] - s * b[k] for k in range(3)]
            nv = norm(v)
            if nv > eps:
                return tuple(x / nv for x in v)
    # Extreme rays of {t | W t >= 0} lie in intersections of two planes w_i·t=0.
    for i in range(n):
        for j in range(i + 1, n):
            t = cross(wrenches[i], wrenches[j])
            nt = norm(t)
            if nt < eps:
                continue
            t = tuple(x / nt for x in t)
            for sign in (1.0, -1.0):
                ts = tuple(sign * x for x in t)
                if all(dot(w, ts) >= -eps for w in wrenches):
                    return ts
    return None


def is_closed(wrenches) -> float:
    return 0.0 if escape_twist(wrenches) is not None else 1.0


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    if len(xs) == 1:
        return mu, 0.0
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
    if x != 0.0 and abs(x) < 5e-5:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs: list[float], m: float) -> str:
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def verdict(xa: list[float], xb: list[float]) -> str:
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


# Cyclic offset from mid-edge: mid-edge contacts on a square have r || n, so
# the first-order moment is zero and a pure rotation is an "escape". Offsets
# are written before the first run; jitter stays on the same side of mid-edge.
NOMINAL_B = (("right", 0.75), ("top", 0.75), ("left", 0.75), ("bottom", 0.25))
NOMINAL_C = (("left", 0.50), ("right", 0.50))
NOMINAL_ALIGNED = (("left", 0.30), ("left", 0.70), ("right", 0.30), ("right", 0.70))


def jittered_s(rng: random.Random, nominal: float, jitter: float) -> float:
    u = rng.uniform(-1.0, 1.0)
    s = nominal + jitter * u
    return min(0.95, max(0.05, s))


def layout(spec, rng: random.Random, jitter: float):
    return [contact(edge, jittered_s(rng, s0, jitter)) for edge, s0 in spec]


def stream_key(regime: str) -> str:
    if regime == "aligned_normals":
        return "aligned_normals"
    return "layout_abc"


def shared_contacts(regime: str, seed: int, jitter: float) -> dict[str, list]:
    rng = random.Random(1000 * STREAM[stream_key(regime)] + seed)
    if regime == "aligned_normals":
        four = layout(NOMINAL_ALIGNED, rng, jitter)
        return {"B_aligned": four, "A_three": four[:3], "B_four": four, "C_two_finger": four[:2]}
    # One pool of jittered parameters, reused by every arm (common random numbers).
    four = layout(NOMINAL_B, rng, jitter)
    # C is a two-finger mid-edge grasp. Its two jitter draws are taken from the
    # same RNG after the four B draws so C does not steal B's offsets. A uses
    # B's first three contacts (under-constrained).
    two = layout(NOMINAL_C, rng, jitter)
    return {
        "A_three": four[:3],
        "B_four": four,
        "C_two_finger": two,
    }


def evaluate(contacts, mu: float) -> dict[str, float]:
    form = is_closed(frictionless_wrenches(contacts))
    force = is_closed(cone_wrenches(contacts, mu))
    return {"form": form, "force": force, "n": float(len(contacts))}


def seed_rows(regime: str, mu: float, jitter: float) -> dict[str, list[dict[str, float]]]:
    rows = {arm: [] for arm in list(ARMS) + (["B_aligned"] if regime == "aligned_normals" else [])}
    for seed in SEEDS:
        cons = shared_contacts(regime, seed, jitter)
        for arm in rows:
            rows[arm].append(evaluate(cons[arm], mu))
    return rows


def col(rows: list[dict[str, float]], key: str) -> list[float]:
    return [r[key] for r in rows]


def main() -> None:
    print("Synthetic form-closure toy on a shared 2-D square; first-order gap test; not Ferrari-Canny epsilon, not a press-fit")
    print(f"half_width={HALF} jitter={JITTER} alt_jitter={JITTER_ALT} mu={MU} alt_mu={MU_ALT} seeds={len(SEEDS)}")
    print("no integration step: first-order algebraic wrench test (escape twist or none); no time discretisation")
    print(f"paper_min_frictionless_wrenches_2d_polygon={PAPER_MIN_2D} (Zhang, Tang, Sun, Lan, arXiv 2202.03631; 以论文为准)")
    print(f"paper_min_contact_points_3d={PAPER_MIN_3D} (Somov as stated by Carpin, Liu, Falco, Van Wyk, arXiv 1607.06620 §2.5; Zhang et al. for 3-D polygons; 以论文为准, not measured on this planar toy)")

    # Nominal (no jitter) witness, seed-independent, printed for the prose
    nom = {
        "A_three": [contact(e, s) for e, s in NOMINAL_B[:3]],
        "B_four": [contact(e, s) for e, s in NOMINAL_B],
        "C_two_finger": [contact(e, s) for e, s in NOMINAL_C],
        "B_aligned": [contact(e, s) for e, s in NOMINAL_ALIGNED],
    }
    for name, cons in nom.items():
        esc0 = escape_twist(frictionless_wrenches(cons))
        form0 = 0.0 if esc0 is not None else 1.0
        force1 = is_closed(cone_wrenches(cons, MU))
        esc_s = "none" if esc0 is None else f"({esc0[0]:+.4f}, {esc0[1]:+.4f}, {esc0[2]:+.4f})"
        print(f"nominal {name} n={len(cons)} form_mu0={form0:.0f} force_mu{MU:g}={force1:.0f} escape_mu0={esc_s}")

    for regime in REGIMES:
        mu = 0.0 if regime == "mu0_form" else MU
        tag = { "mu0_form": "mu=0, form-closure test",
                "large_mu_force": f"mu={MU}, force-closure test (form still at mu=0 on the same contacts)",
                "aligned_normals": "4 contacts on two opposite sides, aligned normals, mu=0" }[regime]
        print(f"{regime} ({tag})")
        rows = seed_rows(regime, mu, JITTER)
        form0_rows = seed_rows(regime, 0.0, JITTER)  # form-closure is always the mu=0 test
        arms_here = ["B_aligned"] if regime == "aligned_normals" else list(ARMS)
        if regime == "aligned_normals":
            # also show A/C slices? keep B_aligned as the declared fail cell
            for arm in ("B_aligned",):
                fcol, qcol = col(form0_rows[arm], "form"), col(rows[arm], "force")
                print(f"  {arm} form_mu0 {num(mean_sd(fcol)[0])}+-{num(mean_sd(fcol)[1])} force_mu{mu:g} {num(mean_sd(qcol)[0])}+-{num(mean_sd(qcol)[1])}")
            # Compare aligned 4-contact vs a proper 4-contact set on the same seeds
            proper = seed_rows("mu0_form", 0.0, JITTER)
            print(f"  paired B_four-B_aligned form_mu0: {verdict(col(proper['B_four'], 'form'), col(form0_rows['B_aligned'], 'form'))}")
        else:
            for arm in ARMS:
                fcol, qcol = col(form0_rows[arm], "form"), col(rows[arm], "force")
                print(f"  {arm} form_mu0 {num(mean_sd(fcol)[0])}+-{num(mean_sd(fcol)[1])} force_at_regime_mu {num(mean_sd(qcol)[0])}+-{num(mean_sd(qcol)[1])}")
            print(f"  paired B-A form_mu0: {verdict(col(form0_rows['B_four'], 'form'), col(form0_rows['A_three'], 'form'))}")
            print(f"  paired B-C form_mu0: {verdict(col(form0_rows['B_four'], 'form'), col(form0_rows['C_two_finger'], 'form'))}")
            print(f"  paired C-A force_at_regime_mu: {verdict(col(rows['C_two_finger'], 'force'), col(rows['A_three'], 'force'))}")
            print(f"  paired C-B force_at_regime_mu: {verdict(col(rows['C_two_finger'], 'force'), col(rows['B_four'], 'force'))}")

    # Alternatives on the same mu0 / large_mu streams
    rows_j = seed_rows("mu0_form", 0.0, JITTER_ALT)
    print(f"alternative jitter={JITTER_ALT} on mu0_form (same seed keys, narrower edge draws)")
    print(f"  paired B-A form_mu0: {verdict(col(rows_j['B_four'], 'form'), col(rows_j['A_three'], 'form'))}")
    rows_m = seed_rows("large_mu_force", MU_ALT, JITTER)
    form_m = seed_rows("large_mu_force", 0.0, JITTER)
    print(f"alternative mu={MU_ALT} on large_mu_force (same contacts as mu={MU})")
    for arm in ARMS:
        print(f"  {arm} force {num(mean_sd(col(rows_m[arm], 'force'))[0])}+-{num(mean_sd(col(rows_m[arm], 'force'))[1])}")
    print(f"  paired C-A force: {verdict(col(rows_m['C_two_finger'], 'force'), col(rows_m['A_three'], 'force'))}")
    print(f"  paired C-B force: {verdict(col(rows_m['C_two_finger'], 'force'), col(rows_m['B_four'], 'force'))}")
    print(f"  paired B-C form_mu0 (unchanged by mu): {verdict(col(form_m['B_four'], 'form'), col(form_m['C_two_finger'], 'form'))}")

    # Mid-edge 4-contact layout (tried first; first-order moments vanish; disclosed)
    mid_spec = (("right", 0.50), ("top", 0.50), ("left", 0.50), ("bottom", 0.50))
    mid_nom = [contact(e, s) for e, s in mid_spec]
    esc_mid = escape_twist(frictionless_wrenches(mid_nom))
    esc_s = "none" if esc_mid is None else f"({esc_mid[0]:+.4f}, {esc_mid[1]:+.4f}, {esc_mid[2]:+.4f})"
    print(f"alternative four mid-edge contacts (tried first; first-order moments vanish; disclosed) nominal form_mu0={is_closed(frictionless_wrenches(mid_nom)):.0f} escape_mu0={esc_s}")
    b_forms = col(seed_rows("mu0_form", 0.0, JITTER)["B_four"], "form")
    mid_forms = []
    for seed in SEEDS:
        rng = random.Random(1000 * STREAM["mid_edge_posthoc"] + seed)
        mid = [contact(edge, jittered_s(rng, 0.50, JITTER)) for edge, _ in mid_spec]
        mid_forms.append(is_closed(frictionless_wrenches(mid)))
    print(f"  jittered mid-edge form_mu0 {num(mean_sd(mid_forms)[0])}+-{num(mean_sd(mid_forms)[1])}")
    print(f"  paired B_four-mid_edge form_mu0: {verdict(b_forms, mid_forms)}")
    print("No winner declared: four well-placed frictionless contacts immobilize the square; two frictional fingers can be force-closure without being form-closure; four aligned normals are not enough")
    print("Real gripper: 本页未运行; contact counts 以论文为准")


if __name__ == "__main__":
    main()
