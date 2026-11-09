#!/usr/bin/env python3
"""vqbet_residual_vq_toy.py: MSE BC vs k-means bins vs residual VQ + offset (stdlib).

Synthetic two-mode demonstrations: a point moves +x through a corridor and must
pass an obstacle box (0.40 <= x <= 0.60, |y| < 0.12) either LEFT or RIGHT; each
demo picks a side with probability 0.5. Action a = (dx, dy) per step.
Observation = (x bin of 10, side bin of 3: y<-0.02 / |y|<=0.02 / y>0.02).
Every arm gets the SAME demos, the SAME observation bins and the SAME
count-based heads; only the action representation differs:
  MSE    : per-observation mean action (least squares with one-hot features)
  kmeans : one codebook of K=8 vectors (Lloyd, 12 iterations), categorical
           over codes per observation + per-(obs, code) mean offset (BeT-style)
  rvq    : residual VQ, 2 stages x 4 vectors (6 + 6 Lloyd iterations; stage 2
           quantizes stage-1 residuals), categorical over the 16 (primary,
           secondary) pairs per observation + per-(obs, pair) mean offset
Both quantizers store 8 codebook vectors and get 12 Lloyd iterations; rvq has
16 code combinations against 8, so its head and offset tables are 2x larger
(printed). Not a transformer, not a trained network, no GPU.
usage: python3 vqbet_residual_vq_toy.py
"""
from __future__ import annotations

import math
import random
import statistics

SEEDS = (0, 1, 2, 3, 4)
N_DEMOS = 60
N_ROLLOUTS = 100
STEPS = 20
DX = 0.05
OBST = (0.40, 0.60, 0.12)
NOISE = 0.004          # per-step actuator noise (demos and rollouts)
K = 8                  # k-means codebook vectors
K1, K2 = 4, 4          # residual VQ: primary and secondary codebook sizes
ITERS = 12             # Lloyd iterations per quantizer (rvq: split 6 + 6)


def obs_of(x, y):
    xb = min(9, max(0, int(x * 10)))
    sb = 0 if y < -0.02 else (2 if y > 0.02 else 1)
    return xb * 3 + sb


def demo(rng):
    side = rng.choice((-1, 1))
    x, y, rows = 0.0, rng.gauss(0, 0.005), []
    gain = 1 + 0.2 * rng.gauss(0, 1)
    for _ in range(STEPS):
        if x < 0.35:
            dy = side * 0.045 * gain
        elif x < 0.65:
            dy = 0.0
        else:
            dy = -side * 0.045 * gain
        a = (DX, dy)
        rows.append((obs_of(x, y), a))
        x += a[0] + rng.gauss(0, NOISE)
        y += a[1] + rng.gauss(0, NOISE)
    return rows


def d2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def lloyd(points, k, iters, rng):
    cents = [points[i] for i in rng.sample(range(len(points)), k)]
    for _ in range(iters):
        groups = [[] for _ in range(k)]
        for p in points:
            groups[min(range(k), key=lambda j: d2(p, cents[j]))].append(p)
        cents = [(sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g)) if g else cents[j]
                 for j, g in enumerate(groups)]
    return cents


def nearest(p, cents):
    return min(range(len(cents)), key=lambda j: d2(p, cents[j]))


class Quantizer:
    def __init__(self, kind, actions, rng):
        self.kind = kind
        if kind == "kmeans":
            self.books = [lloyd(actions, K, ITERS, rng)]
        else:
            b1 = lloyd(actions, K1, ITERS // 2, rng)
            res = [(a[0] - b1[nearest(a, b1)][0], a[1] - b1[nearest(a, b1)][1]) for a in actions]
            self.books = [b1, lloyd(res, K2, ITERS // 2, rng)]

    def encode(self, a):
        codes, r = [], a
        for b in self.books:
            j = nearest(r, b)
            codes.append(j)
            r = (r[0] - b[j][0], r[1] - b[j][1])
        return tuple(codes)

    def decode(self, codes):
        return (sum(b[j][0] for b, j in zip(self.books, codes)), sum(b[j][1] for b, j in zip(self.books, codes)))

    def combos(self):
        return K if self.kind == "kmeans" else K1 * K2


def fit(kind, rows, rng):
    if kind == "MSE":
        acc = {}
        for o, a in rows:
            s = acc.setdefault(o, [0.0, 0.0, 0])
            s[0] += a[0]; s[1] += a[1]; s[2] += 1
        return {"kind": kind, "mean": {o: (s[0] / s[2], s[1] / s[2]) for o, s in acc.items()}}
    q = Quantizer(kind, [a for _, a in rows], rng)
    counts, off = {}, {}
    for o, a in rows:
        c = q.encode(a)
        counts.setdefault(o, {}).setdefault(c, 0)
        counts[o][c] += 1
        dec = q.decode(c)
        s = off.setdefault((o, c), [0.0, 0.0, 0])
        s[0] += a[0] - dec[0]; s[1] += a[1] - dec[1]; s[2] += 1
    return {"kind": kind, "q": q, "counts": counts,
            "off": {k: (s[0] / s[2], s[1] / s[2]) for k, s in off.items()}}


def act(model, o, rng):
    if model["kind"] == "MSE":
        return model["mean"].get(o, (DX, 0.0))
    cs = model["counts"].get(o)
    if not cs:
        return (DX, 0.0)
    r, acc = rng.random() * sum(cs.values()), 0.0
    for c, n in sorted(cs.items()):
        acc += n
        if r < acc:
            break
    dec, of = model["q"].decode(c), model["off"][(o, c)]
    return (dec[0] + of[0], dec[1] + of[1])


def recon(model, rows):
    """Held-out demo actions: decode-only and decode+offset squared error."""
    if model["kind"] == "MSE":
        e = [d2(a, model["mean"].get(o, (DX, 0.0))) for o, a in rows]
        return statistics.mean(e), statistics.mean(e)
    q, e0, e1 = model["q"], [], []
    for o, a in rows:
        c = q.encode(a)
        dec = q.decode(c)
        of = model["off"].get((o, c), (0.0, 0.0))
        e0.append(d2(a, dec))
        e1.append(d2(a, (dec[0] + of[0], dec[1] + of[1])))
    return statistics.mean(e0), statistics.mean(e1)


def rollout(model, rng):
    x, y, hit, ymin, ymax = 0.0, rng.gauss(0, 0.005), False, 0.0, 0.0
    for _ in range(STEPS):
        a = act(model, obs_of(x, y), rng)
        x += a[0] + rng.gauss(0, NOISE)
        y += a[1] + rng.gauss(0, NOISE)
        if OBST[0] <= x <= OBST[1]:
            hit = hit or abs(y) < OBST[2]
            ymin, ymax = min(ymin, y), max(ymax, y)
    side = "L" if ymin < -OBST[2] else ("R" if ymax > OBST[2] else "-")
    return hit, side, abs(y)


def params(model):
    if model["kind"] == "MSE":
        return f"{2 * len(model['mean'])} (means)"
    q = model["q"]
    book = 2 * sum(len(b) for b in q.books)
    return f"{book} codebook + {q.combos()}x30 head + {2 * q.combos()}x30 offset"


def ms(v, f):
    return f"{statistics.mean(v):{f}}±{statistics.pstdev(v):{f}}"


def main():
    print(f"Synthetic 2-mode demos: {N_DEMOS} train + {N_DEMOS} held-out per seed, {len(SEEDS)} seeds, "
          f"{N_ROLLOUTS} rollouts/seed, obstacle x∈[{OBST[0]},{OBST[1]}] |y|<{OBST[2]}, noise {NOISE}")
    print(f"kmeans K={K}; rvq {K1}x{K2}; {ITERS} Lloyd iterations each; same heads/offset rule")
    rows_out = {}
    for kind in ("MSE", "kmeans", "rvq"):
        res = {"col": [], "left": [], "both": [], "end": [], "q": [], "qo": []}
        for seed in SEEDS:
            drng = random.Random(seed)
            train = [r for _ in range(N_DEMOS) for r in demo(drng)]
            held = [r for _ in range(N_DEMOS) for r in demo(drng)]
            model = fit(kind, train, random.Random(100 + seed))
            q0, q1 = recon(model, held)
            rrng = random.Random(200 + seed)  # same rollout stream for every arm
            outs = [rollout(model, rrng) for _ in range(N_ROLLOUTS)]
            left = sum(s == "L" for _, s, _ in outs)
            right = sum(s == "R" for _, s, _ in outs)
            res["col"].append(sum(h for h, _, _ in outs) / N_ROLLOUTS)
            res["left"].append(left / max(1, left + right))
            res["both"].append(1.0 if left and right else 0.0)
            res["end"].append(statistics.mean(e for _, _, e in outs))
            res["q"].append(q0)
            res["qo"].append(q1)
        rows_out[kind] = (res, params(model))
    print("arm collision left_share both_modes_seen quant_MSE quant+offset_MSE end_|y| params")
    for kind, (r, p) in rows_out.items():
        print(f"{kind} {ms(r['col'], '.2f')} {ms(r['left'], '.2f')} {ms(r['both'], '.1f')} "
              f"{ms(r['q'], '.2e')} {ms(r['qo'], '.2e')} {ms(r['end'], '.3f')} {p}")
    print("MSE regression has no codes: its quant columns are the regression error.")
    print("Paper speed-ups (e.g. 5x vs diffusion) are not measured here: 以论文为准. GPU training: 本页未运行.")


if __name__ == "__main__":
    main()
