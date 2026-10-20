"""bc_reach.py: behaviour cloning, covariate shift and DAgger on a point gripper in an L-shaped corridor.

The gripper moves in a plane (metres). The corridor runs from START (0, 0) along +x to the corner (1, 0),
then along +y to GOAL (1, 1); it is 0.2 m wide (walls 0.1 m either side of the centre line). Each step the
policy commands a displacement (dx, dy) of at most 0.05 m; the gripper moves by that plus actuator noise
(Gaussian, 0.01 m per axis). Success: within 0.05 m of GOAL inside 80 steps without touching a wall.

The expert is a scripted controller (pure pursuit of a point 0.15 m ahead on the centre line). Demonstrations
are recorded like a teleoperated dataset: one row per frame with episode_index, frame_index, the observation
(x, y) and the action (dx, dy). The learned policy is 1-nearest-neighbour behaviour cloning: look up the
recorded frame whose (x, y) is closest and replay its action. Standard library only, fixed seeds.
usage: python3 bc_reach.py [demos.csv]      (writes the 20-demo dataset to demos.csv if a name is given)
"""
import math
import random
import sys

START, CORNER, GOAL = (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)
HALF_WIDTH, STEP, NOISE, MAX_STEPS = 0.10, 0.05, 0.01, 80


def path_s(p):
    """Distance along the centre line of the point on it nearest p, and p's distance from the line."""
    x, y = p
    cx = min(max(x, 0.0), 1.0)                       # nearest point on the first leg, (cx, 0)
    cy = min(max(y, 0.0), 1.0)                       # nearest point on the second leg, (1, cy)
    d1, d2 = math.hypot(x - cx, y), math.hypot(x - 1.0, y - cy)
    return (cx, d1) if d1 < d2 else (1.0 + cy, d2)


def point_at(s):
    s = min(max(s, 0.0), 2.0)
    return (s, 0.0) if s <= 1.0 else (1.0, s - 1.0)


def in_corridor(p):
    x, y = p
    leg1 = -0.1 <= x <= 1.0 + HALF_WIDTH and abs(y) <= HALF_WIDTH
    leg2 = abs(x - 1.0) <= HALF_WIDTH and -HALF_WIDTH <= y <= 1.0 + HALF_WIDTH
    return leg1 or leg2


def expert(p):
    """Pure pursuit: aim at the centre-line point 0.15 m ahead of where we are, at most STEP per step."""
    s, _ = path_s(p)
    tx, ty = point_at(s + 0.15) if s < 1.85 else GOAL
    dx, dy = tx - p[0], ty - p[1]
    d = math.hypot(dx, dy)
    k = min(1.0, STEP / d) if d > 0 else 0.0
    return dx * k, dy * k


def rollout(policy, rng, noise=NOISE, record=None):
    """Run one episode. Returns (result, steps, worst distance from the centre line, final position)."""
    p = (START[0] + rng.uniform(-0.03, 0.03), START[1] + rng.uniform(-0.03, 0.03))
    worst = 0.0
    for t in range(MAX_STEPS):
        a = policy(p)
        if record is not None:
            record.append((t, p, a))
        p = (p[0] + a[0] + rng.gauss(0, noise), p[1] + a[1] + rng.gauss(0, noise))
        worst = max(worst, path_s(p)[1])
        if not in_corridor(p):
            return 'wall', t + 1, worst, p
        if math.hypot(p[0] - GOAL[0], p[1] - GOAL[1]) < 0.05:
            return 'success', t + 1, worst, p
    return 'timeout', MAX_STEPS, worst, p


def record_demos(n, rng, noise=0.0):
    """Expert demonstrations; by default executed without actuator noise (a careful operator)."""
    frames = []
    for ep in range(n):
        rows = []
        rollout(expert, rng, noise=noise, record=rows)
        frames += [(ep, t, p, a) for t, p, a in rows]
    return frames


def nn_policy(frames):
    """1-nearest-neighbour behaviour cloning: replay the action of the closest recorded observation."""
    obs = [(f[2], f[3]) for f in frames]

    def policy(p):
        best = min(obs, key=lambda o: (o[0][0] - p[0]) ** 2 + (o[0][1] - p[1]) ** 2)
        return best[1]
    return policy


def place(p):
    """Where along the corridor a wall was hit."""
    s, _ = path_s(p)
    return 'leg 1' if s < 0.85 else 'corner' if s < 1.15 else 'leg 2' if s < 1.9 else 'goal end'


def evaluate(policy, seed, n=100):
    rng = random.Random(seed)
    counts = {'success': 0, 'wall': 0, 'timeout': 0}
    walls = {'leg 1': 0, 'corner': 0, 'leg 2': 0, 'goal end': 0}
    worst = []
    for _ in range(n):
        result, _, w, p = rollout(policy, rng)
        counts[result] += 1
        worst.append(w)
        if result == 'wall':
            walls[place(p)] += 1
    worst.sort()
    return counts, worst[n // 2], walls


def report(label, frames, policy):
    c, med, walls = evaluate(policy, seed=2026)
    print(f'{label:<20} {len(frames):>5} frames   success {c["success"]:>3}/100   wall {c["wall"]:>3}   '
          f'timeout {c["timeout"]:>3}   median worst offset {med * 100:.1f} cm')
    if c['wall']:
        print(' ' * 21 + 'wall hits at: ' + ', '.join(f'{k} {v}' for k, v in walls.items()))


def main():
    rng = random.Random(6)
    demos = record_demos(80, rng)
    print('Recorded 80 expert demos (no actuator noise), first frames of episode 0:')
    print('episode_index frame_index  observation.state   action')
    for ep, t, p, a in demos[:3]:
        print(f'{ep:>13} {t:>11}  ({p[0]:+.3f}, {p[1]:+.3f})  ({a[0]:+.3f}, {a[1]:+.3f})')
    lengths = {}
    for ep, *_ in demos:
        lengths[ep] = lengths.get(ep, 0) + 1
    print(f'episode length: {min(lengths.values())} to {max(lengths.values())} frames')
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'w') as f:
            f.write('episode_index,frame_index,x,y,dx,dy\n')
            for ep, t, p, a in demos:
                if ep < 20:
                    f.write(f'{ep},{t},{p[0]:.4f},{p[1]:.4f},{a[0]:.4f},{a[1]:.4f}\n')
        print(f'wrote the first 20 episodes to {sys.argv[1]}')

    print('\nEvaluation: 100 rollouts each, actuator noise 1 cm per step, same seed for every policy')
    report('expert', [], expert)
    for n in (5, 20, 80):
        frames = [f for f in demos if f[0] < n]
        report(f'BC, {n} demos', frames, nn_policy(frames))
    noisy = record_demos(20, random.Random(8), noise=NOISE)      # the expert corrects its own noise
    report('BC, 20 noisy demos', noisy, nn_policy(noisy))

    print('\nDAgger: start from BC on 5 demos; each round runs the current policy 10 times with noise,')
    print('asks the expert what it would have done in every visited state, and adds those frames')
    frames = [f for f in demos if f[0] < 5]
    drng = random.Random(7)
    for k in range(1, 4):
        policy = nn_policy(frames)
        new = []
        for ep in range(10):
            rows = []
            rollout(policy, drng, record=rows)
            new += [(1000 * k + ep, t, p, expert(p)) for t, p, _ in rows]
        frames = frames + new
        report(f'DAgger round {k}', frames, nn_policy(frames))


if __name__ == '__main__':
    main()
