#!/usr/bin/env python3
"""Magma-style Set-of-Mark + Trace-of-Mark vs direct coordinate output vs shuffled marks, on shared scenes.

Synthetic, stdlib only.  Not Magma's model, data or benchmarks: a discrete stand-in for the two
ideas in the paper's section 3.2 (select a numbered mark instead of regressing a coordinate; then
predict the mark's future trace).  Not a UI agent, not HAMSTER's 2-D path, not MolmoAct traces,
not TraceVLA, not ThinkAct.  Magma benchmark numbers are 以论文为准; GPU, UI or robot runs:
本页未运行.

Scene (image coordinates normalised to [0, 1], as in the paper): K candidate objects at uniform
positions; object 0 is the instructed target.  Each object moves with a constant velocity per
step (speed set by the regime, random direction); its true trace is p + v * tau, tau = 1..L.
Shared belief: the same noisy relevance score per candidate, target SIGNAL + N(0, SIG_B),
distractors N(0, SIG_B); softmax weights w_k.
Arms (same scene, same scores):
  A_direct  outputs one continuous point: sum_k w_k p_k plus N(0, SIG_REG) per axis (a regressor
            averages its candidates); no trace, so its plan for every future step is that point
  B_somtom  selects the mark with the highest score; the point is that mark's position quantised
            to BINS bins per axis (the paper quantises coordinates into 256 bins); then predicts
            the mark's trace with a tracked velocity v + N(0, SIG_TRK) per axis
  C_shuffle same selection and trace step as B, but the numeric labels are drawn on the wrong
            objects (a uniform random permutation; with K = 1 it can only be the identity)
Metrics per seed (SCENES scenes): grounding % (point within RADIUS of the target now), trace ADE
(mean distance to the target's true trace over L steps, x 100), success % (planned point at step
L within RADIUS of the target then).  No integration step: positions are closed form per step.
Common random numbers: per (regime, seed), the positions, velocities, scores, regression noise,
tracking noise and permutations are drawn once per scene and used by all three arms.
Regimes and expectations, written before the first run:
  cluttered      K 8, speed 0.01 per step, SIG_TRK 0.002   B consistent win over A on grounding
                                                            and success
  single_target  K 1, static, SIG_TRK 0                      A and B tie on grounding and success
  static_jitter  K 2, static, SIG_TRK 0.012                 B ties or loses to A on success (the
                                                            trace adds error to a static target)
  C loses to B on grounding in every regime with K > 1.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
SCENES = 400
L = 8              # trace length (steps)
RADIUS = 0.05
BINS = 256
SIGNAL, SIG_B = 3.0, 1.0
SIG_REG = 0.01
NUM_ZERO = 1e-9
ARMS = ("A_direct", "B_somtom", "C_shuffle")
# name: (K, speed per step, SIG_TRK); written before the first run
REGIMES = {
    "cluttered": (8, 0.01, 0.002),
    "single_target": (1, 0.0, 0.0),
    "static_jitter": (2, 0.0, 0.012),
}
STREAM = {"cluttered": 0, "single_target": 1, "static_jitter": 2}


def quantise(u):
    k = min(BINS - 1, max(0, int(u * BINS)))
    return (k + 0.5) / BINS


def shared_draws(regime, seed):
    rng = random.Random(1000 * STREAM[regime] + seed)
    k, speed, sig_trk = REGIMES[regime]
    scenes = []
    for _ in range(SCENES):
        pos = [(rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95)) for _ in range(k)]
        vel = []
        for _ in range(k):
            th = rng.uniform(0.0, 2.0 * math.pi)
            vel.append((speed * math.cos(th), speed * math.sin(th)))
        score = [(SIGNAL if i == 0 else 0.0) + rng.gauss(0.0, SIG_B) for i in range(k)]
        reg = (rng.gauss(0.0, SIG_REG), rng.gauss(0.0, SIG_REG))
        trk = (rng.gauss(0.0, sig_trk), rng.gauss(0.0, sig_trk)) if sig_trk > 0 else (0.0, 0.0)
        perm = list(range(k))
        rng.shuffle(perm)
        scenes.append((pos, vel, score, reg, trk, perm))
    return scenes


def plan(arm, scene):
    pos, vel, score, reg, trk, perm = scene
    if arm == "A_direct":
        mx = max(score)
        w = [math.exp(s - mx) for s in score]
        tot = sum(w)
        px = sum(wi * p[0] for wi, p in zip(w, pos)) / tot + reg[0]
        py = sum(wi * p[1] for wi, p in zip(w, pos)) / tot + reg[1]
        return [(px, py)] * (L + 1)
    sel = max(range(len(score)), key=lambda i: score[i])
    obj = perm[sel] if arm == "C_shuffle" else sel
    p = (quantise(pos[obj][0]), quantise(pos[obj][1]))
    v = (vel[obj][0] + trk[0], vel[obj][1] + trk[1])
    return [(p[0] + v[0] * t, p[1] + v[1] * t) for t in range(L + 1)]


def evaluate(arm, scenes):
    g = s = ade = 0.0
    for sc in scenes:
        pos, vel = sc[0], sc[1]
        tr = [(pos[0][0] + vel[0][0] * t, pos[0][1] + vel[0][1] * t) for t in range(L + 1)]
        pl = plan(arm, sc)
        g += math.dist(pl[0], tr[0]) <= RADIUS
        s += math.dist(pl[L], tr[L]) <= RADIUS
        ade += sum(math.dist(pl[t], tr[t]) for t in range(1, L + 1)) / L
    n = len(scenes)
    return {"ground": 100.0 * g / n, "ade": 100.0 * ade / n, "success": 100.0 * s / n}


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


def main():
    print("Synthetic Magma-style probe: direct point vs Set-of-Mark + Trace-of-Mark vs shuffled marks; discrete stand-in, not Magma")
    print(f"SCENES={SCENES} L={L} RADIUS={RADIUS} BINS={BINS} SIGNAL={SIGNAL} SIG_B={SIG_B} SIG_REG={SIG_REG} seeds={len(SEEDS)}")
    print(f"quantisation error at most {0.5 / BINS:.6f} per axis; no integration step (closed-form positions per step)")
    print("regime arm grounding_% trace_ADE_x100 success_%  (mean+-sd over seeds)")
    for regime, (k, speed, sig_trk) in REGIMES.items():
        w0 = math.exp(SIGNAL) / (math.exp(SIGNAL) + (k - 1))
        print(f"{regime} (K {k}; speed {speed} per step, target moves {speed * L:.4f} over L; SIG_TRK {sig_trk}; noise-free target weight {w0:.4f})")
        draws = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [evaluate(arm, d) for d in draws] for arm in ARMS}
        for arm in ARMS:
            cols = ["{}+-{}".format(*map(num, mean_sd([r[key] for r in res[arm]]))) for key in ("ground", "ade", "success")]
            print(f"  {arm} " + " ".join(cols))
        for x, y in (("B_somtom", "A_direct"), ("C_shuffle", "B_somtom")):
            for key in ("ground", "ade", "success"):
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[key] for r in res[x]], [r[key] for r in res[y]])}")
    print("No winner declared: marks help where a regressor averages many candidates, change nothing with one target, and a noisy trace hurts a static target; wrong marks hurt")
    print("Magma benchmark numbers 以论文为准; GPU / UI / robot: 本页未运行")


if __name__ == "__main__":
    main()
