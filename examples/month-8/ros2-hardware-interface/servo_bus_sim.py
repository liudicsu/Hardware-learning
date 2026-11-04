#!/usr/bin/env python3
"""servo_bus_sim.py: simulate hardware read/write cycle jitter → timeout counts.

Models a ros2_control-style loop at CONTROL_HZ. Each tick must finish both
read() and write() within the period. Bus latency is base + jitter; when the
sum exceeds the period the tick is a TIMEOUT (deadline miss).

Modes:
  naive — always pay full read+write cost.
  budget_guard — if projected read+write would exceed the period, skip the
                 blocking write and apply a cheap hold (HOLD_MS). That can still
                 miss if read alone is huge, but usually cuts timeouts.

Pinned seed and constants keep expected/ stable. Pure CPU; no real serial.
The so101_hw/ skeleton beside this file is for your Jazzy workspace
(marked 「本页未运行」 in the lesson).
usage: python3 servo_bus_sim.py
"""
from __future__ import annotations

import random

CONTROL_HZ = 100
PERIOD_MS = 1000.0 / CONTROL_HZ  # 10.0
BASE_READ_MS = 2.0
BASE_WRITE_MS = 2.5
JITTER_MS = 6.0  # uniform [0, JITTER_MS] added to read and to write
HOLD_MS = 0.4  # cheap "hold last command" path under budget_guard
TICKS = 200
SEED = 8


def run(budget_guard: bool) -> tuple[int, float, int]:
    """Return (timeouts, max_overshoot_ms, holds_used)."""
    rng = random.Random(SEED)
    timeouts = 0
    max_over = 0.0
    holds = 0
    for _ in range(TICKS):
        read_ms = BASE_READ_MS + rng.random() * JITTER_MS
        write_ms = BASE_WRITE_MS + rng.random() * JITTER_MS
        if budget_guard and (read_ms + write_ms) > PERIOD_MS:
            total = read_ms + HOLD_MS
            holds += 1
        else:
            total = read_ms + write_ms
        over = total - PERIOD_MS
        if over > 0:
            timeouts += 1
            max_over = max(max_over, over)
    return timeouts, max_over, holds


def main() -> None:
    t_naive, o_naive, _ = run(False)
    t_guard, o_guard, holds = run(True)
    print(f"servo_bus_sim control_hz={CONTROL_HZ} period_ms={PERIOD_MS:g} ticks={TICKS} seed={SEED}")
    print(f"naive_timeouts={t_naive} naive_max_overshoot_ms={o_naive:.3f}")
    print(f"guard_timeouts={t_guard} guard_max_overshoot_ms={o_guard:.3f} holds={holds}")
    print(f"timeout_reduction={t_naive - t_guard}")
    print("ok: CPU bus jitter toy (no real STS3215 bus, page not run)")


if __name__ == "__main__":
    main()
