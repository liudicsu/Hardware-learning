#!/usr/bin/env python3
"""NORA-style small VLA with FAST+-style action tokens vs a large per-step-binning head.

Synthetic action chunks, stdlib only.  Not the NORA 3B checkpoint, not
Qwen-2.5-VL, not the real FAST+ tokenizer (no BPE here), not LIBERO / WidowX
and not a GPU: 本页未运行.  Paper numbers (3B, 970k demonstrations, success
rates) 以论文为准 and are not toy outputs.  Not VLA-Adapter's Bridge Attention,
not SmolVLA and not the pi0-FAST catalogue line.

What the NORA paper (arXiv 2504.19854) says, and what this toy keeps:
  NORA is a 3B VLA on a Qwen-2.5-VL-3B backbone that autoregressively
  generates FAST+ action tokens (2048 extra vocabulary tokens) and decodes them
  into actions; the motivation is lower overhead than 7B-class VLAs.  This toy
  keeps two cost levers - fewer parameters and fewer action tokens per chunk -
  and one risk - a smaller backbone may fit long horizons worse.

Per (regime, seed) the chunks are smooth multi-joint trajectories; a policy's
prediction is the true chunk plus model error SIG * z, where z is one shared
standard-normal draw per value (common random numbers: the same z for every
arm, only the declared SIG differs).  Arms:
  A_large_bins : P_LARGE=7.0 B-parameter stand-in, one token per joint per step
                 (256 bins over -1..1, OpenVLA-style), SIG_LARGE
  B_small_fast : P_SMALL=3.0 B-parameter stand-in, FAST-style tokens: per joint
                 a DCT over the chunk's time axis, scaled by GAMMA and rounded;
                 tokens = nonzero rounded coefficients (BPE not modelled), SIG_SMALL
  C_shuffled   : B's model and tokens, but the decoder reads them through a
                 shuffled codebook (a fixed random permutation of token values)
Success: chunk RMSE against the true chunk strictly below TOL.  Cost proxy:
parameters x generated tokens (B-param x token), a stand-in for decode work.
No integration step: chunks are evaluated, not simulated.

Regimes and parameters were written before the first run:
  short_in_dist : H=10 steps, SIG_LARGE=SIG_SMALL=0.030 - A and B may near-tie
                  on success; B consistent lower cost; C consistent lose
  long_horizon  : H=30 steps, SIG_LARGE=0.040, SIG_SMALL=0.055 (the small
                  backbone fits long horizons worse - a declared assumption)
                  - B may LOSE success to A; keep and print whatever happens
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared model parameters, written before the first run (toy values).
D = 7                 # joints / action dimensions
N_EP = 200            # chunks per seed
BINS = 256            # A: per-step bins over -1..1
GAMMA = 10.0          # B/C: DCT coefficient scale before rounding (FAST-style)
P_LARGE = 7.0         # B-parameter stand-in for a 7B-class head
P_SMALL = 3.0         # B-parameter stand-in for a 3B head
TOL = 0.060           # success iff chunk RMSE < TOL (strict)
VOCAB = 64            # C: shuffled codebook over integer values -VOCAB..VOCAB

REGIMES = {
    "short_in_dist": {"H": 10, "SIG_LARGE": 0.030, "SIG_SMALL": 0.030},
    "long_horizon": {"H": 30, "SIG_LARGE": 0.040, "SIG_SMALL": 0.055},
}
ARMS = ("A_large_bins", "B_small_fast", "C_shuffled")


_COS = {}


def cos_table(n):
    """cos(pi*(t+0.5)*k/n) for every (k, t), cached per chunk length."""
    if n not in _COS:
        _COS[n] = [[math.cos(math.pi * (t + 0.5) * k / n) for t in range(n)] for k in range(n)]
    return _COS[n]


def dct(x):
    n = len(x)
    cs = cos_table(n)
    out = []
    for k in range(n):
        s = sum(x[t] * cs[k][t] for t in range(n))
        out.append(s * math.sqrt((1.0 if k == 0 else 2.0) / n))
    return out


def idct(c):
    n = len(c)
    cs = cos_table(n)
    w = [math.sqrt((1.0 if k == 0 else 2.0) / n) for k in range(n)]
    out = []
    for t in range(n):
        s = sum(c[k] * w[k] * cs[k][t] for k in range(n))
        out.append(s)
    return out


def shared_chunks(regime, seed):
    """Common random numbers: chunks, model-error draws and the codebook permutation."""
    h = REGIMES[regime]["H"]
    rng = random.Random(f"{regime}/{seed}")
    eps = []
    for _ in range(N_EP):
        truth, z = [], []
        for _ in range(D):
            a, f, ph, off = rng.uniform(0.2, 0.6), rng.uniform(0.2, 1.0), rng.uniform(0.0, 2 * math.pi), rng.uniform(-0.2, 0.2)
            truth.append([off + a * math.sin(2 * math.pi * f * t / h + ph) for t in range(h)])
            z.append([rng.gauss(0.0, 1.0) for _ in range(h)])
        eps.append({"truth": truth, "z": z})
    vals = list(range(-VOCAB, VOCAB + 1))
    perm = vals[:]
    rng.shuffle(perm)
    return eps, dict(zip(vals, perm))


def clip(v):
    return max(-1.0, min(1.0, v))


def bins_roundtrip(row):
    w = 2.0 / BINS
    return [-1.0 + (min(int((clip(v) + 1.0) / w), BINS - 1) + 0.5) * w for v in row]


def fast_tokens(row, gamma):
    return [int(round(gamma * c)) for c in dct([clip(v) for v in row])]


def run_seed(regime, seed, arm, gamma=GAMMA):
    cfg = REGIMES[regime]
    sig = cfg["SIG_LARGE"] if arm == "A_large_bins" else cfg["SIG_SMALL"]
    params = P_LARGE if arm == "A_large_bins" else P_SMALL
    eps, book = shared_chunks(regime, seed)
    succ = 0
    tok_sum = rmse_sum = 0.0
    for ep in eps:
        se = 0.0
        tokens = 0
        for d in range(D):
            truth = ep["truth"][d]
            pred = [x + sig * e for x, e in zip(truth, ep["z"][d])]
            if arm == "A_large_bins":
                rec = bins_roundtrip(pred)
                tokens += len(pred)
            else:
                q = fast_tokens(pred, gamma)
                tokens += sum(1 for v in q if v != 0)
                if arm == "C_shuffled":
                    q = [book.get(v, v) if v != 0 else 0 for v in q]
                rec = idct([v / gamma for v in q])
            se += sum((r - x) ** 2 for r, x in zip(rec, truth))
        rmse = math.sqrt(se / (D * len(ep["truth"][0])))
        rmse_sum += rmse
        tok_sum += tokens
        succ += int(rmse < TOL)
    tok = tok_sum / len(eps)
    return {"success_pct": 100.0 * succ / len(eps), "rmse": rmse_sum / len(eps),
            "tokens": tok, "cost": params * tok}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
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


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


_TABLES = {}


def table(regime, gamma=GAMMA):
    if (regime, gamma) not in _TABLES:
        _TABLES[(regime, gamma)] = {arm: [run_seed(regime, seed, arm, gamma) for seed in SEEDS] for arm in ARMS}
    return _TABLES[(regime, gamma)]


def col(res, arm, key):
    return [float(r[key]) for r in res[arm]]


def main():
    print("Synthetic NORA-style small-VLA + FAST-style token toy (arXiv 2504.19854); shared chunks; not the NORA checkpoint")
    print(f"seeds={len(SEEDS)} D={D} N_EP={N_EP} BINS={BINS} GAMMA={GAMMA:.1f} P_LARGE={P_LARGE:.1f} P_SMALL={P_SMALL:.1f} "
          f"TOL={TOL:.3f} VOCAB={VOCAB} (toy values; BPE not modelled)")
    print("No integration step: chunks are scored, not simulated; no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print(f"hand_calc A tokens: one per joint per step, D*H = {D}*10 = {D * 10} (H=10) and {D}*30 = {D * 30} (H=30)")
    print(f"hand_calc A bin error: bin width 2/{BINS} = {2.0 / BINS:.6f}, at most half a bin = {1.0 / BINS:.6f}")
    print(f"hand_calc rounding RMS per coefficient (uniform error): 1/(GAMMA*sqrt(12)) = {1.0 / (GAMMA * math.sqrt(12.0)):.6f}")
    print(f"hand_calc cost ratio at equal tokens: P_SMALL/P_LARGE = {P_SMALL / P_LARGE:.4f}")
    print("success_rule: success iff chunk RMSE < TOL (strict); "
          f"rmse {TOL:.4f} -> success {int(TOL < TOL)}; rmse {TOL - 0.0001:.4f} -> success {int(TOL - 0.0001 < TOL)}")
    for regime, cfg in REGIMES.items():
        res = table(regime)
        print(f"{regime} (H={cfg['H']} steps, SIG_LARGE={cfg['SIG_LARGE']:.3f}, SIG_SMALL={cfg['SIG_SMALL']:.3f}; "
              f"{N_EP} chunks per seed):")
        for arm in ARMS:
            print(f"  {arm} success_pct {fmt_pair(*mean_sd(col(res, arm, 'success_pct')))} "
                  f"rmse {fmt_pair(*mean_sd(col(res, arm, 'rmse')))} tokens {fmt_pair(*mean_sd(col(res, arm, 'tokens')))} "
                  f"cost {fmt_pair(*mean_sd(col(res, arm, 'cost')))}")
        print(f"  paired B-A success_pct: {verdict(col(res, 'B_small_fast', 'success_pct'), col(res, 'A_large_bins', 'success_pct'))}")
        print(f"  paired B-A tokens: {verdict(col(res, 'B_small_fast', 'tokens'), col(res, 'A_large_bins', 'tokens'))}")
        print(f"  paired B-A cost: {verdict(col(res, 'B_small_fast', 'cost'), col(res, 'A_large_bins', 'cost'))}")
        print(f"  paired C-B success_pct: {verdict(col(res, 'C_shuffled', 'success_pct'), col(res, 'B_small_fast', 'success_pct'))}")
    for regime, alt in (("short_in_dist", 20.0), ("long_horizon", 20.0)):
        base = table(regime)
        res = table(regime, alt)
        print(f"alternative GAMMA={alt:.1f} on {regime} (same seeds):")
        print(f"  B_small_fast success_pct@alt {fmt_pair(*mean_sd(col(res, 'B_small_fast', 'success_pct')))} "
              f"tokens@alt {fmt_pair(*mean_sd(col(res, 'B_small_fast', 'tokens')))} "
              f"(default success_pct {fmt_pair(*mean_sd(col(base, 'B_small_fast', 'success_pct')))})")
        print(f"  paired B-A success_pct@alt: {verdict(col(res, 'B_small_fast', 'success_pct'), col(res, 'A_large_bins', 'success_pct'))}")
        print(f"  paired B-A cost@alt: {verdict(col(res, 'B_small_fast', 'cost'), col(res, 'A_large_bins', 'cost'))}")
    print("No winner declared: fewer parameters and fewer action tokens cut the decode-cost proxy on every chunk, "
          "but success depends on whether the small backbone fits the task, and a decoder with the wrong codebook fails")
    print("NORA checkpoint / LIBERO / WidowX / GPU: 本页未运行; paper numbers 以论文为准")


if __name__ == "__main__":
    main()
