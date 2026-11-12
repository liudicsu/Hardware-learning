#!/usr/bin/env python3
"""VLA-Adapter Bridge Attention stand-in on a tiny backbone vs a larger plain head. Stdlib only.

Not 0.5B weights, not SmolVLA, not the weights-only budget table already on this page,
not OpenVLA-OFT. Paper (arXiv 2509.09372) 0.5B / 8-hour / LIBERO numbers are 以论文为准;
GPU / real 0.5B training / LIBERO: 本页未运行.

Model assumptions (also stated in the lesson prose):
  Each demo has a 2-D proprio state, a 2-D action, a vision vector that stores two object
  positions, and a binary instruction. Conditions are a mid-layer-style raw latent C_R
  (both objects + the instruction) and an ActionQuery-style latent C_AQ (a linear mix of
  the same raw features, not a pre-selected answer). There is no plant integration step
  (discrete SGD, L1 action regression, one-shot readout).

Arms (Common random numbers: per (regime, seed) every demo, every test point, the
ActionQuery mix, and C's shuffle permutation are drawn once; batch i is the same set of
demos for every arm):
  A_large      a wider concat-MLP action head, no bridge; sees the same raw features
  B_bridge     tiny features + one-layer Bridge Attention (cross-attend action tokens to
               C_R and to C_AQ+proprio, self-attend on the action tokens, tanh(g) raw gate
               with g starting at 0, then a residual FFN)
  C_shuffle    same tiny + bridge architecture and the same init as B, but conditions are
               shuffled across the batch at train and test time

Equal step budget STEPS, batch BATCH, learning rate LR. Metrics: test success %
(|a_hat - a| <= TOL), mean L1, parameter count, and a latency / FLOP proxy (multiply-adds
in one forward). Size and FLOP do not depend on the seed.

Regimes, written before the first run:
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
import random

SEEDS = (0, 1, 2, 3, 4)
STEPS, BATCH, TEST = 250, 8, 200
LR = 0.05
TOL = 0.25
NUM_ZERO = 1e-9
# A: wide concat MLP. B/C: tiny bridge. Written before the first run.
D_RAW_SHORT = 6   # 2 objects * 2 + 2 instruction one-hot
D_RAW_PREC = 16
D_PROP = 2
D_ACT = 2
D_LARGE = 24      # hidden width of the plain head
D_TINY = 6
N_ACT = 2         # action tokens
N_RAW = 2         # raw condition tokens
N_AQ = 2          # ActionQuery + proprio tokens
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


def transpose(m):
    return [list(col) for col in zip(*m)]


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


def make_demo(regime, rng, aq_mix):
    d_raw = raw_dim(regime)
    k = 0 if rng.random() < 0.5 else 1
    o0 = [rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)]
    o1 = [rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)]
    prop = [rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)]
    inst = [1.0, 0.0] if k == 0 else [0.0, 1.0]
    if regime == "precise":
        # long raw: objects + instruction + filler; action is a thin mix of all of it
        raw = (o0 + o1 + inst + [rng.uniform(-1.0, 1.0) for _ in range(d_raw - 6)])[:d_raw]
        # mix is provided by the caller so it is shared across the regime/seed
        action = None  # filled later
    else:
        raw = o0 + o1 + inst
        if regime == "short_id":
            action = [prop[0], -prop[1]]
        else:
            obj = o0 if k == 0 else o1
            action = obj[:]
    return {"raw": raw, "prop": prop, "action": action, "k": k, "o0": o0, "o1": o1}


def fill_precise_actions(demos, mix):
    for d in demos:
        d["action"] = [dot(mix[0], d["raw"]), dot(mix[1], d["raw"])]


def make_aq(raw, mix):
    # ActionQuery stand-in: a linear mix of the raw features, not the labelled object
    return [dot(mix[0], raw), dot(mix[1], raw)]


def shared_draws(regime, seed):
    rng = random.Random(3000 * STREAM[regime] + seed)
    d_raw = raw_dim(regime)
    aq_mix = [[rng.gauss(0.0, 0.5) for _ in range(d_raw)] for _ in range(2)]
    prec_mix = None
    if regime == "precise":
        prec_mix = [[rng.gauss(0.0, 0.4) for _ in range(d_raw)] for _ in range(2)]
    demos = []
    for _ in range(STEPS * BATCH):
        demos.append(make_demo(regime, rng, aq_mix))
    test = [make_demo(regime, rng, aq_mix) for _ in range(TEST)]
    if prec_mix is not None:
        fill_precise_actions(demos, prec_mix)
        fill_precise_actions(test, prec_mix)
    # shuffle permutation used by C: a derangement-ish perm of BATCH indices, one per batch
    # plus a test permutation
    shuffles = []
    for _ in range(STEPS):
        perm = list(range(BATCH))
        rng.shuffle(perm)
        if perm == list(range(BATCH)):
            if BATCH > 1:
                perm[0], perm[1] = perm[1], perm[0]
        shuffles.append(perm)
    test_perm = list(range(TEST))
    rng.shuffle(test_perm)
    inits = {
        "A": {
            "W1": rand_mat(rng, D_LARGE, d_raw + D_PROP),
            "b1": rand_vec(rng, D_LARGE),
            "W2": rand_mat(rng, D_ACT, D_LARGE),
            "b2": rand_vec(rng, D_ACT),
        },
        "B": init_bridge(rng, d_raw),
    }
    return {
        "d_raw": d_raw,
        "aq_mix": aq_mix,
        "demos": demos,
        "test": test,
        "shuffles": shuffles,
        "test_perm": test_perm,
        "inits": inits,
    }


def init_bridge(rng, d_raw):
    # tokenisers + one bridge layer + readout
    return {
        "Wr": rand_mat(rng, N_RAW * D_TINY, d_raw),  # raw -> N_RAW tokens
        "br": rand_vec(rng, N_RAW * D_TINY),
        "Wq": rand_mat(rng, D_TINY, 2),  # 2-D AQ mix -> one token
        "bq": rand_vec(rng, D_TINY),
        "Wp": rand_mat(rng, D_TINY, D_PROP),
        "bp": rand_vec(rng, D_TINY),
        "Wa": rand_mat(rng, N_ACT * D_TINY, D_ACT),  # init action (zeros) -> tokens; plus bias
        "ba": rand_vec(rng, N_ACT * D_TINY),
        "g": 0.0,  # tanh gate, paper init
        "Wmix": rand_mat(rng, D_TINY, 3 * D_TINY),
        "bmix": rand_vec(rng, D_TINY),
        "W1": rand_mat(rng, D_TINY, D_TINY),
        "b1": rand_vec(rng, D_TINY),
        "W2": rand_mat(rng, D_TINY, D_TINY),
        "b2": rand_vec(rng, D_TINY),
        "Wo": rand_mat(rng, D_ACT, N_ACT * D_TINY),
        "bo": rand_vec(rng, D_ACT),
    }


def n_params_large(d_raw):
    return D_LARGE * (d_raw + D_PROP) + D_LARGE + D_ACT * D_LARGE + D_ACT


def n_params_bridge(d_raw):
    return (
        N_RAW * D_TINY * d_raw + N_RAW * D_TINY
        + D_TINY * 2 + D_TINY
        + D_TINY * D_PROP + D_TINY
        + N_ACT * D_TINY * D_ACT + N_ACT * D_TINY
        + 1  # g
        + D_TINY * 3 * D_TINY + D_TINY
        + D_TINY * D_TINY + D_TINY
        + D_TINY * D_TINY + D_TINY
        + D_ACT * N_ACT * D_TINY + D_ACT
    )


def flops_large(d_raw):
    # W1 (D_LARGE x in) + W2 (D_ACT x D_LARGE)
    return D_LARGE * (d_raw + D_PROP) + D_ACT * D_LARGE


def flops_bridge(d_raw):
    # tokenisers
    f = N_RAW * D_TINY * d_raw + D_TINY * 2 + D_TINY * D_PROP + N_ACT * D_TINY * D_ACT
    # two cross-attns + self-attn (scores + weighted sum)
    def attn(nq, nk):
        return nq * nk * D_TINY + nq * nk * D_TINY  # Q·K and p·V
    f += attn(N_ACT, N_RAW) + attn(N_ACT, N_AQ) + attn(N_ACT, N_ACT)
    f += N_ACT * D_TINY * 3 * D_TINY  # mix
    f += 2 * N_ACT * D_TINY * D_TINY  # FFN
    f += D_ACT * N_ACT * D_TINY  # readout
    return f


# ---- attention with backward ----
SCALE = 1.0 / math.sqrt(D_TINY)


def xattn_forward(Q, K, V):
    # Q,K,V: list of vectors
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
        # o = sum p_j V_j
        for j, pj in enumerate(p):
            axpy_vec(dV[j], do, pj)
        dp = [dot(do, V[j]) for j in range(len(V))]
        # softmax backward: ds = p ⊙ (dp - sum p*dp)
        dotp = sum(pj * dpj for pj, dpj in zip(p, dp))
        ds = [pj * (dpj - dotp) for pj, dpj in zip(p, dp)]
        for j, dsj in enumerate(ds):
            # s_j = (q·K_j)/sqrt(d)
            axpy_vec(dQ[i], K[j], dsj * SCALE)
            axpy_vec(dK[j], q, dsj * SCALE)
    return dQ, dK, dV


def tokens_from(mat, bias, vec, n, d):
    flat = add_vec(matvec(mat, vec), bias)
    return [flat[i * d:(i + 1) * d] for i in range(n)], flat


def bridge_forward(params, raw, prop, aq, flop_acc=None):
    raw_toks, raw_flat = tokens_from(params["Wr"], params["br"], raw, N_RAW, D_TINY)
    aq_tok = add_vec(matvec(params["Wq"], aq), params["bq"])
    pr_tok = add_vec(matvec(params["Wp"], prop), params["bp"])
    aq_toks = [aq_tok, pr_tok]
    # action tokens from a zero init action (same length as the target)
    a0 = [0.0] * D_ACT
    act_toks, act_flat = tokens_from(params["Wa"], params["ba"], a0, N_ACT, D_TINY)
    ca1, c1 = xattn_forward(act_toks, raw_toks, raw_toks)
    ca2, c2 = xattn_forward(act_toks, aq_toks, aq_toks)
    sa, cs = xattn_forward(act_toks, act_toks, act_toks)
    gate = math.tanh(params["g"])
    mixed, mid, pre = [], [], []
    for t in range(N_ACT):
        cat = [gate * x for x in ca1[t]] + ca2[t] + sa[t]
        h = add_vec(matvec(params["Wmix"], cat), params["bmix"])
        # residual FFN
        z = add_vec(matvec(params["W1"], h), params["b1"])
        r = relu(z)
        h2 = add_vec(h, add_vec(matvec(params["W2"], r), params["b2"]))
        mixed.append(h2)
        mid.append((cat, h, z, r))
    flat = []
    for tok in mixed:
        flat.extend(tok)
    y = add_vec(matvec(params["Wo"], flat), params["bo"])
    cache = {
        "raw": raw, "prop": prop, "aq": aq, "a0": a0,
        "raw_toks": raw_toks, "aq_toks": aq_toks, "act_toks": act_toks,
        "ca1": ca1, "c1": c1, "ca2": ca2, "c2": c2, "sa": sa, "cs": cs,
        "gate": gate, "mid": mid, "mixed": mixed, "flat": flat, "y": y,
    }
    return y, cache


def linear_backward_matvec(W, x, dy):
    dW = outer(dy, x)
    db = dy[:]
    dx = [sum(W[k][j] * dy[k] for k in range(len(W))) for j in range(len(x))]
    return dW, db, dx


def zeros_like_params(p, d_raw):
    z = init_bridge(random.Random(0), d_raw)
    for k, v in z.items():
        if k == "g":
            z[k] = 0.0
        elif isinstance(v, list) and v and isinstance(v[0], list):
            z[k] = zeros(len(v), len(v[0]))
        else:
            z[k] = zeros(len(v))
    return z


def bridge_backward(params, cache, dy):
    d_raw = len(cache["raw"])
    g = zeros_like_params(params, d_raw)
    dWo, dbo, dflat = linear_backward_matvec(params["Wo"], cache["flat"], dy)
    axpy_mat(g["Wo"], dWo, 1.0)
    axpy_vec(g["bo"], dbo, 1.0)
    d_mixed = [dflat[i * D_TINY:(i + 1) * D_TINY] for i in range(N_ACT)]
    d_h = []
    d_cat = []
    for t in range(N_ACT):
        cat, h, z, r = cache["mid"][t]
        dh2 = d_mixed[t]
        # h2 = h + W2 r + b2
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
        d_h.append(dh)
        d_cat.append(dcat)
    gate = cache["gate"]
    dca1 = [d_cat[t][0:D_TINY] for t in range(N_ACT)]
    dca2 = [d_cat[t][D_TINY:2 * D_TINY] for t in range(N_ACT)]
    dsa = [d_cat[t][2 * D_TINY:3 * D_TINY] for t in range(N_ACT)]
    # gate * ca1: dca1_pre = gate * d(gate*ca1); dg = sum d(gate*ca1) * ca1 * sech^2
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
    # tokenisers
    d_raw_flat = []
    for tok in d_raw_toks:
        d_raw_flat.extend(tok)
    dWr, dbr, _draw = linear_backward_matvec(params["Wr"], cache["raw"], d_raw_flat)
    axpy_mat(g["Wr"], dWr, 1.0)
    axpy_vec(g["br"], dbr, 1.0)
    dWq, dbq, _daq = linear_backward_matvec(params["Wq"], cache["aq"], d_aq_toks[0])
    axpy_mat(g["Wq"], dWq, 1.0)
    axpy_vec(g["bq"], dbq, 1.0)
    dWp, dbp, _dp = linear_backward_matvec(params["Wp"], cache["prop"], d_aq_toks[1])
    axpy_mat(g["Wp"], dWp, 1.0)
    axpy_vec(g["bp"], dbp, 1.0)
    d_act_flat = []
    for tok in d_act:
        d_act_flat.extend(tok)
    dWa, dba, _da0 = linear_backward_matvec(params["Wa"], cache["a0"], d_act_flat)
    axpy_mat(g["Wa"], dWa, 1.0)
    axpy_vec(g["ba"], dba, 1.0)
    return g


def add_params(dst, src, s):
    for k, v in src.items():
        if k == "g":
            dst[k] += s * v
        elif isinstance(v, list) and v and isinstance(v[0], list):
            axpy_mat(dst[k], v, s)
        else:
            axpy_vec(dst[k], v, s)


def copy_params(p):
    out = {}
    for k, v in p.items():
        if k == "g":
            out[k] = v
        elif isinstance(v, list) and v and isinstance(v[0], list):
            out[k] = clip_copy_mat(v)
        else:
            out[k] = v[:]
    return out


def large_forward(params, raw, prop):
    x = list(raw) + list(prop)
    h = relu(add_vec(matvec(params["W1"], x), params["b1"]))
    y = add_vec(matvec(params["W2"], h), params["b2"])
    return y, x, h


def large_backward(params, x, h, pre_rel, dy):
    dW2, db2, dh = linear_backward_matvec(params["W2"], h, dy)
    dz = [dh[i] if pre_rel[i] > 0.0 else 0.0 for i in range(len(h))]
    dW1, db1, _dx = linear_backward_matvec(params["W1"], x, dz)
    return {"W1": dW1, "b1": db1, "W2": dW2, "b2": db2}


def large_forward_cache(params, raw, prop):
    x = list(raw) + list(prop)
    z = add_vec(matvec(params["W1"], x), params["b1"])
    h = relu(z)
    y = add_vec(matvec(params["W2"], h), params["b2"])
    return y, x, h, z


def l1_grad(y, target):
    # d/dy |y-t| = sign(y-t), 0 if equal
    dy = []
    loss = 0.0
    for yi, ti in zip(y, target):
        d = yi - ti
        loss += abs(d)
        if d > 0:
            dy.append(1.0)
        elif d < 0:
            dy.append(-1.0)
        else:
            dy.append(0.0)
    return loss, dy


def apply_shuffle(batch, perm):
    raws = [batch[i]["raw"] for i in perm]
    aqs = [batch[i]["aq"] for i in perm]
    out = []
    for i, demo in enumerate(batch):
        d = dict(demo)
        d["raw"] = raws[i]
        d["aq"] = aqs[i]
        out.append(d)
    return out


def attach_aq(demos, mix):
    out = []
    for d in demos:
        nd = dict(d)
        nd["aq"] = make_aq(d["raw"], mix)
        out.append(nd)
    return out


def train_large(draws):
    p = {
        "W1": clip_copy_mat(draws["inits"]["A"]["W1"]),
        "b1": draws["inits"]["A"]["b1"][:],
        "W2": clip_copy_mat(draws["inits"]["A"]["W2"]),
        "b2": draws["inits"]["A"]["b2"][:],
    }
    demos = attach_aq(draws["demos"], draws["aq_mix"])
    for s in range(STEPS):
        batch = demos[s * BATCH:(s + 1) * BATCH]
        acc = {k: (zeros(len(v), len(v[0])) if isinstance(v[0], list) else zeros(len(v))) for k, v in p.items()}
        for d in batch:
            y, x, h, z = large_forward_cache(p, d["raw"], d["prop"])
            _loss, dy = l1_grad(y, d["action"])
            dy = [v / BATCH for v in dy]
            g = large_backward(p, x, h, z, dy)
            for k in acc:
                if isinstance(acc[k][0], list):
                    axpy_mat(acc[k], g[k], 1.0)
                else:
                    axpy_vec(acc[k], g[k], 1.0)
        for k in p:
            if isinstance(p[k][0], list):
                axpy_mat(p[k], acc[k], -LR)
            else:
                axpy_vec(p[k], acc[k], -LR)
    return p


def train_bridge(draws, shuffle=False):
    p = copy_params(draws["inits"]["B"])
    demos = attach_aq(draws["demos"], draws["aq_mix"])
    for s in range(STEPS):
        batch = demos[s * BATCH:(s + 1) * BATCH]
        if shuffle:
            batch = apply_shuffle(batch, draws["shuffles"][s])
        acc = zeros_like_params(p, draws["d_raw"])
        for d in batch:
            y, cache = bridge_forward(p, d["raw"], d["prop"], d["aq"])
            _loss, dy = l1_grad(y, d["action"])
            dy = [v / BATCH for v in dy]
            g = bridge_backward(p, cache, dy)
            add_params(acc, g, 1.0)
        add_params(p, acc, -LR)
    return p


def eval_large(p, draws):
    tes = attach_aq(draws["test"], draws["aq_mix"])
    ok, l1 = 0, 0.0
    for d in tes:
        y, _, _, _ = large_forward_cache(p, d["raw"], d["prop"])
        err = [a - b for a, b in zip(y, d["action"])]
        dist = math.sqrt(sum(e * e for e in err))
        l1 += sum(abs(e) for e in err)
        if dist <= TOL:
            ok += 1
    n = len(tes)
    return {"success_%": 100.0 * ok / n, "l1": l1 / n}


def eval_bridge(p, draws, shuffle=False):
    tes = attach_aq(draws["test"], draws["aq_mix"])
    if shuffle:
        tes = apply_shuffle(tes, draws["test_perm"])
    ok, l1 = 0, 0.0
    for d in tes:
        y, _ = bridge_forward(p, d["raw"], d["prop"], d["aq"])
        err = [a - b for a, b in zip(y, d["action"])]
        dist = math.sqrt(sum(e * e for e in err))
        l1 += sum(abs(e) for e in err)
        if dist <= TOL:
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
        f"D_TINY={D_TINY} D_LARGE={D_LARGE} seeds={len(SEEDS)}"
    )
    print("no plant integration step (discrete SGD, L1, one-shot readout)")
    print("regime arm success_% l1 params flops  (mean+-sd over seeds; params/flops are deterministic)")
    keys = ("success_%", "l1", "params", "flops")
    import os
    only=os.environ.get("B18P3_ONLY")
    for regime in ((only,) if only else REGIMES):
        d_raw = raw_dim(regime)
        pa, fa = n_params_large(d_raw), flops_large(d_raw)
        pb, fb = n_params_bridge(d_raw), flops_bridge(d_raw)
        draws_all = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [] for arm in ARMS}
        for d in draws_all:
            pA = train_large(d)
            pB = train_bridge(d, shuffle=False)
            pC = train_bridge(d, shuffle=True)
            eA = eval_large(pA, d)
            eB = eval_bridge(pB, d, shuffle=False)
            eC = eval_bridge(pC, d, shuffle=True)
            eA["params"], eA["flops"] = float(pa), float(fa)
            eB["params"], eB["flops"] = float(pb), float(fb)
            eC["params"], eC["flops"] = float(pb), float(fb)
            res["A_large"].append(eA)
            res["B_bridge"].append(eB)
            res["C_shuffle"].append(eC)
        print(
            f"{regime} (d_raw={d_raw}; A params {pa} flops {fa}; B/C params {pb} flops {fb})"
        )
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


if __name__ == "__main__":
    main()
