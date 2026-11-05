"""rlpd_chain_toy.py: why a few demos plus 50/50 sampling make sparse-reward RL possible (stdlib).

A 10-state "combination lock" chain stands in for a real-robot task:
- states 0..9, start at 0, goal is state 9;
- in every state one of two actions is right (fixed per state); the right one
  moves forward, the wrong one sends you back to 0 (think: the part slipped,
  someone resets the scene);
- reward is 1 only on reaching the goal, 0 everywhere else; at most 30 steps
  per episode, 40 episodes per run.

Three tabular Q-learning learners share the same replay update (8 sampled
transitions per environment step, epsilon-greedy with epsilon 0.1):
  online    online replay only, no demos
  one_buf   3 demos dumped into the same buffer as online data (uniform
            sampling, so the demos get diluted as online data piles up)
  rlpd_5050 3 demos in their own buffer, every sample is a coin flip between
            the demo buffer and the online buffer (RLPD's symmetric sampling)

20 seeds each. Reported: how many seeds ever reached the goal while
training, mean episode of the first success, how many resets the learner
caused (each one is a human walking over on a real robot), greedy success at
the end, and what share of the last episode's samples came from demos.
No neural nets, no ensembles, no LayerNorm: only the data-mixing idea.
"""

import random

N = 10            # states 0..9, goal = N - 1
H = 30            # steps per episode
EPISODES = 40
SEEDS = 20
ALPHA = 0.5
GAMMA = 0.9
EPS = 0.1
UPDATES = 8       # sampled Q updates per environment step
DEMOS = 3
LOCK_SEED = 7     # the "right" action per state is the same for every run


def make_lock():
    r = random.Random(LOCK_SEED)
    return [r.randrange(2) for _ in range(N - 1)]


LOCK = make_lock()


def step(s, a):
    """Return (next_state, reward, done)."""
    if a != LOCK[s]:
        return 0, 0.0, False          # wrong action: back to the start
    s2 = s + 1
    if s2 == N - 1:
        return s2, 1.0, True
    return s2, 0.0, False


def demo_transitions():
    out = []
    for _ in range(DEMOS):
        s = 0
        while True:
            a = LOCK[s]
            s2, r, done = step(s, a)
            out.append((s, a, r, s2, done))
            if done:
                break
            s = s2
    return out


def act(q, s, rng, eps):
    if rng.random() < eps or q[s][0] == q[s][1]:
        return rng.randrange(2)
    return 0 if q[s][0] > q[s][1] else 1


def update(q, t):
    s, a, r, s2, done = t
    target = r if done else r + GAMMA * max(q[s2])
    q[s][a] += ALPHA * (target - q[s][a])


def greedy_success(q):
    s = 0
    for _ in range(H):
        a = 0 if q[s][0] >= q[s][1] else 1   # fixed tie-break, no luck
        s, _, done = step(s, a)
        if done:
            return True
    return False


def run(mode, seed):
    rng = random.Random(1000 + seed)
    q = [[0.0, 0.0] for _ in range(N)]
    demos = demo_transitions()
    online = []
    first = None
    resets = 0
    from_demo = drawn = 0
    for ep in range(1, EPISODES + 1):
        s = 0
        ep_demo = ep_drawn = 0
        for _ in range(H):
            a = act(q, s, rng, EPS)
            s2, r, done = step(s, a)
            t = (s, a, r, s2, done)
            online.append(t)
            if a != LOCK[s]:
                resets += 1
            for _ in range(UPDATES):
                if mode == "online":
                    x = online[rng.randrange(len(online))]
                    d = False
                elif mode == "one_buf":
                    i = rng.randrange(len(demos) + len(online))
                    d = i < len(demos)
                    x = demos[i] if d else online[i - len(demos)]
                else:  # rlpd_5050
                    d = rng.random() < 0.5
                    x = demos[rng.randrange(len(demos))] if d else online[rng.randrange(len(online))]
                update(q, x)
                ep_demo += d
                ep_drawn += 1
            if done:
                if first is None:
                    first = ep
                break
            s = s2
        from_demo, drawn = ep_demo, ep_drawn
    return {
        "first": first,
        "resets": resets,
        "greedy": greedy_success(q),
        "demo_share": from_demo / drawn,
        "steps": len(online),
    }


def summarize(mode):
    rs = [run(mode, k) for k in range(SEEDS)]
    hit = [r["first"] for r in rs if r["first"] is not None]
    never = SEEDS - len(hit)
    mean_first = sum(hit) / len(hit) if hit else float("nan")
    resets = sum(r["resets"] for r in rs) / SEEDS
    greedy = sum(r["greedy"] for r in rs)
    share = sum(r["demo_share"] for r in rs) / SEEDS
    steps = sum(r["steps"] for r in rs) / SEEDS
    return len(hit), never, mean_first, resets, greedy, share, steps


def main():
    print("10-state lock chain: wrong action -> back to 0, reward only at the goal")
    print(f"right actions per state: {LOCK}")
    print(f"chance a uniformly random run of 9 moves opens the lock: 1/{2 ** (N - 1)}")
    print(f"{EPISODES} episodes x <= {H} steps, {UPDATES} sampled updates per step, epsilon {EPS}, {SEEDS} seeds")
    print(f"demos: {DEMOS} x {N - 1} transitions = {DEMOS * (N - 1)} transitions")
    print()
    print("mode       reached  never  first_ep  resets/run  greedy_end  demo_share_last  env_steps/run")
    rows = {}
    for mode in ("online", "one_buf", "rlpd_5050"):
        rows[mode] = summarize(mode)
        hit, never, mf, rs, g, sh, st = rows[mode]
        print(f"{mode:<10} {hit:>4}/{SEEDS}  {never:>5}  {mf:>8.1f}  {rs:>10.1f}  {g:>7}/{SEEDS}  {100 * sh:>13.1f} %  {st:>13.1f}")
    print()
    o, b, p = rows["online"], rows["one_buf"], rows["rlpd_5050"]
    print(f"resets per run: online {o[3]:.1f} vs rlpd_5050 {p[3]:.1f} (each reset = a person re-staging the scene)")
    print(f"demo share of the last episode's samples: one_buf {100 * b[5]:.1f} %, rlpd_5050 {100 * p[5]:.1f} %")
    print("note: tabular Q never forgets, so one_buf still works here; with a neural critic the")
    print("diluted demos are what RLPD found weaker than keeping a fixed 50/50 split.")


if __name__ == "__main__":
    main()
