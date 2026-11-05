#!/usr/bin/env python3
"""lqr_model_error_toy.py: observer vs oracle under model error (stdlib).

The observer sees ONLY the scalar measurement y = C x + v. Full-state feedback
is an ORACLE upper reference that reads the privileged true state x — it is
NOT an equal-information baseline. Arm names make that explicit:
  oracle_fullstate          u = -K x_true   (privileged)
  observer_output_feedback  Luenberger xhat from y only; u = -K xhat
  open_loop                 u = 0

Gain K and observer gain L are designed on the NOMINAL (A, B) by pole
placement (Ackermann for this 2-state plant). Evaluation runs on a PERTURBED
plant A_pert with the SAME process-noise realisation across arms. This is
model-error sensitivity awareness, NOT H∞ design, and NOT a discrete-Riccati
optimality claim (lesson 5.2's lqr_sim.py already covers Riccati LQR).

The scored cost is sum (x0² + 0.1 x1² + 0.01 u²): under model error the
observer can look similar on position RMS alone (its lag filters) while
spending far more control effort and leaving more velocity — the cost makes
the privileged-information gap visible without claiming equal-info superiority.

Luenberger / observability structure: UC Berkeley CE295 notes, Ch. 2 State
Estimation (https://ecal.studentorg.berkeley.edu/files/ce295/CH02-StateEstimation.pdf).
Simon, Optimal State Estimation (Wiley, 2006) is the standard KF book citation;
no free full-text URL is claimed.
usage: python3 lqr_model_error_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 52
DT = 0.02                 # s
HORIZON = 250             # steps ≈ 5 s
M = 1.0                   # kg
B_NOM = 0.40              # N·s/m  (design model)
B_PERT = 0.10             # lighter damping on the evaluation plant
PROCESS_STD = 0.04        # shared process noise on velocity (discrete)
MEAS_STD = 0.05           # observer measurement noise on y = position (m)
K_POLES = (0.92, 0.88)
L_POLES = (0.85, 0.80)
# Running cost weights for the scored sum.
QX, QV, RU = 1.0, 0.1, 0.01


def mat_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]


def eye(n):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def scale_mat(s, A):
    return [[s * A[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def cont_to_disc(A_c, B_c, dt):
    """Forward-Euler discretisation (teaching toy; not zoh-exact)."""
    I = eye(len(A_c))
    A = [[I[i][j] + dt * A_c[i][j] for j in range(2)] for i in range(2)]
    B = [[dt * B_c[i][0]] for i in range(2)]
    return A, B


def char_poly_poles(p1, p2):
    return [1.0, -(p1 + p2), p1 * p2]


def adjugate_2(M):
    return [[M[1][1], -M[0][1]], [-M[1][0], M[0][0]]]


def det_2(M):
    return M[0][0] * M[1][1] - M[0][1] * M[1][0]


def ackermann_K(A, B, poles):
    AB = mat_mul(A, B)
    Cc = [[B[0][0], AB[0][0]], [B[1][0], AB[1][0]]]
    assert abs(det_2(Cc)) > 1e-9, "not controllable"
    _, a1, a0 = char_poly_poles(*poles)
    A2 = mat_mul(A, A)
    alphaA = [[A2[i][j] + a1 * A[i][j] + a0 * (1.0 if i == j else 0.0)
               for j in range(2)] for i in range(2)]
    inv = scale_mat(1.0 / det_2(Cc), adjugate_2(Cc))
    eT = inv[1]
    return [eT[0] * alphaA[0][j] + eT[1] * alphaA[1][j] for j in range(2)]


def ackermann_L(A, C, poles):
    CA = mat_mul(C, A)
    Ob = [[C[0][0], C[0][1]], [CA[0][0], CA[0][1]]]
    assert abs(det_2(Ob)) > 1e-9, "not observable"
    _, a1, a0 = char_poly_poles(*poles)
    A2 = mat_mul(A, A)
    alphaA = [[A2[i][j] + a1 * A[i][j] + a0 * (1.0 if i == j else 0.0)
               for j in range(2)] for i in range(2)]
    inv = scale_mat(1.0 / det_2(Ob), adjugate_2(Ob))
    col = [inv[0][1], inv[1][1]]
    return [alphaA[i][0] * col[0] + alphaA[i][1] * col[1] for i in range(2)]


def build(b):
    A_c = [[0.0, 1.0], [0.0, -b / M]]
    B_c = [[0.0], [1.0 / M]]
    return cont_to_disc(A_c, B_c, DT)


def simulate(arm, A_nom, A_pert, B, K, L, C, noise_w, noise_v, x0):
    x = list(x0)
    xhat = [0.0, 0.0]
    xs, us = [], []
    for k in range(HORIZON):
        if arm == "oracle_fullstate":
            # Privileged true state — NOT the same information as the observer.
            u = -(K[0] * x[0] + K[1] * x[1])
        elif arm == "observer_output_feedback":
            u = -(K[0] * xhat[0] + K[1] * xhat[1])
        else:
            u = 0.0
        w = [0.0, noise_w[k]]
        x_next = [A_pert[i][0] * x[0] + A_pert[i][1] * x[1] + B[i][0] * u + w[i]
                  for i in range(2)]
        y = C[0][0] * x[0] + C[0][1] * x[1] + noise_v[k]
        if arm == "observer_output_feedback":
            yhat = C[0][0] * xhat[0] + C[0][1] * xhat[1]
            innov = y - yhat
            xhat = [A_nom[i][0] * xhat[0] + A_nom[i][1] * xhat[1]
                    + B[i][0] * u + L[i] * innov for i in range(2)]
        x = x_next
        xs.append(x[:])
        us.append(u)
    return xs, us


def rms(vals):
    return math.sqrt(sum(v * v for v in vals) / len(vals))


def cost(xs, us):
    return sum(QX * x[0] * x[0] + QV * x[1] * x[1] + RU * u * u
               for x, u in zip(xs, us))


def main() -> None:
    A_nom, B = build(B_NOM)
    A_pert, _ = build(B_PERT)
    C = [[1.0, 0.0]]
    K = ackermann_K(A_nom, B, K_POLES)
    L = ackermann_L(A_nom, C, L_POLES)

    rng = random.Random(SEED)
    noise_w = [rng.gauss(0.0, PROCESS_STD) for _ in range(HORIZON)]
    noise_v = [rng.gauss(0.0, MEAS_STD) for _ in range(HORIZON)]
    x0 = [1.0, 0.0]

    print(f"seed={SEED} dt={DT} horizon={HORIZON} m={M} b_nom={B_NOM} b_pert={B_PERT}")
    print(f"design: pole-placement on nominal (A,B); K_poles={list(K_POLES)} L_poles={list(L_POLES)}")
    print(f"K=[{K[0]:.4f}, {K[1]:.4f}]  L=[{L[0]:.4f}, {L[1]:.4f}]")
    print("oracle_fullstate uses privileged true x; observer uses only y=Cx+noise")
    print("NOT H-infinity; NOT equal-info baseline; shared process noise across arms")
    print(f"cost = sum(x_pos^2 + {QV}*x_vel^2 + {RU}*u^2) over the horizon")
    print()
    hdr = f"{'arm':<28} {'rms_pos':>10} {'rms_vel':>10} {'rms_u':>10} {'cost':>12} {'final_pos':>10}"
    print(hdr)
    results = {}
    for arm in ("open_loop", "oracle_fullstate", "observer_output_feedback"):
        xs, us = simulate(arm, A_nom, A_pert, B, K, L, C, noise_w, noise_v, x0)
        rp, rv, ru = rms([x[0] for x in xs]), rms([x[1] for x in xs]), rms(us)
        c = cost(xs, us)
        results[arm] = (rp, rv, ru, c, xs[-1][0])
        print(f"{arm:<28} {rp:10.4f} {rv:10.4f} {ru:10.4f} {c:12.2f} {xs[-1][0]:10.4f}")

    c_or = results["oracle_fullstate"][3]
    c_ob = results["observer_output_feedback"][3]
    c_ol = results["open_loop"][3]
    assert c_or < c_ob < c_ol, f"cost order oracle<observer<open failed: {c_or}, {c_ob}, {c_ol}"
    assert results["oracle_fullstate"][2] < results["observer_output_feedback"][2], "oracle should spend less |u|"
    print("ok: oracle_fullstate (privileged x) cost < observer_output_feedback cost < open_loop; "
          "model-error sweep on perturbed plant (real hardware 本页未运行)")


if __name__ == "__main__":
    main()
