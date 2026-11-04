#!/usr/bin/env python3
"""stage_graph_toy.py: MoveIt Task Constructor–style stage DAG checks (stdlib).

Models a pick-place task as stages with types (generator / propagator /
connector) and container roles (serial / parallel / wrapper). Detects cycles,
disconnected stages, and a missing Connect between open-hand and the grasp
serial container — the classic MTC wiring mistake.

Prints a fixed stage table (SEED pins any mock cost noise) plus diagnostics.
Not a MoveIt / ROS 2 run — no URDF required.
usage: python3 stage_graph_toy.py
"""
from __future__ import annotations

from collections import defaultdict, deque

SEED = 9
# Mock planning costs (seconds); fixed table, no RNG draws so expected/ is stable.
STAGES = [
    # name, type, container, depends_on (comma-separated predecessors)
    ("current_state", "generator", "root", ""),
    ("open_hand", "propagator", "serial", "current_state"),
    ("connect_to_grasp", "connector", "root", "open_hand"),
    ("approach", "propagator", "serial_grasp", "connect_to_grasp"),
    ("generate_grasp_pose", "generator", "serial_grasp", "approach"),
    ("compute_ik", "propagator", "serial_grasp", "generate_grasp_pose"),
    ("allow_collision", "propagator", "serial_grasp", "compute_ik"),
    ("close_hand", "propagator", "serial_grasp", "allow_collision"),
    ("attach_object", "propagator", "serial_grasp", "close_hand"),
    ("lift", "propagator", "serial_grasp", "attach_object"),
    ("connect_to_place", "connector", "root", "lift"),
    ("place_approach", "propagator", "serial_place", "connect_to_place"),
    ("generate_place_pose", "generator", "serial_place", "place_approach"),
    ("place_ik", "propagator", "serial_place", "generate_place_pose"),
    ("open_place", "propagator", "serial_place", "place_ik"),
    ("detach", "propagator", "serial_place", "open_place"),
    ("retreat", "propagator", "serial_place", "detach"),
    ("return_home", "propagator", "serial", "retreat"),
]

# Deterministic mock costs keyed by name (seconds of "planning effort").
MOCK_COST = {
    "current_state": 0.01,
    "open_hand": 0.05,
    "connect_to_grasp": 0.40,
    "approach": 0.20,
    "generate_grasp_pose": 0.15,
    "compute_ik": 0.25,
    "allow_collision": 0.02,
    "close_hand": 0.05,
    "attach_object": 0.02,
    "lift": 0.18,
    "connect_to_place": 0.45,
    "place_approach": 0.20,
    "generate_place_pose": 0.12,
    "place_ik": 0.22,
    "open_place": 0.05,
    "detach": 0.02,
    "retreat": 0.15,
    "return_home": 0.30,
}


def parse_stages():
    names = []
    types = {}
    containers = {}
    preds = {}
    for name, typ, container, dep in STAGES:
        names.append(name)
        types[name] = typ
        containers[name] = container
        preds[name] = [p for p in dep.split(",") if p]
    return names, types, containers, preds


def successors(preds):
    succ = defaultdict(list)
    for n, ps in preds.items():
        for p in ps:
            succ[p].append(n)
    return succ


def find_cycle(names, preds):
    """Return one cycle as a list of names, or None."""
    color = {n: 0 for n in names}  # 0=white 1=grey 2=black
    stack = []

    def dfs(u):
        color[u] = 1
        stack.append(u)
        for v in successors(preds)[u]:
            if color[v] == 1:
                i = stack.index(v)
                return stack[i:] + [v]
            if color[v] == 0:
                cyc = dfs(v)
                if cyc:
                    return cyc
        stack.pop()
        color[u] = 2
        return None

    for n in names:
        if color[n] == 0:
            cyc = dfs(n)
            if cyc:
                return cyc
    return None


def reachable_from(root, names, preds):
    succ = successors(preds)
    seen = set()
    q = deque([root])
    while q:
        u = q.popleft()
        if u in seen:
            continue
        seen.add(u)
        for v in succ[u]:
            q.append(v)
    return seen


def missing_connect(names, types, preds):
    """Flag if open_hand has no outgoing connector before the grasp serial chain."""
    issues = []
    if "open_hand" not in names:
        return issues
    succ = successors(preds)
    outs = succ.get("open_hand", [])
    if not any(types.get(s) == "connector" for s in outs):
        issues.append(
            "missing_connect: open_hand has no connector successor "
            "(need Connect before serial_grasp)"
        )
    # Also: every generator that is not the root current_state should eventually
    # feed a connector or be inside a container that a connector reaches.
    return issues


def broken_graph():
    """A deliberately broken DAG: drop connect_to_grasp and add a cycle edge."""
    names, types, containers, preds = parse_stages()
    # remove the connect stage
    names = [n for n in names if n != "connect_to_grasp"]
    for d in (types, containers, preds):
        d.pop("connect_to_grasp", None)
    # approach now hangs off open_hand directly (no connector)
    preds["approach"] = ["open_hand"]
    # cycle: return_home -> current_state
    preds["current_state"] = ["return_home"]
    return names, types, containers, preds


def diagnose(names, types, containers, preds, label):
    print(f"=== {label} ===")
    print(f"{'stage':<22} {'type':<12} {'container':<14} {'cost_s':>7} deps")
    total = 0.0
    for n in names:
        cost = MOCK_COST.get(n, 0.0)
        total += cost
        deps = ",".join(preds[n]) if preds[n] else "-"
        print(
            f"{n:<22} {types[n]:<12} {containers[n]:<14} {cost:7.2f} {deps}"
        )
    print(f"stages={len(names)} total_mock_cost_s={total:.2f} seed={SEED}")

    cyc = find_cycle(names, preds)
    if cyc:
        print(f"FAIL cycle: {' -> '.join(cyc)}")
    else:
        print("ok: no cycle")

    root = "current_state" if "current_state" in names else names[0]
    seen = reachable_from(root, names, preds)
    disconnected = [n for n in names if n not in seen]
    if disconnected:
        print(f"FAIL disconnected_from_{root}: {','.join(disconnected)}")
    else:
        print(f"ok: all stages reachable from {root}")

    for issue in missing_connect(names, types, preds):
        print(f"FAIL {issue}")
    if not missing_connect(names, types, preds):
        print("ok: open_hand has a connector successor")

    n_gen = sum(1 for n in names if types[n] == "generator")
    n_prop = sum(1 for n in names if types[n] == "propagator")
    n_conn = sum(1 for n in names if types[n] == "connector")
    print(f"counts generators={n_gen} propagators={n_prop} connectors={n_conn}")


def main() -> None:
    names, types, containers, preds = parse_stages()
    diagnose(names, types, containers, preds, "good_pick_place")
    print()
    b_names, b_types, b_containers, b_preds = broken_graph()
    diagnose(b_names, b_types, b_containers, b_preds, "broken_no_connect_plus_cycle")


if __name__ == "__main__":
    main()
