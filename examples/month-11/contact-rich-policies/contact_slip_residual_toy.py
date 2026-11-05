#!/usr/bin/env python3
"""contact_slip_residual_toy.py: same-frame velocity residual + slip proxy (stdlib).

A planar 2-link arm (L1, L2 in m) pushes an object along a table. Every
residual compares LIKE quantities: the fingertip velocity predicted from
proprioception, v_pred = J(q_meas) @ qdot_meas (forward kinematics, world
frame, m/s), against a synthetic measured object/contact velocity v_meas
(world frame, m/s). Both are then projected on the table tangent t and normal
n. A force (N) is never subtracted from a velocity (m/s): the Vel guard below
refuses mixed units or frames.

Contact break is read ONLY from an explicit assumed sensor channel: a normal-
force reading f_n (N) thresholded into a contact flag (toy assumption written
in the lesson). The normal velocity residual is printed but never used to
decide "break".

Slip is a toy PROXY: while the contact flag is true, the tangential residual
(mean over SLIP_WINDOW ticks) above SLIP_THRESH for SLIP_HOLD ticks raises a
slip alarm. It is not a GelSight / AnySkin slip classifier.

Scenarios stick / slip / break share one seeded noise stream (joint, velocity
and force noise). The contact-Jacobian idea is the same as 11.6's J_c qdot;
this toy does not redo the floating-base projector.
usage: python3 contact_slip_residual_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 117
DT = 0.01                 # s
HORIZON = 200             # ticks
L1, L2 = 0.30, 0.25       # m
ONSET = 100               # tick where slip or break begins
SLIP_RAMP = 20            # ticks to reach full slip speed
SLIP_SPEED = 0.05         # m/s tangential lag at full slip
F_CONTACT = 5.0           # N while pressing
F_THRESH = 2.0            # N: assumed contact-flag threshold
Q_NOISE = 0.001           # rad
QD_NOISE = 0.01           # rad/s
V_NOISE = 0.004           # m/s on the measured velocity
F_NOISE = 0.3             # N
SLIP_WINDOW = 5           # ticks
SLIP_THRESH = 0.02        # m/s
SLIP_HOLD = 3             # consecutive ticks over threshold
TANGENT = (1.0, 0.0)      # table tangent, world frame
NORMAL = (0.0, 1.0)       # table normal, world frame


class Vel:
    """A 2-D quantity tagged with unit and frame; only m/s in 'world' here."""

    def __init__(self, x: float, y: float, unit: str, frame: str) -> None:
        self.x, self.y, self.unit, self.frame = x, y, unit, frame

    def __sub__(self, other: "Vel") -> "Vel":
        if self.unit != other.unit or self.frame != other.frame:
            raise TypeError(f"refuse {self.unit}@{self.frame} - {other.unit}@{other.frame}")
        return Vel(self.x - other.x, self.y - other.y, self.unit, self.frame)

    def along(self, axis: tuple[float, float]) -> float:
        return self.x * axis[0] + self.y * axis[1]


def joints(k: int) -> tuple[float, float, float, float]:
    t = k * DT
    w = 2 * math.pi * 0.5
    q1 = 0.5 + 0.25 * math.sin(w * t)
    q2 = 1.1 + 0.15 * math.sin(2 * w * t)
    return q1, q2, 0.25 * w * math.cos(w * t), 0.15 * 2 * w * math.cos(2 * w * t)


def fk_velocity(q1: float, q2: float, qd1: float, qd2: float) -> Vel:
    """v = J(q) qdot for the fingertip of a planar 2-link arm (world, m/s)."""
    s1, c1 = math.sin(q1), math.cos(q1)
    s12, c12 = math.sin(q1 + q2), math.cos(q1 + q2)
    vx = (-L1 * s1 - L2 * s12) * qd1 - L2 * s12 * qd2
    vy = (L1 * c1 + L2 * c12) * qd1 + L2 * c12 * qd2
    return Vel(vx, vy, "m/s", "world")


def shared_noise() -> list[tuple[float, ...]]:
    rng = random.Random(SEED)
    return [tuple(rng.gauss(0.0, s) for s in
                  (Q_NOISE, Q_NOISE, QD_NOISE, QD_NOISE, V_NOISE, V_NOISE, F_NOISE))
            for _ in range(HORIZON)]


def run(scenario: str, noise: list[tuple[float, ...]], gated: bool = True) -> dict:
    window: list[float] = []
    over = 0
    slip_alarm_at = break_flag_at = None
    false_slip = 0
    pre, post = [], []
    max_normal_resid_post = 0.0
    for k in range(HORIZON):
        q1, q2, qd1, qd2 = joints(k)
        nq1, nq2, nqd1, nqd2, nvx, nvy, nf = noise[k]
        v_true = fk_velocity(q1, q2, qd1, qd2)
        v_pred = fk_velocity(q1 + nq1, q2 + nq2, qd1 + nqd1, qd2 + nqd2)
        # Synthetic object velocity in the same world frame (m/s).
        lag = 0.0
        if scenario == "slip" and k >= ONSET:
            lag = SLIP_SPEED * min(1.0, (k - ONSET + 1) / SLIP_RAMP)
        if scenario == "break" and k >= ONSET:
            obj = Vel(0.0, 0.0, "m/s", "world")   # object left behind
            f_n = 0.0
        else:
            obj = Vel(v_true.x - lag * TANGENT[0], v_true.y - lag * TANGENT[1], "m/s", "world")
            f_n = F_CONTACT
        v_meas = Vel(obj.x + nvx, obj.y + nvy, "m/s", "world")
        f_meas = f_n + nf                          # N: separate channel
        contact = f_meas > F_THRESH                # assumed sensor channel
        r = v_meas - v_pred                        # m/s - m/s, same frame
        r_t, r_n = r.along(TANGENT), r.along(NORMAL)
        (post if k >= ONSET else pre).append(math.hypot(r.x, r.y))
        if k >= ONSET:
            max_normal_resid_post = max(max_normal_resid_post, abs(r_n))
        if not contact and gated:
            if break_flag_at is None and k >= ONSET:
                break_flag_at = k
            window.clear()
            over = 0
            continue                               # slip proxy suspended
        window.append(abs(r_t))
        if len(window) > SLIP_WINDOW:
            window.pop(0)
        mean_t = sum(window) / len(window)
        over = over + 1 if mean_t > SLIP_THRESH else 0
        if over >= SLIP_HOLD:
            if scenario != "stick" and k >= ONSET:
                if slip_alarm_at is None:
                    slip_alarm_at = k
            else:
                false_slip += 1
    rms = lambda xs: math.sqrt(sum(x * x for x in xs) / len(xs))
    return {"pre": rms(pre), "post": rms(post), "slip_at": slip_alarm_at,
            "break_at": break_flag_at, "false_slip": false_slip,
            "max_rn_post": max_normal_resid_post}


def main() -> None:
    noise = shared_noise()
    print(f"seed={SEED} dt_s={DT} horizon={HORIZON} onset_tick={ONSET} "
          f"slip_speed_mps={SLIP_SPEED} ramp_ticks={SLIP_RAMP}")
    print("residual r = v_meas - J(q_meas) qdot_meas  [m/s, world frame; t=(1,0) n=(0,1)]")
    print(f"contact flag = f_n > {F_THRESH} N (assumed sensor channel); "
          f"slip proxy: mean|r_t| over {SLIP_WINDOW} > {SLIP_THRESH} m/s for {SLIP_HOLD} ticks")
    try:
        _ = Vel(5.0, 0.0, "N", "world") - fk_velocity(*joints(0))
        guard = "accepted (BUG)"
    except TypeError as exc:
        guard = str(exc)
    print(f"unit_guard: {guard}")
    print(f"{'scenario':<8} {'rms_r_pre':>10} {'rms_r_post':>11} {'slip_alarm_tick':>15} "
          f"{'slip_latency_ms':>15} {'flag_drop_tick':>14} {'false_slip_ticks':>16}")
    res = {}
    for sc in ("stick", "slip", "break"):
        r = res[sc] = run(sc, noise)
        lat = "-" if r["slip_at"] is None else f"{(r['slip_at'] - ONSET) * DT * 1000:.0f}"
        print(f"{sc:<8} {r['pre']:>10.4f} {r['post']:>11.4f} "
              f"{'-' if r['slip_at'] is None else r['slip_at']:>15} {lat:>15} "
              f"{'-' if r['break_at'] is None else r['break_at']:>14} {r['false_slip']:>16d}")
    ungated = run("break", noise, gated=False)
    print(f"break_ungated: slip_alarm_tick={ungated['slip_at']} "
          "(without the contact flag the proxy would call a break 'slip')")
    print(f"break: max|r_n| after onset = {res['break']['max_rn_post']:.4f} m/s "
          "(printed, not used to decide break)")
    assert res["stick"]["false_slip"] == 0 and res["slip"]["slip_at"] is not None
    assert res["break"]["break_at"] == ONSET and res["break"]["slip_at"] is None
    assert res["break"]["false_slip"] == 0 and ungated["slip_at"] is not None
    assert all(abs(res[s]["pre"] - res["stick"]["pre"]) < 1e-12 for s in res)
    print("ok: shared noise (identical pre-onset residuals); break from contact flag only; "
          "slip = toy proxy, not a GelSight/AnySkin classifier")


if __name__ == "__main__":
    main()
