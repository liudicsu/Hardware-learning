#!/usr/bin/env python3
"""ROS 2 QoS Deadline and Lifespan vs a reliability-only subscription, on one shared timeline.

Synthetic, stdlib only.  A discrete-event stand-in for one publisher and one subscription; it is
not an rmw / DDS implementation and makes no claim about bit-exact middleware behaviour.  Not the
reliability / durability *mismatch* earlier on this page (there every pair here is compatible and
connected), not the bag QoS replay, not composition, and not a FreeRTOS task deadline (Month 2).
Real `ros2 topic` / rclpy QoS events: 本页未运行.  ROS 2 Jazzy "Quality of Service settings"
definitions are 以原文为准:
  Deadline: the expected maximum amount of time between subsequent messages being published.
  Lifespan: the maximum time between publishing and reception before a message is stale or
            expired; expired messages are silently dropped.
  Requested deadline missed: the subscription has not received a message within the deadline.
  Offered deadline missed: the publisher has not published within the deadline.
  Compatibility: a subscription requesting a deadline shorter than the one offered is not
            connected (offered x, requested y < x: No).
Timeline (integer microseconds, so every comparison is exact): the publisher stamps a sample
every PERIOD with jitter; in late_sensor it sometimes stalls.  Each sample reaches the subscriber
after a network delay; a lost first transmission is repaired by a retransmission (reliable
delivery), modelled only as extra delay.  The subscriber keeps the newest stamp it has received
(an older sample arriving later is ignored by every arm).  A controller tick runs every PERIOD
with a per-seed phase; at each tick an arm either acts on its current sample or holds.
No integration step: there is no plant and no time stepping, only event times in microseconds,
so there is no step-size criterion (a test checks that all times are integers).
Common random numbers: for each (regime, seed) the publication times, stalls, delays, losses and
the controller phase are drawn once and shared by all three arms; five seeds.
Arms (same publication, delay, loss and tick draws):
  A_rel     reliability only (deadline and lifespan left at default, i.e. infinite): acts on the
            newest received sample whatever its age.
  B_dl      requested deadline DL_B and lifespan LS_B: a sample older than LS_B on arrival is
            dropped; if no sample has been accepted for longer than DL_B (requested deadline
            missed) the controller holds instead of acting.
  C_tight   the same with deadline DL_C shorter than the publish period, offered and requested
            alike (compatible), so the deadline is missed on almost every gap by construction.
Metrics per seed: stale-use % (ticks that act on a sample older than STALE), hold % (ticks with
no action), mean age of the samples acted on (ms), requested-deadline-missed events, lifespan
drops.  A deadline miss is counted per gap g between accepted receptions as ceil(g / DL) - 1, so
a gap exactly equal to the deadline is not a miss.
Regimes and expectations, written before the first run:
  late_sensor     stalls (prob 0.01, 40-120 ms), delay 1-3 ms, no loss
                  B consistent fewer stale uses than A (B pays hold ticks)
  on_time         no stalls, delay 1-3 ms, no loss       A and B tie (no misses, no drops)
  lossy_reliable  no stalls, loss 0.15 repaired after 10-30 ms
                  B ties A on stale uses and loses on hold % (lifespan drops the repaired samples)
  C_tight holds on most ticks in every regime (consistent loss to B on hold %).
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
MS = 1000                # microseconds per millisecond
PERIOD = 10 * MS         # publish and control period
JITTER = 1 * MS          # publish jitter, uniform +-
DURATION = 20000 * MS    # 20 s
STALE = 25 * MS          # a sample older than this at use is stale for the controller
DL_B, LS_B = 20 * MS, 10 * MS
DL_C, LS_C = 5 * MS, 10 * MS
NUM_ZERO = 1e-9
ARMS = ("A_rel", "B_dl", "C_tight")
# name: (stall prob, stall min ms, stall max ms, loss prob, repair min ms, repair max ms); before the first run
REGIMES = {
    "late_sensor": (0.01, 40, 120, 0.0, 0, 0),
    "on_time": (0.0, 0, 0, 0.0, 0, 0),
    "lossy_reliable": (0.0, 0, 0, 0.15, 10, 30),
}
STREAM = {"late_sensor": 0, "on_time": 1, "lossy_reliable": 2}
QOS = {"A_rel": (None, None), "B_dl": (DL_B, LS_B), "C_tight": (DL_C, LS_C)}


def compatible(offered, requested):
    """Deadline compatibility table of the Jazzy page; None stands for 'default' (infinite)."""
    if requested is None:
        return True
    if offered is None:
        return False
    return requested >= offered


def shared_draws(regime, seed):
    rng = random.Random(1000 * STREAM[regime] + seed)
    p_stall, s_min, s_max, p_loss, r_min, r_max = REGIMES[regime]
    samples, t = [], 0
    while True:
        t += PERIOD + rng.randint(-JITTER, JITTER)
        if p_stall and rng.random() < p_stall:
            t += rng.randint(s_min * MS, s_max * MS)
        if t > DURATION:
            break
        delay = rng.randint(1 * MS, 3 * MS)
        if p_loss and rng.random() < p_loss:
            delay += rng.randint(r_min * MS, r_max * MS)
        samples.append((t, t + delay))
    phase = rng.randint(0, PERIOD - 1)
    ticks = list(range(PERIOD + phase, DURATION + 1, PERIOD))
    return samples, ticks


def run_arm(arm, draw):
    samples, ticks = draw
    deadline, lifespan = QOS[arm]
    arrivals = sorted(samples, key=lambda s: (s[1], s[0]))
    accepted, drops = [], 0
    newest = -1
    for stamp, recv in arrivals:
        if lifespan is not None and recv - stamp > lifespan:
            drops += 1
            continue
        if stamp > newest:
            newest = stamp
            accepted.append((recv, stamp))
    misses = 0
    if deadline is not None:
        for (r0, _), (r1, _) in zip(accepted, accepted[1:]):
            gap = r1 - r0
            misses += max(0, -(-gap // deadline) - 1)
    stale = hold = 0
    ages = []
    k, cur, last_recv = 0, None, None
    for t in ticks:
        while k < len(accepted) and accepted[k][0] <= t:
            last_recv, cur = accepted[k]
            k += 1
        if cur is None or (deadline is not None and t - last_recv > deadline):
            hold += 1
            continue
        age = t - cur
        ages.append(age)
        if age > STALE:
            stale += 1
    n = len(ticks)
    return {"stale": 100.0 * stale / n, "hold": 100.0 * hold / n,
            "age": (sum(ages) / len(ages) / MS) if ages else 0.0, "miss": float(misses), "drop": float(drops)}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-5:
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


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{num(m)}+-{num(s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{num(m)}+-{num(s)}: {label}; {sign_note(diffs, m)}"


def main():
    print("Synthetic ROS 2 QoS stand-in: reliability only vs deadline + lifespan vs a deadline tighter than the period; not rmw / DDS")
    print(f"PERIOD={PERIOD // MS} ms JITTER=+-{JITTER // MS} ms DURATION={DURATION // MS // 1000} s STALE={STALE // MS} ms "
          f"B: deadline {DL_B // MS} ms lifespan {LS_B // MS} ms; C: deadline {DL_C // MS} ms lifespan {LS_C // MS} ms; seeds={len(SEEDS)}")
    print("no integration step: integer-microsecond event times, no plant")
    print(f"compatibility (Jazzy table): offered 20 ms / requested 20 ms -> {compatible(20, 20)}; offered 20 / requested 5 -> "
          f"{compatible(20, 5)} (no connection); offered 5 / requested 20 -> {compatible(5, 20)}; offered default / requested 20 -> {compatible(None, 20)}")
    print("regime arm stale_use_% hold_% mean_age_ms deadline_misses lifespan_drops  (mean+-sd over seeds)")
    for regime, (p_stall, s_min, s_max, p_loss, r_min, r_max) in REGIMES.items():
        print(f"{regime} (stall prob {p_stall}, {s_min}-{s_max} ms; loss {p_loss}, repaired after {r_min}-{r_max} ms)")
        draws = [shared_draws(regime, s) for s in SEEDS]
        res = {arm: [run_arm(arm, d) for d in draws] for arm in ARMS}
        for arm in ARMS:
            cols = ["{}+-{}".format(*map(num, mean_sd([r[k] for r in res[arm]]))) for k in ("stale", "hold", "age", "miss", "drop")]
            print(f"  {arm} " + " ".join(cols))
        for x, y in (("B_dl", "A_rel"), ("C_tight", "B_dl")):
            for key in ("stale", "hold", "age"):
                print(f"  paired {x[0]}-{y[0]} {key}: {verdict([r[key] for r in res[x]], [r[key] for r in res[y]])}")
    print("No winner declared: deadline + lifespan trade stale actions for hold ticks; they cost nothing on an on-time stream and cost holds when late repairs are dropped")
    print("Real ros2 topic / rclpy QoS events: 本页未运行; ROS 2 Jazzy QoS definitions 以原文为准")


if __name__ == "__main__":
    main()
