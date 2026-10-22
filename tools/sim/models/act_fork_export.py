"""Export the decision at the fork of multimodal.py for the block-task diagram in act-diffusion (D115).

Writes JSON to stdout; the committed copy is src/lib/diagrams/data/act-fork.json and tools/check_diagrams.mjs
re-runs this script and requires an identical result.

Everything comes from examples/month-6/act-diffusion/multimodal.py with its own seed: the 40 expert demos
(random.Random(5)), the K = 10 recorded frames nearest (0, 0.23) (the point of the lesson's first table) with the
action each one recorded, and their mean, which is what average_policy plays there. Metres, rounded to 4 decimals.
"""
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "examples", "month-6", "act-diffusion"))
import multimodal as mm  # noqa: E402

AT = (0.0, 0.23)


def r4(v):
    return [round(v[0], 4), round(v[1], 4)]


def main():
    episodes = mm.record_demos(40, random.Random(5))
    demos = mm.Demos(episodes)
    near = demos.nearest(AT)
    acts = [demos.chunk(f, 1)[0] for f in near]
    mean = mm.average_policy(demos)(AT, 0)[0]
    out = {
        "source": "tools/sim/models/act_fork_export.py",
        "goal": list(mm.GOAL), "block_y": mm.BLOCK_Y, "half": mm.HALF, "fork_y": mm.FORK_Y,
        "step": mm.STEP, "k": mm.K, "at": list(AT),
        "demos": len(episodes), "lefts": sum(1 for rows in episodes if min(p[0] for p, _ in rows) < -0.1),
        "near": [{"p": r4(f[2]), "a": r4(a)} for f, a in zip(near, acts)],
        "mean": r4(mean),
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
