#!/usr/bin/env python3
"""tf2 Buffer lookup time: latest (time 0) vs lookup at the image stamp vs extrapolating past the buffer.

Synthetic, stdlib only.  A Buffer stand-in, not tf2: no C++ BufferCore, no
message filters, no clocks, no executor.  Real `ros2 run tf2_ros ...` and a
real camera: 本页未运行.  tf2 statements are 以原文为准.

One pan joint (planar rotation about z) is broadcast at 50 Hz; every sample
reaches the listener's buffer after a transport latency.  A camera stamps an
image at t_img and the node asks for base_link <- camera at t_q (delivery).
    A_latest      lookupTransform(target, source, time 0): newest sample in the buffer
    B_stamped     lookupTransform(..., t_img, timeout 50 ms): interpolate between the two
                  samples around t_img; if t_img is newer than the newest sample, wait up to
                  the timeout for it to arrive, else fail (ExtrapolationException)
    C_extrapolate t_img inside the buffer: same interpolation as B; newer than the newest
                  sample: extrapolate linearly from the two newest samples, no wait
tf2 itself never extrapolates (it raises); C is what a hand-rolled workaround does.
For one rotation axis, tf2's slerp reduces to linear interpolation of the angle.

Common random numbers: per (regime, seed) the joint trajectory, broadcast
stamp jitter, transport latencies, image stamps and image delivery lags are
drawn once and shared by all three arms.  Arms differ only in the lookup rule.

No integration step: the joint angle is a closed-form function of time and
the buffer is a lookup table, so no step-size stability criterion applies.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
US = 1_000_000            # microseconds per second; stamps are integers, as tf2 uses integer time
TF_PERIOD = 20_000        # us: 50 Hz joint_states -> robot_state_publisher -> /tf
IMG_PERIOD = 33_000       # us: about 30 Hz camera
TIMEOUT = 50_000          # us: B's lookupTransform timeout
LEVER = 1.0               # m: error is measured on a point 1 m in front of the camera
T_END = 10 * US
CACHE = 10 * US           # tf2 default cache time (BUFFER_CORE_DEFAULT_CACHE_TIME = 10 s)
NUM_ZERO = 1e-9           # |m| and sd both below this: floating-point residue, not a gap

# name: (moving, transport latency range us, image delivery lag range us, dropout (period us, length us) or None)
REGIMES = {
    "static_tree": (False, (2_000, 8_000), (60_000, 100_000), None),
    "lagging_stamp": (True, (2_000, 8_000), (60_000, 100_000), None),
    "fresh_stamp": (True, (15_000, 30_000), (1_000, 3_000), None),
    "tf_dropout": (True, (2_000, 8_000), (60_000, 100_000), (1_000_000, 300_000)),
}
ARMS = ("A_latest", "B_stamped", "C_extrapolate")


def shared_draws(regime, seed):
    """Common random numbers: one trajectory, one broadcast timeline, one camera timeline for all arms."""
    moving, lat, lag, drop = REGIMES[regime]
    rng = random.Random(f"{regime}/{seed}")
    amp, f1, ph1 = rng.uniform(0.8, 1.2), rng.uniform(0.4, 0.6), rng.uniform(0.0, 2 * math.pi)
    amp2, f2, ph2 = rng.uniform(0.2, 0.4), rng.uniform(1.5, 2.0), rng.uniform(0.0, 2 * math.pi)
    rest = rng.uniform(-0.5, 0.5)
    traj = (moving, rest, amp, f1, ph1, amp2, f2, ph2)
    tf = []                                   # (stamp, arrival) for every broadcast sample
    t = 0
    while t <= T_END:
        stamp = t + rng.randrange(0, 2_001)   # broadcast jitter up to 2 ms
        if not (drop and drop[0] // 2 <= stamp % drop[0] < drop[0] // 2 + drop[1]):
            tf.append((stamp, stamp + rng.randrange(lat[0], lat[1] + 1)))
        t += TF_PERIOD
    imgs = []                                 # (t_img, t_query)
    t = US
    while t <= T_END - US:
        imgs.append((t, t + rng.randrange(lag[0], lag[1] + 1)))
        t += IMG_PERIOD
    return traj, tf, imgs


def angle(traj, t_us):
    moving, rest, amp, f1, ph1, amp2, f2, ph2 = traj
    if not moving:
        return rest
    t = t_us / US
    return rest + amp * math.sin(2 * math.pi * f1 * t + ph1) + amp2 * math.sin(2 * math.pi * f2 * t + ph2)


def lerp(s0, a0, s1, a1, t):
    if s1 == s0:
        return a1
    return a0 + (a1 - a0) * ((t - s0) / (s1 - s0))


def lookup(arm, buf, t_img, t_q, arrivals):
    """buf: samples (stamp, angle) already in the buffer at t_q, oldest first.  Returns (angle or None, wait_us)."""
    if arm == "A_latest":
        return buf[-1][1], 0
    if buf[0][0] <= t_img <= buf[-1][0]:
        for (s0, a0), (s1, a1) in zip(buf, buf[1:]):
            if s0 <= t_img <= s1:
                return lerp(s0, a0, s1, a1, t_img), 0
    if t_img < buf[0][0]:
        return None, 0                        # into the past: older than the cache
    if arm == "C_extrapolate":
        (s0, a0), (s1, a1) = buf[-2], buf[-1]
        return lerp(s0, a0, s1, a1, t_img), 0
    for stamp, ang, arrival in arrivals:      # B: wait for a sample newer than t_img
        if stamp >= t_img:
            if arrival - t_q > TIMEOUT:
                return None, 0                # ExtrapolationException after the timeout
            return lerp(buf[-1][0], buf[-1][1], stamp, ang, t_img), arrival - t_q
    return None, 0


def run(regime, seed):
    traj, tf, imgs = shared_draws(regime, seed)
    samples = sorted((arr, st, angle(traj, st)) for st, arr in tf)
    out = {a: {"err": [], "fail": 0, "wait": []} for a in ARMS}
    answers = []
    for t_img, t_q in imgs:
        buf = sorted((st, ang) for arr, st, ang in samples if arr <= t_q and st >= t_q - CACHE)
        later = sorted((st, ang, arr) for arr, st, ang in samples if arr > t_q)
        truth = angle(traj, t_img)
        row = {}
        for arm in ARMS:
            ang, wait = lookup(arm, buf, t_img, t_q, later)
            row[arm] = None if ang is None else 2.0 * LEVER * abs(math.sin((ang - truth) / 2.0)) * 1000.0
            if ang is None:
                out[arm]["fail"] += 1
            else:
                out[arm]["wait"].append(wait / 1000.0)
        answers.append(row)
    common = [r for r in answers if all(r[a] is not None for a in ARMS)]
    res = {}
    for arm in ARMS:
        res[arm] = {
            "err": sum(r[arm] for r in common) / len(common),
            "fail": 100.0 * out[arm]["fail"] / len(imgs),
            "wait": sum(out[arm]["wait"]) / len(out[arm]["wait"]),
            "n": len(common),
        }
    return res


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs, m):
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def main():
    print("Synthetic tf2 Buffer stand-in: one pan joint at 50 Hz, a 30 Hz camera; arms differ only in the lookup time rule; not tf2 itself")
    print(f"TF period {TF_PERIOD / 1000:.0f} ms, B timeout {TIMEOUT / 1000:.0f} ms, cache {CACHE // US} s, error on a point {LEVER:.0f} m in front of the camera; seeds={len(SEEDS)}")
    print("No integration step: the joint angle is closed-form in time and the buffer is a lookup table")
    res = {r: [run(r, s) for s in SEEDS] for r in REGIMES}
    print("regime arm err_mm fail_% wait_ms  (mean+-sd over seeds; err on images every arm answered)")
    for r, (moving, lat, lag, drop) in REGIMES.items():
        dtxt = f", TF dropout {drop[1] // 1000} ms every {drop[0] // 1000} ms" if drop else ""
        print(f"{r} ({'moving' if moving else 'static'} joint, transport {lat[0] // 1000}-{lat[1] // 1000} ms, image delivery lag {lag[0] // 1000}-{lag[1] // 1000} ms{dtxt}; {min(x['A_latest']['n'] for x in res[r])}-{max(x['A_latest']['n'] for x in res[r])} common images per seed)")
        for a in ARMS:
            cols = " ".join(f"{num(mean_sd([x[a][m] for x in res[r]])[0])}+-{num(mean_sd([x[a][m] for x in res[r]])[1])}" for m in ("err", "fail", "wait"))
            print(f"  {a} {cols}")
        for other in ("A_latest", "C_extrapolate"):
            for m in ("err", "fail", "wait"):
                xa, xb = [x[other][m] for x in res[r]], [x["B_stamped"][m] for x in res[r]]
                print(f"  paired {other[0]}-B {m}: {verdict(xa, xb)}")
    print("No winner declared: a stamped lookup removes the lag error but waits for fresh data and fails when TF stops; extrapolation never fails and is wrong when the joint turns")
    print("Real ros2 / tf2_ros / camera: 本页未运行; tf2 behaviour 以原文为准")


if __name__ == "__main__":
    main()
