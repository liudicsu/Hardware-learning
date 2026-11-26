#!/usr/bin/env python3
"""Synthetic Timer1 input-capture vs software edge-poll stand-in.

Stdlib only. A labeled stand-in of the opened ATmega328P 7810D section 15.6
Input Capture Unit contract, not a port of the datasheet C examples and not
a flash or logic-analyzer run.

Arms:
  A_poll   software rising-edge polling at a declared loop period. The
           timestamp is the poll instant when a low-to-high sample is
           first seen, so a short pulse that stays high only between
           polls can be missed.
  B_icr    official-contract stand-in: on a qualifying rising edge
           (ICES=1), copy TCNT into a one-deep ICR at that same timer
           tick. ICNC is declared off, so the official four system-clock
           noise-canceler delay is not added. A second qualifying edge
           before ICR is read overwrites ICR.
  C_ices   pre-declared lose mode: ICES swapped (falling edge). One
           mode only, declared before the first run. Kept.

Common random numbers: seeds 0-4. Every regime is deterministic
(fixed edge schedules; the five seeds repeat the same figures).

Regimes (declared before the first run):
  sparse_edges    rising period much longer than the poll interval
                  -> A vs B exact or official near-tie
  short_pulses    pulse width and period shorter than the poll
                  -> B clearly better than A (missed software samples)
  icr_overwrite   second rising edge before ICR is read
                  -> official overwrite; late-read and keep-first
                     behaviour disclosed and kept
  wrong_ices      C uses falling-edge select on the sparse schedule
                  -> C loses on the first-capture stamp

ATmega328P 7810D section 15.6 以文档为准. Official AVR flash / logic
analyzer: 本页未运行.
"""
from __future__ import annotations

import math

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
CLEAR_FRAC = 0.2000  # small-vs-clear factor; printed before the first official run
F_CLK_HZ = 16_000_000  # lesson-declared, matching this page's Timer0 64 / 16 MHz = 4 us arithmetic
N_PRESCALER = 8  # official Table 15-6 clkI/O/8; N in {1, 8, 64, 256, 1024}
TICK_S = N_PRESCALER / F_CLK_HZ  # 0.5000 us, labelled 手算
ICNC_ON = False
ICNC_DELAY_CLK = 4  # official delay when ICNC is on; not applied
ICES_RISING = 1  # official ICES1=1, rising (positive) edge
ICES_FALLING = 0  # C's pre-declared lose mode: ICES swapped
POLL_PERIOD_TICKS = 20
POLL_PERIOD_ALT_TICKS = 1  # named alternative, not adopted
SPARSE_RISES = (200, 1000, 1800)
SPARSE_WIDTH_TICKS = 40
SHORT_FIRST_RISE = 1
SHORT_PERIOD_TICKS = 8
SHORT_WIDTH_TICKS = 3
SHORT_N_PULSES = 16
OVERWRITE_RISES = (100, 108)
OVERWRITE_WIDTH_TICKS = 4
LATE_READ_TICKS = 120
ARMS = ("A_poll", "B_icr", "C_ices")
REGIMES = ("sparse_edges", "short_pulses", "icr_overwrite", "wrong_ices")


def tick_to_us(ticks: float) -> float:
    return ticks * TICK_S * 1e6


def pin_high(t: int, rises: tuple[int, ...], width: int) -> bool:
    return any(r <= t < r + width for r in rises)


def falling_edges(rises: tuple[int, ...], width: int) -> tuple[int, ...]:
    return tuple(r + width for r in rises)


def qualifying_edges(ices: int, rises: tuple[int, ...], width: int) -> tuple[int, ...]:
    return rises if ices == ICES_RISING else falling_edges(rises, width)


def poll_captures(rises: tuple[int, ...], width: int, poll: int, t_end: int) -> list[int]:
    """Software rising-edge poll: timestamp is the poll instant."""
    found: list[int] = []
    prev = 0
    t = 0
    while t <= t_end:
        level = 1 if pin_high(t, rises, width) else 0
        if prev == 0 and level == 1:
            found.append(t)
        prev = level
        t += poll
    return found


def icr_captures(ices: int, rises: tuple[int, ...], width: int, read_immediately: bool) -> list[int]:
    """Official one-deep ICR. If read_immediately, each capture is saved before the next edge."""
    edges = qualifying_edges(ices, rises, width)
    if read_immediately:
        return list(edges)
    if not edges:
        return []
    # Unread: each new qualifying edge overwrites ICR; only the last remains.
    return [edges[-1]]


def first_kept(ices: int, rises: tuple[int, ...], width: int) -> int | None:
    """Disclosed keep-first behaviour: ignore the official overwrite."""
    edges = qualifying_edges(ices, rises, width)
    return edges[0] if edges else None


def mean_period(captures: list[int]) -> float | None:
    if len(captures) < 2:
        return None
    gaps = [b - a for a, b in zip(captures, captures[1:])]
    return sum(gaps) / len(gaps)


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    if len(xs) == 1:
        return mu, 0.0
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
    if x != 0.0 and abs(x) < 5e-5:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs: list[float], m: float) -> str:
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def verdict(xa: list[float], xb: list[float]) -> str:
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{num(m)}+-{num(s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < CLEAR_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{num(m)}+-{num(s)}: {label}; {sign_note(diffs, m)}"


def seed_repeat(value: float) -> list[float]:
    return [value] * len(SEEDS)


def print_pair(label: str, xa: list[float], xb: list[float], unit: str) -> None:
    print(f"  paired {label}: {verdict(xa, xb)} {unit}".rstrip())


def run_sparse(poll: int) -> dict[str, list[int]]:
    t_end = SPARSE_RISES[-1] + SPARSE_WIDTH_TICKS + poll
    return {
        "A_poll": poll_captures(SPARSE_RISES, SPARSE_WIDTH_TICKS, poll, t_end),
        "B_icr": icr_captures(ICES_RISING, SPARSE_RISES, SPARSE_WIDTH_TICKS, True),
        "C_ices": icr_captures(ICES_FALLING, SPARSE_RISES, SPARSE_WIDTH_TICKS, True),
    }


def run_short(poll: int) -> dict[str, list[int]]:
    rises = tuple(SHORT_FIRST_RISE + i * SHORT_PERIOD_TICKS for i in range(SHORT_N_PULSES))
    t_end = rises[-1] + SHORT_WIDTH_TICKS + poll
    return {
        "A_poll": poll_captures(rises, SHORT_WIDTH_TICKS, poll, t_end),
        "B_icr": icr_captures(ICES_RISING, rises, SHORT_WIDTH_TICKS, True),
        "C_ices": icr_captures(ICES_FALLING, rises, SHORT_WIDTH_TICKS, True),
    }


def run_overwrite() -> dict[str, object]:
    t_end = LATE_READ_TICKS
    a = poll_captures(OVERWRITE_RISES, OVERWRITE_WIDTH_TICKS, POLL_PERIOD_TICKS, t_end)
    official_last = icr_captures(ICES_RISING, OVERWRITE_RISES, OVERWRITE_WIDTH_TICKS, False)
    kept = first_kept(ICES_RISING, OVERWRITE_RISES, OVERWRITE_WIDTH_TICKS)
    c = icr_captures(ICES_FALLING, OVERWRITE_RISES, OVERWRITE_WIDTH_TICKS, False)
    return {
        "A_poll": a,
        "B_icr_late": official_last,
        "keep_first": kept,
        "C_ices_late": c,
        "rising_edges": OVERWRITE_RISES,
    }


def print_arm_stats(name: str, captures: list[int], metric: str) -> tuple[list[float], list[float]]:
    n = seed_repeat(float(len(captures)))
    first = seed_repeat(float(captures[0]) if captures else math.nan)
    period = mean_period(captures)
    print(f"  {name} n_capt {num(n[0])}+-{num(0.0)}")
    if captures:
        print(f"  {name} first_ticks {num(first[0])}+-{num(0.0)} first_us {num(tick_to_us(first[0]))}+-{num(0.0)} (hand_calc)")
    else:
        print(f"  {name} first_ticks none first_us none")
    if period is not None:
        per = seed_repeat(period)
        print(
            f"  {name} period_ticks {num(per[0])}+-{num(0.0)} period_us {num(tick_to_us(period))}+-{num(0.0)} (hand_calc)"
        )
    else:
        per = []
        print(f"  {name} period_ticks none period_us none")
    return n, (first if captures else []), per


def main() -> None:
    sparse = run_sparse(POLL_PERIOD_TICKS)
    short = run_short(POLL_PERIOD_TICKS)
    short_alt = run_short(POLL_PERIOD_ALT_TICKS)
    overw = run_overwrite()

    hc_tick_us = TICK_S * 1e6
    hc_icnc_us = ICNC_DELAY_CLK / F_CLK_HZ * 1e6
    hc_poll_us = tick_to_us(POLL_PERIOD_TICKS)
    hc_sparse_period_ticks = float(SPARSE_RISES[1] - SPARSE_RISES[0])
    hc_sparse_first_a = float(SPARSE_RISES[0])
    hc_sparse_first_c = float(SPARSE_RISES[0] + SPARSE_WIDTH_TICKS)
    hc_short_n_b = float(SHORT_N_PULSES)
    hc_short_n_a = 0.0
    hc_overwrite_b = float(OVERWRITE_RISES[1])
    hc_keep_first = float(OVERWRITE_RISES[0])
    hc_overwrite_a = float(OVERWRITE_RISES[0])  # poll lands on the first rising
    hc_freq_sparse = 1.0 / (hc_sparse_period_ticks * TICK_S)

    print(
        "Synthetic Timer1 input-capture vs software edge-poll toy; "
        "stdlib stand-in only; not a flash or logic-analyzer run"
    )
    print(
        f"f_clk={F_CLK_HZ}Hz N={N_PRESCALER} tick_us={hc_tick_us:.4f} "
        f"(hand_calc N/f_clk) ICNC={int(ICNC_ON)} icnc_delay_clk={ICNC_DELAY_CLK} "
        f"icnc_delay_us={hc_icnc_us:.4f} (hand_calc, not applied)"
    )
    print(
        f"ICES_B={ICES_RISING} ICES_C={ICES_FALLING} (pre-declared C lose mode: wrong ICES only) "
        f"poll_ticks={POLL_PERIOD_TICKS} poll_us={hc_poll_us:.4f} (hand_calc) "
        f"seeds={len(SEEDS)} clear_frac={CLEAR_FRAC:.4f} "
        f"hand_calc work_plan 30+25+50+40+35=180"
    )
    print(
        "no integration step: exact integer timer ticks; SI period and frequency are hand_calc "
        "from declared tick and delta ICR, not a closed-form printed in section 15.6"
    )
    print(
        f"hand_calc sparse period_ticks={hc_sparse_period_ticks:.10f} "
        f"period_us={tick_to_us(hc_sparse_period_ticks):.10f} "
        f"freq_hz={hc_freq_sparse:.10f} first_A=B={hc_sparse_first_a:.10f} "
        f"first_C={hc_sparse_first_c:.10f}"
    )
    print(
        f"hand_calc short n_A={hc_short_n_a:.10f} n_B={hc_short_n_b:.10f} "
        f"period_ticks={float(SHORT_PERIOD_TICKS):.10f} "
        f"period_us={tick_to_us(SHORT_PERIOD_TICKS):.10f} "
        f"first_rise={SHORT_FIRST_RISE} width={SHORT_WIDTH_TICKS} "
        f"poll_ticks={POLL_PERIOD_TICKS}"
    )
    print(
        f"hand_calc overwrite late_read_ticks={LATE_READ_TICKS} "
        f"official_ICR_B={hc_overwrite_b:.10f} keep_first={hc_keep_first:.10f} "
        f"A_first={hc_overwrite_a:.10f} edges={OVERWRITE_RISES[0]},{OVERWRITE_RISES[1]}"
    )

    # --- sparse_edges ---
    print("sparse_edges (rising period much longer than the declared poll interval)")
    n_map: dict[str, list[float]] = {}
    first_map: dict[str, list[float]] = {}
    per_map: dict[str, list[float]] = {}
    for arm in ARMS:
        n, first, per = print_arm_stats(arm, sparse[arm], "sparse")
        n_map[arm] = n
        if first:
            first_map[arm] = first
        if per:
            per_map[arm] = per
    print_pair("A-B period_ticks", per_map["A_poll"], per_map["B_icr"], "")
    print_pair("A-B first_ticks", first_map["A_poll"], first_map["B_icr"], "")
    print(
        f"  residual_step-closed_A_first={sparse['A_poll'][0] - hc_sparse_first_a:.3e}ticks "
        f"residual_step-closed_B_first={sparse['B_icr'][0] - hc_sparse_first_a:.3e}ticks"
    )

    # --- short_pulses ---
    print("short_pulses (pulse width and period shorter than the declared poll; missed software samples)")
    n_map = {}
    first_map = {}
    per_map = {}
    for arm in ARMS:
        n, first, per = print_arm_stats(arm, short[arm], "short")
        n_map[arm] = n
        if first:
            first_map[arm] = first
        if per:
            per_map[arm] = per
    print_pair("A-B n_capt", n_map["A_poll"], n_map["B_icr"], "")
    print(
        f"  residual_step-closed_A_n={len(short['A_poll']) - hc_short_n_a:.3e} "
        f"residual_step-closed_B_n={len(short['B_icr']) - hc_short_n_b:.3e}"
    )

    # --- icr_overwrite ---
    print(
        "icr_overwrite (second rising edge before ICR is read; official overwrite; "
        "late-read and keep-first disclosed and kept)"
    )
    a_over = overw["A_poll"]
    b_late = overw["B_icr_late"]
    keep = overw["keep_first"]
    c_late = overw["C_ices_late"]
    print(f"  A_poll n_capt {num(float(len(a_over)))}+-{num(0.0)} first_ticks {num(float(a_over[0]))}+-{num(0.0)}")
    print(f"  B_icr late_read ICR_ticks {num(float(b_late[0]))}+-{num(0.0)} (official overwrite, last edge)")
    print(f"  keep_first ICR_ticks {num(float(keep))}+-{num(0.0)} (disclosed, not the official capture)")
    print(f"  C_ices late_read ICR_ticks {num(float(c_late[0]))}+-{num(0.0)}")
    print_pair("B-keep_first ICR_ticks", seed_repeat(float(b_late[0])), seed_repeat(float(keep)), "")
    print_pair("A-B first_vs_official_ICR_ticks", seed_repeat(float(a_over[0])), seed_repeat(float(b_late[0])), "")
    print(
        f"  residual_step-closed_B_ICR={b_late[0] - hc_overwrite_b:.3e}ticks "
        f"residual_step-closed_keep={keep - hc_keep_first:.3e}ticks "
        f"residual_step-closed_A_first={a_over[0] - hc_overwrite_a:.3e}ticks"
    )

    # --- wrong_ices ---
    print("wrong_ices (C uses falling-edge select on the sparse schedule; pre-declared lose, kept)")
    first_map = {}
    per_map = {}
    for arm in ARMS:
        n, first, per = print_arm_stats(arm, sparse[arm], "wrong")
        if first:
            first_map[arm] = first
        if per:
            per_map[arm] = per
    print_pair("C-B first_ticks", first_map["C_ices"], first_map["B_icr"], "")
    print_pair("A-B first_ticks", first_map["A_poll"], first_map["B_icr"], "")
    print(
        "  C falling-to-falling period still matches the official rising period when pulse width is constant; "
        "C loses on the first-capture stamp"
    )
    print(
        f"  residual_step-closed_C_first={sparse['C_ices'][0] - hc_sparse_first_c:.3e}ticks"
    )

    a_alt = short_alt["A_poll"]
    b_alt = short_alt["B_icr"]
    print(
        f"alternative short_pulses poll_ticks={POLL_PERIOD_ALT_TICKS} (not adopted) "
        f"n_A={len(a_alt):.10f} n_B={len(b_alt):.10f} "
        f"first_A={a_alt[0] if a_alt else 'none'} first_B={b_alt[0]}"
    )
    print("  paired A-B n_capt: " + verdict(seed_repeat(float(len(a_alt))), seed_repeat(float(len(b_alt)))))
    print(
        "No winner declared: on sparse edges A and B tie on period and first stamp; "
        "on short pulses B captures the declared rising train and A misses every pulse; "
        "a second unread event overwrites ICR with the later stamp; "
        "wrong ICES loses on the first-capture stamp"
    )
    print("Official AVR flash / logic analyzer: 本页未运行; ATmega328P 7810D section 15.6 以文档为准")


if __name__ == "__main__":
    main()
