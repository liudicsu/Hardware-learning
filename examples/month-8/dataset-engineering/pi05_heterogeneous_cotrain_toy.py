#!/usr/bin/env python3
"""Synthetic heterogeneous co-training stand-in for a pi0.5-style mixture.

Stdlib only. Shared scenes, instructions and evaluation features are drawn
once per (regime, seed) and then read by every arm (common random numbers).

Arm A uses only target-robot / in-domain action features. Arm B is a
co-training mixture stand-in: declared target-robot, web, subtask and
other-robot weights. Arm C uses the web / subtask / other-robot features
with no target-robot actions.

This is a linear lookup stand-in, not pi0.5 weights and not a house rollout.
It is not Knowledge Insulation, not a pi0 10-step flow-matching convention,
not a FAST-then-flow architecture, and not RTC latency. Paper first-phase
non-target-data percentage and house-clean figures are 以论文为准 and are
not toy outputs. GPU / pi0.5 weights / real homes: 本页未运行.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared toy parameters (linear lookup stand-in, not paper percentages).
N_SCENES = 25
BIAS = 0.0500
SIG = 0.0800
CLIP_LO = 0.0000
CLIP_HI = 1.0000
W_TARGET = 0.4000
W_WEB = 0.2000
W_SUBTASK = 0.2500
W_OTHER = 0.1500
W_TARGET_A = 1.0000
W_TARGET_C = 0.0000

# In-domain lab-like: target and co-train features are similarly informative.
# OOD / new-home stand-in: target-robot features drop; web / subtask stay useful.
MUS = {
    "in_domain": {"target": 0.7500, "web": 0.7500, "subtask": 0.7500, "other": 0.7500},
    "ood_new_home": {"target": 0.3500, "web": 0.6000, "subtask": 0.6000, "other": 0.5500},
}

METRICS = ("success",)
ARMS = ("A_target_only", "B_cotrain", "C_no_target")
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

# name: declared expectation; written before the first run
REGIMES = {
    "in_domain": "A and B may near-tie on success (lab-like in-domain task) - keep",
    "ood_new_home": "B consistently above A on success (OOD new-home stand-in) - keep",
}

REGIME_IDS = {"in_domain": 0, "ood_new_home": 1}

C_EXPECT = "C loses to B on success (no target-robot actions) - keep"

ALT_SIG = 0.1200
ALT_W = {"target": 0.5000, "web": 0.2000, "subtask": 0.2000, "other": 0.1000}


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
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


def clip(x, lo=CLIP_LO, hi=CLIP_HI):
    return lo if x < lo else hi if x > hi else x


def draw_features(regime, seed, sig=SIG):
    rng = random.Random(seed + 1000 * REGIME_IDS[regime] + int(round(1000 * sig)))
    if sig == SIG:
        rng = random.Random(seed + 1000 * REGIME_IDS[regime])
    mus = MUS[regime]
    scenes = []
    for _ in range(N_SCENES):
        target = clip(rng.gauss(mus["target"], sig))
        web = clip(rng.gauss(mus["web"], sig))
        subtask = clip(rng.gauss(mus["subtask"], sig))
        other = clip(rng.gauss(mus["other"], sig))
        scenes.append((target, web, subtask, other))
    return scenes


def score_of(feat, weights):
    target, web, subtask, other = feat
    raw = (
        BIAS
        + weights["target"] * target
        + weights["web"] * web
        + weights["subtask"] * subtask
        + weights["other"] * other
    )
    return clip(raw)


def arm_weights():
    return {
        "A_target_only": {"target": W_TARGET_A, "web": 0.0, "subtask": 0.0, "other": 0.0},
        "B_cotrain": {"target": W_TARGET, "web": W_WEB, "subtask": W_SUBTASK, "other": W_OTHER},
        "C_no_target": {"target": W_TARGET_C, "web": W_WEB, "subtask": W_SUBTASK, "other": W_OTHER},
    }


def run_regime(regime, seed, sig=SIG, b_weights=None):
    scenes = draw_features(regime, seed, sig=sig)
    weights = arm_weights()
    if b_weights is not None:
        weights["B_cotrain"] = b_weights
        weights["C_no_target"] = {
            "target": W_TARGET_C,
            "web": b_weights["web"],
            "subtask": b_weights["subtask"],
            "other": b_weights["other"],
        }
    out = {}
    for arm, w in weights.items():
        suc = sum(score_of(feat, w) for feat in scenes) / float(N_SCENES)
        out[arm] = {"success": suc}
    return out


def main():
    w_sum = W_TARGET + W_WEB + W_SUBTASK + W_OTHER
    c_sum = W_WEB + W_SUBTASK + W_OTHER
    print(
        "Heterogeneous co-training toy: shared synthetic scenes / instructions / "
        "eval under common random numbers (linear lookup stand-in, not pi0.5 "
        "weights, not a house rollout)"
    )
    print(
        "Paper first-phase non-target-data percentage and house-clean figures "
        "以论文为准 and are not toy outputs; GPU / pi0.5 weights / real homes: "
        "本页未运行"
    )
    print(
        f"seeds={len(SEEDS)} n_scenes={num(float(N_SCENES))} bias={num(BIAS)} "
        f"sig={num(SIG)} clip_lo={num(CLIP_LO)} clip_hi={num(CLIP_HI)} "
        f"w_target={num(W_TARGET)} w_web={num(W_WEB)} w_subtask={num(W_SUBTASK)} "
        f"w_other={num(W_OTHER)} w_sum={num(w_sum)} "
        f"w_target_A={num(W_TARGET_A)} w_target_C={num(W_TARGET_C)} "
        f"c_used_weight_sum={num(c_sum)} "
        f"mu_in_domain_target={num(MUS['in_domain']['target'])} "
        f"mu_in_domain_web={num(MUS['in_domain']['web'])} "
        f"mu_in_domain_subtask={num(MUS['in_domain']['subtask'])} "
        f"mu_in_domain_other={num(MUS['in_domain']['other'])} "
        f"mu_ood_target={num(MUS['ood_new_home']['target'])} "
        f"mu_ood_web={num(MUS['ood_new_home']['web'])} "
        f"mu_ood_subtask={num(MUS['ood_new_home']['subtask'])} "
        f"mu_ood_other={num(MUS['ood_new_home']['other'])}"
    )
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: the scene / instruction / eval feature draws "
        "are shared across arms at each regime and seed"
    )
    print(f"hand_calc n_scenes = {num(float(N_SCENES))}")
    print(
        f"hand_calc B mixture weights {num(W_TARGET)} + {num(W_WEB)} + "
        f"{num(W_SUBTASK)} + {num(W_OTHER)} = {num(w_sum)}"
    )
    print(
        f"hand_calc C used-weight sum {num(W_WEB)} + {num(W_SUBTASK)} + "
        f"{num(W_OTHER)} = {num(c_sum)} (w_target_C = {num(W_TARGET_C)}, not renormalized)"
    )
    print(f"hand_calc bias = {num(BIAS)} sig = {num(SIG)} clip = {num(CLIP_LO)} to {num(CLIP_HI)}")
    print(
        f"hand_calc in_domain mus target/web/subtask/other = "
        f"{num(MUS['in_domain']['target'])}, {num(MUS['in_domain']['web'])}, "
        f"{num(MUS['in_domain']['subtask'])}, {num(MUS['in_domain']['other'])}"
    )
    print(
        f"hand_calc ood_new_home mus target/web/subtask/other = "
        f"{num(MUS['ood_new_home']['target'])}, {num(MUS['ood_new_home']['web'])}, "
        f"{num(MUS['ood_new_home']['subtask'])}, {num(MUS['ood_new_home']['other'])}"
    )
    print(
        f"hand_calc in_domain expected A ~ {num(BIAS)} + {num(W_TARGET_A)} * "
        f"{num(MUS['in_domain']['target'])} = {num(BIAS + W_TARGET_A * MUS['in_domain']['target'])}"
    )
    print(
        f"hand_calc in_domain expected B ~ {num(BIAS)} + {num(w_sum)} * "
        f"{num(MUS['in_domain']['target'])} = {num(BIAS + w_sum * MUS['in_domain']['target'])}"
    )
    ood = MUS["ood_new_home"]
    b_ood = BIAS + W_TARGET * ood["target"] + W_WEB * ood["web"] + W_SUBTASK * ood["subtask"] + W_OTHER * ood["other"]
    a_ood = BIAS + W_TARGET_A * ood["target"]
    c_ood = BIAS + W_WEB * ood["web"] + W_SUBTASK * ood["subtask"] + W_OTHER * ood["other"]
    print(f"hand_calc ood_new_home expected A ~ {num(a_ood)}")
    print(f"hand_calc ood_new_home expected B ~ {num(b_ood)}")
    print(f"hand_calc ood_new_home expected C ~ {num(c_ood)}")

    for r, exp in REGIMES.items():
        print(f"declared {r}: {exp}")
        print(f"declared {r} C: {C_EXPECT}")

    store = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_sig = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_w = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    for seed in SEEDS:
        for r in REGIMES:
            official = run_regime(r, seed)
            sig_run = run_regime(r, seed, sig=ALT_SIG)
            w_run = run_regime(r, seed, b_weights=ALT_W)
            for arm in ARMS:
                for m in METRICS:
                    store[r][arm][m].append(official[arm][m])
                    alt_sig[r][arm][m].append(sig_run[arm][m])
                    alt_w[r][arm][m].append(w_run[arm][m])

    for r in REGIMES:
        print(f"regime {r}")
        for arm in ARMS:
            for m in METRICS:
                mu, sd = mean_sd(store[r][arm][m])
                print(f"  {arm} {m}: {num(mu)}+-{num(sd)}")
        for left, right in PAIRS:
            la = [a for a in ARMS if a.startswith(left + "_")][0]
            ra = [a for a in ARMS if a.startswith(right + "_")][0]
            for m in METRICS:
                print(f"  paired {left}-{right} {m}: {verdict(store[r][la][m], store[r][ra][m])}")

    print("alternatives on the same seeds (not adopted):")
    print(f"  alternative sig={num(ALT_SIG)}")
    for r in REGIMES:
        print(f"  regime {r}")
        for left, right in (("B", "A"), ("C", "B")):
            la = [a for a in ARMS if a.startswith(left + "_")][0]
            ra = [a for a in ARMS if a.startswith(right + "_")][0]
            print(
                f"    paired {left}-{right} success: "
                f"{verdict(alt_sig[r][la]['success'], alt_sig[r][ra]['success'])}"
            )
    print(
        f"  alternative B weights target={num(ALT_W['target'])} web={num(ALT_W['web'])} "
        f"subtask={num(ALT_W['subtask'])} other={num(ALT_W['other'])}"
    )
    for r in REGIMES:
        print(f"  regime {r}")
        for left, right in (("B", "A"), ("C", "B")):
            la = [a for a in ARMS if a.startswith(left + "_")][0]
            ra = [a for a in ARMS if a.startswith(right + "_")][0]
            print(
                f"    paired {left}-{right} success: "
                f"{verdict(alt_w[r][la]['success'], alt_w[r][ra]['success'])}"
            )


if __name__ == "__main__":
    main()
