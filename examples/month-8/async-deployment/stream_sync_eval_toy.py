#!/usr/bin/env python3
"""Causal buffered alignment vs latest-arrived multi-stream fusion (stdlib).
Capture time != arrival time != sensor clock stamp. Known synthetic clock
biases are corrected, not magically estimated. At each arrival, the query
is now-LAG. Interpolation can use samples after the query ONLY if they have
already ARRIVED by now. Never inspect future-arriving packets.
Both modes share packets/noise and are scored at the SAME lagged query.
Catch-window hit is a retrospective synthetic proxy, not live robot success.
"""
import bisect
import math
import random

SEED = 41
LAG = 0.14
CLOCK_OFFSETS = (0.012, -0.006, 0.004)
RATES = (30, 100, 60)
DELAYS = (0.065, 0.015, 0.035)
JITTER = (0.010, 0.004, 0.008)
TOL = 0.012


def truth(t):
    target = 0.30 * math.sin(2.2 * t) + 0.10
    encoder = 0.22 * math.sin(2.2 * t - 0.3)
    # Third channel is a synthetic gap proxy in metres, not a real force sensor.
    return target, encoder, target - encoder


def make_packets():
    rng = random.Random(SEED)
    packets = []
    for stream, rate in enumerate(RATES):
        for k in range(5 * rate + 1):
            capture = k / rate
            arrival = capture + DELAYS[stream] + rng.uniform(-JITTER[stream], JITTER[stream])
            stamp = capture + CLOCK_OFFSETS[stream]
            value = truth(capture)[stream] + rng.gauss(0, 0.001)
            packets.append((arrival, stream, stamp, value))
    return sorted(packets)


def interpolate(history, query, now):
    # history contains ONLY packets appended by the arrival-event loop.
    times = [p[0] for p in history]
    i = bisect.bisect_left(times, query)
    if i == 0 or i == len(history):
        return None  # need an arrived bracket; no extrapolation
    a, b = history[i - 1], history[i]
    assert a[2] <= now and b[2] <= now  # arrival, NOT capture, is availability
    assert a[0] <= query <= b[0]
    w = (query - a[0]) / (b[0] - a[0])
    return a[1] + w * (b[1] - a[1])


def main():
    # Regression: a captured endpoint is not usable before it arrives.
    assert interpolate([(0.85, 1.0, 0.92)], 0.86, 1.0) is None
    arrived = [(0.85, 1.0, 0.92), (0.88, 4.0, 0.95)]
    assert abs(interpolate(arrived, 0.86, 1.0) - 2.0) < 1e-12
    try:
        interpolate([(0.85, 1.0, 0.92), (0.88, 4.0, 1.02)], 0.86, 1.0)
    except AssertionError:
        pass
    else:
        raise AssertionError("future-arriving bracket accepted")
    histories = [[], [], []]
    errors = {mode: [] for mode in ("latest", "stamp_aligned")}
    hits = {mode: 0 for mode in errors}
    for now, stream, stamp, value in make_packets():
        capture = stamp - CLOCK_OFFSETS[stream]
        # Insert by corrected capture time, handling out-of-order arrivals.
        bisect.insort(histories[stream], (capture, value, now))
        query = now - LAG
        if query < 0.2 or query > 4.8 or not all(histories):
            continue
        aligned = [interpolate(h, query, now) for h in histories]
        if any(x is None for x in aligned):
            continue  # matched coverage for both conditions
        latest = [h[-1][1] for h in histories]  # newest capture among arrived data
        true_gap = truth(query)[2]
        for mode, values in (("latest", latest), ("stamp_aligned", aligned)):
            gap_error = values[0] - values[1] - true_gap
            proxy_error = values[2] - true_gap
            errors[mode].append((gap_error, proxy_error))
            hits[mode] += int(abs(gap_error) <= TOL and abs(proxy_error) <= TOL)
    count = len(errors["latest"])
    assert count > 0 and count == len(errors["stamp_aligned"])
    print(f"seed={SEED} lag_s={LAG:.2f} shared_packets_and_noise=True")
    print("clock_offsets_s=0.012,-0.006,0.004 known_correction=True")
    print(f"matched_arrival_events={count} catch_tolerance_m={TOL:.3f}")
    for mode, e in errors.items():
        rmse = math.sqrt(sum(a*a + b*b for a, b in e) / (2 * count))
        print(f"{mode} misalignment_rmse_m={rmse:.6f} catch_proxy={hits[mode]}/{count}")
    print("arrived_brackets_only=True extrapolation=False live_success_claim=False")


if __name__ == "__main__":
    main()
