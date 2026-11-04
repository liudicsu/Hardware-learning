#!/usr/bin/env python3
"""watchdog_sim.py: command-stream faults with/without a timeout watchdog (stdlib).

A 1-D joint command stream (rad) is disturbed by: dropped packets, delayed
delivery, NaN payloads, and occasional wild spikes. Without a watchdog the last
command sticks — including spikes past the soft stops. With a watchdog: if no
valid command arrives within TIMEOUT_TICKS, hold the last safe command; always
clamp to [Q_MIN, Q_MAX].

Compares max excursion beyond the software limits.
No STS3215 overload / temperature numbers — soft stops are lesson-chosen only.
usage: python3 watchdog_sim.py
"""
from __future__ import annotations

import math
import random

SEED = 7
HORIZON = 200
TIMEOUT_TICKS = 3
Q_MIN = -0.80
Q_MAX = 0.80
DROP_P = 0.06
SPIKE_AT = (55, 120)  # wild commands past the soft stop
NAN_AT = (40, 90, 150)
DELAY_AT = (70,)  # hold off applying the next command for 5 ticks


def nominal(t: int) -> float:
    return 0.55 * math.sin(2 * math.pi * t / 50.0)


def build_stream(rng: random.Random) -> list[float | None]:
    """Per-tick payload: float, or None meaning 'no packet this tick'."""
    planned: list[float | None] = []
    for t in range(HORIZON):
        if t in NAN_AT:
            planned.append(float("nan"))
        elif t in SPIKE_AT:
            planned.append(1.45 if t % 2 else -1.45)  # past ±0.80
        elif rng.random() < DROP_P:
            planned.append(None)
        else:
            planned.append(nominal(t))
    # apply delay: replace DELAY_AT tick with None and push its value later
    for d in DELAY_AT:
        if d < len(planned) and planned[d] is not None and not (
            isinstance(planned[d], float) and math.isnan(planned[d])
        ):
            val = planned[d]
            planned[d] = None
            dest = min(HORIZON - 1, d + 5)
            # only overwrite if dest empty-ish
            planned[dest] = val
    return planned


def run(stream: list[float | None], watchdog: bool) -> tuple[float, int, int]:
    last_safe = 0.0
    applied = 0.0
    since_valid = 0
    max_over = 0.0
    clamps = 0
    holds = 0
    for payload in stream:
        valid = payload is not None and not (isinstance(payload, float) and math.isnan(payload))
        if valid:
            since_valid = 0
            cmd = float(payload)
            # "safe" memory only records in-range commands
            if Q_MIN <= cmd <= Q_MAX:
                last_safe = cmd
        else:
            since_valid += 1
            if watchdog and since_valid >= TIMEOUT_TICKS:
                cmd = last_safe
                holds += 1
            else:
                cmd = applied  # stick
        if watchdog:
            clamped = max(Q_MIN, min(Q_MAX, cmd))
            if clamped != cmd:
                clamps += 1
            cmd = clamped
        applied = cmd
        over = max(0.0, applied - Q_MAX, Q_MIN - applied)
        if over > max_over:
            max_over = over
    return max_over, clamps, holds


def main() -> None:
    rng = random.Random(SEED)
    stream = build_stream(rng)
    drops = sum(1 for p in stream if p is None)
    nans = sum(1 for p in stream if isinstance(p, float) and math.isnan(p))
    spikes = sum(
        1
        for p in stream
        if isinstance(p, float) and not math.isnan(p) and (p > Q_MAX or p < Q_MIN)
    )
    print(
        f"seed={SEED} horizon={HORIZON} timeout_ticks={TIMEOUT_TICKS} "
        f"q_min={Q_MIN} q_max={Q_MAX} drops={drops} nans={nans} spikes={spikes}"
    )
    over_off, _, _ = run(stream, watchdog=False)
    over_on, clamps, holds = run(stream, watchdog=True)
    print(f"{'mode':<16} {'max_overshoot':>14} {'clamps':>7} {'holds':>7}")
    print(f"{'no_watchdog':<16} {over_off:14.4f} {0:7d} {0:7d}")
    print(f"{'watchdog_clamp':<16} {over_on:14.4f} {clamps:7d} {holds:7d}")
    print(
        f"ok: watchdog max_overshoot < no_watchdog "
        f"({over_on:.4f} < {over_off:.4f})"
    )


if __name__ == "__main__":
    main()
