#!/usr/bin/env python3
"""Shared synthetic current edges; Vpin = Vrail - L_loop * di/dt ONLY.
Far bulk, local ceramic/short loop, and long trace differ only in effective L.
This proxies the fast current-return loop, NOT a simulated capacitor network.
No I*R, I*dt/C, ESR, ESL network, ringing, FCC/CE or fuse claims; not 11.1 IR.
A real SN74HC14 datasheet recommends local 0.1 uF; it does NOT supply these L,
current edges or rail predictions. All toy numeric inputs are synthetic. Stdlib.
"""
from typing import NamedTuple

VRAIL = 3.3
LOOPS_NH = (("far_bulk", 40.0), ("local_ceramic_short", 3.0), ("long_trace", 100.0))
# delta current A, linear rise/fall duration ns. Each is held for 500 ns.
PULSES = ((0.10, 20.0), (0.16, 40.0), (0.08, 10.0))


class Edge(NamedTuple):
    time_s: float
    di_dt: float        # A/s, signed; falling edges produce a model overshoot


def pulse_train():
    """Three shared periods; pulse starts 10 us apart, cycles 100 us apart."""
    edges = []
    for cycle in range(3):
        for index, (delta_a, rise_ns) in enumerate(PULSES):
            start = cycle * 100e-6 + index * 10e-6
            duration = rise_ns * 1e-9
            slope = delta_a / duration
            edges.extend((Edge(start, slope), Edge(start + duration + 500e-9, -slope)))
    return tuple(edges)


def evaluate(loop_nh, edges):
    if loop_nh < 0:
        raise ValueError("loop inductance must be nonnegative")
    # Include idle rail. No artificial clipping hides undershoot/overshoot.
    rails = (VRAIL,) + tuple(VRAIL - loop_nh * 1e-9 * edge.di_dt for edge in edges)
    return min(rails), VRAIL - min(rails)


def main():
    edges = pulse_train()
    print("Synthetic L*di/dt ONLY; local-current-loop proxy, not capacitor-network simulation")
    print(f"shared train rising_edges={sum(e.di_dt > 0 for e in edges)} falling_edges={sum(e.di_dt < 0 for e in edges)} rail_V={VRAIL:.3f}")
    print("arm effective_L_nH min_rail_V dip_V")
    for arm, loop_nh in LOOPS_NH:
        minimum, dip = evaluate(loop_nh, edges)
        print(f"{arm} {loop_nh:.1f} {minimum:.6f} {dip:.6f}")
    print("No capacitor charge/ESR/ESL/ringing prediction; no FCC/CE or fuse conclusion")
    print("Real board / scope / EMC test: 本页未运行")


if __name__ == "__main__":
    main()
