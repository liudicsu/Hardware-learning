#!/usr/bin/env python3
"""dual_system_vla_cadence_toy.py: slow planner / fast controller vs single-rate arms (stdlib).

Synthetic 2-D reaching: two moving targets (red, blue); the instruction says
which one to follow and switches from "red" to "blue" at a random tick.
A second scenario holds both targets still and never switches (scored over the
same tick window), to show when a single-rate arm loses nothing. Control
runs at 50 ticks/s for 300 ticks. Compute is counted in units; every arm gets
the SAME 1.0 unit per tick on average, the SAME targets, perception noise and
switch times (common random numbers per seed), the SAME speed limit and gain.
What each arm sees:
  A slow_single   big model (instruction + image) every 10 ticks, 10 units/call,
                  result after 10 ticks of latency; action held in between
  B fast_single   small model (image only) every tick, 1 unit/call; the goal is
                  the instruction parsed once at t=0 (that parse is not charged)
                  and never refreshed
  C dual_rt       System 2 (instruction + image) every 20 ticks, 10 units/call,
                  10-tick latency -> goal = which target; System 1 every tick,
                  0.5 units, uses the latest goal AND the current image
  D dual_no_rt    like C, but System 1 only gets System 2's target snapshot,
                  no current image (fails OpenHelix's real-time criterion)
Not a VLA, not trained, no GPU. Numbers depend on the lesson-chosen rates.
usage: python3 dual_system_vla_cadence_toy.py
"""
from __future__ import annotations

import math
import random
import statistics

SEEDS = (0, 1, 2, 3, 4, 5, 6, 7)
TICKS = 300
HZ = 50
VMAX = 0.02            # max move per tick
GAIN = 0.3
PERC = 0.005           # perception noise on target positions
REACH = 0.05           # "on target" radius
COST = {"A": (10, 10.0, 0.0), "B": (1, 1.0, 0.0), "C": (20, 10.0, 0.5), "D": (20, 10.0, 0.5)}
LATENCY = 10           # ticks for a big-model call (A, and System 2 in C/D)
ARMS = {"A": "slow_single", "B": "fast_single", "C": "dual_rt", "D": "dual_no_rt"}


def targets(t, phase, moving=True):
    w = 2 * math.pi * 0.25 / HZ * t if moving else 0.0
    red = (0.5 + 0.25 * math.cos(w + phase), 0.5 + 0.25 * math.sin(w + phase))
    blue = (0.5 - 0.25 * math.cos(1.3 * w + phase), 0.5 + 0.20 * math.sin(1.3 * w))
    return {"red": red, "blue": blue}


def step_to(p, goal):
    dx, dy = GAIN * (goal[0] - p[0]), GAIN * (goal[1] - p[1])
    n = math.hypot(dx, dy)
    if n > VMAX:
        dx, dy = dx * VMAX / n, dy * VMAX / n
    return (p[0] + dx, p[1] + dy)


def episode(arm, seed, scenario="moving_switch"):
    rng = random.Random(seed)
    switch = rng.randint(100, 200)
    moving = scenario == "moving_switch"
    score_from = switch
    if not moving:  # static targets, no instruction switch; score the same window
        switch = TICKS + 1
    phase = rng.uniform(0, 2 * math.pi)
    noise = [(rng.gauss(0, PERC), rng.gauss(0, PERC), rng.gauss(0, PERC), rng.gauss(0, PERC)) for _ in range(TICKS)]
    every, big, small = COST[arm]

    def seen(t):  # noisy image at tick t (shared draws)
        tg, n = targets(t, phase, moving), noise[t]
        return {"red": (tg["red"][0] + n[0], tg["red"][1] + n[1]), "blue": (tg["blue"][0] + n[2], tg["blue"][1] + n[3])}

    def instr(t):
        return "red" if t < switch else "blue"

    p = (0.5, 0.5)
    compute = 0.0
    held = None            # A: held action target
    goal_name, goal_snap, goal_age_t = "red", seen(0)["red"], 0
    pending = []           # (ready_tick, payload)
    err, fresh, ages, reached = [], 0, [], None
    for t in range(TICKS):
        if t % every == 0 and arm != "B":
            compute += big
            obs = seen(t)
            pending.append((t + LATENCY, (instr(t), obs[instr(t)], t)))
        if arm == "B":
            compute += big
        for item in [x for x in pending if x[0] <= t]:
            pending.remove(item)
            goal_name, goal_snap, goal_age_t = item[1]
            held = goal_snap
            if arm == "A":
                fresh += 1
        now = seen(t)
        if arm == "A":
            target = held if held is not None else p
            age = t - goal_age_t
        elif arm == "B":
            target, age = now["red"], 0     # instruction parsed once at t=0
            fresh += 1
        else:
            compute += small
            fresh += 1
            target = now[goal_name] if arm == "C" else goal_snap
            age = t - goal_age_t
        p = step_to(p, target)
        true = targets(t + 1, phase, moving)[instr(t)]
        d = math.hypot(p[0] - true[0], p[1] - true[1])
        if t >= score_from:
            err.append(d)
            if reached is None and d < REACH:
                reached = t - score_from
        ages.append(age)
    follow = sum(e < REACH for e in err) / len(err)
    return {"rmse": math.sqrt(statistics.mean(e * e for e in err)), "follow": follow,
            "react": reached if reached is not None else TICKS - score_from, "miss": reached is None,
            "underrun": 1 - fresh / TICKS, "age": statistics.mean(ages), "unit": compute / TICKS}


def ms(v, f):
    return f"{statistics.mean(v):{f}}±{statistics.pstdev(v):{f}}"


def main():
    print(f"Synthetic cadence: {TICKS} ticks at {HZ} Hz, {len(SEEDS)} seeds (switch tick 100..200), "
          f"big call latency {LATENCY} ticks, vmax {VMAX}/tick, reach {REACH}")
    for scenario in ("moving_switch", "static_no_switch"):
        print(f"[{scenario}] arm units/tick rmse on_target_frac react_ticks never_reached underrun goal_age_ticks")
        for arm, name in ARMS.items():
            rs = [episode(arm, s, scenario) for s in SEEDS]
            print(f"{arm}_{name} {ms([r['unit'] for r in rs], '.2f')} {ms([r['rmse'] for r in rs], '.3f')} "
                  f"{ms([r['follow'] for r in rs], '.2f')} {ms([r['react'] for r in rs], '.1f')} "
                  f"{sum(r['miss'] for r in rs)}/{len(SEEDS)} {ms([r['underrun'] for r in rs], '.2f')} "
                  f"{ms([r['age'] for r in rs], '.1f')}")
    print("Same targets, noise, switch ticks and compute per tick; what each arm sees differs and is declared.")
    print("No winner is declared; real VLA weights, GPUs and robots: 本页未运行.")


if __name__ == "__main__":
    main()
