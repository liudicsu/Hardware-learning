#!/usr/bin/env python3
"""Synthetic Yoshikawa manipulability on a planar 2R arm. Stdlib only.

Model (stated in the lesson prose too): planar 2R arm, the lesson's link lengths
L1 = 0.116 m, L2 = 0.135 m; position Jacobian only (no orientation row); no
joint-position limits, no dynamics, no torque limits; each joint rate is limited
to QD_MAX = 3 rad/s by scaling the whole joint-rate vector uniformly.

  J(q)  = [[-L1 s1 - L2 s12, -L2 s12], [L1 c1 + L2 c12, L2 c12]]
  w(q)  = sqrt(det(J J^T)) = sigma1 * sigma2 = |det J| = L1 L2 |sin q2|
  kappa = sigma1 / sigma2   (condition number of J; = mu1 of Modern Robotics 5.4,
                            and kappa^2 = mu2, the condition number of A = J J^T)

Task: the tip follows a straight radial line at V = 0.05 m/s, then holds the end
point for 0.5 s. Resolved-rate control, explicit Euler at DT = 5 ms:
  qdot = solve(v_ref + KP (p_ref - p)), KP = 20 1/s (KP*DT = 0.1 < 2, so the
  feedback loop e' = -KP e is stable under explicit Euler), then the rate limit.
  A_ignore_w  exact inverse J^-1, no monitor
  B_keep_w    same controller, but the reference is reshaped: its reach is capped
              at R_CAP where w = W_MIN = 0.3 * L1 L2 (the monitor gives up reach)
  C_dls       damped least squares J^T (J J^T + LAM^2 I)^-1, LAM = 0.01 m, no monitor

The feedback sees the tip through a measurement with noise sd 0.1 mm per axis.
Common random numbers: per (regime, seed) one heading of the radial line, one
actuator rate-noise sequence (sd 0.02 rad/s per joint per step) and one
tip-measurement noise sequence are drawn once and applied identically to all
three arms; no arm skips a noise source.
Metrics per seed: min w along the run, RMS tip error against the ORIGINAL
time-indexed reference (mm), final tip error after the hold (mm), peak joint rate
(deg/s), and the RMS commanded joint rate during the hold (deg/s): mostly the
reaction to the two noise sources, plus the decay of any lag left at the end of
the line (time constant 1/KP = 50 ms).
The metrics are blind to joint torque, payload, orientation and joint limits.
No presumed winner. Real SO-101 run: 本页未运行.
"""
from __future__ import annotations

import math
import random

L1, L2 = 0.116, 0.135
REACH = L1 + L2
V = 0.05  # m/s along the radial line
DT = 0.005  # s, explicit Euler step
KP = 20.0  # 1/s, task-space feedback gain
QD_MAX = 3.0  # rad/s per joint (uniform scaling)
LAM = 0.01  # m, DLS damping
W_MAX = L1 * L2
W_MIN = 0.3 * W_MAX  # monitor threshold for B
NOISE = 0.02  # rad/s actuator rate noise sd
MEAS = 1e-4  # m, tip-position measurement noise sd (what the feedback sees)
HOLD = 0.5  # s
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_ignore_w", "B_keep_w", "C_dls")
REGIMES = (("far_from_singularity", 0.130, 0.200), ("near_singularity", 0.150, 0.2505))


def fk(q1: float, q2: float) -> tuple[float, float]:
    return (L1 * math.cos(q1) + L2 * math.cos(q1 + q2), L1 * math.sin(q1) + L2 * math.sin(q1 + q2))


def jac(q1: float, q2: float) -> tuple[float, float, float, float]:
    s1, c1, s12, c12 = math.sin(q1), math.cos(q1), math.sin(q1 + q2), math.cos(q1 + q2)
    return (-L1 * s1 - L2 * s12, -L2 * s12, L1 * c1 + L2 * c12, L2 * c12)


def svd2(j: tuple[float, float, float, float]) -> tuple[float, float]:
    """Singular values of a 2x2 matrix from the eigenvalues of J J^T."""
    a, b, c, d = j
    t = a * a + b * b + c * c + d * d  # trace(J J^T)
    det = a * d - b * c
    disc = math.sqrt(max(t * t / 4.0 - det * det, 0.0))
    return math.sqrt(t / 2.0 + disc), math.sqrt(max(t / 2.0 - disc, 0.0))


def manipulability(q2: float) -> float:
    return W_MAX * abs(math.sin(q2))


def ik_elbow_down(x: float, y: float) -> tuple[float, float]:
    c2 = max(-1.0, min(1.0, (x * x + y * y - L1 * L1 - L2 * L2) / (2 * L1 * L2)))
    q2 = -math.acos(c2)
    return math.atan2(y, x) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2)), q2


def reach_at_w(w_min: float) -> float:
    """Reach (elbow folded) at which w = L1 L2 |sin q2| equals w_min."""
    c2 = math.sqrt(1.0 - (w_min / W_MAX) ** 2)
    return math.sqrt(L1 * L1 + L2 * L2 + 2 * L1 * L2 * c2)


R_CAP = reach_at_w(W_MIN)


def rate(arm: str, j, ex: float, ey: float) -> tuple[float, float]:
    a, b, c, d = j
    if arm == "C_dls":  # J^T (J J^T + lam^2 I)^-1 e
        m11, m12, m22 = a * a + b * b + LAM ** 2, a * c + b * d, c * c + d * d + LAM ** 2
        det = m11 * m22 - m12 * m12
        ux, uy = (m22 * ex - m12 * ey) / det, (m11 * ey - m12 * ex) / det
        return a * ux + c * uy, b * ux + d * uy
    det = a * d - b * c  # exact inverse (A and B)
    return (d * ex - b * ey) / det, (a * ey - c * ex) / det


def run(arm: str, r0: float, r1: float, heading: float, noise: list[tuple[float, float, float, float]]) -> dict:
    t_move = (r1 - r0) / V
    steps = len(noise)
    ux, uy = math.cos(heading), math.sin(heading)
    q1, q2 = ik_elbow_down(r0 * ux, r0 * uy)
    w_min, sq, peak, hold_sq, hold_n = math.inf, 0.0, 0.0, 0.0, 0
    for k in range(steps):
        t = k * DT
        r = r0 + V * min(t, t_move)
        speed = V if t < t_move else 0.0
        if arm == "B_keep_w" and r >= R_CAP:  # reshaped reference: stop at the w threshold
            r, speed = R_CAP, 0.0
        px, py = fk(q1, q2)
        ex, ey = r * ux - (px + noise[k][2]), r * uy - (py + noise[k][3])  # measured tip
        tx = r0 * ux + V * min(t, t_move) * ux - px  # error vs the ORIGINAL reference
        ty = r0 * uy + V * min(t, t_move) * uy - py
        sq += tx * tx + ty * ty
        j = jac(q1, q2)
        w_min = min(w_min, abs(j[0] * j[3] - j[1] * j[2]))
        d1, d2 = rate(arm, j, speed * ux + KP * ex, speed * uy + KP * ey)
        big = max(abs(d1), abs(d2))
        if big > QD_MAX:
            d1, d2 = d1 * QD_MAX / big, d2 * QD_MAX / big
        peak = max(peak, abs(d1), abs(d2))
        if t >= t_move:  # hold phase: noise reaction plus decay of any end-of-line lag
            hold_sq += d1 * d1 + d2 * d2
            hold_n += 1
        q1 += (d1 + noise[k][0]) * DT
        q2 += (d2 + noise[k][1]) * DT
    px, py = fk(q1, q2)
    fx, fy = r1 * ux - px, r1 * uy - py
    return {"w_min": w_min, "rms_mm": 1e3 * math.sqrt(sq / steps), "final_mm": 1e3 * math.hypot(fx, fy),
            "peak_dps": math.degrees(peak), "hold_dps": math.degrees(math.sqrt(hold_sq / hold_n))}


def shared_draws(regime: str, seed: int, steps: int) -> tuple[float, list[tuple[float, float, float, float]]]:
    rng = random.Random(f"{regime}:{seed}")
    heading = rng.uniform(-0.5, 0.5)
    return heading, [(rng.gauss(0.0, NOISE), rng.gauss(0.0, NOISE), rng.gauss(0.0, MEAS), rng.gauss(0.0, MEAS))
                     for _ in range(steps)]


def ms(xs: list[float]) -> tuple[float, float]:
    m = sum(xs) / len(xs)
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def sign_note(diffs: list[float], m: float) -> str:
    """How many seeds disagree in sign with the paired mean (zeros listed apart)."""
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def verdict(xa: list[float], xb: list[float], unit: str = "") -> str:
    """tie: identical on every seed; near-tie: |paired mean| <= paired sd.
    "Consistent" means only |paired mean| > paired sd; the 20 % rule (|mean| <
    20 % of the smaller arm mean) only decides whether a consistent gap is
    called "small" or "clear". The appended sign count says how many seeds
    disagree in sign with the paired mean."""
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "tie: identical on every seed"
    m, s = ms(diffs)
    if abs(m) <= s:
        return f"near-tie / small gap, within seed noise (indistinguishable from 0 within +-{s:.4f}{unit})"
    base = "small but consistent gap, not a tie" if abs(m) < 0.2 * min(ms(xa)[0], ms(xb)[0]) else "clear gap, not a tie"
    return base + "; " + sign_note(diffs, m)


def fmt_pair(m: float, s: float) -> str:
    """Paired mean+-sd; extra decimals when 4 would print a signed zero such as -0.0000."""
    if m != 0.0 and abs(m) < 5e-5:
        return f"{m:.6f}+-{s:.6f}"
    return f"{m:.4f}+-{s:.4f}"


def main() -> None:
    print("planar 2R L1=0.116 L2=0.135 reach=0.251 m; w=sqrt(det(J J^T))=L1*L2*|sin q2|")
    print(f"W_MAX={W_MAX:.6f} m^2 W_MIN=0.3*W_MAX={W_MIN:.6f} m^2 -> R_CAP={R_CAP:.4f} m")
    print("config q2_deg sigma1 sigma2 w=s1*s2 L1L2|sin q2| kappa=s1/s2 kappa^2")
    for deg in (-90.0, -60.0, -30.0, -10.0, -3.0, -1.0):
        s1, s2 = svd2(jac(0.3, math.radians(deg)))
        print(f"  {deg:6.1f} {s1:.5f} {s2:.6f} {s1 * s2:.6f} {manipulability(math.radians(deg)):.6f} "
              f"{s1 / s2:9.2f} {(s1 / s2) ** 2:11.1f}")
    print(f"seeds={len(SEEDS)} V={V} m/s DT={DT} s KP={KP} QD_MAX={QD_MAX} rad/s LAM={LAM} m noise={NOISE} rad/s meas={MEAS * 1e3} mm")
    print("regime arm w_min(m^2) rms_mm final_mm peak_deg_per_s hold_rate_rms_deg_per_s  (mean+-sd over seeds)")
    keys = ("w_min", "rms_mm", "final_mm", "peak_dps", "hold_dps")
    summary: dict[str, dict[str, float]] = {}
    for regime, r0, r1 in REGIMES:
        steps = int(round(((r1 - r0) / V + HOLD) / DT))
        res = {arm: {k: [] for k in keys} for arm in ARMS}
        for seed in SEEDS:
            heading, noise = shared_draws(regime, seed, steps)
            for arm in ARMS:
                out = run(arm, r0, r1, heading, noise)
                for k in keys:
                    res[arm][k].append(out[k])
        summary[regime] = {arm: min(res[arm]["w_min"]) for arm in ARMS}
        for arm in ARMS:
            cells = [ms(res[arm][k]) for k in keys]
            print(f"{regime} {arm} " + " ".join(
                f"{m:.6f}+-{s:.6f}" if k == "w_min" else f"{m:.3f}+-{s:.3f}" for k, (m, s) in zip(keys, cells)))
        for a, b in (("A_ignore_w", "B_keep_w"), ("C_dls", "A_ignore_w")):
            for k in ("rms_mm", "final_mm", "hold_dps"):
                d = ms([x - y for x, y in zip(res[a][k], res[b][k])])
                unit = " mm" if k.endswith("_mm") else " deg/s"
                print(f"{regime} paired {a[0]}-{b[0]} {k} {fmt_pair(*d)}: {verdict(res[a][k], res[b][k], unit)}")
    far, near = summary["far_from_singularity"], summary["near_singularity"]
    print(f"far_from_singularity: lowest w over all seeds {far['B_keep_w']:.6f} > W_MIN, so B's monitor never fires and A and B "
          "run the same commands on the same draws")
    print(f"near_singularity: B's lowest w over all seeds {near['B_keep_w']:.6f} sits just below W_MIN {W_MIN:.6f} (a reshaped reference, "
          f"not a hard barrier: shared noise jitters the held pose); it stops {1e3 * (0.2505 - R_CAP):.2f} mm short "
          "of 0.2505 m by design")
    print(f"near_singularity: A's lowest w {near['A_ignore_w']:.6f}; A hits the {math.degrees(QD_MAX):.1f} deg/s "
          "rate limit and has the largest hold-phase joint rate (its reaction to the shared noise)")
    print("No winner declared: w and kappa flag the singular direction; what to give up (reach, speed, accuracy) is a task choice")
    print("Real SO-101 / MoveIt run: 本页未运行; Modern Robotics numbers 以原文为准")


if __name__ == "__main__":
    main()
