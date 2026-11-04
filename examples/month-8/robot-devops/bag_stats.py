#!/usr/bin/env python3
"""bag_stats.py: topic rates and drop gaps from a synthetic rosbag2/MCAP fixture.

Real Jazzy rosbag2 defaults to the mcap storage plugin
(rosbag2_storage::get_default_storage_id() returns \"mcap\" on the jazzy branch).
This toy reads a JSON timeline that mirrors per-topic stamp sequences extracted
from such a bag — no libmcap required, so expected/ stays CPU-reproducible.

Reports Hz estimates and inter-arrival gaps that exceed 1.5× the nominal period.
usage: python3 bag_stats.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "sample_bag", "timeline.json")


def main() -> None:
    with open(FIX, encoding="utf-8") as f:
        bag = json.load(f)
    assert bag.get("storage_id") == "mcap"
    print(
        f"bag={bag['uri']} storage_id={bag['storage_id']} "
        f"duration_s={bag['duration_s']:g} (synthetic fixture; not a binary .mcap)"
    )
    print(f"{'topic':<28} {'n':>5} {'hz_est':>8} {'nominal':>8} {'gaps':>5}")
    total_gaps = 0
    for topic in bag["topics"]:
        name = topic["name"]
        stamps = topic["stamps_ns"]
        nominal_hz = float(topic["nominal_hz"])
        n = len(stamps)
        if n >= 2:
            dur = (stamps[-1] - stamps[0]) / 1e9
            hz = (n - 1) / dur if dur > 0 else float("nan")
        else:
            hz = 0.0
        period = 1e9 / nominal_hz
        gaps = 0
        for a, b in zip(stamps, stamps[1:]):
            if (b - a) > 1.5 * period:
                gaps += 1
        total_gaps += gaps
        print(f"{name:<28} {n:5d} {hz:8.2f} {nominal_hz:8.1f} {gaps:5d}")
    print(f"total_gap_events={total_gaps}")
    print("ok: fixture storage_id is mcap (Jazzy rosbag2 default)")


if __name__ == "__main__":
    main()
