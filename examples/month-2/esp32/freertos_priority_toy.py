#!/usr/bin/env python3
"""freertos_priority_toy.py: priority inversion with a medium task (stdlib).

Single-core fixed-priority preemptive scheduler in FreeRTOS numbering
(higher numeric priority runs first; tskIDLE_PRIORITY = 0 is lowest).
ESP-IDF FreeRTOS is an SMP dual-core variant with core affinity; this toy
is deliberately single-core so the inversion story is visible without SMP
scheduling. Real FreeRTOS on ESP32 and Zephyr builds are 本页未运行.

Three tasks share one mutex-guarded critical section:
  low     (prio 1)  logging — takes the mutex for a long stretch
  medium  (prio 2)  background — never takes the mutex
  high    (prio 3)  control — needs the mutex briefly each period

Unbounded inversion needs the medium task: without it, when high blocks on
the mutex held by low, low keeps the CPU (nothing else is ready at a higher
priority than low among non-blocked tasks), so high's wait is just low's
remaining critical-section time. With medium ready, medium preempts low and
high stays blocked for an unbounded medium stretch.

Arms (shared arrival noise):
  no_inheritance  lock is a binary-semaphore stand-in: no priority boost
  inheritance     lock is a mutex stand-in: holder inherits waiter's priority

FreeRTOS fact (kernel semphr.h): xSemaphoreCreateMutex() implements priority
inheritance; xSemaphoreCreateBinary() does not — using a binary semaphore as
a mutual-exclusion lock is the classic bug. Inheritance BOUNDS blocking by
the medium task; it does not eliminate the wait for the low task to finish
its critical section (no priority-ceiling claim here).

Zephyr polarity (prose only, docs.zephyrproject.org threads): lower number =
higher priority; negative priorities are cooperative. Toy stays FreeRTOS
numbering.

Metrics: high-task deadline misses; max inversion wait (ticks high spent
blocked while a medium ran).
usage: python3 freertos_priority_toy.py
"""
from __future__ import annotations

import random

SEED = 42
HORIZON = 400          # scheduler ticks
DT_MS = 1              # one tick = 1 ms of simulated time

# FreeRTOS-style priorities: higher number = higher priority.
P_LOW, P_MED, P_HIGH = 1, 2, 3

# Workloads (ticks of CPU needed per job).
LOW_CS = 18            # low's critical-section length while holding the lock
LOW_PERIOD = 80
MED_BURST = 12         # medium CPU burst (no lock)
MED_PERIOD = 25
HIGH_CS = 3            # high's short critical section
HIGH_PERIOD = 20
HIGH_DEADLINE = 20     # miss if response > this many ticks from release

# Shared arrival jitter (±ticks) applied identically to both arms.
ARRIVAL_JITTER = 2


class Scheduler:
    """Tiny single-core preemptive FP scheduler with one lock."""

    def __init__(self, inherit: bool, arrivals: list[tuple[int, int, int]]) -> None:
        self.inherit = inherit
        self.arrivals = arrivals  # (low_rel, med_rel, high_rel) jitter per period index
        self.lock_holder: str | None = None
        self.lock_waiters: list[str] = []
        # base priority / effective priority
        self.base = {"low": P_LOW, "medium": P_MED, "high": P_HIGH}
        self.eff = dict(self.base)
        self.ready: dict[str, int] = {}          # task -> remaining CPU this job
        self.blocked: set[str] = set()
        self.release_at = {"low": 0, "medium": 0, "high": 0}
        self.period_i = {"low": 0, "medium": 0, "high": 0}
        self.high_release_tick: int | None = None
        self.deadline_misses = 0
        self.max_inv_wait = 0
        self.cur_inv_wait = 0
        self.max_lock_wait = 0
        self.cur_lock_wait = 0
        self.high_jobs = 0
        self.high_responses: list[int] = []
        self.holding_cs_left = 0  # remaining CS work while holding lock

    def _prio(self, name: str) -> int:
        return self.eff[name]

    def _boost(self) -> None:
        """Priority inheritance: holder gets max(own, waiters' base)."""
        if not self.inherit or self.lock_holder is None:
            return
        holder = self.lock_holder
        boost = self.base[holder]
        for w in self.lock_waiters:
            boost = max(boost, self.base[w])
        self.eff[holder] = boost

    def _drop_boost(self) -> None:
        if self.lock_holder is None:
            self.eff = dict(self.base)
            return
        # reset non-holders; re-compute holder
        for n in self.eff:
            if n != self.lock_holder:
                self.eff[n] = self.base[n]
        self._boost()

    def _try_release(self, t: int) -> None:
        for name, period, work in (
            ("low", LOW_PERIOD, LOW_CS),
            ("medium", MED_PERIOD, MED_BURST),
            ("high", HIGH_PERIOD, HIGH_CS),
        ):
            if t < self.release_at[name]:
                continue
            if name in self.ready or name in self.blocked or name == self.lock_holder:
                # still running previous job; skip this release (overload)
                self.release_at[name] = t + period
                self.period_i[name] += 1
                continue
            # apply shared arrival jitter
            pi = self.period_i[name]
            jitter_triple = self.arrivals[pi % len(self.arrivals)]
            jitter = {"low": jitter_triple[0], "medium": jitter_triple[1],
                      "high": jitter_triple[2]}[name]
            # release now (jitter already baked into precomputed arrival offsets
            # relative to nominal; we just start the job)
            self.ready[name] = work
            if name == "high":
                self.high_release_tick = t
                self.high_jobs += 1
            self.release_at[name] = t + period + jitter
            self.period_i[name] += 1
            _ = jitter  # jitter shifts next release; first release at 0

    def _take_lock(self, name: str) -> bool:
        if self.lock_holder is None:
            self.lock_holder = name
            self.holding_cs_left = self.ready[name]
            self._boost()
            return True
        if self.lock_holder == name:
            return True
        # must wait
        if name not in self.lock_waiters:
            self.lock_waiters.append(name)
        self.blocked.add(name)
        if name in self.ready:
            # keep remaining work recorded in ready? move to blocked
            pass
        self._boost()
        return False

    def _give_lock(self) -> None:
        self.lock_holder = None
        self.holding_cs_left = 0
        # wake waiters in priority order
        self.lock_waiters.sort(key=lambda n: -self.base[n])
        woken = []
        while self.lock_waiters:
            w = self.lock_waiters.pop(0)
            self.blocked.discard(w)
            woken.append(w)
            # highest waiter takes the lock immediately
            self.lock_holder = w
            self.holding_cs_left = self.ready.get(w, HIGH_CS)
            break
        self._drop_boost()
        self._boost()

    def _pick(self) -> str | None:
        candidates = []
        for name, rem in self.ready.items():
            if rem <= 0:
                continue
            if name in self.blocked:
                continue
            # if someone else holds the lock and this task needs it:
            # low and high need the lock for their whole job in this toy;
            # medium never needs it.
            if name in ("low", "high"):
                if self.lock_holder is not None and self.lock_holder != name:
                    # try to take (will block)
                    if not self._take_lock(name):
                        continue
                elif self.lock_holder is None:
                    if not self._take_lock(name):
                        continue
            candidates.append(name)
        if not candidates:
            return None
        # highest effective priority wins; stable by name for ties
        candidates.sort(key=lambda n: (-self._prio(n), n))
        return candidates[0]

    def run(self) -> dict:
        for t in range(HORIZON):
            self._try_release(t)
            # inversion wait = high blocked WHILE medium runs (unbounded w/o PI)
            # lock wait = any tick high spends blocked on the lock (bounded by low CS under PI)
            high_blocked = "high" in self.blocked
            running = self._pick()
            # re-read blocked after _pick (which may have blocked high)
            high_blocked = "high" in self.blocked
            if high_blocked:
                self.cur_lock_wait += 1
                self.max_lock_wait = max(self.max_lock_wait, self.cur_lock_wait)
                if running == "medium":
                    self.cur_inv_wait += 1
                    self.max_inv_wait = max(self.max_inv_wait, self.cur_inv_wait)
                else:
                    self.cur_inv_wait = 0
            else:
                self.cur_inv_wait = 0
                self.cur_lock_wait = 0

            if running is None:
                continue

            # execute one tick
            self.ready[running] -= 1
            if running == self.lock_holder:
                self.holding_cs_left -= 1

            if self.ready[running] <= 0:
                # job done
                if running == "high" and self.high_release_tick is not None:
                    resp = t - self.high_release_tick + 1
                    self.high_responses.append(resp)
                    if resp > HIGH_DEADLINE:
                        self.deadline_misses += 1
                    self.high_release_tick = None
                if running == self.lock_holder:
                    self._give_lock()
                del self.ready[running]

        return {
            "arm": "inheritance" if self.inherit else "no_inheritance",
            "deadline_misses": self.deadline_misses,
            "high_jobs": self.high_jobs,
            "max_inversion_wait_ticks": self.max_inv_wait,
            "max_inversion_wait_ms": self.max_inv_wait * DT_MS,
            "max_lock_wait_ticks": self.max_lock_wait,
            "mean_high_response_ticks": (
                sum(self.high_responses) / len(self.high_responses)
                if self.high_responses else 0.0),
        }


def shared_arrivals() -> list[tuple[int, int, int]]:
    rng = random.Random(SEED)
    # enough for HORIZON / min_period
    n = HORIZON // 10 + 5
    out = []
    for _ in range(n):
        out.append((
            rng.randint(-ARRIVAL_JITTER, ARRIVAL_JITTER),
            rng.randint(-ARRIVAL_JITTER, ARRIVAL_JITTER),
            rng.randint(-ARRIVAL_JITTER, ARRIVAL_JITTER),
        ))
    return out


def main() -> None:
    arrivals = shared_arrivals()
    rows = []
    for inherit in (False, True):
        rows.append(Scheduler(inherit, arrivals).run())

    print(f"seed={SEED} horizon={HORIZON} tick={DT_MS}ms single_core=1")
    print("priorities FreeRTOS-style: low=1 medium=2 high=3 (higher number runs first)")
    print(f"workloads: low_CS={LOW_CS} med_burst={MED_BURST} high_CS={HIGH_CS} "
          f"periods L/M/H={LOW_PERIOD}/{MED_PERIOD}/{HIGH_PERIOD}")
    print("lock: no_inheritance = binary-semaphore stand-in (no PI); "
          "inheritance = mutex stand-in (PI)")
    print("inversion needs medium: medium preempts lock-holding low while high blocks")
    print(f"{'arm':<16} {'deadline_misses':>15} {'high_jobs':>9} "
          f"{'max_inv_wait':>12} {'max_lock_wait':>13} {'mean_high_resp':>14}")
    for r in rows:
        print(f"{r['arm']:<16} {r['deadline_misses']:15d} {r['high_jobs']:9d} "
              f"{r['max_inversion_wait_ticks']:12d} {r['max_lock_wait_ticks']:13d} "
              f"{r['mean_high_response_ticks']:14.2f}")

    no, yes = rows[0], rows[1]
    assert no["max_inversion_wait_ticks"] > yes["max_inversion_wait_ticks"], (
        "inheritance should cut medium-driven inversion wait")
    assert no["max_inversion_wait_ticks"] > 0, "medium must create visible inversion"
    assert yes["max_lock_wait_ticks"] > 0, (
        "PI bounds but does not eliminate lock wait (low still finishes CS)")
    assert yes["max_lock_wait_ticks"] <= LOW_CS, "PI lock wait bounded by low CS length"
    assert no["deadline_misses"] >= yes["deadline_misses"], (
        "inheritance should not increase deadline misses")
    print("ok: medium-driven inversion; mutex PI bounds medium wait but lock wait "
          f"remains (PI max_lock_wait={yes['max_lock_wait_ticks']}<=low_CS={LOW_CS}); "
          "binary semaphore has no PI (FreeRTOS-Kernel semphr.h); "
          "ESP-IDF SMP dual-core 本页未运行; Zephyr polarity prose-only")


if __name__ == "__main__":
    main()
