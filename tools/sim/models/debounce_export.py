"""Export the bounce edges of debounce_sim.py for the debounce timing diagram in timing-interrupts.

Writes JSON to stdout; the committed copy is src/lib/diagrams/data/debounce-bounce.json and
tools/check_diagrams.mjs re-runs this script and requires an identical result.

The button model, its fixed seed (bouncy_button's default seed=1), the 0.1 ms sampler and the five presses
are those of debounce_sim.py, so the edges are exactly what the lesson's naive and debounced counters see.
The "quiet line" rule of reaction_timer.ino's ISR is applied to the same edges: the ISR runs on every edge
(attachInterrupt CHANGE), t = millis() (whole milliseconds), and a LOW edge counts as a press only when
t - lastEdge > DEBOUNCE_MS; every edge sets lastEdge = t (lastEdge starts at 0).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from debounce_sim import STEP_MS, bouncy_button, naive_presses  # noqa: E402

PRESSES = [(100, 300), (700, 150), (1200, 400), (2000, 80), (2500, 250)]  # as in debounce_sim.py
DEBOUNCE_MS = 30  # reaction_timer.ino


def main():
    samples = bouncy_button(PRESSES)
    edges, last = [], 1
    for t, level in samples:
        if level != last:
            edges.append([t, level])
            last = level
    accepted, last_edge = [], 0
    for t, level in edges:
        ms = math.floor(t + 1e-9)  # millis() at the edge
        if level == 0 and ms - last_edge > DEBOUNCE_MS:
            accepted.append(t)
        last_edge = ms
    out = {
        "source": "tools/sim/models/debounce_export.py",
        "seed": 1,
        "step_ms": STEP_MS,
        "presses": [list(p) for p in PRESSES],
        "naive_presses": naive_presses(samples),
        "debounce_ms": DEBOUNCE_MS,
        "edges": edges,
        "accepted": accepted,
    }
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
