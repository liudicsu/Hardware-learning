#!/usr/bin/env python3
"""InternVLA-M1-style "where, then how": a stdlib stand-in for spatially guided action training.

Synthetic tabletop scenes, stdlib only.  Not InternVLA-M1 weights, not its
Qwen2.5-VL planner or DiT action expert, not SimplerEnv / LIBERO and not a
real robot: 本页未运行.  Paper numbers 以论文为准 and are not reproduced here.
Not SpatialVLA (Ego3D position encoding + adaptive action grids), not Magma
Set-of-Mark / Trace-of-Mark, not HAMSTER 2-D paths and not MolmoAct traces.

What the InternVLA-M1 paper (arXiv 2510.13778) says, and what this toy keeps:
  Stage 1, spatial grounding pre-training, trains only the VLM on box / point /
  trace QA data ("where to act", embodiment-agnostic).  Stage 2, spatially
  guided action post-training, trains the VLM and the action expert on
  demonstrations, with a spatial prompt appended to the instruction ("how to
  act").  This toy keeps only the split: a grounding stage that learns which
  object an instruction names from a large grounding corpus, then an action
  stage that reaches the grounded point.  The paper's spatial prompt is a text
  cue whose answer is not decoded; here the "where" is an explicit point, a
  stand-in, said so on the page.

Scene: K objects, each a distinct (colour, shape) pair out of N_COLOR x N_SHAPE,
at uniform positions in the unit square.  The instruction names the target's
(colour, shape).  A grounder knows a pair if it saw that pair in its training
items.  Known pair: it picks the right object.  Unknown pair: it picks
uniformly among objects that share the colour or the shape with the
instruction (all objects if none does), using the shared tie-break draw.

Common random numbers: per (regime, seed) the demonstrations, the grounding
corpus, every test scene, every tie-break draw, every execution-noise draw and
the shuffled-prompt permutation are drawn once and shared by all arms.  Arms:
  A_direct   : no spatial grounding stage; the action head learns which
               object a pair names only from the N_DEMO robot demonstrations
  B_where_how: grounding stage trained on G_ITEMS grounding items plus the
               demonstrations, then the same action stage reaches the point
  C_shuffled : B's pipeline, but the spatial prompt (the point) comes from a
               different test scene (a fixed derangement of the batch)
Success: the arm reaches the right object, i.e. the reached point (grounded
point + shared execution noise) is strictly within TOL of the target.  No
integration step: one reach per episode, no ODE.

Regimes and parameters were written before the first run:
  cluttered      : K=8, N_DEMO=40 - B consistent better success than A
  single_object  : K=1, N_DEMO=40 - nothing to ground; A and B tie (or near-tie)
  many_demos     : K=8, N_DEMO=400 - demonstrations cover the pairs; A and B
                   may near-tie
  camera_shift   : K=8, N_DEMO=400, but the grounding corpus swaps two colour
                   words (web photos vs the robot camera); B prefers its
                   grounding stage - B may LOSE to A; keep whatever happens
  C (shuffled prompt) consistent lose against B in every regime.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared model parameters, written before the first run (toy values).
N_COLOR = 6
N_SHAPE = 5
N_TEST = 200          # test episodes per seed
G_ITEMS = 600         # grounding QA items (toy count; the paper's 2.3M is 以论文为准)
SIGMA_EXEC = 0.02     # execution noise per axis (unit square)
TOL = 0.05            # success iff reach error < TOL (strict)
SWAP = (0, 1)         # colour words swapped in the camera_shift grounding corpus

REGIMES = {
    "cluttered": {"K": 8, "N_DEMO": 40, "swap": False},
    "single_object": {"K": 1, "N_DEMO": 40, "swap": False},
    "many_demos": {"K": 8, "N_DEMO": 400, "swap": False},
    "camera_shift": {"K": 8, "N_DEMO": 400, "swap": True},
}
ARMS = ("A_direct", "B_where_how", "C_shuffled")


def make_scene(rng, k):
    pairs = rng.sample([(c, s) for c in range(N_COLOR) for s in range(N_SHAPE)], k)
    objs = [{"pair": p, "xy": (rng.random(), rng.random())} for p in pairs]
    target = rng.randrange(k)
    return {"objs": objs, "target": target, "u": rng.random(),
            "noise": (rng.gauss(0.0, SIGMA_EXEC), rng.gauss(0.0, SIGMA_EXEC))}


def shared_world(regime, seed, g_items=G_ITEMS):
    """Common random numbers: demos, grounding corpus, test scenes, draws; used by every arm."""
    cfg = REGIMES[regime]
    rng = random.Random(f"{regime}/{seed}")
    demos = [make_scene(rng, cfg["K"]) for _ in range(cfg["N_DEMO"])]
    tests = [make_scene(rng, cfg["K"]) for _ in range(N_TEST)]
    shift = rng.randrange(1, N_TEST)          # fixed derangement for C
    grng = random.Random(f"ground/{seed}")    # grounding corpus: same items in every regime
    corpus = [(grng.randrange(N_COLOR), grng.randrange(N_SHAPE)) for _ in range(g_items)]
    return {"demos": demos, "tests": tests, "shift": shift, "corpus": corpus}


def swap_colour(pair):
    c, s = pair
    if c == SWAP[0]:
        return (SWAP[1], s)
    if c == SWAP[1]:
        return (SWAP[0], s)
    return pair


def knowledge(arm, world, regime):
    """Map instruction pair -> visual pair the arm believes it names."""
    know = {}
    if arm != "A_direct":
        for p in world["corpus"]:
            know[p] = swap_colour(p) if REGIMES[regime]["swap"] else p
    for d in world["demos"]:
        p = d["objs"][d["target"]]["pair"]
        know.setdefault(p, p)   # B keeps its grounding-stage answer when it has one
    return know


def ground(know, scene, pair):
    """Index of the object the arm grounds the instruction to."""
    objs = scene["objs"]
    if pair in know:
        vis = know[pair]
        hits = [i for i, o in enumerate(objs) if o["pair"] == vis]
        if hits:
            return hits[0]
    cands = [i for i, o in enumerate(objs) if o["pair"][0] == pair[0] or o["pair"][1] == pair[1]]
    if not cands:
        cands = list(range(len(objs)))
    return cands[min(int(scene["u"] * len(cands)), len(cands) - 1)]


def run_seed(regime, seed, arm, g_items=G_ITEMS):
    world = shared_world(regime, seed, g_items)
    know = knowledge(arm, world, regime)
    tests = world["tests"]
    where = succ = 0
    for i, sc in enumerate(tests):
        pair = sc["objs"][sc["target"]]["pair"]
        if arm == "C_shuffled":
            other = tests[(i + world["shift"]) % len(tests)]
            j = ground(know, other, other["objs"][other["target"]]["pair"])
            aim = other["objs"][j]["xy"]
            right = math.dist(aim, sc["objs"][sc["target"]]["xy"]) < TOL
        else:
            j = ground(know, sc, pair)
            aim = sc["objs"][j]["xy"]
            right = j == sc["target"]
        reach = (aim[0] + sc["noise"][0], aim[1] + sc["noise"][1])
        where += int(right)
        succ += int(math.dist(reach, sc["objs"][sc["target"]]["xy"]) < TOL)
    return {"where_pct": 100.0 * where / len(tests), "success_pct": 100.0 * succ / len(tests),
            "known_pairs": float(len(know))}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
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


def table(regime, g_items=G_ITEMS):
    return {arm: [run_seed(regime, seed, arm, g_items) for seed in SEEDS] for arm in ARMS}


def col(res, arm, key):
    return [float(r[key]) for r in res[arm]]


def main():
    print("Synthetic InternVLA-M1-style where-then-how toy (arXiv 2510.13778); shared scenes; not InternVLA-M1 weights")
    print(f"seeds={len(SEEDS)} N_COLOR={N_COLOR} N_SHAPE={N_SHAPE} pairs={N_COLOR * N_SHAPE} N_TEST={N_TEST} "
          f"G_ITEMS={G_ITEMS} (toy count) SIGMA_EXEC={SIGMA_EXEC:.3f} TOL={TOL:.3f} SWAP=colours {SWAP[0]}<->{SWAP[1]}")
    print("No integration step: one reach per episode, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print(f"hand_calc reach: per-axis noise sd {SIGMA_EXEC:.3f}, radial sd ratio TOL/SIGMA_EXEC = {TOL / SIGMA_EXEC:.4f}; "
          f"P(radius < TOL) = 1-exp(-(TOL/SIGMA_EXEC)^2/2) = {100.0 * (1.0 - math.exp(-(TOL / SIGMA_EXEC) ** 2 / 2.0)):.4f} %")
    print(f"hand_calc chance: a uniform guess among 8 objects is right 1/8 = {100.0 / 8:.4f} % of the time")
    print("success_rule: success iff |reach - target| < TOL (strict); "
          f"error {TOL:.4f} -> success {int(TOL < TOL)}; error {TOL - 0.0001:.4f} -> success {int(TOL - 0.0001 < TOL)}")
    for regime, cfg in REGIMES.items():
        res = table(regime)
        print(f"{regime} (K={cfg['K']} objects, N_DEMO={cfg['N_DEMO']} demos, colour swap in grounding corpus: "
              f"{'yes' if cfg['swap'] else 'no'}; {N_TEST} test scenes per seed):")
        for arm in ARMS:
            print(f"  {arm} success_pct {fmt_pair(*mean_sd(col(res, arm, 'success_pct')))} "
                  f"where_pct {fmt_pair(*mean_sd(col(res, arm, 'where_pct')))} "
                  f"known_pairs {fmt_pair(*mean_sd(col(res, arm, 'known_pairs')))}")
        print(f"  paired B-A success_pct: {verdict(col(res, 'B_where_how', 'success_pct'), col(res, 'A_direct', 'success_pct'))}")
        print(f"  paired B-A where_pct: {verdict(col(res, 'B_where_how', 'where_pct'), col(res, 'A_direct', 'where_pct'))}")
        print(f"  paired C-B success_pct: {verdict(col(res, 'C_shuffled', 'success_pct'), col(res, 'B_where_how', 'success_pct'))}")
    for regime, alt in (("cluttered", 60), ("camera_shift", 60)):
        base = table(regime)
        res = table(regime, alt)
        print(f"alternative G_ITEMS={alt} on {regime} (same seeds):")
        print(f"  B_where_how success_pct@alt {fmt_pair(*mean_sd(col(res, 'B_where_how', 'success_pct')))} "
              f"known_pairs@alt {fmt_pair(*mean_sd(col(res, 'B_where_how', 'known_pairs')))} "
              f"(default success_pct {fmt_pair(*mean_sd(col(base, 'B_where_how', 'success_pct')))})")
        print(f"  paired B-A success_pct@alt: {verdict(col(res, 'B_where_how', 'success_pct'), col(res, 'A_direct', 'success_pct'))}")
    print("No winner declared: grounding helps when clutter makes 'which object' the hard part and demonstrations are few; "
          "with one object or plenty of demonstrations it adds little, and a grounding corpus that disagrees with the robot camera can hurt")
    print("InternVLA-M1 weights / SimplerEnv / LIBERO / real robot: 本页未运行; paper numbers 以论文为准")


if __name__ == "__main__":
    main()
