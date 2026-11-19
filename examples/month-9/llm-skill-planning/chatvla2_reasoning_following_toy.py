#!/usr/bin/env python3
"""Synthetic ChatVLA-2-style reasoning-following toy.

A linear / table stand-in: a reasoner scores a board equation and an action
head picks a number card. Not Qwen2-VL, not DexVLA, not the paper's
52-equation lab. Paper math-matching scores (43/52 and the rest) are
以论文为准; GPU / real whiteboard / paper-task runs are 本页未运行.

Arms: A_overwrite (naive dense end-to-end fine-tune that overwrites the
reasoner on in-domain robot equations only), B_two_stage (stage-1
co-train on image-text arithmetic plus in-domain robot data, then
stage-2 freeze the reasoner and train only action-following),
C_stage2_only (train the action head against a frozen, un-co-trained
reasoner). Regimes: in_domain (the memorised training equations) and
ood (unseen equations).

Metrics: pick_acc (the chosen card equals the true sum) and
reason_then_pick (the reasoner also outputs that sum, then the action
head follows it).

Common random numbers: one random.Random(f"{regime}/{seed}") stream
per (regime, seed) draws the in-domain and OOD equation sets and the
card decks first, in a fixed order, before any arm is evaluated; all
arms share the same scenes.

Regimes and parameters were written before the first run.  Declared
expectations are printed as they come, without tuning.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
A_MIN = 1
A_MAX = 9
B_MIN = 1
B_MAX = 9
N_ID_EQ = 12
N_OOD_EQ = 20
N_CARDS = 5
N_ARITH = 40
UNTRAINED_Y = -100.0
ALT_UNTRAINED_Y = None  # alternative: use the first addend; printed, not adopted
HAND_A = 7
HAND_B = 5

ARMS = ("A_overwrite", "B_two_stage", "C_stage2_only")
METRICS = ("pick_acc", "reason_then_pick")
PAIRS = (
    ("B_two_stage", "A_overwrite"),
    ("C_stage2_only", "B_two_stage"),
    ("C_stage2_only", "A_overwrite"),
)

REGIMES = ("in_domain", "ood")
DECLARED = {
    "in_domain": "A and B may near-tie on pick_acc - keep",
    "ood": "B consistently higher reason_then_pick and pick_acc than A - keep; C loses on OOD vs B - keep",
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


def all_pairs():
    return [(a, b) for a in range(A_MIN, A_MAX + 1) for b in range(B_MIN, B_MAX + 1)]


def build_scenes(seed):
    """Shared in-domain and OOD boards for one seed; used by both regimes."""
    rng = random.Random(f"shared/{seed}")
    pairs = list(all_pairs())
    rng.shuffle(pairs)
    id_eq = pairs[:N_ID_EQ]
    ood_eq = pairs[N_ID_EQ:N_ID_EQ + N_OOD_EQ]
    possible = list(range(A_MIN + B_MIN, A_MAX + B_MAX + 1))

    def decks(eqs):
        out = []
        for a, b in eqs:
            total = a + b
            others = [c for c in possible if c != total]
            rng.shuffle(others)
            cards = [total] + others[: N_CARDS - 1]
            rng.shuffle(cards)
            out.append((a, b, total, tuple(cards)))
        return out

    return {
        "id_eq": id_eq,
        "ood_eq": ood_eq,
        "id_scenes": decks(id_eq),
        "ood_scenes": decks(ood_eq),
        "train_mean": sum(a + b for a, b in id_eq) / len(id_eq),
        "id_lookup": {(a, b): a + b for a, b in id_eq},
    }


def reason_A(a, b, world):
    if (a, b) in world["id_lookup"]:
        return float(world["id_lookup"][(a, b)])
    return float(world["train_mean"])


def reason_B(a, b, world):
    return float(a + b)


def reason_C(a, b, world, untrained=UNTRAINED_Y):
    if untrained is None:
        return float(a)
    return float(untrained)


def pick_card(yhat, cards, lookup, a, b, allow_memory):
    if allow_memory and (a, b) in lookup:
        target = lookup[(a, b)]
        # memorised in-domain pick: choose the card that equals the stored sum
        for c in cards:
            if c == target:
                return c
    return min(cards, key=lambda c: (abs(c - yhat), c))


def evaluate(arm, scenes, world, untrained=UNTRAINED_Y):
    if arm == "A_overwrite":
        reason = reason_A
        memory = False  # follows the overwritten reasoner
    elif arm == "B_two_stage":
        reason = reason_B
        memory = False
    else:
        def reason(a, b, w, _u=untrained):
            return reason_C(a, b, w, _u)
        memory = True  # stage-2-only may memorise in-domain picks
    n = len(scenes)
    pick_ok = 0
    both_ok = 0
    reason_ok = 0
    for a, b, total, cards in scenes:
        yhat = reason(a, b, world)
        chosen = pick_card(yhat, cards, world["id_lookup"], a, b, memory)
        if chosen == total:
            pick_ok += 1
        if yhat == float(total):
            reason_ok += 1
        if yhat == float(total) and chosen == total:
            both_ok += 1
    return {
        "pick_acc": pick_ok / n,
        "reason_then_pick": both_ok / n,
        "reason_acc": reason_ok / n,
    }


def run_regime(regime, seed, untrained=UNTRAINED_Y):
    world = build_scenes(seed)
    # The regime stream is opened after the shared scene draw so the
    # documented CRN name is used; it does not redraw the boards.
    random.Random(f"{regime}/{seed}")
    scenes = world["id_scenes"] if regime == "in_domain" else world["ood_scenes"]
    out = {}
    for arm in ARMS:
        out[arm] = evaluate(arm, scenes, world, untrained=untrained)
    return out, world


def main():
    n_pairs = (A_MAX - A_MIN + 1) * (B_MAX - B_MIN + 1)
    print("ChatVLA-2-style reasoning-following toy: board equation and number cards (synthetic; not Qwen2-VL, not DexVLA, not the paper's 52-equation lab)")
    print("paper math-matching scores (43/52 and the rest) 以论文为准; GPU / real whiteboard / paper-task runs: 本页未运行")
    print(
        f"seeds={len(SEEDS)} a_min={A_MIN} a_max={A_MAX} b_min={B_MIN} b_max={B_MAX} "
        f"n_id_eq={N_ID_EQ} n_ood_eq={N_OOD_EQ} n_cards={N_CARDS} n_arith={N_ARITH} "
        f"n_add_pairs={n_pairs} untrained_y={num(UNTRAINED_Y)} "
        f"hand_a={HAND_A} hand_b={HAND_B} (declared)"
    )
    print("Regimes and parameters were written before the first run")
    print(f"hand_calc {HAND_A}+{HAND_B} = {num(float(HAND_A + HAND_B))}")
    print(f"hand_calc untrained_y = {num(UNTRAINED_Y)}")
    print(f"hand_calc n_add_pairs = {n_pairs}")
    for r in REGIMES:
        print(f"declared {r}: {DECLARED[r]}")

    store = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_store = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    train_means = []
    for seed in SEEDS:
        for regime in REGIMES:
            out, world = run_regime(regime, seed)
            if regime == "in_domain":
                train_means.append(world["train_mean"])
            for arm in ARMS:
                for m in METRICS:
                    store[regime][arm][m].append(out[arm][m])
            alt_out, _ = run_regime(regime, seed, untrained=ALT_UNTRAINED_Y)
            for arm in ARMS:
                for m in METRICS:
                    alt_store[regime][arm][m].append(alt_out[arm][m])

    print(f"hand_calc mean of in-domain train_mean over seeds = {num(sum(train_means) / len(train_means))}")

    for regime in REGIMES:
        print(f"regime {regime}")
        for arm in ARMS:
            for m in METRICS:
                xs = store[regime][arm][m]
                mu, sd = mean_sd(xs)
                print(f"  {arm} {m}: {num(mu)}+-{num(sd)}")
        for left, right in PAIRS:
            for m in METRICS:
                v = verdict(store[regime][left][m], store[regime][right][m])
                print(f"  paired {left[0]}-{right[0]} {m}: {v}")

    print("alternative untrained_y = first addend (printed, not adopted)")
    for regime in REGIMES:
        print(f"  alt regime {regime}")
        for left, right in PAIRS:
            for m in METRICS:
                v = verdict(alt_store[regime][left][m], alt_store[regime][right][m])
                print(f"    (paired {left[0]}-{right[0]} {m}): {v}")


if __name__ == "__main__":
    main()
