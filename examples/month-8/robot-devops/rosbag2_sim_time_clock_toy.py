#!/usr/bin/env python3
"""Official rosbag2 simulation-time clock contract, stdlib only.

Synthetic arrival schedules, not a live ros2 bag, not a real simulator,
and not a second mcap / bag-stats / bag-QoS lecture.  Live ros2 bag /
real simulator / Foxglove / Rerun / hardware clock: 本页未运行.
rosbag2 statements 以原文为准.

In ROS 2, "simulation time" refers to publishing a clock value on the
/clock topic, instead of using the system clock to tell time.

Common random numbers: one shared synthetic arrival schedule per seed
(data messages plus a /clock stream that starts late, so every seed has
at least one data message before the first /clock).  Arms, shared
arrivals (per seed):
  A_official        : --use-sim-time record: do not write until the
                      first /clock; thereafter stamp each written
                      message with the latest /clock.  zero_then_n_jump
                      is false on this arm.
  C_write_0_then_N  : write early messages with timestamp 0 until
                      /clock arrives, then stamp later messages with
                      time N from /clock.  Pre-declared as remaining
                      playable / not introducing the official 0-then-N
                      jump.  Pre-declared lose, kept.  One fail mode,
                      declared before the first run.
The arms differ only in how record timestamps are formed.

Play --clock facts in this file use official argparse const=40 and
default=0 only.  They are not a second pre-declared lose claim.
"""

from __future__ import annotations

import random

# Declared before the first official run.
SEEDS = (0, 1, 2, 3, 4)
N_DATA = 12  # grid data messages, plus per-seed early extras
DATA_PERIOD_MS = 50  # grid spacing, ms
CLOCK_FIRST_MS = 150  # first /clock wall arrival; starts late
CLOCK_FIRST_ALT_MS = 250  # named alternative late start, not adopted
CLOCK_PERIOD_MS = 50  # /clock stream period after the first, ms
N_CLOCK = 10  # /clock messages in the stream
SIM_T0_MS = 1000  # first /clock sim-time value N, ms (N > 0)
CLEAR_FRAC = 0.2000  # small-vs-clear factor; printed before the first official run
NUM_ZERO = 1e-9
CLOCK_HZ_DEFAULT = 0  # official argparse default
CLOCK_HZ_BARE = 40  # official argparse const for bare --clock
PLAY_PERIOD_MS = 25  # 手算 1000/40 = 25
SESSION_ACTIVE_MS = 250  # 手算 250/25 = 10 publishes at 40 Hz
IDLE_AFTER_STOP_MS = 200
RUN_BEFORE_PAUSE_MS = 100
PAUSE_MS = 100
RESTART_SESSION_MS = 100

ARMS = ("A_official", "C_write_0_then_N")


def shared_schedule(seed: int, clock_first_ms: int) -> tuple[list[int], list[tuple[int, int]]]:
    """One shared arrival schedule for this seed (CRN).

    Data grid plus extra early messages drawn before CLOCK_FIRST_MS, so
    every seed has at least one data message before the first /clock.
    The /clock stream starts at clock_first_ms (late) with sim time
    SIM_T0_MS, then steps by CLOCK_PERIOD_MS.
    """
    rng = random.Random(seed)
    data = [k * DATA_PERIOD_MS for k in range(N_DATA)]
    n_extra = 1 + rng.randrange(0, 3)  # 1, 2, or 3 extras, all early
    extras = [rng.randrange(0, CLOCK_FIRST_MS) for _ in range(n_extra)]
    data.extend(extras)
    data.sort()
    clocks = [
        (clock_first_ms + i * CLOCK_PERIOD_MS, SIM_T0_MS + i * CLOCK_PERIOD_MS)
        for i in range(N_CLOCK)
    ]
    return data, clocks


def record_arm(data: list[int], clocks: list[tuple[int, int]], official: bool) -> dict[str, float]:
    """Stamp data messages under the official or the 0-then-N record rule."""
    events: list[tuple[int, str, int]] = []
    for t in data:
        events.append((t, "data", 0))
    for t, sim in clocks:
        events.append((t, "clock", sim))
    # At equal wall time, apply /clock before data so a message arriving
    # with the first /clock is stamped with that clock, not dropped.
    events.sort(key=lambda e: (e[0], 0 if e[1] == "clock" else 1))

    latest: int | None = None
    written_stamps: list[int] = []
    dropped = 0
    for _wall, kind, sim in events:
        if kind == "clock":
            latest = sim
            continue
        if official:
            if latest is None:
                dropped += 1
                continue
            written_stamps.append(latest)
        else:
            if latest is None:
                written_stamps.append(0)
            else:
                written_stamps.append(latest)

    jump = 0
    zero_then_n = 0
    if written_stamps:
        has_zero = any(s == 0 for s in written_stamps)
        later_n = [s for s in written_stamps if s > 0]
        if has_zero and later_n:
            zero_then_n = 1
            jump = later_n[0] - 0
    return {
        "written": float(len(written_stamps)),
        "dropped": float(dropped),
        "first_stamp_ms": float(written_stamps[0]) if written_stamps else 0.0,
        "last_stamp_ms": float(written_stamps[-1]) if written_stamps else 0.0,
        "jump_from_zero_ms": float(jump),
        "zero_then_n_jump": float(zero_then_n),
        "playable": 0.0 if zero_then_n else 1.0,
    }


def mean_sd(xs: list[float]) -> tuple[float, float]:
    mu = sum(xs) / len(xs)
    if len(xs) == 1:
        return mu, 0.0
    return mu, (sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


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


def fmt_pair(m: float, s: float) -> str:
    return f"{num(m)}+-{num(s)}"


def verdict(xa: list[float], xb: list[float]) -> str:
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < CLEAR_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def collect(clock_first_ms: int) -> dict[str, dict[str, list[float]]]:
    keys = (
        "written",
        "dropped",
        "first_stamp_ms",
        "last_stamp_ms",
        "jump_from_zero_ms",
        "zero_then_n_jump",
        "playable",
    )
    out = {arm: {k: [] for k in keys} for arm in ARMS}
    for seed in SEEDS:
        data, clocks = shared_schedule(seed, clock_first_ms)
        for arm, official in (("A_official", True), ("C_write_0_then_N", False)):
            vals = record_arm(data, clocks, official)
            for k in keys:
                out[arm][k].append(vals[k])
    return out


def print_arm(tag: str, res: dict[str, list[float]]) -> None:
    print(
        f"  {tag} written {fmt_pair(*mean_sd(res['written']))}  "
        f"dropped {fmt_pair(*mean_sd(res['dropped']))}  "
        f"first_stamp_ms {fmt_pair(*mean_sd(res['first_stamp_ms']))}  "
        f"last_stamp_ms {fmt_pair(*mean_sd(res['last_stamp_ms']))}"
    )
    print(
        f"    jump_from_zero_ms {fmt_pair(*mean_sd(res['jump_from_zero_ms']))}  "
        f"zero_then_n_jump {fmt_pair(*mean_sd(res['zero_then_n_jump']))}  "
        f"playable {fmt_pair(*mean_sd(res['playable']))}"
    )


def play_clock_publishes(frequency_hz: float, active_ms: int, period_ms: int) -> int:
    """Fixed-frequency /clock count while a session is active (t < active_ms)."""
    if frequency_hz <= 0:
        return 0
    n = 0
    t = 0
    while t < active_ms:
        n += 1
        t += period_ms
    return n


def play_pause_demo() -> tuple[int, int, int, bool, int]:
    """Running then paused ticks; pause keeps publishing the paused time."""
    period = PLAY_PERIOD_MS
    play_head = 0
    running_times: list[int] = []
    pause_times: list[int] = []
    t = 0
    while t < RUN_BEFORE_PAUSE_MS:
        running_times.append(play_head)
        play_head += period
        t += period
    paused_time = play_head
    t = 0
    while t < PAUSE_MS:
        pause_times.append(paused_time)
        t += period
    all_paused = bool(pause_times) and all(x == paused_time for x in pause_times)
    further_after_stop = 0  # node may stay alive; session has ended
    return len(running_times), len(pause_times), paused_time, all_paused, further_after_stop


def main() -> None:
    print("Synthetic rosbag2 simulation-time clock toy; shared arrivals; not a live ros2 bag")
    print(
        f"seeds={len(SEEDS)} n_data={N_DATA} data_period_ms={DATA_PERIOD_MS} "
        f"clock_first_ms={CLOCK_FIRST_MS} clock_period_ms={CLOCK_PERIOD_MS} "
        f"n_clock={N_CLOCK} sim_t0_ms={SIM_T0_MS} clear_frac={CLEAR_FRAC:.4f}"
    )
    print(
        f"hand_calc 1000/{CLOCK_HZ_BARE}={PLAY_PERIOD_MS}  "
        f"hand_calc {SESSION_ACTIVE_MS}/{PLAY_PERIOD_MS}={SESSION_ACTIVE_MS // PLAY_PERIOD_MS}  "
        f"work_plan 30+25+50+40+35=180"
    )
    print(
        "Arm C lose mode, declared before the first run: write early messages with timestamp 0 "
        "until /clock arrives, then stamp later messages with time N from /clock; "
        "pre-declared as remaining playable / not introducing the official 0-then-N jump"
    )
    print("Regimes were written before the first run")

    res = collect(CLOCK_FIRST_MS)
    print(
        f"record official vs lose (clock_first_ms={CLOCK_FIRST_MS}; "
        "shared arrivals, /clock starts late)"
    )
    print_arm("A_official", res["A_official"])
    print_arm("C_write_0_then_N", res["C_write_0_then_N"])
    print(
        "  paired C-A zero_then_n_jump: "
        f"{verdict(res['C_write_0_then_N']['zero_then_n_jump'], res['A_official']['zero_then_n_jump'])}"
    )
    print(
        "  paired C-A jump_from_zero_ms: "
        f"{verdict(res['C_write_0_then_N']['jump_from_zero_ms'], res['A_official']['jump_from_zero_ms'])}"
    )
    print(
        "  paired C-A playable: "
        f"{verdict(res['C_write_0_then_N']['playable'], res['A_official']['playable'])}"
    )
    print(
        "  paired A-C dropped: "
        f"{verdict(res['A_official']['dropped'], res['C_write_0_then_N']['dropped'])}"
    )
    print(
        "  paired A-C written: "
        f"{verdict(res['A_official']['written'], res['C_write_0_then_N']['written'])}"
    )

    res_alt = collect(CLOCK_FIRST_ALT_MS)
    print(
        f"alternative clock_first_ms={CLOCK_FIRST_ALT_MS} "
        f"(same seed family, CRN: same data arrivals, later /clock, not adopted)"
    )
    print_arm("A_official", res_alt["A_official"])
    print_arm("C_write_0_then_N", res_alt["C_write_0_then_N"])
    print(
        "  paired C-A zero_then_n_jump: "
        f"{verdict(res_alt['C_write_0_then_N']['zero_then_n_jump'], res_alt['A_official']['zero_then_n_jump'])}"
    )
    print(
        f"  paired A(alt)-A(clock_first_ms={CLOCK_FIRST_MS}) dropped: "
        f"{verdict(res_alt['A_official']['dropped'], res['A_official']['dropped'])}"
    )
    print(
        "  paired C-A jump_from_zero_ms: "
        f"{verdict(res_alt['C_write_0_then_N']['jump_from_zero_ms'], res_alt['A_official']['jump_from_zero_ms'])}"
    )

    print(
        "cli --use-sim-time --no-discovery: rejected  "
        "The /clock topic needs to be discovered to record with sim time."
    )
    print(
        "--use-sim-time and --no-discovery both set, but are incompatible settings. "
        "The /clock topic needs to be discovered to record with sim time."
    )

    n_default = play_clock_publishes(CLOCK_HZ_DEFAULT, SESSION_ACTIVE_MS, PLAY_PERIOD_MS)
    n_bare = play_clock_publishes(CLOCK_HZ_BARE, SESSION_ACTIVE_MS, PLAY_PERIOD_MS)
    print(
        f"play --clock default={CLOCK_HZ_DEFAULT}: publish_count={n_default} "
        "bag_clock_excluded=no"
    )
    print(
        f"play --clock bare const={CLOCK_HZ_BARE}: "
        f"session_active_ms={SESSION_ACTIVE_MS} period_ms={PLAY_PERIOD_MS} "
        f"hand_calc {SESSION_ACTIVE_MS}/{PLAY_PERIOD_MS}={SESSION_ACTIVE_MS // PLAY_PERIOD_MS} "
        f"publish_count={n_bare} bag_clock_excluded=yes"
    )
    print(
        f"play --clock {CLOCK_HZ_BARE} after session stop, node still alive "
        f"idle_ms={IDLE_AFTER_STOP_MS}: further_publish_count=0"
    )
    run_n, pause_n, paused_time, all_paused, further = play_pause_demo()
    print(
        f"play --clock {CLOCK_HZ_BARE} pause does not end the session: "
        f"run_ticks={run_n} pause_ticks={pause_n} pause_time_ms={paused_time} "
        f"pause_publish_count={pause_n} pause_times_all_paused="
        f"{'yes' if all_paused else 'no'} then stop further_publish_count={further}"
    )
    n_restart = play_clock_publishes(CLOCK_HZ_BARE, RESTART_SESSION_MS, PLAY_PERIOD_MS)
    print(
        f"play --clock {CLOCK_HZ_BARE} starting another session restarts publication: "
        f"restart_session_ms={RESTART_SESSION_MS} restart_publish_count={n_restart}"
    )

    print(
        "No winner declared: official --use-sim-time waits for the first /clock "
        "and does not write a 0-then-N jump; writing at time 0 then N loses "
        "because that jump is officially essentially unplayable"
    )
    print(
        "Live ros2 bag / real simulator / Foxglove / Rerun / hardware clock: 本页未运行; "
        "rosbag2 statements 以原文为准"
    )


if __name__ == "__main__":
    main()
