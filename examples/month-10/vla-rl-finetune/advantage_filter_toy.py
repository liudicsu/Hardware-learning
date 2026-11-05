"""advantage_filter_toy.py: behaviour cloning that keeps only steps with A > 0 (stdlib).

Same 10-state lock chain as 10.6 (wrong action -> back to state 0, goal at
state 9, at most 30 steps). A mediocre behaviour policy (think: an SFT'd
VLA, or teleop plus autonomous rollouts) records 40 episodes. It gets most
states right but is worse than a coin flip in states 2 and 5.

1. Value from the log: V(s) = mean of "minus steps to finish" over every
   visit to s (a timed-out episode counts its remaining steps plus a
   30-step penalty). This is the flavour of value pi*0.6 / RECAP describes
   (predicting how far you are from done); here it is a plain average.
2. Advantage per logged step: A = -1 + V(s') - V(s), with V(goal) = 0.
3. Three tabular "policies" built by counting logged actions per state:
     bc            every step, equal weight
     success_only  only steps from episodes that reached the goal
     adv_filter    only steps with A > 0 (binary advantage weight)
   Each is evaluated by sampling actions in proportion to the counts,
   2000 rollouts with a fixed seed.
4. Same recipe on a log with no successes at all: V has nothing to rank,
   so the filter keeps noise (outcome-reward RL also needs a policy that
   already succeeds sometimes).
No VLA, no GPU: only the reweighting idea.
"""

import random

N = 10
H = 30
LOCK = [1, 0, 1, 0, 0, 0, 1, 0, 0]     # same right actions as rlpd_chain_toy.py
GOOD = [0.9, 0.9, 0.35, 0.9, 0.9, 0.4, 0.9, 0.9, 0.9]   # P(right action) of the behaviour policy
EPISODES = 40
EVAL = 2000


def step(s, a):
    if a != LOCK[s]:
        return 0, False
    s2 = s + 1
    return s2, s2 == N - 1


def collect(p_right, episodes, seed):
    rng = random.Random(seed)
    log = []   # list of episodes; each a list of (s, a, s2, done)
    for _ in range(episodes):
        ep, s = [], 0
        for _ in range(H):
            a = LOCK[s] if rng.random() < p_right[s] else 1 - LOCK[s]
            s2, done = step(s, a)
            ep.append((s, a, s2, done))
            if done:
                break
            s = s2
        log.append(ep)
    return log


def values(log):
    tot = [0.0] * N
    cnt = [0] * N
    for ep in log:
        success = ep[-1][3]
        L = len(ep)
        for t, (s, _, _, _) in enumerate(ep):
            g = -(L - t) if success else -(L - t) - H
            tot[s] += g
            cnt[s] += 1
    v = [tot[s] / cnt[s] if cnt[s] else -2.0 * H for s in range(N)]
    v[N - 1] = 0.0
    return v


def count_policy(steps):
    c = [[0, 0] for _ in range(N - 1)]
    for s, a in steps:
        c[s][a] += 1
    return c


def p_right(c, s):
    n = c[s][0] + c[s][1]
    return c[s][LOCK[s]] / n if n else 0.5


def evaluate(c, seed):
    rng = random.Random(seed)
    wins = lens = 0
    for _ in range(EVAL):
        s = 0
        for t in range(1, H + 1):
            a = LOCK[s] if rng.random() < p_right(c, s) else 1 - LOCK[s]
            s, done = step(s, a)
            if done:
                wins += 1
                lens += t
                break
    return wins / EVAL, (lens / wins if wins else float("nan"))


def build(log, v):
    all_steps, succ_steps, adv_steps = [], [], []
    for ep in log:
        success = ep[-1][3]
        for s, a, s2, done in ep:
            all_steps.append((s, a))
            if success:
                succ_steps.append((s, a))
            if -1.0 + v[s2] - v[s] > 0:
                adv_steps.append((s, a))
    return {
        "bc": (count_policy(all_steps), len(all_steps)),
        "success_only": (count_policy(succ_steps), len(succ_steps)),
        "adv_filter": (count_policy(adv_steps), len(adv_steps)),
    }


def report(title, log, seed):
    v = values(log)
    wins = sum(ep[-1][3] for ep in log)
    print(title)
    print(f"  logged episodes {len(log)}, successes {wins}, steps {sum(len(ep) for ep in log)}")
    print("  V(s): " + " ".join(f"{x:.1f}" for x in v))
    pols = build(log, v)
    print("  policy        kept_steps  P(right) in states 2 / 5  success  mean_steps_if_success")
    for name, (c, kept) in pols.items():
        sr, ml = evaluate(c, seed)
        mls = f"{ml:.1f}" if sr else "n/a"
        print(f"  {name:<12} {kept:>11}  {p_right(c, 2):>12.2f} / {p_right(c, 5):.2f}  {100 * sr:>6.1f} %  {mls:>8}")
    print()


def main():
    print("lock chain: wrong action -> state 0, goal at 9, at most 30 steps; A = -1 + V(s') - V(s)")
    print()
    report("A) mediocre log (right action 90 % of the time, 35 % in state 2, 40 % in state 5)",
           collect(GOOD, EPISODES, seed=3), seed=11)
    report("B) log with no successes (coin-flip policy, 6 episodes)",
           collect([0.5] * (N - 1), 6, seed=4), seed=11)
    print("in A the filter drops the wrong actions that BC copies; in B nothing ever")
    print("finished, so V cannot tell good steps from bad and the filter keeps noise.")


if __name__ == "__main__":
    main()
