#!/usr/bin/env python3
"""sysid_pe_compare_toy.py: PE vs step — fair energy, report conditioning (stdlib).

Persistency of excitation (PE) is about the RICHNESS of the regressors over the
identification horizon (how well-conditioned ΦᵀΦ is), not a claim that "two
parameters ⇒ a step cannot identify them." A transient step often identifies a
first-order time constant τ; for a richer structure the same step can leave
ΦᵀΦ ill-conditioned. Numbers decide — this toy reports them and does not
guarantee that PE always wins.

Fair comparison LOCKED: same horizon N, the SAME measurement-noise sequence for
every input arm of a case, and input energy Σ u² matched within ENERGY_TOL
(the richer input is scaled to the step's energy). Peak |u| is also printed.

Noise model (LOCKED): independent additive measurement noise. A noise-free
state z follows the ARX recursion; the measured output is y = z + v with
v ~ N(0, σ²) independent of (z, u). Equation-error OLS then puts noisy lagged
y into Φ, so it is an errors-in-variables (EIV) estimator: the printed
‖θ̂−θ‖ includes that EE-OLS bias. This is NOT the ARX *innovation* model
y_k = a y_{k-1} + b u_{k-1} + e_k (where e_k is independent of the lagged
regressors and OLS is consistent). An output-error (OE) or instrumental-
variable (IV) fit would be a different estimator; not implemented here.

The finite-window Gram cond(ΦᵀΦ) is a practical diagnostic of regressor
richness on this horizon. Strict PE is a stronger statement: there exist a
fixed window length N and α>0 such that for all sliding start indices k,
Σ_{i=k}^{k+N-1} φᵢφᵢᵀ ⪰ αI (a uniform lower bound). The toy reports the
diagnostic, not a PE certificate.

Pointers (no copyrighted book text pasted): Ljung, System Identification, 2ed
(ISBN 0136566952) via the MIT OCW 6.435 syllabus; De Nicolao 1997 tutorial on
OE vs EE and PE. Existing lesson 5.1 step-τ identification and Month 7
sysid_fit are siblings, not redone here.
usage: python3 sysid_pe_compare_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 51
N = 200                 # identification horizon (samples), shared
DT = 0.01               # s
ENERGY_TOL = 0.01       # |E_step - E_other| / E_step must be <= this
NOISE_STD = 0.02        # additive measurement noise v on y = z + v (same stream per case)

# Case A: first-order speed plant  τ z' + z = K u  (discrete ARX-1 on noise-free z).
# A single step is classically enough to read τ; PE is not required.
TAU_A = 0.08            # s  (matches the Month 3 / 5.1 joint time constant)
K_A = 1.0
A_TRUE_A = math.exp(-DT / TAU_A)
B_TRUE_A = K_A * (1.0 - A_TRUE_A)

# Case B: second-order ARX-2 with a slow and a fast mode. A step puts almost
# all energy at DC; a richer two-tone input improves the conditioning of ΦᵀΦ.
A1_TRUE_B = 1.70
A2_TRUE_B = -0.72
B_TRUE_B = 0.05


def prbs(rng: random.Random, n: int, amp: float) -> list[float]:
    """±amp pseudo-random binary sequence (clock every 4 samples)."""
    u, level = [], amp
    for k in range(n):
        if k % 4 == 0:
            level = amp if rng.random() < 0.5 else -amp
        u.append(level)
    return u


def two_tone(n: int, amp: float, f1: float = 1.5, f2: float = 7.0) -> list[float]:
    """Sum of two sines (Hz) — richer spectrum than a single step."""
    return [amp * (math.sin(2 * math.pi * f1 * k * DT)
                   + 0.7 * math.sin(2 * math.pi * f2 * k * DT)) for k in range(n)]


def scale_energy(u: list[float], target: float) -> list[float]:
    e = sum(v * v for v in u)
    if e <= 0.0:
        return list(u)
    s = math.sqrt(target / e)
    return [s * v for v in u]


def sim_meas_arx1(u: list[float], a: float, b: float, noise: list[float]) -> list[float]:
    """Noise-free ARX-1 state z; measured y = z + v (independent measurement noise)."""
    z = [0.0] * len(u)
    y = [0.0] * len(u)
    for k in range(1, len(u)):
        z[k] = a * z[k - 1] + b * u[k - 1]
        y[k] = z[k] + noise[k]
    return y


def sim_meas_arx2(
    u: list[float], a1: float, a2: float, b: float, noise: list[float]
) -> list[float]:
    """Noise-free ARX-2 state z; measured y = z + v (independent measurement noise)."""
    z = [0.0] * len(u)
    y = [0.0] * len(u)
    for k in range(2, len(u)):
        z[k] = a1 * z[k - 1] + a2 * z[k - 2] + b * u[k - 1]
        y[k] = z[k] + noise[k]
    return y


def ols(phi: list[list[float]], yy: list[float]) -> tuple[list[float], float]:
    """θ̂ = (ΦᵀΦ)⁻¹ Φᵀ y via Gaussian elimination; also return cond(ΦᵀΦ)."""
    p = len(phi[0])
    g = [[0.0] * p for _ in range(p)]
    rhs = [0.0] * p
    for row, yk in zip(phi, yy):
        for i in range(p):
            rhs[i] += row[i] * yk
            for j in range(p):
                g[i][j] += row[i] * row[j]
    # 2-norm condition via eigenvalue ratio of the Gram matrix (p small).
    cond = _cond(g)
    theta = _solve(g, rhs)
    return theta, cond


def _cond(g: list[list[float]]) -> float:
    # For p=2 use closed form; for p=3 use characteristic polynomial roots via
    # numpy-free power iteration on G and G^{-1} for rough 2-norm cond.
    p = len(g)
    if p == 2:
        tr = g[0][0] + g[1][1]
        det = g[0][0] * g[1][1] - g[0][1] * g[1][0]
        # eigenvalues of 2x2: roots of λ² - tr λ + det = 0
        disc = max(0.0, tr * tr - 4.0 * det)
        lam1 = 0.5 * (tr + math.sqrt(disc))
        lam2 = 0.5 * (tr - math.sqrt(disc))
        return abs(lam1 / lam2) if abs(lam2) > 1e-18 else float("inf")
    # Power iteration for λ_max(G) and λ_max(G^{-1}).
    def power(mat, iters=40):
        v = [1.0] * p
        for _ in range(iters):
            w = [sum(mat[i][j] * v[j] for j in range(p)) for i in range(p)]
            nrm = math.sqrt(sum(x * x for x in w)) or 1.0
            v = [x / nrm for x in w]
        w = [sum(mat[i][j] * v[j] for j in range(p)) for i in range(p)]
        return sum(v[i] * w[i] for i in range(p))
    lam_max = power(g)
    ginv = _invert(g)
    lam_min_inv = power(ginv)  # ≈ 1/λ_min
    lam_min = 1.0 / lam_min_inv if abs(lam_min_inv) > 1e-18 else 0.0
    return abs(lam_max / lam_min) if abs(lam_min) > 1e-18 else float("inf")


def _invert(g: list[list[float]]) -> list[list[float]]:
    p = len(g)
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(p)] for i, row in enumerate(g)]
    for col in range(p):
        piv = max(range(col, p), key=lambda r: abs(a[r][col]))
        a[col], a[piv] = a[piv], a[col]
        div = a[col][col]
        for j in range(2 * p):
            a[col][j] /= div
        for r in range(p):
            if r == col:
                continue
            f = a[r][col]
            for j in range(2 * p):
                a[r][j] -= f * a[col][j]
    return [row[p:] for row in a]


def _solve(g: list[list[float]], rhs: list[float]) -> list[float]:
    p = len(g)
    a = [g[i][:] + [rhs[i]] for i in range(p)]
    for col in range(p):
        piv = max(range(col, p), key=lambda r: abs(a[r][col]))
        a[col], a[piv] = a[piv], a[col]
        div = a[col][col]
        for j in range(p + 1):
            a[col][j] /= div
        for r in range(p):
            if r == col:
                continue
            f = a[r][col]
            for j in range(p + 1):
                a[r][j] -= f * a[col][j]
    return [a[i][p] for i in range(p)]


def fit_arx1(u: list[float], y: list[float]) -> tuple[list[float], float, float]:
    phi, yy = [], []
    for k in range(1, len(u)):
        phi.append([y[k - 1], u[k - 1]])
        yy.append(y[k])
    theta, cond = ols(phi, yy)
    true = [A_TRUE_A, B_TRUE_A]
    err = math.sqrt(sum((theta[i] - true[i]) ** 2 for i in range(2)))
    return theta, cond, err


def fit_arx2(u: list[float], y: list[float]) -> tuple[list[float], float, float]:
    phi, yy = [], []
    for k in range(2, len(u)):
        phi.append([y[k - 1], y[k - 2], u[k - 1]])
        yy.append(y[k])
    theta, cond = ols(phi, yy)
    true = [A1_TRUE_B, A2_TRUE_B, B_TRUE_B]
    err = math.sqrt(sum((theta[i] - true[i]) ** 2 for i in range(3)))
    return theta, cond, err


def energy(u: list[float]) -> float:
    return sum(v * v for v in u)


def peak(u: list[float]) -> float:
    return max(abs(v) for v in u)


def main() -> None:
    print(f"seed={SEED} N={N} dt={DT} energy_tol={ENERGY_TOL} noise_std={NOISE_STD}")
    print(
        "noise_model: y=z+v (independent measurement noise on noise-free ARX state z); "
        "NOT ARX innovation e_k"
    )
    print(
        "estimator: equation-error OLS (ARX) on noisy y in Phi → EIV / EE-OLS bias; "
        "NOT claimed unbiased (OE/IV not implemented)"
    )
    print(
        "PE diagnostic: finite-window cond(Phi^T Phi); "
        "strict PE = exist fixed N, alpha>0: for all sliding k, "
        "sum_{i=k..k+N-1} phi_i phi_i^T >= alpha I (uniform; not claimed here)"
    )
    print()

    # ---- Case A: first-order τ — a step often suffices ----
    rng_n = random.Random(SEED)
    noise_a = [rng_n.gauss(0.0, NOISE_STD) for _ in range(N)]
    u_step_a = [0.0 if k < 10 else 1.0 for k in range(N)]
    e_step = energy(u_step_a)
    rng_prbs = random.Random(SEED + 1)
    u_prbs_raw = prbs(rng_prbs, N, amp=1.0)
    u_prbs_a = scale_energy(u_prbs_raw, e_step)

    print(f"case_A first_order_tau={TAU_A} K={K_A}  true_theta=[{A_TRUE_A:.6f}, {B_TRUE_A:.6f}]")
    print(f"{'input':<10} {'energy':>10} {'peak|u|':>10} {'cond(PhiTPhi)':>14} {'||theta_hat-theta||':>20}")
    results_a = []
    for name, u in (("step", u_step_a), ("prbs", u_prbs_a)):
        y = sim_meas_arx1(u, A_TRUE_A, B_TRUE_A, noise_a)
        theta, cond, err = fit_arx1(u, y)
        e = energy(u)
        print(f"{name:<10} {e:10.4f} {peak(u):10.4f} {cond:14.4g} {err:20.6f}")
        results_a.append((name, e, cond, err, theta))
    # energy match assert
    e0, e1 = results_a[0][1], results_a[1][1]
    rel = abs(e0 - e1) / e0
    assert rel <= ENERGY_TOL, f"case_A energy mismatch rel={rel}"
    print(f"energy_match_rel={rel:.6f} (tol={ENERGY_TOL})  "
          f"step_err={results_a[0][3]:.6f} prbs_err={results_a[1][3]:.6f} "
          f"(step is capable; numbers decide, PE not guaranteed to win; "
          f"err is single-run parameter error, may include systematic bias)")
    print()

    # ---- Case B: second-order — richer input improves conditioning ----
    rng_n = random.Random(SEED + 7)   # fresh noise stream for case B, shared across its arms
    noise_b = [rng_n.gauss(0.0, NOISE_STD) for _ in range(N)]
    u_step_b = [0.0 if k < 10 else 1.0 for k in range(N)]
    e_step_b = energy(u_step_b)
    u_rich_b = scale_energy(two_tone(N, amp=1.0), e_step_b)

    print(f"case_B second_order  true_theta=[{A1_TRUE_B}, {A2_TRUE_B}, {B_TRUE_B}]")
    print(f"{'input':<10} {'energy':>10} {'peak|u|':>10} {'cond(PhiTPhi)':>14} {'||theta_hat-theta||':>20}")
    results_b = []
    for name, u in (("step", u_step_b), ("two_tone", u_rich_b)):
        y = sim_meas_arx2(u, A1_TRUE_B, A2_TRUE_B, B_TRUE_B, noise_b)
        theta, cond, err = fit_arx2(u, y)
        e = energy(u)
        print(f"{name:<10} {e:10.4f} {peak(u):10.4f} {cond:14.4g} {err:20.6f}")
        results_b.append((name, e, cond, err, theta))
    e0, e1 = results_b[0][1], results_b[1][1]
    rel = abs(e0 - e1) / e0
    assert rel <= ENERGY_TOL, f"case_B energy mismatch rel={rel}"
    # Report whether richer input improved conditioning (data-dependent; asserted direction).
    assert results_b[1][2] < results_b[0][2], (
        f"expected two_tone cond < step cond, got {results_b[1][2]} vs {results_b[0][2]}")
    print(f"energy_match_rel={rel:.6f} (tol={ENERGY_TOL})  "
          f"cond_step={results_b[0][2]:.4g} cond_two_tone={results_b[1][2]:.4g} "
          f"step_err={results_b[0][3]:.6f} two_tone_err={results_b[1][3]:.6f} "
          f"(richer input improved conditioning; err is single-run parameter error, may include systematic bias)")
    print("ok: fair energy; case_A step-capable; case_B richer input better cond; "
          "measurement-noise EIV → single-run parameter error may include systematic bias (one seed cannot quantify statistical bias; real motor sysid 本页未运行)")


if __name__ == "__main__":
    main()
