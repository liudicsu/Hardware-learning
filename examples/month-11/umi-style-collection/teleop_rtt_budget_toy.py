#!/usr/bin/env python3
"""Unilateral POSITION teleop + explicit visual-reaction stop model.
Shared command stream, common packet-jitter draws, shared 20 operator reactions.
Low/high are physical toy links; one_way_only is an optimistic ACCOUNTING
ablation of high, not a third measured network or a proposed safety controller.
All Wi-Fi/WebRTC-like delays are illustrative; no actual network is measured.
"""
from __future__ import annotations
import math
import random
import statistics

SEED = 114
DT = 0.01
TAU = 0.08
N = 500
EVENT = 200
SPEED = 0.35  # m/s, lesson-defined ramp
LIMIT = 0.18  # m additional travel; exercise threshold, NOT a safety standard
# forward command ticks, acknowledgement ticks, video return ticks
LINKS = {"low_RTT": (2, 2, 4), "high_RTT": (10, 12, 20),
         "one_way_only_estimate": (10, 12, 20)}
PIPELINE = 4  # capture/encode/decode/display ticks; no real camera run


def follower(commands, forward_ticks, jitter):
    events = sorted((i + max(0, forward_ticks + jitter[i]), i, value)
                    for i, value in enumerate(commands))
    q, latest, held, cursor = 0.0, -1, 0.0, 0
    result = []
    for step in range(N):
        while cursor < len(events) and events[cursor][0] <= step:
            _, seq, value = events[cursor]
            if seq > latest:  # a late packet never overwrites a fresher command
                latest, held = seq, value
            cursor += 1
        q += (held - q) * DT / TAU
        result.append(q)
    return result


def main():
    rng = random.Random(SEED)
    jitter = tuple(rng.choice((-1, 0, 1)) for _ in range(N))
    reactions = tuple(rng.randint(18, 28) for _ in range(20))
    commands = tuple(0.25 * math.sin(1.8 * i * DT) for i in range(N))
    print(f"seed={SEED} unilateral_position dt_ms={DT*1000:.0f} servo_tau_ms={TAU*1000:.0f}")
    print("shared_stream=500_positions; shared_jitter_draws=yes; shared_reactions=20")
    print("arm command_oneway_ms control_RTT_ms video_probe_RTT_ms display_age_used_ms")
    rows = []
    for name, (forward, ack, video) in LINKS.items():
        display = 0 if name == "one_way_only_estimate" else video + PIPELINE
        # Nominal control probe: command+ack; video probe: request+video+pipeline.
        print(f"{name} {forward*10} {(forward+ack)*10} "
              f"{(forward+video+PIPELINE)*10} {display*10}")
        q = follower(commands, forward, jitter)
        mae = statistics.mean(abs(q[i] - commands[i]) for i in range(50, N))
        lag = min(range(51), key=lambda delay: sum(
            abs(q[i] - commands[i-delay]) for i in range(50, N)))
        advances = []
        for reaction in reactions:
            # Remote hazard at EVENT; seen after display age, then operator reacts.
            stop_sent = EVENT + display + reaction
            stream = tuple(SPEED * DT * min(i, stop_sent) for i in range(N))
            trajectory = follower(stream, forward, jitter)
            advances.append(max(trajectory[EVENT:]) - trajectory[EVENT])
        misses = sum(a > LIMIT for a in advances)
        rows.append((name, mae, lag * 10, statistics.mean(advances), max(advances), misses))
    print("arm tracking_MAE_m best_lag_ms stop_advance_mean_m max_m miss_count/20")
    for name, mae, lag, mean, maximum, misses in rows:
        print(f"{name} {mae:.5f} {lag} {mean:.5f} {maximum:.5f} {misses}/20")
    # Causality and out-of-order behavior: future command cannot act before arrival.
    impulse = (0.0,) * 10 + (1.0,) * (N - 10)
    test = follower(impulse, 5, (0,) * N)
    assert all(x == 0 for x in test[:15]) and test[15] > 0
    assert follower((0.0,) * N, 10, jitter) == [0.0] * N
    assert rows[2][3] < rows[1][3]  # omitted video return makes budget optimistic
    print("reaction_ticks=18..28; stop_sent=hazard+display_age+reaction")
    print("stop_advance=additional_follower_travel_after_hazard; miss=advance_gt_0.18m")
    print("one_way_only_estimate_ignores_display_NOT_actual_high_link_performance")
    print("control_RTT_is_not_video_RTT; no_force_feedback; network_real_robot_not_run")


if __name__ == "__main__":
    main()
