#!/usr/bin/env python3
"""Synthetic Hi Robot-style hierarchical VLA with mid-task feedback.

A discrete skill / language stand-in on a shared table scene. Not π,
not Paligemma, not a real UR5e, and not a reproduction of the paper's
instruction-accuracy / task-progress figures. Paper IA/TP figures are
以论文为准; real robots / GPT-4o / paper-task runs are 本页未运行.

Arms: A_flat (the full prompt is sent straight to the low-level
stand-in, which does not replan on mid-task text), B_hier_feedback
(a high-level stand-in maps the prompt, the scene and mid-task user
text to an atomic command; a new user line triggers a replan),
C_hier_ignore (the same hierarchy, but mid-task feedback is ignored).
Regimes: atomic_no_interrupt (a familiar "pick up the cup" with no
user line mid-task) and mid_task_correction (a "clear the trash"
prompt plus "that's not trash" when the stand-in reaches for a bowl).

Metrics: instruction_acc (the executed commands match the post-feedback
intent) and task_progress (fraction of true-trash objects in the bin
plus forbidden objects left in place, over all of those objects).

Common random numbers: one random.Random(f"{regime}/{seed}") stream
per (regime, seed) draws the shared scenes first, in a fixed order,
before any arm is evaluated; all arms share the same scenes.

Regimes and parameters were written before the first run.  Declared
expectations are printed as they come, without tuning.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
N_SCENES = 8
N_STEPS = 6
N_ATOMIC_STEPS = 3
INTERRUPT_AFTER = 2
ALT_INTERRUPT_AFTER = 3  # printed, not adopted
REPLAN_EVERY = 1  # stand-in for the paper's "one second has elapsed"
N_TRUE_TRASH = 2
N_FORBIDDEN = 1
N_OBJECTS = 4  # cup + 2 trash + 1 bowl (forbidden under the correction)
HAND_TRASH = 2
HAND_FORBIDDEN = 1

ARMS = ("A_flat", "B_hier_feedback", "C_hier_ignore")
METRICS = ("instruction_acc", "task_progress")
PAIRS = (
    ("B_hier_feedback", "A_flat"),
    ("C_hier_ignore", "B_hier_feedback"),
    ("C_hier_ignore", "A_flat"),
)

REGIMES = ("atomic_no_interrupt", "mid_task_correction")
DECLARED = {
    "atomic_no_interrupt": "A and B may near-tie - keep (hierarchy is not required for a familiar atomic command)",
    "mid_task_correction": "B consistently wins on instruction_acc and task_progress; A and C lose - keep",
}

OBJECTS_ATOMIC = ("cup", "bowl", "bottle", "wrapper")
TRASH_POOL = ("wrapper", "napkin", "can", "peel")
FORBIDDEN_POOL = ("bowl", "plate", "mug")


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0  # identical values: no floating residue in mean or sd
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    """Half-up rounding on the shortest decimal repr; tiny non-zero values in scientific form."""
    if x != 0.0 and abs(x) < 5e-4:
        return format(Decimal(repr(x)), ".3e")
    s = format(Decimal(repr(x)), ".4f")
    return "0.0000" if s == "-0.0000" else s


def sign_note(diffs, m):
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def build_scenes(regime, seed):
    rng = random.Random(f"{regime}/{seed}")
    scenes = []
    if regime == "atomic_no_interrupt":
        for _ in range(N_SCENES):
            objs = list(OBJECTS_ATOMIC)
            rng.shuffle(objs)
            scenes.append({
                "objects": tuple(objs),
                "target": "cup",
                "true_trash": (),
                "forbidden": (),
                "interrupt": None,
                "interrupt_after": None,
            })
        return scenes
    for _ in range(N_SCENES):
        trash = list(TRASH_POOL)
        rng.shuffle(trash)
        true_trash = tuple(trash[:N_TRUE_TRASH])
        forb_pool = list(FORBIDDEN_POOL)
        rng.shuffle(forb_pool)
        forbidden = tuple(forb_pool[:N_FORBIDDEN])
        objs = list(true_trash) + list(forbidden) + ["cup"]
        rng.shuffle(objs)
        scenes.append({
            "objects": tuple(objs),
            "target": None,
            "true_trash": true_trash,
            "forbidden": forbidden,
            "interrupt": "that's not trash",
            "interrupt_after": INTERRUPT_AFTER,
        })
    return scenes


def low_level_step(command, remaining, bin_):
    """Execute one atomic command. Returns the new remaining list and bin."""
    rem = list(remaining)
    bin_ = list(bin_)
    if command is None:
        return rem, bin_
    kind, obj = command
    if kind == "pick_bin" and obj in rem:
        rem.remove(obj)
        bin_.append(obj)
    elif kind == "leave" and obj in rem:
        rem.remove(obj)  # left on the table, not counted in the bin
        # keep it out of 'remaining' so it is not picked later
        # but it is not in the bin either; record as left-in-place via absence from bin
        rem = rem  # already removed
        # mark as left: store under a side channel? progress uses objects not in bin if forbidden
        # We'll track left-in-place separately... actually remaining-remove means we need left set.
        pass
    return rem, bin_


# Better to track left_in_place explicitly.

def apply_cmd(command, remaining, bin_, left):
    rem = list(remaining)
    bin_ = list(bin_)
    left = list(left)
    if command is None:
        return rem, bin_, left
    kind, obj = command
    if kind == "pick_bin" and obj in rem:
        rem.remove(obj)
        bin_.append(obj)
    elif kind == "leave" and obj in rem:
        rem.remove(obj)
        left.append(obj)
    elif kind == "pick_hold" and obj in rem:
        rem.remove(obj)
        left.append(obj)  # held/left on the table, not binned
    return rem, bin_, left


def high_level(scene, feedback, phase, remaining):
    """Map prompt + optional mid-task text to the next atomic command."""
    if scene["target"] is not None:
        if scene["target"] in remaining:
            return ("pick_hold", scene["target"])
        return None
    # "clear the trash"
    if feedback == "that's not trash":
        # after the correction: leave each forbidden object still on the table,
        # then bin remaining true trash.
        for obj in scene["forbidden"]:
            if obj in remaining:
                return ("leave", obj)
        for obj in scene["true_trash"]:
            if obj in remaining:
                return ("pick_bin", obj)
        return None
    # before any correction: the stand-in mistakes the first forbidden
    # object for trash, then the true trash (a false-positive first guess).
    for obj in scene["forbidden"]:
        if obj in remaining:
            return ("pick_bin", obj)
    for obj in scene["true_trash"]:
        if obj in remaining:
            return ("pick_bin", obj)
    return None


def flat_plan(scene):
    """Low-level stand-in reading the original prompt only, no mid-task text."""
    if scene["target"] is not None:
        return [("pick_hold", scene["target"])]
    # "clear the trash" with no feedback: bins the mistaken forbidden object
    # and the true trash.
    cmds = []
    for obj in scene["forbidden"]:
        cmds.append(("pick_bin", obj))
    for obj in scene["true_trash"]:
        cmds.append(("pick_bin", obj))
    return cmds


def rollout(arm, scene, interrupt_after):
    remaining = list(scene["objects"])
    bin_, left = [], []
    cmds = []
    n_steps = N_ATOMIC_STEPS if scene["target"] is not None else N_STEPS
    flat_cmds = flat_plan(scene)
    fi = 0
    feedback = None
    for t in range(n_steps):
        # Mid-task: steps before the interrupt are a reach, not a commit.
        # The correction arrives at interrupt_after, before the first pick.
        if (
            scene["interrupt"] is not None
            and interrupt_after is not None
            and t < interrupt_after
        ):
            cmds.append(None)
            continue
        if (
            scene["interrupt"] is not None
            and interrupt_after is not None
            and t == interrupt_after
            and arm == "B_hier_feedback"
        ):
            feedback = scene["interrupt"]
        if arm == "A_flat":
            command = flat_cmds[fi] if fi < len(flat_cmds) else None
            fi += 1
        else:
            # High-level reruns every REPLAN_EVERY step, and also when B
            # has just accepted a new user line.
            command = high_level(
                scene,
                feedback if arm == "B_hier_feedback" else None,
                t,
                remaining,
            )
        cmds.append(command)
        remaining, bin_, left = apply_cmd(command, remaining, bin_, left)
    return cmds, remaining, bin_, left


def score(scene, bin_, left):
    if scene["target"] is not None:
        ia = 1.0 if (scene["target"] in left and scene["target"] not in bin_) else 0.0
        # task progress: the cup was picked and nothing else was binned
        tp = 1.0 if ia == 1.0 and not bin_ else 0.0
        return {"instruction_acc": ia, "task_progress": tp}
    true = list(scene["true_trash"])
    forb = list(scene["forbidden"])
    trash_ok = sum(1 for o in true if o in bin_)
    forb_ok = sum(1 for o in forb if o not in bin_)
    denom = len(true) + len(forb)
    tp = (trash_ok + forb_ok) / denom
    intent_ok = (trash_ok == len(true)) and (forb_ok == len(forb))
    ia = 1.0 if intent_ok else 0.0
    return {"instruction_acc": ia, "task_progress": tp}


def run_regime(regime, seed, interrupt_after=INTERRUPT_AFTER):
    scenes = build_scenes(regime, seed)
    # rebuild mid-task scenes if an alternative interrupt step was requested:
    # the object draw stays on the same CRN stream; only the trigger step changes.
    if regime == "mid_task_correction":
        for sc in scenes:
            sc["interrupt_after"] = interrupt_after
    out = {arm: {m: 0.0 for m in METRICS} for arm in ARMS}
    n = len(scenes)
    for scene in scenes:
        for arm in ARMS:
            _, _, bin_, left = rollout(arm, scene, interrupt_after if regime == "mid_task_correction" else None)
            sc = score(scene, bin_, left)
            for m in METRICS:
                out[arm][m] += sc[m]
    for arm in ARMS:
        for m in METRICS:
            out[arm][m] /= n
    return out


def main():
    hand_tp_wrong = HAND_TRASH / (HAND_TRASH + HAND_FORBIDDEN)  # all trash binned, forbidden also binned
    hand_tp_right = (HAND_TRASH + HAND_FORBIDDEN) / (HAND_TRASH + HAND_FORBIDDEN)
    print("Hi Robot-style hierarchical feedback toy: discrete skills on a shared table (synthetic; not pi, not Paligemma, not a UR5e)")
    print("paper IA/TP figures 以论文为准; real robots / GPT-4o / paper-task runs: 本页未运行")
    print(
        f"seeds={len(SEEDS)} n_scenes={N_SCENES} n_steps={N_STEPS} n_atomic_steps={N_ATOMIC_STEPS} "
        f"interrupt_after={INTERRUPT_AFTER} replan_every={REPLAN_EVERY} "
        f"n_true_trash={N_TRUE_TRASH} n_forbidden={N_FORBIDDEN} n_objects={N_OBJECTS} "
        f"hand_trash={HAND_TRASH} hand_forbidden={HAND_FORBIDDEN} (declared)"
    )
    print("Regimes and parameters were written before the first run")
    print(f"hand_calc task_progress if all trash and the forbidden object are binned = {num(hand_tp_wrong)}")
    print(f"hand_calc task_progress if trash is binned and the forbidden object is left = {num(hand_tp_right)}")
    print(f"hand_calc instruction_acc in that last case = 1.0000")
    for r in REGIMES:
        print(f"declared {r}: {DECLARED[r]}")

    store = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_store = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    for seed in SEEDS:
        for regime in REGIMES:
            out = run_regime(regime, seed)
            for arm in ARMS:
                for m in METRICS:
                    store[regime][arm][m].append(out[arm][m])
            alt = run_regime(regime, seed, interrupt_after=ALT_INTERRUPT_AFTER)
            for arm in ARMS:
                for m in METRICS:
                    alt_store[regime][arm][m].append(alt[arm][m])

    for regime in REGIMES:
        print(f"regime {regime}")
        for arm in ARMS:
            for m in METRICS:
                xs = store[regime][arm][m]
                mu, sd = mean_sd(xs)
                print(f"  {arm} {m}: {num(mu)}+-{num(sd)}")
        for left, right in PAIRS:
            for m in METRICS:
                v = verdict(store[regime][left][m], store[regime][right][m])
                print(f"  paired {left[0]}-{right[0]} {m}: {v}")

    print("alternative interrupt_after = 3 (printed, not adopted)")
    for regime in REGIMES:
        print(f"  alt regime {regime}")
        for left, right in PAIRS:
            for m in METRICS:
                v = verdict(alt_store[regime][left][m], alt_store[regime][right][m])
                print(f"    (paired {left[0]}-{right[0]} {m}): {v}")


if __name__ == "__main__":
    main()
