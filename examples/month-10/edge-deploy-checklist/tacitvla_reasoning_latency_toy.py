#!/usr/bin/env python3
"""Stdlib stand-in of reasoning latency vs ledger memory for a VLA.

Stdlib only. Not a GPU RoboMME / RMBench / LIBERO-Plus / PhysicalAI-AV
run, and not the int8 budget, VLA-Adapter, RTC, CoT-VLA, ChatVLA-2, or
ThinkAct already on nearby pages. GPU / RoboMME / PhysicalAI-AV:
本页未运行.

TacitVLA (Lu, You, Li, et al., arXiv 2610.17540 v1) is a reasoning VLA
whose action expert never attends to the reasoning it generates for the
current call. Reasoning supervision can still improve the backbone; on
long-horizon memory tasks the reasoning text can be generated during
action execution rather than before acting. Paper figures (up to 3.4x
lower latency than an explicit-reasoning counterpart, up to +17.1 %
success at a no-reasoning architecture's latency, RoboMME Counting
82.7 % vs 66.8 %, RMBench 77.5 % vs 56.5 %, LIBERO-Plus 72.9 %, and a
52.5 % PhysicalAI-AV public-split scene score) are 以论文为准 and are
not toy outputs.

Shared tasks, a shared backbone-quality stand-in, and a shared
reasoning-token cost are generated once per (regime, seed) and then
read by every arm (common random numbers).

Arms:
  A_explicit  action waits for and conditions on the current reasoning
  B_tacit     action does not attend to current r_t; on memory tasks,
              reasoning may be emitted during the execution window
  C_lose      no reasoning supervision (no ledger entry), or action
              that attends to truncated / stale / scrambled reasoning

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean|
and sd both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap
(small if |m| < 20 % of the smaller arm mean, else clear), with a
sign count. ROUND_HALF_UP output.

TacitVLA paper: body read; 以论文为准.
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
# Times are a latency stand-in, not paper milliseconds.
N_EP = 40
N_STEPS = 6
T_ACTION = 8.0000
T_REASON = 12.0000
WINDOW = 20.0000
P_SHORT = 0.8500
P_SHORT_NOSUP = 0.7000
TARGETS = (2, 3, 4, 5)
# C with no ledger always presses this many times (a fixed prior).
C_FIXED_PRESSES = 4
# Named alternative (same seeds, not adopted): a longer reasoning cost
# that no longer fits in the execution window.
ALT_T_REASON = 25.0000

ARMS = ("A_explicit", "B_tacit", "C_lose")

REGIMES = {
    "short_reactive": (
        "short-horizon / no memory; A and B may near-tie on success, "
        "with B consistent lower stand-in latency - keep"
    ),
    "memory_ledger": (
        "memory / ledger where C has no entry; B consistent higher "
        "success than C at comparable latency - keep"
    ),
    "stale_memory": (
        "hard memory cell; C or stale reasoning loses - keep"
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
    material = "tacitvla-latency|" + "|".join(str(p) for p in parts)
    return random.Random(material)


def shared_bank(regime, seed, n_ep=N_EP):
    """Shared tasks, uniforms, targets and stale draws (CRN)."""
    rng = rng_for(regime, seed, "bank")
    episodes = []
    for i in range(n_ep):
        target = TARGETS[i % len(TARGETS)]
        u_short = rng.random()
        # Stale / scrambled target: a different legal count, drawn once.
        stale_choices = [t for t in TARGETS if t != target]
        stale_target = stale_choices[rng.randrange(len(stale_choices))]
        episodes.append(
            {
                "target": target,
                "u_short": u_short,
                "stale_target": stale_target,
            }
        )
    return episodes


def latency(arm, t_reason=T_REASON, window=WINDOW):
    """Action-ready latency. Tacit generation adds no wait if it fits."""
    if arm == "A_explicit":
        return T_ACTION + t_reason
    if arm == "B_tacit":
        return T_ACTION
    # C_lose: no-supervision does not wait; stale-attending does wait.
    # The caller picks which C variant applies in that regime.
    raise AssertionError("C latency is regime-specific")


def short_success(episode, p):
    return 1 if episode["u_short"] < p else 0


def press_until(target, n_steps=N_STEPS):
    """Press once per step while the available count is below target."""
    count = 0
    for _ in range(n_steps):
        if count < target:
            count += 1
    return count


def evaluate(regime, seed, t_reason=T_REASON, window=WINDOW, n_ep=N_EP):
    episodes = shared_bank(regime, seed, n_ep=n_ep)
    a_hits, b_hits, c_hits = [], [], []
    a_lat, b_lat, c_lat = [], [], []
    tacit_fits = t_reason <= window
    if regime == "short_reactive":
        for ep in episodes:
            a_hits.append(short_success(ep, P_SHORT))
            b_hits.append(short_success(ep, P_SHORT))
            c_hits.append(short_success(ep, P_SHORT_NOSUP))
            a_lat.append(T_ACTION + t_reason)
            b_lat.append(T_ACTION)
            c_lat.append(T_ACTION)
    elif regime == "memory_ledger":
        # Target is in the shared instruction. A conditions on the
        # current running count; B uses only past ledger entries, which
        # is enough to decide whether another press is needed. C has
        # no ledger entry and always presses C_FIXED_PRESSES times.
        for ep in episodes:
            target = ep["target"]
            a_count = press_until(target)
            b_count = press_until(target)
            c_count = min(C_FIXED_PRESSES, N_STEPS)
            a_hits.append(1 if a_count == target else 0)
            b_hits.append(1 if b_count == target else 0)
            c_hits.append(1 if c_count == target else 0)
            a_lat.append(T_ACTION + t_reason)
            b_lat.append(T_ACTION if tacit_fits else T_ACTION + (t_reason - window))
            c_lat.append(T_ACTION)
    elif regime == "stale_memory":
        # Hard memory cell: the target is only in the reasoning / first
        # ledger entry, not in the instruction. A waits and reads it.
        # B writes the entry during the first execution window and then
        # uses that past ledger; with N_STEPS > max(TARGETS) it can
        # still reach the count (it does not attend to current r_t).
        # C attends to a stale / scrambled target and waits for it.
        for ep in episodes:
            target = ep["target"]
            stale = ep["stale_target"]
            a_count = press_until(target)
            b_count = press_until(target)
            c_count = press_until(stale)
            a_hits.append(1 if a_count == target else 0)
            b_hits.append(1 if b_count == target else 0)
            c_hits.append(1 if c_count == target else 0)
            a_lat.append(T_ACTION + t_reason)
            b_lat.append(T_ACTION if tacit_fits else T_ACTION + (t_reason - window))
            c_lat.append(T_ACTION + t_reason)
    else:
        raise AssertionError(regime)
    return {
        "n_ep": n_ep,
        "tacit_fits": tacit_fits,
        "A_success": sum(a_hits) / n_ep,
        "B_success": sum(b_hits) / n_ep,
        "C_success": sum(c_hits) / n_ep,
        "A_latency": sum(a_lat) / n_ep,
        "B_latency": sum(b_lat) / n_ep,
        "C_latency": sum(c_lat) / n_ep,
    }


def official_rows(name, t_reason=T_REASON, window=WINDOW, n_ep=N_EP):
    return [evaluate(name, seed, t_reason=t_reason, window=window, n_ep=n_ep) for seed in SEEDS]


def print_regime(title, rows):
    print(f"regime {title}  (mean+-sd over seeds)")
    print(f"  n_ep={rows[0]['n_ep']} n_steps={N_STEPS} tacit_fits={int(rows[0]['tacit_fits'])}")
    a_s = [r["A_success"] for r in rows]
    b_s = [r["B_success"] for r in rows]
    c_s = [r["C_success"] for r in rows]
    a_l = [r["A_latency"] for r in rows]
    b_l = [r["B_latency"] for r in rows]
    c_l = [r["C_latency"] for r in rows]
    print(f"  A_explicit success {num(mean_sd(a_s)[0])}+-{num(mean_sd(a_s)[1])}")
    print(f"  B_tacit success {num(mean_sd(b_s)[0])}+-{num(mean_sd(b_s)[1])}")
    print(f"  C_lose success {num(mean_sd(c_s)[0])}+-{num(mean_sd(c_s)[1])}")
    print(f"  A_explicit latency {num(mean_sd(a_l)[0])}+-{num(mean_sd(a_l)[1])}")
    print(f"  B_tacit latency {num(mean_sd(b_l)[0])}+-{num(mean_sd(b_l)[1])}")
    print(f"  C_lose latency {num(mean_sd(c_l)[0])}+-{num(mean_sd(c_l)[1])}")
    print(f"  paired B-A success: {verdict(b_s, a_s)}")
    print(f"  paired B-A latency: {verdict(b_l, a_l)}")
    print(f"  paired B-C success: {verdict(b_s, c_s)}")
    print(f"  paired B-C latency: {verdict(b_l, c_l)}")
    print(f"  paired C-A success: {verdict(c_s, a_s)}")
    print(f"  paired C-B success: {verdict(c_s, b_s)}")


def main():
    print("Stdlib stand-in of reasoning latency vs ledger memory; not a TacitVLA eval")
    print(
        f"declared T_ACTION={num(T_ACTION)} T_REASON={num(T_REASON)} "
        f"WINDOW={num(WINDOW)} N_EP={N_EP} N_STEPS={N_STEPS} "
        f"P_SHORT={num(P_SHORT)} P_SHORT_NOSUP={num(P_SHORT_NOSUP)} "
        f"C_FIXED_PRESSES={C_FIXED_PRESSES} SMALL_FRAC={num(SMALL_FRAC)} "
        f"seeds={','.join(str(s) for s in SEEDS)}"
    )
    print(
        "declared arms: A_explicit waits for and conditions on current reasoning; "
        "B_tacit does not attend to current r_t and may emit reasoning during the "
        "execution window on memory tasks; "
        "C_lose is no reasoning supervision or attends to stale / scrambled reasoning"
    )
    print(f"declared targets={','.join(str(t) for t in TARGETS)}")
    print(f"hand_calc T_ACTION + T_REASON = {num(T_ACTION + T_REASON)}")
    print(f"hand_calc WINDOW - T_REASON = {num(WINDOW - T_REASON)}")
    print(f"hand_calc explicit_over_tacit_latency = {num((T_ACTION + T_REASON) / T_ACTION)}")
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print("paper_figure explicit_latency_ratio_up_to = 3.4x (以论文为准, not a toy output)")
    print("paper_figure no_reasoning_latency_success_gain_pct = 17.1 (以论文为准, not a toy output)")
    print("paper_figure RoboMME_Counting_success_pct = 82.7 vs 66.8 (以论文为准, not a toy output)")
    print("paper_figure RMBench_success_pct = 77.5 vs 56.5 (以论文为准, not a toy output)")
    print("paper_figure LIBERO_Plus_success_pct = 72.9 (以论文为准, not a toy output)")
    print("paper_figure PhysicalAI_AV_public_split_scene_score_pct = 52.5 (以论文为准, not a toy output)")
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: tasks, uniforms, targets and stale draws "
        "are shared across arms at each regime and seed"
    )
    print(
        "Assumptions: stdlib latency and ledger stand-in, not RoboMME, "
        "not RMBench, not LIBERO-Plus, not PhysicalAI-AV, not VLA-Adapter, "
        "not RTC, not CoT-VLA, not ChatVLA-2, not ThinkAct"
    )
    print("Paper 3.4x / 17.1 % / 82.7 % / 77.5 % / 72.9 % / 52.5 % 以论文为准")
    print("GPU / RoboMME / PhysicalAI-AV: 本页未运行")
    print(f"declared short_reactive: {REGIMES['short_reactive']}")
    print_regime("short_reactive", official_rows("short_reactive"))
    print(f"declared expectation memory_ledger: {REGIMES['memory_ledger']}")
    print_regime("memory_ledger", official_rows("memory_ledger"))
    print(f"declared expectation stale_memory: {REGIMES['stale_memory']}")
    print_regime("stale_memory", official_rows("stale_memory"))

    print(f"alternative same seeds ALT_T_REASON={num(ALT_T_REASON)} (not adopted)")
    print(f"hand_calc ALT_T_REASON - WINDOW = {num(ALT_T_REASON - WINDOW)}")
    print_regime(
        "memory_ledger alt_t_reason=25.0000",
        official_rows("memory_ledger", t_reason=ALT_T_REASON),
    )

    print("No GPU eval was started")
    print(
        "No winner is universal: short-horizon success may near-tie, with tacit "
        "lower latency; do not retune so that tacit must beat explicit on success"
    )


if __name__ == "__main__":
    main()
