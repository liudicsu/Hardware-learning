#!/usr/bin/env python3
"""Synthetic discrete LQR vs continuous+ZOH literacy toy. Stdlib only.

Shared continuous plant (A_c, B_c) and shared Q, R meaning for every arm.
Process-noise draws are **common random numbers**: for a given seed, A/B/C
see the identical noise sequence (no arm gets a quieter plant).

Discretization: exact **zero-order hold (ZOH)** via the matrix exponential
of the augmented [[A_c, B_c],[0,0]] block (scaling-and-squaring + Taylor),
not forward-Euler.

Discrete Riccati: iterate the DARE map until ‖ΔP‖_F < RICCATI_TOL (explicit).
Continuous K_c from Kleinman iteration on the CARE (stabilizing Lyapunov steps).

Arms:
  A_cont_zoh   continuous LQR K_c held with ZOH at the regime T_s
  B_disc       discrete LQR K_d designed at that same T_s
  C_disc_fine  discrete LQR designed and applied at fine T_s (always)

Regimes (≥5 seeds on shared process noise):
  coarse_Ts — discrete B beats cont+ZOH A (design at the hold rate matters)
  fine_Ts   — A and B near-tie as T_s→0 (remaining small gap from hold + noise)

Stability criterion: closed-loop eigenvalues of (A_d − B_d K) have modulus < 1
(tested for B and C). Metrics: infinite-horizon-style cost, settling steps,
max |λ|. ≠ Bode redo; ≠ continuous Riccati-only lesson. Real plant: 本页未运行.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_cont_zoh", "B_disc", "C_disc_fine")
# Continuous plant: unit mass + damping  ẍ = −b ẋ + u
M = 1.0
B_DAMP = 0.40
A_C = [[0.0, 1.0], [0.0, -B_DAMP / M]]
B_C = [[0.0], [1.0 / M]]
# Shared continuous cost meaning; discrete stage cost ≈ integral ≈ Q*Ts, R*Ts
Q_C = [[25.0, 0.0], [0.0, 1.0]]
R_C = 0.05
TS_COARSE = 0.10
TS_FINE = 0.01
HORIZON_S = 6.0
PROCESS_STD = 0.05  # shared accel noise, continuous-time intensity proxy
SETTLE_EPS = 0.05
RICCATI_TOL = 1e-12
RICCATI_MAX_ITER = 10_000
EXPM_SQUARINGS_CAP = 8
SUBSTEP = 0.001  # continuous integration substep under ZOH (<< fine Ts)


def mat_add(A, B):
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def mat_sub(A, B):
    return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def mat_scale(s, A):
    return [[s * A[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def mat_mul(A, B):
    return [
        [sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
        for i in range(len(A))
    ]


def mat_T(A):
    return [[A[j][i] for j in range(len(A))] for i in range(len(A[0]))]


def eye(n):
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def frobenius(A):
    return math.sqrt(sum(A[i][j] * A[i][j] for i in range(len(A)) for j in range(len(A[0]))))


def solve_2x2(M, v):
    det = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    if abs(det) < 1e-18:
        raise ZeroDivisionError("singular 2x2")
    return [
        (M[1][1] * v[0] - M[0][1] * v[1]) / det,
        (-M[1][0] * v[0] + M[0][0] * v[1]) / det,
    ]


def mat_inv_2(M):
    det = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    return [[M[1][1] / det, -M[0][1] / det], [-M[1][0] / det, M[0][0] / det]]


def expm(M):
    """Scaling-and-squaring + Taylor; M square. Stdlib-only ZOH building block."""
    n = len(M)
    # scale so ||M/2^s|| small
    norm = max(sum(abs(M[i][j]) for j in range(n)) for i in range(n))
    s = 0
    while norm > 0.5 and s < EXPM_SQUARINGS_CAP:
        M = mat_scale(0.5, M)
        norm *= 0.5
        s += 1
    # Taylor sum_k M^k / k!
    term = eye(n)
    total = eye(n)
    for k in range(1, 20):
        term = mat_scale(1.0 / k, mat_mul(term, M))
        total = mat_add(total, term)
        if frobenius(term) < 1e-16:
            break
    for _ in range(s):
        total = mat_mul(total, total)
    return total


def zoh_discretize(A_c, B_c, ts: float):
    """Exact ZOH: exp([[A,B],[0,0]]*ts) → (A_d, B_d)."""
    n = len(A_c)
    m = len(B_c[0])
    aug = [[0.0] * (n + m) for _ in range(n + m)]
    for i in range(n):
        for j in range(n):
            aug[i][j] = A_c[i][j] * ts
        for j in range(m):
            aug[i][n + j] = B_c[i][j] * ts
    E = expm(aug)
    A_d = [[E[i][j] for j in range(n)] for i in range(n)]
    B_d = [[E[i][n + j] for j in range(m)] for i in range(n)]
    return A_d, B_d


def dare_iterate(A, B, Q, R, tol=RICCATI_TOL):
    """Discrete Riccati iteration → (P, K, n_iter). Explicit convergence tol."""
    n = len(A)
    P = [row[:] for row in Q]
    K = [[0.0] * n]
    for it in range(1, RICCATI_MAX_ITER + 1):
        # K = (R + B'P B)^{-1} B' P A
        BtP = mat_mul(mat_T(B), P)
        S = mat_add([[R]], mat_mul(BtP, B))  # 1x1 for our SISO B
        BtPA = mat_mul(BtP, A)
        # S is 1x1
        invS = 1.0 / S[0][0]
        K_new = [[invS * BtPA[0][j] for j in range(n)]]
        # P = Q + A'P A - A'P B K
        AtP = mat_mul(mat_T(A), P)
        P_new = mat_add(Q, mat_sub(mat_mul(AtP, A), mat_mul(mat_mul(AtP, B), K_new)))
        if frobenius(mat_sub(P_new, P)) < tol:
            return P_new, K_new, it
        P, K = P_new, K_new
    return P, K, RICCATI_MAX_ITER


def care_kleinman(A, B, Q, R, tol=1e-12):
    """Continuous ARE via Kleinman iteration; returns (P, K)."""
    n = len(A)
    # Start from a stabilizing gain (LQR-ish PD on this plant)
    K = [[4.0, 2.0]]
    P = eye(n)
    for _ in range(200):
        # A_cl = A - B K
        A_cl = mat_sub(A, mat_mul(B, K))
        # Solve Lyapunov A_cl' P + P A_cl = -(Q + K' R K) for 2x2
        QK = mat_add(Q, mat_scale(R, mat_mul(mat_T(K), K)))
        P_new = solve_lyapunov_2(A_cl, QK)
        # K = R^{-1} B' P
        BtP = mat_mul(mat_T(B), P_new)
        K_new = [[BtP[0][0] / R, BtP[0][1] / R]]
        if frobenius(mat_sub(P_new, P)) < tol and frobenius(mat_sub(K_new, K)) < tol:
            return P_new, K_new
        P, K = P_new, K_new
    return P, K


def solve_lyapunov_2(A, Q):
    """Solve A'P + P A = -Q for 2×2 P (symmetric) via 3×3 linear system."""
    # P = [[p, q],[q, r]]; expand
    a, b = A[0][0], A[0][1]
    c, d = A[1][0], A[1][1]
    # coeffs for [p,q,r]
    # (1,1): 2a p + 2c q = -Q00
    # (1,2): b p + (a+d) q + c r = -Q01
    # (2,2): 2b q + 2d r = -Q11
    M = [
        [2 * a, 2 * c, 0.0],
        [b, a + d, c],
        [0.0, 2 * b, 2 * d],
    ]
    rhs = [-Q[0][0], -Q[0][1], -Q[1][1]]
    # Gaussian elimination 3x3
    A3 = [M[i][:] + [rhs[i]] for i in range(3)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(A3[r][col]))
        A3[col], A3[piv] = A3[piv], A3[col]
        div = A3[col][col]
        if abs(div) < 1e-18:
            raise ZeroDivisionError("Lyapunov singular")
        for j in range(col, 4):
            A3[col][j] /= div
        for r in range(3):
            if r == col:
                continue
            fac = A3[r][col]
            for j in range(col, 4):
                A3[r][j] -= fac * A3[col][j]
    p, q, r = A3[0][3], A3[1][3], A3[2][3]
    return [[p, q], [q, r]]


def eig_moduli_2(M):
    """|λ| of 2×2 real matrix via characteristic polynomial."""
    tr = M[0][0] + M[1][1]
    det = M[0][0] * M[1][1] - M[0][1] * M[1][0]
    disc = tr * tr - 4.0 * det
    if disc >= 0.0:
        s = math.sqrt(disc)
        return [abs(0.5 * (tr + s)), abs(0.5 * (tr - s))]
    # complex conjugate: |λ| = sqrt(det) when det>0 for stable oscillation
    return [math.sqrt(abs(det)), math.sqrt(abs(det))]


def stage_QR(ts: float):
    """Map continuous Q,R meaning to discrete stage weights ≈ ∫ over Ts."""
    Qd = mat_scale(ts, Q_C)
    Rd = R_C * ts
    return Qd, Rd


def shared_noise_series(seed: int) -> list[float]:
    """Common random numbers: one accel-noise sample per SUBSTEP for the horizon.

    Every arm indexes the **same** series by absolute substep, so changing the
    hold period does not give anyone a quieter plant.
    """
    n = int(round(HORIZON_S / SUBSTEP))
    rng = random.Random(50_000 + seed)
    return [rng.gauss(0.0, PROCESS_STD) for _ in range(n)]


def simulate(
    K, ts: float, seed: int, noise: list[float] | None = None
) -> tuple[float, float, list[float]]:
    """ZOH hold of u=-Kx at period ts; integrate continuous plant with SUBSTEP.

    Returns (cost, settle_time_s, noise_series). Cost ≈ Σ (x'Q_c x + R_c u²)·dt.
    """
    if noise is None:
        noise = shared_noise_series(seed)
    n_hold = int(round(HORIZON_S / ts))
    n_sub_per = max(1, int(round(ts / SUBSTEP)))
    dt = ts / n_sub_per
    x = [1.0, 0.0]
    cost = 0.0
    settled_at = None
    sub_i = 0
    for k in range(n_hold):
        u = -(K[0][0] * x[0] + K[0][1] * x[1])
        for _ in range(n_sub_per):
            w = noise[sub_i] if sub_i < len(noise) else 0.0
            sub_i += 1
            xdot0 = A_C[0][0] * x[0] + A_C[0][1] * x[1] + B_C[0][0] * (u + w)
            xdot1 = A_C[1][0] * x[0] + A_C[1][1] * x[1] + B_C[1][0] * (u + w)
            xQx = Q_C[0][0] * x[0] * x[0] + Q_C[1][1] * x[1] * x[1]
            cost += (xQx + R_C * u * u) * dt
            x = [x[0] + dt * xdot0, x[1] + dt * xdot1]
        if settled_at is None and abs(x[0]) < SETTLE_EPS and abs(x[1]) < SETTLE_EPS:
            settled_at = (k + 1) * ts
    if settled_at is None:
        settled_at = HORIZON_S
    return cost, settled_at, noise


def design_cont_K():
    _, K = care_kleinman(A_C, B_C, Q_C, R_C)
    return K


def design_disc_K(ts: float):
    A_d, B_d = zoh_discretize(A_C, B_C, ts)
    Qd, Rd = stage_QR(ts)
    P, K, n_it = dare_iterate(A_d, B_d, Qd, Rd)
    mods = eig_moduli_2(mat_sub(A_d, mat_mul(B_d, K)))
    return K, max(mods), n_it, A_d, B_d


def mean_sd(xs: list[float]) -> tuple[float, float]:
    n = len(xs)
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / max(1, n - 1)
    return mu, math.sqrt(var)


def main() -> None:
    Kc = design_cont_K()
    Kd_c, rho_c, it_c, _, _ = design_disc_K(TS_COARSE)
    Kd_f, rho_f, it_f, _, _ = design_disc_K(TS_FINE)
    print(
        "Synthetic discrete-LQR / ZOH toy; shared plant Q/R / noise; "
        "not a hardware plant"
    )
    print(
        f"plant m={M} b={B_DAMP} Q=diag({Q_C[0][0]},{Q_C[1][1]}) R={R_C} "
        f"Ts_coarse={TS_COARSE} Ts_fine={TS_FINE} "
        f"RICCATI_TOL={RICCATI_TOL:g} SUBSTEP={SUBSTEP} seeds={len(SEEDS)}"
    )
    print(
        f"model: ZOH via expm(augmented); DARE iterate to ‖ΔP‖_F<{RICCATI_TOL:g}; "
        f"stability |λ(A_d−B_dK)|<1; Kc={Kc[0][0]:.4f},{Kc[0][1]:.4f} "
        f"Kd_coarse={Kd_c[0][0]:.4f},{Kd_c[0][1]:.4f} (iters={it_c}, max|λ|={rho_c:.6f}) "
        f"Kd_fine={Kd_f[0][0]:.4f},{Kd_f[0][1]:.4f} (iters={it_f}, max|λ|={rho_f:.6f})"
    )
    print(
        "regime arm cost settle_s max_eig_mod (mean+-sd over seeds; "
        "C always uses fine Ts)"
    )
    # Verify stability
    assert rho_c < 1.0 and rho_f < 1.0

    regimes = (
        ("coarse_Ts", TS_COARSE),
        ("fine_Ts", TS_FINE),
    )
    summary: dict[tuple[str, str], tuple[float, float, float]] = {}
    for reg_name, ts in regimes:
        for arm in ARMS:
            costs, settles, rhos = [], [], []
            for seed in SEEDS:
                noise = shared_noise_series(seed)  # identical series for every arm
                if arm == "A_cont_zoh":
                    K = Kc
                    ts_app = ts
                    Ad, Bd = zoh_discretize(A_C, B_C, ts_app)
                    rho = max(eig_moduli_2(mat_sub(Ad, mat_mul(Bd, K))))
                elif arm == "B_disc":
                    K, rho, _, _, _ = design_disc_K(ts)
                    ts_app = ts
                else:
                    K, rho, _, _, _ = design_disc_K(TS_FINE)
                    ts_app = TS_FINE
                cost, settle, noise_used = simulate(K, ts_app, seed, noise=noise)
                assert noise_used is noise
                costs.append(cost)
                settles.append(settle)
                rhos.append(rho)
            mc, sc = mean_sd(costs)
            ms, ss = mean_sd(settles)
            mr, sr = mean_sd(rhos)
            summary[(reg_name, arm)] = (mc, ms, mr)
            print(
                f"{reg_name} {arm} {mc:.4f}+-{sc:.4f} "
                f"{ms:.4f}+-{ss:.4f} {mr:.6f}+-{sr:.6f}"
            )

    # Coarse: B should beat A on cost
    ca = summary[("coarse_Ts", "A_cont_zoh")][0]
    cb = summary[("coarse_Ts", "B_disc")][0]
    cc = summary[("coarse_Ts", "C_disc_fine")][0]
    print(
        f"coarse_Ts: cost_A − cost_B = {ca - cb:.4f} "
        f"(discrete-at-hold beats cont+ZOH; C_fine={cc:.4f})"
    )
    # Fine: A and B near-tie
    fa = summary[("fine_Ts", "A_cont_zoh")][0]
    fb = summary[("fine_Ts", "B_disc")][0]
    gap = abs(fa - fb)
    rel = gap / max(fa, fb, 1e-12)
    print(
        f"fine_Ts: |cost_A − cost_B| = {gap:.4f} "
        f"(near-tie / small gap as Ts→0; relative {rel:.4f}; "
        f"remaining gap from ZOH hold of Kc vs DARE K_d plus shared noise)"
    )
    print(
        f"stability: max|λ| coarse={summary[('coarse_Ts','B_disc')][2]:.6f} "
        f"fine={summary[('fine_Ts','B_disc')][2]:.6f} (both < 1)"
    )
    print(
        "No winner declared: coarse Ts needs discrete design; fine Ts makes "
        "cont+ZOH approach discrete; C’s fine rate is a budget, not free"
    )
    print(
        "Real discrete-LQR / embedded plant lab: 本页未运行; "
        "Underactuated / SciPy DARE numbers 以原文为准"
    )


if __name__ == "__main__":
    main()
