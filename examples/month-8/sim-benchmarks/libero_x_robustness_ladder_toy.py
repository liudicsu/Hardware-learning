#!/usr/bin/env python3
"""Stdlib stand-in of a five-level cumulative robustness ladder.

Stdlib only. Not lerobot-eval, not a GPU LIBERO-X run, and not a redo of
the five-suite LIBERO fake-score table, SimplerEnv, or imagination
ranking already on this page. Real GPU lerobot-eval / LIBERO-X:
本页未运行.

LIBERO-X (Wang, Zhang, Liu, et al., arXiv 2602.06556 v1) is a
manipulation benchmark whose point is that a single suite success rate
can hide failure under cumulative distribution shifts. Paper figures
(2,520 demonstrations, 600 tasks, 100 scenes, and the 9.8 % drop in
average success rate from Level 1 to Level 2 in Figure 5) are
以论文为准: the 9.8 % figure is a drop, not a suite mean, not the
L1-to-L5 decline, and not a toy output.

Shared base scenes, object slots and instructions, and a shared policy
stand-in, are generated once per (regime, seed) and then read by every
arm (common random numbers).

Arms:
  A_unperturbed  in-distribution / unperturbed suite mean only
  B_ladder       five-level cumulative ladder (per-level success and
                 the drop from L1 to L5)
  C_leak         lose arm: a train-test leak that reuses the L1
                 outcomes and reports them as if they were L5

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean|
and sd both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap
(small if |m| < 20 % of the smaller arm mean, else clear), with a
sign count. ROUND_HALF_UP output.

LIBERO-X paper: body read; 以论文为准.
"""
from __future__ import annotations

import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared stand-in parameters. Written before the first run.
# These are toy penalties, not paper success rates.
N_EP = 40
N_SCENES = 8
N_SLOTS = 4
P_BASE = 0.8000
# Cumulative penalties added as each level is stacked on the previous.
# L1 is a small local jitter; later levels are larger stacked shifts.
PENALTY = {
    1: 0.0200,  # local spatial perturbation (minor jitter)
    2: 0.1200,  # extended spatial perturbation
    3: 0.1800,  # scene topology reconstruction
    4: 0.1600,  # visual attribute variation (unseen / confounding)
    5: 0.1400,  # semantic-equivalent instruction reformulation
}
# Unstructured harsh alternative (same seeds, not adopted).
HARSH_PENALTY = 0.7000

LEVELS = (1, 2, 3, 4, 5)
ARMS = ("A_unperturbed", "B_ladder", "C_leak")
# Official paired metrics: unperturbed mean vs ladder at the regime's
# focus levels, plus C's leaked "L5" report against B's true L5.
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

REGIMES = {
    "l1_jitter": (
        "L1-like minor jitter; A and B may near-tie on success - keep"
    ),
    "cumulative_shift": (
        "cumulative L3-L5 shifts; B consistent lower success than A's "
        "unperturbed mean - keep"
    ),
    "leak_misreport": (
        "C mis-reports by reusing L1 outcomes as if they were L5 - keep"
    ),
}


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
    elif abs(m) < SMALL_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def rng_for(*parts):
    material = "libero-x-ladder|" + "|".join(str(p) for p in parts)
    return random.Random(material)


def clip01(p):
    return 0.0 if p < 0.0 else 1.0 if p > 1.0 else p


def cumulative_penalty(level, penalty=PENALTY):
    return sum(penalty[k] for k in LEVELS if k <= level)


def shared_bank(regime, seed, n_ep=N_EP):
    """Shared scenes, slots, instructions, competence and uniforms (CRN)."""
    rng = rng_for(regime, seed, "bank")
    episodes = []
    for i in range(n_ep):
        scene = i % N_SCENES
        slot = (i * 3) % N_SLOTS
        instruction = (i * 5 + scene) % 16
        competence = rng.uniform(-0.0400, 0.0400)
        u = rng.random()
        episodes.append(
            {
                "scene": scene,
                "slot": slot,
                "instruction": instruction,
                "competence": competence,
                "u": u,
            }
        )
    return episodes


def success_prob(episode, stacked_penalty):
    return clip01(P_BASE + episode["competence"] - stacked_penalty)


def roll_success(episode, stacked_penalty):
    return 1 if episode["u"] < success_prob(episode, stacked_penalty) else 0


def evaluate(regime, seed, penalty=None, harsh=None, n_ep=N_EP):
    if penalty is None:
        penalty = PENALTY
    episodes = shared_bank(regime, seed, n_ep=n_ep)
    # A: unperturbed / in-distribution, one suite mean on the shared bank.
    a_hits = [roll_success(ep, 0.0) for ep in episodes]
    a_mean = sum(a_hits) / n_ep
    # B: cumulative ladder, per level, same bank and same uniforms.
    b_level = {}
    b_hits = {}
    for lv in LEVELS:
        hits = [roll_success(ep, cumulative_penalty(lv, penalty)) for ep in episodes]
        b_hits[lv] = hits
        b_level[lv] = sum(hits) / n_ep
    b_drop_l1_l5 = b_level[1] - b_level[5]
    # C official: leak L1 outcomes and report them as L5.
    c_l5_leak = b_level[1]
    # Optional unstructured harsh report (used only in the named alternative).
    if harsh is None:
        c_harsh = None
    else:
        c_harsh = sum(roll_success(ep, harsh) for ep in episodes) / n_ep
    return {
        "n_ep": n_ep,
        "A_unperturbed": a_mean,
        "B_level": b_level,
        "B_drop_l1_l5": b_drop_l1_l5,
        "C_leak_l5": c_l5_leak,
        "C_harsh": c_harsh,
        "penalty": dict(penalty),
    }


def official_rows(name, penalty=None, harsh=None, n_ep=N_EP):
    return [evaluate(name, seed, penalty=penalty, harsh=harsh, n_ep=n_ep) for seed in SEEDS]


def print_regime(title, rows, focus):
    print(f"regime {title}  (mean+-sd over seeds)")
    print(f"  n_ep={rows[0]['n_ep']} n_scenes={N_SCENES} n_slots={N_SLOTS}")
    a = [r["A_unperturbed"] for r in rows]
    print(f"  A_unperturbed success {num(mean_sd(a)[0])}+-{num(mean_sd(a)[1])}")
    b_levels = {}
    for lv in LEVELS:
        xs = [r["B_level"][lv] for r in rows]
        b_levels[lv] = xs
        print(f"  B_ladder L{lv} success {num(mean_sd(xs)[0])}+-{num(mean_sd(xs)[1])}")
    drop = [r["B_drop_l1_l5"] for r in rows]
    print(f"  B_ladder drop_L1_to_L5 {num(mean_sd(drop)[0])}+-{num(mean_sd(drop)[1])}")
    c = [r["C_leak_l5"] for r in rows]
    print(f"  C_leak reported_as_L5 {num(mean_sd(c)[0])}+-{num(mean_sd(c)[1])}")
    if rows[0]["C_harsh"] is not None:
        h = [r["C_harsh"] for r in rows]
        print(f"  C_harsh unstructured success {num(mean_sd(h)[0])}+-{num(mean_sd(h)[1])}")

    # Focused official pairs for this regime, plus the leak comparison.
    if focus == "l1":
        print(f"  paired B-A L1_success: {verdict(b_levels[1], a)}")
        print(f"  paired C-B leaked_L5_minus_true_L5: {verdict(c, b_levels[5])}")
        print(f"  paired C-A leaked_L5_minus_unperturbed: {verdict(c, a)}")
    elif focus == "cumulative":
        for lv in (3, 4, 5):
            print(f"  paired B-A L{lv}_success: {verdict(b_levels[lv], a)}")
        print(f"  paired C-B leaked_L5_minus_true_L5: {verdict(c, b_levels[5])}")
        print(f"  paired C-A leaked_L5_minus_unperturbed: {verdict(c, a)}")
    else:
        # leak_misreport: C vs true L5 and vs A; also show L1 near A for context
        print(f"  paired B-A L1_success: {verdict(b_levels[1], a)}")
        print(f"  paired B-A L5_success: {verdict(b_levels[5], a)}")
        print(f"  paired C-B leaked_L5_minus_true_L5: {verdict(c, b_levels[5])}")
        print(f"  paired C-A leaked_L5_minus_unperturbed: {verdict(c, a)}")


def main():
    print("Stdlib stand-in of a five-level cumulative robustness ladder; not a LIBERO-X eval")
    print(
        f"declared P_BASE={num(P_BASE)} N_EP={N_EP} N_SCENES={N_SCENES} "
        f"N_SLOTS={N_SLOTS} SMALL_FRAC={num(SMALL_FRAC)} "
        f"seeds={','.join(str(s) for s in SEEDS)}"
    )
    print(
        "declared arms: A_unperturbed in-distribution suite mean; "
        "B_ladder cumulative L1-L5; "
        "C_leak reuses L1 outcomes as if they were L5"
    )
    print(
        "declared penalties L1={p1} L2={p2} L3={p3} L4={p4} L5={p5}".format(
            p1=num(PENALTY[1]),
            p2=num(PENALTY[2]),
            p3=num(PENALTY[3]),
            p4=num(PENALTY[4]),
            p5=num(PENALTY[5]),
        )
    )
    for lv in LEVELS:
        print(f"hand_calc cumulative_penalty L{lv} = {num(cumulative_penalty(lv))}")
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    # Paper figures, labelled as such, not toy outputs.
    print("paper_figure demonstrations = 2,520 (以论文为准, not a toy output)")
    print("paper_figure tasks = 600 (以论文为准, not a toy output)")
    print("paper_figure scenes = 100 (以论文为准, not a toy output)")
    print("paper_figure L1_to_L2_average_success_drop_pct = 9.8 (Figure 5; a drop, not a suite mean, not L1-to-L5, 以论文为准, not a toy output)")
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: scenes, slots, instructions, competence and uniforms are shared across arms at each regime and seed")
    print("Assumptions: stdlib policy stand-in, not lerobot-eval, not LIBERO-Plus, not the five-suite table")
    print("Paper dataset sizes and the 9.8 % L1 to L2 drop 以论文为准")
    print("GPU lerobot-eval / real LIBERO-X: 本页未运行")
    print("declared l1_jitter: A and B may near-tie on success - keep")
    print("declared cumulative_shift: B consistent lower success than A's unperturbed mean - keep")
    print("declared leak_misreport: C mis-reports (leak) - keep")
    print(f"declared expectation l1_jitter: {REGIMES['l1_jitter']}")
    print_regime("l1_jitter", official_rows("l1_jitter"), "l1")
    print(f"declared expectation cumulative_shift: {REGIMES['cumulative_shift']}")
    print_regime("cumulative_shift", official_rows("cumulative_shift"), "cumulative")
    print(f"declared expectation leak_misreport: {REGIMES['leak_misreport']}")
    print_regime("leak_misreport", official_rows("leak_misreport"), "leak")

    print("alternative same seeds HARSH_PENALTY=0.7000 unstructured (not adopted)")
    print(f"hand_calc harsh residual success floor if competence=0 = {num(clip01(P_BASE - HARSH_PENALTY))}")
    rows = official_rows("cumulative_shift", harsh=HARSH_PENALTY)
    print_regime("cumulative_shift alt_harsh=0.7000", rows, "cumulative")

    print("No GPU eval was started")
    print("No winner is universal: L1-like jitter can near-tie; the hidden drop is the cumulative ladder, not a retune toward the unperturbed mean")


if __name__ == "__main__":
    main()
