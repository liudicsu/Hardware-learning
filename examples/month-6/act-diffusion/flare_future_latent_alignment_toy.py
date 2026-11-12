#!/usr/bin/env python3
"""Tiny stdlib stand-in for FLARE (arXiv 2505.15659): action loss plus lambda times a
cosine alignment loss between learnable future tokens z = P W x and a frozen embedding
g(x_future) = G x_future.  This is a stdlib stand-in, not GR00T N1 / SigLIP2 / a DiT.
FLARE paper numbers 以论文为准.  GPU / RoboCasa / GR-1 本页未运行.

Shared by every arm: the same data draws, the same frozen G and the same initial
(W, v, P).  Full-batch gradient descent with exact analytic gradients.  The alignment
loss for one sample is -cos(z, g); its gradient with respect to z is
-(g/|g| - cos * z/|z|) / |z|.  Arms: A_action_only (lam = 0, labelled only),
B_flare (lam = LAMBDA, alignment on labelled + action-free), C_big_lambda
(lam = LAMBDA_BIG, otherwise as B).  Parameters were declared before the first run.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

# Declared parameters, written before the first run.
SEEDS = (0, 1, 2, 3, 4)
D = 8                    # observation dimension
K = 2                    # latent / future-token dimension
LAMBDA = 0.2             # the paper's alignment weight
LAMBDA_BIG = 2.0         # deliberately large lambda
LR = 0.05                # full-batch gradient-descent step
EPOCHS = 400             # full-batch passes
SUCCESS_TOL = 0.25       # |a_hat - a| below this counts as a success
N_TEST = 200             # fresh test samples per (regime, seed)

REGIMES = {
    "delayed": {"n_lab": 6, "n_vid": 60},
    "reactive": {"n_lab": 60, "n_vid": 0},
}
ARMS = ("A_action_only", "B_flare", "C_big_lambda")
METRICS = ("action_mse", "success", "latent_cos")
PAIRS = (("B_flare", "A_action_only"), ("C_big_lambda", "A_action_only"),
         ("C_big_lambda", "B_flare"))


def matvec(M, x):
    return [sum(M[k][j] * x[j] for j in range(len(x))) for k in range(len(M))]


def init_params(seed):
    """Common random numbers: identical W, v, P for every arm at this seed."""
    rng = random.Random(2000 + seed)
    W = [[rng.gauss(0.0, 0.1) for _ in range(D)] for _ in range(K)]
    v = [rng.gauss(0.0, 0.1) for _ in range(K)]
    P = [[rng.gauss(0.0, 0.1) for _ in range(K)] for _ in range(K)]
    return W, v, P


def frozen_G(seed):
    """Frozen target embedding matrix G (K x D), drawn once and never trained."""
    rng = random.Random(1000 + seed)
    return [[rng.gauss(0.0, 1.0) / math.sqrt(D) for _ in range(D)] for _ in range(K)]


def delayed_labelled(rng):
    goal = rng.uniform(-1.0, 1.0)
    x = [0.3 * goal + rng.gauss(0.0, 0.05)] + [rng.gauss(0.0, 1.0) for _ in range(D - 1)]
    xf = [1.0 * goal + rng.gauss(0.0, 0.05)] + [rng.gauss(0.0, 1.0) for _ in range(D - 1)]
    return x, goal, xf


def delayed_video(rng):
    goal = rng.uniform(-1.0, 1.0)
    x = [0.3 * goal + rng.gauss(0.0, 0.05)] + [rng.gauss(0.0, 1.0) for _ in range(D - 1)]
    xf = [1.0 * goal + rng.gauss(0.0, 0.05)] + [rng.gauss(0.0, 1.0) for _ in range(D - 1)]
    return x, xf


def make_labelled(rng, regime):
    if regime == "delayed":
        return delayed_labelled(rng)
    x = [rng.gauss(0.0, 1.0) for _ in range(D)]
    a = 0.5 * x[0] - 0.3 * x[1] + rng.gauss(0.0, 0.05)
    xf = [rng.gauss(0.0, 1.0) for _ in range(D)]
    return x, a, xf


def make_video(rng, regime):
    if regime == "delayed":
        return delayed_video(rng)
    x = [rng.gauss(0.0, 1.0) for _ in range(D)]
    xf = [rng.gauss(0.0, 1.0) for _ in range(D)]
    return x, xf


def generate(regime, seed, n_lab=None, n_vid=None):
    """One rng stream per (regime, seed): train data first, then the fresh test set."""
    index = list(REGIMES).index(regime)
    rng = random.Random(seed * 100 + index)
    nl = REGIMES[regime]["n_lab"] if n_lab is None else n_lab
    nv = REGIMES[regime]["n_vid"] if n_vid is None else n_vid
    lab = [make_labelled(rng, regime) for _ in range(nl)]
    vid = [make_video(rng, regime) for _ in range(nv)]
    test = [make_labelled(rng, regime) for _ in range(N_TEST)]
    return lab, vid, test


def train(W, v, P, G, lam, lab, vid):
    """Full-batch GD; exact analytic gradients for the action and cosine alignment terms."""
    n_lab = len(lab)
    align = [(x, xf) for x, _, xf in lab] + list(vid)
    n_align = len(align)
    for _ in range(EPOCHS):
        gW = [[0.0] * D for _ in range(K)]
        gv = [0.0] * K
        gP = [[0.0] * K for _ in range(K)]
        # Action loss: mean over labelled samples of (v.h - a)^2.
        for x, a, _ in lab:
            h = matvec(W, x)
            ahat = sum(v[k] * h[k] for k in range(K))
            d = 2.0 * (ahat - a) / n_lab
            for k in range(K):
                gv[k] += d * h[k]
                for j in range(D):
                    gW[k][j] += d * v[k] * x[j]
        # Alignment loss: lam * mean over alignment samples of -cos(P.h, G.xf).
        if lam != 0.0 and n_align:
            w = lam / n_align
            for x, xf in align:
                h = matvec(W, x)
                z = matvec(P, h)
                t = matvec(G, xf)
                nz = math.sqrt(sum(z[k] * z[k] for k in range(K)))
                nt = math.sqrt(sum(t[k] * t[k] for k in range(K)))
                nzt = nz * nt
                if nzt < 1e-12:
                    continue
                c = sum(z[k] * t[k] for k in range(K)) / nzt
                # d(-cos)/dz = -(t/|t| - c * z/|z|) / |z|, scaled by the mean weight.
                dz = [(-(t[k] / nt - c * z[k] / nz) / nz) * w for k in range(K)]
                for k in range(K):
                    for l in range(K):
                        gP[k][l] += dz[k] * h[l]
                dh = [sum(dz[k] * P[k][l] for k in range(K)) for l in range(K)]
                for k in range(K):
                    for j in range(D):
                        gW[k][j] += dh[k] * x[j]
        for k in range(K):
            v[k] -= LR * gv[k]
            for j in range(D):
                W[k][j] -= LR * gW[k][j]
            for l in range(K):
                P[k][l] -= LR * gP[k][l]
    return W, v, P


def evaluate(W, v, P, G, test):
    n = len(test)
    se = 0.0
    hits = 0
    cosum = 0.0
    for x, a, xf in test:
        h = matvec(W, x)
        ahat = sum(v[k] * h[k] for k in range(K))
        e = ahat - a
        se += e * e
        if abs(e) < SUCCESS_TOL:
            hits += 1
        z = matvec(P, h)
        t = matvec(G, xf)
        nz = math.sqrt(sum(z[k] * z[k] for k in range(K)))
        nt = math.sqrt(sum(t[k] * t[k] for k in range(K)))
        cosum += (sum(z[k] * t[k] for k in range(K)) / (nz * nt)) if nz * nt > 0.0 else 0.0
    return {"action_mse": se / n, "success": hits / n, "latent_cos": cosum / n}


def run(lam, seed, data):
    lab, vid, test = data
    G = frozen_G(seed)
    W, v, P = init_params(seed)
    W, v, P = train(W, v, P, G, lam, lab, vid)
    return evaluate(W, v, P, G, test)


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


NUM_ZERO = 1e-9


def collect(regime, lam_b=LAMBDA, n_lab=None, n_vid=None, arms=ARMS):
    res = {arm: [] for arm in arms}
    for s in SEEDS:
        data = generate(regime, s, n_lab, n_vid)
        for arm in arms:
            lam = 0.0 if arm == "A_action_only" else (lam_b if arm == "B_flare" else LAMBDA_BIG)
            res[arm].append(run(lam, s, data))
    return res


def col(rows, key):
    return [x[key] for x in rows]


def report(regime):
    res = collect(regime)
    p = REGIMES[regime]
    if regime == "delayed":
        declared = ("declared: B consistently better than A on action_mse and success; "
                    "C consistently higher action_mse than B")
        detail = "hidden goal g, x[0]=0.3g+noise, x_future[0]=1.0g+noise, dims 1..7 distractors"
    else:
        declared = ("declared: A and B may near-tie or B loses; "
                    "C consistently higher action_mse than B")
        detail = "a=0.5x[0]-0.3x[1]+noise, x_future independent fresh noise (no future information)"
    print(f"{regime} (N_LAB={p['n_lab']} labelled, N_VID={p['n_vid']} action-free; {detail}):")
    print("  " + declared)
    for arm in ARMS:
        print(f"  {arm} " + " ".join(
            f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS))
    for a, b in PAIRS:
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: "
                  f"{verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("Synthetic FLARE future-latent alignment toy; shared data, frozen G and initial params; "
          "action loss + lambda * cosine alignment; not GR00T N1 / SigLIP2 / a DiT")
    print(f"seeds={len(SEEDS)} D={D} K={K} LAMBDA={num(LAMBDA)} LAMBDA_BIG={num(LAMBDA_BIG)} "
          f"LR={num(LR)} EPOCHS={EPOCHS} SUCCESS_TOL={num(SUCCESS_TOL)} N_TEST={N_TEST} "
          f"(declared toy parameters; FLARE paper numbers 以论文为准)")
    print("Full-batch gradient descent with exact analytic gradients; "
          "W is KxD, v is K, P is KxK; z=P W x is aligned to the frozen G x_future")
    print("Regimes and parameters were written before the first run")
    print(f"hand_calc alignment weight at cos=1: -LAMBDA={num(-LAMBDA)}; "
          f"-LAMBDA_BIG={num(-LAMBDA_BIG)}")
    print(f"hand_calc delayed goal/distractor std ratio: current obs "
          f"0.3*sqrt(1/3)/1.0={num(0.3 * math.sqrt(1.0 / 3.0))}; "
          f"future obs 1.0*sqrt(1/3)={num(math.sqrt(1.0 / 3.0))}")
    for regime in REGIMES:
        report(regime)
    print("alternatives (same seeds, declared before the run, not adopted):")
    alt = collect("delayed", lam_b=0.05, arms=("A_action_only", "B_flare"))
    print(f"  delayed LAMBDA={num(0.05)}: paired B-A action_mse@alt: "
          f"{verdict(col(alt['B_flare'], 'action_mse'), col(alt['A_action_only'], 'action_mse'))}")
    alt = collect("delayed", lam_b=1.0, arms=("A_action_only", "B_flare"))
    print(f"  delayed LAMBDA={num(1.0)}: paired B-A action_mse@alt: "
          f"{verdict(col(alt['B_flare'], 'action_mse'), col(alt['A_action_only'], 'action_mse'))}")
    alt = collect("delayed", n_lab=12, arms=("A_action_only", "B_flare"))
    print(f"  delayed N_LAB=12: paired B-A action_mse@alt: "
          f"{verdict(col(alt['B_flare'], 'action_mse'), col(alt['A_action_only'], 'action_mse'))}")
    alt = collect("reactive", lam_b=1.0, arms=("A_action_only", "B_flare"))
    print(f"  reactive LAMBDA={num(1.0)}: paired B-A action_mse@alt: "
          f"{verdict(col(alt['B_flare'], 'action_mse'), col(alt['A_action_only'], 'action_mse'))}")
    print("No universal winner: alignment helps when the future reveals what the action needs and is noise when it does not")
    print("GR00T N1 / RoboCasa / GR-1 / GPU: 本页未运行; FLARE paper numbers 以论文为准")


if __name__ == "__main__":
    main()
