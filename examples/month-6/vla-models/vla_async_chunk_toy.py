#!/usr/bin/env python3
"""vla_async_chunk_toy.py: sync vs async action-chunk inference, as a tradeoff (stdlib).

SmolVLA (arXiv 2506.01844, 3.3) runs a RobotClient that pops one action per
control tick from a queue and, when the remaining fraction |A|/n drops below a
threshold g, captures an observation and asks a PolicyServer for a new chunk
without stopping. g = 0 is the sequential limit (drain, then wait), g = 1 the
compute-intensive limit (a request as soon as the last one returns).

Every arm here shares:
  - the same chunk predictor (a function of the observation only),
  - the same chunk size n and control tick dt,
  - the same latency draws l_S: the k-th request of every arm takes LAT[k],
  - the same target path (piecewise-constant velocity, seeded).
The robot tracks a moving target; a chunk is the target extrapolated from the
observation, so old observations give worse actions after a velocity change.

Metrics per arm: idle_s (ticks with an empty queue x dt), infer_calls,
underruns (separate empty-queue episodes), staleness = age of the observation
behind each executed action (mean / max, s), switches = new chunks spliced
into a non-empty queue and their mean |jump| (overlap thrash), track_rmse.
Aggregation f here: actions carry the executed-step index they belong to; on
arrival the new chunk's already-executed steps are dropped and overlapping
steps take the new value (one simple f; the paper only says "aggregate").
This is NOT 10.2 RTC (no soft mask, the new chunk is not conditioned on the
old one) and NOT 8.3 timestamp alignment of sensor streams. Async need not
win every metric. SmolVLA weights, a GPU server and an SO-100 arm are not run
on this page (本页未运行); paper latency / success numbers are 以论文为准.
usage: python3 vla_async_chunk_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 1844
DT = 1 / 30             # 30 Hz control, as in the paper's real-world setting
N_CHUNK = 50            # chunk size n (the paper trains n = 50)
HORIZON = 900           # ticks = 30 s
LAT_MEAN, LAT_SD = 0.30, 0.10   # l_S in seconds (lesson-chosen, not measured)
LAT_MIN = 0.10
ARMS = (("sync", 0.0), ("async_g0.1", 0.1), ("async_g0.3", 0.3), ("async_g0.7", 0.7), ("async_g1.0", 1.0))


def target_path(rng):
    """Target position per tick: velocity changes every 1-3 s."""
    pos, vel, out, t_next = 0.0, 0.0, [], 0
    for t in range(HORIZON + N_CHUNK + 200):
        if t == t_next:
            vel = rng.uniform(-0.3, 0.3)
            t_next = t + rng.randint(30, 90)
        out.append((pos, vel))
        pos += vel * DT
    return out


def latencies(rng, k=2000):
    return [max(LAT_MIN, rng.gauss(LAT_MEAN, LAT_SD)) for _ in range(k)]


def predict_chunk(obs_step, obs_tick, path):
    """Same predictor for all arms: extrapolate the observed target n steps ahead.

    Actions are indexed by executed-step count (not wall time): a chunk from an
    observation taken after step k covers steps k+1 .. k+n.
    """
    p, v = path[obs_tick]
    return {obs_step + 1 + i: p + v * (i + 1) * DT for i in range(N_CHUNK)}


def run(g, path, lat):
    queue = predict_chunk(0, 0, path)   # initial chunk, as in Algorithm 1 line 2
    source = {k: 0 for k in queue}      # step -> wall tick of the observation behind it
    inflight = None                     # (arrival_tick, obs_step, obs_tick)
    step, calls, idle, underruns, was_empty = 0, 1, 0, 0, False
    ages, jumps, errs, held = [], [], [], 0.0
    for t in range(1, HORIZON + 1):
        if inflight and inflight[0] <= t:          # chunk arrives: aggregate f(A, A~)
            _arr, obs_step, obs_tick = inflight
            live = {k: a for k, a in predict_chunk(obs_step, obs_tick, path).items() if k > step}
            overlap = [k for k in live if k in queue]
            if overlap:
                k0 = min(overlap)
                jumps.append(abs(live[k0] - queue[k0]))
            queue.update(live)
            source.update({k: obs_tick for k in live})
            inflight = None
        if step + 1 in queue:                      # pop and execute the next step
            step += 1
            held = queue.pop(step)
            ages.append((t - source[step]) * DT)
            was_empty = False
        else:                                      # empty queue: the arm waits
            idle += 1
            underruns += not was_empty
            was_empty = True
        errs.append(held - path[t][0])
        if inflight is None and (not queue or len(queue) / N_CHUNK < g):
            inflight = (t + max(1, math.ceil(lat[calls] / DT)), step, t)
            calls += 1
    return {
        "idle_s": idle * DT, "calls": calls, "underruns": underruns,
        "age_mean": sum(ages) / len(ages), "age_max": max(ages),
        "switches": len(jumps), "jump_mean": sum(jumps) / len(jumps) if jumps else 0.0,
        "rmse": math.sqrt(sum(e * e for e in errs) / len(errs)),
    }


def main() -> None:
    path = target_path(random.Random(SEED))
    lat = latencies(random.Random(SEED + 1))
    mean_lat = sum(lat[:200]) / 200
    print(f"seed={SEED} dt={DT:.4f}s n={N_CHUNK} horizon={HORIZON * DT:.0f}s "
          f"l_S~N({LAT_MEAN},{LAT_SD}) min {LAT_MIN}s, shared draws (mean of first 200 = {mean_lat:.3f}s)")
    print(f"no-idle rule of thumb (paper 3.3): g >= E[l_S]/(n*dt) = {mean_lat / (N_CHUNK * DT):.3f}")
    print("same predictor, same n, same latency draws, same target path for every arm")
    print(f"{'arm':<11} {'g':>4} {'idle_s':>7} {'infer_calls':>11} {'underruns':>9} "
          f"{'stale_mean_s':>12} {'stale_max_s':>11} {'switches':>8} {'mean_jump':>9} {'track_rmse':>10}")
    rows = {}
    for name, g in ARMS:
        r = run(g, path, lat)
        rows[name] = r
        print(f"{name:<11} {g:4.1f} {r['idle_s']:7.2f} {r['calls']:11d} {r['underruns']:9d} "
              f"{r['age_mean']:12.3f} {r['age_max']:11.3f} {r['switches']:8d} {r['jump_mean']:9.4f} "
              f"{r['rmse']:10.4f}")
    s, a = rows["sync"], rows["async_g0.7"]
    assert a["idle_s"] < s["idle_s"] and a["age_mean"] < s["age_mean"]
    assert a["calls"] > s["calls"] and a["switches"] > s["switches"]
    print(f"ok: async_g0.7 cuts idle {s['idle_s']:.2f}->{a['idle_s']:.2f}s and staleness "
          f"{s['age_mean']:.3f}->{a['age_mean']:.3f}s but costs infer_calls {s['calls']}->{a['calls']} "
          f"and {a['switches']} overlap switches; not RTC (10.2), not stamp sync (8.3); "
          "SmolVLA / GPU / arm 本页未运行")


if __name__ == "__main__":
    main()
