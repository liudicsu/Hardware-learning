"""Synthetic WorldVLA-style action-chunk attention mask. Stdlib only.

Model (stated in the lesson prose too): a linear-Gaussian stand-in, not a
Chameleon backbone and not image tokens.
  latent scene state  s ~ N(0, I3)
  observation         x = s + N(0, SIGMA_OBS^2 I3)     (what "vision" sees)
  demo action         a_k = c_k . s + N(0, SIGMA_DEMO^2), k = 1..H
  c_k = (cos(0.3 + 0.15 k), sin(0.3 + 0.15 k), 0.5): neighbouring actions in a
  chunk are strongly correlated, as in a smooth reach.
Limited action generalization (the paper's stated cause) is modelled as a decode
error: at test time every predicted action of every arm gets an extra
N(0, SIGMA_DEC^2) error before it is tokenized (same draw for every arm).
Every action (target, teacher-forcing input, prediction) passes through one shared
256-bin tokenizer per chunk step whose bin widths come from the training range.
Each arm is a ridge regression (LAM = 1e-3 per sample) fitted on the same
N_TRAIN demos:
  A_causal    default causal attention: step k sees x AND the previous action
              token; trained with teacher forcing (the demo's previous action),
              run on its OWN previous prediction at test time.
  B_mask      WorldVLA-style action mask: step k sees x only, never a prior action.
  C_parallel  one head emits all H steps at once from x (parallel decoding).
Common random numbers: per seed one set of train demos, one set of test scenes and
one set of observation / demo-noise draws is generated once and fed to all three
arms and all four regimes (a regime only changes H and the observation-noise
scale); no arm skips a noise source.
Metrics per seed over N_TEST test scenes: chunk RMSE against the noiseless
c_k . s, last-step RMSE, and success = share of scenes whose worst step error in
the chunk is below TOL. They are open-loop: blind to closed-loop recovery, to
decode latency and to the reactivity lost with long chunks.
No presumed winner. LIBERO numbers 以论文为准; GPU WorldVLA run 本页未运行.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
N_TRAIN, N_TEST, BINS, LAM, TOL, SIGMA_DEMO, SIGMA_DEC = 40, 200, 256, 1e-3, 0.5, 0.10, 0.15
REGIMES = (("H1_noisy_obs", 1, 0.3), ("H5_noisy_obs", 5, 0.3), ("H10_noisy_obs", 10, 0.3), ("H10_clean_obs", 10, 0.05))
ARMS = ("A_causal", "B_mask", "C_parallel")
H_MAX = max(r[1] for r in REGIMES)


def coef(k):
    return (math.cos(0.3 + 0.15 * k), math.sin(0.3 + 0.15 * k), 0.5)


def solve(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                for j in range(c, n + 1):
                    m[r][j] -= f * m[c][j]
    return [m[i][n] / m[i][i] for i in range(n)]


def ridge(rows, ys):
    d = len(rows[0])
    a = [[sum(r[i] * r[j] for r in rows) + (LAM * len(rows) if i == j else 0.0) for j in range(d)] for i in range(d)]
    return solve(a, [sum(r[i] * y for r, y in zip(rows, ys)) for i in range(d)])


def dot(w, v):
    return sum(p * q for p, q in zip(w, v))


def shared_draws(seed, horizon, sigma_obs):
    """Common random numbers: one draw per seed, shared by every arm AND every
    regime (regimes only change H and the observation-noise scale)."""
    rng = random.Random(seed)

    def scene():
        s = [rng.gauss(0, 1) for _ in range(3)]
        z = [rng.gauss(0, 1) for _ in range(3)]
        e = [rng.gauss(0, SIGMA_DEMO) for _ in range(H_MAX)]
        nu = [rng.gauss(0, SIGMA_DEC) for _ in range(H_MAX)]
        x = [v + sigma_obs * u for v, u in zip(s, z)]
        clean = [dot(coef(k), s) for k in range(1, horizon + 1)]
        return x, clean, [c + n for c, n in zip(clean, e)], nu

    return [scene() for _ in range(N_TRAIN)], [scene() for _ in range(N_TEST)]


def tokenizer(train, horizon):
    out = []
    for k in range(horizon):
        lo, hi = min(t[2][k] for t in train), max(t[2][k] for t in train)
        w = (hi - lo) / BINS
        out.append(lambda v, lo=lo, w=w: lo + (min(BINS - 1, max(0, int((v - lo) / w))) + 0.5) * w)
    return out


def fit_predict(arm, train, test, horizon):
    q = tokenizer(train, horizon)
    tgt = [[q[k](t[2][k]) for k in range(horizon)] for t in train]
    preds, beta = [], []
    if arm == "A_causal":
        ws = [ridge([t[0] for t in train], [y[0] for y in tgt])]
        for k in range(1, horizon):
            ws.append(ridge([t[0] + [y[k - 1]] for t, y in zip(train, tgt)], [y[k] for y in tgt]))
        for x, _, _, nu in test:
            p = [q[0](dot(ws[0], x) + nu[0])]
            for k in range(1, horizon):
                p.append(q[k](dot(ws[k], x + [p[-1]]) + nu[k]))
            preds.append(p)
        beta.extend(w[-1] for w in ws[1:])
    elif arm == "B_mask":
        ws = [ridge([t[0] for t in train], [y[k] for y in tgt]) for k in range(horizon)]
        for x, _, _, nu in test:
            preds.append([q[k](dot(ws[k], x) + nu[k]) for k in range(horizon)])
    else:
        xs = [t[0] for t in train]
        d = len(xs[0])
        g = [[sum(r[i] * r[j] for r in xs) + (LAM * len(xs) if i == j else 0.0) for j in range(d)] for i in range(d)]
        ginv = [solve(g, [1.0 if i == j else 0.0 for i in range(d)]) for j in range(d)]
        xty = [[sum(r[i] * y[k] for r, y in zip(xs, tgt)) for k in range(horizon)] for i in range(d)]
        w = [[sum(ginv[j][i] * xty[i][k] for i in range(d)) for j in range(d)] for k in range(horizon)]
        for x, _, _, nu in test:
            preds.append([q[k](dot(w[k], x) + nu[k]) for k in range(horizon)])
    return preds, beta


def metrics(preds, test, horizon):
    errs = [[p[k] - t[1][k] for k in range(horizon)] for p, t in zip(preds, test)]
    rmse = math.sqrt(sum(e * e for row in errs for e in row) / (len(errs) * horizon))
    last = math.sqrt(sum(row[-1] ** 2 for row in errs) / len(errs))
    succ = sum(max(abs(e) for e in row) < TOL for row in errs)
    return rmse, last, succ


def ms(v):
    m = sum(v) / len(v)
    return m, math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def fmt(x, nd=4):
    if x != 0 and abs(x) < 0.5 * 10 ** -nd:
        return f"{x:.2e}"
    return f"{x:.{nd}f}"


def sign_note(diffs, m):
    """How many seeds disagree in sign with the paired mean (zeros listed apart)."""
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def label(diffs, mean_a, mean_b, scale=1):
    """tie: identical on every seed; near-tie: |paired mean| <= paired sd;
    otherwise consistent (|mean| > sd), called small if |mean| < 20 % of the
    smaller arm mean. The 20 % rule only decides "small". "Consistent" means
    only |mean| > sd; the appended sign count (seeds whose paired difference
    has the opposite sign to the mean) separates sign-consistent gaps."""
    if all(d == 0 for d in diffs):
        return "tie: identical on every seed"
    m, sd = ms(diffs)
    if abs(m) <= sd:
        return f"near-tie / small gap, within seed noise (indistinguishable from 0 within +-{sd / scale:.4f})"
    base = "small but consistent gap, not a tie" if abs(m) < 0.2 * min(abs(mean_a), abs(mean_b)) else "clear gap, not a tie"
    return base + "; " + sign_note(diffs, m)


def main():
    print(f"seeds={len(SEEDS)} n_train={N_TRAIN} n_test={N_TEST} bins={BINS} sigma_demo={SIGMA_DEMO} sigma_dec={SIGMA_DEC} tol={TOL} lam={LAM}")
    print("regime arm chunk_rmse last_step_rmse success  (mean+-sd over seeds)")
    res = {}
    for name, horizon, sigma_obs in REGIMES:
        per, betas = {a: [] for a in ARMS}, []
        for seed in SEEDS:
            train, test = shared_draws(seed, horizon, sigma_obs)
            for a in ARMS:
                preds, beta = fit_predict(a, train, test, horizon)
                per[a].append(metrics(preds, test, horizon))
                betas.extend(beta)
        res[name] = per
        for a in ARMS:
            cols = [ms([r[i] for r in per[a]]) for i in range(3)]
            cols[2] = (cols[2][0] / N_TEST, cols[2][1] / N_TEST)
            print(f"{name} H={horizon} sigma_obs={sigma_obs} {a} " + " ".join(f"{m:.4f}+-{sd:.4f}" for m, sd in cols))
        if betas:
            print(f"{name} A_causal weight on its previous action token, mean over steps 2..H and seeds: {sum(betas) / len(betas):.3f}")
        for x, y in (("A_causal", "B_mask"), ("C_parallel", "B_mask")):
            for i, met in ((0, "chunk_rmse"), (1, "last_step_rmse"), (2, "success")):
                scale = N_TEST if i == 2 else 1  # success is compared as integer counts
                d = [p[i] - r[i] for p, r in zip(per[x], per[y])]
                m, sd = ms(d)
                ma, mb = ms([p[i] for p in per[x]])[0], ms([r[i] for r in per[y]])[0]
                print(f"{name} paired {x[0]}-{y[0]} {met} {fmt(m / scale)}+-{sd / scale:.4f}: {label(d, ma, mb, scale)}")
    print("H=1: a one-step chunk has no prior action to attend to, so the mask changes nothing")
    print("B vs C: with the prior actions masked, each step is a function of x only, so token-by-token and parallel decoding compute the same chunk here")
    print("No winner declared: the metrics are open-loop and blind to decode latency and to closed-loop recovery")
    print("LIBERO success rates 以论文为准; GPU WorldVLA run 本页未运行")


if __name__ == "__main__":
    main()
