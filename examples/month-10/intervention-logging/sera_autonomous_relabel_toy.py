#!/usr/bin/env python3
"""SeRA stand-in: set-valued relabeling of unlabeled autonomous frames.

A shared stream of short trajectories has an intervention mask. Two later
checkpoint policies, used only as action predictors, propose relabels.
This is a standard-library CPU stand-in, not a diffusion trainer and not
Set-Supervised Diffusion Policy training.

Arms:
  A  train and score only on human-labelled frames; unlabeled frames
     are unused for action supervision
  B  also imitate historical robot actions on unlabeled frames
  C  SeRA-lite: later checkpoints relabel unlabeled states; accept a
     relabel only when they agree within a declared absolute tolerance;
     supervise a set (accepted relabel as a positive, historical robot
     action as a negative / excluded point); on disagreement, reject
     that step and later steps of the same chunk
  D  exact-target pseudo-label: imitate the latest checkpoint's relabel
     as an exact point on every unlabeled frame (named variant; may
     lose; kept)

Metrics per seed, on unlabeled frames: task_mse (squared error versus
the optimal action; lower is better) and robot_mse (squared error versus
the historical robot action; a larger value is lower imitation of that
historical action).

Regimes and expectations, written before the first run:
  already_good          historical robot actions already match a later
                        good policy: B and C may near-tie each other
                        (keep)
  wrong_auton_agree     early autonomous actions are systematically
                        wrong and later checkpoints agree on a better
                        action: C is consistently better than B, with
                        lower imitation of the bad historical action
                        (keep)
  checkpoints_disagree  checkpoints disagree (noisy relabels): C rejects
                        and does not degrade to the noisy relabel; an
                        exact-imitate-relabel or B may lose or fail to
                        improve (keep)
  exact_target_lose     checkpoints agree on a slightly wrong relabel
                        whose desired set still contains the optimum:
                        the exact-target variant may lose (keep)

Named alternative, same streams, not adopted: r_N = 0 on accepted
relabels (exact target after the agreement filter).

Paper tables, tomato-picking percentages, LIBERO and PushT numbers are
以论文为准 and are not toy outputs. Real robot / diffusion policy /
SDP training / LIBERO / PushT: 本页未运行.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

N_TRAJ = 8
CHUNK_LEN = 4
STEPS = (0, 1, 2, 3)
HUMAN_STEPS = (0,)  # intervention at the first step of each chunk
N_CHECKPOINTS = 2
MIN_CHECKPOINTS = 2
AGREE_ABS = 0.1500  # accept iff |ckpt1 - ckpt2| < AGREE_ABS
RADIUS_RATIO = 1.0000  # paper r_N = 1; radius = r_N * |relabel - robot|
A_STAR_BIAS = 1.0000
A_STAR_SLOPE = 0.2500
# Regime-specific historical robot actions and checkpoint predictions.
ROBOT_GOOD = "star"  # a_r = a*
ROBOT_BAD = -1.0000
ROBOT_FAR = -2.0000
RELABEL_BIAS = 0.2000  # imperfect agreed relabel in exact_target_lose
DISAGREE_DELTA = 1.5000  # ckpt offset at the first unlabeled step
ALT_RADIUS_RATIO = 0.0000  # named alternative, not adopted

ARMS = ("A", "B", "C", "D")
REGIMES = (
    "already_good",
    "wrong_auton_agree",
    "checkpoints_disagree",
    "exact_target_lose",
)


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
        return format(Decimal(repr(x)), ".3e")
    s = format(Decimal(repr(x)), ".4f")
    return "0.0000" if s == "-0.0000" else s




def fmt_minus(a, b):
    """ASCII subtraction typography: 0.2000-(-2.0000), never 0.2000--2.0000."""
    right = num(b)
    if right.startswith("-"):
        return f"{num(a)}-({right})"
    return f"{num(a)}-{right}"

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
    elif abs(m) < SMALL_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def a_star(step: int) -> float:
    return A_STAR_BIAS + A_STAR_SLOPE * step


def is_human(step: int) -> bool:
    return step in HUMAN_STEPS


def robot_action(regime: str, step: int) -> float:
    if is_human(step):
        return a_star(step)
    if regime == "already_good":
        return a_star(step)
    if regime == "exact_target_lose":
        return ROBOT_FAR
    return ROBOT_BAD


def checkpoints(regime: str, step: int) -> tuple[float, float]:
    """Two later checkpoint predictions at this step (stand-in predictors)."""
    star = a_star(step)
    if regime == "already_good":
        return star, star
    if regime == "wrong_auton_agree":
        return star, star
    if regime == "exact_target_lose":
        return RELABEL_BIAS, RELABEL_BIAS
    # checkpoints_disagree: disagreement at the first unlabeled step;
    # later steps would agree individually (prefix rejection demo).
    if step == 1:
        return star + DISAGREE_DELTA, star - DISAGREE_DELTA
    return star, star


def agreement_ok(p1: float, p2: float) -> bool:
    return N_CHECKPOINTS >= MIN_CHECKPOINTS and abs(p1 - p2) < AGREE_ABS


def desired_radius(relabel: float, robot: float, radius_ratio: float) -> float:
    return radius_ratio * abs(relabel - robot)


def in_desired_set(x: float, relabel: float, robot: float, radius_ratio: float) -> bool:
    radius = desired_radius(relabel, robot, radius_ratio)
    if radius == 0.0:
        return x == relabel
    return abs(x - relabel) <= radius


def set_target(base: float, relabel: float, robot: float, radius_ratio: float) -> float:
    """Point in the desired set closest to base; never the excluded robot
    action when the set has positive radius (fall back to the relabel)."""
    radius = desired_radius(relabel, robot, radius_ratio)
    if radius == 0.0:
        return relabel
    lo, hi = relabel - radius, relabel + radius
    x = min(max(base, lo), hi)
    if x == robot:
        return relabel
    return x


def build_stream(regime: str):
    """Shared chunk stream. One chunk per trajectory; identical across arms."""
    frames = []
    for traj in range(N_TRAJ):
        prefix_failed = False
        for step in STEPS:
            human = is_human(step)
            p1, p2 = checkpoints(regime, step)
            would_agree = agreement_ok(p1, p2)
            if human:
                accepted = False
                rejected_prefix = False
                relabel = p1
            else:
                if prefix_failed:
                    accepted = False
                    rejected_prefix = True
                elif would_agree:
                    accepted = True
                    rejected_prefix = False
                else:
                    accepted = False
                    rejected_prefix = False
                    prefix_failed = True
                relabel = p1  # latest checkpoint stands in for the relabel
            frames.append(
                {
                    "traj": traj,
                    "step": step,
                    "human": human,
                    "a_h": a_star(step) if human else None,
                    "a_r": robot_action(regime, step),
                    "a_star": a_star(step),
                    "p1": p1,
                    "p2": p2,
                    "would_agree": would_agree,
                    "accepted": accepted,
                    "rejected_prefix": rejected_prefix,
                    "relabel": relabel,
                }
            )
    return frames


def human_policy(frames):
    human_vals = [f["a_h"] for f in frames if f["human"]]
    human_mean = sum(human_vals) / len(human_vals)
    per_step = {}
    for step in STEPS:
        vals = [f["a_h"] for f in frames if f["human"] and f["step"] == step]
        per_step[step] = (sum(vals) / len(vals)) if vals else human_mean
    return per_step, human_mean


def fit_arm(frames, arm: str, radius_ratio: float):
    base, human_mean = human_policy(frames)
    policy = dict(base)
    if arm == "A":
        return policy, human_mean
    for step in STEPS:
        step_frames = [f for f in frames if f["step"] == step and not f["human"]]
        if not step_frames:
            continue
        if arm == "B":
            policy[step] = sum(f["a_r"] for f in step_frames) / len(step_frames)
        elif arm == "D":
            policy[step] = sum(f["relabel"] for f in step_frames) / len(step_frames)
        elif arm == "C":
            accepted = [f for f in step_frames if f["accepted"]]
            if not accepted:
                continue  # rejected unlabeled frames: leave the human-only base
            targets = [
                set_target(base[step], f["relabel"], f["a_r"], radius_ratio)
                for f in accepted
            ]
            policy[step] = sum(targets) / len(targets)
    return policy, human_mean


def score(frames, policy):
    unlabeled = [f for f in frames if not f["human"]]
    task = [(policy[f["step"]] - f["a_star"]) ** 2 for f in unlabeled]
    robot = [(policy[f["step"]] - f["a_r"]) ** 2 for f in unlabeled]
    return sum(task) / len(task), sum(robot) / len(robot)


def mask_counts(frames):
    unlabeled = [f for f in frames if not f["human"]]
    n_acc = sum(1 for f in unlabeled if f["accepted"])
    n_pref = sum(1 for f in unlabeled if f["rejected_prefix"])
    n_rej = len(unlabeled) - n_acc
    # unique steps (same mask on every traj)
    one = [f for f in frames if f["traj"] == 0]
    return n_acc, n_rej, n_pref, one


def run_regime(regime: str, radius_ratio: float = RADIUS_RATIO):
    # Seeds repeat the same deterministic stream so exact-tie cells print
    # as identical on every seed. Common random numbers: the stream, the
    # intervention mask, and both checkpoint queries are shared across arms.
    rows = {arm: {"task_mse": [], "robot_mse": []} for arm in ARMS}
    frames = None
    for _seed in SEEDS:
        frames = build_stream(regime)
        for arm in ARMS:
            policy, _ = fit_arm(frames, arm, radius_ratio)
            task, robot = score(frames, policy)
            rows[arm]["task_mse"].append(task)
            rows[arm]["robot_mse"].append(robot)
    return rows, frames


def fmt_mean(xs):
    m, s = mean_sd(xs)
    return f"{num(m)}+-{num(s)}"


def print_regime(name: str, expl: str) -> None:
    rows, frames = run_regime(name)
    n_acc, n_rej, n_pref, one = mask_counts(frames)
    print()
    print(f"regime {name}")
    print(expl)
    print(
        f"unlabeled_frames={N_TRAJ * (CHUNK_LEN - len(HUMAN_STEPS))} "
        f"accepted={n_acc} rejected={n_rej} rejected_prefix={n_pref}"
    )
    mask_bits = []
    for f in one:
        if f["human"]:
            tag = "human"
        elif f["accepted"]:
            tag = "accept"
        elif f["rejected_prefix"]:
            tag = "reject_prefix"
        else:
            tag = "reject"
        mask_bits.append(f"step{f['step']}:{tag}")
    print("chunk_mask " + " ".join(mask_bits))
    for f in one:
        print(
            "setup step="
            + str(f["step"])
            + " a_star="
            + num(f["a_star"])
            + " a_r="
            + num(f["a_r"])
            + " ckpt1="
            + num(f["p1"])
            + " ckpt2="
            + num(f["p2"])
            + " abs_diff=|"
            + fmt_minus(f["p1"], f["p2"])
            + "|="
            + num(abs(f["p1"] - f["p2"]))
            + " would_agree="
            + ("n/a" if f["human"] else ("yes" if f["would_agree"] else "no"))
            + " radius="
            + (num(desired_radius(f["relabel"], f["a_r"], RADIUS_RATIO)) if not f["human"] else "n/a")
        )
    for arm in ARMS:
        print(
            f"{arm} task_mse {fmt_mean(rows[arm]['task_mse'])} "
            f"robot_mse {fmt_mean(rows[arm]['robot_mse'])}"
        )
    for metric in ("task_mse", "robot_mse"):
        for left, right in (("B", "A"), ("C", "A"), ("C", "B"), ("D", "C"), ("D", "A"), ("D", "B")):
            print(
                f"paired {left}-{right} {metric}: "
                + verdict(rows[left][metric], rows[right][metric])
            )


def hand_calc_block() -> None:
    print("hand_calc 20 percent small-vs-clear factor = " + num(SMALL_FRAC))
    print(
        "hand_calc a_star(s) = A_STAR_BIAS + A_STAR_SLOPE * s = "
        + num(A_STAR_BIAS)
        + " + "
        + num(A_STAR_SLOPE)
        + " * s"
    )
    for s in STEPS:
        print("hand_calc a_star(" + str(s) + ") = " + num(a_star(s)))

    errs = [(a_star(0) - a_star(s)) ** 2 for s in STEPS if not is_human(s)]
    mse = sum(errs) / len(errs)
    print(
        "hand_calc human-only unlabeled task_mse = ("
        + "+".join(num(e) for e in errs)
        + ") / "
        + str(len(errs))
        + " = "
        + num(sum(errs))
        + "/"
        + str(len(errs))
        + " = "
        + num(mse)
    )
    # D on disagree: latest p1 at steps 1,2,3
    d_errs = []
    for s in STEPS:
        if is_human(s):
            continue
        pred = checkpoints("checkpoints_disagree", s)[0]
        d_errs.append((pred - a_star(s)) ** 2)
    print(
        "hand_calc exact-imitate latest unlabeled task_mse on checkpoints_disagree = ("
        + "+".join(num(e) for e in d_errs)
        + ") / "
        + str(len(d_errs))
        + " = "
        + num(sum(d_errs))
        + "/"
        + str(len(d_errs))
        + " = "
        + num(sum(d_errs) / len(d_errs))
    )
    e_errs = [(RELABEL_BIAS - a_star(s)) ** 2 for s in STEPS if not is_human(s)]
    print(
        "hand_calc exact-target RELABEL_BIAS unlabeled task_mse = ("
        + "+".join(num(e) for e in e_errs)
        + ") / "
        + str(len(e_errs))
        + " = "
        + num(sum(e_errs))
        + "/"
        + str(len(e_errs))
        + " = "
        + num(sum(e_errs) / len(e_errs))
    )
    # already_good radius at step 1
    rel, rob = a_star(1), a_star(1)
    print(
        "hand_calc already_good step=1 radius = RADIUS_RATIO * |relabel-robot| = "
        + num(RADIUS_RATIO)
        + " * |"
        + fmt_minus(rel, rob)
        + "| = "
        + num(desired_radius(rel, rob, RADIUS_RATIO))
    )
    # exact_target_lose set at step 1
    rel, rob = RELABEL_BIAS, ROBOT_FAR
    radius = desired_radius(rel, rob, RADIUS_RATIO)
    lo, hi = rel - radius, rel + radius
    print(
        "hand_calc exact_target_lose step=1 radius = "
        + num(RADIUS_RATIO)
        + " * |"
        + fmt_minus(rel, rob)
        + "| = "
        + num(radius)
        + " set=["
        + num(lo)
        + ","
        + num(hi)
        + "] a_star(1)="
        + num(a_star(1))
        + " inside="
        + ("yes" if in_desired_set(a_star(1), rel, rob, RADIUS_RATIO) else "no")
        + " base="
        + num(a_star(0))
        + " inside="
        + ("yes" if in_desired_set(a_star(0), rel, rob, RADIUS_RATIO) else "no")
    )
    # prefix rejection
    p1, p2 = checkpoints("checkpoints_disagree", 1)
    print(
        "hand_calc checkpoints_disagree step=1 abs_diff = |"
        + fmt_minus(p1, p2)
        + "| = "
        + num(abs(p1 - p2))
        + " agree_abs="
        + num(AGREE_ABS)
        + " would_agree="
        + ("yes" if agreement_ok(p1, p2) else "no")
        + " so steps 2 and 3 of the chunk are also rejected"
    )
    p1, p2 = checkpoints("checkpoints_disagree", 2)
    print(
        "hand_calc checkpoints_disagree step=2 abs_diff = |"
        + fmt_minus(p1, p2)
        + "| = "
        + num(abs(p1 - p2))
        + " would_agree_individually="
        + ("yes" if agreement_ok(p1, p2) else "no")
        + " but rejected because step 1 failed"
    )


def print_alternative() -> None:
    print()
    print(
        "named alternative ALT_RADIUS_RATIO="
        + num(ALT_RADIUS_RATIO)
        + " on accepted relabels (exact target after the agreement filter), "
        "same streams, not adopted"
    )
    for name in REGIMES:
        rows, _ = run_regime(name, radius_ratio=ALT_RADIUS_RATIO)
        official, _ = run_regime(name, radius_ratio=RADIUS_RATIO)
        print(
            "alt "
            + name
            + " C_task_mse "
            + fmt_mean(rows["C"]["task_mse"])
            + " official_C_task_mse "
            + fmt_mean(official["C"]["task_mse"])
            + " paired altC-officialC task_mse: "
            + verdict(rows["C"]["task_mse"], official["C"]["task_mse"])
        )


def main() -> None:
    print("sera_autonomous_relabel_toy")
    print("stdlib CPU stand-in, not a diffusion trainer")
    print(
        "seeds="
        + ",".join(str(s) for s in SEEDS)
        + " n_seeds="
        + str(len(SEEDS))
        + " n_traj="
        + str(N_TRAJ)
        + " chunk_len="
        + str(CHUNK_LEN)
        + " human_steps="
        + ",".join(str(s) for s in HUMAN_STEPS)
        + " n_checkpoints="
        + str(N_CHECKPOINTS)
        + " min_checkpoints="
        + str(MIN_CHECKPOINTS)
        + " agree_abs="
        + num(AGREE_ABS)
        + " radius_ratio="
        + num(RADIUS_RATIO)
        + " small_frac="
        + num(SMALL_FRAC)
    )
    print(
        "setup A_STAR_BIAS="
        + num(A_STAR_BIAS)
        + " A_STAR_SLOPE="
        + num(A_STAR_SLOPE)
        + " ROBOT_BAD="
        + num(ROBOT_BAD)
        + " ROBOT_FAR="
        + num(ROBOT_FAR)
        + " RELABEL_BIAS="
        + num(RELABEL_BIAS)
        + " DISAGREE_DELTA="
        + num(DISAGREE_DELTA)
    )
    print(
        "Common random numbers: the shared stream, intervention mask and "
        "checkpoint queries are identical across arms; five seeds repeat "
        "the same deterministic tables so exact-tie cells are identical "
        "on every seed. Seeds do not add jitter."
    )
    hand_calc_block()
    print_regime(
        "already_good",
        "historical robot actions already match a later good policy; "
        "B and C may near-tie each other (keep)",
    )
    print_regime(
        "wrong_auton_agree",
        "early autonomous actions are systematically wrong and later "
        "checkpoints agree on a better action; C consistently better / "
        "lower imitation of the bad historical action (keep)",
    )
    print_regime(
        "checkpoints_disagree",
        "checkpoints disagree at the first unlabeled step; C rejects "
        "that step and later steps of the chunk and does not degrade "
        "to the noisy relabel; an exact-imitate-relabel or B may lose "
        "(keep)",
    )
    print_regime(
        "exact_target_lose",
        "checkpoints agree on a slightly wrong relabel whose desired "
        "set still contains the optimum; the exact-target variant may "
        "lose (keep)",
    )
    print_alternative()
    print()
    print(
        "No universal winner declared; paper tables and tomato-picking "
        "percentages 以论文为准; real robot / diffusion policy / SDP "
        "training / LIBERO / PushT 本页未运行"
    )


if __name__ == "__main__":
    main()
