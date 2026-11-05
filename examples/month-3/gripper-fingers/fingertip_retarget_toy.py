#!/usr/bin/env python3
"""fingertip_retarget_toy.py: fingertip retarget under embodiment gap (stdlib).

Lesson-defined planar multifinger hand (NOT a vendor URDF). Four fingers ×
three revolute joints = 12 actuated DoF in this toy. LEAP Hand is 16 DoF per
its paper (arXiv 2309.06440: policy observes / commands 16 joint angles) —
以论文为准; this lesson does not require buying LEAP / Allegro / a mocap glove.

Avoid tautology (§9): fingertip IK trivially beats joint-angle copy on
fingertip RMSE when targets are reachable on an identical kinematic chain.
This toy therefore includes:
  - human / robot link-length ratio (embodiment gap)
  - robot joint limits
  - some partially unreachable targets
  - a scaled-target variant (human targets × ratio) so IK is not doomed
  - a second metric (joint-space smoothness / limit violations) so neither
    arm wins by construction

Arms (same target cloud + shared noise):
  joint_copy     map human joint angles 1:1 onto the robot (ignores link gap)
  fingertip_ik   per-finger planar IK / clamped least-squares to robot links

Metrics: fingertip RMSE (m); joint-limit violations (count of clamps);
mean |Δq| joint-space smoothness (rad/step).
usage: python3 fingertip_retarget_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 73
N_FRAMES = 40
N_FINGERS = 4
N_JOINTS = 3          # per finger; lesson-defined 12 DoF total
# Human link lengths (m) — index-like planar chain.
HUMAN_LINKS = (0.045, 0.025, 0.020)
# Robot links are shorter (embodiment gap). Ratio ≈ robot/human.
LINK_RATIO = 0.75
ROBOT_LINKS = tuple(LINK_RATIO * L for L in HUMAN_LINKS)
# Robot joint limits (rad). Human demo uses a wider range, so some poses clip.
ROBOT_Q_MIN = (-0.2, -0.1, -0.1)
ROBOT_Q_MAX = (1.2, 1.4, 1.0)
# Shared measurement noise on human joint angles (rad).
Q_NOISE = 0.01


def clamp(q: float, lo: float, hi: float) -> tuple[float, bool]:
    if q < lo:
        return lo, True
    if q > hi:
        return hi, True
    return q, False


def fk(links: tuple[float, ...], q: tuple[float, ...]) -> tuple[float, float]:
    """Planar open-chain fingertip XY in the finger's local frame."""
    x = y = 0.0
    a = 0.0
    for L, qi in zip(links, q):
        a += qi
        x += L * math.cos(a)
        y += L * math.sin(a)
    return x, y


def finger_origin(i: int) -> tuple[float, float]:
    """Spread fingers along a palm x-axis (lesson frame, m)."""
    return (0.02 * (i - 1.5), 0.0)


def human_trajectory(rng: random.Random) -> list[list[tuple[float, float, float]]]:
    """N_FRAMES × N_FINGERS joint triples (human)."""
    frames = []
    for k in range(N_FRAMES):
        t = k / max(N_FRAMES - 1, 1)
        fingers = []
        for i in range(N_FINGERS):
            # Opening → closing curl; outer fingers curl a bit more.
            base = 0.15 + 0.9 * t + 0.08 * i
            q = (
                base + 0.15 * math.sin(2 * math.pi * t + 0.4 * i),
                0.3 + 1.1 * t + 0.05 * math.sin(4 * math.pi * t),
                0.2 + 0.7 * t,
            )
            # Some frames deliberately exceed robot limits (unreachable / clip).
            if k in (5, 12, 28) and i in (0, 3):
                q = (q[0] + 0.35, q[1] + 0.45, q[2] + 0.25)
            noise = tuple(rng.gauss(0.0, Q_NOISE) for _ in range(N_JOINTS))
            fingers.append(tuple(qi + ni for qi, ni in zip(q, noise)))
        frames.append(fingers)
    return frames


def ik_one(links: tuple[float, ...], target_xy: tuple[float, float],
           q_seed: tuple[float, ...]) -> tuple[tuple[float, ...], int]:
    """Damped least-squares IK for a 3R planar finger; clamp to robot limits.

    Returns (q_robot, n_limit_violations_on_final_clamp).
    """
    q = list(q_seed)
    tx, ty = target_xy
    clamps = 0
    for _ in range(25):
        x, y = fk(links, tuple(q))
        ex, ey = tx - x, ty - y
        if ex * ex + ey * ey < 1e-10:
            break
        # Jacobian of fingertip wrt joint angles.
        a1 = q[0]
        a2 = q[0] + q[1]
        a3 = q[0] + q[1] + q[2]
        L1, L2, L3 = links
        # dx/dq, dy/dq
        j = [
            (-L1 * math.sin(a1) - L2 * math.sin(a2) - L3 * math.sin(a3),
             L1 * math.cos(a1) + L2 * math.cos(a2) + L3 * math.cos(a3)),
            (-L2 * math.sin(a2) - L3 * math.sin(a3),
             L2 * math.cos(a2) + L3 * math.cos(a3)),
            (-L3 * math.sin(a3),
             L3 * math.cos(a3)),
        ]
        # J^T e step with damping
        lam = 1e-3
        # Solve (J J^T + lam I) delta_x = e, then dq = J^T …
        # Simpler: dq_i = (J_i · e) / (|J_i|^2 + lam)
        for i in range(3):
            jx, jy = j[i]
            denom = jx * jx + jy * jy + lam
            dq = (jx * ex + jy * ey) / denom
            q[i] += 0.5 * dq  # step size
        # soft clamp during iteration
        for i in range(3):
            q[i], hit = clamp(q[i], ROBOT_Q_MIN[i], ROBOT_Q_MAX[i])
            if hit:
                clamps += 1
    # final clamp count (unique joints that sit on a limit)
    final_hits = 0
    out = []
    for i in range(3):
        qi, hit = clamp(q[i], ROBOT_Q_MIN[i], ROBOT_Q_MAX[i])
        out.append(qi)
        if hit:
            final_hits += 1
    return tuple(out), final_hits


def eval_arm(name: str, human_frames: list, scale_targets: bool) -> dict:
    tip_err_sq = 0.0
    n_tips = 0
    limit_viol = 0
    smooth_acc = 0.0
    smooth_n = 0
    prev_q: list[tuple[float, ...] | None] = [None] * N_FINGERS
    # seed IK at mid-range
    q_seed = tuple(0.5 * (ROBOT_Q_MIN[i] + ROBOT_Q_MAX[i]) for i in range(N_JOINTS))

    for fingers in human_frames:
        for i, q_h in enumerate(fingers):
            ox, oy = finger_origin(i)
            hx, hy = fk(HUMAN_LINKS, q_h)
            target = (ox + hx, oy + hy)
            if scale_targets:
                # scale the fingertip offset from palm by LINK_RATIO
                target = (ox + LINK_RATIO * hx, oy + LINK_RATIO * hy)

            if name == "joint_copy":
                q_r_list = []
                hits = 0
                for j in range(N_JOINTS):
                    qi, hit = clamp(q_h[j], ROBOT_Q_MIN[j], ROBOT_Q_MAX[j])
                    q_r_list.append(qi)
                    if hit:
                        hits += 1
                q_r = tuple(q_r_list)
                limit_viol += hits
            else:
                # IK toward target in finger-local coordinates
                local_tgt = (target[0] - ox, target[1] - oy)
                q_r, hits = ik_one(ROBOT_LINKS, local_tgt, q_seed if prev_q[i] is None else prev_q[i])
                limit_viol += hits

            rx, ry = fk(ROBOT_LINKS, q_r)
            # Compare robot fingertip to the (possibly scaled) target.
            ex = (ox + rx) - target[0]
            ey = (oy + ry) - target[1]
            tip_err_sq += ex * ex + ey * ey
            n_tips += 1

            if prev_q[i] is not None:
                smooth_acc += sum(abs(q_r[j] - prev_q[i][j]) for j in range(N_JOINTS))
                smooth_n += N_JOINTS
            prev_q[i] = q_r

    rmse = math.sqrt(tip_err_sq / n_tips)
    smooth = smooth_acc / max(smooth_n, 1)
    return {
        "arm": name,
        "scale_targets": scale_targets,
        "fingertip_rmse_m": rmse,
        "limit_violations": limit_viol,
        "mean_abs_dq": smooth,
        "n_tips": n_tips,
    }


def main() -> None:
    rng = random.Random(SEED)
    human = human_trajectory(rng)

    variants = [
        ("raw_targets", False),
        ("scaled_targets", True),
    ]
    print(f"seed={SEED} frames={N_FRAMES} fingers={N_FINGERS} joints_per_finger={N_JOINTS} "
          f"lesson_DoF={N_FINGERS * N_JOINTS}")
    print(f"human_links_m={HUMAN_LINKS} robot_links_m=({', '.join(f'{L:.4f}' for L in ROBOT_LINKS)}) "
          f"link_ratio={LINK_RATIO}")
    print(f"robot_q_limits_rad min={ROBOT_Q_MIN} max={ROBOT_Q_MAX}")
    print("LEAP Hand = 16 DoF per arXiv:2309.06440 (以论文为准); toy is lesson-defined 12 DoF; "
          "no hand purchase")
    print(f"{'variant':<16} {'arm':<14} {'rmse_m':>10} {'limit_viol':>11} {'mean_|dq|':>10}")

    results = []
    for vname, scale in variants:
        for arm in ("joint_copy", "fingertip_ik"):
            # fresh noise already baked into `human`; both arms see the same frames
            r = eval_arm(arm, human, scale)
            r["variant"] = vname
            results.append(r)
            print(f"{vname:<16} {arm:<14} {r['fingertip_rmse_m']:10.5f} "
                  f"{r['limit_violations']:11d} {r['mean_abs_dq']:10.5f}")

    raw_copy = next(r for r in results if r["variant"] == "raw_targets" and r["arm"] == "joint_copy")
    raw_ik = next(r for r in results if r["variant"] == "raw_targets" and r["arm"] == "fingertip_ik")
    sc_copy = next(r for r in results if r["variant"] == "scaled_targets" and r["arm"] == "joint_copy")
    sc_ik = next(r for r in results if r["variant"] == "scaled_targets" and r["arm"] == "fingertip_ik")

    assert raw_ik["fingertip_rmse_m"] < raw_copy["fingertip_rmse_m"], (
        "IK should reduce fingertip RMSE vs joint copy on raw targets")
    assert sc_ik["fingertip_rmse_m"] < sc_copy["fingertip_rmse_m"]
    # Neither arm wins by construction: joint_copy can be smoother and/or hit fewer
    # iterative clamps; we require at least one second-metric edge for joint_copy
    # on the raw variant.
    copy_smoother = raw_copy["mean_abs_dq"] < raw_ik["mean_abs_dq"]
    copy_fewer_limits = raw_copy["limit_violations"] <= raw_ik["limit_violations"]
    assert copy_smoother or copy_fewer_limits, (
        "joint_copy must win at least one secondary metric (smoothness or limits)")
    assert raw_copy["limit_violations"] > 0 or raw_ik["limit_violations"] > 0, (
        "unreachable / over-limit frames must produce some violations")
    print("ok: embodiment gap + limits + scaled variant; IK better on RMSE; "
          "joint_copy keeps a secondary metric; LEAP 16 DoF 以论文为准; "
          "real hand / mocap 本页未运行")


if __name__ == "__main__":
    main()
