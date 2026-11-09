#!/usr/bin/env python3
"""Diffusion Forcing stand-in: what the training noise pattern does to a causal token model. Stdlib only.

Model assumptions (also stated in the lesson prose):
  tokens are 2D points from a noisy limit-cycle map x' = R(0.3) x (1 + 0.15 (1 - |x|^2)) + N(0, 0.02^2 I);
  the true orbit is the unit circle. Training sequences are 8 tokens long and start at radius
  U(0.2, 1.2), so they contain growing and shrinking spirals. The causal denoiser is the SAME
  model class for every arm: for each pair of noise levels (k_prev, k_cur) one linear map
  x0_hat(cur) = P x~prev + Q x~cur + b, fit by least squares (tiny ridge), where x~ = sqrt(abar_k) x
  + sqrt(1 - abar_k) eps. K = 10 levels, cosine schedule abar_k = cos^2(pi k / 20), abar_10 = 0.
  Sampling one token runs deterministic DDIM from level 10 to 0 with the previous token as context.
  This is a linear stand-in for the paper's RNN; it is not a video model and not a robot policy.

Arms (Common random numbers: per seed the same training sequences, the same per-token noise
vectors and the same uniform draws that set noise levels; per evaluation episode the same start,
true continuation, initial token noise and context noise):
  A_teacher   teacher forcing: history always clean (k_prev = 0), current token at a random level;
              at sampling time the model's own previous output is fed back as if clean
  B_dforcing  Diffusion Forcing: k_prev and k_cur drawn independently per token; at sampling time
              the previous output is re-noised to k_small = 1 before it is used (the paper's
              stabilisation, App. B.4), which the model has been trained to discount
  C_fullseq   causal full-sequence diffusion: one shared level for every token (k_prev = k_cur);
              at sampling time the context is re-noised to the current token's level at every step
              (the only pattern it has seen), a stand-in for conditioning without reconstruction guidance

Stability criterion: sampling one token is affine in the previous token for fixed noise, so its
Jacobian G is exact; rho(G) < 1 means fed-back history contracts, rho(G) > 1 means it grows every step.

Regimes: in_horizon (8 tokens, mse to the shared true continuation, jit = mean |x_{t+1} - f(x_t)|),
past_horizon (128 tokens: div = share of episodes whose radius ever exceeds 3, amp = mean |r - 1|
over tokens 9..128 with r capped at 3), guided_s8 / guided_s32 (an 8-token plan must end near a goal;
guidance stand-in = best of S sampled plans by final distance, not the paper's gradient / Monte
Carlo guidance; goal = final distance of the chosen plan, jit = its dynamics residual).

Labels: tie = identical on every seed; |m| < 1e-9 and sd < 1e-9 = numerically zero
(floating-point residue), effectively a tie, no sign count; |paired mean| <= sd = near-tie / small
gap within seed noise; |m| > sd = consistent gap (small if |m| < 20 % of the smaller arm mean, else
clear), always with a sign count.
Video / robot results and GPU training: 本页未运行. Paper numbers: 以论文为准.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
K = 10
ABAR = tuple(0.0 if k == K else math.cos(math.pi * k / (2 * K)) ** 2 for k in range(K + 1))
THETA, GAMMA, SIG_W = 0.3, 0.15, 0.02
N_TRAIN, T_TRAIN = 2000, 8
EPISODES = 20
T_PAST = 128
K_SMALL = 1
ARMS = ("A_teacher", "B_dforcing", "C_fullseq")
REGIMES = (
    ("in_horizon", ("mse", "jit")),
    ("past_horizon", ("div", "amp")),
    ("guided_s8", ("goal", "jit")),
    ("guided_s32", ("goal", "jit")),
)


def f(x):
    """True limit-cycle map (deterministic part)."""
    g = 1.0 + GAMMA * (1.0 - (x[0] ** 2 + x[1] ** 2))
    c, s = math.cos(THETA), math.sin(THETA)
    return (g * (c * x[0] - s * x[1]), g * (s * x[0] + c * x[1]))


def noisy(x, k, e):
    a = ABAR[k]
    return (math.sqrt(a) * x[0] + math.sqrt(1 - a) * e[0], math.sqrt(a) * x[1] + math.sqrt(1 - a) * e[1])


def solve(a, b):
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(m[r][i]))
        m[i], m[p] = m[p], m[i]
        for r in range(n):
            if r != i:
                q = m[r][i] / m[i][i]
                for c in range(i, n + 1):
                    m[r][c] -= q * m[i][c]
    return [m[i][n] / m[i][i] for i in range(n)]


def fit(rows):
    """Least squares (ridge 1e-6) for x0_hat = W [x~prev, x~cur, 1]."""
    d = 5
    a = [[1e-6 if i == j else 0.0 for j in range(d)] for i in range(d)]
    b = [[0.0] * d for _ in range(2)]
    for ft, y in rows:
        for i in range(d):
            for j in range(d):
                a[i][j] += ft[i] * ft[j]
            for o in range(2):
                b[o][i] += ft[i] * y[o]
    return [solve(a, b[o]) for o in range(2)]


def training_draws(seed):
    """Common random numbers for training: sequences, noise vectors, level draws."""
    rng = random.Random(7000 + seed)
    data, draws = [], []
    for _ in range(N_TRAIN):
        r, ph = rng.uniform(0.2, 1.2), rng.uniform(0, 2 * math.pi)
        x = (r * math.cos(ph), r * math.sin(ph))
        seq = [x]
        for _ in range(T_TRAIN - 1):
            y = f(x)
            x = (y[0] + rng.gauss(0, SIG_W), y[1] + rng.gauss(0, SIG_W))
            seq.append(x)
        data.append(seq)
        u_seq = rng.random()
        draws.append([(rng.random(), rng.random(), u_seq, (rng.gauss(0, 1), rng.gauss(0, 1)),
                       (rng.gauss(0, 1), rng.gauss(0, 1))) for _ in range(T_TRAIN)])
    return data, draws


def level(u):
    return min(K, int(u * (K + 1)))


def train(arm, data, draws):
    rows = {}
    for seq, dr in zip(data, draws):
        for t in range(1, T_TRAIN):
            u_prev, u_cur, u_seq, e_prev, e_cur = dr[t]
            if arm == "A_teacher":
                kp, kc = 0, level(u_cur)
            elif arm == "B_dforcing":
                kp, kc = level(u_prev), level(u_cur)
            else:
                kp = kc = level(u_seq)
            xp, xc = noisy(seq[t - 1], kp, e_prev), noisy(seq[t], kc, e_cur)
            rows.setdefault((kp, kc), []).append(((xp[0], xp[1], xc[0], xc[1], 1.0), seq[t]))
    return {key: fit(v) for key, v in rows.items()}


def predict(w, xp, xc):
    ft = (xp[0], xp[1], xc[0], xc[1], 1.0)
    return (sum(a * b for a, b in zip(w[0], ft)), sum(a * b for a, b in zip(w[1], ft)))


def sample_token(models, arm, prev, init, ctx_noise, k_small=K_SMALL):
    """Deterministic DDIM from level K to 0 for one token, given the previous (generated) token."""
    x = init
    for k in range(K, 0, -1):
        kp = 0 if arm == "A_teacher" else (k_small if arm == "B_dforcing" else k)
        x0 = predict(models[(kp, k)], noisy(prev, kp, ctx_noise), x)
        a, an = ABAR[k], ABAR[k - 1]
        eh = ((x[0] - math.sqrt(a) * x0[0]) / math.sqrt(1 - a), (x[1] - math.sqrt(a) * x0[1]) / math.sqrt(1 - a))
        x = (math.sqrt(an) * x0[0] + math.sqrt(1 - an) * eh[0], math.sqrt(an) * x0[1] + math.sqrt(1 - an) * eh[1])
    return x


def token_gain(models, arm, k_small=K_SMALL):
    """Spectral radius of G = d(new token)/d(previous token). sample_token is affine in the previous
    token for fixed noise, so two unit differences give G exactly (up to round-off). rho(G) < 1 is
    the stability criterion for feeding generated tokens back: the deterministic part contracts."""
    z = ((0.0, 0.0), (0.0, 0.0))
    o = sample_token(models, arm, (0.0, 0.0), *z, k_small)
    c1 = sample_token(models, arm, (1.0, 0.0), *z, k_small)
    c2 = sample_token(models, arm, (0.0, 1.0), *z, k_small)
    a, b, c, d = c1[0] - o[0], c2[0] - o[0], c1[1] - o[1], c2[1] - o[1]
    tr, det = a + d, a * d - b * c
    disc = tr * tr / 4 - det
    if disc >= 0:
        return max(abs(tr / 2 + math.sqrt(disc)), abs(tr / 2 - math.sqrt(disc)))
    return math.sqrt(det)


def episode_draws(regime, seed, ep):
    """Common random numbers for one evaluation episode, shared by all arms."""
    rng = random.Random(100000 * [r[0] for r in REGIMES].index(regime) + 1000 * seed + ep)
    ph = rng.uniform(0, 2 * math.pi)
    x0 = (math.cos(ph), math.sin(ph))
    truth = [x0]
    for _ in range(T_TRAIN):
        y = f(truth[-1])
        truth.append((y[0] + rng.gauss(0, SIG_W), y[1] + rng.gauss(0, SIG_W)))
    n_plans = {"guided_s8": 8, "guided_s32": 32}.get(regime, 1)
    length = T_PAST if regime == "past_horizon" else T_TRAIN
    noise = [[((rng.gauss(0, 1), rng.gauss(0, 1)), (rng.gauss(0, 1), rng.gauss(0, 1))) for _ in range(length)]
             for _ in range(n_plans)]
    return x0, truth, noise


def rollout(models, arm, x0, noise_row, k_small=K_SMALL):
    xs, x = [x0], x0
    for init, ctx in noise_row:
        x = sample_token(models, arm, x, init, ctx, k_small)
        xs.append(x)
        if math.hypot(*x) > 1e6:
            break
    return xs


def jitter(xs):
    return sum(math.dist(xs[t + 1], f(xs[t])) for t in range(len(xs) - 1)) / (len(xs) - 1)


def run_episode(regime, models, arm, x0, truth, noise, k_small=K_SMALL):
    if regime == "in_horizon":
        xs = rollout(models, arm, x0, noise[0], k_small)
        mse = sum((xs[t][0] - truth[t][0]) ** 2 + (xs[t][1] - truth[t][1]) ** 2 for t in range(1, T_TRAIN + 1)) / T_TRAIN
        return {"mse": mse, "jit": jitter(xs)}
    if regime == "past_horizon":
        xs = rollout(models, arm, x0, noise[0], k_small)
        rs = [min(math.hypot(*x), 3.0) for x in xs[1:]] + [3.0] * (T_PAST + 1 - len(xs))
        return {"div": 1.0 if max(rs) >= 3.0 else 0.0, "amp": sum(abs(r - 1.0) for r in rs[T_TRAIN:]) / (T_PAST - T_TRAIN)}
    goal = truth[T_TRAIN]
    best = min((rollout(models, arm, x0, row) for row in noise), key=lambda xs: math.dist(xs[-1], goal))
    return {"goal": math.dist(best[-1], goal), "jit": jitter(best)}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
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


NUM_ZERO = 1e-9  # |m| and sd both below this: floating-point residue, not a gap


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(mean_sd(xa)[0], mean_sd(xb)[0]):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def main() -> None:
    print("Synthetic 2D limit-cycle tokens; shared training sequences / noise / levels and shared evaluation draws; "
          "linear stand-in denoiser, not a video model or robot")
    print(f"seeds={len(SEEDS)} train={N_TRAIN}x{T_TRAIN} tokens K={K} cosine levels k_small={K_SMALL} "
          f"episodes={EPISODES} past horizon={T_PAST}")
    models = {seed: None for seed in SEEDS}
    for seed in SEEDS:
        data, draws = training_draws(seed)
        models[seed] = {arm: train(arm, data, draws) for arm in ARMS}
    for arm in ARMS:
        print(f"{arm} one-token gain rho(G) per seed: " + " ".join(f"{token_gain(models[s][arm], arm):.4f}" for s in SEEDS))
    print("B_dforcing k_small=0 rho(G) per seed: " + " ".join(f"{token_gain(models[s]['B_dforcing'], 'B_dforcing', 0):.4f}" for s in SEEDS)
          + " (rho < 1: generated history contracts; rho > 1: it grows)")
    print("regime arm metrics  (mean+-sd over seeds of the per-seed episode means)")
    kept = {}
    for regime, metrics in REGIMES:
        per = {arm: {m: [] for m in metrics} for arm in ARMS}
        for seed in SEEDS:
            acc = {arm: {m: 0.0 for m in metrics} for arm in ARMS}
            for ep in range(EPISODES):
                x0, truth, noise = episode_draws(regime, seed, ep)
                for arm in ARMS:
                    out = run_episode(regime, models[seed][arm], arm, x0, truth, noise)
                    for m in metrics:
                        acc[arm][m] += out[m] / EPISODES
            for arm in ARMS:
                for m in metrics:
                    per[arm][m].append(acc[arm][m])
        kept[regime] = per
        for arm in ARMS:
            print(f"{regime} {arm} " + " ".join("{}={}+-{}".format(m, *map(num, mean_sd(per[arm][m]))) for m in metrics))
        for a, b in (("B_dforcing", "A_teacher"), ("C_fullseq", "B_dforcing")):
            for m in metrics:
                print(f"{regime} paired {a[0]}-{b[0]} {m}: {verdict(per[a][m], per[b][m])}")
    for ks in (0, 1, 2):
        mse, div = [], []
        for seed in SEEDS:
            a = b = 0.0
            for ep in range(EPISODES):
                x0, truth, noise = episode_draws("in_horizon", seed, ep)
                a += run_episode("in_horizon", models[seed]["B_dforcing"], "B_dforcing", x0, truth, noise, ks)["mse"] / EPISODES
                x0, truth, noise = episode_draws("past_horizon", seed, ep)
                b += run_episode("past_horizon", models[seed]["B_dforcing"], "B_dforcing", x0, truth, noise, ks)["div"] / EPISODES
            mse.append(a)
            div.append(b)
        print(f"B_dforcing k_small={ks}: in_horizon mse={'{}+-{}'.format(*map(num, mean_sd(mse)))} "
              f"past_horizon div={'{}+-{}'.format(*map(num, mean_sd(div)))}")
        if ks == 0:
            print(f"in_horizon paired B(k_small=0)-A mse: {verdict(mse, kept['in_horizon']['A_teacher']['mse'])}")
    print("in_horizon: re-noising the history costs B accuracy inside the training length; A uses the clean history")
    print("past_horizon: A feeds its own output back as clean history and its growing linear map diverges")
    print("guided: best-of-S selection rewards diverse samples; the chosen plan's jit shows whether it is dynamically consistent")
    print("k_small=0 turns B's sampler into teacher-forcing-style feedback: in-horizon it is within seed noise of A, past the horizon it diverges like A")
    print("C here is causal and token-by-token; a non-causal full-sequence planner with joint gradient guidance is not modelled")
    print("No winner declared; Diffusion Forcing video / planning / Franka results 以论文为准; GPU training 本页未运行")


if __name__ == "__main__":
    main()
