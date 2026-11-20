#!/usr/bin/env python3
"""ROS 2 executor and callback-group contract, as a discrete-time stand-in.

Synthetic, stdlib only.  Not rclpy / rclcpp, and not a live executor.  Not a redo of
composition, not a redo of QoS Deadline / Lifespan, and not a claim that Multi-Threaded
is always faster.  Real rclpy / rclcpp / composition container: 本页未运行.
Official Jazzy wording 以文档为准:
  spin(node) is a Single-Threaded Executor.
  Currently three executor types: Single-Threaded, Multi-Threaded, Static Single-Threaded.
  Static Single-Threaded is a scan-once variant, not a concurrency variant; it is not an arm.
  The node's default callback group is Mutually Exclusive.
  If everything stays in that default group, the node "essentially acts as if it was
  handled by a Single-Threaded Executor, even if a multi-threaded one is specified".
  Mutually Exclusive: callbacks in the group must not run in parallel.
  Reentrant: callbacks in the group, including two instances of the same callback,
  may run concurrently.
  Callbacks in different groups may always run in parallel.
  A synchronous service call from a callback that shares a Mutually Exclusive group
  with the service server "will always cause a deadlock".
  Outlook names WaitSet and rclc; this stand-in does not invent a fourth executor type.

Discrete integer ticks.  Three callbacks share one timeline:
  a timer that may issue a synchronous service request and then block until it completes;
  a service-handler that advances the pending request;
  a subscription that must keep being serviced.

While a callback is blocked in a synchronous call it still occupies its Mutually
Exclusive group (and one thread).  The handler can run only if a thread is free and
its group allows it.  If the handler cannot run, the request never completes.

Arms:
  A_single       Single-Threaded Executor; every callback in the default Mutually Exclusive group.
  A_mt_default   Multi-Threaded (N_THREADS), everything in the default Mutually Exclusive group.
  B_two_groups   Multi-Threaded; timer in group client (ME), service in group server (ME),
                 subscription in group sub (ME).  Different groups may run in parallel.
  C_shared_me    Multi-Threaded; timer and service (and the subscription) in one shared
                 Mutually Exclusive group that is not the default.  The documented deadlock.

Common random numbers: the event timeline is deterministic and shared across arms.
Five seeds repeat that same schedule so the exact-tie cells can be printed as
"identical on every seed".  Seeds do not add jitter.

Metrics per seed: timer_done (completed timer callbacks), req_done (completed
synchronous requests), sub_done (completed subscription callbacks),
handler_progress (ticks the service handler actually ran), starved_ticks
(subscription messages still queued at the end, plus ticks a due subscription
could not start).

Regimes and expectations, written before the first run:
  no_sync_no_overlap   no synchronous call, no overlapping work: A_single, A_mt_default
                       and B_two_groups exact-tie on timer_done and sub_done (keep)
  overlap_sync         long handler that must overlap a subscription: B consistent
                       better subscription service / lower starved ticks than A (keep);
                       C loses (deadlock / zero progress on the inner handler) (keep)

Named alternative, same timeline, not adopted: Multi-Threaded + one Reentrant group
holding timer, service and subscription (also allows the subscription to run while
the timer is blocked).

No integration step: integer ticks, no plant, every comparison is exact.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared schedule (integer ticks), printed.
N_THREADS = 3
HORIZON = 40
TIMER_PERIOD = 10
TIMER_LOCAL = 1  # ticks of local work before a sync call (or the only work if no call)
SVC_WORK_LONG = 8  # ticks the handler needs for a long synchronous request
SUB_PERIOD = 2
SUB_WORK = 1
# First timer fires at t=TIMER_FIRST; first subscription at t=SUB_FIRST.
TIMER_FIRST = 0
SUB_FIRST = 1

ARMS = ("A_single", "A_mt_default", "B_two_groups", "C_shared_me")
METRICS = ("timer_done", "req_done", "sub_done", "handler_progress", "starved_ticks")

REGIMES = {
    "no_sync_no_overlap": (
        "no_sync_no_overlap",
        "no synchronous call, no overlapping work: A_single, A_mt_default and B_two_groups exact-tie on completed callbacks - keep",
    ),
    "overlap_sync": (
        "overlap_sync",
        "long handler must overlap a subscription: B consistent better sub service / lower starved ticks than A - keep; C loses (deadlock / zero inner-handler progress) - keep",
    ),
}

ALT_REENTRANT = True


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
        return format(Decimal(repr(x)), ".3e")
    s = format(Decimal(repr(x)), ".4f")
    return "0.0000" if s == "-0.0000" else s


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
    elif abs(m) < SMALL_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def arm_config(arm: str) -> dict:
    """threads, group type and group name for timer / service / subscription."""
    default = ("ME", "default")
    if arm == "A_single":
        return {"threads": 1, "timer": default, "service": default, "sub": default}
    if arm == "A_mt_default":
        return {"threads": N_THREADS, "timer": default, "service": default, "sub": default}
    if arm == "B_two_groups":
        return {
            "threads": N_THREADS,
            "timer": ("ME", "client"),
            "service": ("ME", "server"),
            "sub": ("ME", "sub"),
        }
    if arm == "C_shared_me":
        shared = ("ME", "shared")
        return {"threads": N_THREADS, "timer": shared, "service": shared, "sub": shared}
    if arm == "B_reentrant":
        re = ("RE", "reentrant")
        return {"threads": N_THREADS, "timer": re, "service": re, "sub": re}
    raise KeyError(arm)


def run_arm(arm: str, do_sync: bool, svc_work: int) -> dict:
    cfg = arm_config(arm)
    # Each live callback: name, group_kind, group_name, remaining work, blocked_on_req
    # Occupancy: ME group -> callback name currently occupying it (running or blocked).
    # Reentrant groups have no occupancy lock.
    group_of = {
        "timer": cfg["timer"],
        "service": cfg["service"],
        "sub": cfg["sub"],
    }
    n_threads = cfg["threads"]

    next_timer = TIMER_FIRST
    next_sub = SUB_FIRST
    sub_queue = 0
    pending_req_left = 0  # remaining handler work on the open request
    caller_blocked = False
    live = []  # list of dicts

    timer_done = 0
    req_done = 0
    sub_done = 0
    handler_progress = 0
    starved_ticks = 0
    deadlock = 0

    def group_free(name: str) -> bool:
        kind, gname = group_of[name]
        if kind == "RE":
            return True
        return not any(cb["name"] != name and cb["group"] == (kind, gname) for cb in live)

    def can_start(name: str, free_threads: int) -> bool:
        return free_threads > 0 and group_free(name)

    for t in range(HORIZON):
        # Arrivals at the beginning of the tick.
        if t == next_timer:
            # One timer callback at a time: if the previous timer is still blocked, the
            # due event is deferred until that callback returns (the period still advances).
            timer_due = not any(cb["name"] == "timer" for cb in live)
            next_timer += TIMER_PERIOD
        else:
            timer_due = False
        if t == next_sub:
            sub_queue += 1
            next_sub += SUB_PERIOD

        # How many threads are occupied (running or blocked in a sync call).
        # A blocked caller still holds its thread, as a real call() would.
        used = len(live)
        free = n_threads - used

        # Start order: service (so a just-issued request can begin on a second thread
        # in the same tick after the timer is already live), then subscription, then timer.
        # Starts that become legal mid-tick (handler finishing, group released) are
        # handled by a small inner loop.
        progressed = True
        started_this_tick = set()
        while progressed:
            progressed = False
            used = len(live)
            free = n_threads - used
            # Service handler: needs a pending request with work left, and not already live.
            if (
                pending_req_left > 0
                and not any(cb["name"] == "service" for cb in live)
                and can_start("service", free)
            ):
                live.append({
                    "name": "service",
                    "group": group_of["service"],
                    "left": pending_req_left,
                    "blocked": False,
                })
                started_this_tick.add("service")
                progressed = True
                used = len(live)
                free = n_threads - used
            # Subscription.
            if (
                sub_queue > 0
                and not any(cb["name"] == "sub" for cb in live)
                and can_start("sub", free)
            ):
                live.append({
                    "name": "sub",
                    "group": group_of["sub"],
                    "left": SUB_WORK,
                    "blocked": False,
                })
                sub_queue -= 1
                started_this_tick.add("sub")
                progressed = True
                used = len(live)
                free = n_threads - used
            # Timer.
            if (
                timer_due
                and not any(cb["name"] == "timer" for cb in live)
                and can_start("timer", free)
            ):
                live.append({
                    "name": "timer",
                    "group": group_of["timer"],
                    "left": TIMER_LOCAL,
                    "blocked": False,
                    "will_call": do_sync,
                })
                timer_due = False
                started_this_tick.add("timer")
                progressed = True

        # If a subscription is queued but could not start this tick, count a starved tick.
        if sub_queue > 0 and not any(cb["name"] == "sub" for cb in live):
            starved_ticks += 1

        # Run one tick of work on every non-blocked live callback.
        finished = []
        for cb in live:
            if cb["blocked"]:
                continue
            cb["left"] -= 1
            if cb["name"] == "service":
                handler_progress += 1
                pending_req_left -= 1
            if cb["left"] <= 0:
                if cb["name"] == "timer" and cb.get("will_call"):
                    # Issue the synchronous request and block until it completes.
                    cb["will_call"] = False
                    cb["blocked"] = True
                    caller_blocked = True
                    pending_req_left = svc_work
                else:
                    finished.append(cb)

        for cb in finished:
            live.remove(cb)
            if cb["name"] == "timer":
                timer_done += 1
            elif cb["name"] == "sub":
                sub_done += 1
            elif cb["name"] == "service":
                # Request work is finished; unblock the caller if it is waiting.
                if caller_blocked:
                    for other in live:
                        if other["name"] == "timer" and other["blocked"]:
                            other["blocked"] = False
                            other["left"] = 0  # return from call(); completes this tick
                            caller_blocked = False
                            req_done += 1
                            # Timer completes at the tick the handler finishes.
                            # Leave it in live with left=0 so the next pass... we already
                            # finished the service; mark timer done now.
                            live.remove(other)
                            timer_done += 1
                            break

        # Deadlock detector: a blocked caller, a pending request, no way to start the handler
        # for the rest of the horizon if groups/threads never change.  Flag if this state
        # holds at the end, not mid-horizon (the handler may start next tick on another thread).
        if caller_blocked and pending_req_left > 0 and not any(cb["name"] == "service" for cb in live):
            # If the handler is in a group occupied by the blocked caller, it can never start.
            kind, gname = group_of["service"]
            if kind == "ME" and any(cb["blocked"] and cb["group"] == (kind, gname) for cb in live):
                deadlock = 1

    # If we ended still blocked with no handler progress possible, request never completed.
    if caller_blocked and req_done == 0:
        deadlock = 1

    return {
        "timer_done": float(timer_done),
        "req_done": float(req_done),
        "sub_done": float(sub_done),
        "handler_progress": float(handler_progress),
        "starved_ticks": float(starved_ticks),
        "deadlock": float(deadlock),
    }


def col(rows, metric):
    return [row[metric] for row in rows]


def main():
    print("Synthetic executor / callback-group stand-in; not rclpy")
    print(
        f"declared N_THREADS={N_THREADS} HORIZON={HORIZON} TIMER_PERIOD={TIMER_PERIOD} "
        f"TIMER_LOCAL={TIMER_LOCAL} SVC_WORK_LONG={SVC_WORK_LONG} SUB_PERIOD={SUB_PERIOD} "
        f"SUB_WORK={SUB_WORK} TIMER_FIRST={TIMER_FIRST} SUB_FIRST={SUB_FIRST} "
        f"SMALL_FRAC={num(SMALL_FRAC)} seeds={','.join(str(s) for s in SEEDS)}"
    )
    print("hand_calc 20 percent small-vs-clear factor = " + num(SMALL_FRAC))
    print(f"hand_calc ticks in horizon = {HORIZON}")
    print(f"hand_calc subscription arrivals in horizon = {1 + (HORIZON - 1 - SUB_FIRST) // SUB_PERIOD}")
    print(f"hand_calc timer firings in horizon = {1 + (HORIZON - 1 - TIMER_FIRST) // TIMER_PERIOD}")
    print("declared arms: A_single Single-Threaded + default ME; A_mt_default Multi-Threaded + default ME; "
          "B_two_groups Multi-Threaded + three ME groups; C_shared_me Multi-Threaded + one shared ME group")
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: deterministic shared timeline; seeds repeat the same schedule")
    print("Assumptions: discrete integer ticks; a blocked synchronous caller occupies its ME group and one thread")
    print("Official executor types, default group, and deadlock wording 以文档为准")
    print("Real rclpy / rclcpp / composition container: 本页未运行")
    for name, (_kind, expl) in REGIMES.items():
        print(f"declared {name}: {expl}")

    setups = {
        "no_sync_no_overlap": {"do_sync": False, "svc_work": 0},
        "overlap_sync": {"do_sync": True, "svc_work": SVC_WORK_LONG},
    }
    for name, setup in setups.items():
        expl = REGIMES[name][1]
        print(f"declared expectation {name}: {expl}")
        print(f"regime {name}  (mean+-sd over seeds; deterministic schedule)")
        rows = {arm: [] for arm in ARMS}
        for seed in SEEDS:
            # Seed is recorded but does not change the deterministic timeline.
            _ = seed
            for arm in ARMS:
                rec = run_arm(arm, setup["do_sync"], setup["svc_work"])
                rows[arm].append(rec)
        # Print one representative seed (they are identical) then means.
        print(f"  seed 0 (all {len(SEEDS)} seeds identical):")
        for arm in ARMS:
            rec = rows[arm][0]
            print(
                f"    {arm}: timer_done={num(rec['timer_done'])} req_done={num(rec['req_done'])} "
                f"sub_done={num(rec['sub_done'])} handler_progress={num(rec['handler_progress'])} "
                f"starved_ticks={num(rec['starved_ticks'])} deadlock={num(rec['deadlock'])}"
            )
        for arm in ARMS:
            for metric in METRICS + ("deadlock",):
                xs = col(rows[arm], metric)
                print(f"  {arm} {metric} {fmt_pair(*mean_sd(xs))}")
        for metric in METRICS + ("deadlock",):
            print(f"  paired A_mt_default-A_single {metric}: {verdict(col(rows['A_mt_default'], metric), col(rows['A_single'], metric))}")
            print(f"  paired B-A_single {metric}: {verdict(col(rows['B_two_groups'], metric), col(rows['A_single'], metric))}")
            print(f"  paired B-A_mt_default {metric}: {verdict(col(rows['B_two_groups'], metric), col(rows['A_mt_default'], metric))}")
            print(f"  paired C-B {metric}: {verdict(col(rows['C_shared_me'], metric), col(rows['B_two_groups'], metric))}")
            print(f"  paired C-A_mt_default {metric}: {verdict(col(rows['C_shared_me'], metric), col(rows['A_mt_default'], metric))}")

    print("named alternative B_reentrant (Multi-Threaded + one Reentrant group) - not adopted")
    for name, setup in setups.items():
        alt = []
        base = []
        for seed in SEEDS:
            _ = seed
            alt.append(run_arm("B_reentrant", setup["do_sync"], setup["svc_work"]))
            base.append(run_arm("B_two_groups", setup["do_sync"], setup["svc_work"]))
        print(f"  alt {name}:")
        rec = alt[0]
        print(
            f"    timer_done={num(rec['timer_done'])} req_done={num(rec['req_done'])} "
            f"sub_done={num(rec['sub_done'])} handler_progress={num(rec['handler_progress'])} "
            f"starved_ticks={num(rec['starved_ticks'])} deadlock={num(rec['deadlock'])}"
        )
        for metric in METRICS:
            print(f"    paired alt-B_two_groups {metric}: {verdict(col(alt, metric), col(base, metric))}")
    print("no integration step: integer ticks, no plant, no step-size criterion")
    print("No winner declared")


if __name__ == "__main__":
    main()
