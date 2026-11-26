#!/usr/bin/env python3
"""Synthetic RMT symbol / encoder contract versus a bit-banged delay loop.

Stdlib only. A labeled stand-in of the opened ESP-IDF v5.3.2 ESP32-S3 Remote
Control Transceiver (RMT) driver contract. Official RMT driver / flash:
本页未运行. ESP-IDF RMT statements 以文档为准.

The opened guide (not invented here): the minimal data unit is the RMT symbol,
rmt_symbol_word_t; each symbol is two pairs of a 15-bit duration in RMT ticks
and a 1-bit level; RMT cannot transmit raw byte streams like SPI or I2C and
can only send rmt_symbol_word_t; software encoders convert user data, and a
bytes encoder is created by rmt_new_bytes_encoder() with bit0 / bit1 as
rmt_symbol_word_t and msb_first for bit endianness; resolution_hz sets the
internal tick counter used to calculate signal timing; the official example
uses resolution_hz = 1 * 1000 * 1000 with the comment "1 MHz tick resolution,
i.e., 1 tick = 1 us" (an example, not a chip-universal default); loop_count
is hardware-controlled, so a channel can generate many periodic sequences
with minimal CPU intervention; -1 loops until rmt_disable() and does not
generate trans-done; a positive number is a finite iteration count; non-zero
loop_count has a documented memory-block size limitation.

This toy does not invent a channel count, WS2812 / datasheet bit timings, or
datasheet currents, and it does not flash led_strip, ir_nec_transceiver,
dshot_esc, or onewire.

Arms:
  A_bitbang    software delay loop on the same symbol list. With no extra
               load the delays equal the declared tick times. With a declared
               ISR / background load the delays stretch.
  B_hardware   hardware-timed symbol list: durations stay the declared ticks
               at the named resolution_hz, including under that same load.
               A hardware loop_count restart has no software re-issue gap.
  C_wrong_hz   same ticks as B, but timed at a declared wrong resolution_hz.
               Pre-declared lose, kept.
  D_bit_swap   bytes encoder with bit0 and bit1 swapped. Pre-declared lose,
               kept.
  E_swap_lvl   same symbols as B with level0 / level1 swapped. Pre-declared
               lose, kept.

Common random numbers: seeds 0-4. Idle, wrong-resolution, bit-swap and
level-swap cells are deterministic (the five seeds repeat the same value).
ISR-loaded cells draw a shared Poisson ISR-count stream from each seed's
RNG, keyed on the declared hardware durations so every arm sees the same
load draws; B ignores the load, A applies it. No integration step: algebraic
tick-to-microsecond conversion and additive ISR counts, closed form.

Regimes (declared before the first run):
  idle                   single-shot short-pulse list, no ISR load
                         -> A vs B exact tie on total_us and on wrong_level_us
  isr_loaded_short       same list, declared ISR load
                         -> A stretches; B stays on the declared ticks;
                            B clearly better than A on total_us
                            (20 % of the smaller-arm mean)
  hw_loop_periodic       finite hardware loop_count versus software re-issue
                         of the same periodic sequence, under the same load
                         -> B stays at loop_count * period; A stretches;
                            B clearly better than A on total_us
  wrong_resolution       C vs B on the idle short-pulse list
                         -> C loses, kept
  bytes_bit_swap         D vs B on a declared bytes-encoder payload
                         -> D loses on wrong_level_us, kept
  swapped_levels         E vs B on the idle short-pulse list
                         -> E loses on wrong_level_us, kept
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
CLEAR_FRAC = 0.2000  # small-vs-clear factor; printed before the first official run

# Official example tick: resolution_hz = 1 * 1000 * 1000, "1 MHz tick resolution,
# i.e., 1 tick = 1 us". An example, not a chip-universal default.
RESOLUTION_HZ = 1 * 1000 * 1000
WRONG_RESOLUTION_HZ = 2 * 1000 * 1000  # declared wrong arm; 0.5 us/tick
# Lesson-declared short-pulse symbol (not a datasheet / WS2812 / NEC figure).
SHORT_D0 = 8
SHORT_L0 = 1
SHORT_D1 = 4
SHORT_L1 = 0
N_SHORT = 8
# Lesson-declared periodic symbol for the loop_count contrast.
PERIOD_D0 = 20
PERIOD_L0 = 1
PERIOD_D1 = 30
PERIOD_L1 = 0
LOOP_COUNT = 4  # official: a positive number is a finite iteration count
REISSUE_GAP_US = 8.0  # declared software re-arm gap between bit-bang repeats
# Lesson-declared bytes-encoder symbols and payload (not WS2812 bits).
BIT0_D0, BIT0_L0, BIT0_D1, BIT0_L1 = 4, 1, 12, 0
BIT1_D0, BIT1_L0, BIT1_D1, BIT1_L1 = 12, 1, 4, 0
PAYLOAD = 0xA5
MSB_FIRST = True
# Declared ISR stand-in (not a datasheet or a flashed driver).
LAMBDA_PER_US = 0.15
ISR_COST_US = 5.0
LAMBDA_ALT = 0.05  # disclosed alternative, same seeds, not adopted


@dataclass(frozen=True)
class Symbol:
    duration0: int
    level0: int
    duration1: int
    level1: int

    def swapped_levels(self) -> "Symbol":
        return Symbol(self.duration0, self.level1, self.duration1, self.level0)

    def pairs(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return (self.duration0, self.level0), (self.duration1, self.level1)


SHORT_SYM = Symbol(SHORT_D0, SHORT_L0, SHORT_D1, SHORT_L1)
PERIOD_SYM = Symbol(PERIOD_D0, PERIOD_L0, PERIOD_D1, PERIOD_L1)
BIT0 = Symbol(BIT0_D0, BIT0_L0, BIT0_D1, BIT0_L1)
BIT1 = Symbol(BIT1_D0, BIT1_L0, BIT1_D1, BIT1_L1)


def tick_us(resolution_hz: float) -> float:
    return 1_000_000.0 / resolution_hz


def poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0.0:
        return 0
    # Knuth's algorithm; lam is small for every declared delay.
    threshold = math.exp(-lam)
    count = 0
    product = 1.0
    while product > threshold:
        count += 1
        product *= rng.random()
    return count - 1


def encode_byte(payload: int, bit0: Symbol, bit1: Symbol, msb_first: bool) -> list[Symbol]:
    symbols: list[Symbol] = []
    for i in range(8):
        shift = 7 - i if msb_first else i
        bit = (payload >> shift) & 1
        symbols.append(bit1 if bit else bit0)
    return symbols


def decode_byte(symbols: list[Symbol], bit0: Symbol, bit1: Symbol, msb_first: bool) -> int:
    value = 0
    for i, sym in enumerate(symbols):
        if sym == bit1:
            bit = 1
        elif sym == bit0:
            bit = 0
        else:
            bit = -1
        if bit < 0:
            continue
        shift = 7 - i if msb_first else i
        value |= bit << shift
    return value


def hardware_total_us(symbols: list[Symbol], resolution_hz: float, loops: int = 1) -> float:
    one = sum((p[0] * tick_us(resolution_hz)) for sym in symbols for p in sym.pairs())
    return one * loops


def load_draws(symbols: list[Symbol], resolution_hz: float, loops: int, reissue_gaps: int, rng: random.Random, lam: float) -> list[int]:
    draws: list[int] = []
    for _ in range(loops):
        for sym in symbols:
            for ticks, _level in sym.pairs():
                declared = ticks * tick_us(resolution_hz)
                draws.append(poisson(rng, lam * declared))
        # One draw is reserved for each software re-issue gap (unused by hardware).
    for _ in range(reissue_gaps):
        draws.append(poisson(rng, lam * REISSUE_GAP_US))
    return draws


def play(
    symbols: list[Symbol],
    resolution_hz: float,
    *,
    hardware: bool,
    loops: int,
    reissue_gap_us: float,
    draws: list[int] | None,
    isr_cost: float,
) -> tuple[list[tuple[int, float]], float]:
    """Return (level, duration_us) segments and total_us."""
    segments: list[tuple[int, float]] = []
    total = 0.0
    cursor = 0
    draws = draws or []

    def consume(declared: float, stretch: bool) -> float:
        nonlocal cursor
        extra = 0.0
        if stretch and cursor < len(draws):
            extra = draws[cursor] * isr_cost
            cursor += 1
        return declared + extra

    for loop_i in range(loops):
        for sym in symbols:
            for ticks, level in sym.pairs():
                declared = ticks * tick_us(resolution_hz)
                dur = declared if hardware else consume(declared, True)
                segments.append((level, dur))
                total += dur
        if (not hardware) and loop_i < loops - 1 and reissue_gap_us > 0.0:
            gap = consume(reissue_gap_us, True)
            # A re-issue gap holds the last level; it is software time, not a
            # hardware symbol. Counted in total_us only.
            total += gap
    return segments, total


def wrong_level_us(actual: list[tuple[int, float]], ref: list[tuple[int, float]]) -> float:
    """Microseconds in [0, t_ref] where the actual level differs from the ref."""
    mismatch = 0.0
    i = j = 0
    t = 0.0
    a_end = 0.0
    r_end = 0.0
    a_level = ref[0][0] if ref else 0
    r_level = a_level
    a_seg = actual
    r_seg = ref
    t_ref = sum(d for _l, d in ref)
    while t < t_ref - NUM_ZERO:
        if i < len(a_seg) and t >= a_end - NUM_ZERO:
            a_level, a_dur = a_seg[i]
            a_end += a_dur
            i += 1
        if j < len(r_seg) and t >= r_end - NUM_ZERO:
            r_level, r_dur = r_seg[j]
            r_end += r_dur
            j += 1
        nxt = t_ref
        if i <= len(a_seg):
            nxt = min(nxt, a_end)
        if j <= len(r_seg):
            nxt = min(nxt, r_end)
        step = nxt - t
        if step <= 0.0:
            break
        if a_level != r_level:
            mismatch += step
        t = nxt
    return mismatch


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


def print_arm_stats(name: str, totals: list[float], mismatch: list[float]) -> None:
    tm, ts = mean_sd(totals)
    mm, ms = mean_sd(mismatch)
    print(f"  {name} total_us {num(tm)}+-{num(ts)} wrong_level_us {num(mm)}+-{num(ms)}")


def print_paired(label: str, xa: list[float], xb: list[float]) -> None:
    print(f"  paired {label}: {verdict(xa, xb)}")


def main() -> None:
    short = [SHORT_SYM] * N_SHORT
    period = [PERIOD_SYM]
    payload_syms = encode_byte(PAYLOAD, BIT0, BIT1, MSB_FIRST)
    swapped_payload = encode_byte(PAYLOAD, BIT1, BIT0, MSB_FIRST)  # bit0/bit1 swap
    decoded_ok = decode_byte(payload_syms, BIT0, BIT1, MSB_FIRST)
    decoded_swap = decode_byte(swapped_payload, BIT0, BIT1, MSB_FIRST)
    bit_pattern = "".join(
        "1" if ((PAYLOAD >> (7 - i)) & 1) else "0" for i in range(8)
    )

    us = tick_us(RESOLUTION_HZ)
    wrong_us = tick_us(WRONG_RESOLUTION_HZ)
    short_one_us = (SHORT_D0 + SHORT_D1) * us
    short_total = short_one_us * N_SHORT
    short_wrong_total = (SHORT_D0 + SHORT_D1) * wrong_us * N_SHORT
    period_us = (PERIOD_D0 + PERIOD_D1) * us
    loop_hw_us = period_us * LOOP_COUNT
    loop_sw_idle_us = loop_hw_us + REISSUE_GAP_US * (LOOP_COUNT - 1)
    byte_us = 8 * (BIT0_D0 + BIT0_D1) * us  # bit0 and bit1 have equal period

    print("Synthetic RMT symbol / encoder stand-in versus bit-bang stretch; official driver / flash 本页未运行")
    print(
        f"resolution_hz={RESOLUTION_HZ} (official example 1 MHz tick, 1 tick = 1 us; not a chip-universal default) "
        f"tick_us={us:.4f} wrong_resolution_hz={WRONG_RESOLUTION_HZ} wrong_tick_us={wrong_us:.4f}"
    )
    print(
        f"short_symbol duration0={SHORT_D0} level0={SHORT_L0} duration1={SHORT_D1} level1={SHORT_L1} "
        f"N_SHORT={N_SHORT} hand_calc short_one={short_one_us:.4f} us short_total={short_total:.4f} us "
        f"short_wrong_total={short_wrong_total:.4f} us"
    )
    print(
        f"period_symbol duration0={PERIOD_D0} level0={PERIOD_L0} duration1={PERIOD_D1} level1={PERIOD_L1} "
        f"loop_count={LOOP_COUNT} (positive finite; -1 would loop until rmt_disable and skip trans-done, not used here) "
        f"reissue_gap_us={REISSUE_GAP_US:.4f}"
    )
    print(
        f"hand_calc period={period_us:.4f} us loop_hw={loop_hw_us:.4f} us "
        f"loop_sw_idle={loop_sw_idle_us:.4f} us"
    )
    print(
        f"bytes_encoder payload=0x{PAYLOAD:02X} msb_first={MSB_FIRST} bit_pattern={bit_pattern} "
        f"bit0 duration0={BIT0_D0} level0={BIT0_L0} duration1={BIT0_D1} level1={BIT0_L1} "
        f"bit1 duration0={BIT1_D0} level0={BIT1_L0} duration1={BIT1_D1} level1={BIT1_L1}"
    )
    print(
        f"hand_calc byte_total={byte_us:.4f} us decoded_official=0x{decoded_ok:02X} "
        f"decoded_bit_swap=0x{decoded_swap:02X}"
    )
    print(
        f"seeds={len(SEEDS)} clear_frac={CLEAR_FRAC:.4f} lambda_per_us={LAMBDA_PER_US:.4f} "
        f"isr_cost_us={ISR_COST_US:.4f} lambda_alt={LAMBDA_ALT:.4f} "
        f"hand_calc work_plan 30+25+50+40+35=180"
    )
    print("no integration step: tick-to-us conversion and additive ISR counts, closed form")
    print(
        "ISR load draws are common random numbers, keyed on the declared hardware durations; "
        "B ignores them, A applies them"
    )

    # --- idle: no load, exact hardware durations for A and B ---
    ref_seg, ref_total = play(short, RESOLUTION_HZ, hardware=True, loops=1, reissue_gap_us=0.0, draws=None, isr_cost=0.0)
    a_idle_seg, a_idle_total = play(short, RESOLUTION_HZ, hardware=False, loops=1, reissue_gap_us=0.0, draws=None, isr_cost=0.0)
    zeros = [0.0] * len(SEEDS)
    a_idle_tot = [a_idle_total] * len(SEEDS)
    b_idle_tot = [ref_total] * len(SEEDS)
    a_idle_mis = [wrong_level_us(a_idle_seg, ref_seg)] * len(SEEDS)
    b_idle_mis = [wrong_level_us(ref_seg, ref_seg)] * len(SEEDS)
    print("idle (single-shot short-pulse list, no ISR load)")
    print_arm_stats("A_bitbang", a_idle_tot, a_idle_mis)
    print_arm_stats("B_hardware", b_idle_tot, b_idle_mis)
    print_paired("A-B total_us", a_idle_tot, b_idle_tot)
    print_paired("A-B wrong_level_us", a_idle_mis, b_idle_mis)

    # --- isr_loaded_short ---
    a_load_tot: list[float] = []
    b_load_tot: list[float] = []
    a_load_mis: list[float] = []
    b_load_mis: list[float] = []
    a_alt_tot: list[float] = []
    a_alt_mis: list[float] = []
    for seed in SEEDS:
        rng = random.Random(seed)
        draws = load_draws(short, RESOLUTION_HZ, loops=1, reissue_gaps=0, rng=rng, lam=LAMBDA_PER_US)
        b_seg, b_tot = play(short, RESOLUTION_HZ, hardware=True, loops=1, reissue_gap_us=0.0, draws=draws, isr_cost=ISR_COST_US)
        a_seg, a_tot = play(short, RESOLUTION_HZ, hardware=False, loops=1, reissue_gap_us=0.0, draws=draws, isr_cost=ISR_COST_US)
        a_load_tot.append(a_tot)
        b_load_tot.append(b_tot)
        a_load_mis.append(wrong_level_us(a_seg, b_seg))
        b_load_mis.append(wrong_level_us(b_seg, b_seg))
        rng_alt = random.Random(seed)
        draws_alt = load_draws(short, RESOLUTION_HZ, loops=1, reissue_gaps=0, rng=rng_alt, lam=LAMBDA_ALT)
        a_seg_alt, a_tot_alt = play(short, RESOLUTION_HZ, hardware=False, loops=1, reissue_gap_us=0.0, draws=draws_alt, isr_cost=ISR_COST_US)
        a_alt_tot.append(a_tot_alt)
        a_alt_mis.append(wrong_level_us(a_seg_alt, b_seg))
    print(
        f"isr_loaded_short (same short-pulse list, lambda_per_us={LAMBDA_PER_US:.4f} isr_cost_us={ISR_COST_US:.4f})"
    )
    print_arm_stats("A_bitbang", a_load_tot, a_load_mis)
    print_arm_stats("B_hardware", b_load_tot, b_load_mis)
    print_paired("A-B total_us", a_load_tot, b_load_tot)
    print_paired("A-B wrong_level_us", a_load_mis, b_load_mis)
    print_paired("B total_us vs declared", b_load_tot, [short_total] * len(SEEDS))

    # --- hw_loop_periodic under the same load style ---
    a_loop_tot: list[float] = []
    b_loop_tot: list[float] = []
    a_loop_mis: list[float] = []
    b_loop_mis: list[float] = []
    gaps = LOOP_COUNT - 1
    for seed in SEEDS:
        rng = random.Random(1000 + seed)  # distinct from the short-pulse stream, still CRN across arms
        draws = load_draws(period, RESOLUTION_HZ, loops=LOOP_COUNT, reissue_gaps=gaps, rng=rng, lam=LAMBDA_PER_US)
        b_seg, b_tot = play(period, RESOLUTION_HZ, hardware=True, loops=LOOP_COUNT, reissue_gap_us=REISSUE_GAP_US, draws=draws, isr_cost=ISR_COST_US)
        a_seg, a_tot = play(period, RESOLUTION_HZ, hardware=False, loops=LOOP_COUNT, reissue_gap_us=REISSUE_GAP_US, draws=draws, isr_cost=ISR_COST_US)
        a_loop_tot.append(a_tot)
        b_loop_tot.append(b_tot)
        a_loop_mis.append(wrong_level_us(a_seg, b_seg))
        b_loop_mis.append(wrong_level_us(b_seg, b_seg))
    print(
        f"hw_loop_periodic (loop_count={LOOP_COUNT} vs software re-issue, same ISR load; "
        f"reissue_gap_us={REISSUE_GAP_US:.4f})"
    )
    print_arm_stats("A_bitbang", a_loop_tot, a_loop_mis)
    print_arm_stats("B_hardware", b_loop_tot, b_loop_mis)
    print_paired("A-B total_us", a_loop_tot, b_loop_tot)
    print_paired("A-B wrong_level_us", a_loop_mis, b_loop_mis)
    print_paired("B total_us vs declared", b_loop_tot, [loop_hw_us] * len(SEEDS))

    # --- wrong resolution (deterministic lose) ---
    c_seg, c_tot = play(short, WRONG_RESOLUTION_HZ, hardware=True, loops=1, reissue_gap_us=0.0, draws=None, isr_cost=0.0)
    c_tot_l = [c_tot] * len(SEEDS)
    c_mis = [wrong_level_us(c_seg, ref_seg)] * len(SEEDS)
    print("wrong_resolution (C times the same ticks at wrong_resolution_hz, no ISR load)")
    print_arm_stats("C_wrong_hz", c_tot_l, c_mis)
    print_arm_stats("B_hardware", b_idle_tot, b_idle_mis)
    print_paired("C-B total_us", c_tot_l, b_idle_tot)
    print_paired("C-B wrong_level_us", c_mis, b_idle_mis)

    # --- bytes encoder bit0/bit1 swap ---
    b_byte_seg, b_byte_tot = play(payload_syms, RESOLUTION_HZ, hardware=True, loops=1, reissue_gap_us=0.0, draws=None, isr_cost=0.0)
    d_seg, d_tot = play(swapped_payload, RESOLUTION_HZ, hardware=True, loops=1, reissue_gap_us=0.0, draws=None, isr_cost=0.0)
    d_tot_l = [d_tot] * len(SEEDS)
    b_byte_tot_l = [b_byte_tot] * len(SEEDS)
    d_mis = [wrong_level_us(d_seg, b_byte_seg)] * len(SEEDS)
    b_byte_mis = [wrong_level_us(b_byte_seg, b_byte_seg)] * len(SEEDS)
    print(
        f"bytes_bit_swap (D swaps bit0/bit1 on payload 0x{PAYLOAD:02X}; "
        f"decoded_official=0x{decoded_ok:02X} decoded_bit_swap=0x{decoded_swap:02X})"
    )
    print_arm_stats("D_bit_swap", d_tot_l, d_mis)
    print_arm_stats("B_hardware", b_byte_tot_l, b_byte_mis)
    print_paired("D-B total_us", d_tot_l, b_byte_tot_l)
    print_paired("D-B wrong_level_us", d_mis, b_byte_mis)

    # --- swapped levels ---
    e_syms = [SHORT_SYM.swapped_levels()] * N_SHORT
    e_seg, e_tot = play(e_syms, RESOLUTION_HZ, hardware=True, loops=1, reissue_gap_us=0.0, draws=None, isr_cost=0.0)
    e_tot_l = [e_tot] * len(SEEDS)
    e_mis = [wrong_level_us(e_seg, ref_seg)] * len(SEEDS)
    print("swapped_levels (E swaps level0/level1 on the idle short-pulse list)")
    print_arm_stats("E_swap_lvl", e_tot_l, e_mis)
    print_arm_stats("B_hardware", b_idle_tot, b_idle_mis)
    print_paired("E-B total_us", e_tot_l, b_idle_tot)
    print_paired("E-B wrong_level_us", e_mis, b_idle_mis)

    print(
        f"alternative lambda_per_us={LAMBDA_ALT:.4f} on isr_loaded_short (same seeds, not adopted)"
    )
    print_arm_stats("A_bitbang@alt", a_alt_tot, a_alt_mis)
    print_arm_stats("B_hardware", b_load_tot, b_load_mis)
    print_paired("A-B total_us@alt", a_alt_tot, b_load_tot)

    print(
        "No winner declared: with no extra load the bit-bang loop can match the "
        "hardware-timed list; a declared ISR load stretches the software delays "
        "while the hardware-timed list stays on the declared ticks; a hardware "
        "loop_count restart stays on loop_count times the period while a software "
        "re-issue stretches; wrong tick resolution, a bytes-encoder bit0/bit1 swap, "
        "and swapped level0/level1 lose and are kept"
    )
    print("Official RMT driver / flash: 本页未运行; ESP-IDF RMT statements 以文档为准")


if __name__ == "__main__":
    main()
