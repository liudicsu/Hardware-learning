"""intervention_log_toy.py: read a human-in-the-loop log the way a dataset sees it (stdlib).

A seeded stand-in for a DAgger-style rollout recorded with an `intervention`
column. Each frame row is (episode_index, frame_index, intervention, dev),
where dev is how far the arm has drifted from where the demos go.

1. Generate episodes: the policy drifts; when dev crosses TAKE_OVER the
   operator pauses (no frames recorded while paused), takes over with the
   leader arm (intervention=1) and hands back after finishing the fix.
2. Split each intervention run into segments; intervention rate per episode.
3. Label frames inside a segment, RaC-style: "recovery" while dev is still
   above IN_DIST (getting back to familiar states), "correction" after that.
4. Count what RaC's second rule (end the episode after an intervention)
   would keep.
5. Merge: a demo dataset without `intervention` and the HIL dataset do not
   share a schema; the toy merge refuses, then passes after the column is
   removed. The error text is this toy's, not LeRobot's.
No robot, no LeRobot install.
"""

import random

SEED = 5
FPS = 30
EPISODES = 6
FRAMES_PER_EPISODE = 240
TAKE_OVER = 0.60   # operator presses the key once drift passes this
IN_DIST = 0.20     # below this the state looks like the demos again
RECOVER_STEP = 0.08
CORRECT_FRAMES = (12, 30)

DEMO_FEATURES = ["observation.state", "action", "timestamp", "frame_index", "episode_index", "index", "task_index"]
HIL_FEATURES = DEMO_FEATURES + ["intervention"]


def rollout(rng, ep):
    rows, dev, f = [], 0.05, 0
    while f < FRAMES_PER_EPISODE:
        dev = max(0.0, dev + rng.gauss(0.006, 0.03))
        if dev <= TAKE_OVER:
            rows.append((ep, f, 0, dev))
            f += 1
            continue
        # pause: robot holds, nothing is recorded; then the human drives
        while dev > IN_DIST and f < FRAMES_PER_EPISODE:
            dev = max(0.0, dev - RECOVER_STEP + rng.gauss(0, 0.01))
            rows.append((ep, f, 1, dev))
            f += 1
        for _ in range(rng.randint(*CORRECT_FRAMES)):
            if f >= FRAMES_PER_EPISODE:
                break
            dev = max(0.0, dev * 0.7 + rng.gauss(0, 0.01))
            rows.append((ep, f, 1, dev))
            f += 1
    return rows


def segments(rows):
    segs, start = [], None
    for i, r in enumerate(rows):
        if r[2] and start is None:
            start = i
        if start is not None and (not r[2] or i == len(rows) - 1):
            end = i if r[2] else i - 1
            segs.append(rows[start:end + 1])
            start = None
    return segs


def label(seg):
    """RaC-style split: recovery until dev first drops to IN_DIST, then correction."""
    rec = 0
    for r in seg:
        if r[3] > IN_DIST:
            rec += 1
        else:
            break
    return rec, len(seg) - rec


def timeline(rows, step=4):
    out = []
    in_dist_seen = False
    for r in rows[::step]:
        if not r[2]:
            out.append(".")
            in_dist_seen = False
        else:
            if r[3] <= IN_DIST:
                in_dist_seen = True
            out.append("c" if in_dist_seen else "R")
    return "".join(out)


def merge(a_name, a_feats, b_name, b_feats):
    extra_b = [f for f in b_feats if f not in a_feats]
    extra_a = [f for f in a_feats if f not in b_feats]
    if extra_a or extra_b:
        raise ValueError(f"features differ: only in {b_name}: {extra_b}; only in {a_name}: {extra_a}")
    return a_feats


def main() -> None:
    rng = random.Random(SEED)
    data = [rollout(rng, ep) for ep in range(EPISODES)]
    print(f"seed={SEED}  {EPISODES} episodes x {FRAMES_PER_EPISODE} frames @ {FPS} fps  "
          f"take-over dev>{TAKE_OVER}  in-distribution dev<={IN_DIST}")
    print("keys (lerobot-rollout --strategy.type=dagger, docs main): Space pause/resume policy, "
          "Tab start/stop correction, Enter push to Hub (corrections-only), ESC stop")
    print("timeline ep0 (every 4th frame; . policy, R recovery, c correction):")
    print("  " + timeline(data[0]))

    print(f"{'ep':>2} {'frames':>6} {'interv':>6} {'rate':>6} {'segs':>4} {'recov':>5} {'corr':>5} {'keep_rule2':>10}")
    tot = tot_i = tot_s = tot_r = tot_c = tot_keep = 0
    seg_lens = []
    for ep, rows in enumerate(data):
        segs = segments(rows)
        n_i = sum(r[2] for r in rows)
        rec = sum(label(s)[0] for s in segs)
        cor = sum(label(s)[1] for s in segs)
        keep = (rows.index(segs[0][-1]) + 1) if segs else len(rows)
        seg_lens += [len(s) for s in segs]
        print(f"{ep:>2} {len(rows):>6} {n_i:>6} {n_i / len(rows):>6.1%} {len(segs):>4} {rec:>5} {cor:>5} {keep:>10}")
        tot, tot_i, tot_s, tot_r, tot_c, tot_keep = (tot + len(rows), tot_i + n_i, tot_s + len(segs),
                                                     tot_r + rec, tot_c + cor, tot_keep + keep)
    print(f"all {tot:>6} {tot_i:>6} {tot_i / tot:>6.1%} {tot_s:>4} {tot_r:>5} {tot_c:>5} {tot_keep:>10}")
    mean_len = sum(seg_lens) / len(seg_lens)
    print(f"segments: {tot_s}  mean length {mean_len:.1f} frames = {mean_len / FPS:.2f} s  "
          f"shortest {min(seg_lens)}  longest {max(seg_lens)}")
    print(f"recovery share of intervention frames: {tot_r / tot_i:.1%}")
    print(f"corrections-only recording would save {tot_s} episodes with {tot_i} frames; "
          f"full logging keeps {tot} frames incl. autonomous context")
    print(f"RaC rule 2 (end after the first intervention) keeps {tot_keep} of {tot} frames")

    try:
        merge("demos", DEMO_FEATURES, "hil", HIL_FEATURES)
    except ValueError as e:
        print(f"merge demos + hil: ERROR {e}")
    stripped = [f for f in HIL_FEATURES if f != "intervention"]
    merge("demos", DEMO_FEATURES, "hil_stripped", stripped)
    print(f"after remove_feature('intervention'): merge ok, {len(stripped)} features")


if __name__ == "__main__":
    main()
