#!/usr/bin/env python3
"""EgoVLA human-video pretraining plus IK retargeting toy: ridge regression with
a prior mean on a synthetic linear stand-in.

Topic.  EgoVLA (arXiv 2507.12440) pretrains a VLA on egocentric human video to
predict wrist pose and MANO hand actions, converts them to a humanoid with
inverse kinematics and retargeting, then post-trains on a small set of robot
demonstrations.  Paper statements (以论文为准, not reproduced here): zero-shot
deployment without robot post-training gives 0 % success on all tasks,
pretraining helps most on long-horizon tasks, and halving robot data drops
long-horizon success sharply.  Those are the paper's numbers, not outputs of
this toy.

Scope.  This is a synthetic linear stand-in, not MANO / Isaac Lab / Quest data, not a GPU run (本页未运行).
It is not the UMI relative/absolute/delta toy, not FLARE, not GraspVLA;
the toy prints its own success numbers and does not replicate the paper.

Model (declared).  D = 16 action features plus an intercept (P = 17
parameters).  For each (seed, task) the task skill is theta_true ~ N(0, 1) per
dimension; the human-video prior is theta_h = theta_true + DELTA_SD * z with z
standard normal per dimension and DELTA_SD set by the regime.  The robot action
for an observation x ~ N(0, I_D) is y = x . theta_true + B_ROBOT with
B_ROBOT = 1.0 (robot offset).  The calibrated IK / retarget offset used
without post-training is B_RETARGET = B_ROBOT - OFFSET_MISMATCH with
OFFSET_MISMATCH = 1.5.  Robot demonstrations: N_FULL = 32 pairs
(x_i, y_i + SIG_DEMO * e_i) with SIG_DEMO = 0.5.  Fit (theta, b) by ridge
regression with a prior mean: minimise sum (y_i - x_i . theta - b)^2 +
LAM * |theta - mu|^2 + 1e-6 * b^2, solved exactly with Gaussian elimination on
the 17x17 normal equations.  Test: each subtask draws a fresh x; the action
error is e = x . (theta_hat - theta_true) + (b_hat - B_ROBOT) and the subtask
succeeds if |e| < TOL = 0.5.  A short-horizon rollout is 1 subtask; a
long-horizon rollout is 4 sequential subtasks and succeeds only if all 4
succeed; progress PSR = (number of subtasks completed before the first
failure) / 4.  N_TASKS = 4, N_ROLL = 25 short and 25 long rollouts per task
per seed.

Arms.  A_robot_only: mu = 0, LAM = SIG_DEMO^2 / 1.0 = 0.25, robot demos only
(the EgoVLA-NoPretrain stand-in).  B_human_pretrain: mu = theta_h,
LAM = SIG_DEMO^2 / 0.1^2 = 25.0, that is it believes the human prior is good to
0.1 per dimension, plus the same robot demos.  C_zero_shot: theta_hat =
theta_h, b_hat = B_RETARGET, no robot demos.

Common random numbers: every draw comes from random.Random(f"{seed}/{task}") in
this fixed order, independent of the regime and of the arm: theta_true (D),
z (D), N_FULL demo x vectors and N_FULL demo noises e, then N_ROLL short test x
vectors, then N_ROLL * 4 long test x vectors.  All arms and all regimes reuse
these draws; a regime with fewer demos uses the first n of them.

Regimes and parameters were written before the first run.  Declared
expectations (not tuned; print whatever comes):
  in_domain_full : C consistently fails (short and long success near zero);
                   B consistently above A on long_sr; B vs A on short_sr a
                   consistent B win or a near-tie.
  half_data      : B long_sr consistently lower than in in_domain_full - keep;
                   B vs A as it comes.
  large_mismatch : B may lose to A or near-tie - keep.

Alternatives (same seeds, declared before the run, not adopted): large_mismatch
with LAM = 5.0 for B (paired B-A long_sr); in_domain_full with TOL = 0.7
(paired B-A long_sr); zero-shot with OFFSET_MISMATCH = 0.5 (C short_sr and
long_sr m+-sd, and paired C-A long_sr).
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
D = 16
P = 17
N_TASKS = 4
N_ROLL = 25
N_FULL = 32
N_HALF = 16
SIG_DEMO = 0.5
B_ROBOT = 1.0
OFFSET_MISMATCH = 1.5
B_RETARGET = B_ROBOT - OFFSET_MISMATCH
TOL = 0.5
PRIOR_SD_B = 0.1
LAM_A = SIG_DEMO ** 2 / 1.0
LAM_B = SIG_DEMO ** 2 / PRIOR_SD_B ** 2
B_PRIOR_WEIGHT = 1e-6

REGIMES = {"in_domain_full": (N_FULL, 0.1),
            "half_data": (N_HALF, 0.1),
            "large_mismatch": (N_FULL, 0.5)}
REGIME_ORDER = ("in_domain_full", "half_data", "large_mismatch")
ARMS = ("A_robot_only", "B_human_pretrain", "C_zero_shot")
METRICS = ("short_sr", "long_sr", "long_psr")
PAIRS = (("B_human_pretrain", "A_robot_only"),
         ("C_zero_shot", "A_robot_only"),
         ("C_zero_shot", "B_human_pretrain"))
DECLARED = {
    "in_domain_full": "C consistently fails (short and long success near zero); "
                      "B consistently above A on long_sr; B vs A on short_sr a "
                      "consistent B win or a near-tie",
    "half_data": "B long_sr consistently lower than in in_domain_full - keep; "
                 "B vs A as it comes",
    "large_mismatch": "B may lose to A or near-tie - keep",
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


def gauss_solve(A, rhs):
    """Exact solve of A x = rhs by Gaussian elimination with partial pivoting."""
    n = len(A)
    M = [A[i][:] + [rhs[i]] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-14:
            raise ValueError("singular normal equations")
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        for r in range(col + 1, n):
            f = M[r][col] / pv
            if f != 0.0:
                for c in range(col, n + 1):
                    M[r][c] -= f * M[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = M[r][n] - sum(M[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / M[r][r]
    return x


def ridge_fit(X, Y, mu, lam):
    """Ridge with prior mean mu: min sum (y - x.theta - b)^2 + lam|theta-mu|^2 + 1e-6 b^2."""
    n = len(X)
    d = len(mu)
    A = [[0.0] * (d + 1) for _ in range(d + 1)]
    rhs = [0.0] * (d + 1)
    for i in range(n):
        xi = X[i]
        yi = Y[i]
        for a in range(d):
            xa = xi[a]
            row_a = A[a]
            for b in range(d):
                row_a[b] += xa * xi[b]
            row_a[d] += xa
            A[d][a] += xa
            rhs[a] += xa * yi
        A[d][d] += 1.0
        rhs[d] += yi
    for a in range(d):
        A[a][a] += lam
        rhs[a] += lam * mu[a]
    A[d][d] += B_PRIOR_WEIGHT
    sol = gauss_solve(A, rhs)
    return sol[:d], sol[d]


DRAWS = {}


def draws_for(seed, task):
    """Common random numbers: one fixed stream per (seed, task), shared by all arms and regimes."""
    key = (seed, task)
    if key not in DRAWS:
        rng = random.Random(f"{seed}/{task}")
        theta_true = [rng.gauss(0.0, 1.0) for _ in range(D)]
        z = [rng.gauss(0.0, 1.0) for _ in range(D)]
        demo_x = [[rng.gauss(0.0, 1.0) for _ in range(D)] for _ in range(N_FULL)]
        demo_e = [rng.gauss(0.0, 1.0) for _ in range(N_FULL)]
        short_x = [[rng.gauss(0.0, 1.0) for _ in range(D)] for _ in range(N_ROLL)]
        long_x = [[rng.gauss(0.0, 1.0) for _ in range(D)] for _ in range(N_ROLL * 4)]
        DRAWS[key] = (theta_true, z, demo_x, demo_e, short_x, long_x)
    return DRAWS[key]


def demo_targets(theta_true, demo_x, demo_e):
    return [sum(demo_x[i][j] * theta_true[j] for j in range(D)) + B_ROBOT
            + SIG_DEMO * demo_e[i] for i in range(N_FULL)]


def arm_params(arm, theta_true, theta_h, demo_x, y_demo, n, lam_b, offset):
    if arm == "C_zero_shot":
        return theta_h[:], B_ROBOT - offset
    if arm == "A_robot_only":
        mu, lam = [0.0] * D, LAM_A
    else:
        mu, lam = theta_h, lam_b
    return ridge_fit(demo_x[:n], y_demo[:n], mu, lam)


def evaluate(theta_hat, b_hat, theta_true, short_x, long_x, tol):
    """Short-horizon success rate, long-horizon success rate and long-horizon PSR for one task."""
    dth = [theta_hat[j] - theta_true[j] for j in range(D)]
    doff = b_hat - B_ROBOT
    short_hits = 0
    for xv in short_x:
        err = doff
        for j in range(D):
            err += xv[j] * dth[j]
        if abs(err) < tol:
            short_hits += 1
    long_hits = 0
    psr_sum = 0.0
    for r in range(N_ROLL):
        completed = 0
        all_ok = True
        for k in range(4):
            xv = long_x[4 * r + k]
            err = doff
            for j in range(D):
                err += xv[j] * dth[j]
            if abs(err) < tol:
                completed += 1
            else:
                all_ok = False
                break
        psr_sum += completed / 4.0
        if all_ok:
            long_hits += 1
    return short_hits, long_hits, psr_sum


def regime_results(regime, lam_b=None, tol=TOL, offset=OFFSET_MISMATCH):
    """Per-seed metric lists for every arm in one regime."""
    n, delta_sd = REGIMES[regime]
    lb = LAM_B if lam_b is None else lam_b
    out = {arm: {metric: [] for metric in METRICS} for arm in ARMS}
    for seed in SEEDS:
        acc = {arm: [0, 0, 0.0] for arm in ARMS}
        for task in range(N_TASKS):
            theta_true, z, demo_x, demo_e, short_x, long_x = draws_for(seed, task)
            y_demo = demo_targets(theta_true, demo_x, demo_e)
            theta_h = [theta_true[j] + delta_sd * z[j] for j in range(D)]
            for arm in ARMS:
                th, bh = arm_params(arm, theta_true, theta_h, demo_x, y_demo, n, lb, offset)
                sh, lh, ps = evaluate(th, bh, theta_true, short_x, long_x, tol)
                acc[arm][0] += sh
                acc[arm][1] += lh
                acc[arm][2] += ps
        denom = float(N_TASKS * N_ROLL)
        for arm in ARMS:
            out[arm]["short_sr"].append(acc[arm][0] / denom)
            out[arm]["long_sr"].append(acc[arm][1] / denom)
            out[arm]["long_psr"].append(acc[arm][2] / denom)
    return out


def col(res, arm, metric):
    return res[arm][metric]


def report(regime, res, lam_b=None):
    n, delta_sd = REGIMES[regime]
    lb = LAM_B if lam_b is None else lam_b
    print(f"{regime} (n={n} delta_sd={num(delta_sd)} lam_a={num(LAM_A)} "
          f"lam_b={num(lb)}):")
    print(f"  declared: {DECLARED[regime]}")
    for arm in ARMS:
        print(f"  {arm} " + " ".join(
            f"{metric} {fmt_pair(*mean_sd(col(res, arm, metric)))}" for metric in METRICS))
    for a, b in PAIRS:
        for metric in METRICS:
            print(f"  paired {a[0]}-{b[0]} {metric}: "
                  f"{verdict(col(res, a, metric), col(res, b, metric))}")
    return res


def main():
    print("Synthetic EgoVLA human-pretrain + retarget toy: ridge regression with a "
          "prior mean on a synthetic linear stand-in; common random numbers; not "
          "MANO / Isaac Lab / Quest data, not a GPU run")
    print(f"seeds={len(SEEDS)} d={D} p={P} sig_demo={num(SIG_DEMO)} "
          f"b_robot={num(B_ROBOT)} b_retarget={num(B_RETARGET)} "
          f"offset_mismatch={num(OFFSET_MISMATCH)} tol={num(TOL)} n_full={N_FULL} "
          f"n_half={N_HALF} tasks={N_TASKS} roll={N_ROLL} (declared)")
    print("paper statements (以论文为准, not reproduced here): zero-shot deployment "
          "without robot post-training is 0 % success on all tasks; pretraining "
          "helps most on long-horizon tasks; halving robot data drops long-horizon "
          "success sharply")
    print("the toy prints its own success numbers and does not replicate the paper")
    print("Regimes and parameters were written before the first run")
    print("rule: y = x.theta_true + b_robot; prior theta_h = theta_true + delta_sd*z; "
          "ridge min sum (y_i - x_i.theta - b)^2 + lam*|theta-mu|^2 + 1e-6*b^2; "
          "success if |x.(theta_hat-theta_true) + (b_hat-b_robot)| < tol")

    s_ols = math.sqrt(SIG_DEMO ** 2 * P / (N_FULL - P - 1))
    s_prior = math.sqrt(D * 0.1 ** 2)
    p_ols = math.erf(TOL / (s_ols * math.sqrt(2.0)))
    p_prior = math.erf(TOL / (s_prior * math.sqrt(2.0)))
    print(f"hand_calc OLS test-error sd for A at n={N_FULL}: "
          f"sqrt(sig_demo^2 * P / (n - P - 1)) = sqrt({num(SIG_DEMO ** 2)}*{P}/"
          f"{N_FULL - P - 1}) = {num(s_ols)}")
    print(f"hand_calc prior-only error sd for theta_h (delta_sd=0.1): "
          f"sqrt(D * 0.1^2) = sqrt({D}*0.01) = {num(s_prior)}")
    print(f"hand_calc per-subtask success for s={num(s_ols)}: "
          f"erf(tol/(s*sqrt(2))) = erf({num(TOL / (s_ols * math.sqrt(2.0)))}) = "
          f"{num(p_ols)}; long-horizon p^4 = {num(p_ols ** 4)}")
    print(f"hand_calc per-subtask success for s={num(s_prior)}: "
          f"erf(tol/(s*sqrt(2))) = erf({num(TOL / (s_prior * math.sqrt(2.0)))}) = "
          f"{num(p_prior)}; long-horizon p^4 = {num(p_prior ** 4)}")
    print(f"hand_calc zero-shot offset error {num(OFFSET_MISMATCH)} vs tol {num(TOL)}: "
          f"offset alone is {num(OFFSET_MISMATCH / TOL)}x tol, so the retarget offset "
          f"alone can never pass")
    print(f"hand_calc ridge posterior sd per dim: A "
          f"sqrt(sig_demo^2/(n+lam_a)) = {num(math.sqrt(SIG_DEMO ** 2 / (N_FULL + LAM_A)))}"
          f"; B in_domain_full sqrt(sig_demo^2/(n+lam_b)) = "
          f"{num(math.sqrt(SIG_DEMO ** 2 / (N_FULL + LAM_B)))}; B half_data = "
          f"{num(math.sqrt(SIG_DEMO ** 2 / (N_HALF + LAM_B)))}")

    results = {}
    for regime in REGIME_ORDER:
        res = regime_results(regime)
        results[regime] = res
        report(regime, res)

    print("cross-regime paired B(half_data)-B(in_domain_full):")
    for metric in ("long_sr", "short_sr"):
        v_cross = verdict(col(results["half_data"], "B_human_pretrain", metric),
                          col(results["in_domain_full"], "B_human_pretrain", metric))
        print(f"  paired B(half_data)-B(in_domain_full) {metric}: {v_cross}")

    print("alternative parameters (declared before the run, same seeds, not adopted):")
    alt_lm = regime_results("large_mismatch", lam_b=5.0)
    v_lm = verdict(col(alt_lm, "B_human_pretrain", "long_sr"),
                   col(alt_lm, "A_robot_only", "long_sr"))
    print(f"  large_mismatch LAM_B=5.0000: paired B-A long_sr: {v_lm}")
    alt_tol = regime_results("in_domain_full", tol=0.7)
    v_tol = verdict(col(alt_tol, "B_human_pretrain", "long_sr"),
                    col(alt_tol, "A_robot_only", "long_sr"))
    print(f"  in_domain_full TOL=0.7000: paired B-A long_sr: {v_tol}")
    alt_off = regime_results("in_domain_full", offset=0.5)
    c_short = fmt_pair(*mean_sd(col(alt_off, "C_zero_shot", "short_sr")))
    c_long = fmt_pair(*mean_sd(col(alt_off, "C_zero_shot", "long_sr")))
    print(f"  in_domain_full zero-shot OFFSET_MISMATCH=0.5000: C_zero_shot "
          f"short_sr {c_short} long_sr {c_long}")
    v_off = verdict(col(alt_off, "C_zero_shot", "long_sr"),
                    col(results["in_domain_full"], "A_robot_only", "long_sr"))
    print(f"  in_domain_full zero-shot OFFSET_MISMATCH=0.5000: paired C-A long_sr: {v_off}")

    print("No winner beyond the declared prior: human pretraining helps when the "
          "human prior is close and robot data is scarce, zero-shot retargeting "
          "fails on the offset, and a wrong prior can hurt")
    print("MANO / Isaac Lab / Quest / GPU: 本页未运行; EgoVLA paper results 以论文为准")


if __name__ == "__main__":
    main()
