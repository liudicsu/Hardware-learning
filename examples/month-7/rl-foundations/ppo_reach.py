#!/usr/bin/env python3
"""ppo_reach.py: 1-D reach MDP trained with a clipped-surrogate (PPO-style) policy, 3 seeds.

Toy environment: state is position in [-1, 1], action is a step in [-0.2, 0.2], reward is
−|x − goal| each step, episode length 20, goal at +0.8. The policy is a linear Gaussian:
mean = tanh(w · x + b) · 0.2. We take several epochs of clipped-ratio updates on each
batch of rollouts (the PPO idea from Schulman et al. 2017), without a neural net or
PyTorch, so the expected table is reproducible with the standard library only.

On a learner machine with GPU optional: Stable-Baselines3's PPO is meant to run primarily
on the CPU when not using a CNN; see the SB3 PPO docs. That path is not run here.
usage: python3 ppo_reach.py
"""
from __future__ import annotations

import math
import random

GOAL = 0.8
HORIZON = 20
ACTION_SCALE = 0.2
GAMMA = 0.99
CLIP = 0.2
LR = 0.12
EPOCHS = 6
ROLLOUTS = 48
ITERS = 80
SEEDS = (0, 1, 2)


def step_env(x: float, a: float) -> tuple[float, float, bool]:
    a = max(-ACTION_SCALE, min(ACTION_SCALE, a))
    nx = max(-1.0, min(1.0, x + a))
    r = -abs(nx - GOAL)
    done = False
    return nx, r, done


def discount(rewards: list[float], gamma: float = GAMMA) -> list[float]:
    g = 0.0
    out = [0.0] * len(rewards)
    for t in range(len(rewards) - 1, -1, -1):
        g = rewards[t] + gamma * g
        out[t] = g
    return out


class Policy:
    """Linear Gaussian: a ~ N(tanh(w x + b) * ACTION_SCALE, sigma)."""

    def __init__(self, rng: random.Random):
        self.w = rng.uniform(-0.3, 0.3)
        self.b = rng.uniform(-0.3, 0.3)
        self.log_std = -1.0  # sigma ≈ 0.37 * ACTION_SCALE after tanh scale

    def mean(self, x: float) -> float:
        return math.tanh(self.w * x + self.b) * ACTION_SCALE

    def std(self) -> float:
        return math.exp(self.log_std) * ACTION_SCALE

    def act(self, x: float, rng: random.Random) -> tuple[float, float]:
        mu = self.mean(x)
        sig = self.std()
        a = mu + sig * rng.gauss(0.0, 1.0)
        a = max(-ACTION_SCALE, min(ACTION_SCALE, a))
        # log prob under unclipped Gaussian (for ratio); clamp a for env only
        logp = -0.5 * ((a - mu) / sig) ** 2 - math.log(sig) - 0.5 * math.log(2 * math.pi)
        return a, logp

    def logp(self, x: float, a: float) -> float:
        mu = self.mean(x)
        sig = self.std()
        return -0.5 * ((a - mu) / sig) ** 2 - math.log(sig) - 0.5 * math.log(2 * math.pi)


def collect(policy: Policy, rng: random.Random, n: int = ROLLOUTS):
    batch = []
    returns = []
    for _ in range(n):
        x = rng.uniform(-1.0, -0.2)
        traj = []
        rewards = []
        for _t in range(HORIZON):
            a, lp = policy.act(x, rng)
            nx, r, _ = step_env(x, a)
            traj.append((x, a, lp))
            rewards.append(r)
            x = nx
        Gs = discount(rewards)
        returns.append(sum(rewards))  # undiscounted episode return for the table
        for (x, a, lp), G in zip(traj, Gs):
            batch.append((x, a, lp, G))
    return batch, sum(returns) / len(returns)


def ppo_update(policy: Policy, batch):
    # Normalise advantages
    Gs = [b[3] for b in batch]
    mean_g = sum(Gs) / len(Gs)
    var = sum((g - mean_g) ** 2 for g in Gs) / len(Gs)
    std = math.sqrt(var) + 1e-8
    for _ in range(EPOCHS):
        for x, a, old_lp, G in batch:
            adv = (G - mean_g) / std
            new_lp = policy.logp(x, a)
            ratio = math.exp(max(-20.0, min(20.0, new_lp - old_lp)))
            unclipped = ratio * adv
            clipped = max(1.0 - CLIP, min(1.0 + CLIP, ratio)) * adv
            # surrogate to maximise; gradient via finite difference on w, b
            # analytical d logp / d mu * d mu / d param
            mu = policy.mean(x)
            sig = policy.std()
            dlogp_dmu = (a - mu) / (sig * sig)
            # mu = tanh(z)*ACTION_SCALE, z = w x + b
            z = policy.w * x + policy.b
            dmu_dz = (1.0 - math.tanh(z) ** 2) * ACTION_SCALE
            # Use clipped objective: if ratio outside clip and adv has the wrong sign, skip
            if (adv > 0 and ratio > 1.0 + CLIP) or (adv < 0 and ratio < 1.0 - CLIP):
                continue
            # ascend: param += LR * adv * dlogp/dparam  (on-policy PG inside the clip)
            policy.w += LR * adv * dlogp_dmu * dmu_dz * x
            policy.b += LR * adv * dlogp_dmu * dmu_dz


def train(seed: int) -> tuple[float, float, float]:
    rng = random.Random(seed)
    policy = Policy(rng)
    # initial return
    _, r0 = collect(policy, random.Random(seed + 1000), n=16)
    for it in range(ITERS):
        batch, _ = collect(policy, rng)
        ppo_update(policy, batch)
    _, rT = collect(policy, random.Random(seed + 2000), n=32)
    # final mean distance to goal over 32 eval rollouts (greedy mean action)
    dists = []
    for k in range(32):
        erng = random.Random(seed + 3000 + k)
        x = erng.uniform(-1.0, -0.2)
        for _ in range(HORIZON):
            a = policy.mean(x)
            x, _, _ = step_env(x, a)
        dists.append(abs(x - GOAL))
    return r0, rT, sum(dists) / len(dists)


def main() -> None:
    print(f"1-D reach  goal={GOAL}  horizon={HORIZON}  gamma={GAMMA}  clip={CLIP}")
    print("seed  return_init  return_final  mean_|x-goal|_greedy")
    finals = []
    for s in SEEDS:
        r0, rT, d = train(s)
        finals.append(rT)
        print(f"{s:4d}  {r0:11.3f}  {rT:12.3f}  {d:20.4f}")
    print(f"mean final return over {len(SEEDS)} seeds: {sum(finals)/len(finals):.3f}")


if __name__ == "__main__":
    main()
