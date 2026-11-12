#!/usr/bin/env python3
"""VLA-Adapter Bridge Attention stand-in on a tiny backbone vs a larger plain head. Stdlib only.

Not 0.5B weights, not SmolVLA, not the weights-only budget table already on this page,
not OpenVLA-OFT. Paper (arXiv 2509.09372) 0.5B / 8-hour / LIBERO numbers are 以论文为准;
GPU / real 0.5B training / LIBERO: 本页未运行.

Model assumptions (also stated in the lesson prose):
  Each demo has a 2-D proprio state, a 2-D action, a vision vector that stores two object
  positions (plus filler in the precise regime), and a binary instruction. Conditions are a
  mid-layer-style raw latent C_R and a learned ActionQuery latent C_AQ (a 1-hidden-layer
  MLP on the same raw features, trained from scratch, not a pre-selected answer). There is
  no plant integration step (discrete SGD, L1 action regression, one-shot readout).

  After the first run, four changes were made and are not claimed to have been fixed
  before that run: (1) ActionQuery is a trained MLP rather than a frozen random mix;
  (2) the tiny readout concatenates the bridge output with the ActionQuery vector and
  proprio (a residual injection), and the bridge-output block of that readout starts at 0;
  (3) the large arm uses a two-layer 48-wide backbone stand-in so the tiny arm wins the
  size and FLOP proxy (the first run had a 24-wide single hidden layer whose parameter
  count was below the tiny policy); (4) STEPS and LR moved from 250 / 0.05 to 300 / 0.10.
  The first-run short_id table is still produced by
  `_vla_adapter_firstrun.py` on the same seeds and printed below.

Arms (Common random numbers: per (regime, seed) every demo, every test point, and C's
shuffle permutation are drawn once; batch i is the same set of demos for every arm;
B and C share the same initialization):
  A_large      a wider two-layer concat-MLP on a 48-wide backbone stand-in, no bridge
  B_bridge     tiny features + one-layer Bridge Attention (cross-attend action tokens to
               C_R and to C_AQ+proprio, self-attend on the action tokens, tanh(g) raw gate
               with g starting at 0, residual FFN, then a readout over [bridge, AQ, proprio])
  C_shuffle    same tiny + bridge architecture and the same init as B, but conditions are
               shuffled across the batch at train and test time

Equal step budget STEPS, batch BATCH, learning rate LR. Metrics: test success %
(|a_hat - a| <= TOL), mean L1, parameter count, and a latency / FLOP proxy (multiply-adds
in one forward). Size and FLOP do not depend on the seed.

Regimes, written before the first run (the architecture/hparams above were not):
  short_id   action = (p_0, -p_1) from proprio; instruction and objects are irrelevant
             A and B may near-tie on success; B consistent wins size and the FLOP proxy
  need_vl    action = the instructed object's position; VL conditions are required
             B consistent better success than C; shuffled C consistent lose
  precise    action is a thin linear mix of a longer raw vector (16-D)
             if the tiny+bridge arm loses success to the large head, that split is kept

Paper 8 h / 0.5B / SOTA claims stay 以论文为准 and are not printed as toy results.
"""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys
from pathlib import Path

SEEDS = (0, 1, 2, 3, 4)
# STEPS and LR were 250 and 0.05 on the first run; raised after that run (see docstring).
STEPS, BATCH, TEST = 300, 8, 200
LR = 0.10
TOL = 0.25
NUM_ZERO = 1e-9
D_RAW_SHORT = 6
D_RAW_PREC = 16
D_PROP = 2
D_ACT = 2
D_BB = 48
D_HID = 48
D_TINY = 6
HQ = 8          # ActionQuery hidden width
N_ACT = 2
N_RAW = 2
N_AQ = 2
INIT_SD = 0.08
ARMS = ("A_large", "B_bridge", "C_shuffle")
REGIMES = ("short_id", "need_vl", "precise")
STREAM = {"short_id": 0, "need_vl": 1, "precise": 2}


def zeros(r, c=None):
    if c is None:
        return [0.0] * r
    return [[0.0] * c for _ in range(r)]


def rand_mat(rng, r, c, sd=INIT_SD):
    return [[rng.gauss(0.0, sd) for _ in range(c)] for _ in range(r)]


def rand_vec(rng, n, sd=INIT_SD):
    return [rng.gauss(0.0, sd) for _ in range(n)]


def matvec(mat, v):
    return [sum(a * b for a, b in zip(row, v)) for row in mat]


def add_vec(a, b, s=1.0):
    return [x + s * y for x, y in zip(a, b)]


def axpy_mat(dst, src, s):
    for i, row in enumerate(src):
        for j, v in enumerate(row):
            dst[i][j] += s * v


def axpy_vec(dst, src, s):
    for i, v in enumerate(src):
        dst[i] += s * v


def clip_copy_mat(m):
    return [row[:] for row in m]


def relu(v):
    return [max(0.0, x) for x in v]


def softmax(logits):
    m = max(logits)
    ex = [math.exp(x - m) for x in logits]
    z = sum(ex)
    return [e / z for e in ex]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def outer(u, v):
    return [[ui * vj for vj in v] for ui in u]


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


def raw_dim(regime):
    return D_RAW_PREC if regime == "precise" else D_RAW_SHORT


def make_demo(regime, rng):
    d_raw = raw_dim(regime)
    k = 0 if rng.random() < 0.5 else 1
    o0 = [rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)]
    o1 = [rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)]
    prop = [rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)]
    inst = [1.0, 0.0] if k == 0 else [0.0, 1.0]
    if regime == "precise":
        raw = (o0 + o1 + inst + [rng.uniform(-1.0, 1.0) for _ in range(d_raw - 6)])[:d_raw]
        action = None
    else:
        raw = o0 + o1 + inst
        if regime == "short_id":
            action = [prop[0], -prop[1]]
        else:
            action = (o0 if k == 0 else o1)[:]
    return {"raw": raw, "prop": prop, "action": action, "k": k}


def fill_precise_actions(demos, mix):
    for d in demos:
        d["action"] = [dot(mix[0], d["raw"]), dot(mix[1], d["raw"])]


def init_large(rng, d_raw):
    return {
        "Wbb": rand_mat(rng, D_BB, d_raw),
        "bbb": rand_vec(rng, D_BB),
        "W1": rand_mat(rng, D_HID, D_BB + D_PROP),
        "b1": rand_vec(rng, D_HID),
        "W2": rand_mat(rng, D_ACT, D_HID),
        "b2": rand_vec(rng, D_ACT),
    }


def init_bridge(rng, d_raw):
    wo = rand_mat(rng, D_ACT, N_ACT * D_TINY + D_TINY + D_PROP)
    # bridge-output block of the readout starts at 0 (chosen after the first run)
    for i in range(D_ACT):
        for j in range(N_ACT * D_TINY):
            wo[i][j] = 0.0
    return {
        "Wr": rand_mat(rng, N_RAW * D_TINY, d_raw),
        "br": rand_vec(rng, N_RAW * D_TINY),
        "Wq1": rand_mat(rng, HQ, d_raw, sd=0.2),
        "bq1": zeros(HQ),
        "Wq2": rand_mat(rng, D_TINY, HQ, sd=0.2),
        "bq2": zeros(D_TINY),
        "Wp": rand_mat(rng, D_TINY, D_PROP),
        "bp": rand_vec(rng, D_TINY),
        "Wa": rand_mat(rng, N_ACT * D_TINY, D_ACT),
        "ba": rand_vec(rng, N_ACT * D_TINY),
        "g": 0.0,
        "Wmix": rand_mat(rng, D_TINY, 3 * D_TINY),
        "bmix": rand_vec(rng, D_TINY),
        "W1": rand_mat(rng, D_TINY, D_TINY),
        "b1": rand_vec(rng, D_TINY),
        "W2": rand_mat(rng, D_TINY, D_TINY),
        "b2": rand_vec(rng, D_TINY),
        "Wo": wo,
        "bo": rand_vec(rng, D_ACT),
    }


def count_params(p):
    n = 0
    for k, v in p.items():
        if k == "g" or isinstance(v, float):
            n += 1
        elif v and isinstance(v[0], list):
            n += sum(len(row) for row in v)
        else:
            n += len(v)
    return n


def flops_large(d_raw):
    return D_BB * d_raw + D_HID * (D_BB + D_PROP) + D_ACT * D_HID


def flops_bridge(d_raw):
    f = N_RAW * D_TINY * d_raw
    f += HQ * d_raw + D_TINY * HQ  # AQ MLP
    f += D_TINY * D_PROP + N_ACT * D_TINY * D_ACT

    def attn(nq, nk):
        return nq * nk * D_TINY + nq * nk * D_TINY

    f += attn(N_ACT, N_RAW) + attn(N_ACT, N_AQ) + attn(N_ACT, N_ACT)
    f += N_ACT * D_TINY * 3 * D_TINY
    f += 2 * N_ACT * D_TINY * D_TINY
    f += D_ACT * (N_ACT * D_TINY + D_TINY + D_PROP)
    return f


def shared_draws(regime, seed):
    rng = random.Random(3000 * STREAM[regime] + seed)
    d_raw = raw_dim(regime)
    prec_mix = None
    if regime == "precise":
        prec_mix = [[rng.gauss(0.0, 0.4) for _ in range(d_raw)] for _ in range(2)]
    demos = [make_demo(regime, rng) for _ in range(STEPS * BATCH)]
    test = [make_demo(regime, rng) for _ in range(TEST)]
    if prec_mix is not None:
        fill_precise_actions(demos, prec_mix)
        fill_precise_actions(test, prec_mix)
    shuffles = []
    for _ in range(STEPS):
        perm = list(range(BATCH))
        rng.shuffle(perm)
        if perm == list(range(BATCH)) and BATCH > 1:
            perm[0], perm[1] = perm[1], perm[0]
        shuffles.append(perm)
    test_perm = list(range(TEST))
    rng.shuffle(test_perm)
    return {
        "d_raw": d_raw,
        "demos": demos,
        "test": test,
        "shuffles": shuffles,
        "test_perm": test_perm,
        "inits": {"A": init_large(rng, d_raw), "B": init_bridge(rng, d_raw)},
    }


SCALE = 1.0 / math.sqrt(D_TINY)


def xattn_forward(Q, K, V):
    outs, caches = [], []
    for q in Q:
        scores = [dot(q, k) * SCALE for k in K]
        p = softmax(scores)
        o = [0.0] * len(V[0])
        for w, v in zip(p, V):
            axpy_vec(o, v, w)
        outs.append(o)
        caches.append((q, scores, p))
    return outs, caches


def xattn_backward(do_list, caches, Q, K, V):
    dQ = [zeros(len(Q[0])) for _ in Q]
    dK = [zeros(len(K[0])) for _ in K]
    dV = [zeros(len(V[0])) for _ in V]
    for i, (do, (q, scores, p)) in enumerate(zip(do_list, caches)):
        for j, pj in enumerate(p):
            axpy_vec(dV[j], do, pj)
        dp = [dot(do, V[j]) for j in range(len(V))]
        dotp = sum(pj * dpj for pj, dpj in zip(p, dp))
        ds = [pj * (dpj - dotp) for pj, dpj in zip(p, dp)]
        for j, dsj in enumerate(ds):
            axpy_vec(dQ[i], K[j], dsj * SCALE)
            axpy_vec(dK[j], q, dsj * SCALE)
    return dQ, dK, dV


def tokens_from(mat, bias, vec, n, d):
    flat = add_vec(matvec(mat, vec), bias)
    return [flat[i * d:(i + 1) * d] for i in range(n)], flat


def aq_forward(params, raw):
    z = add_vec(matvec(params["Wq1"], raw), params["bq1"])
    h = relu(z)
    aq = add_vec(matvec(params["Wq2"], h), params["bq2"])
    return aq, z, h


def linear_backward_matvec(W, x, dy):
    dW = outer(dy, x)
    db = dy[:]
    dx = [sum(W[k][j] * dy[k] for k in range(len(W))) for j in range(len(x))]
    return dW, db, dx


def zeros_like_params(p):
    z = {}
    for k, v in p.items():
        if k == "g" or isinstance(v, float):
            z[k] = 0.0
        elif v and isinstance(v[0], list):
            z[k] = zeros(len(v), len(v[0]))
        else:
            z[k] = zeros(len(v))
    return z


def copy_params(p):
    out = {}
    for k, v in p.items():
        if k == "g" or isinstance(v, float):
            out[k] = v
        elif v and isinstance(v[0], list):
            out[k] = clip_copy_mat(v)
        else:
            out[k] = v[:]
    return out


def add_params(dst, src, s):
    for k, v in src.items():
        if k == "g" or isinstance(v, float):
            dst[k] += s * v
        elif v and isinstance(v[0], list):
            axpy_mat(dst[k], v, s)
        else:
            axpy_vec(dst[k], v, s)


def bridge_forward(params, raw, prop):
    raw_toks, raw_flat = tokens_from(params["Wr"], params["br"], raw, N_RAW, D_TINY)
    aq, zq, hq = aq_forward(params, raw)
    pr_tok = add_vec(matvec(params["Wp"], prop), params["bp"])
    aq_toks = [aq, pr_tok]
    a0 = [0.0] * D_ACT
    act_toks, act_flat = tokens_from(params["Wa"], params["ba"], a0, N_ACT, D_TINY)
    ca1, c1 = xattn_forward(act_toks, raw_toks, raw_toks)
    ca2, c2 = xattn_forward(act_toks, aq_toks, aq_toks)
    sa, cs = xattn_forward(act_toks, act_toks, act_toks)
    gate = math.tanh(params["g"])
    mixed, mid = [], []
    for t in range(N_ACT):
        cat = [gate * x for x in ca1[t]] + ca2[t] + sa[t]
        h = add_vec(matvec(params["Wmix"], cat), params["bmix"])
        z = add_vec(matvec(params["W1"], h), params["b1"])
        r = relu(z)
        h2 = add_vec(h, add_vec(matvec(params["W2"], r), params["b2"]))
        mixed.append(h2)
        mid.append((cat, h, z, r))
    flat = []
    for tok in mixed:
        flat.extend(tok)
    feat = flat + aq + list(prop)
    y = add_vec(matvec(params["Wo"], feat), params["bo"])
    cache = {
        "raw": raw, "prop": prop, "a0": a0, "aq": aq, "zq": zq, "hq": hq,
        "raw_toks": raw_toks, "aq_toks": aq_toks, "act_toks": act_toks,
        "ca1": ca1, "c1": c1, "ca2": ca2, "c2": c2, "sa": sa, "cs": cs,
        "gate": gate, "mid": mid, "mixed": mixed, "feat": feat, "y": y,
    }
    return y, cache


def bridge_backward(params, cache, dy):
    g = zeros_like_params(params)
    dWo, dbo, dfeat = linear_backward_matvec(params["Wo"], cache["feat"], dy)
    axpy_mat(g["Wo"], dWo, 1.0)
    axpy_vec(g["bo"], dbo, 1.0)
    n_flat = N_ACT * D_TINY
    d_flat = dfeat[:n_flat]
    d_aq_res = dfeat[n_flat:n_flat + D_TINY]
    # d_prop_res = dfeat[n_flat + D_TINY:]  # no param solely from this skip besides Wo
    d_mixed = [d_flat[i * D_TINY:(i + 1) * D_TINY] for i in range(N_ACT)]
    d_cat = []
    for t in range(N_ACT):
        cat, h, z, r = cache["mid"][t]
        dh2 = d_mixed[t]
        dW2, db2, dr = linear_backward_matvec(params["W2"], r, dh2)
        axpy_mat(g["W2"], dW2, 1.0)
        axpy_vec(g["b2"], db2, 1.0)
        dz = [dr[i] if z[i] > 0.0 else 0.0 for i in range(D_TINY)]
        dW1, db1, dh_from_ff = linear_backward_matvec(params["W1"], h, dz)
        axpy_mat(g["W1"], dW1, 1.0)
        axpy_vec(g["b1"], db1, 1.0)
        dh = add_vec(dh2, dh_from_ff)
        dWm, dbm, dcat = linear_backward_matvec(params["Wmix"], cat, dh)
        axpy_mat(g["Wmix"], dWm, 1.0)
        axpy_vec(g["bmix"], dbm, 1.0)
        d_cat.append(dcat)
    gate = cache["gate"]
    dca1 = [d_cat[t][0:D_TINY] for t in range(N_ACT)]
    dca2 = [d_cat[t][D_TINY:2 * D_TINY] for t in range(N_ACT)]
    dsa = [d_cat[t][2 * D_TINY:3 * D_TINY] for t in range(N_ACT)]
    dg = 0.0
    dca1_pre = []
    for t in range(N_ACT):
        dca1_pre.append([gate * v for v in dca1[t]])
        dg += sum(dca1[t][i] * cache["ca1"][t][i] for i in range(D_TINY))
    g["g"] += dg * (1.0 - gate * gate)
    dQ1, dK1, dV1 = xattn_backward(dca1_pre, cache["c1"], cache["act_toks"], cache["raw_toks"], cache["raw_toks"])
    dQ2, dK2, dV2 = xattn_backward(dca2, cache["c2"], cache["act_toks"], cache["aq_toks"], cache["aq_toks"])
    dQs, dKs, dVs = xattn_backward(dsa, cache["cs"], cache["act_toks"], cache["act_toks"], cache["act_toks"])
    d_act = [add_vec(add_vec(dQ1[t], dQ2[t]), add_vec(dQs[t], add_vec(dKs[t], dVs[t]))) for t in range(N_ACT)]
    d_raw_toks = [add_vec(dK1[j], dV1[j]) for j in range(N_RAW)]
    d_aq_toks = [add_vec(dK2[j], dV2[j]) for j in range(N_AQ)]
    # AQ token is both aq_toks[0] and the residual branch
    d_aq = add_vec(d_aq_toks[0], d_aq_res)
    d_raw_flat = []
    for tok in d_raw_toks:
        d_raw_flat.extend(tok)
    dWr, dbr, _ = linear_backward_matvec(params["Wr"], cache["raw"], d_raw_flat)
    axpy_mat(g["Wr"], dWr, 1.0)
    axpy_vec(g["br"], dbr, 1.0)
    # AQ MLP
    dWq2, dbq2, dhq = linear_backward_matvec(params["Wq2"], cache["hq"], d_aq)
    axpy_mat(g["Wq2"], dWq2, 1.0)
    axpy_vec(g["bq2"], dbq2, 1.0)
    dzq = [dhq[i] if cache["zq"][i] > 0.0 else 0.0 for i in range(HQ)]
    dWq1, dbq1, _ = linear_backward_matvec(params["Wq1"], cache["raw"], dzq)
    axpy_mat(g["Wq1"], dWq1, 1.0)
    axpy_vec(g["bq1"], dbq1, 1.0)
    dWp, dbp, _ = linear_backward_matvec(params["Wp"], cache["prop"], d_aq_toks[1])
    axpy_mat(g["Wp"], dWp, 1.0)
    axpy_vec(g["bp"], dbp, 1.0)
    d_act_flat = []
    for tok in d_act:
        d_act_flat.extend(tok)
    dWa, dba, _ = linear_backward_matvec(params["Wa"], cache["a0"], d_act_flat)
    axpy_mat(g["Wa"], dWa, 1.0)
    axpy_vec(g["ba"], dba, 1.0)
    return g


def large_forward(params, raw, prop):
    zbb = add_vec(matvec(params["Wbb"], raw), params["bbb"])
    bb = relu(zbb)
    x = bb + list(prop)
    z = add_vec(matvec(params["W1"], x), params["b1"])
    h = relu(z)
    y = add_vec(matvec(params["W2"], h), params["b2"])
    return y, (zbb, bb, x, z, h)


def large_backward(params, raw, cache, dy):
    zbb, bb, x, z, h = cache
    dW2, db2, dh = linear_backward_matvec(params["W2"], h, dy)
    dz = [dh[i] if z[i] > 0.0 else 0.0 for i in range(len(z))]
    dW1, db1, dx = linear_backward_matvec(params["W1"], x, dz)
    dbb = dx[:D_BB]
    dzbb = [dbb[i] if zbb[i] > 0.0 else 0.0 for i in range(D_BB)]
    dWbb, dbbb, _ = linear_backward_matvec(params["Wbb"], raw, dzbb)
    return {"Wbb": dWbb, "bbb": dbbb, "W1": dW1, "b1": db1, "W2": dW2, "b2": db2}


def l1_grad(y, target):
    dy, loss = [], 0.0
    for yi, ti in zip(y, target):
        d = yi - ti
        loss += abs(d)
        dy.append(1.0 if d > 0 else (-1.0 if d < 0 else 0.0))
    return loss, dy


def apply_shuffle(batch, perm):
    raws = [batch[i]["raw"] for i in perm]
    out = []
    for i, demo in enumerate(batch):
        d = dict(demo)
        d["raw"] = raws[i]
        out.append(d)
    return out


def train_large(draws):
    p = copy_params(draws["inits"]["A"])
    for s in range(STEPS):
        batch = draws["demos"][s * BATCH:(s + 1) * BATCH]
        acc = zeros_like_params(p)
        for d in batch:
            y, cache = large_forward(p, d["raw"], d["prop"])
            _loss, dy = l1_grad(y, d["action"])
            dy = [v / BATCH for v in dy]
            g = large_backward(p, d["raw"], cache, dy)
            add_params(acc, g, 1.0)
        add_params(p, acc, -LR)
    return p


def train_bridge(draws, shuffle=False):
    p = copy_params(draws["inits"]["B"])
    for s in range(STEPS):
        batch = draws["demos"][s * BATCH:(s + 1) * BATCH]
        if shuffle:
            batch = apply_shuffle(batch, draws["shuffles"][s])
        acc = zeros_like_params(p)
        for d in batch:
            y, cache = bridge_forward(p, d["raw"], d["prop"])
            _loss, dy = l1_grad(y, d["action"])
            dy = [v / BATCH for v in dy]
            g = bridge_backward(p, cache, dy)
            add_params(acc, g, 1.0)
        add_params(p, acc, -LR)
    return p


def eval_large(p, draws):
    ok, l1 = 0, 0.0
    for d in draws["test"]:
        y, _ = large_forward(p, d["raw"], d["prop"])
        err = [a - b for a, b in zip(y, d["action"])]
        l1 += sum(abs(e) for e in err)
        if math.sqrt(sum(e * e for e in err)) <= TOL:
            ok += 1
    n = len(draws["test"])
    return {"success_%": 100.0 * ok / n, "l1": l1 / n}


def eval_bridge(p, draws, shuffle=False):
    tes = draws["test"]
    if shuffle:
        tes = apply_shuffle(tes, draws["test_perm"])
    ok, l1 = 0, 0.0
    for d in tes:
        y, _ = bridge_forward(p, d["raw"], d["prop"])
        err = [a - b for a, b in zip(y, d["action"])]
        l1 += sum(abs(e) for e in err)
        if math.sqrt(sum(e * e for e in err)) <= TOL:
            ok += 1
    n = len(tes)
    return {"success_%": 100.0 * ok / n, "l1": l1 / n}


def fmt_arm(name, rows, keys):
    parts = []
    for k in keys:
        xs = [r[k] for r in rows]
        m, s = mean_sd(xs)
        parts.append(f"{k}={num(m)}+-{num(s)}")
    return f"  {name} " + " ".join(parts)


def main():
    print(
        "Synthetic VLA-Adapter probe: large plain head vs tiny + Bridge Attention vs "
        "tiny + shuffled conditions; stdlib stand-in, not a 0.5B backbone"
    )
    print(
        f"STEPS={STEPS} BATCH={BATCH} LR={LR} TOL={TOL} TEST={TEST} "
        f"D_TINY={D_TINY} D_BB={D_BB} D_HID={D_HID} HQ={HQ} seeds={len(SEEDS)}"
    )
    print("no plant integration step (discrete SGD, L1, one-shot readout)")
    print("regime arm success_% l1 params flops  (mean+-sd over seeds; params/flops are deterministic)")
    keys = ("success_%", "l1", "params", "flops")
    # param/flop counts depend only on d_raw
    dummy6, dummy16 = init_bridge(random.Random(0), 6), init_bridge(random.Random(0), 16)
    pa6, pb6 = count_params(init_large(random.Random(0), 6)), count_params(dummy6)
    pa16, pb16 = count_params(init_large(random.Random(0), 16)), count_params(dummy16)
    print(f"param counts A/B: d_raw=6 {pa6}/{pb6}; d_raw=16 {pa16}/{pb16}")
    print(f"flop proxy A/B: d_raw=6 {flops_large(6)}/{flops_bridge(6)}; d_raw=16 {flops_large(16)}/{flops_bridge(16)}")
    for regime in REGIMES:
        d_raw = raw_dim(regime)
        pa, fa = (pa6, flops_large(6)) if d_raw == 6 else (pa16, flops_large(16))
        pb, fb = (pb6, flops_bridge(6)) if d_raw == 6 else (pb16, flops_bridge(16))
        draws_all = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [] for arm in ARMS}
        for d in draws_all:
            pA = train_large(d)
            pB = train_bridge(d, shuffle=False)
            pC = train_bridge(d, shuffle=True)
            eA, eB, eC = eval_large(pA, d), eval_bridge(pB, d, False), eval_bridge(pC, d, True)
            eA["params"], eA["flops"] = float(pa), float(fa)
            eB["params"], eB["flops"] = float(pb), float(fb)
            eC["params"], eC["flops"] = float(pb), float(fb)
            res["A_large"].append(eA)
            res["B_bridge"].append(eB)
            res["C_shuffle"].append(eC)
        print(f"{regime} (d_raw={d_raw}; A params {pa} flops {fa}; B/C params {pb} flops {fb})")
        for arm in ARMS:
            print(fmt_arm(arm, res[arm], keys))
        pairs = (("B_bridge", "A_large"), ("C_shuffle", "B_bridge"), ("C_shuffle", "A_large"))
        for met in keys:
            for x, y in pairs:
                print(
                    f"  paired {x}-{y} {met}: "
                    + verdict([r[met] for r in res[x]], [r[met] for r in res[y]])
                )
    print(
        "No winner declared on success: the tiny + bridge arm is built to win the size and "
        "FLOP proxy; shuffled conditions test whether the VL condition is actually used"
    )
    print("VLA-Adapter paper numbers (0.5B, 8 hours, LIBERO) 以论文为准; GPU / 0.5B train: 本页未运行")
    print("not SmolVLA; not the weights-only budget table; not OpenVLA-OFT")
    print(
        "alternative first-run architecture on short_id (frozen random AQ, no proprio/AQ "
        "residual, A was a 24-wide single hidden layer, STEPS=250 LR=0.05; same seeds). "
        "Not fixed before the first run:"
    )
    env = os.environ.copy()
    env["B18P3_ONLY"] = "short_id"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    alt = subprocess.check_output(
        [sys.executable, str(Path(__file__).with_name("_vla_adapter_firstrun.py"))],
        env=env,
        text=True,
    )
    for line in alt.rstrip().splitlines():
        print("  " + line)


if __name__ == "__main__":
    main()
