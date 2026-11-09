#!/usr/bin/env python3
"""Synthetic FORGE-Tree-style toy: one-shot decoding vs segment search with a frozen prefix. Stdlib only.

A trajectory is L = S x M action tokens; each token is a 2-D end-effector displacement (cm), so
positions are cumulative sums and an error in one token shifts every later position (drift
compounds). Stage j ends at token (j + 1) M - 1 and must land within TOL of its goal G_j.
The frozen "VLA + Diffusion Forcing head" stand-in decodes token i as the demo displacement
plus noise: delta_i = mu_i + b_j + SIGMA * eps_i (b_j a per-stage bias, eps_i ~ N(0, 1)).

Arms (same decoded trajectory, same candidate noise pool, same evaluation noise pool):
  A_oneshot  execute the one-shot decode (fixed schedule, no test-time search)
  B_tree     stage by stage: spend BUDGET partial-denoise simulations on future segments, chosen
             by P-UCT with Laplace smoothing (Score = Q + C_PUCT P sqrt(log(N + 1) / (N_a + 1)))
             over meta-actions a = (segment, strength, guidance); unvisited children are ordered by
             a fast heuristic (estimated end error / TOL); keep a candidate if its noisy geometry
             return beats the current plan's; then commit the current stage (prefix frozen)
  C_random   the same budget, edit operator, acceptance rule and commit, segment and meta-action
             picked uniformly at random (no tree value)
The tree here is depth 1 (root = current plan, children = meta-actions), a stand-in for the
paper's stage-aware MCTD; there is no scene graph, no VLA likelihood and no learned network.
Partial denoise of segment k at strength rho with guidance w (only segment k changes):
  delta'_i = mu_i + b_k + SIGMA (sqrt(1 - rho) eps_i + sqrt(rho) eta_i) - w e_hat / M
with eta from the shared candidate pool and e_hat the noisy estimate of stage k's end error.
Geometry return = - sum over future stages of max(0, |e_hat_j| - TOL)  (e_hat = e + N(0, SIGMA_EVAL)).

Integrity criterion (the paper preserves the executed prefix): once a stage is committed its
tokens never change; prefix violations are counted for every arm (must be 0 for B and C) and an
unmasked edit is printed as a check. No integration step: each partial denoise is one closed-form
jump, nothing is stepped in time.
Common random numbers: per (regime, seed, trial) the goals, the one-shot decode noise, the stage
biases, the candidate noise pool and the evaluation noise pool are drawn once; simulation number
n uses pool entry n in both B and C.
Metrics per trial, averaged over TRIALS per seed: stage (share of stage goals within TOL), final
(all stages within TOL), edits (accepted edits), prefix (prefix violations).
Labels: tie = identical on every seed; numerically zero = |paired mean| and sd both < 1e-9
(effectively a tie, no sign count); |m| <= sd = near-tie; |m| > sd = consistent gap (small if
|m| < 20 % of the smaller arm mean, else clear), with a sign count.
OpenVLA / Octo / LIBERO / a GPU: 本页未运行. Paper numbers: 以论文为准.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
TRIALS = 40
M = 8  # tokens per stage
SIGMA = 0.4  # per-token decode noise (cm)
BIAS = 0.15  # per-stage bias sd (cm per token)
SIGMA_EVAL = 0.3  # geometry-score noise (cm)
C_PUCT = 1.0
STRENGTHS = (0.5, 1.0)
GUIDES = (0.3, 0.6)
POOL = 400
NUM_ZERO = 1e-9
ARMS = ("A_oneshot", "B_tree", "C_random")
# name: (stages S, TOL cm, simulations per stage, SIGMA_EVAL)
REGIMES = {
    "single_stage": (1, 1.5, 8, SIGMA_EVAL),
    "long_loose": (4, 4.0, 8, SIGMA_EVAL),
    "long_tight": (4, 1.0, 8, SIGMA_EVAL),
    "low_budget": (4, 1.0, 1, SIGMA_EVAL),
    "noisy_graph": (4, 1.0, 8, 1.5),
}
BUDGETS = (1, 2, 4, 8, 16)


def world(stages, seed, trial, tag):
    """Common random numbers for one (regime, seed, trial)."""
    rng = random.Random(f"{tag}-{seed}-{trial}")
    goals, mu, p = [], [], (0.0, 0.0)
    for _ in range(stages):
        g = (p[0] + rng.uniform(6.0, 10.0), p[1] + rng.uniform(-4.0, 4.0))
        mu += [((g[0] - p[0]) / M, (g[1] - p[1]) / M)] * M
        goals.append(g)
        p = g
    bias = [(rng.gauss(0.0, BIAS), rng.gauss(0.0, BIAS)) for _ in range(stages)]
    eps = [(rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0)) for _ in range(stages * M)]
    pool = [[(rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0)) for _ in range(M)] for _ in range(POOL)]
    evals = [[(rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0)) for _ in range(stages)] for _ in range(2 * POOL + 2)]
    picks = [rng.random() for _ in range(2 * POOL)]
    return goals, mu, bias, eps, pool, evals, picks


def decode(mu, bias, eps):
    return [(mu[i][0] + bias[i // M][0] + SIGMA * eps[i][0], mu[i][1] + bias[i // M][1] + SIGMA * eps[i][1]) for i in range(len(mu))]


def stage_errors(tokens, goals):
    x = y = 0.0
    errs = []
    for i, (dx, dy) in enumerate(tokens):
        x += dx
        y += dy
        if (i + 1) % M == 0:
            g = goals[i // M]
            errs.append((x - g[0], y - g[1]))
    return errs


def estimate(errs, noise, sig):
    return [(e[0] + sig * n[0], e[1] + sig * n[1]) for e, n in zip(errs, noise)]


def ret(est, tol, first):
    return -sum(max(0.0, math.hypot(*e) - tol) for e in est[first:])


def edit(tokens, mu, bias, eps_now, k, rho, w, e_hat, eta):
    """Partial denoise of segment k only: every other token is copied unchanged."""
    out = list(tokens)
    new_eps = []
    for t in range(M):
        i = k * M + t
        ex = math.sqrt(1.0 - rho) * eps_now[i][0] + math.sqrt(rho) * eta[t][0]
        ey = math.sqrt(1.0 - rho) * eps_now[i][1] + math.sqrt(rho) * eta[t][1]
        new_eps.append((ex, ey))
        out[i] = (mu[i][0] + bias[k][0] + SIGMA * ex - w * e_hat[0] / M, mu[i][1] + bias[k][1] + SIGMA * ey - w * e_hat[1] / M)
    return out, new_eps


def run(arm, regime, seed, trial, budget=None):
    stages, tol, sims, sig = REGIMES[regime]
    sims = sims if budget is None else budget
    goals, mu, bias, eps, pool, evals, picks = world(stages, seed, trial, regime)
    tokens = decode(mu, bias, eps)
    eps_now = list(eps)
    edits = viol = 0
    n = 0  # simulation counter: pool entry n is used by B and C alike
    if arm != "A_oneshot":
        for s in range(stages):
            actions = [(k, rho, w) for k in range(s, stages) for rho in STRENGTHS for w in GUIDES]
            visits, value = {a: 0 for a in actions}, {a: 0.0 for a in actions}
            for _ in range(sims):
                cur = estimate(stage_errors(tokens, goals), evals[2 * n], sig)
                if arm == "B_tree":
                    unvisited = [a for a in actions if visits[a] == 0]
                    if unvisited:
                        a = max(unvisited, key=lambda a: (math.hypot(*cur[a[0]]) / tol, -a[1], -a[2]))
                    else:
                        tot = sum(visits.values())
                        a = max(actions, key=lambda a: value[a] / visits[a] + C_PUCT / len(actions) * math.sqrt(math.log(tot + 1) / (visits[a] + 1)))
                else:
                    a = actions[int(picks[n] * len(actions))]
                k, rho, w = a
                cand, cand_eps = edit(tokens, mu, bias, eps_now, k, rho, w, cur[k], pool[n % POOL])
                new = estimate(stage_errors(cand, goals), evals[2 * n + 1], sig)
                gain = ret(new, tol, s) - ret(cur, tol, s)
                visits[a] += 1
                value[a] += gain
                if gain > 0.0:
                    before = tokens[: s * M]
                    tokens = cand
                    for t in range(M):
                        eps_now[k * M + t] = cand_eps[t]
                    edits += 1
                    viol += sum(1 for p, q in zip(before, tokens[: s * M]) if p != q)
                n += 1
    errs = stage_errors(tokens, goals)
    ok = [math.hypot(*e) <= tol for e in errs]
    return {"stage": sum(ok) / len(ok), "final": 1.0 if all(ok) else 0.0, "edits": float(edits), "prefix": float(viol)}


def unmasked_edit_check():
    """Stage 1 committed: a masked edit of segment 2 vs a re-denoise of the whole trajectory (no mask)."""
    goals, mu, bias, eps, pool, evals, picks = world(4, 0, 0, "long_tight")
    tokens = decode(mu, bias, eps)
    masked, _ = edit(tokens, mu, bias, eps, 1, 1.0, 0.3, (0.0, 0.0), pool[0])
    redo = decode(mu, bias, [(math.sqrt(0.5) * a[0] + math.sqrt(0.5) * b[0], math.sqrt(0.5) * a[1] + math.sqrt(0.5) * b[1]) for a, b in zip(eps, [p for seg in pool[:4] for p in seg])])
    changed = lambda new: sum(1 for p, q in zip(tokens[:M], new[:M]) if p != q)
    return changed(redo), changed(masked)


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


KEYS = ("stage", "final", "edits", "prefix")


def per_seed(arm, regime, budget=None):
    out = []
    for seed in SEEDS:
        rs = [run(arm, regime, seed, t, budget) for t in range(TRIALS)]
        out.append({k: sum(r[k] for r in rs) / TRIALS for k in KEYS})
    return out


def main():
    print("Synthetic FORGE-Tree-style toy; displacement tokens, depth-1 segment search, frozen prefix; not OpenVLA / Octo / LIBERO")
    print(f"seeds={len(SEEDS)} trials={TRIALS} tokens/stage={M} sigma={SIGMA} bias={BIAS} c_puct={C_PUCT} strengths={STRENGTHS} guidance={GUIDES}; no integration step (closed-form partial denoise)")
    bad, good = unmasked_edit_check()
    print(f"integrity check: a re-denoise without the segment mask changes {bad} of the {M} committed stage-1 tokens; a masked edit of segment 2 changes {good}")
    print("regime arm stage final edits prefix  (mean+-sd over seeds of per-seed trial means)")
    for regime, (stages, tol, sims, sig) in REGIMES.items():
        print(f"{regime} (stages={stages}, tol={tol} cm, simulations/stage={sims}, sigma_eval={sig} cm)")
        res = {arm: per_seed(arm, regime) for arm in ARMS}
        for arm in ARMS:
            cells = " ".join("{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in KEYS)
            print(f"  {arm} {cells}")
        for x, y in (("B_tree", "A_oneshot"), ("C_random", "B_tree"), ("C_random", "A_oneshot")):
            for k in ("stage", "final"):
                print(f"  paired {x[0]}-{y[0]} {k}: {verdict([r[k] for r in res[x]], [r[k] for r in res[y]])}")
    print("budget sweep on long_tight (final: mean over seeds; paired B-A final)")
    a = per_seed("A_oneshot", "long_tight")
    for b in BUDGETS:
        rb = per_seed("B_tree", "long_tight", budget=b)
        rc = per_seed("C_random", "long_tight", budget=b)
        print(f"  budget={b}: A {num(mean_sd([r['final'] for r in a])[0])} B {num(mean_sd([r['final'] for r in rb])[0])} C {num(mean_sd([r['final'] for r in rc])[0])}; B-A final: {verdict([r['final'] for r in rb], [r['final'] for r in a])}")
    print("No winner declared: search helps where clearances are tight and the score is informative; it costs edits and can hurt when the score is noisy or the budget tiny")
    print("Real FORGE-Tree on OpenVLA / Octo, LIBERO, a GPU: 本页未运行; Huang et al. results 以论文为准")


if __name__ == "__main__":
    main()
