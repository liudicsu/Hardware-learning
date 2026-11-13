#!/usr/bin/env python3
"""Synthetic generalized advantage estimation (GAE) toy.

A scalar two-action logistic policy (theta = 0, P(a=1) = P1 = 0.5) on a
finite episode of H steps; not a neural network, not MuJoCo, not SB3.
Paper biped / quadruped locomotion results 以论文为准; GPU / SB3 are not
run here (本页未运行).

Arms: A_lam1 (LAM = 1), B_lam (LAM = 0.95, the declared value inside the
0.92-0.98 range the paper reports as fastest on cart-pole, 以论文为准),
C_lam0 (LAM = 0).  Regimes: long_noisy (immediate reward, H = 50, reward
noise sd 1.0, noisy value with per-state sd 0.3); one_step (immediate,
H = 1, same noise); delayed_coarse (all reward at the final step, H = 30,
value a single constant equal to the mean true value over time).

True advantages are known in closed form; the value stand-in is either
the true state value plus a fixed per-state error or a coarse constant.
Gradients are estimated over N_EP = 16 episodes per repetition and
M_DRAW = 40 repetitions per seed; metrics are the variance of the
per-repetition gradient estimate and its mean squared error to g_true.

Common random numbers: one random.Random(f"{regime}/{seed}") stream per
(regime, seed) draws the value errors first, then all actions and reward
noises for every repetition and episode, in a fixed order before any arm
is evaluated; all arms share the same episodes and the same V.

Regimes and parameters were written before the first run.  Declared
expectations are printed as they come, without tuning.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
GAMMA = 0.99
P1 = 0.5
C_R = 1.0
SIG_R = 1.0
N_EP = 16
M_DRAW = 40
LAM_DECL = 0.95

ARMS = ("A_lam1", "B_lam", "C_lam0")
ARM_LAM = {"A_lam1": 1.0, "B_lam": LAM_DECL, "C_lam0": 0.0}
METRICS = ("grad_var", "grad_mse")
PAIRS = (("B_lam", "A_lam1"), ("C_lam0", "B_lam"), ("C_lam0", "A_lam1"))

REGIMES = {
    "long_noisy": {"H": 50, "mode": "immediate", "value": "noisy", "SIG_V": 0.3},
    "one_step": {"H": 1, "mode": "immediate", "value": "noisy", "SIG_V": 0.3},
    "delayed_coarse": {"H": 30, "mode": "delayed", "value": "coarse", "SIG_V": 0.0},
}
DECLARED = {
    "long_noisy": "B consistently lower grad_var than A - keep; C as it comes",
    "one_step": "all three lambdas tie or near-tie - keep",
    "delayed_coarse": "C (lambda = 0) loses on grad_mse to B and to A - keep",
}


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


def true_value(regime, t):
    cfg = REGIMES[regime]
    H = cfg["H"]
    if cfg["mode"] == "immediate":
        return sum(GAMMA ** ell for ell in range(H - t)) * C_R * P1
    return (GAMMA ** (H - 1 - t)) * H * C_R * P1


def true_grad(regime):
    cfg = REGIMES[regime]
    H = cfg["H"]
    total = 0.0
    for t in range(H):
        if cfg["mode"] == "immediate":
            total += (GAMMA ** t) * C_R * P1 * (1.0 - P1)
        else:
            total += (GAMMA ** t) * (GAMMA ** (H - 1 - t)) * C_R * P1 * (1.0 - P1)
    return total


def build_data(regime, seed, value_mode=None, sig_v=None):
    cfg = REGIMES[regime]
    H = cfg["H"]
    mode = cfg["mode"]
    if value_mode is None:
        value_mode = cfg["value"]
    if sig_v is None:
        sig_v = cfg["SIG_V"]
    rng = random.Random(f"{regime}/{seed}")
    errs = [rng.gauss(0.0, 1.0) for _ in range(H)]
    raw = []
    for _ in range(M_DRAW):
        eps = []
        for _ in range(N_EP):
            actions = [1 if rng.random() < P1 else 0 for _ in range(H)]
            if mode == "immediate":
                rewards = [C_R * actions[t] + rng.gauss(0.0, SIG_R) for t in range(H)]
            else:
                total = C_R * sum(actions)
                noise = rng.gauss(0.0, SIG_R) * math.sqrt(H)
                rewards = [0.0] * H
                rewards[H - 1] = total + noise
            eps.append((actions, rewards))
        raw.append(eps)
    true_v = [true_value(regime, t) for t in range(H)]
    if value_mode == "noisy":
        V = [true_v[t] + sig_v * errs[t] for t in range(H)]
    else:
        m = sum(true_v) / H
        V = [m] * H
    V.append(0.0)
    data = []
    for eps in raw:
        draw = []
        for actions, rewards in eps:
            deltas = [0.0] * H
            for t in range(H):
                deltas[t] = rewards[t] + GAMMA * V[t + 1] - V[t]
            draw.append((actions, deltas))
        data.append(draw)
    return H, data


def seed_metrics(regime, seed, lams, value_mode=None, sig_v=None):
    H, data = build_data(regime, seed, value_mode, sig_v)
    target = true_grad(regime)
    out = {}
    for lam in lams:
        gs = []
        for draw in data:
            total = 0.0
            for actions, deltas in draw:
                adv = [0.0] * H
                running = 0.0
                for t in range(H - 1, -1, -1):
                    running = deltas[t] + GAMMA * lam * running
                    adv[t] = running
                disc = 1.0
                for t in range(H):
                    total += disc * adv[t] * (actions[t] - P1)
                    disc *= GAMMA
            gs.append(total / N_EP)
        var = mean_sd(gs)[1] ** 2
        mse = sum((g - target) ** 2 for g in gs) / len(gs)
        out[lam] = (var, mse)
    return out


def run_regime(regime):
    acc = {arm: {key: [] for key in METRICS} for arm in ARMS}
    for seed in SEEDS:
        res = seed_metrics(regime, seed, (1.0, LAM_DECL, 0.0))
        for arm in ARMS:
            var, mse = res[ARM_LAM[arm]]
            acc[arm]["grad_var"].append(var)
            acc[arm]["grad_mse"].append(mse)
    return acc


def report(regime, res):
    print(f"{regime}:")
    print(f"  declared: {DECLARED[regime]}")
    for arm in ARMS:
        parts = []
        for key in METRICS:
            parts.append(f"{key} {fmt_pair(*mean_sd(res[arm][key]))}")
        print(f"  {arm} " + " ".join(parts))
    for a, b in PAIRS:
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: "
                  f"{verdict(res[a][key], res[b][key])}")


def alt_values(regime, lam, index, value_mode=None, sig_v=None):
    vals = []
    for seed in SEEDS:
        res = seed_metrics(regime, seed, (lam,), value_mode, sig_v)
        vals.append(res[lam][index])
    return vals


def main():
    print("GAE lambda toy: synthetic policy-gradient estimate for lambda = 1, 0.95, 0")
    print("not a neural net; not MuJoCo or SB3; paper locomotion results 以论文为准; "
          "GPU / SB3: 本页未运行")
    print(f"seeds={len(SEEDS)} gamma={num(GAMMA)} p1={num(P1)} c_r={num(C_R)} "
          f"sig_r={num(SIG_R)} n_ep={N_EP} m_draw={M_DRAW} (declared)")
    print("score d log pi(a)/d theta = a - P1; terminal value V(H) = 0")
    print("Regimes and parameters were written before the first run")
    for name in ("long_noisy", "one_step", "delayed_coarse"):
        print(f"hand_calc g_true {name} = {num(true_grad(name))}")
    print(f"hand_calc effective horizon 1/(1-GAMMA*LAM) for LAM = 0.95 = "
          f"{num(1.0 / (1.0 - GAMMA * LAM_DECL))}")
    print(f"hand_calc effective horizon 1/(1-GAMMA*LAM) for LAM = 1 = "
          f"{num(1.0 / (1.0 - GAMMA))}")
    print("hand_calc H = 1 check: A_hat_0 = delta_0 = r_0 - V(0) for LAM = 0, "
          "0.95, 1, so all three estimators equal r_0 - V(0)")
    base = {}
    for regime in ("long_noisy", "one_step", "delayed_coarse"):
        base[regime] = run_regime(regime)
        report(regime, base[regime])
    print("alternative parameters (declared before the run, same seeds, not adopted):")
    a_var = base["long_noisy"]["A_lam1"]["grad_var"]
    x = alt_values("long_noisy", 0.9, 0)
    print(f"  long_noisy with LAM = 0.9 (paired X-A grad_var): "
          f"{verdict(x, a_var)}")
    x = alt_values("long_noisy", 0.98, 0)
    print(f"  long_noisy with LAM = 0.98 (paired X-A grad_var): "
          f"{verdict(x, a_var)}")
    c_mse = base["delayed_coarse"]["C_lam0"]["grad_mse"]
    x = alt_values("delayed_coarse", 0.0, 1, value_mode="noisy", sig_v=0.3)
    print(f"  delayed_coarse with noisy value (SIG_V = 0.3) for C "
          f"(paired X-C grad_mse): "
          f"{verdict(x, c_mse)}")
    print("No winner beyond the declared lambda trade-off: B keeps grad_var low "
          "while C trades bias for a simpler estimate; paper biped / quadruped "
          "numbers stand as reported")
    print("Paper biped / quadruped results 以论文为准; GPU / SB3 / MuJoCo: 本页未运行")


if __name__ == "__main__":
    main()
