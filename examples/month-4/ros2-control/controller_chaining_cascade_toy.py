#!/usr/bin/env python3
"""Synthetic ros2_control controller-chaining / cascade stand-in.

Stdlib only. Discrete-time two-time-scale plant. No real controller_manager
process is started, and no EtherCAT timing or Ziegler-Nichols tuning is
re-taught here.

A shared outer reference, shared measurement-noise sequence and shared
inner-disturbance draws are generated once per (regime, seed) and then
read by every arm (common random numbers).

Arms:
  A_single -- the outer command is written straight to the hardware
    command interface (no inner loop).
  B_cascade -- the preceding outer controller claims the following inner
    controller's reference interfaces; the inner loop is in chained mode
    and its subscriber is disabled.
  C_broken -- the preceding controller is activated while the following
    controller is still inactive, so the exported reference interfaces
    stay unavailable / unclaimed and the hardware command stays at 0.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.

Activation order, chained-mode subscriber behaviour, and reference-interface
availability stay 以文档为准.
Real ros2_control / DiffBot / hardware: 本页未运行.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared discrete-time stand-in (not a textbook "cascade is always 2x" claim).
DT = 0.002  # s
T_SIM = 8.0000  # s
T_WARM = 1.0000  # s, dropped from the RMSE window
N_STEP = int(round(T_SIM / DT))
TAU_INNER = 0.0250  # s, fast inner plant
TAU_OUTER = 0.6000  # s, slow outer plant
T_REF = 2.5000  # s, slow reference time constant
KP_SINGLE = 1.8500  # single-loop gain on the hardware command
KP_OUTER = 2.0000  # preceding outer gain, writes the inner reference
KP_INNER = 12.0000  # following inner gain, chained mode
SIG_Y = 0.0100  # shared measurement-noise stddev
DIST_AMP = 0.3500  # inner-state step disturbance
DIST_START = 2.0000  # s
U_BROKEN = 0.0000  # hardware command when the following controller is inactive

# Named alternative, same seeds, not adopted.
KP_SINGLE_ALT = 1.5000

ARMS = ("A_single", "B_cascade", "C_broken")
METRICS = ("outer_rmse", "inner_rmse")
PAIRS = (("B", "A"), ("C", "A"), ("C", "B"))

# name: (has_inner_dist, declared expectation); written before the first run
REGIMES = {
    "slow_no_dist": (
        False,
        "A and B may near-tie on outer error - keep",
    ),
    "inner_disturbance": (
        True,
        "B consistent better inner tracking / outer error - keep",
    ),
    "broken_chain": (
        False,
        "C loses (following inactive, reference unavailable) - keep",
    ),
}


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


def zoh(tau, dt=DT):
    a = math.exp(-dt / tau)
    return a, 1.0 - a


def rng_for(*parts):
    h = 16
    for part in parts:
        if isinstance(part, str):
            for ch in part:
                h = (h * 131 + ord(ch)) & 0xFFFFFFFFFFFFFFFF
        else:
            h = (h * 131 + int(part)) & 0xFFFFFFFFFFFFFFFF
    return random.Random(h)


def shared_draws(seed, has_inner_dist, tag="official"):
    """Common random numbers: reference is deterministic; noise and optional step shared."""
    rng = rng_for("chain-draws", tag, seed, int(round(SIG_Y * 1e6)), int(has_inner_dist))
    meas = [SIG_Y * rng.gauss(0.0, 1.0) for _ in range(N_STEP)]
    dist = []
    for k in range(N_STEP):
        t = k * DT
        if has_inner_dist and t >= DIST_START:
            dist.append(DIST_AMP)
        else:
            dist.append(0.0)
    return {"meas": meas, "dist": dist}


def reference(k):
    return 1.0 - math.exp(-(k * DT) / T_REF)


def evaluate(arm, draws, kp_single=KP_SINGLE):
    a_i, b_i = zoh(TAU_INNER)
    a_o, b_o = zoh(TAU_OUTER)
    y = 0.0
    v = 0.0
    u = 0.0
    outer_sq = 0.0
    inner_sq = 0.0
    n_win = 0
    for k in range(N_STEP):
        r = reference(k)
        y_meas = y + draws["meas"][k]
        # Diagnostic inner reference (same outer gain for every arm) so
        # inner_rmse compares how well the inner state tracks that request.
        v_ref_diag = KP_OUTER * (r - y_meas)
        if arm == "A_single":
            u = kp_single * (r - y_meas)
        elif arm == "B_cascade":
            # Preceding outer claims the following inner reference; subscriber off.
            u = KP_INNER * (v_ref_diag - v)
        elif arm == "C_broken":
            # Following controller inactive: reference interfaces unavailable.
            u = U_BROKEN
        else:
            raise ValueError(arm)
        v = a_i * v + b_i * u + draws["dist"][k]
        y = a_o * y + b_o * v
        if k * DT >= T_WARM:
            outer_sq += (r - y) ** 2
            inner_sq += (v_ref_diag - v) ** 2
            n_win += 1
    return {
        "outer_rmse": math.sqrt(outer_sq / n_win),
        "inner_rmse": math.sqrt(inner_sq / n_win),
    }


def run_regime(name, seed, kp_single=KP_SINGLE, tag="official"):
    has_dist, _decl = REGIMES[name]
    draws = shared_draws(seed, has_dist, tag=f"{tag}|{name}")
    row = {}
    for arm in ARMS:
        row[arm] = evaluate(arm, draws, kp_single=kp_single)
    return row


def print_regime(title, rows):
    print(f"regime {title}  (mean+-sd over seeds)")
    for arm in ARMS:
        outer = [r[arm]["outer_rmse"] for r in rows]
        inner = [r[arm]["inner_rmse"] for r in rows]
        print(
            f"  {arm} outer_rmse {num(mean_sd(outer)[0])}+-{num(mean_sd(outer)[1])} "
            f"inner_rmse {num(mean_sd(inner)[0])}+-{num(mean_sd(inner)[1])}"
        )
    for left, right in PAIRS:
        la = [a for a in ARMS if a.startswith(left)][0]
        ra = [a for a in ARMS if a.startswith(right)][0]
        for key in METRICS:
            xa = [r[la][key] for r in rows]
            xb = [r[ra][key] for r in rows]
            print(f"  paired {left}-{right} {key}: {verdict(xa, xb)}")


def official_rows(name, kp_single=KP_SINGLE, tag="official"):
    return [run_regime(name, seed, kp_single=kp_single, tag=tag) for seed in SEEDS]


def main():
    a_i, b_i = zoh(TAU_INNER)
    a_o, b_o = zoh(TAU_OUTER)
    n_win = sum(1 for k in range(N_STEP) if k * DT >= T_WARM)
    print("Synthetic controller-chaining cascade stand-in; not a real controller_manager")
    print(
        f"declared DT={num(DT)} s T_SIM={num(T_SIM)} s T_WARM={num(T_WARM)} s "
        f"N_STEP={N_STEP} TAU_INNER={num(TAU_INNER)} s TAU_OUTER={num(TAU_OUTER)} s "
        f"T_REF={num(T_REF)} s"
    )
    print(
        f"declared KP_SINGLE={num(KP_SINGLE)} KP_OUTER={num(KP_OUTER)} "
        f"KP_INNER={num(KP_INNER)} SIG_Y={num(SIG_Y)} DIST_AMP={num(DIST_AMP)} "
        f"DIST_START={num(DIST_START)} s U_BROKEN={num(U_BROKEN)} "
        f"SMALL_FRAC={num(SMALL_FRAC)} seeds={','.join(str(s) for s in SEEDS)}"
    )
    print(
        "declared arms: A_single writes the hardware command interface; "
        "B_cascade preceding outer claims the following inner reference "
        "(chained mode, subscriber disabled); C_broken following still inactive"
    )
    print(f"hand_calc inner ZOH a={num(a_i)} b={num(b_i)}")
    print(f"hand_calc outer ZOH a={num(a_o)} b={num(b_o)}")
    print(f"hand_calc TAU_OUTER/TAU_INNER = {num(TAU_OUTER / TAU_INNER)}")
    print(f"hand_calc RMSE window steps after T_WARM = {n_win}")
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print(
        "docs_commit=b558c3ab693fbf9aa472392cafc0c0f14f9fc549 "
        "(2026-11-17 21:59:51 UTC = 2026-11-18 05:59:51 Asia/Shanghai)"
    )
    print("docs_blob=0b91260a4064e51fce45e0de1e09101c5147fd02")
    print(
        "docs_example16_commit=b34cc5917f216b36ff3bda1ca0cc0736ecc00235 "
        "(2025-07-10 07:15:16 UTC = 2025-07-10 15:15:16 Asia/Shanghai)"
    )
    print("docs_example16_blob=331f9881206b6a71a60b6c5b0463161c2039e99b")
    print(
        "docs_contract: first activate all following controllers before the preceding one; "
        "deactivation is the inverse; switch_controllers may take the chain as a list; "
        "spawner --activate-as-group (Jazzy chaining page; 以文档为准)"
    )
    print(
        "docs_chained_mode: a chainable controller in chained mode disables its external "
        "subscribers (PID <controller_name>/pid_reference; diff_drive_controller cmd_vel "
        "and cmd_vel_unstamped; publishers may continue) (以文档为准)"
    )
    print(
        "docs_reference_interfaces: unavailable+unclaimed when the exporter is inactive; "
        "available+unclaimed when active but not chained (references from the subscriber); "
        "available+claimed when chained (Jazzy chaining page / DiffBot example 16; 以文档为准)"
    )
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: the measurement-noise sequence and inner-disturbance "
        "step are shared across arms at each regime and seed; the outer reference is shared"
    )
    print(
        "Assumptions: discrete-time ZOH stand-in, not controller_manager, not a copied "
        "numerical claim that cascade is always 2x better"
    )
    print("Documentation figures (activation order, chained mode, claimed/unclaimed) 以文档为准")
    print("Real ros2_control / DiffBot / hardware: 本页未运行")
    print("declared slow_no_dist: A and B may near-tie on outer error - keep")
    print("declared inner_disturbance: B consistent better inner tracking / outer error - keep")
    print("declared broken_chain: C loses (following inactive, reference unavailable) - keep")

    official = {name: official_rows(name) for name in REGIMES}
    for name, (_has, decl) in REGIMES.items():
        print(f"declared expectation {name}: {decl}")
        print_regime(name, official[name])

    print(f"alternative same seeds KP_SINGLE={num(KP_SINGLE_ALT)} (not adopted)")
    print(
        f"hand_calc alternative KP_SINGLE={num(KP_SINGLE_ALT)} vs official {num(KP_SINGLE)}"
    )
    for name in REGIMES:
        print_regime(
            f"{name} alt_kp_single={num(KP_SINGLE_ALT)}",
            official_rows(name, kp_single=KP_SINGLE_ALT, tag="official"),
        )

    print("No real controller_manager process was started")
    print(
        "No winner is universal: a well-tuned single loop may near-tie a cascade on a "
        "slow undisturbed reference; the chain matters when the inner loop must reject "
        "a disturbance, and a broken activation order leaves the command at zero"
    )


if __name__ == "__main__":
    main()
