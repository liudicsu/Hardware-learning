#!/usr/bin/env python3
"""GraspVLA-style synthetic pre-training: geometry only vs grounding-first chain on randomised synthetic data vs no DR vs shuffled labels.

Synthetic appearance vectors and a nearest-sample grounding step, stdlib
only.  Not GraspVLA, not SynGrasp-1B, not a VLM, not flow matching and not
the force-closure / epsilon toy above; no weights, no GPU, no Isaac Sim, no
LIBERO and no real grasp cell: 本页未运行.  Paper statements and numbers
(arXiv 2505.03233, for example its billion frames or its success rates)
以论文为准; nothing here reproduces them.

What the paper body says (and what this toy keeps): SynGrasp-1B is rendered
in simulation with domain randomisation of materials, lighting, camera views
and backgrounds; GraspVLA's Progressive Action Generation is a chain of
thought that first predicts a 2-D bounding box of the named object, then a
grasp pose, then an action chunk.  Internet grounding data supervises only
the bounding-box step, which is how categories that never appear in the
synthetic action data become graspable (open vocabulary).

Toy: a scene holds N_OBJ objects of distinct categories; the instruction
names one.  Each category has a prototype appearance vector; a rendering
domain applies a per-dimension gain and offset plus noise.  The real test
domain is one fixed gain / offset.  Categories 0..S_CAT-1 are "synthetic"
(they have synthetic action data); S_CAT..S_CAT+W_CAT-1 are "web" categories
that appear only in the Internet grounding set (rendered with varied gains,
like photos).  Grounding = pick the object whose appearance is nearest to
any training sample labelled with the named category (box step).  Grasp =
a shared geometric step: the grasp succeeds iff the chosen object is the
named one and its observed orientation error is < ORI_TOL (strict).
Arms:
  A_geom     : no language: picks the object with the best geometric score
  B_cot_dr   : grounding-first chain; synthetic samples rendered with DR,
               plus the Internet grounding set
  C_no_dr    : same chain, synthetic samples rendered in ONE canonical domain
  D_shuffled : same as B but every category label is shifted by one
               (a derangement) in both training sets

Common random numbers: for each seed one set of prototypes, one Internet
set and one set of synthetic draws (instances, noise, DR gains) is drawn
once; B, C and D see the same draws and differ only in the rendering domain
or the labels.  For each (regime, seed) one list of scenes (categories,
target, test noise, geometric scores, orientation errors) is shared by
every arm.
No integration step: no dynamics, no ODE, no time-step criterion.

Regimes and parameters were written before the first run:
  in_family     : N_OBJ objects from synthetic categories, real domain
                  - B consistent better than A; keep C and D if they lose
  web_category  : the named object is a web category, distractors synthetic
                  - B consistent better than A (open vocabulary); C may tie B
                    because web samples never needed DR; keep
  single_object : one object only, nothing to ground
                  - A and B may near-tie (or tie); keep
Alternatives, also written before the first run, on the same seeds:
  narrow DR (gain 0.9..1.1, offset -0.1..0.1) instead of the wide range (in_family);
  N_OBJ = 5 instead of 3 (in_family).
All dimensions, gains, offsets, counts and tolerances are declared toy parameters.
Code change after the first run: only the closing "No winner declared" line.
It first said the chain "needs DR on the synthetic side"; the first run showed
C_no_dr near-tying B on in_family and tying it on web_category, so the line
now says the no-DR arm did not lose.  No parameter, regime or number changed.
"""
from __future__ import annotations

import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
DIM = 8                  # appearance vector length (toy)
S_CAT = 6                # synthetic categories with action data (toy)
W_CAT = 4                # web-only categories (toy)
N_PER = 30               # training samples per category and source (toy)
INST_SIGMA = 0.15        # per-instance appearance spread (toy)
PIX_SIGMA = 0.05         # rendering noise (toy)
DR_GAIN = (0.4, 1.6)     # synthetic domain randomisation, gain range (toy)
DR_OFF = (-0.5, 0.5)     # synthetic domain randomisation, offset range (toy)
WEB_GAIN = (0.5, 1.5)    # Internet photos, gain range (toy)
WEB_OFF = (-0.4, 0.4)    # Internet photos, offset range (toy)
REAL_GAIN, REAL_OFF = 0.6, 0.35   # the fixed real test domain (toy)
N_OBJ = 3
N_SCENES = 60
ORI_SIGMA = 5.0          # deg, observed orientation error sd (toy)
ORI_TOL = 10.0           # deg, grasp succeeds iff orientation error < ORI_TOL
ARMS = ("A_geom", "B_cot_dr", "C_no_dr", "D_shuffled")
REGIMES = ("in_family", "web_category", "single_object")
METRICS = ("pick_ok", "success")


def prototypes(seed):
    rng = random.Random(f"graspvla-proto|{seed}")
    return [[rng.uniform(0.0, 1.0) for _ in range(DIM)] for _ in range(S_CAT + W_CAT)]


def render(proto, gain, off, inst, noise):
    return [gain * (p + i) + off + n for p, i, n in zip(proto, inst, noise)]


def train_draws(seed):
    """Shared by B, C and D: synthetic instances, noise and DR gains, and the Internet set."""
    rng = random.Random(f"graspvla-train|{seed}")
    syn = []
    for c in range(S_CAT):
        for _ in range(N_PER):
            inst = [rng.gauss(0.0, INST_SIGMA) for _ in range(DIM)]
            noise = [rng.gauss(0.0, PIX_SIGMA) for _ in range(DIM)]
            u_gain, u_off = rng.random(), rng.random()
            syn.append((c, inst, noise, u_gain, u_off))
    web = []
    for c in range(S_CAT, S_CAT + W_CAT):
        for _ in range(N_PER):
            inst = [rng.gauss(0.0, INST_SIGMA) for _ in range(DIM)]
            noise = [rng.gauss(0.0, PIX_SIGMA) for _ in range(DIM)]
            gain, off = rng.uniform(*WEB_GAIN), rng.uniform(*WEB_OFF)
            web.append((c, inst, noise, gain, off))
    return syn, web


def train_set(arm, seed, dr=(DR_GAIN, DR_OFF)):
    protos = prototypes(seed)
    syn, web = train_draws(seed)
    out = []
    for c, inst, noise, u_gain, u_off in syn:
        if arm == "C_no_dr":
            gain, off = 1.0, 0.0
        else:
            gain = dr[0][0] + (dr[0][1] - dr[0][0]) * u_gain
            off = dr[1][0] + (dr[1][1] - dr[1][0]) * u_off
        out.append((c, render(protos[c], gain, off, inst, noise)))
    for c, inst, noise, gain, off in web:
        out.append((c, render(protos[c], gain, off, inst, noise)))
    if arm == "D_shuffled":
        out = [((c + 1) % (S_CAT + W_CAT), x) for c, x in out]
    return out


def test_scenes(regime, seed, n_obj=N_OBJ):
    rng = random.Random(f"graspvla-test|{regime}|{seed}|{n_obj}")
    protos = prototypes(seed)
    out = []
    for _ in range(N_SCENES):
        k = 1 if regime == "single_object" else n_obj
        if regime == "web_category":
            cats = [S_CAT + rng.randrange(W_CAT)] + rng.sample(range(S_CAT), k - 1)
        else:
            cats = rng.sample(range(S_CAT), k)
        target = 0                               # cats[0] is the named object
        objs = []
        for c in cats:
            inst = [rng.gauss(0.0, INST_SIGMA) for _ in range(DIM)]
            noise = [rng.gauss(0.0, PIX_SIGMA) for _ in range(DIM)]
            app = render(protos[c], REAL_GAIN, REAL_OFF, inst, noise)
            geom = rng.random()                   # geometric graspability score, category-blind
            ori = abs(rng.gauss(0.0, ORI_SIGMA))  # observed orientation error, deg
            objs.append((c, app, geom, ori))
        order = list(range(k))
        rng.shuffle(order)                        # object order in the scene is random
        objs = [objs[i] for i in order]
        out.append((cats[target], objs))
    return out


def dist2(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def pick(arm, train, named, objs):
    if arm == "A_geom" or len(objs) == 1:
        return max(range(len(objs)), key=lambda i: objs[i][2])
    pool = [x for c, x in train if c == named]
    return min(range(len(objs)), key=lambda i: min(dist2(objs[i][1], x) for x in pool))


def evaluate(arm, regime, seed, train, n_obj=N_OBJ):
    picks, ok = 0, 0
    for named, objs in test_scenes(regime, seed, n_obj):
        i = pick(arm, train, named, objs)
        right = objs[i][0] == named
        picks += 1 if right else 0
        ok += 1 if right and objs[i][3] < ORI_TOL else 0
    return {"pick_ok": picks / N_SCENES, "success": ok / N_SCENES}


def mean_sd(xs):
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


_TRAIN = {}


def trained(arm, seed, dr=(DR_GAIN, DR_OFF)):
    key = (arm, seed, dr)
    if key not in _TRAIN:
        _TRAIN[key] = train_set(arm, seed, dr)
    return _TRAIN[key]


def collect(regime, dr=(DR_GAIN, DR_OFF), n_obj=N_OBJ):
    return {arm: [evaluate(arm, regime, s, trained(arm, s, dr), n_obj) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [r[key] for r in rows]


def pairs(res, suffix=""):
    for key in METRICS:
        print(f"  paired B-A {key}{suffix}: {verdict(col(res['B_cot_dr'], key), col(res['A_geom'], key))}")
    for other, tag in (("C_no_dr", "C"), ("D_shuffled", "D")):
        print(f"  paired {tag}-B success{suffix}: {verdict(col(res[other], 'success'), col(res['B_cot_dr'], 'success'))}")


def report(regime):
    res = collect(regime)
    print(f"{regime}:")
    for arm in ARMS:
        parts = [f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS]
        print(f"  {arm} " + " ".join(parts))
    pairs(res)


def main():
    print("Synthetic appearance-vector toy with nearest-sample grounding; geometry only vs grounding-first chain with DR vs no DR vs shuffled labels; not GraspVLA")
    print(f"seeds={len(SEEDS)} DIM={DIM} S_CAT={S_CAT} W_CAT={W_CAT} N_PER={N_PER} N_OBJ={N_OBJ} N_SCENES={N_SCENES} "
          f"INST_SIGMA={INST_SIGMA:.2f} PIX_SIGMA={PIX_SIGMA:.2f} (declared toy parameters)")
    print(f"DR gain=[{DR_GAIN[0]:.1f}, {DR_GAIN[1]:.1f}] offset=[{DR_OFF[0]:.1f}, {DR_OFF[1]:.1f}]; "
          f"web gain=[{WEB_GAIN[0]:.1f}, {WEB_GAIN[1]:.1f}] offset=[{WEB_OFF[0]:.1f}, {WEB_OFF[1]:.1f}]; "
          f"real gain={REAL_GAIN:.2f} offset={REAL_OFF:.2f} (declared toy parameters)")
    print(f"ORI_SIGMA={ORI_SIGMA:.1f} deg ORI_TOL={ORI_TOL:.1f} deg (grasp succeeds iff the named object is picked "
          f"and its orientation error < ORI_TOL, strict; declared toy parameters)")
    print("No integration step: no dynamics, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    inside = DR_GAIN[0] <= REAL_GAIN <= DR_GAIN[1] and DR_OFF[0] <= REAL_OFF <= DR_OFF[1]
    print(f"domain_check: real domain inside the wide DR range: {inside}; equal to the canonical no-DR domain: "
          f"{(REAL_GAIN, REAL_OFF) == (1.0, 0.0)}; inside the narrow DR range: {0.9 <= REAL_GAIN <= 1.1 and -0.1 <= REAL_OFF <= 0.1}")
    print(f"hand_calc A_geom names nothing, so it picks the named object by chance: 1/N_OBJ = 1/{N_OBJ} = {num(1 / N_OBJ)}; "
          f"with 5 objects 1/5 = {num(1 / 5)}")
    print(f"hand_calc P(|N(0, ORI_SIGMA)| < ORI_TOL) = erf({ORI_TOL:.1f}/({ORI_SIGMA:.1f}*sqrt(2))) = "
          f"{num(math.erf(ORI_TOL / (ORI_SIGMA * math.sqrt(2))))}, the ceiling for every arm")
    for regime in REGIMES:
        report(regime)
    narrow = ((0.9, 1.1), (-0.1, 0.1))
    print("alternative narrow DR (gain [0.9, 1.1], offset [-0.1, 0.1]) on in_family (same seeds, same draws):")
    alt = collect("in_family", dr=narrow)
    base = collect("in_family")
    print(f"  B_cot_dr@alt success {fmt_pair(*mean_sd(col(alt['B_cot_dr'], 'success')))} "
          f"(wide: {fmt_pair(*mean_sd(col(base['B_cot_dr'], 'success')))})")
    print(f"  paired Bwide-Bnarrow success: {verdict(col(base['B_cot_dr'], 'success'), col(alt['B_cot_dr'], 'success'))}")
    print(f"  paired Bnarrow-C success: {verdict(col(alt['B_cot_dr'], 'success'), col(alt['C_no_dr'], 'success'))}")
    print("alternative N_OBJ=5 on in_family (same seeds, same training draws):")
    alt = collect("in_family", n_obj=5)
    for arm in ARMS:
        print(f"  {arm}@alt success {fmt_pair(*mean_sd(col(alt[arm], 'success')))}")
    pairs(alt, "@alt")
    print("No winner declared: grounding-first beats a language-blind grasp when the scene has a choice and is useless with shuffled labels; here the canonical no-DR arm did not lose")
    print("GPU / weights / SynGrasp-1B / Isaac Sim / LIBERO / real grasp cell: 本页未运行; GraspVLA arXiv 2505.03233 statements and numbers 以论文为准")


if __name__ == "__main__":
    main()
