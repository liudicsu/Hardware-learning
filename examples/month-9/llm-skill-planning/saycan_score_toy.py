#!/usr/bin/env python3
"""saycan_score_toy.py: SayCan-style skill selection with a fake LLM (stdlib).

NO paid API. Deterministic lookup tables stand in for LLM usefulness scores and
scene affordances. For each of five instructions, select a skill sequence by
argmax(usefulness × affordance) until 'done', then contrast the same loop with
affordance forced to 1.0 (which can pick infeasible skills like 'pick vacuum').

Pinned tables keep expected/ stable. Keys never enter the repo.
usage: python3 saycan_score_toy.py
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# Closed skill table — LLM may only propose these names.
SKILLS: List[str] = [
    "find apple",
    "pick apple",
    "find coke",
    "pick coke",
    "pick vacuum",  # present in skill table but NOT in this scene
    "go to table",
    "place on table",
    "done",
]

# Scene affordance in [0, 1]: what the robot can actually do *now*.
# Vacuum is absent → affordance 0 (SayCan world grounding).
AFFORDANCE: Dict[str, float] = {
    "find apple": 1.0,
    "pick apple": 0.9,  # apple visible / graspable
    "find coke": 1.0,
    "pick coke": 0.85,
    "pick vacuum": 0.0,  # infeasible in this scene
    "go to table": 1.0,
    "place on table": 0.95,
    "done": 1.0,
}

# Fake LLM usefulness p(skill | instruction, history_tail).
# Keys: (instruction_id, last_skill_or_START, skill) → score in (0, 1].
# Only the scores that matter for the five demos are listed; others default low.
LLM_SCORES: Dict[Tuple[str, str, str], float] = {}


def _put(instr: str, hist: str, skill: str, score: float) -> None:
    LLM_SCORES[(instr, hist, skill)] = score


# --- instruction A: "bring me the apple" ---
# Good plan: find apple → pick apple → go to table → place on table → done
A = "bring me the apple"
_put(A, "START", "find apple", 0.92)
_put(A, "START", "pick apple", 0.70)
_put(A, "START", "pick vacuum", 0.55)  # LLM may invent; affordance kills it
_put(A, "START", "go to table", 0.20)
_put(A, "START", "done", 0.05)
_put(A, "find apple", "pick apple", 0.95)
_put(A, "find apple", "pick vacuum", 0.40)
_put(A, "find apple", "done", 0.05)
_put(A, "pick apple", "go to table", 0.90)
_put(A, "pick apple", "place on table", 0.50)
_put(A, "pick apple", "done", 0.05)
_put(A, "go to table", "place on table", 0.93)
_put(A, "go to table", "done", 0.05)
_put(A, "place on table", "done", 0.99)

# --- instruction B: "bring me a drink" (coke path) ---
B = "bring me a drink"
_put(B, "START", "find coke", 0.88)
_put(B, "START", "pick coke", 0.60)
_put(B, "START", "pick vacuum", 0.50)
_put(B, "START", "done", 0.05)
_put(B, "find coke", "pick coke", 0.94)
_put(B, "find coke", "pick vacuum", 0.35)
_put(B, "pick coke", "go to table", 0.91)
_put(B, "go to table", "place on table", 0.92)
_put(B, "place on table", "done", 0.99)

# --- instruction C: "clean the floor with the vacuum" ---
# Without affordance the fake LLM eagerly picks 'pick vacuum'; with aff → blocked,
# so 'done' wins (nothing feasible to execute — world grounding).
C = "clean the floor with the vacuum"
_put(C, "START", "pick vacuum", 0.97)
_put(C, "START", "find apple", 0.05)
_put(C, "START", "pick apple", 0.05)
_put(C, "START", "go to table", 0.05)
_put(C, "START", "done", 0.20)  # honest stop when vacuum is unavailable
_put(C, "pick vacuum", "done", 0.95)

# --- instruction D: "put the apple on the table" (already holding? start mid-plan) ---
D = "put the apple on the table"
_put(D, "START", "go to table", 0.85)
_put(D, "START", "place on table", 0.70)
_put(D, "START", "pick apple", 0.55)
_put(D, "START", "pick vacuum", 0.30)
_put(D, "START", "done", 0.05)
_put(D, "go to table", "place on table", 0.96)
_put(D, "place on table", "done", 0.99)
_put(D, "pick apple", "go to table", 0.90)

# --- instruction E: "I'm done, stop" ---
E = "I'm done, stop"
_put(E, "START", "done", 0.99)
_put(E, "START", "pick apple", 0.05)
_put(E, "START", "pick vacuum", 0.05)

INSTRUCTIONS = [A, B, C, D, E]
DEFAULT_LLM = 0.02
MAX_STEPS = 8


def llm_score(instr: str, hist: str, skill: str) -> float:
    return LLM_SCORES.get((instr, hist, skill), DEFAULT_LLM)


def select_sequence(
    instr: str, use_affordance: bool
) -> Tuple[List[str], List[Tuple[str, float, float, float]]]:
    """Return (skill_names, debug rows of skill,u,a,combined at each pick)."""
    plan: List[str] = []
    debug: List[Tuple[str, float, float, float]] = []
    hist = "START"
    for _ in range(MAX_STEPS):
        best_skill = None
        best_comb = -1.0
        best_u = 0.0
        best_a = 0.0
        for skill in SKILLS:
            u = llm_score(instr, hist, skill)
            a = AFFORDANCE[skill] if use_affordance else 1.0
            comb = u * a
            if comb > best_comb:
                best_comb = comb
                best_skill = skill
                best_u = u
                best_a = a
        assert best_skill is not None
        debug.append((best_skill, best_u, best_a, best_comb))
        plan.append(best_skill)
        if best_skill == "done":
            break
        hist = best_skill
    return plan, debug


def fmt_plan(plan: List[str]) -> str:
    return " -> ".join(plan)


def main() -> None:
    print(
        f"skills={len(SKILLS)} instructions={len(INSTRUCTIONS)} "
        f"affordance_pick_vacuum={AFFORDANCE['pick vacuum']} "
        f"fake_llm=lookup (no API)"
    )
    print("--- with affordance ---")
    for instr in INSTRUCTIONS:
        plan, _ = select_sequence(instr, use_affordance=True)
        print(f"instr={instr!r}")
        print(f"  plan: {fmt_plan(plan)}")
    print("--- without affordance ---")
    vacuum_picked = False
    for instr in INSTRUCTIONS:
        plan, _ = select_sequence(instr, use_affordance=False)
        if "pick vacuum" in plan:
            vacuum_picked = True
        print(f"instr={instr!r}")
        print(f"  plan: {fmt_plan(plan)}")
    # Spotlight instruction C contrast
    plan_aff, _ = select_sequence(C, use_affordance=True)
    plan_raw, _ = select_sequence(C, use_affordance=False)
    print("--- contrast instr=clean the floor with the vacuum ---")
    print(f"with_affordance:    {fmt_plan(plan_aff)}")
    print(f"without_affordance: {fmt_plan(plan_raw)}")
    print(
        f"ok: without_affordance_picks_vacuum={('pick vacuum' in plan_raw)} "
        f"with_affordance_blocks_vacuum={('pick vacuum' not in plan_aff)} "
        f"any_without_vacuum={vacuum_picked}"
    )


if __name__ == "__main__":
    main()
