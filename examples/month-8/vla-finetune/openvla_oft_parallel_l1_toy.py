#!/usr/bin/env python3
"""OpenVLA-OFT action-token toy: 256-bin autoregressive tokens vs a parallel L1 continuous action chunk vs a small diffusion head.

A stdlib stand-in for the fine-tuning recipe of "Fine-Tuning Vision-Language-Action
Models: Optimizing Speed and Success" (OpenVLA-OFT; Moo Jin Kim, Chelsea Finn,
Percy Liang; arXiv 2502.19645): discrete 256-bin action tokens decoded
autoregressively, versus parallel decoding of a continuous action chunk trained
with an L1 loss, versus a small diffusion action head.

This is a stdlib stand-in, not the 7B OpenVLA model and not a LoRA fine-tune:
the paper's 97.1 % and 26x are 以论文为准, not toy outputs.  GPU / LIBERO /
ALOHA: 本页未运行.  Not ChatVLA, not SimpleVLA-RL.

Stand-in model.  The observation is a cell index c in 0..NCELL-1 (NCELL=8) plus
an instruction bit l in {0,1}.  Every arm is a per-cell lookup fitted to the
demos in that cell (a perfect-capacity stand-in, so that only the action
representation and the decoding differ, not the model capacity).  An action
chunk has K steps x DA=2 dims, each value in [-1,1].
  A_ar_256bin : tokenise every demo value into 256 uniform bins on [-1,1] (bin
                width 2/256); per cell and per (step, dim) take the most frequent
                bin (ties -> lowest bin index) and decode its centre.  Forward
                passes per chunk = K*DA (one per token, autoregressive).
  B_oft_l1    : per cell and per (step, dim) the median of the demo values (the
                minimiser of L1; for an even count the mean of the two middle
                values).  Forward passes per chunk = 1 (parallel decoding).
  C_diffusion : per cell, start from x ~ gauss(0,1) per value and run T_DIFF=10
                denoising steps toward the demo set with a kernel score: at step
                i (sigma_i = 1.0 * (0.02/1.0)**(i/(T_DIFF-1))) replace x by the
                softmax(-|x - d|^2 / (2 sigma_i^2))-weighted mean of the cell's
                demo chunks d (whole-chunk distance), then add gauss(0,
                sigma_i*0.1) except after the last step.  Forward passes =
                T_DIFF.  Its random draws come from random.Random(5000+seed) and
                are consumed in a fixed order (cells in order, then steps in
                order, the noise of a step drawn after that step's update).
  D_oft_film  : like B but the lookup is per (cell, instruction) pair
                (language-conditioned, the OFT+ / FiLM idea); it differs from B
                only in the "language" regime and falls back to the per-cell
                median if a (cell, instruction) pair has no demo.

Common random numbers: for each (regime, seed) the demos are drawn once from
random.Random(seed*100 + regime_index) and shared by every arm; the test set is
one query per cell (and per instruction where relevant).

Regimes and parameters were written before the first run:
  unimodal : per cell a true chunk mu_c[k][j] = U[-0.8, 0.8] fixed per cell,
             demo = mu + gauss(0, NOISE) per value.  Metrics: abs_err = mean
             |pred - mu| over all values and cells, success = fraction of cells
             whose chunk has max |pred - mu| < SUCCESS_TOL, passes = forward
             passes per chunk.
  bimodal  : per cell each demo goes left (all values = -0.5 + gauss(0,0.01))
             or right (+0.5 + gauss(0,0.01)) with probability 1/2.  Metric:
             success = fraction of cells whose predicted chunk has every value
             within MODE_TOL of -0.5 or every value within MODE_TOL of +0.5.
  language : l=0 means "left" (target chunk all -0.5) and l=1 "right" (+0.5);
             the instruction agrees with a visual cue (cue = cell parity, even
             cells -> left) in 90 % of demos; the action follows l plus
             gauss(0,0.01).  At test every cell is queried with BOTH
             instructions.  Metric: follow_err = fraction of the 2*NCELL queries
             whose predicted chunk mean has the wrong sign for the instruction
             (a mean of exactly 0 counts as wrong for both instructions).
  k1       : as unimodal but K=1 (a single step).  Metrics: abs_err, passes.

Pairs: B-A, C-B, D-B on every metric of every regime, on the per-seed values
(first minus second).  passes is deterministic, so its verdict shows plainly.
Pre-declared expectations (printed, not tuned): unimodal -> B consistently
better than A on abs_err and on passes, and B vs C may near-tie on success while
C consistently costs more passes; bimodal -> B can average the modes and lose to
C (and A); language -> B (no language conditioning) consistently higher
follow_err than D; k1 -> the passes of B vs A differ only by DA.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared constants, written before the first run.
NCELL = 8
K = 8
DA = 2
N_DEMO = 10
NOISE = 0.002
SUCCESS_TOL = 0.003
MODE_TOL = 0.1
T_DIFF = 10
NBIN = 256
BIN_W = 2.0 / NBIN
SIGMA_MAX = 1.0
SIGMA_MIN = 0.02
MU_RANGE = 0.8        # unimodal per-cell true chunk, U[-0.8, 0.8]
MODE_VALUE = 0.5      # bimodal / language targets, +-0.5
FIT_NOISE = 0.01      # demo noise in the bimodal and language regimes
CUE_AGREE = 0.9       # language: the instruction agrees with the cell-parity cue
DIFF_SEED_BASE = 5000  # the diffusion head's random.Random(5000 + seed)

ARMS = ("A_ar_256bin", "B_oft_l1", "C_diffusion", "D_oft_film")
REGIMES = ("unimodal", "bimodal", "language", "k1")
REGIME_INDEX = {r: i for i, r in enumerate(REGIMES)}
REGIME_METRICS = {
    "unimodal": ("abs_err", "success", "passes"),
    "bimodal": ("success", "passes"),
    "language": ("follow_err", "passes"),
    "k1": ("abs_err", "passes"),
}
METRIC_UNIT = {"abs_err": "", "success": " frac", "follow_err": " frac", "passes": " fwd/chunk"}
PAIRS = (("B_oft_l1", "A_ar_256bin"), ("C_diffusion", "B_oft_l1"), ("D_oft_film", "B_oft_l1"))
DECLARED = {
    "unimodal": "declared: B consistently better than A on abs_err and on passes; B vs C may near-tie on success while C consistently costs more passes",
    "bimodal": "declared: B can average the modes and lose to C (and A)",
    "language": "declared: B (no language conditioning) consistently higher follow_err than D",
    "k1": "declared: the passes of B vs A differ only by DA",
}


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0  # identical values: no floating residue in mean or sd
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    """Half-up rounding on the shortest decimal repr; tiny non-zero values in scientific form."""
    if x != 0.0 and abs(x) < 5e-4:
        return format(Decimal(repr(x)), ".3e")
    s = format(Decimal(repr(x)), ".4f")
    return "0.0000" if s == "-0.0000" else s


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


def k_steps_of(regime):
    return 1 if regime == "k1" else K


def passes_of(arm, k_steps):
    if arm == "A_ar_256bin":
        return float(k_steps * DA)
    if arm == "C_diffusion":
        return float(T_DIFF)
    return 1.0


def gen_demos(regime, seed, n_demo=N_DEMO, noise=NOISE):
    """Common random numbers: one draw per (regime, seed), shared by every arm."""
    rng = random.Random(seed * 100 + REGIME_INDEX[regime])
    k_steps, n = k_steps_of(regime), k_steps_of(regime) * DA
    cells = []
    for c in range(NCELL):
        mu = None
        if regime in ("unimodal", "k1"):
            mu = [rng.uniform(-MU_RANGE, MU_RANGE) for _ in range(n)]
        chunks, labels = [], []
        for _ in range(n_demo):
            if regime in ("unimodal", "k1"):
                chunk = [mu[q] + rng.gauss(0.0, noise) for q in range(n)]
                label = 0
            elif regime == "bimodal":
                side = -MODE_VALUE if rng.random() < 0.5 else MODE_VALUE
                chunk = [side + rng.gauss(0.0, FIT_NOISE) for _ in range(n)]
                label = 0
            else:  # language
                cue = c % 2
                label = cue if rng.random() < CUE_AGREE else 1 - cue
                target = -MODE_VALUE if label == 0 else MODE_VALUE
                chunk = [target + rng.gauss(0.0, FIT_NOISE) for _ in range(n)]
            chunks.append(chunk)
            labels.append(label)
        cells.append({"mu": mu, "chunks": chunks, "labels": labels})
    return cells


def bin_index(v):
    b = int(math.floor((v + 1.0) / BIN_W))
    return 0 if b < 0 else (NBIN - 1 if b > NBIN - 1 else b)


def bin_centre(b):
    return -1.0 + (b + 0.5) * BIN_W


def median_pred(chunks, n):
    """Per (step, dim) the median of the demo values: the minimiser of the L1 loss."""
    out = []
    for q in range(n):
        vals = sorted(d[q] for d in chunks)
        m = len(vals)
        out.append(vals[m // 2] if m % 2 else 0.5 * (vals[m // 2 - 1] + vals[m // 2]))
    return out


def arm_a_pred(cell, n):
    """Most frequent 256-bin token per (step, dim), ties -> lowest bin index; decode its centre."""
    out = []
    for q in range(n):
        counts = [0] * NBIN
        for d in cell["chunks"]:
            counts[bin_index(d[q])] += 1
        best = 0
        for b in range(1, NBIN):
            if counts[b] > counts[best]:
                best = b
        out.append(bin_centre(best))
    return out


def arm_c_pred(cells, n, seed):
    """Kernel-score denoising toward the cell's demo chunks; draws from random.Random(5000+seed) in a fixed order."""
    rng = random.Random(DIFF_SEED_BASE + seed)
    out = []
    for cell in cells:
        chunks = cell["chunks"]
        x = [rng.gauss(0.0, 1.0) for _ in range(n)]
        for i in range(T_DIFF):
            sigma = SIGMA_MAX * (SIGMA_MIN / SIGMA_MAX) ** (i / (T_DIFF - 1))
            dists = [sum((x[q] - d[q]) ** 2 for q in range(n)) for d in chunks]
            low = min(dists)
            exps = [math.exp(-(dd - low) / (2.0 * sigma * sigma)) for dd in dists]
            tot = sum(exps)
            x = [sum(w * d[q] for w, d in zip(exps, chunks)) / tot for q in range(n)]
            if i < T_DIFF - 1:
                x = [x[q] + rng.gauss(0.0, sigma * 0.1) for q in range(n)]
        out.append(x)
    return out


def arm_d_pred(cell, n):
    """Per (cell, instruction) lookup; fall back to the per-cell median when a pair has no demo."""
    fallback = median_pred(cell["chunks"], n)
    out = {}
    for l in (0, 1):
        sel = [ch for ch, lab in zip(cell["chunks"], cell["labels"]) if lab == l]
        out[l] = median_pred(sel, n) if sel else list(fallback)
    return out


def predict_arm(arm, cells, k_steps, seed):
    n = k_steps * DA
    if arm == "A_ar_256bin":
        base = [arm_a_pred(cell, n) for cell in cells]
    elif arm == "B_oft_l1":
        base = [median_pred(cell["chunks"], n) for cell in cells]
    elif arm == "C_diffusion":
        base = arm_c_pred(cells, n, seed)
    else:
        base = [arm_d_pred(cell, n) for cell in cells]
    out = []
    for c in range(NCELL):
        out.append({l: (base[c][l] if arm == "D_oft_film" else list(base[c])) for l in (0, 1)})
    return out


def evaluate(arm, regime, seed, cells, k_steps, success_tol=SUCCESS_TOL):
    preds = predict_arm(arm, cells, k_steps, seed)
    if regime in ("unimodal", "k1"):
        total_err, good = 0.0, 0
        for c, cell in enumerate(cells):
            mu, p = cell["mu"], preds[c][0]
            errs = [abs(p[q] - mu[q]) for q in range(k_steps * DA)]
            total_err += sum(errs) / len(errs)
            if max(errs) < success_tol:
                good += 1
        return {"abs_err": total_err / NCELL, "success": good / NCELL, "passes": passes_of(arm, k_steps)}
    if regime == "bimodal":
        good = 0
        for c in range(NCELL):
            p = preds[c][0]
            left = all(abs(v + MODE_VALUE) < MODE_TOL for v in p)
            right = all(abs(v - MODE_VALUE) < MODE_TOL for v in p)
            if left or right:
                good += 1
        return {"success": good / NCELL, "passes": passes_of(arm, k_steps)}
    wrong, total = 0, 0
    for c in range(NCELL):
        for l in (0, 1):
            p = preds[c][l]
            m = sum(p) / len(p)
            sign = 1 if m > 0.0 else (-1 if m < 0.0 else 0)
            want = -1 if l == 0 else 1
            if sign != want:
                wrong += 1
            total += 1
    return {"follow_err": wrong / total, "passes": passes_of(arm, k_steps)}


def collect(regime, n_demo=N_DEMO, noise=NOISE, success_tol=SUCCESS_TOL):
    demos = {s: gen_demos(regime, s, n_demo=n_demo, noise=noise) for s in SEEDS}
    k_steps = k_steps_of(regime)
    return {arm: [evaluate(arm, regime, s, demos[s], k_steps, success_tol) for s in SEEDS]
            for arm in ARMS}


def col(rows, key):
    return [x[key] for x in rows]


def regime_note(regime, demos):
    if regime in ("unimodal", "k1"):
        vals = []
        for s in SEEDS:
            worst = 0.0
            for cell in demos[s]:
                mu = cell["mu"]
                for d in cell["chunks"]:
                    worst = max(worst, max(abs(d[q] - mu[q]) for q in range(len(mu))))
            vals.append(worst)
        return "  per-seed max |demo - mu| over all cells: " + " ".join(num(v) for v in vals)
    if regime == "bimodal":
        vals = []
        for s in SEEDS:
            even = 0
            for cell in demos[s]:
                left = sum(1 for d in cell["chunks"] if d[0] < 0.0)
                if 2 * left == len(cell["chunks"]):
                    even += 1
            vals.append(even)
        return "  per-seed cells with an even left/right split (the median collapses): " + " ".join(str(v) for v in vals)
    vals = []
    for s in SEEDS:
        empty = 0
        for c, cell in enumerate(demos[s]):
            for l in (0, 1):
                if l != c % 2 and not any(lab == l for lab in cell["labels"]):
                    empty += 1
        vals.append(empty)
    return "  per-seed empty mismatched (cell,instruction) pairs (D falls back to the per-cell median): " + " ".join(str(v) for v in vals)


def report(regime):
    res = collect(regime)
    demos = {s: gen_demos(regime, s) for s in SEEDS}
    metrics = REGIME_METRICS[regime]
    if regime == "unimodal":
        head = (f"unimodal (per-cell true chunk mu ~ U[-{num(MU_RANGE)}, {num(MU_RANGE)}] fixed per cell; "
                f"demo = mu + N(0,{num(NOISE)}); success tol {num(SUCCESS_TOL)} on max |pred - mu| per cell):")
    elif regime == "bimodal":
        head = (f"bimodal (each demo is all -{num(MODE_VALUE)} + N(0,{num(FIT_NOISE)}) or all +{num(MODE_VALUE)} + "
                f"N(0,{num(FIT_NOISE)}) with probability 1/2; success tol {num(MODE_TOL)} on every value):")
    elif regime == "language":
        head = (f"language (l=0 'left' = all -{num(MODE_VALUE)}, l=1 'right' = all +{num(MODE_VALUE)}; the instruction "
                f"matches the cell-parity cue in {int(CUE_AGREE * 100)} % of demos; every cell queried with both instructions):")
    else:
        head = (f"k1 (as unimodal with K=1: a single step x {DA} dims; demo = mu + N(0,{num(NOISE)}); "
                f"success tol {num(SUCCESS_TOL)} on max |pred - mu| per cell):")
    print(head)
    print("  " + DECLARED[regime])
    print(regime_note(regime, demos))
    for arm in ARMS:
        print(f"  {arm} " + " ".join(
            f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}{METRIC_UNIT[key]}" for key in metrics))
    for a, b in PAIRS:
        for key in metrics:
            print(f"  paired {a[0]}-{b[0]} {key}: {verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("OpenVLA-OFT action-token toy; 256-bin autoregressive tokens vs a parallel L1 continuous chunk vs a small diffusion head; stdlib stand-in, not the 7B OpenVLA / LoRA model")
    print(f"seeds={len(SEEDS)} cells={NCELL} K={K} DA={DA} demos/cell={N_DEMO} bins={NBIN} noise={num(NOISE)} "
          f"success_tol={num(SUCCESS_TOL)} mode_tol={num(MODE_TOL)} T_DIFF={T_DIFF} (declared toy parameters, not the paper's)")
    print(f"Action chunk: {K} steps x {DA} dims, each value in [-1,1]; every arm is a per-cell lookup fitted to that cell's demos (perfect-capacity stand-in), so only the action representation and the decoding differ")
    print("Common random numbers: the demos of each (regime, seed) are drawn once from random.Random(seed*100+regime_index) and shared by every arm; the diffusion head draws from random.Random(5000+seed) in a fixed order")
    print("Regimes and parameters were written before the first run")
    # Labelled hand calculations.
    print(f"hand_calc binning: {NBIN} uniform bins on [-1,1] -> bin width 2/{NBIN}={num(BIN_W)}; worst-case quantisation error half a bin={num(BIN_W / 2)}")
    print(f"hand_calc forward passes: AR tokens K*DA={K}*{DA}={K * DA} (one per token, autoregressive) vs parallel L1 1 "
          f"({K * DA}x fewer passes in this toy; the paper's 26x is 以论文为准 and measured differently) vs diffusion steps {T_DIFF}")
    print(f"hand_calc bimodal: with a 5-5 left/right split the median of {N_DEMO} demos sits between the modes, "
          f"~(-{num(MODE_VALUE)}+{num(MODE_VALUE)})/2={num(0.0)}, outside MODE_TOL={num(MODE_TOL)} of both; "
          f"P(even split)=C({N_DEMO},5)/2^{N_DEMO}={num(math.comb(N_DEMO, 5) / 2.0 ** N_DEMO)}")
    print(f"hand_calc language: a mismatched (cell,instruction) pair holds no demo with prob {num(CUE_AGREE)}^{N_DEMO}={num(CUE_AGREE ** N_DEMO)} "
          f"(D falls back to the per-cell median there); B has no instruction input at all, so it can only follow the cell-parity cue")
    for regime in REGIMES:
        report(regime)
    print("alternatives (post-hoc checks of the declared tolerances, noise and demo count; same seeds, declared before the run, not adopted):")
    for tol in (0.002, 0.005):
        alt = collect("unimodal", success_tol=tol)
        print(f"  unimodal SUCCESS_TOL={num(tol)}: paired B-A success@alt: {verdict(col(alt['B_oft_l1'], 'success'), col(alt['A_ar_256bin'], 'success'))}")
    alt = collect("unimodal", noise=0.01)
    print(f"  unimodal NOISE={num(0.01)}: paired B-A abs_err@alt: {verdict(col(alt['B_oft_l1'], 'abs_err'), col(alt['A_ar_256bin'], 'abs_err'))}")
    alt = collect("bimodal", n_demo=11)
    print(f"  bimodal N_DEMO=11: paired C-B success@alt: {verdict(col(alt['C_diffusion'], 'success'), col(alt['B_oft_l1'], 'success'))}")
    print("No universal winner: parallel L1 is precise and cheap on unimodal chunks, averages bimodal demos, and ignores an instruction it is not conditioned on")
    print("7B OpenVLA / LoRA / LIBERO / ALOHA / GPU: 本页未运行; OpenVLA-OFT paper numbers 以论文为准")


if __name__ == "__main__":
    main()
