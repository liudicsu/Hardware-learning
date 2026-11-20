#!/usr/bin/env python3
"""foc_dq_decoupling_toy.py: current-mode d/q feedforward on a coupled plant.

stdlib CPU comparison. Official SimpleFOC flash is 本页未运行. This is not a
run of the library, not a port of the firmware, and not a third PWM rail.

Shared plant (opened SimpleFOC voltage-mode model):

    u_d = R * i_d + L_d * di_d/dt - v_e * L_q * i_q
    u_q = R * i_q + L_q * di_q/dt + v_e * L_d * i_d + U_bemf

with v_e = n_pp * v and the opened first back-EMF law U_bemf = K_e * v,
where v is mechanical speed. v is prescribed in each cell; i_q is a torque
proxy and does not integrate rotor mechanics. Forward Euler needs
dt << L/R; the printed hand_calc lines name L_d/R and L_q/R.

Official current-mode laws, if L_d and L_q are provided (opened current-mode
page; feedforward uses the unhatted i_d, i_q, which on that page are the
same symbols as the current references; d-axis target is 0):

    u_q = PI_q(i_q - i_hat_q) + L_d * i_d * v_e
    u_d = PI_d(-i_hat_d) - L_q * i_q * v_e

PI-only (no inductance feedforward) is the same without those extra terms.
PI uses measured currents i_hat_d, i_hat_q. Integrators have no anti-windup.
V_LIM is a soft ud/uq clamp only, not a real PWM DC-rail / duty limit.

Arms, written before the first official run:
  (A) PI-only current mode, no inductance feedforward
  (B) official current-mode feedforward as written above (adopted)
  (C) wrong-sign d-axis compensation: u_d = PI_d + L_q * i_q * v_e (lose arm)
  ALT_VOLTAGE_MODE_LAG: voltage-mode u_d = -v_e * L_q * i_q and
    u_q = R * i_q + U_bemf, with no current PI. Named, printed, not adopted.

Common random numbers: each seed draws one current-noise sequence shared
by all four arms. Five seeds. Metrics are plant-frame RMSE of i_d and i_q
against the references over the declared window (lower is better).

Regimes, written before the first official run (keep whatever the frozen
first run prints; do not retune R, L, or v_e after that freeze):
  low_speed_settled     low speed, modest constant i_q, settled window:
                        A and B may near-tie on i_d or i_q tracking (keep;
                        an exact tie is also allowed if the freeze prints it)
  high_speed_iq_step    high v_e and a dynamic i_q step: B consistent lower
                        |i_d| error and/or better i_q tracking than A (keep);
                        wrong-sign C loses on this cell (keep)

Label order: exact tie; numerically zero (floating-point residue); near-tie
(|m| <= sd); then small vs clear using 20 % of the smaller-arm mean, with a
sign count. Printed numbers use ASCII minus and +-.
"""
from __future__ import annotations

import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Lesson-chosen parameters, named before the first official run.
R = 0.8000
L_D = 0.0020
L_Q = 0.0024
N_PP = 7
K_E = 0.0400  # U_bemf = K_E * v; v is mechanical
DT = 1e-4
KP_D = 5.0000
KI_D = 1000.0000
KP_Q = 5.0000
KI_Q = 1000.0000
V_LIM = 24.0000  # soft ud/uq clamp only; not a real PWM rail
ID_REF = 0.0000
NOISE_I = 0.0200

# low_speed_settled: modest i_q, slow / settled reference
LOW_V = 8.0000
LOW_IQ = 1.0000
LOW_TOTAL = 0.0800
LOW_WARM = 0.0400

# high_speed_iq_step: high electrical speed and a step in i_q
HIGH_V = 220.0000
HIGH_IQ_BEFORE = 0.5000
HIGH_IQ_AFTER = 2.0000
HIGH_STEP_T = 0.0100
HIGH_TOTAL = 0.0400
HIGH_METRIC_START = 0.0100


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
    n = len(diffs)
    opp = sum(1 for d in diffs if d * m < 0)
    zero = sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def fmt_mean(xs):
    m, s = mean_sd(xs)
    return fmt_pair(m, s)


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return (
            f"{fmt_pair(m, s)}: numerically zero (floating-point residue), "
            "effectively a tie"
        )
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < SMALL_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def soft_clamp(u):
    return max(-V_LIM, min(V_LIM, u))


def noise_stream(seed, n_steps):
    """One current-noise sequence per seed, reused by every arm (CRN)."""
    rng = random.Random(seed)
    return [(rng.gauss(0.0, NOISE_I), rng.gauss(0.0, NOISE_I)) for _ in range(n_steps)]


def run_arm(arm, noise, v, iq_of_t, total, metric_start):
    n = int(round(total / DT))
    metric_i0 = int(round(metric_start / DT))
    v_e = N_PP * v
    u_bemf = K_E * v
    id_p = 0.0
    iq_p = 0.0
    int_d = 0.0
    int_q = 0.0
    s_id = 0.0
    s_iq = 0.0
    n_m = 0
    sat = 0
    for k in range(n):
        t = k * DT
        iq_ref = iq_of_t(t)
        n_d, n_q = noise[k]
        id_hat = id_p + n_d
        iq_hat = iq_p + n_q
        err_d = ID_REF - id_hat
        err_q = iq_ref - iq_hat
        if arm == "ALT":
            pi_d = 0.0
            pi_q = 0.0
        else:
            int_d += err_d * DT  # no anti-windup (omitted)
            int_q += err_q * DT
            pi_d = KP_D * err_d + KI_D * int_d
            pi_q = KP_Q * err_q + KI_Q * int_q
        # Unhatted i_d, i_q in the opened feedforward are the references.
        ff_d = -L_Q * iq_ref * v_e
        ff_q = L_D * ID_REF * v_e
        if arm == "A":
            ud, uq = pi_d, pi_q
        elif arm == "B":
            ud, uq = pi_d + ff_d, pi_q + ff_q
        elif arm == "C":
            ud, uq = pi_d - ff_d, pi_q + ff_q
        elif arm == "ALT":
            ud, uq = ff_d, R * iq_ref + u_bemf
        else:
            raise ValueError(arm)
        ud_c = soft_clamp(ud)
        uq_c = soft_clamp(uq)
        if ud_c != ud or uq_c != uq:
            sat += 1
        did = (ud_c - R * id_p + v_e * L_Q * iq_p) / L_D
        diq = (uq_c - R * iq_p - v_e * L_D * id_p - u_bemf) / L_Q
        id_p += did * DT
        iq_p += diq * DT
        if k >= metric_i0:
            s_id += (id_p - ID_REF) ** 2
            s_iq += (iq_p - iq_ref) ** 2
            n_m += 1
    return {
        "id_rmse": math.sqrt(s_id / n_m),
        "iq_rmse": math.sqrt(s_iq / n_m),
        "sat": float(sat),
        "n_m": n_m,
    }


def collect(arm, v, iq_of_t, total, metric_start):
    n = int(round(total / DT))
    rows = []
    for seed in SEEDS:
        noise = noise_stream(seed, n)
        rows.append(run_arm(arm, noise, v, iq_of_t, total, metric_start))
    return rows


def print_arm_means(label, rows):
    print(
        f"{label} id_rmse={fmt_mean([r['id_rmse'] for r in rows])} "
        f"iq_rmse={fmt_mean([r['iq_rmse'] for r in rows])} "
        f"sat_hits={fmt_mean([r['sat'] for r in rows])}"
    )


def print_regime(name, expectation, v, iq_of_t, total, metric_start, extra_lines):
    print(f"regime {name}")
    print(expectation)
    for line in extra_lines:
        print(line)
    series = {}
    for arm in ("A", "B", "C", "ALT"):
        series[arm] = collect(arm, v, iq_of_t, total, metric_start)
        label = "ALT_VOLTAGE_MODE_LAG" if arm == "ALT" else arm
        print_arm_means(label, series[arm])
    print("adopted=B not_adopted=ALT_VOLTAGE_MODE_LAG")
    for key in ("id_rmse", "iq_rmse"):
        xs = {arm: [r[key] for r in series[arm]] for arm in series}
        print(f"paired B-A {key}: {verdict(xs['B'], xs['A'])}")
        print(f"paired C-A {key}: {verdict(xs['C'], xs['A'])}")
        print(f"paired C-B {key}: {verdict(xs['C'], xs['B'])}")
        print(
            f"paired ALT-B {key}: {verdict(xs['ALT'], xs['B'])} (not adopted)"
        )


def low_iq(_t):
    return LOW_IQ


def high_iq(t):
    return HIGH_IQ_AFTER if t >= HIGH_STEP_T else HIGH_IQ_BEFORE


def main():
    print("foc_dq_decoupling_toy")
    print(
        "stdlib CPU shared dq plant; official SimpleFOC flash 本页未运行"
    )
    print(
        "U_bemf law: U_bemf = K_e * v (mechanical); "
        "v_e = n_pp * v; v prescribed, no rotor mechanics"
    )
    print("anti_windup=omitted")
    print("pwm_rail_limit=omitted")  # V_LIM is a soft ud/uq clamp only
    print(
        "feedforward uses unhatted i_d, i_q = current references "
        "(d-axis target 0)"
    )
    print(
        f"R={num(R)} L_d={num(L_D)} L_q={num(L_Q)} n_pp={N_PP} K_e={num(K_E)}"
    )
    print(
        f"dt={num(DT)} kp_d={num(KP_D)} ki_d={num(KI_D)} "
        f"kp_q={num(KP_Q)} ki_q={num(KI_Q)}"
    )
    print(
        f"V_LIM={num(V_LIM)} id_ref={num(ID_REF)} noise_i={num(NOISE_I)}"
    )
    print("seeds=" + ",".join(str(s) for s in SEEDS) + " common_random_numbers=true")
    print(f"SMALL_FRAC={num(SMALL_FRAC)}")
    print(
        f"hand_calc L_d/R = {num(L_D)}/{num(R)} = {num(L_D / R)}"
    )
    print(
        f"hand_calc L_q/R = {num(L_Q)}/{num(R)} = {num(L_Q / R)}"
    )
    print("hand_calc 30+25+50+40+35=180")

    v_e_low = N_PP * LOW_V
    u_bemf_low = K_E * LOW_V
    coup_low = v_e_low * L_Q * LOW_IQ
    print_regime(
        "low_speed_settled",
        "declared: A and B may near-tie on id or iq tracking when settled "
        "at low speed (keep)",
        LOW_V,
        low_iq,
        LOW_TOTAL,
        LOW_WARM,
        [
            f"v={num(LOW_V)} iq_ref={num(LOW_IQ)} (constant) "
            f"total={num(LOW_TOTAL)} warm={num(LOW_WARM)}",
            f"hand_calc v_e = n_pp*v = {N_PP}*{num(LOW_V)} = {num(v_e_low)}",
            f"hand_calc U_bemf = K_e*v = {num(K_E)}*{num(LOW_V)} = {num(u_bemf_low)}",
            f"hand_calc v_e*L_q*iq_ref = {num(v_e_low)}*{num(L_Q)}*{num(LOW_IQ)} "
            f"= {num(coup_low)}",
        ],
    )

    v_e_high = N_PP * HIGH_V
    u_bemf_high = K_E * HIGH_V
    coup_high = v_e_high * L_Q * HIGH_IQ_AFTER
    print_regime(
        "high_speed_iq_step",
        "declared: B consistent lower |id| error and/or better iq tracking "
        "than A; wrong-sign C loses (keep)",
        HIGH_V,
        high_iq,
        HIGH_TOTAL,
        HIGH_METRIC_START,
        [
            f"v={num(HIGH_V)} iq_ref steps {num(HIGH_IQ_BEFORE)} -> "
            f"{num(HIGH_IQ_AFTER)} at t={num(HIGH_STEP_T)}; "
            f"total={num(HIGH_TOTAL)} metric from t={num(HIGH_METRIC_START)}",
            f"hand_calc v_e = n_pp*v = {N_PP}*{num(HIGH_V)} = {num(v_e_high)}",
            f"hand_calc U_bemf = K_e*v = {num(K_E)}*{num(HIGH_V)} = {num(u_bemf_high)}",
            f"hand_calc v_e*L_q*iq_after = {num(v_e_high)}*{num(L_Q)}*"
            f"{num(HIGH_IQ_AFTER)} = {num(coup_high)}",
        ],
    )


if __name__ == "__main__":
    main()
