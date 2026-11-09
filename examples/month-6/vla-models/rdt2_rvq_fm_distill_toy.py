#!/usr/bin/env python3
"""rdt2_rvq_fm_distill_toy.py: RDT2-style recipe pieces on toy action chunks (stdlib).

Synthetic action chunks: 2 steps x (dx, dy) = 4 numbers, from four heading
modes with speed, heading and turn noise. Every arm in a part gets the SAME
train chunks, held-out chunks and noise draws (common random numbers per seed).

Part 1, tokenizer at an EQUAL 8-bit budget per chunk (Stage 1 needs tokens):
  bins_4x4       four tokens, 4 uniform bins per number over the train range
  single_vq_256  one token from a 256-entry codebook (k-means)
  rvq_2x16       two tokens, each stage a 16-entry codebook on the residual
  rvq_4x4        four tokens, each stage a 4-entry codebook on the residual
  -> held-out MSE, tokens per chunk, codebook entries, unused (dead) entries.

Part 2, continuous expert vs a one-step student under an online NFE budget:
  the "expert" velocity is the exact flow-matching field of a lightly smoothed
  copy of the train chunks (what a perfectly fitted expert converges to); no
  network is trained and no VLM features condition it.
  path A^tau = (1 - tau) * eps + tau * A, Euler steps from tau = 0 (noise)
  fm_1, fm_2, fm_5   Euler with 1, 2 or 5 function evaluations (NFE)
  distill_1_nn      a lookup student: returns the 5-step expert output F stored
                     for the nearest of DISTILL_PAIRS stored noise draws
  distill_1_avg3     the same pairs, averaging the 3 nearest stored outputs
                     (RDT2 instead trains G(eps) = eps + v'(eps), initialised
                     from the expert); both students cost 1 online NFE, but the
                     pairs cost offline expert calls
  -> precision (mean distance to the nearest held-out chunk), recall (mean
     distance from each held-out chunk to the nearest sample), off-manifold
     share, distinct outputs, online NFE and offline expert NFE.
Not RDT2, not Qwen2.5-VL, no GPU. Numbers depend on the lesson-chosen sizes.
usage: python3 rdt2_rvq_fm_distill_toy.py
"""
from __future__ import annotations

import math
import random
import statistics

SEEDS = (0, 1, 2, 3, 4)
N_TOK, N_TRAIN, N_TEST, N_GEN = 768, 256, 200, 200
LLOYD_ITERS = 8
SMOOTH = 0.05          # expert smoothing (std of the Gaussian around each train chunk)
DISTILL_PAIRS = 400
OFF_MANIFOLD = 0.25    # distance to the nearest held-out chunk that counts as off-manifold
TOKENIZERS = (("bins_4x4", [4, 4, 4, 4]), ("single_vq_256", [256]), ("rvq_2x16", [16, 16]), ("rvq_4x4", [4, 4, 4, 4]))
GENERATORS = ("fm_1", "fm_2", "fm_5", "distill_1_nn", "distill_1_avg3")


def sample_chunk(rng):
    mode = rng.randrange(4)
    head = mode * math.pi / 2 + rng.gauss(0.0, 0.12)
    speed = 1.0 + rng.gauss(0.0, 0.08)
    turn = rng.gauss(0.0, 0.3)
    v1 = (speed * math.cos(head), speed * math.sin(head))
    v2 = (speed * math.cos(head + turn), speed * math.sin(head + turn))
    return [v1[0], v1[1], v2[0], v2[1]]


def d2(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def nearest(c, pts):
    best, bi = float("inf"), 0
    for i, p in enumerate(pts):
        d = d2(c, p)
        if d < best:
            best, bi = d, i
    return bi, best


def kmeans(data, k, rng):
    cent = [list(p) for p in rng.sample(data, k)] if k <= len(data) else [list(p) for p in data]
    for _ in range(LLOYD_ITERS):
        sums = [[0.0] * 4 for _ in cent]
        cnt = [0] * len(cent)
        for p in data:
            i, _ = nearest(p, cent)
            cnt[i] += 1
            for j in range(4):
                sums[i][j] += p[j]
        for i in range(len(cent)):
            if cnt[i]:
                cent[i] = [s / cnt[i] for s in sums[i]]
    return cent


def train_rvq(data, stages, rng):
    books, resid = [], [list(p) for p in data]
    for k in stages:
        book = kmeans(resid, k, rng)
        books.append(book)
        resid = [[r[j] - book[nearest(r, book)[0]][j] for j in range(4)] for r in resid]
    return books


def encode_decode(x, books):
    rec, resid, codes = [0.0] * 4, list(x), []
    for book in books:
        i, _ = nearest(resid, book)
        codes.append(i)
        rec = [rec[j] + book[i][j] for j in range(4)]
        resid = [resid[j] - book[i][j] for j in range(4)]
    return rec, codes


def velocity(x, tau, train):
    """Exact FM field for a mixture of N(a_i, SMOOTH^2 I) under A^tau = (1-tau) eps + tau A."""
    var = (1.0 - tau) ** 2 + (tau * SMOOTH) ** 2
    logw = [-d2(x, [tau * v for v in a]) / (2.0 * var) for a in train]
    m = max(logw)
    w = [math.exp(l - m) for l in logw]
    z = sum(w)
    gain = tau * SMOOTH ** 2 / var
    ea = [0.0] * 4
    for wi, a in zip(w, train):
        for j in range(4):
            ea[j] += wi * (a[j] + gain * (x[j] - tau * a[j]))
    ea = [v / z for v in ea]
    return [(ea[j] - x[j]) / (1.0 - tau) for j in range(4)]


def euler(eps, steps, train):
    x, h = list(eps), 1.0 / steps
    for s in range(steps):
        v = velocity(x, s * h, train)
        x = [x[j] + h * v[j] for j in range(4)]
    return x


def knn_student(pairs, eps, k):
    """Average of the stored 5-step outputs for the k nearest stored noise draws."""
    near = sorted(pairs, key=lambda p: d2(p[0], eps))[:k]
    return [sum(p[1][j] for p in near) / k for j in range(4)]


def gen_metrics(samples, test):
    prec = [math.sqrt(nearest(s, test)[1]) for s in samples]
    rec = [math.sqrt(nearest(t, samples)[1]) for t in test]
    off = 100.0 * sum(p > OFF_MANIFOLD for p in prec) / len(prec)
    return statistics.mean(prec), statistics.mean(rec), off


def ms(xs, f="{:.3f}"):
    return (f + "±" + f).format(statistics.mean(xs), statistics.stdev(xs))


def main():
    tok = {n: {"mse": [], "dead": []} for n, _ in TOKENIZERS}
    gen = {n: {"prec": [], "rec": [], "off": [], "uniq": []} for n in GENERATORS}
    for seed in SEEDS:
        rd = random.Random(1000 + seed)
        tok_data = [sample_chunk(rd) for _ in range(N_TOK)]
        train = tok_data[:N_TRAIN]                   # the expert sees a subset of the same chunks
        test = [sample_chunk(rd) for _ in range(N_TEST)]
        for name, stages in TOKENIZERS:
            if name.startswith("bins"):
                lo = [min(p[j] for p in tok_data) for j in range(4)]
                hi = [max(p[j] for p in tok_data) for j in range(4)]
                codes = [[min(3, max(0, int((p[j] - lo[j]) / (hi[j] - lo[j]) * 4))) for j in range(4)] for p in tok_data]
                tok[name]["dead"].append(100.0 * sum(4 - len({c[j] for c in codes}) for j in range(4)) / 16)
                rec = lambda t: [lo[j] + (min(3, max(0, int((t[j] - lo[j]) / (hi[j] - lo[j]) * 4))) + 0.5) * (hi[j] - lo[j]) / 4 for j in range(4)]
                tok[name]["mse"].append(statistics.mean(d2(rec(t), t) / 4 for t in test))
                continue
            books = train_rvq(tok_data, stages, random.Random(2000 + seed))
            used = [set() for _ in books]
            for p in tok_data:
                for s, c in enumerate(encode_decode(p, books)[1]):
                    used[s].add(c)
            tok[name]["dead"].append(100.0 * sum(len(b) - len(u) for b, u in zip(books, used)) / sum(len(b) for b in books))
            tok[name]["mse"].append(statistics.mean(d2(encode_decode(t, books)[0], t) / 4 for t in test))
        rn = random.Random(3000 + seed)
        noise = [[rn.gauss(0.0, 1.0) for _ in range(4)] for _ in range(N_GEN)]
        rp = random.Random(4000 + seed)
        pair_eps = [[rp.gauss(0.0, 1.0) for _ in range(4)] for _ in range(DISTILL_PAIRS)]
        pairs = []
        for e in pair_eps:
            pairs.append((e, euler(e, 5, train)))
        for name in GENERATORS:
            if name.startswith("distill"):
                samples = [knn_student(pairs, e, 1 if name.endswith("nn") else 3) for e in noise]
            else:
                samples = [euler(e, int(name[3:]), train) for e in noise]
            p, r, o = gen_metrics(samples, test)
            gen[name]["prec"].append(p)
            gen[name]["rec"].append(r)
            gen[name]["off"].append(o)
            gen[name]["uniq"].append(100.0 * len({tuple(round(v, 9) for v in x) for x in samples}) / N_GEN)
    print("Synthetic RDT2-style toy: 4-number action chunks, four heading modes; not RDT2, no VLM, no GPU")
    print(f"seeds={len(SEEDS)} tokenizer_train={N_TOK} expert_train={N_TRAIN} test={N_TEST} generated={N_GEN} lloyd_iters={LLOYD_ITERS} distill_pairs={DISTILL_PAIRS} (mean±sd over seeds)")
    print("[part1 tokenizer, equal 8-bit budget per chunk]")
    print("arm tokens_per_chunk codebook_entries heldout_mse dead_entries_%")
    for name, stages in TOKENIZERS:
        print(f"{name} {len(stages)} {sum(stages)} {ms(tok[name]['mse'], '{:.4f}')} {ms(tok[name]['dead'], '{:.1f}')}")
    print("[part2 generator, shared noise draws; expert = exact FM field of smoothed train chunks]")
    print("arm online_nfe offline_expert_nfe precision recall off_manifold_% distinct_outputs_%")
    for name in GENERATORS:
        dist = name.startswith("distill")
        nfe = 1 if dist else int(name[3:])
        off_nfe = DISTILL_PAIRS * 5 if dist else 0
        g = gen[name]
        print(f"{name} {nfe} {off_nfe} {ms(g['prec'])} {ms(g['rec'])} {ms(g['off'], '{:.1f}')} {ms(g['uniq'], '{:.1f}')}")
    print("RDT2 recipe (per the paper): Stage 1 RVQ tokens + cross-entropy, Stage 2 frozen VLM + flow-matching expert, Stage 3 one-step distillation")
    print("No winner is declared; RDT2 task scores 以论文为准; 7B training / GPU / robots: 本页未运行")


if __name__ == "__main__":
    main()
