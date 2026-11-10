#!/usr/bin/env python3
"""Synthetic DDPG-style single critic vs TD3 vs clipped double Q without delay. Stdlib only.

Plant (continuing, 1-D): s' = clip(s + 0.5 a, -2, 2), a in [-1, 1], reward r = -s'^2 - 0.1 a^2 + noise
(noise sd SIGMA_R per regime, zero mean). The agent resets to a fresh start state every EP steps; the reset is
not treated as terminal, so every target bootstraps with discount GAMMA.
Function approximation: each critic is linear in quadratic features phi(s, a) = (1, s, a, s^2, a^2, s a);
the actor is a = clip(k s + b, -1, 1). Critics learn by minibatch SGD on squared TD error; the actor follows the
deterministic policy gradient dQ1/da * da/d(k, b). Targets are Polyak copies (TAU). Arms:
  A_ddpg      one critic, target y = r + GAMMA Q'(s', pi'(s')), actor and targets updated every step
  B_td3       two critics, y = r + GAMMA min(Q1', Q2')(s', pi'(s') + eps), eps ~ clip(N(0, 0.2), -0.5, 0.5),
              actor and targets updated every D = 2 critic steps (Fujimoto et al. 2018, Algorithm 1)
  C_cdq_nodelay  B with D = 1 (clipped double Q and smoothing, no delay)
Common random numbers: per seed the start states, exploration noise, reward noise, minibatch picks, target
smoothing noise and initial critic weights are drawn once and shared by every arm (one stream per role).
No integration step: the plant is a one-line map, not an ODE. Stability criterion instead: SGD on the critic
is stable when LR * |phi|^2 < 2 (the toy prints the largest |phi|^2 over the feature box and asserts
LR * max|phi|^2 < 2; the tests check a single-sample update shrinks the error at 0.98x and grows it at 1.02x
of LR = 2/|phi|^2). A run is flagged "diverged" if any weight leaves [-1e4, 1e4].
Metrics (on fixed evaluation start states, no exploration): bias = mean of Q1(s, pi(s)) minus the
noise-free discounted Monte Carlo return of the final policy (60 steps); ret = mean undiscounted 10-step
return of the final policy; absbias = |bias|.
Labels: tie = identical on every seed; numerically zero = |paired mean| and sd both < 1e-9 (effectively a
tie, no sign count); |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 % of the smaller arm
mean, else clear), with a sign count.
Not PPO (the clipped-ratio toy above) and not HER. MuJoCo / Gym / SB3 / GPU training: 本页未运行.
Paper numbers: 以论文为准.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
GAMMA = 0.8
EP = 10
STEPS = 3000
WARMUP = 200
BATCH = 8
LR = 0.01
LR_ACTOR = 0.002
TAU = 0.01
EXPL = 0.3
D = 2
SMOOTH_SD, SMOOTH_CLIP = 0.2, 0.5
BOUND = 1e4
NUM_ZERO = 1e-9
ARMS = ("A_ddpg", "B_td3", "C_cdq_nodelay")
# name: (reward noise sd, discount); pre-declared before the first run
REGIMES = {
    "noisy_reward": (1.0, GAMMA),
    "easy": (0.0, GAMMA),
    "bandit_no_bootstrap": (0.0, 0.0),
}
EVAL = [-1.5 + 0.25 * i for i in range(13)]


def phi(s, a):
    return (1.0, s, a, s * s, a * a, s * a)


def q(w, s, a):
    return sum(x * y for x, y in zip(w, phi(s, a)))


def dq_da(w, s, a):
    return w[2] + 2.0 * w[4] * a + w[5] * s


def act(k, b, s):
    return max(-1.0, min(1.0, k * s + b))


def step(s, a):
    return max(-2.0, min(2.0, s + 0.5 * a))


def max_phi2():
    """Largest |phi|^2 over the box s in [-2, 2], a in [-1, 1] (attained at a corner)."""
    return max(sum(x * x for x in phi(s, a)) for s in (-2.0, 2.0) for a in (-1.0, 1.0))


def shared_draws(seed):
    """Common random numbers: one stream per role, shared by every arm."""
    rngs = [random.Random(seed * 100 + i) for i in range(6)]
    n = STEPS
    return {
        "start": [rngs[0].uniform(-1.5, 1.5) for _ in range(n // EP + 1)],
        "expl": [rngs[1].gauss(0.0, EXPL) for _ in range(n)],
        "rnoise": [rngs[2].gauss(0.0, 1.0) for _ in range(n)],
        "pick": [[rngs[3].random() for _ in range(BATCH)] for _ in range(n)],
        "smooth": [[max(-SMOOTH_CLIP, min(SMOOTH_CLIP, rngs[4].gauss(0.0, SMOOTH_SD))) for _ in range(BATCH)] for _ in range(n)],
        "w0": [[rngs[5].uniform(-0.1, 0.1) for _ in range(6)] for _ in range(2)],
    }


def mc_return(k, b, s, gamma):
    g, disc = 0.0, 1.0
    for _ in range(60):
        a = act(k, b, s)
        s = step(s, a)
        g += disc * (-s * s - 0.1 * a * a)
        disc *= gamma
        if gamma == 0.0:
            break
    return g


def run(arm, regime, dr):
    sigma_r, gamma = REGIMES[regime]
    twin = arm != "A_ddpg"
    d = D if arm == "B_td3" else 1
    w = [list(dr["w0"][0]), list(dr["w0"][1])]
    wt = [list(w[0]), list(w[1])]
    k, b = 0.0, 0.0
    kt, bt = k, b
    buf = []
    s = dr["start"][0]
    for t in range(STEPS):
        if t % EP == 0:
            s = dr["start"][t // EP]
        a = max(-1.0, min(1.0, act(k, b, s) + dr["expl"][t]))
        s2 = step(s, a)
        r = -s2 * s2 - 0.1 * a * a + sigma_r * dr["rnoise"][t]
        buf.append((s, a, r, s2))
        s = s2
        if t < WARMUP:
            continue
        batch = [buf[int(u * len(buf))] for u in dr["pick"][t]]
        for j, (bs, ba, br, bs2) in enumerate(batch):
            a2 = act(kt, bt, bs2)
            if twin:
                a2 = max(-1.0, min(1.0, a2 + dr["smooth"][t][j]))
                nxt = min(q(wt[0], bs2, a2), q(wt[1], bs2, a2))
            else:
                nxt = q(wt[0], bs2, a2)
            y = br + gamma * nxt
            f = phi(bs, ba)
            for c in ((0, 1) if twin else (0,)):
                err = y - q(w[c], bs, ba)
                w[c] = [wi + LR / BATCH * err * fi for wi, fi in zip(w[c], f)]
        if any(abs(x) > BOUND for c in w for x in c):
            return None
        if (t - WARMUP) % d == 0:
            gk = gb = 0.0
            for bs, _, _, _ in batch:
                a0 = k * bs + b
                if -1.0 < a0 < 1.0:
                    g = dq_da(w[0], bs, a0)
                    gk += g * bs
                    gb += g
            k += LR_ACTOR * gk / BATCH
            b += LR_ACTOR * gb / BATCH
            for c in range(2):
                wt[c] = [TAU * x + (1 - TAU) * y_ for x, y_ in zip(w[c], wt[c])]
            kt, bt = TAU * k + (1 - TAU) * kt, TAU * b + (1 - TAU) * bt
    bias = sum(q(w[0], s0, act(k, b, s0)) - mc_return(k, b, s0, gamma) for s0 in EVAL) / len(EVAL)
    ret = 0.0
    for s0 in EVAL:
        x = s0
        for _ in range(EP):
            a = act(k, b, x)
            x = step(x, a)
            ret += -x * x - 0.1 * a * a
    return {"bias": bias, "absbias": abs(bias), "ret": ret / len(EVAL), "k": k}


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


KEYS = ("bias", "absbias", "ret")


def main():
    print("Synthetic DDPG-style vs TD3 vs clipped double Q without delay; linear critics on a 1-D plant; not MuJoCo / Gym")
    m2 = max_phi2()
    assert LR * m2 < 2.0
    print(f"GAMMA={GAMMA} EP={EP} STEPS={STEPS} BATCH={BATCH} LR={LR} LR_ACTOR={LR_ACTOR} TAU={TAU} D={D} smooth N(0,{SMOOTH_SD}) clip {SMOOTH_CLIP} seeds={len(SEEDS)}")
    print(f"critic SGD stability: max|phi|^2={m2:.1f}, LR*max|phi|^2={LR * m2:.4f} < 2 (limit LR={2 / m2:.4f}); no integration step")
    print("regime arm bias absbias ret  (mean+-sd over seeds)")
    draws = [shared_draws(s) for s in SEEDS]
    for regime, (sigma_r, gamma) in REGIMES.items():
        print(f"{regime} (reward noise sd={sigma_r}, gamma={gamma})")
        res = {arm: [run(arm, regime, d) for d in draws] for arm in ARMS}
        for arm in ARMS:
            ok = [r for r in res[arm] if r is not None]
            if len(ok) < len(SEEDS):
                print(f"  {arm} diverged (|w| > {BOUND:.0f}) on {len(SEEDS) - len(ok)} of {len(SEEDS)} seeds")
                continue
            print(f"  {arm} " + " ".join("{}+-{}".format(*map(num, mean_sd([r[k] for r in ok]))) for k in KEYS))
        for x, y in (("B_td3", "A_ddpg"), ("C_cdq_nodelay", "B_td3"), ("C_cdq_nodelay", "A_ddpg")):  # C-A added after the first run
            if any(r is None for r in res[x] + res[y]):
                print(f"  paired {x[0]}-{y[0]}: not compared (diverged)")
                continue
            for key in KEYS:
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[key] for r in res[x]], [r[key] for r in res[y]])}")
    print("No winner declared: the min of two critics trades overestimation for underestimation, and the delay halves actor updates")
    print("MuJoCo / Gym / SB3 / GPU training: 本页未运行; paper numbers 以论文为准")


if __name__ == "__main__":
    main()
