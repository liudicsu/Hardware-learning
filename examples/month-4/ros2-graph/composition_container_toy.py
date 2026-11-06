#!/usr/bin/env python3
"""Synthetic deterministic pub/sub scheduling counters, NOT ROS benchmarks.
Every component gets the same immutable command stream in both deployments.
Each process polls once per tick, even idle: a declared accounting assumption,
not Linux context switches or CPU time. Callbacks use the same work function.
Fault injection kills the process containing component 1 before tick 5;
no restart, shared dependencies or downstream cascade are modelled.
"""
from dataclasses import dataclass

TICKS = 12
CRASH_TICK = 5


@dataclass(frozen=True)
class Result:
    processes: int
    polls: int
    callbacks: int
    checksum: int
    lost_callbacks: int
    blast_radius: int


def run(n, composed, fault=False):
    if n < 2:
        raise ValueError("need at least two components")
    groups = (tuple(range(n)),) if composed else tuple((i,) for i in range(n))
    polls = callbacks = checksum = lost = 0
    victims = next(group for group in groups if 1 in group) if fault and CRASH_TICK < TICKS else ()
    for tick in range(TICKS):
        for group in groups:
            dead = fault and tick >= CRASH_TICK and 1 in group
            if not dead:
                polls += 1
            for component in group:
                # One publisher fan-out stream, same subscription schedule and payloads.
                if (tick + component) % 3 == 0:
                    if dead:
                        lost += 1
                    else:
                        callbacks += 1
                        checksum += (tick + 1) * (component + 1)
    return Result(len(groups), polls, callbacks, checksum, lost, len(victims))


def main():
    print("Synthetic shared stream: ticks=12; equal callback work; deterministic N sweep (no seeds).")
    print("N deployment processes poll_ticks callbacks checksum lost_callbacks crash_blast_radius")
    for fault in (False, True):
        print("fault=component1_before_tick5" if fault else "healthy")
        for n in (2, 4, 8):
            for composed in (False, True):
                r = run(n, composed, fault)
                print(n, "container" if composed else "separate", r.processes, r.polls,
                      r.callbacks, r.checksum, r.lost_callbacks, r.blast_radius)
    print("Poll ticks count per-process polling, NOT OS context switches or wall-clock speed.")
    print("Crash blast radius counts directly killed components, not downstream dependency loss.")
    print("Composition does not prove zero-copy; real intra-process demo is reading only.")


if __name__ == "__main__":
    main()
