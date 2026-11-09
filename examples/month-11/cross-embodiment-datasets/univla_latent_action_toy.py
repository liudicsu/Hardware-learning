#!/usr/bin/env python3
"""univla_latent_action_toy.py: task-centric latent actions vs raw motor BC (stdlib).

Synthetic 2-D world in [0, 1]^2: an end-effector (EE) must reach the goal named
by the instruction ("left" or "right") and go around a round obstacle in the
middle; touching it ends the episode as a failure. A second blob (another agent,
the task-irrelevant dynamics) wanders on its own. Frames show both blobs.

Two embodiments see the SAME scenes but map a motor command m to an EE step
differently: A: step = m; B: step = (-0.6 * m_y, 1.4 * m_x) (axes swapped, one
flipped, different gains). Shared per seed: video episodes, starts, wanderer
paths and evaluation starts (common random numbers). Arms:
  A_raw_bc_A         tabular BC from EE cell + instruction to motor, trained on
                     A's labelled episodes only
  B_latent_lang      latent action = codebook index of the EE's frame-to-frame
                     change (the instruction marks which blob is the actor; real
                     UniVLA learns this split from DINOv2 features in two stages,
                     not modelled); policy on unlabelled video of A AND B; a
                     per-embodiment linear decoder from the code's centroid
  C_latent_no_lang   the same, but the code covers the whole frame change (EE and
                     wanderer), as in latent models without language conditioning
  D_raw_bc_small     tabular BC trained only on the decoder's labelled steps
Equal budgets: the same codebook size, Lloyd iterations, video, grid and decoder
labels (DEC_LABELS labelled steps per embodiment) for B, C and D; decoder input
is 2 numbers for B and 4 for C (labelled). Not UniVLA, no VLM, no GPU.
usage: python3 univla_latent_action_toy.py
"""
from __future__ import annotations

import math
import random
import statistics

SEEDS = (0, 1, 2, 3, 4)
STEP = 0.05
OBST, OBST_R = (0.5, 0.5), 0.17
GOALS = {"left": (0.12, 0.88), "right": (0.88, 0.88)}
GRID = 10
VIDEO_EPISODES = 80        # per embodiment
DEC_LABELS = 20            # labelled steps per embodiment for decoders (and D)
CODES = 12
LLOYD_ITERS = 10
T_MAX = 40
N_EVAL = 40
SCENARIOS = (("wanderer", 0.06), ("still_scene", 0.0))
ARMS = ("A_raw_bc_A", "B_latent_lang", "C_latent_no_lang", "D_raw_bc_small")


def to_step(emb, m):
    return (m[0], m[1]) if emb == "A" else (-0.6 * m[1], 1.4 * m[0])


def to_motor(emb, d):
    return (d[0], d[1]) if emb == "A" else (d[1] / 1.4, -d[0] / 0.6)


def blocked(a, b):
    """Does the segment a->b pass within OBST_R + 0.04 of the obstacle centre?"""
    vx, vy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((OBST[0] - a[0]) * vx + (OBST[1] - a[1]) * vy) / (vx * vx + vy * vy + 1e-12)))
    return math.hypot(a[0] + t * vx - OBST[0], a[1] + t * vy - OBST[1]) < OBST_R + 0.04


def expert_step(ee, goal):
    """Straight to the goal, or first to a waypoint below and beside the obstacle."""
    tgt = goal
    if blocked(ee, goal):
        side = 1.0 if goal[0] > OBST[0] else -1.0
        tgt = (OBST[0] + side * 0.3, min(ee[1], 0.26))
        if math.hypot(tgt[0] - ee[0], tgt[1] - ee[1]) < 1e-9:
            tgt = goal
    dx, dy = tgt[0] - ee[0], tgt[1] - ee[1]
    dist = math.hypot(dx, dy)
    s = min(STEP, dist)
    return (s * dx / dist, s * dy / dist)


def clip(p):
    return (min(max(p[0], 0.0), 1.0), min(max(p[1], 0.0), 1.0))


def hit(p):
    return math.hypot(p[0] - OBST[0], p[1] - OBST[1]) < OBST_R


def start(rng):
    while True:
        p = (rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.4))
        if not hit(p):
            return p


def cell(ee, task):
    return (min(GRID - 1, int(ee[0] * GRID)), min(GRID - 1, int(ee[1] * GRID)), task)


def wander(w, rng, sigma):
    return clip((w[0] + rng.gauss(0.0, sigma), w[1] + rng.gauss(0.0, sigma)))


def video(emb, rng, sigma):
    """Expert episodes: (cell, motor, ee_change, wanderer_change) per step."""
    rows = []
    for _ in range(VIDEO_EPISODES):
        task = rng.choice(("left", "right"))
        ee, w = start(rng), (rng.random(), rng.random())
        for _ in range(T_MAX):
            d = expert_step(ee, GOALS[task])
            m = to_motor(emb, d)
            m = (m[0] + rng.gauss(0.0, 0.002), m[1] + rng.gauss(0.0, 0.002))
            st = to_step(emb, m)
            nee = clip((ee[0] + st[0], ee[1] + st[1]))
            nw = wander(w, rng, sigma)
            rows.append((cell(ee, task), m, (nee[0] - ee[0], nee[1] - ee[1]), (nw[0] - w[0], nw[1] - w[1])))
            ee, w = nee, nw
            if math.hypot(ee[0] - GOALS[task][0], ee[1] - GOALS[task][1]) < 0.06:
                break
    return rows


def d2(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def kmeans(data, k, rng):
    cent = [list(p) for p in rng.sample(data, k)]
    for _ in range(LLOYD_ITERS):
        sums, cnt = [[0.0] * len(data[0]) for _ in cent], [0] * k
        for p in data:
            i = min(range(k), key=lambda c: d2(p, cent[c]))
            cnt[i] += 1
            sums[i] = [s + v for s, v in zip(sums[i], p)]
        cent = [[s / cnt[i] for s in sums[i]] if cnt[i] else cent[i] for i in range(k)]
    return cent


def lstsq(xs, ys):
    """Least squares y = W x (no bias), solved with normal equations + tiny ridge."""
    n = len(xs[0])
    a = [[sum(x[i] * x[j] for x in xs) + (1e-6 if i == j else 0.0) for j in range(n)] for i in range(n)]
    W = []
    for k in range(len(ys[0])):
        b = [sum(x[i] * y[k] for x, y in zip(xs, ys)) for i in range(n)]
        m = [row[:] + [bb] for row, bb in zip(a, b)]
        for c in range(n):
            piv = max(range(c, n), key=lambda r: abs(m[r][c]))
            m[c], m[piv] = m[piv], m[c]
            for r in range(n):
                if r != c:
                    f = m[r][c] / m[c][c]
                    m[r] = [u - f * v for u, v in zip(m[r], m[c])]
        W.append([m[i][n] / m[i][i] for i in range(n)])
    return W


def table(pairs):
    """cell -> mean value (motor) or majority value (code)."""
    acc = {}
    for c, v in pairs:
        acc.setdefault(c, []).append(v)
    return acc


def lookup(tab, key, reduce):
    if key in tab:
        return reduce(tab[key])
    near = min((k for k in tab if k[2] == key[2]), key=lambda k: (k[0] - key[0]) ** 2 + (k[1] - key[1]) ** 2)
    return reduce(tab[near])


def mean_vec(vs):
    return tuple(sum(v[i] for v in vs) / len(vs) for i in range(len(vs[0])))


def majority(vs):
    return max(sorted(set(vs)), key=vs.count)


def rollout(emb, act, rng, sigma):
    task = rng.choice(("left", "right"))
    ee, w = start(rng), (rng.random(), rng.random())
    for t in range(T_MAX):
        m = act(cell(ee, task))
        s = to_step(emb, m)
        n = math.hypot(s[0], s[1])
        if n > 2 * STEP:                       # actuator saturation, same for every arm
            s = (s[0] * 2 * STEP / n, s[1] * 2 * STEP / n)
        ee = clip((ee[0] + s[0], ee[1] + s[1]))
        w = wander(w, rng, sigma)
        if hit(ee):
            return 0, 1
        if math.hypot(ee[0] - GOALS[task][0], ee[1] - GOALS[task][1]) < 0.06:
            return 1, 0
    return 0, 0


def run_seed(seed, sigma):
    vids = {e: video(e, random.Random(100 * seed + (1 if e == "A" else 2)), sigma) for e in ("A", "B")}
    feats = {"B_latent_lang": lambda r: list(r[2]), "C_latent_no_lang": lambda r: list(r[2]) + list(r[3])}
    pol, books = {}, {}
    for arm, f in feats.items():
        allrows = vids["A"] + vids["B"]
        book = kmeans([f(r) for r in allrows], CODES, random.Random(500 + seed))
        books[arm] = book
        code = lambda r, f=f, book=book: min(range(CODES), key=lambda c: d2(f(r), book[c]))
        pol[arm] = table([(r[0], code(r)) for r in allrows])
    raw_A = table([(r[0], r[1]) for r in vids["A"]])
    out = {}
    for emb in ("A", "B"):
        lab = random.Random(700 + seed).sample(vids[emb], DEC_LABELS)
        dec = {}
        for arm, f in feats.items():
            book = books[arm]
            xs = [book[min(range(CODES), key=lambda c: d2(f(r), book[c]))] for r in lab]
            dec[arm] = lstsq(xs, [r[1] for r in lab])
        small = table([(r[0], r[1]) for r in lab])
        acts = {
            "A_raw_bc_A": lambda c: lookup(raw_A, c, mean_vec),
            "B_latent_lang": lambda c: tuple(sum(w * x for w, x in zip(row, books["B_latent_lang"][lookup(pol["B_latent_lang"], c, majority)])) for row in dec["B_latent_lang"]),
            "C_latent_no_lang": lambda c: tuple(sum(w * x for w, x in zip(row, books["C_latent_no_lang"][lookup(pol["C_latent_no_lang"], c, majority)])) for row in dec["C_latent_no_lang"]),
            "D_raw_bc_small": lambda c: lookup(small, c, mean_vec),
        }
        for arm in ARMS:
            re = random.Random(900 + seed)
            res = [rollout(emb, acts[arm], re, sigma) for _ in range(N_EVAL)]
            out[(arm, emb)] = (sum(r[0] for r in res) / N_EVAL, sum(r[1] for r in res) / N_EVAL)
    return out


def ms(xs):
    return f"{statistics.mean(xs):.3f}±{statistics.stdev(xs):.3f}"


def main():
    print("Synthetic UniVLA-style latent-action toy: 2-D reach around an obstacle, two embodiments; not UniVLA, no VLM, no GPU")
    print(f"seeds={len(SEEDS)} video_episodes_per_embodiment={VIDEO_EPISODES} codes={CODES} lloyd_iters={LLOYD_ITERS} "
          f"decoder_labels={DEC_LABELS} grid={GRID}x{GRID}x2 eval_episodes={N_EVAL} (mean±sd over seeds)")
    print("B motor map: step = (-0.6*m_y, 1.4*m_x); labels from B exist only for the decoder budget")
    print("scenario arm success_on_A success_on_B collision_on_B")
    for name, sigma in SCENARIOS:
        res = [run_seed(seed, sigma) for seed in SEEDS]
        for arm in ARMS:
            sa = [r[(arm, "A")][0] for r in res]
            sb = [r[(arm, "B")][0] for r in res]
            cb = [r[(arm, "B")][1] for r in res]
            print(f"{name} {arm} {ms(sa)} {ms(sb)} {ms(cb)}")
    print("No winner is declared; UniVLA LIBERO / R2R / real-robot gains 以论文为准; VLM pretraining / GPU / robots: 本页未运行")


if __name__ == "__main__":
    main()
