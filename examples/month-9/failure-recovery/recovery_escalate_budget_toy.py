#!/usr/bin/env python3
"""recovery_escalate_budget_toy.py: infinite retry vs Retry+Fallback vs escalation ladder.

Synthetic, stdlib only. One shared task stream per seed: every task has a
hidden failure case and pre-drawn outcomes (common random numbers), so all
three arms see the SAME failures and the SAME detect signal (a post-grasp
"object in gripper" check, assumed correct here). Arms differ only in policy:
  A infinite_retry      retry the primary grasp until the episode deadline
  B retry_fallback      Retry(primary, 2) -> backup grasp once -> FAILURE
  C escalate_ladder     detect -> Retry(primary, 2) -> backup once -> human
                        handoff (if operator budget left) -> abort
Explicit rung costs (seconds of robot time, operator minutes) are toy values.
unsafe_retry = any attempt of a skill that has already failed RISK_AFTER times
in this task (a stand-in for "repeating a failed grasp into the same clutter").
usage: python3 recovery_escalate_budget_toy.py
"""
from __future__ import annotations

import json
import random
import statistics

SEEDS = (0, 1, 2, 3, 4)
TASKS = 40
# Hidden case mix (probabilities) and per-attempt success probabilities.
CASES = (("transient", 0.50), ("primary_blocked", 0.25), ("needs_human", 0.15), ("unrecoverable", 0.10))
P_SUCCESS = {  # case -> (primary, backup, human)
    "transient": (0.6, 0.6, 0.95),
    "primary_blocked": (0.0, 0.7, 0.95),
    "needs_human": (0.0, 0.0, 0.90),
    "unrecoverable": (0.0, 0.0, 0.00),
}
COST_S = {"detect": 1.0, "primary": 8.0, "backup": 12.0, "handoff_wait": 45.0, "abort": 5.0}
OPERATOR_MIN = 1.5      # operator minutes per handoff
DEADLINE_S = 120.0      # per-task episode bookkeeping deadline (not a watchdog)
RETRY_CAP = 2
RISK_AFTER = 3
OPERATOR_BUDGET = 6     # handoffs allowed per 40-task stream (arm C)
MAX_DRAWS = 40          # pre-drawn uniforms per skill per task
ARMS = ("A_infinite_retry", "B_retry_fallback", "C_escalate_ladder")


def make_stream(seed):
    rng = random.Random(seed)
    stream = []
    for i in range(TASKS):
        r, acc, case = rng.random(), 0.0, CASES[-1][0]
        for name, p in CASES:
            acc += p
            if r < acc:
                case = name
                break
        draws = {k: [rng.random() for _ in range(MAX_DRAWS)] for k in ("primary", "backup", "human")}
        stream.append({"id": i, "case": case, "draws": draws})
    return stream


def attempt(task, skill, n):
    p = P_SUCCESS[task["case"]][("primary", "backup", "human").index(skill)]
    return task["draws"][skill][n] < p


def run_task(arm, task, ops_left):
    t, tried, fails = 0.0, [], {"primary": 0, "backup": 0}
    out = {"success": False, "operator_calls": 0, "unsafe": 0, "livelock": False,
           "aborted": False, "handoff": None}

    def try_skill(skill):
        nonlocal t
        if fails[skill] >= RISK_AFTER:
            out["unsafe"] += 1
        n = fails[skill]
        t += COST_S[skill] + COST_S["detect"]
        tried.append(skill)
        ok = attempt(task, skill, n)
        if not ok:
            fails[skill] += 1
        return ok

    if arm == "A_infinite_retry":
        while t + COST_S["primary"] + COST_S["detect"] <= DEADLINE_S:
            if try_skill("primary"):
                out["success"] = True
                break
        else:
            out["livelock"] = True
        out["time"] = t
        return out
    for _ in range(RETRY_CAP):
        if try_skill("primary"):
            out["success"] = True
            out["time"] = t
            return out
    if try_skill("backup"):
        out["success"] = True
        out["time"] = t
        return out
    if arm == "C_escalate_ladder" and ops_left > 0:
        out["operator_calls"] = 1
        out["handoff"] = {
            "escalate_reason": "retry_cap_and_backup_exhausted",
            "last_obs_summary": f"task {task['id']}: gripper empty after {len(tried)} attempts",
            "attempted_skills": list(tried),
        }
        t += COST_S["handoff_wait"]
        if attempt(task, "human", 0):
            out["success"] = True
            out["time"] = t
            return out
    t += COST_S["abort"]
    out["aborted"] = True
    out["time"] = t
    return out


def run_stream(arm, seed, budget=OPERATOR_BUDGET):
    ops_left = budget
    tot = {"success": 0, "operator_calls": 0, "unsafe": 0, "livelock": 0, "aborted": 0,
           "makespan_s": 0.0, "auto_success": 0, "budget_exhausted_aborts": 0,
           "handoff_failed": 0}
    first_handoff = None
    for task in make_stream(seed):
        exhausted = arm == "C_escalate_ladder" and ops_left == 0
        r = run_task(arm, task, ops_left)
        ops_left -= r["operator_calls"]
        tot["success"] += r["success"]
        tot["auto_success"] += r["success"] and not r["operator_calls"]
        tot["operator_calls"] += r["operator_calls"]
        tot["handoff_failed"] += r["operator_calls"] and not r["success"]
        tot["unsafe"] += r["unsafe"]
        tot["livelock"] += r["livelock"]
        tot["aborted"] += r["aborted"]
        tot["budget_exhausted_aborts"] += exhausted and r["aborted"]
        tot["makespan_s"] += r["time"]
        if r["handoff"] and first_handoff is None:
            first_handoff = r["handoff"]
    return tot, first_handoff


def ms(vals, f=".1f"):
    return f"{statistics.mean(vals):{f}}±{statistics.pstdev(vals):{f}}"


def main():
    print(f"Synthetic stream: {TASKS} tasks x {len(SEEDS)} seeds; cases {dict(CASES)}")
    print(f"Rung costs s: {COST_S}; operator {OPERATOR_MIN} min/handoff; "
          f"retry_cap={RETRY_CAP} risk_after={RISK_AFTER} deadline={DEADLINE_S}s operator_budget={OPERATOR_BUDGET}")
    cases = [sum(t["case"] == c for t in make_stream(s)) for s in SEEDS for c, _ in CASES]
    print("case counts per seed:", [cases[i:i + 4] for i in range(0, len(cases), 4)])
    print("arm success auto_success operator_calls operator_min unsafe_retry livelock aborted budget_exhausted_aborts makespan_s")
    sample = None
    for arm in ARMS:
        rows = [run_stream(arm, s) for s in SEEDS]
        if arm == "C_escalate_ladder":
            sample = rows[0][1]
        t = [r[0] for r in rows]
        print(arm, ms([x["success"] for x in t]), ms([x["auto_success"] for x in t]),
              ms([x["operator_calls"] for x in t]), ms([x["operator_calls"] * OPERATOR_MIN for x in t]),
              ms([x["unsafe"] for x in t]), ms([x["livelock"] for x in t]), ms([x["aborted"] for x in t]),
              ms([x["budget_exhausted_aborts"] for x in t]), ms([x["makespan_s"] for x in t], ".0f"))
    for b in (0, 6, 20):
        t = [run_stream("C_escalate_ladder", s, b)[0] for s in SEEDS]
        print(f"C operator_budget={b}: success {ms([x['success'] for x in t])} operator_calls "
              f"{ms([x['operator_calls'] for x in t])} handoff_failed {ms([x['handoff_failed'] for x in t])} "
              f"makespan_s {ms([x['makespan_s'] for x in t], '.0f')}")
    print("first handoff record (seed 0):", json.dumps(sample, sort_keys=True))
    print("Same stream, outcomes and detect signal for every arm; no winner is declared.")


if __name__ == "__main__":
    main()
