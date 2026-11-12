#!/usr/bin/env python3
"""LQG separation toy: a Kalman filter plus an LQR gain on a known linear plant.

Synthetic, stdlib only, deterministic.  Not H-infinity, not a real IMU or
plant (本页未运行).  Not a redo of the lesson's Luenberger-versus-oracle
model-error toy: there is NO model error here, the plant is known exactly.
The full-state arm is a privileged oracle, not an equal-information baseline.

Plant (same mass-damper as the lesson's observer toy, forward-Euler, declared):
DT = 0.02 s, M = 1.0 kg, B_DAMP = 0.40 N*s/m.  A = [[1, DT],
[0, 1 - B_DAMP*DT/M]], B = [[0], [DT/M]], C = [1, 0] (position measured).
x_{i+1} = A x_i + B u_i + v_i, y_i = C x_i + w_i, with v_i = [0, SIG_W*e1_i]
(process noise on velocity only, so V = diag(0, SIG_W^2)) and w_i =
SIG_V*e2_i (W = SIG_V^2).  SIG_W = 0.04 (declared).  Cost weights
Q = diag(1.0, 0.1), R = 0.01.  HORIZON = 500 steps.

Separation principle: the estimator and the state-feedback gain are designed
independently.  The Kalman gain comes from the noise covariances V and W, not
from placed poles.

LQR gain K: iterate the discrete Riccati map S <- A'SA - A'SB (B'SB + R)^-1
B'SA + Q from S = Q until the max abs change < 1e-12; K = (B'SB + R)^-1 B'SA.
Kalman gain (steady state, predictive form exactly as Wikipedia's discrete
LQG): iterate P <- A (P - P C' (C P C' + W)^-1 C P) A' + V from
P = diag(0.25, 0.01) until the max abs change < 1e-12; L = P C' (C P C' + W)^-1.
Estimator update each step: x_pred = A xhat + B u; after measuring y_{i+1}:
xhat = x_pred + L (y_{i+1} - C x_pred).  Control u_i = -K xhat_i.

Luenberger arms use the lesson's existing predictor form:
xhat_{i+1} = A xhat_i + B u_i + Lp (y_i - C xhat_i), with Lp from Ackermann
pole placement on (A, C).

Arms (all start from the same x0 and xhat0 = [0, 0] = E[x0]):
  A_oracle     : u = -K x (privileged true state).
  B_lqg        : Kalman with the TRUE V, W of the regime, then u = -K xhat.
  C_luen_page  : Luenberger with the lesson's observer poles (0.85, 0.80).
  D_luen_fast  : Luenberger with casually fast poles (0.20, 0.20).
  E_kf_misspec : Kalman designed with misspecified covariances
                 V_design = 0.01*V_true and W_design = 100*W_true (trusts the
                 model far too much).

Common random numbers: for each (regime, seed) draw ONCE from
random.Random(f"{regime}/{seed}"): x0 = [0.5*g, 0.1*g] (two gauss(0,1) draws,
so P0 = diag(0.25, 0.01)), then HORIZON values e1 and HORIZON+1 values e2
(standard normal), shared by all arms; each regime scales e2 by its SIG_V.

Regimes (true measurement noise SIG_V): "matched" 0.05 (the lesson's
MEAS_STD); "noisy_sensor" 0.25; "quiet_sensor" 0.005.

Metrics per seed: cost = mean over the horizon of (x0^2 + 0.1*x1^2 +
0.01*u^2); est_rms = rms of the position estimation error (0 for A_oracle);
u_rms = rms of u.

Pairs, every metric in every regime: B-A, B-C, B-D, E-C, E-B.

Regimes and parameters were written before the first run.  Declared
expectations (not tuned; print whatever comes):
  matched      : A is the oracle bound (B-A cost consistent > 0); B
                 consistently below D on cost; B vs C either a consistent B
                 win or a near-tie; E may lose to C on cost - keep.
  noisy_sensor : B consistently below C and D on cost (fast observers pass
                 sensor noise into u); E keep as it comes.
  quiet_sensor : B vs D may near-tie; B consistently below C or a near-tie;
                 E loses to C - keep.

The ordering of the arms follows from the declared noise covariances and pole
sets; the toy shows magnitudes and seed scatter, not evidence that one
estimator always wins.

Alternatives (same seeds, declared before the run, not adopted):
  matched with the opposite misspecification V_design = 100*V, W_design =
  0.01*W (paired E-C cost);
  matched with slower page poles (0.90, 0.85) for C (paired B-C cost);
  noisy_sensor with HORIZON = 1000 (paired B-C cost).
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
DT = 0.02                    # s
M = 1.0                      # kg
B_DAMP = 0.40                # N*s/m
SIG_W = 0.04                 # process noise on velocity
Q = [[1.0, 0.0], [0.0, 0.1]]
R = 0.01
HORIZON = 500
A = [[1.0, DT], [0.0, 1.0 - B_DAMP * DT / M]]
B = [[0.0], [DT / M]]
C = [[1.0, 0.0]]
V_TRUE = [[0.0, 0.0], [0.0, SIG_W ** 2]]
P0 = [[0.25, 0.0], [0.0, 0.01]]

REGIMES = {"matched": 0.05, "noisy_sensor": 0.25, "quiet_sensor": 0.005}
ARMS = ("A_oracle", "B_lqg", "C_luen_page", "D_luen_fast", "E_kf_misspec")
METRICS = ("cost", "est_rms", "u_rms")
PAIRS = (("B_lqg", "A_oracle"),
         ("B_lqg", "C_luen_page"),
         ("B_lqg", "D_luen_fast"),
         ("E_kf_misspec", "C_luen_page"),
         ("E_kf_misspec", "B_lqg"))
PAGE_POLES = (0.85, 0.80)
FAST_POLES = (0.20, 0.20)
DECLARED = {
    "matched": "A is the oracle bound (B-A cost consistent > 0); B consistently "
               "below D on cost; B vs C either a consistent B win or a near-tie; "
               "E may lose to C on cost - keep",
    "noisy_sensor": "B consistently below C and D on cost (fast observers pass "
                    "sensor noise into u); E keep as it comes",
    "quiet_sensor": "B vs D may near-tie; B consistently below C or a near-tie; "
                    "E loses to C - keep",
}


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


def mat_mul(X, Y):
    n, k, m = len(X), len(Y), len(Y[0])
    return [[sum(X[i][t] * Y[t][j] for t in range(k)) for j in range(m)]
            for i in range(n)]


def mat_add(X, Y):
    return [[X[i][j] + Y[i][j] for j in range(len(X[0]))] for i in range(len(X))]


def mat_sub(X, Y):
    return [[X[i][j] - Y[i][j] for j in range(len(X[0]))] for i in range(len(X))]


def mat_T(X):
    return [[X[j][i] for j in range(len(X))] for i in range(len(X[0]))]


def inv2(Mm):
    a, b = Mm[0]
    c, d = Mm[1]
    det = a * d - b * c
    return [[d / det, -b / det], [-c / det, a / det]]


def max_abs_eig(Mm):
    a, b = Mm[0]
    c, d = Mm[1]
    tr = (a + d) / 2.0
    disc = ((a - d) / 2.0) ** 2 + b * c
    if disc >= 0.0:
        r = math.sqrt(disc)
        return max(abs(tr + r), abs(tr - r))
    return math.sqrt(tr * tr - disc)


def lqr_gain(Aa, Bb, Qq, Rr):
    """Discrete Riccati map from S = Q; returns K = (B'SB + R)^-1 B'SA."""
    S = [row[:] for row in Qq]
    At, Bt = mat_T(Aa), mat_T(Bb)
    for _ in range(100000):
        BtS = mat_mul(Bt, S)
        BtSB = mat_mul(BtS, Bb)[0][0]
        BtSA = mat_mul(BtS, Aa)
        AtS = mat_mul(At, S)
        AtSA = mat_mul(AtS, Aa)
        AtSB = mat_mul(AtS, Bb)
        coef = 1.0 / (BtSB + Rr)
        corr = [[AtSB[i][0] * coef * BtSA[0][j] for j in range(2)] for i in range(2)]
        S_new = mat_add(mat_sub(AtSA, corr), Qq)
        delta = max(abs(S_new[i][j] - S[i][j]) for i in range(2) for j in range(2))
        S = S_new
        if delta < 1e-12:
            break
    BtS = mat_mul(Bt, S)
    BtSB = mat_mul(BtS, Bb)[0][0]
    BtSA = mat_mul(BtS, Aa)
    return [[BtSA[0][j] / (BtSB + Rr) for j in range(2)]]


def kalman_gain(Aa, Cc, Vv, Ww, P_init):
    """Steady-state predictive-form Kalman gain for the discrete LQG map."""
    P = [row[:] for row in P_init]
    At, Ct = mat_T(Aa), mat_T(Cc)
    for _ in range(100000):
        PCt = mat_mul(P, Ct)
        CP = mat_mul(Cc, P)
        S_meas = mat_mul(CP, Ct)[0][0] + Ww
        corr = [[PCt[i][0] * (1.0 / S_meas) * CP[0][j] for j in range(2)]
                for i in range(2)]
        Pbar = mat_sub(P, corr)
        P_new = mat_add(mat_mul(mat_mul(Aa, Pbar), At), Vv)
        delta = max(abs(P_new[i][j] - P[i][j]) for i in range(2) for j in range(2))
        P = P_new
        if delta < 1e-12:
            break
    PCt = mat_mul(P, Ct)
    CP = mat_mul(Cc, P)
    S_meas = mat_mul(CP, Ct)[0][0] + Ww
    return [[PCt[i][0] / S_meas] for i in range(2)]


def ackermann_observer(Aa, Cc, poles):
    """Lp with eig(A - Lp C) = poles, by Ackermann on the dual pair (A', C')."""
    At, Ct = mat_T(Aa), mat_T(Cc)
    ATCt = mat_mul(At, Ct)
    Ctrb = [[Ct[0][0], ATCt[0][0]], [Ct[1][0], ATCt[1][0]]]
    Ctrb_inv = inv2(Ctrb)
    At2 = mat_mul(At, At)
    tr = sum(poles)
    prod = poles[0] * poles[1]
    phi = mat_add(mat_sub(At2, [[tr * At[i][j] for j in range(2)]
                                for i in range(2)]),
                  [[prod * (1.0 if i == j else 0.0) for j in range(2)]
                   for i in range(2)])
    Kd = mat_mul(mat_mul([[0.0, 1.0]], Ctrb_inv), phi)
    return [[Kd[0][0]], [Kd[0][1]]]


def shared_draws(regime, seed, horizon):
    """Common random numbers: one x0, one e1 train, one e2 train per (regime, seed)."""
    rng = random.Random(f"{regime}/{seed}")
    g1 = rng.gauss(0.0, 1.0)
    g2 = rng.gauss(0.0, 1.0)
    x0 = [0.5 * g1, 0.1 * g2]
    e1 = [rng.gauss(0.0, 1.0) for _ in range(horizon)]
    e2 = [rng.gauss(0.0, 1.0) for _ in range(horizon + 1)]
    return x0, e1, e2


def run_arm(arm, regime, seed, K, L_kf, Lp, horizon=HORIZON, sig_v=0.05):
    x0, e1, e2 = shared_draws(regime, seed, horizon)
    x = [x0[0], x0[1]]
    xhat = [0.0, 0.0]
    cost_sum, est_sum, u_sum = 0.0, 0.0, 0.0
    for i in range(horizon):
        if arm == "A_oracle":
            u = -(K[0][0] * x[0] + K[0][1] * x[1])
        else:
            u = -(K[0][0] * xhat[0] + K[0][1] * xhat[1])
        cost_sum += x[0] * x[0] + 0.1 * x[1] * x[1] + 0.01 * u * u
        if arm != "A_oracle":
            est_sum += (xhat[0] - x[0]) ** 2
        u_sum += u * u
        x_next = [A[0][0] * x[0] + A[0][1] * x[1] + B[0][0] * u,
                  A[1][0] * x[0] + A[1][1] * x[1] + B[1][0] * u + SIG_W * e1[i]]
        if arm == "A_oracle":
            pass
        elif arm in ("B_lqg", "E_kf_misspec"):
            y_next = x_next[0] + sig_v * e2[i + 1]
            x_pred = [A[0][0] * xhat[0] + A[0][1] * xhat[1] + B[0][0] * u,
                      A[1][0] * xhat[0] + A[1][1] * xhat[1] + B[1][0] * u]
            innov = y_next - x_pred[0]
            xhat = [x_pred[0] + L_kf[0][0] * innov,
                    x_pred[1] + L_kf[1][0] * innov]
        else:
            y_cur = x[0] + sig_v * e2[i]
            innov = y_cur - xhat[0]
            xhat = [A[0][0] * xhat[0] + A[0][1] * xhat[1] + B[0][0] * u
                    + Lp[0][0] * innov,
                    A[1][0] * xhat[0] + A[1][1] * xhat[1] + B[1][0] * u
                    + Lp[1][0] * innov]
        x = x_next
    return {"cost": cost_sum / horizon,
            "est_rms": math.sqrt(est_sum / horizon),
            "u_rms": math.sqrt(u_sum / horizon)}


def collect(regime, K, L_true, L_miss, Lp_page, Lp_fast, horizon=HORIZON):
    sig_v = REGIMES[regime]
    gains = {"A_oracle": (None, None), "B_lqg": (L_true, None),
             "C_luen_page": (None, Lp_page), "D_luen_fast": (None, Lp_fast),
             "E_kf_misspec": (L_miss, None)}
    return {arm: [run_arm(arm, regime, s, K, gains[arm][0], gains[arm][1],
                          horizon, sig_v) for s in SEEDS] for arm in ARMS}


def arm_col(regime, arm, K, L_kf, Lp, horizon=HORIZON, sig_v=None):
    if sig_v is None:
        sig_v = REGIMES[regime]
    return [run_arm(arm, regime, s, K, L_kf, Lp, horizon, sig_v) for s in SEEDS]


def col(rows, key):
    return [x[key] for x in rows]


def report(regime, K, L_true, L_miss, Lp_page, Lp_fast):
    sig_v = REGIMES[regime]
    res = collect(regime, K, L_true, L_miss, Lp_page, Lp_fast)
    print(f"{regime} (SIG_V={num(sig_v)}):")
    print(f"  declared: {DECLARED[regime]}")
    for arm in ARMS:
        print(f"  {arm} " + " ".join(
            f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS))
    for a, b in PAIRS:
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: "
                  f"{verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("Synthetic LQG separation toy: Kalman filter plus LQR on a known "
          "mass-damper plant; common random numbers; not a real IMU or plant")
    print(f"seeds={len(SEEDS)} dt={num(DT)} s m={num(M)} kg b={num(B_DAMP)} N*s/m "
          f"sig_w={num(SIG_W)} q=diag(1.0,0.1) r={num(R)} horizon={HORIZON} (declared)")
    print("No model error: the plant is known exactly; the full-state arm is a "
          "privileged oracle, not an equal-information baseline")
    print("Regimes and parameters were written before the first run")
    print("rule: u=-K*xhat; x_pred=A*xhat+B*u; xhat=x_pred+L*(y-C*x_pred); "
          "Luenberger xhat+=A*xhat+B*u+Lp*(y-C*xhat)")
    K = lqr_gain(A, B, Q, R)
    print(f"hand_calc LQR K = [{num(K[0][0])}, {num(K[0][1])}]")
    L_true = {}
    L_miss = {}
    for regime, sig_v in REGIMES.items():
        L_true[regime] = kalman_gain(A, C, V_TRUE, sig_v ** 2, P0)
        V_design = [[0.01 * V_TRUE[i][j] for j in range(2)] for i in range(2)]
        L_miss[regime] = kalman_gain(A, C, V_design, 100.0 * sig_v ** 2, P0)
        print(f"hand_calc Kalman L ({regime}, SIG_V={num(sig_v)}) = "
              f"[{num(L_true[regime][0][0])}, {num(L_true[regime][1][0])}]")
    Lp_page = ackermann_observer(A, C, PAGE_POLES)
    Lp_fast = ackermann_observer(A, C, FAST_POLES)
    print(f"hand_calc Luenberger Lp (page poles {PAGE_POLES[0]:.2f}, "
          f"{PAGE_POLES[1]:.2f}) = [{num(Lp_page[0][0])}, {num(Lp_page[1][0])}]")
    print(f"hand_calc Luenberger Lp (fast poles {FAST_POLES[0]:.2f}, "
          f"{FAST_POLES[1]:.2f}) = [{num(Lp_fast[0][0])}, {num(Lp_fast[1][0])}]")
    print(f"hand_calc max|eig(A-BK)| = {num(max_abs_eig(mat_sub(A, mat_mul(B, K))))}")
    print(f"hand_calc max|eig(A-LC)| (Kalman, matched) = "
          f"{num(max_abs_eig(mat_sub(A, mat_mul(L_true['matched'], C))))}")
    print(f"hand_calc max|eig(A-LpC)| (page poles) = "
          f"{num(max_abs_eig(mat_sub(A, mat_mul(Lp_page, C))))}")
    L1 = P0[0][0] / (P0[0][0] + REGIMES["matched"] ** 2)
    print("hand_calc first-step Kalman gain from P0=diag(0.25,0.01) with "
          f"SIG_V=0.05: L1=[0.25/(0.25+0.0025), 0]=[{num(L1)}, 0.0000]")
    for regime in REGIMES:
        report(regime, K, L_true[regime], L_miss[regime], Lp_page, Lp_fast)
    print("alternative parameters (declared before the run, same seeds, not adopted):")
    sig_m = REGIMES["matched"]
    V_opp = [[100.0 * V_TRUE[i][j] for j in range(2)] for i in range(2)]
    L_opp = kalman_gain(A, C, V_opp, 0.01 * sig_m ** 2, P0)
    alt_e = arm_col("matched", "E_kf_misspec", K, L_opp, None, HORIZON, sig_m)
    alt_c = arm_col("matched", "C_luen_page", K, None, Lp_page, HORIZON, sig_m)
    print(f"  matched V_design=100*V, W_design=0.01*W: paired E-C cost: "
          f"{verdict(col(alt_e, 'cost'), col(alt_c, 'cost'))}")
    Lp_slow = ackermann_observer(A, C, (0.90, 0.85))
    alt_c2 = arm_col("matched", "C_luen_page", K, None, Lp_slow, HORIZON, sig_m)
    alt_b = arm_col("matched", "B_lqg", K, L_true["matched"], None, HORIZON, sig_m)
    print(f"  matched C page poles (0.90,0.85): paired B-C cost: "
          f"{verdict(col(alt_b, 'cost'), col(alt_c2, 'cost'))}")
    sig_n = REGIMES["noisy_sensor"]
    alt_b2 = arm_col("noisy_sensor", "B_lqg", K, L_true["noisy_sensor"], None,
                     1000, sig_n)
    alt_c3 = arm_col("noisy_sensor", "C_luen_page", K, None, Lp_page, 1000, sig_n)
    print(f"  noisy_sensor HORIZON=1000: paired B-C cost: "
          f"{verdict(col(alt_b2, 'cost'), col(alt_c3, 'cost'))}")
    print("Separation: one K for every arm; only the estimator changes. No winner "
          "beyond the noise model: the Kalman gain is best when its V and W match "
          "the plant, and a misspecified Kalman can lose to a placed observer")
    print("Real plant / IMU / MATLAB toolbox: 本页未运行; not H-infinity; "
          "Wikipedia LQG statements 以原文为准")


if __name__ == "__main__":
    main()
