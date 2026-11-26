#!/usr/bin/env python3
"""Synthetic timeout / control-loop deadline on a wrapped clock.

Stdlib only. No call to the machine clock, and no call to clock_settime.
Jumps are injected by a fake / wrapped clock inside this toy. Arms:

  A_wall   deadline from a time.time() stand-in (adjustable wall clock).
  B_mono   the same deadline from a time.monotonic() stand-in (cannot go
           backwards; not affected by the wall-clock jumps).
  C_stamp  a wrong use of the monotonic stand-in: its absolute value is
           compared with an epoch wall stamp, as if the monotonic reference
           point were the epoch. The reference point is undefined, so only
           the difference between two calls is valid. Pre-declared lose, kept.

Common random numbers: seeds 0-4. Every regime is deterministic (fixed
timeout, step, jump, and origins; the five seeds repeat the same fire time).
No integration step: the loop is an exact multiple of dt, and fire times
also have a closed form printed as hand_calc.

Regimes (declared before the first run):
  no_jump           no wall jump              -> A vs B tie or official near-tie
                                                (both accept the deadline)
  backward_jump     wall set back             -> wall-clock timeout is late /
                                                missed; monotonic holds
  forward_jump      wall jumped forward       -> wall-clock timeout expires
                                                early; monotonic holds
  stamp_confusion   no wall jump; C compares
                    an absolute monotonic
                    reading with an epoch
                    stamp                     -> C loses

Python time docs 以文档为准. Live NTP / clock_settime: 本页未运行.
"""
from __future__ import annotations

import math

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
CLEAR_FRAC = 0.2000  # small-vs-clear factor; printed before the first official run
TIMEOUT_S = 1.0000
DT_S = 0.1250
JUMP_AT_S = 0.2500
BACKWARD_S = -2.0000
FORWARD_S = 2.0000
FORWARD_ALT_S = 0.5000  # disclosed alternative, same jump instant, not adopted
WALL_ORIGIN_S = 1700000000.0000  # declared fake epoch start, not a live time.time()
MONO_ORIGIN_S = 1000.0000  # undefined monotonic reference point
MAX_WAIT_S = 5.0000  # cap when a confused stamp never expires
ARMS = ("A_wall", "B_mono", "C_stamp")
REGIMES = ("no_jump", "backward_jump", "forward_jump", "stamp_confusion")


class FakeClocks:
    """Paired wall and monotonic stand-ins. Only the wall offset can jump."""

    def __init__(self, wall0: float, mono0: float) -> None:
        self.ticks = 0
        self.wall0 = wall0
        self.mono0 = mono0
        self.wall_offset = 0.0

    @property
    def true_t(self) -> float:
        return self.ticks * DT_S

    def advance(self) -> None:
        self.ticks += 1

    def jump_wall(self, delta: float) -> None:
        self.wall_offset += delta

    def time(self) -> float:
        return self.wall0 + self.true_t + self.wall_offset

    def monotonic(self) -> float:
        return self.mono0 + self.true_t


def fire_time(arm: str, jump_delta: float = 0.0, jump_at: float = JUMP_AT_S) -> float:
    clocks = FakeClocks(WALL_ORIGIN_S, MONO_ORIGIN_S)
    if arm == "A_wall":
        deadline = clocks.time() + TIMEOUT_S

        def expired() -> bool:
            return clocks.time() >= deadline
    elif arm == "B_mono":
        deadline = clocks.monotonic() + TIMEOUT_S

        def expired() -> bool:
            return clocks.monotonic() >= deadline
    elif arm == "C_stamp":
        # Wrong: treat the absolute monotonic reading as an epoch wall stamp.
        deadline = WALL_ORIGIN_S + TIMEOUT_S

        def expired() -> bool:
            return clocks.monotonic() >= deadline
    else:
        raise ValueError(arm)

    if expired():
        return clocks.true_t
    jumped = False
    max_ticks = int(round(MAX_WAIT_S / DT_S))
    jump_ticks = int(round(jump_at / DT_S))
    while clocks.ticks < max_ticks:
        clocks.advance()
        if (not jumped) and jump_delta != 0.0 and clocks.ticks >= jump_ticks:
            clocks.jump_wall(jump_delta)
            jumped = True
        if expired():
            return clocks.true_t
    return MAX_WAIT_S


def closed_form_wall(jump_delta: float, jump_at: float = JUMP_AT_S) -> float:
    """Hand_calc fire time for the wall-clock arm, same rule as the stepped loop."""
    if jump_delta == 0.0:
        return TIMEOUT_S
    if jump_at >= TIMEOUT_S:
        return TIMEOUT_S
    if jump_at + jump_delta >= TIMEOUT_S:
        return jump_at
    fire = TIMEOUT_S - jump_delta
    if fire > MAX_WAIT_S:
        return MAX_WAIT_S
    return fire


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


def seed_values(fire: dict[str, float]) -> dict[str, list[float]]:
    return {arm: [fire[arm]] * len(SEEDS) for arm in ARMS}


def print_regime(name: str, tag: str, fire: dict[str, float]) -> None:
    res = seed_values(fire)
    print(f"{name} ({tag})")
    for arm in ARMS:
        m, s = mean_sd(res[arm])
        print(f"  {arm} {num(m)}+-{num(s)} s")
    err_a = [a - b for a, b in zip(res["A_wall"], res["B_mono"])]
    err_c = [c - b for c, b in zip(res["C_stamp"], res["B_mono"])]
    zeros = [0.0] * len(SEEDS)
    print(f"  residual A-B {num(mean_sd(err_a)[0])}+-{num(mean_sd(err_a)[1])} s")
    print(f"  residual C-B {num(mean_sd(err_c)[0])}+-{num(mean_sd(err_c)[1])} s")
    print(f"  paired A-B fire_s: {verdict(res['A_wall'], res['B_mono'])}")
    print(f"  paired C-B fire_s: {verdict(res['C_stamp'], res['B_mono'])}")
    print(f"  paired residual A-B vs 0: {verdict(err_a, zeros)}")
    print(f"  paired residual C-B vs 0: {verdict(err_c, zeros)}")


def main() -> None:
    fire_no = {arm: fire_time(arm, 0.0) for arm in ARMS}
    fire_back = {arm: fire_time(arm, BACKWARD_S) for arm in ARMS}
    fire_fwd = {arm: fire_time(arm, FORWARD_S) for arm in ARMS}
    fire_stamp = {arm: fire_time(arm, 0.0) for arm in ARMS}
    fire_alt = {arm: fire_time(arm, FORWARD_ALT_S) for arm in ARMS}

    hc_no_a = closed_form_wall(0.0)
    hc_back_a = closed_form_wall(BACKWARD_S)
    hc_fwd_a = closed_form_wall(FORWARD_S)
    hc_alt_a = closed_form_wall(FORWARD_ALT_S)
    hc_b = TIMEOUT_S
    hc_c = MAX_WAIT_S

    print("Synthetic monotonic vs wall-clock timeout toy; wrapped clocks only; not a live NTP or clock_settime run")
    print(
        f"timeout={TIMEOUT_S:.4f}s dt={DT_S:.4f}s jump_at={JUMP_AT_S:.4f}s "
        f"backward={BACKWARD_S:.4f}s forward={FORWARD_S:.4f}s max_wait={MAX_WAIT_S:.4f}s"
    )
    print(
        f"wall_origin={WALL_ORIGIN_S:.4f}s mono_origin={MONO_ORIGIN_S:.4f}s "
        f"seeds={len(SEEDS)} clear_frac={CLEAR_FRAC:.4f} "
        f"hand_calc work_plan 30+25+50+40+35=180"
    )
    print("no integration step: exact dt grid and closed-form fire times")
    print(
        f"hand_calc no_jump A={hc_no_a:.10f}s B={hc_b:.10f}s C={hc_c:.10f}s "
        f"step_A={fire_no['A_wall']:.10f}s residual_step-closed_A={fire_no['A_wall'] - hc_no_a:.3e}s"
    )
    print(
        f"hand_calc backward A={hc_back_a:.10f}s B={hc_b:.10f}s C={hc_c:.10f}s "
        f"step_A={fire_back['A_wall']:.10f}s residual_step-closed_A={fire_back['A_wall'] - hc_back_a:.3e}s"
    )
    print(
        f"hand_calc forward A={hc_fwd_a:.10f}s B={hc_b:.10f}s C={hc_c:.10f}s "
        f"step_A={fire_fwd['A_wall']:.10f}s residual_step-closed_A={fire_fwd['A_wall'] - hc_fwd_a:.3e}s"
    )
    print(
        f"hand_calc stamp_confusion A={hc_no_a:.10f}s B={hc_b:.10f}s C={hc_c:.10f}s "
        f"step_C={fire_stamp['C_stamp']:.10f}s residual_step-closed_C={fire_stamp['C_stamp'] - hc_c:.3e}s"
    )
    print(
        f"hand_calc B holds at {hc_b:.10f}s under every declared wall jump; "
        f"C never reaches the epoch stamp mono_end={MONO_ORIGIN_S + MAX_WAIT_S:.10f}s "
        f"< deadline={WALL_ORIGIN_S + TIMEOUT_S:.10f}s"
    )

    print_regime("no_jump", "no wall jump, both official clocks accept the deadline", fire_no)
    print_regime(
        "backward_jump",
        f"wall set back by {BACKWARD_S:.4f}s at {JUMP_AT_S:.4f}s",
        fire_back,
    )
    print_regime(
        "forward_jump",
        f"wall jumped forward by {FORWARD_S:.4f}s at {JUMP_AT_S:.4f}s",
        fire_fwd,
    )
    print_regime(
        "stamp_confusion",
        "no wall jump; C compares absolute monotonic with an epoch stamp",
        fire_stamp,
    )

    print(
        f"alternative forward_jump {FORWARD_ALT_S:.4f}s (same jump_at, not adopted) "
        f"fire_A={fire_alt['A_wall']:.10f}s fire_B={fire_alt['B_mono']:.10f}s "
        f"fire_C={fire_alt['C_stamp']:.10f}s closed_A={hc_alt_a:.10f}s "
        f"residual_step-closed_A={fire_alt['A_wall'] - hc_alt_a:.3e}s"
    )
    print("  paired A-B fire_s: " + verdict([fire_alt["A_wall"]] * len(SEEDS), [fire_alt["B_mono"]] * len(SEEDS)))
    print(
        "No winner declared: with no jump the wall clock and the monotonic clock "
        "tie on the deadline; a backward jump makes the wall timeout late, a "
        "forward jump expires it early, and treating a monotonic absolute as an "
        "epoch stamp loses"
    )
    print("Live NTP / clock_settime: 本页未运行; Python time library docs 以文档为准")


if __name__ == "__main__":
    main()
