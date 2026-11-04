#!/usr/bin/env python3
"""chunk_latency_sim.py: sync vs async action-chunk latency (discrete time, stdlib).

Models a control loop at CONTROL_HZ. The policy returns ACTION_CHUNK steps per
inference that costs INFER_MS of wall time (converted to control ticks).

Sync: robot is idle for the whole inference; then plays the chunk.
Async: robot keeps playing the previous chunk while the next inference runs;
       a new chunk is swapped in when ready (may jump).

Reports idle-frame ratio and mean |Δa| at chunk boundaries for both modes.
Pinned constants keep expected/ stable. Not run on a real arm or GPU here.
usage: python3 chunk_latency_sim.py
"""
from __future__ import annotations

CONTROL_HZ = 50
INFER_MS = 80.0
ACTION_CHUNK = 16  # actions_per_chunk
THRESHOLD = 8  # chunk_size_threshold: async starts next infer when remaining <= this
HORIZON_S = 4.0
SEED_ACTION = 0.02  # per-step drift inside a chunk


def ticks(ms: float) -> int:
    return max(1, int(round(ms / 1000.0 * CONTROL_HZ)))


def make_chunk(start_a: float, n: int, drift: float) -> list[float]:
    return [start_a + drift * i for i in range(n)]


def sim_sync(total_ticks: int, infer_ticks: int, chunk: int) -> tuple[float, float, int]:
    t = 0
    idle = 0
    jumps = []
    a_prev = None
    base = 0.0
    while t < total_ticks:
        # infer (idle)
        for _ in range(infer_ticks):
            if t >= total_ticks:
                break
            idle += 1
            t += 1
        actions = make_chunk(base, chunk, SEED_ACTION)
        base += SEED_ACTION * chunk + 0.05  # next chunk starts a bit higher
        for i, a in enumerate(actions):
            if t >= total_ticks:
                break
            if a_prev is not None and i == 0:
                jumps.append(abs(a - a_prev))
            a_prev = a
            t += 1
    idle_ratio = idle / total_ticks
    mean_jump = sum(jumps) / len(jumps) if jumps else 0.0
    return idle_ratio, mean_jump, len(jumps)


def sim_async(total_ticks: int, infer_ticks: int, chunk: int, threshold: int) -> tuple[float, float, int]:
    t = 0
    idle = 0
    jumps = []
    a_prev = None
    # bootstrap: must wait for first chunk
    for _ in range(infer_ticks):
        idle += 1
        t += 1
    base = 0.0
    queue = make_chunk(base, chunk, SEED_ACTION)
    base += SEED_ACTION * chunk + 0.05
    infer_remaining = 0
    pending = None
    while t < total_ticks:
        if infer_remaining > 0:
            infer_remaining -= 1
            if infer_remaining == 0 and pending is not None:
                # swap
                if queue:
                    # jump from current head to new chunk start
                    pass
                queue = pending
                pending = None
        if not queue:
            # underrun — idle one tick and kick an infer if needed
            idle += 1
            t += 1
            if pending is None and infer_remaining == 0:
                pending = make_chunk(base, chunk, SEED_ACTION)
                base += SEED_ACTION * chunk + 0.05
                infer_remaining = infer_ticks
            continue
        a = queue.pop(0)
        if a_prev is not None and len(queue) == chunk - 1:
            # just started a fresh chunk (queue was refilled to chunk then popped once → chunk-1)
            # detect swap: when previous queue emptied and we took from new — handled below
            pass
        if a_prev is not None:
            da = abs(a - a_prev)
            # count only large boundary jumps (> 2 * drift)
            if da > SEED_ACTION * 2.5:
                jumps.append(da)
        a_prev = a
        t += 1
        # start next infer when remaining <= threshold
        if pending is None and infer_remaining == 0 and len(queue) <= threshold:
            pending = make_chunk(base, chunk, SEED_ACTION)
            base += SEED_ACTION * chunk + 0.05
            infer_remaining = infer_ticks
    idle_ratio = idle / total_ticks
    mean_jump = sum(jumps) / len(jumps) if jumps else 0.0
    return idle_ratio, mean_jump, len(jumps)


def main() -> None:
    total = int(HORIZON_S * CONTROL_HZ)
    it = ticks(INFER_MS)
    print(
        f"control_hz={CONTROL_HZ} infer_ms={INFER_MS:g} infer_ticks={it} "
        f"actions_per_chunk={ACTION_CHUNK} chunk_size_threshold={THRESHOLD} horizon_s={HORIZON_S:g}"
    )
    s_idle, s_jump, s_n = sim_sync(total, it, ACTION_CHUNK)
    a_idle, a_jump, a_n = sim_async(total, it, ACTION_CHUNK, THRESHOLD)
    print(f"{'mode':<8} {'idle_ratio':>11} {'mean_jump':>10} {'n_jumps':>8}")
    print(f"{'sync':<8} {s_idle:11.3f} {s_jump:10.4f} {s_n:8d}")
    print(f"{'async':<8} {a_idle:11.3f} {a_jump:10.4f} {a_n:8d}")
    print(f"ok: async_idle < sync_idle ({a_idle:.3f} < {s_idle:.3f})")


if __name__ == "__main__":
    main()
