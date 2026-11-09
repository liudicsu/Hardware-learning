"""Synthetic X-VLA-style embodiment soft prompts. Stdlib only.

Model (stated in the lesson prose too): a linear / bilinear stand-in, not the
0.9B flow-matching Transformer.
  task features   x ~ N(0, I_D), D = 6        (what the shared backbone sees)
  embodiment e    hidden hardware vector h_e in R^R
  demo action     a = (sum_j h_e[j] T_j) x + N(0, SIGMA^2 I_2)
  T_1..T_R are fixed 2 x D maps; R is the true number of hardware factors.
Arms, all fitted on the same demos:
  A_pooled       one linear map W x for every embodiment (no embodiment input)
  B_hard_id      the one-hot ID is the prompt (fixed, length = number of
                 embodiments): in this stand-in that is one separate linear head
                 per embodiment, nothing shared between embodiments
  C_soft_prompt  a = (sum_j p_e[j] B_j) x with a learned prompt p_e in R^K, K = 2,
                 per embodiment and a shared backbone B_1..B_K, fitted jointly by
                 alternating least squares (ALS_ITERS sweeps)
Adaptation to a held-out embodiment with N_NEW demos (Phase II stand-in):
  A_pooled       ridge fine-tune of W toward the pooled W        (2 D numbers)
  B_hard_id      a fresh head, ridge toward zero                 (2 D numbers)
  C_soft_prompt  backbone frozen, only a new prompt p_new fitted (K numbers);
                 the paper's second step (joint fine-tune) is not modelled.
Common random numbers: per (regime, seed) one set of hardware vectors, maps T_j,
train demos, demo noise, adaptation demos and test inputs is drawn once and fed
to all three arms; C's prompt initialisation comes from its own fixed seed.
Metrics per seed: action RMSE against the noiseless action on N_TEST test inputs
per seen embodiment, and on the held-out embodiment after adaptation. They are
blind to camera / action-space differences, to compute and to training stability.
No presumed winner. Benchmark numbers 以论文为准; GPU X-VLA run 本页未运行.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
D, K, SIGMA, LAM, ALS_ITERS, N_TEST, N_NEW = 6, 2, 0.10, 1e-3, 60, 100, 4
# name, number of seen embodiments, true hardware factors R, demos per embodiment
REGIMES = (("single_embodiment", 1, 2, 24), ("shared_low_rank", 6, 2, 8), ("unrelated_full_rank", 6, 6, 30))
ARMS = ("A_pooled", "B_hard_id", "C_soft_prompt")


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


def ridge(rows, ys, prior=None, lam=LAM):
    """argmin sum (y - w.r)^2 + lam * n * |w - prior|^2."""
    d, n = len(rows[0]), len(rows)
    prior = prior or [0.0] * d
    a = [[sum(r[i] * r[j] for r in rows) + (lam * n if i == j else 0.0) for j in range(d)] for i in range(d)]
    b = [sum(r[i] * y for r, y in zip(rows, ys)) + lam * n * prior[i] for i in range(d)]
    return solve(a, b)


def apply(w, x):
    return [sum(w[o][i] * x[i] for i in range(D)) for o in range(2)]


def rmse(w, xs, truth):
    err = [(p - t) ** 2 for x, tr in zip(xs, truth) for p, t in zip(apply(w, x), tr)]
    return math.sqrt(sum(err) / len(err))


def shared_draws(seed, n_emb, rank, n_demo):
    """Common random numbers: one draw per (regime, seed), shared by every arm."""
    rng = random.Random(1000 * seed + 10 * n_emb + rank)
    t = [[[rng.gauss(0, 1 / math.sqrt(D)) for _ in range(D)] for _ in range(2)] for _ in range(rank)]
    if rank == n_emb:  # unrelated: one private hardware factor per embodiment
        hs = [[1.0 if j == e else 0.0 for j in range(rank)] for e in range(n_emb)]
    else:
        hs = [[rng.gauss(0, 1) for _ in range(rank)] for _ in range(n_emb)]
    h_new = [rng.gauss(0, 1) for _ in range(rank)]

    def true_map(h):
        return [[sum(h[j] * t[j][o][i] for j in range(rank)) for i in range(D)] for o in range(2)]

    def demos(w, n):
        xs = [[rng.gauss(0, 1) for _ in range(D)] for _ in range(n)]
        return xs, [[v + rng.gauss(0, SIGMA) for v in apply(w, x)] for x in xs]

    maps = [true_map(h) for h in hs]
    train = [demos(w, n_demo) for w in maps]
    new_map = true_map(h_new)
    adapt = demos(new_map, N_NEW)
    test_x = [[rng.gauss(0, 1) for _ in range(D)] for _ in range(N_TEST)]
    return maps, train, new_map, adapt, test_x


def fit_pooled(train):
    xs = [x for d in train for x in d[0]]
    ys = [y for d in train for y in d[1]]
    return [ridge(xs, [y[o] for y in ys]) for o in range(2)]


def fit_head(xs, ys, prior=None):
    return [ridge(xs, [y[o] for y in ys], prior[o] if prior else None) for o in range(2)]


def prompt_map(p, b):
    return [[sum(p[j] * b[j][o][i] for j in range(K)) for i in range(D)] for o in range(2)]


def fit_prompt(xs, ys, b):
    rows, tgt = [], []
    for x, y in zip(xs, ys):
        feats = [apply(b[j], x) for j in range(K)]
        for o in range(2):
            rows.append([feats[j][o] for j in range(K)])
            tgt.append(y[o])
    return ridge(rows, tgt)


def fit_soft(train, seed):
    rng = random.Random(7919 + seed)  # C's own prompt initialisation
    prompts = [[rng.gauss(0, 1) for _ in range(K)] for _ in train]
    b = None
    for _ in range(ALS_ITERS):
        b = [[[0.0] * D for _ in range(2)] for _ in range(K)]
        for o in range(2):
            rows = [[p[j] * xi for j in range(K) for xi in x] for p, d in zip(prompts, train) for x in d[0]]
            ys = [y[o] for d in train for y in d[1]]
            w = ridge(rows, ys)
            for j in range(K):
                b[j][o] = w[j * D:(j + 1) * D]
        prompts = [fit_prompt(d[0], d[1], b) for d in train]
    return prompts, b


def run(seed, n_emb, rank, n_demo):
    maps, train, new_map, adapt, test_x = shared_draws(seed, n_emb, rank, n_demo)
    truth = [[apply(w, x) for x in test_x] for w in maps]
    truth_new = [apply(new_map, x) for x in test_x]
    pooled = fit_pooled(train)
    heads = [fit_head(d[0], d[1]) for d in train]
    prompts, b = fit_soft(train, seed)
    seen = {
        "A_pooled": sum(rmse(pooled, test_x, tr) for tr in truth) / n_emb,
        "B_hard_id": sum(rmse(h, test_x, tr) for h, tr in zip(heads, truth)) / n_emb,
        "C_soft_prompt": sum(rmse(prompt_map(p, b), test_x, tr) for p, tr in zip(prompts, truth)) / n_emb,
    }
    new = {
        "A_pooled": rmse(fit_head(adapt[0], adapt[1], pooled), test_x, truth_new),
        "B_hard_id": rmse(fit_head(adapt[0], adapt[1]), test_x, truth_new),
        "C_soft_prompt": rmse(prompt_map(fit_prompt(adapt[0], adapt[1], b), b), test_x, truth_new),
    }
    return seen, new


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


def label(diffs, mean_a, mean_b):
    """tie: identical on every seed; near-tie: |paired mean| <= paired sd;
    otherwise consistent (|mean| > sd), called small if |mean| < 20 % of the
    smaller arm mean. The 20 % rule only decides "small". "Consistent" means
    only |mean| > sd; the appended sign count (seeds whose paired difference
    has the opposite sign to the mean) separates sign-consistent gaps."""
    if all(d == 0 for d in diffs):
        return "tie: identical on every seed"
    m, sd = ms(diffs)
    if abs(m) <= sd:
        return f"near-tie / small gap, within seed noise (indistinguishable from 0 within +-{sd:.4f})"
    base = "small but consistent gap, not a tie" if abs(m) < 0.2 * min(abs(mean_a), abs(mean_b)) else "clear gap, not a tie"
    return base + "; " + sign_note(diffs, m)


def main():
    print(f"seeds={len(SEEDS)} D={D} K={K} sigma={SIGMA} lam={LAM} als_iters={ALS_ITERS} n_test={N_TEST} n_new={N_NEW}")
    print(f"numbers tuned to adapt to a new embodiment: A_pooled {2 * D}, B_hard_id {2 * D}, C_soft_prompt {K}")
    print("regime arm seen_rmse new_emb_rmse  (mean+-sd over seeds)")
    for name, n_emb, rank, n_demo in REGIMES:
        res = [run(seed, n_emb, rank, n_demo) for seed in SEEDS]
        for a in ARMS:
            s, n = ms([r[0][a] for r in res]), ms([r[1][a] for r in res])
            print(f"{name} E={n_emb} R={rank} demos={n_demo} {a} {s[0]:.4f}+-{s[1]:.4f} {n[0]:.4f}+-{n[1]:.4f}")
        for x, y in (("C_soft_prompt", "B_hard_id"), ("C_soft_prompt", "A_pooled"), ("B_hard_id", "A_pooled")):
            for i, met in ((0, "seen_rmse"), (1, "new_emb_rmse")):
                d = [r[i][x] - r[i][y] for r in res]
                m, sd = ms(d)
                print(f"{name} paired {x[0]}-{y[0]} {met} {fmt(m)}+-{sd:.4f}: {label(d, ms([r[i][x] for r in res])[0], ms([r[i][y] for r in res])[0])}")
    print("No winner declared: K = 2 prompts help only when embodiments share a few hardware factors")
    print("Benchmark success rates 以论文为准; GPU X-VLA run 本页未运行")


if __name__ == "__main__":
    main()
