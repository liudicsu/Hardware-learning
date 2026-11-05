#!/usr/bin/env python3
"""lifecycle_sm_toy.py: ROS 2 *managed-node* lifecycle state machine (stdlib).

LOCKED: this toy implements the managed ROS lifecycle node SM from
  https://design.ros2.org/articles/node_lifecycle.html
It is NOT the ros2_control HardwareComponentInterface state machine.
Hardware components are plugins transitioned by ResourceManager /
Controller Manager; do not equate the two SMs (see lesson MDX contrast).

Primary states (design): Unconfigured, Inactive, Active, Finalized.
Transition state used here: ErrorProcessing.
Supervisory transitions used here: configure, activate, deactivate,
cleanup, shutdown. Illegal requests are rejected and leave the primary
state unchanged — they do NOT permanently brick the node.

Callback result paths (design doc, Configuring / ErrorProcessing):
  configure SUCCESS  → Inactive
  configure FAILURE  → Unconfigured
  configure ERROR/exception → ErrorProcessing
  on_error SUCCESS   → Unconfigured
  on_error FAILURE   → Finalized

Script A: configure → activate → Active.
Script B: activate from Unconfigured (illegal, reject) → still
          Unconfigured; then configure → activate → Active (recovery).
Script C: configure → activate → shutdown → Finalized.
Script D: configure(FAILURE) → Unconfigured (stays / returns).
Script E: configure(ERROR) → ErrorProcessing; on_error(SUCCESS) → Unconfigured.
Script F: configure(ERROR) → ErrorProcessing; on_error(FAILURE) → Finalized.
Metrics: illegal_rejects, reached_active, final_state, callback_results.

Tracing / LTTng / real HardwareComponent load = 本页未运行.
usage: python3 lifecycle_sm_toy.py
"""
from __future__ import annotations

# Primary states from the design doc.
UNCONFIGURED = "Unconfigured"
INACTIVE = "Inactive"
ACTIVE = "Active"
FINALIZED = "Finalized"
ERROR_PROCESSING = "ErrorProcessing"

# Legal supervisory edges when the callback succeeds: (state, transition) -> new_state
# From design: Unconfigured --configure--> Inactive
#              Unconfigured --shutdown--> Finalized
#              Inactive --activate--> Active
#              Inactive --cleanup--> Unconfigured
#              Inactive --shutdown--> Finalized
#              Active --deactivate--> Inactive
#              Active --shutdown--> Finalized
LEGAL_SUCCESS = {
    (UNCONFIGURED, "configure"): INACTIVE,
    (UNCONFIGURED, "shutdown"): FINALIZED,
    (INACTIVE, "activate"): ACTIVE,
    (INACTIVE, "cleanup"): UNCONFIGURED,
    (INACTIVE, "shutdown"): FINALIZED,
    (ACTIVE, "deactivate"): INACTIVE,
    (ACTIVE, "shutdown"): FINALIZED,
}

# Callback outcomes the toy can inject on a request.
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
ERROR = "ERROR"  # exception / non-failure error code → ErrorProcessing


class ManagedLifecycleNode:
    """Minimal managed-node lifecycle — design adjacency + callback results."""

    def __init__(self) -> None:
        self.state = UNCONFIGURED
        self.illegal_rejects = 0
        self.transition_log: list[str] = []

    def request(self, transition: str, result: str = SUCCESS) -> bool:
        # on_error is only legal from ErrorProcessing.
        if transition == "on_error":
            if self.state != ERROR_PROCESSING:
                self.illegal_rejects += 1
                self.transition_log.append(
                    f"on_error:REJECT(from={self.state})"
                )
                return False
            if result == SUCCESS:
                new_state = UNCONFIGURED
                self.transition_log.append(
                    f"on_error:SUCCESS({ERROR_PROCESSING}->{new_state})"
                )
                self.state = new_state
                return True
            # FAILURE or any other code → Finalized (design).
            new_state = FINALIZED
            self.transition_log.append(
                f"on_error:FAILURE({ERROR_PROCESSING}->{new_state})"
            )
            self.state = new_state
            return False

        key = (self.state, transition)
        if key not in LEGAL_SUCCESS:
            self.illegal_rejects += 1
            self.transition_log.append(
                f"{transition}:REJECT(from={self.state})"
            )
            return False

        if result == SUCCESS:
            new_state = LEGAL_SUCCESS[key]
            self.transition_log.append(
                f"{transition}:OK({self.state}->{new_state})"
            )
            self.state = new_state
            return True

        if result == FAILURE:
            # Design (Configuring): onConfigure FAILURE → back to Unconfigured.
            # For other transitions the design routes non-success to ErrorProcessing
            # except configure's explicit failure code; we model only configure's
            # FAILURE→Unconfigured path here (the required teaching).
            if transition == "configure":
                new_state = UNCONFIGURED
                self.transition_log.append(
                    f"configure:FAILURE({self.state}->{new_state})"
                )
                self.state = new_state
                return False
            # Non-configure FAILURE treated as error path.
            new_state = ERROR_PROCESSING
            self.transition_log.append(
                f"{transition}:FAILURE({self.state}->{new_state})"
            )
            self.state = new_state
            return False

        # ERROR / exception → ErrorProcessing (design).
        new_state = ERROR_PROCESSING
        self.transition_log.append(
            f"{transition}:ERROR({self.state}->{new_state})"
        )
        self.state = new_state
        return False


def run_script(name: str, steps: list) -> dict:
    """steps: list of transition str, or (transition, result) tuples."""
    node = ManagedLifecycleNode()
    for step in steps:
        if isinstance(step, tuple):
            transition, result = step
            node.request(transition, result)
        else:
            node.request(step)
    reached = 1 if any("->Active" in e for e in node.transition_log) else 0
    return {
        "script": name,
        "steps": steps,
        "illegal_rejects": node.illegal_rejects,
        "reached_active": reached,
        "final_state": node.state,
        "log": node.transition_log,
    }


def _fmt_steps(steps: list) -> str:
    parts = []
    for s in steps:
        if isinstance(s, tuple):
            parts.append(f"{s[0]}({s[1]})")
        else:
            parts.append(s)
    return ",".join(parts)


def main() -> None:
    print(
        "lifecycle_sm_toy sm=ros2_managed_node "
        "source=design.ros2.org/articles/node_lifecycle.html"
    )
    print(
        "note: NOT HardwareComponentInterface SM; "
        "ResourceManager transitions that plugin (prose map only)"
    )
    print(
        "callback_paths: configure FAILURE→Unconfigured; "
        "ERROR/exception→ErrorProcessing; "
        "on_error SUCCESS→Unconfigured, FAILURE→Finalized"
    )

    a = run_script("A", ["configure", "activate"])
    b = run_script("B", ["activate", "configure", "activate"])
    c = run_script("C", ["configure", "activate", "shutdown"])
    d = run_script("D", [("configure", FAILURE)])
    e = run_script("E", [("configure", ERROR), ("on_error", SUCCESS)])
    f = run_script("F", [("configure", ERROR), ("on_error", FAILURE)])

    for r in (a, b, c, d, e, f):
        print(
            f"script_{r['script']}: steps={_fmt_steps(r['steps'])} "
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

    assert d["illegal_rejects"] == 0
    assert d["reached_active"] == 0
    assert d["final_state"] == UNCONFIGURED
    print("configure_failure_returns_unconfigured=1")

    assert e["illegal_rejects"] == 0
    assert e["final_state"] == UNCONFIGURED
    print("on_error_success_returns_unconfigured=1")

    assert f["illegal_rejects"] == 0
    assert f["final_state"] == FINALIZED
    print("on_error_failure_goes_finalized=1")

    print(
        "ok: managed-node lifecycle toy "
        "(LTTng/ros2_tracing/HW plugin load 本页未运行)"
    )


if __name__ == "__main__":
    main()
