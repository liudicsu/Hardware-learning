#!/usr/bin/env python3
"""recovery_bt_toy.py: mini behaviour tree with grasp retry + fallback (stdlib).

Tree (tick until SUCCESS or root FAILURE):
  Fallback(root)
    Sequence(primary)
      Retry(n=2) → Action(GraspPrimary)   # fails twice, then would fail
      Action(Lift)
    Sequence(backup)
      Action(GraspBackup)                 # succeeds
      Action(Lift)

Injected: GraspPrimary fails on attempts 1 and 2 (returns FAILURE). After
Retry exhausts, Fallback ticks the backup sequence. Prints a decision trace.

Contrasts with Month 4 Nav2 recoveries (map clear / spin) and Month 8 watchdog
(command timeout): this toy is *semantic skill* failure, not packet silence.
usage: python3 recovery_bt_toy.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

SUCCESS, FAILURE, RUNNING = "SUCCESS", "FAILURE", "RUNNING"


@dataclass
class Trace:
    lines: List[str] = field(default_factory=list)

    def log(self, msg: str) -> None:
        self.lines.append(msg)
        print(msg)


class Node:
    def tick(self, tr: Trace) -> str:
        raise NotImplementedError


@dataclass
class Action(Node):
    name: str
    fn: Callable[[Trace], str]

    def tick(self, tr: Trace) -> str:
        status = self.fn(tr)
        tr.log(f"action {self.name} -> {status}")
        return status


@dataclass
class Retry(Node):
    child: Node
    max_attempts: int
    name: str = "Retry"

    def tick(self, tr: Trace) -> str:
        for attempt in range(1, self.max_attempts + 1):
            tr.log(f"retry {self.name} attempt={attempt}/{self.max_attempts}")
            status = self.child.tick(tr)
            if status == SUCCESS:
                return SUCCESS
            if status == RUNNING:
                return RUNNING
        tr.log(f"retry {self.name} exhausted -> FAILURE")
        return FAILURE


@dataclass
class Sequence(Node):
    children: List[Node]
    name: str = "Sequence"

    def tick(self, tr: Trace) -> str:
        tr.log(f"sequence {self.name} enter")
        for ch in self.children:
            status = ch.tick(tr)
            if status != SUCCESS:
                tr.log(f"sequence {self.name} -> {status}")
                return status
        tr.log(f"sequence {self.name} -> SUCCESS")
        return SUCCESS


@dataclass
class Fallback(Node):
    children: List[Node]
    name: str = "Fallback"

    def tick(self, tr: Trace) -> str:
        tr.log(f"fallback {self.name} enter")
        for ch in self.children:
            status = ch.tick(tr)
            if status == SUCCESS:
                tr.log(f"fallback {self.name} -> SUCCESS")
                return SUCCESS
            if status == RUNNING:
                return RUNNING
        tr.log(f"fallback {self.name} -> FAILURE")
        return FAILURE


def main() -> None:
    grasp_attempts = {"n": 0}

    def grasp_primary(tr: Trace) -> str:
        grasp_attempts["n"] += 1
        # Fail the first two calls; would succeed on a 3rd but Retry max=2.
        if grasp_attempts["n"] <= 2:
            return FAILURE
        return SUCCESS

    def grasp_backup(tr: Trace) -> str:
        return SUCCESS

    def lift(tr: Trace) -> str:
        return SUCCESS

    tree = Fallback(
        name="root",
        children=[
            Sequence(
                name="primary",
                children=[
                    Retry(
                        name="grasp_primary",
                        max_attempts=2,
                        child=Action("GraspPrimary", grasp_primary),
                    ),
                    Action("Lift", lift),
                ],
            ),
            Sequence(
                name="backup",
                children=[
                    Action("GraspBackup", grasp_backup),
                    Action("Lift", lift),
                ],
            ),
        ],
    )

    tr = Trace()
    print("bt=Fallback(Sequence(Retry(GraspPrimary,2),Lift), Sequence(GraspBackup,Lift))")
    status = tree.tick(tr)
    print(f"root_status={status}")
    print(f"grasp_primary_attempts={grasp_attempts['n']}")
    print(f"trace_lines={len(tr.lines)}")
    # Key assertions mirrored in expected/
    used_backup = any("GraspBackup" in line for line in tr.lines)
    print(f"used_backup={used_backup}")
    print(
        f"ok: root SUCCESS after GraspPrimary failed twice and GraspBackup ran "
        f"({status == SUCCESS and grasp_attempts['n'] == 2 and used_backup})"
    )


if __name__ == "__main__":
    main()
