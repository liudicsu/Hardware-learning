#!/usr/bin/env python3
"""latent_predict_toy.py: tiny discrete latent imagination (stdlib).

Hand-written latent×action transition dict. From a fixed seed start state,
roll H steps under a fixed action schedule, print predicted latent sequence
and a proxy reward. Proves "imagine in latent space" needs no pixel replay
and no neural net training / weight download.
usage: python3 latent_predict_toy.py
"""
from __future__ import annotations

import random

SEED = 99
H = 8
# Discrete latents and actions.
LATENTS = ("idle", "reach", "grasp", "lift", "fail")
ACTIONS = ("wait", "move", "close", "up")
# (z, a) → next_z
TRANSITIONS: dict[tuple[str, str], str] = {
    ("idle", "wait"): "idle",
    ("idle", "move"): "reach",
    ("idle", "close"): "idle",
    ("idle", "up"): "idle",
    ("reach", "wait"): "reach",
    ("reach", "move"): "reach",
    ("reach", "close"): "grasp",
    ("reach", "up"): "fail",
    ("grasp", "wait"): "grasp",
    ("grasp", "move"): "fail",
    ("grasp", "close"): "grasp",
    ("grasp", "up"): "lift",
    ("lift", "wait"): "lift",
    ("lift", "move"): "lift",
    ("lift", "close"): "lift",
    ("lift", "up"): "lift",
    ("fail", "wait"): "idle",
    ("fail", "move"): "idle",
    ("fail", "close"): "fail",
    ("fail", "up"): "fail",
}
REWARD = {
    "idle": 0.0,
    "reach": 0.1,
    "grasp": 0.4,
    "lift": 1.0,
    "fail": -0.5,
}
# Fixed action schedule for the imagined rollout.
SCHEDULE = ("move", "move", "close", "up", "wait", "move", "wait", "wait")


def main() -> None:
    rng = random.Random(SEED)
    # Start latent drawn once from seed (pinned).
    start = LATENTS[rng.randrange(0, 3)]  # idle / reach / grasp
    assert len(SCHEDULE) == H
    print(
        f"seed={SEED} H={H} start={start} "
        f"n_latents={len(LATENTS)} n_actions={len(ACTIONS)}"
    )
    print(f"{'t':>3} {'z':<8} {'a':<8} {'z_next':<8} {'r':>6}")
    z = start
    total_r = 0.0
    path = [z]
    for t in range(H):
        a = SCHEDULE[t]
        z_next = TRANSITIONS[(z, a)]
        r = REWARD[z_next]
        total_r += r
        print(f"{t:3d} {z:<8} {a:<8} {z_next:<8} {r:6.2f}")
        z = z_next
        path.append(z)
    print(
        f"ok: path={'→'.join(path)} total_r={total_r:.2f} "
        f"(latent imagination; no pixels / no NN weights)"
    )


if __name__ == "__main__":
    main()
