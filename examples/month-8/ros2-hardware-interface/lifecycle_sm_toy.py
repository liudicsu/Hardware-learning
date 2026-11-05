#!/usr/bin/env python3
"""lifecycle_sm_toy.py: ROS 2 *managed-node* lifecycle state machine (stdlib).

LOCKED: this toy implements the managed ROS lifecycle node SM from
  https://design.ros2.org/articles/node_lifecycle.html
It is NOT the ros2_control HardwareComponentInterface state machine.
Hardware components are plugins transitioned by ResourceManager /
Controller Manager; do not equate the two SMs (see lesson MDX contrast).

Primary states (design): Unconfigured, Inactive, Active, Finalized.
Supervisory transitions used here: configure, activate, deactivate,
cleanup, shutdown. Illegal requests are rejected and leave the primary
state unchanged — they do NOT permanently brick the node.

Script A: configure → activate → Active.
Script B: activate from Unconfigured (illegal, reject) → still
          Unconfigured; then configure → activate → Active (recovery).
Script C: configure → activate → shutdown → Finalized.
Metrics: illegal_rejects, reached_active, final_state.

Tracing / LTTng / real HardwareComponent load = 本页未运行.
usage: python3 lifecycle_sm_toy.py
"""
from __future__ import annotations

# Primary states from the design doc.
UNCONFIGURED = "Unconfigured"
INACTIVE = "Inactive"
ACTIVE = "Active"
FINALIZED = "Finalized"

# Legal edges: (state, transition) -> new_state
# From design: Unconfigured --configure--> Inactive
#              Unconfigured --shutdown--> Finalized
#              Inactive --activate--> Active
#              Inactive --cleanup--> Unconfigured
#              Inactive --shutdown--> Finalized
#              Active --deactivate--> Inactive
#              Active --shutdown--> Finalized
LEGAL = {
    (UNCONFIGURED, "configure"): INACTIVE,
    (UNCONFIGURED, "shutdown"): FINALIZED,
    (INACTIVE, "activate"): ACTIVE,
    (INACTIVE, "cleanup"): UNCONFIGURED,
    (INACTIVE, "shutdown"): FINALIZED,
    (ACTIVE, "deactivate"): INACTIVE,
    (ACTIVE, "shutdown"): FINALIZED,
}


class ManagedLifecycleNode:
    """Minimal managed-node lifecycle — design adjacency only."""

    def __init__(self) -> None:
        self.state = UNCONFIGURED
        self.illegal_rejects = 0
        self.transition_log: list[str] = []

    def request(self, transition: str) -> bool:
        key = (self.state, transition)
        if key not in LEGAL:
            self.illegal_rejects += 1
            self.transition_log.append(
                f"{transition}:REJECT(from={self.state})"
            )
            return False
        new_state = LEGAL[key]
        self.transition_log.append(
            f"{transition}:OK({self.state}->{new_state})"
        )
        self.state = new_state
        return True


def run_script(name: str, steps: list[str]) -> dict:
    node = ManagedLifecycleNode()
    for step in steps:
        node.request(step)
    # reached_active: successfully entered Active at least once
    reached = 1 if any("->Active" in e for e in node.transition_log) else 0
    result = {
        "script": name,
        "steps": steps,
        "illegal_rejects": node.illegal_rejects,
        "reached_active": reached,
        "final_state": node.state,
        "log": node.transition_log,
    }
    return result


def main() -> None:
    print(
        "lifecycle_sm_toy sm=ros2_managed_node "
        "source=design.ros2.org/articles/node_lifecycle.html"
    )
    print(
        "note: NOT HardwareComponentInterface SM; "
        "ResourceManager transitions that plugin (prose map only)"
    )

    a = run_script("A", ["configure", "activate"])
    b = run_script("B", ["activate", "configure", "activate"])
    c = run_script("C", ["configure", "activate", "shutdown"])

    for r in (a, b, c):
        print(
            f"script_{r['script']}: steps={','.join(r['steps'])} "
            f"illegal_rejects={r['illegal_rejects']} "
            f"reached_active={r['reached_active']} "
            f"final_state={r['final_state']}"
        )
        print(f"script_{r['script']}_log={' | '.join(r['log'])}")

    assert a["illegal_rejects"] == 0
    assert a["reached_active"] == 1
    assert a["final_state"] == ACTIVE

    assert b["illegal_rejects"] == 1
    assert b["reached_active"] == 1
    assert b["final_state"] == ACTIVE
    # LOCKED: illegal activate must NOT mean permanently dead.
    assert b["final_state"] == ACTIVE
    print("never_permanent_death_after_illegal_activate=1")

    assert c["illegal_rejects"] == 0
    assert c["reached_active"] == 1
    assert c["final_state"] == FINALIZED
    print("reached_finalized_via_shutdown=1")
    print(
        "ok: managed-node lifecycle toy "
        "(LTTng/ros2_tracing/HW plugin load 本页未运行)"
    )


if __name__ == "__main__":
    main()
