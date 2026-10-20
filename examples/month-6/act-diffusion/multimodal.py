"""multimodal.py: why averaging fails on multimodal demonstrations, and what action chunks and diffusion change.

A point gripper starts near (0, 0) and must reach GOAL (0, 1). A square block of side 0.3 m sits in the way,
centred at (0, 0.5). The expert drives straight up to a fork at (0, 0.2) and then passes it on the left or on the right, 50/50, chosen at the start of each
demonstration: both are equally good, so the demonstrations are multimodal. Each step moves at most 0.05 m
plus 0.5 cm of actuator noise per axis. Success: within 0.05 m of GOAL inside 60 steps without touching the block.

Policies (all look at the K = 10 recorded frames nearest the current position):
  average    the mean of their actions; this is what a network trained with a squared-error loss predicts
  sample     the action of one of them, chosen at random, every step
  chunk N    pick one of them at random and play the next N actions of its episode, then look again
             (action chunking, the core idea of ACT; ACT also blends overlapping chunks)
  diffusion  start from Gaussian noise and denoise a chunk of 8 actions in 20 DDPM steps, using the exact
             denoiser for the demonstration set (the function a diffusion policy's network is trained to
             approximate), then play the chunk and look again
Standard library only, fixed seeds.
"""
import math
import random

GOAL, BLOCK_Y, HALF, FORK_Y = (0.0, 1.0), 0.5, 0.15, 0.2
STEP, NOISE, MAX_STEPS, K = 0.05, 0.005, 60, 10


def hits_block(p):
    return abs(p[0]) <= HALF and abs(p[1] - BLOCK_Y) <= HALF


def toward(p, target):
    dx, dy = target[0] - p[0], target[1] - p[1]
    d = math.hypot(dx, dy)
    k = min(1.0, STEP / d) if d > 0 else 0.0
    return dx * k, dy * k


def expert(p, side):
    """Straight up to the fork at (0, 0.2), then to a waypoint beside the block, then to the goal.
    side is -1 (left) or +1 (right); before the fork both kinds of demo look the same."""
    if p[1] < FORK_Y and abs(p[0]) < 0.05:
        return toward(p, (0.0, FORK_Y + 0.05))
    if p[1] < 0.4 and abs(p[0]) < 0.28:
        return toward(p, (0.3 * side, 0.4))
    return toward(p, GOAL)


def run(choose, rng, record=None):
    """choose(p, t) returns a list of actions to play before asking again."""
    p = (rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03))
    plan, t = [], 0
    while t < MAX_STEPS:
        if not plan:
            plan = list(choose(p, t))
        a = plan.pop(0)
        if record is not None:
            record.append((p, a))
        p = (p[0] + a[0] + rng.gauss(0, NOISE), p[1] + a[1] + rng.gauss(0, NOISE))
        t += 1
        if hits_block(p):
            return 'block', t
        if math.hypot(p[0] - GOAL[0], p[1] - GOAL[1]) < 0.05:
            return 'success', t
    return 'timeout', t


def record_demos(n, rng):
    episodes = []
    for _ in range(n):
        side = rng.choice((-1, 1))
        rows = []
        run(lambda p, t: [expert(p, side)], rng, record=rows)
        episodes.append(rows)
    return episodes


class Demos:
    def __init__(self, episodes):
        self.frames = [(e, i, rows[i][0]) for e, rows in enumerate(episodes) for i in range(len(rows))]
        self.episodes = episodes

    def nearest(self, p, k=K):
        return sorted(self.frames, key=lambda f: (f[2][0] - p[0]) ** 2 + (f[2][1] - p[1]) ** 2)[:k]

    def chunk(self, frame, n):
        """The next n actions of that frame's episode, padded with zero moves at the end."""
        e, i, _ = frame
        acts = [a for _, a in self.episodes[e][i:i + n]]
        return acts + [(0.0, 0.0)] * (n - len(acts))


def average_policy(demos):
    def choose(p, t):
        near = demos.nearest(p)
        return [(sum(demos.chunk(f, 1)[0][0] for f in near) / K, sum(demos.chunk(f, 1)[0][1] for f in near) / K)]
    return choose


def chunk_policy(demos, n, rng):
    def choose(p, t):
        return demos.chunk(rng.choice(demos.nearest(p)), n)
    return choose


def diffusion_policy(demos, n, rng, steps=20):
    """DDPM sampling of an n-step action chunk with the exact denoiser of the K nearest demo chunks."""
    betas = [1e-4 + (0.2 - 1e-4) * s / (steps - 1) for s in range(steps)]
    alphas = [1 - b for b in betas]
    abar, prod = [], 1.0
    for a in alphas:
        prod *= a
        abar.append(prod)
    scale = 1 / STEP                     # work in units of one full step so the noise schedule fits

    def choose(p, t):
        data = [[v * scale for a in demos.chunk(f, n) for v in a] for f in demos.nearest(p)]
        dim = len(data[0])
        x = [rng.gauss(0, 1) for _ in range(dim)]
        for s in reversed(range(steps)):
            # exact denoiser: E[x0 | xs] for x0 drawn uniformly from data, xs = sqrt(abar) x0 + sqrt(1 - abar) noise
            logw = [-sum((xi - math.sqrt(abar[s]) * di) ** 2 for xi, di in zip(x, d)) / (2 * (1 - abar[s]))
                    for d in data]
            m = max(logw)
            w = [math.exp(v - m) for v in logw]
            x0 = [sum(wi * d[j] for wi, d in zip(w, data)) / sum(w) for j in range(dim)]
            if s == 0:
                x = x0
                break
            # DDPM posterior mean of x_{s-1} given xs and the predicted x0, plus its noise
            c0 = math.sqrt(abar[s - 1]) * betas[s] / (1 - abar[s])
            cs = math.sqrt(alphas[s]) * (1 - abar[s - 1]) / (1 - abar[s])
            sd = math.sqrt(betas[s] * (1 - abar[s - 1]) / (1 - abar[s]))
            x = [c0 * a0 + cs * xs + sd * rng.gauss(0, 1) for a0, xs in zip(x0, x)]
        return [(x[2 * j] / scale, x[2 * j + 1] / scale) for j in range(n)]
    return choose


def evaluate(label, make, n=100):
    rng = random.Random(2026)
    choose = make(random.Random(11))
    counts = {'success': 0, 'block': 0, 'timeout': 0}
    steps = []
    for _ in range(n):
        result, t = run(choose, rng)
        counts[result] += 1
        if result == 'success':
            steps.append(t)
    mean = f'{sum(steps) / len(steps):.1f}' if steps else '-'
    print(f'{label:<16} success {counts["success"]:>3}/100   hit block {counts["block"]:>3}   '
          f'timeout {counts["timeout"]:>3}   mean steps to goal {mean}')


def main():
    episodes = record_demos(40, random.Random(5))
    lefts = sum(1 for rows in episodes if min(p[0] for p, _ in rows) < -0.1)
    demos = Demos(episodes)
    print(f'40 expert demos: {lefts} pass on the left, {40 - lefts} on the right, {len(demos.frames)} frames')

    print('\nSideways part dx of the first action just past the fork, at (0, 0.23), 200 draws per policy')
    edges = [-0.05, -0.03, -0.01, 0.01, 0.03, 0.05]
    print('  dx bin (cm)  ' + ''.join(f'{100 * lo:+.0f}..{100 * hi:+.0f}'.rjust(9) for lo, hi in zip(edges, edges[1:])))
    rng = random.Random(3)
    near = [demos.chunk(f, 1)[0][0] for f in demos.nearest((0.0, 0.23))]
    rows = [('10 demo frames', near)]
    for label, choose in [('average', average_policy(demos)), ('sample', chunk_policy(demos, 1, rng)),
                          ('diffusion', diffusion_policy(demos, 1, rng))]:
        rows.append((label, [choose((0.0, 0.23), 0)[0][0] for _ in range(200)]))
    for label, dx in rows:
        bins = [sum(1 for v in dx if lo <= v < hi or (hi == edges[-1] and v == hi)) for lo, hi in zip(edges, edges[1:])]
        print(f'  {label:<14}' + ''.join(f'{c:>9}' for c in bins))

    print('\nRollouts: 100 each with 0.5 cm actuator noise, same seeds for every policy')
    evaluate('average', lambda r: average_policy(demos))
    evaluate('sample', lambda r: chunk_policy(demos, 1, r))
    for n in (4, 8, 16):
        evaluate(f'chunk {n}', lambda r, n=n: chunk_policy(demos, n, r))
    evaluate('diffusion 1', lambda r: diffusion_policy(demos, 1, r))
    evaluate('diffusion 8', lambda r: diffusion_policy(demos, 8, r))


if __name__ == '__main__':
    main()
