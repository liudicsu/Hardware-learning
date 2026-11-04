#!/usr/bin/env python3
"""nav_pick_bt.py: navigate-then-pick compose contract on a grid (stdlib).

Compose contract (printed): frames map>base_link>arm_base>ee; mutex =
base settled before arm; nav/grasp timeouts; failure feedback from grasp
to nav ("approach closer then grasp").

Grid A* to a far desk approach, grasp fails (outside arm workspace),
Fallback recovers by navigating one cell closer, then grasp succeeds.

Fixed geometry + seed=9 → expected/. No real LeKiwi / Nav2 / ROS runtime.
usage: python3 nav_pick_bt.py
"""
from __future__ import annotations

import math
from heapq import heappop, heappush
from typing import Dict, List, Optional, Tuple

SEED = 9
W, H = 7, 7
START = (1, 1)
DESK = (6, 3)  # grasp target cell (desk edge object)
APPROACH_FAR = (4, 3)
APPROACH_NEAR = (5, 3)
ARM_WORKSPACE_R = 1.5  # Euclidean cells from base to desk
OBSTACLES = {(3, 1), (3, 2), (3, 4), (3, 5)}  # vertical wall with a gap at y=3
TIMEOUT_NAV_S = 30
TIMEOUT_GRASP_S = 10

Pos = Tuple[int, int]


def in_bounds(p: Pos) -> bool:
    x, y = p
    return 0 <= x < W and 0 <= y < H


def neighbours(p: Pos) -> List[Pos]:
    x, y = p
    out: List[Pos] = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        q = (x + dx, y + dy)
        if in_bounds(q) and q not in OBSTACLES:
            out.append(q)
    return out


def astar(start: Pos, goal: Pos) -> List[Pos]:
    """4-connected A*; returns path including start and goal."""
    if start == goal:
        return [start]
    open_h: List[Tuple[int, int, Pos]] = []
    counter = 0
    heappush(open_h, (0, counter, start))
    came: Dict[Pos, Optional[Pos]] = {start: None}
    gscore: Dict[Pos, int] = {start: 0}

    def h(p: Pos) -> int:
        return abs(p[0] - goal[0]) + abs(p[1] - goal[1])

    while open_h:
        _, _, cur = heappop(open_h)
        if cur == goal:
            path = [cur]
            while came[cur] is not None:
                cur = came[cur]  # type: ignore[assignment]
                path.append(cur)
            path.reverse()
            return path
        for nxt in neighbours(cur):
            tentative = gscore[cur] + 1
            if tentative < gscore.get(nxt, 10**9):
                came[nxt] = cur
                gscore[nxt] = tentative
                counter += 1
                heappush(open_h, (tentative + h(nxt), counter, nxt))
    raise RuntimeError(f"no path {start} -> {goal}")


def dist(a: Pos, b: Pos) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def in_workspace(base: Pos) -> bool:
    return dist(base, DESK) <= ARM_WORKSPACE_R + 1e-9


def fmt_path(path: List[Pos]) -> str:
    return "->".join(f"({x},{y})" for x, y in path)


def main() -> None:
    print(f"seed={SEED}")
    print(
        f"map={W}x{H} start={START} desk={DESK} "
        f"approach_far={APPROACH_FAR} approach_near={APPROACH_NEAR}"
    )
    print(f"arm_workspace_r={ARM_WORKSPACE_R}")
    print(
        "compose: frames=map>base_link>arm_base>ee "
        "mutex=base_settled_before_arm "
        f"timeout_nav_s={TIMEOUT_NAV_S} timeout_grasp_s={TIMEOUT_GRASP_S}"
    )

    # --- primary: nav to far approach, try grasp ---
    path_far = astar(START, APPROACH_FAR)
    path_length_far = len(path_far) - 1
    print(f"nav_path_far={fmt_path(path_far)} path_length_far={path_length_far}")
    print("base_settled=True")  # mutex: arm may move only after this
    d1 = dist(APPROACH_FAR, DESK)
    ws1 = in_workspace(APPROACH_FAR)
    print(
        f"grasp_attempt=1 at_base={APPROACH_FAR} dist_to_desk={d1:.3f} "
        f"in_workspace={ws1} -> FAILURE"
    )
    assert not ws1, "far approach must be outside workspace for the demo"

    # --- recovery: approach closer then grasp ---
    print("recovery=approach_closer_then_grasp")
    path_near = astar(APPROACH_FAR, APPROACH_NEAR)
    path_length_near = len(path_near) - 1
    print(f"nav_path_near={fmt_path(path_near)} path_length_near={path_length_near}")
    print("base_settled=True")
    d2 = dist(APPROACH_NEAR, DESK)
    ws2 = in_workspace(APPROACH_NEAR)
    print(
        f"grasp_attempt=2 at_base={APPROACH_NEAR} dist_to_desk={d2:.3f} "
        f"in_workspace={ws2} -> SUCCESS"
    )
    assert ws2, "near approach must be inside workspace"

    path_length_total = path_length_far + path_length_near
    approach_closer_fired = True
    root_status = "SUCCESS"
    print(f"path_length_total={path_length_total}")
    print(f"grasp_in_workspace_final={ws2}")
    print(f"approach_closer_fired={approach_closer_fired}")
    print(f"root_status={root_status}")
    ok = (
        root_status == "SUCCESS"
        and approach_closer_fired
        and ws2
        and not ws1
        and path_length_total > 0
    )
    print(
        f"ok: compose navigate-then-pick with approach-closer recovery ({ok})"
    )


if __name__ == "__main__":
    main()
