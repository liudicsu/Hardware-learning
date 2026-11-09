#!/usr/bin/env python3
"""HybridVLA-style collaborative action ensemble vs an AR-only and a diffusion-only head.

Synthetic, stdlib only.  Not plain ACT vs Diffusion Policy (earlier on this
page), not CogACT's Adaptive Action Ensemble over time (also on this page),
not OneDP, not Diffusion Forcing.  Real HybridVLA weights / GPU training:
本页未运行.  Paper numbers and the rule "average both when the mean AR token
confidence exceeds theta = 0.96, otherwise use diffusion alone" are
以论文为准 (arXiv 2503.10631, Section 3.3).

Each episode asks for one scalar action a* in [-1, 1].  Two task kinds:
    precision  one mode at a random centre; success if |a - a*| < TOL_PRECISION
    semantic   three candidate modes (-0.6, 0, 0.6), one is right; success if |a - a*| < TOL_SEMANTIC
Two heads are error models, not trained networks (no training, no time step):
    AR head         picks a mode from evidence z_ar ~ N(mu_ar, 1) (right if z_ar > 0),
                    adds N(0, SIGMA) and rounds to one of BINS bins on [-1, 1];
                    its mean token confidence is c = 1 - 0.5 * exp(-KAPPA * |z_ar|)
    diffusion head  picks a mode from its own evidence z_d ~ N(mu_d, 1) and adds N(0, SIGMA)
The two heads' mode errors are drawn independently (an assumption of this toy).
Arms:
    A_ar_only          the AR action
    B_diffusion_only   the diffusion action
    C_hybrid_ensemble  (AR + diffusion) / 2 if c > THETA, else the diffusion action
Common random numbers: per (regime, seed) every episode's task, target, evidence,
noise and wrong-mode pick are drawn once and shared by all three arms.  The arms
differ only in which output is executed.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
EPISODES = 400            # per regime and seed
BINS = 64                 # AR bins on [-1, 1]: width 2/64 = 0.03125
SIGMA = 0.010             # continuous noise of each head (same for both)
THETA = 0.96              # paper's confidence threshold
KAPPA = 1.2               # confidence slope: c > 0.96 when |z_ar| > ln(12.5)/1.2 = 2.105
TOL_PRECISION = 0.012
TOL_SEMANTIC = 0.15
SEMANTIC_MODES = (-0.6, 0.0, 0.6)
NUM_ZERO = 1e-9           # |m| and sd both below this: floating-point residue, not a gap

# name: (share of semantic episodes, mu_ar precision, mu_ar semantic, mu_d semantic, precision tolerance)
REGIMES = {
    "precision": (0.0, 3.0, 1.8, 0.5, TOL_PRECISION),
    "semantic": (1.0, 3.0, 1.8, 0.5, TOL_PRECISION),
    "mixed": (0.5, 3.0, 1.8, 0.5, TOL_PRECISION),
    "easy_precision": (0.0, 3.0, 1.8, 0.5, 0.1),
}
ARMS = ("A_ar_only", "B_diffusion_only", "C_hybrid_ensemble")


def shared_draws(regime, seed):
    """Common random numbers: one list of episodes, used by every arm."""
    sem_share, mu_ar_p, mu_ar_s, mu_d_s, _ = REGIMES[regime]
    rng = random.Random(f"{regime}/{seed}")
    eps = []
    for _ in range(EPISODES):
        semantic = rng.random() < sem_share
        if semantic:
            modes = SEMANTIC_MODES
            right = rng.randrange(3)
            mu_ar, mu_d = mu_ar_s, mu_d_s
        else:
            modes = (rng.uniform(-0.8, 0.8),)
            right = 0
            mu_ar, mu_d = mu_ar_p, mu_ar_p
        eps.append({
            "semantic": semantic, "modes": modes, "right": right,
            "target": modes[right] + (rng.uniform(-0.01, 0.01) if semantic else 0.0),
            "z_ar": rng.gauss(mu_ar, 1.0), "z_d": rng.gauss(mu_d, 1.0),
            "n_ar": rng.gauss(0.0, SIGMA), "n_d": rng.gauss(0.0, SIGMA),
            "wrong_ar": rng.randrange(2), "wrong_d": rng.randrange(2),
        })
    return eps


def pick(ep, z, wrong):
    if len(ep["modes"]) == 1 or z > 0.0:
        return ep["modes"][ep["right"]]
    others = [m for i, m in enumerate(ep["modes"]) if i != ep["right"]]
    return others[wrong]


def quantize(v):
    w = 2.0 / BINS
    i = min(BINS - 1, max(0, int((v + 1.0) / w)))
    return -1.0 + (i + 0.5) * w


def heads(ep):
    a_ar = quantize(pick(ep, ep["z_ar"], ep["wrong_ar"]) + ep["n_ar"])
    a_d = pick(ep, ep["z_d"], ep["wrong_d"]) + ep["n_d"]
    conf = 1.0 - 0.5 * math.exp(-KAPPA * abs(ep["z_ar"]))
    return a_ar, a_d, conf


def run(regime, seed, arm):
    tol_p = REGIMES[regime][4]
    hits, errs, used = 0, 0.0, 0
    for ep in shared_draws(regime, seed):
        a_ar, a_d, conf = heads(ep)
        if arm == "A_ar_only":
            a = a_ar
        elif arm == "B_diffusion_only":
            a = a_d
        elif conf > THETA:
            a, used = 0.5 * (a_ar + a_d), used + 1
        else:
            a = a_d
        err = abs(a - ep["target"])
        hits += err < (TOL_SEMANTIC if ep["semantic"] else tol_p)
        errs += err
    return {"succ": 100.0 * hits / EPISODES, "err": 1000.0 * errs / EPISODES, "gate": 100.0 * used / EPISODES}


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


def cell(xs):
    mu, sd = mean_sd(xs)
    return f"{num(mu)}+-{num(sd)}"


def main():
    print("Synthetic HybridVLA-style ensemble toy; two head error models, no training, no time step; arms differ only in the executed action; shared episodes / evidence / noise")
    print(f"episodes={EPISODES} per seed, seeds={len(SEEDS)}, AR bins={BINS} (width {2.0 / BINS:.5f}), head noise sd={SIGMA}, theta={THETA}, kappa={KAPPA}")
    print(f"confidence passes theta when |z_ar| > {math.log(0.5 / (1.0 - THETA)) / KAPPA:.4f}; tolerances: precision {TOL_PRECISION} (easy 0.1), semantic {TOL_SEMANTIC}; semantic modes {SEMANTIC_MODES}")
    res = {r: {a: [run(r, s, a) for s in SEEDS] for a in ARMS} for r in REGIMES}
    print("regime arm success_% mean_abs_err_x1000 ar_gate_%  (mean+-sd over seeds)")
    for r, (share, mu_p, mu_s, mu_ds, tol) in REGIMES.items():
        print(f"{r} (semantic share {share:.0%}; mu_ar precision {mu_p}, semantic {mu_s}; mu_d semantic {mu_ds}; precision tol {tol})")
        for a in ARMS:
            print(f"  {a} " + " ".join(cell([x[m] for x in res[r][a]]) for m in ("succ", "err", "gate")))
        for other in ("A_ar_only", "B_diffusion_only"):
            for m in ("succ", "err"):
                xc, xo = [x[m] for x in res[r]["C_hybrid_ensemble"]], [x[m] for x in res[r][other]]
                print(f"  paired C-{other[0]} {m}: {verdict(xc, xo)}")
    print("No winner declared: averaging helps when both heads pick the same mode, and hurts when a confident AR head and the diffusion head pick different modes")
    print("Real HybridVLA weights / GPU: 本页未运行; paper numbers 以论文为准")


if __name__ == "__main__":
    main()
