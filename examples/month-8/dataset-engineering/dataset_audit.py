#!/usr/bin/env python3
"""dataset_audit.py: audit a tiny synthetic LeRobot-v3-style dataset (stdlib only).

Layout (toy mirror of LeRobotDataset v3 ideas — many episodes per file, metadata
locates episode boundaries; not a Hub download):
  synthetic_lerobot/meta/info.json
  synthetic_lerobot/meta/episodes.jsonl
  synthetic_lerobot/data/chunk-000.json   # list of frame dicts; episode_index field

Reports: episodes per variation, mean duration, action min/max, missing-frame
gaps, and which variations are under-covered (< target_min episodes).
usage: python3 dataset_audit.py
"""
from __future__ import annotations

import json
import math
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "synthetic_lerobot")
TARGET_MIN = 8  # SmolVLA docs suggest ~50 for real tasks; toy threshold is smaller


def main() -> None:
    with open(os.path.join(ROOT, "meta", "info.json"), encoding="utf-8") as f:
        info = json.load(f)
    fps = float(info["fps"])
    episodes = []
    with open(os.path.join(ROOT, "meta", "episodes.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                episodes.append(json.loads(line))
    with open(os.path.join(ROOT, "data", "chunk-000.json"), encoding="utf-8") as f:
        frames = json.load(f)

    by_ep: dict[int, list[dict]] = defaultdict(list)
    for fr in frames:
        by_ep[int(fr["episode_index"])].append(fr)

    print(f"dataset {info['repo_id']}  fps={fps:g}  episodes={len(episodes)}  frames={len(frames)}")
    print(f"{'variation':<16} {'n_ep':>5} {'mean_s':>8} {'action_min':>11} {'action_max':>11} {'miss':>5} {'flag':>10}")

    under = []
    for ep_meta in episodes:
        eid = int(ep_meta["episode_index"])
        var = ep_meta["variation"]
        seq = sorted(by_ep[eid], key=lambda r: int(r["frame_index"]))
        # duration from frame count / fps
        dur = len(seq) / fps if fps else float("nan")
        actions = [float(r["action"][0]) for r in seq]  # first joint for range
        amin = min(actions) if actions else float("nan")
        amax = max(actions) if actions else float("nan")
        # missing frames: gaps in frame_index
        idxs = [int(r["frame_index"]) for r in seq]
        miss = 0
        if idxs:
            expect = list(range(idxs[0], idxs[-1] + 1))
            miss = len(expect) - len(idxs)
        ep_meta["_dur"] = dur
        ep_meta["_amin"] = amin
        ep_meta["_amax"] = amax
        ep_meta["_miss"] = miss
        ep_meta["_n"] = len(seq)

    # aggregate by variation
    groups: dict[str, list[dict]] = defaultdict(list)
    for ep_meta in episodes:
        groups[ep_meta["variation"]].append(ep_meta)

    for var in sorted(groups):
        eps = groups[var]
        n = len(eps)
        mean_s = sum(e["_dur"] for e in eps) / n
        amin = min(e["_amin"] for e in eps)
        amax = max(e["_amax"] for e in eps)
        miss = sum(e["_miss"] for e in eps)
        flag = "UNDER" if n < TARGET_MIN else "ok"
        if flag == "UNDER":
            under.append(var)
        print(f"{var:<16} {n:5d} {mean_s:8.2f} {amin:11.3f} {amax:11.3f} {miss:5d} {flag:>10}")

    print(f"target_min_episodes_per_variation={TARGET_MIN}")
    if under:
        print("under_covered: " + ", ".join(under))
    else:
        print("under_covered: (none)")
    # pinned totals for check_diagrams
    print(f"total_variations={len(groups)} total_episodes={len(episodes)}")


if __name__ == "__main__":
    main()
