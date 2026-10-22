"""Export trajectories of bc_reach.py for the corridor diagram in behaviour-cloning (D113).

Writes JSON to stdout; the committed copy is src/lib/diagrams/data/bc-corridor.json and
tools/check_diagrams.mjs re-runs this script and requires an identical result.

Everything comes from examples/month-6/behaviour-cloning/bc_reach.py with its own seeds:
  - the first 5 of the 80 noise-free expert demos (random.Random(6)), the "BC, 5 demos" training set;
  - the evaluation of BC on those 5 demos exactly as bc_reach.evaluate does it (seed 2026, 100 rollouts with
    1 cm actuator noise). Recording the path does not change the random numbers, so the counts are the lesson's.
    Two runs are drawn: the first success and the first wall hit at the goal end;
  - for that wall hit, the recorded frame nearest to its last position below the goal's height, and that
    frame's action (what 1-NN replays there).
Coordinates in metres, rounded to 3 decimals (1 mm).
"""
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "examples", "month-6", "behaviour-cloning"))
import bc_reach as bc  # noqa: E402

DEMOS, SEED, RUNS = 5, 2026, 100


def r3(p):
    return [round(p[0], 3), round(p[1], 3)]


def main():
    demos = [f for f in bc.record_demos(80, random.Random(6)) if f[0] < DEMOS]
    policy = bc.nn_policy(demos)
    rng = random.Random(SEED)
    counts = {"success": 0, "wall": 0, "timeout": 0}
    walls = {"leg 1": 0, "corner": 0, "leg 2": 0, "goal end": 0}
    first = {}
    for i in range(RUNS):
        rows = []
        result, steps, worst, p = bc.rollout(policy, rng, record=rows)
        counts[result] += 1
        key = result
        if result == "wall":
            walls[bc.place(p)] += 1
            key = "wall " + bc.place(p)
        if key not in first:
            first[key] = {"run": i, "steps": steps, "worst_cm": round(worst * 100, 1),
                          "path": [r3(q) for _, q, _ in rows] + [r3(p)]}
    fail = first["wall goal end"]
    last = [q for q in fail["path"] if q[1] < bc.GOAL[1]][-1]   # last position below the goal's height
    near = min(demos, key=lambda f: (f[2][0] - last[0]) ** 2 + (f[2][1] - last[1]) ** 2)
    offsets = [bc.path_s(f[2])[1] for f in demos]
    out = {
        "source": "tools/sim/models/bc_corridor_export.py",
        "start": list(bc.START), "corner": list(bc.CORNER), "goal": list(bc.GOAL),
        "half_width": bc.HALF_WIDTH, "step": bc.STEP, "noise": bc.NOISE, "max_steps": bc.MAX_STEPS,
        "demos": [[r3(f[2]) for f in demos if f[0] == ep] for ep in range(DEMOS)],
        "demo_frames": len(demos),
        "demo_frames_over_3cm": sum(1 for o in offsets if o > 0.03),
        "eval": {"seed": SEED, "runs": RUNS, "counts": counts, "walls": walls},
        "success_run": first["success"],
        "wall_run": fail,
        "nearest_frame": {"from": r3(last), "at": r3(near[2]), "action": r3(near[3]),
                          "offset_cm": round(bc.path_s(last)[1] * 100, 1)},
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
