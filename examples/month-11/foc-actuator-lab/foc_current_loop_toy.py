#!/usr/bin/env python3
"""foc_current_loop_toy.py: electrical angle + dq PI on an R–L circuit (stdlib).

Naming LOCKED: the plant is an R–L electrical circuit model (resistance R,
inductance L). It is NOT reinforcement learning.

Simulator vs controller angle contract:
  - Ground-truth physical electrical angle theta_e_star lives ONLY inside the
    plant integrator (back-EMF / how the fictitious machine rotates).
  - The controller NEVER receives theta_e_star. It only sees noisy theta_m_meas
    (and reconstructed currents) and computes hat_theta_e =
    normalize(d * p_ctrl * theta_m_meas - theta_e0_ctrl).
  - Ablation "wrong offset / wrong p" means the controller's hat_theta_e is wrong
    while theta_e_star stays consistent with the plant. Both arms share the SAME
    measurement-noise draws.

Metrics (LOCKED):
  - ctrl_*_rmse: controller-frame tracking of id/iq refs (what the PI sees).
  - plant_*_rmse: true-frame plant currents vs refs (actual torque/flux axes).
    Wrong hat_theta_e can look "OK" in ctrl frame while plant frame drifts —
    that is the pedagogical point.
  - ang_rmse: wrap(hat_theta_e - theta_e_star), diagnostic only (offline; not a
    controller input).

Clarke / Park transforms that are not plant dynamics are algebraic identities.
Cross-coupling omega*L*i terms are OMITTED on BOTH arms (locked).
SinePWM-shaped phase voltage floats only — no MCU timer.

Also OMITTED (stated in the lesson): anti-windup on the integrators; a real
PWM DC-rail / duty limit (V_LIM is a soft clamp on ud/uq only). With the
chosen gains and back-EMF, all three arms report sat=0 (clamp never hits).
Mechanics: OMEGA_M is a prescribed constant; iq is a torque *proxy* and does
NOT integrate rotor speed. Forward-Euler on the R–L ODE needs DT << L/R
(here DT=1e-4 s, L/R≈2.1 ms).
"""
import math
import random

SEED = 13
DT = 1e-4
N = 4000
WARM = 800
R = 1.2
L = 0.0025
KE = 0.04
V_LIM = 8.0
IQ_REF = 1.0
ID_REF = 0.0
OMEGA_M = 6.0
P_TRUE = 7
D_TRUE = 1
THETA_E0_TRUE = 0.20
NOISE_THETA = 0.0015
NOISE_I = 0.015
KP_D, KI_D = 3.0, 800.0
KP_Q, KI_Q = 3.0, 800.0


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def electrical_angle(d, p, theta_m, theta_e0):
    return wrap(d * p * theta_m - theta_e0)


def inv_park(ud, uq, th):
    c, s = math.cos(th), math.sin(th)
    return c * ud - s * uq, s * ud + c * uq


def inv_clarke(ua, ub):
    return (
        ua,
        -0.5 * ua + (math.sqrt(3) / 2) * ub,
        -0.5 * ua - (math.sqrt(3) / 2) * ub,
    )


def clarke(ia, ib, _ic):
    return ia, (ia + 2 * ib) / math.sqrt(3)


def park(i_alpha, i_beta, th):
    c, s = math.cos(th), math.sin(th)
    return i_alpha * c + i_beta * s, -i_alpha * s + i_beta * c


def run_arm(p_ctrl, theta_e0_ctrl, noise_theta, noise_i):
    theta_m = 0.0
    id_plant = 0.0
    iq_plant = 0.0
    int_d = 0.0
    int_q = 0.0
    s_ctrl_id = s_ctrl_iq = s_plant_id = s_plant_iq = s_ang = 0.0
    n_metric = 0
    sat_hits = 0
    ua = ub = uc = 0.0

    for k in range(N):
        theta_e_star = electrical_angle(D_TRUE, P_TRUE, theta_m, THETA_E0_TRUE)
        omega_e = D_TRUE * P_TRUE * OMEGA_M
        e_q = KE * omega_e

        theta_m_meas = theta_m + noise_theta[k]
        hat_theta_e = electrical_angle(D_TRUE, p_ctrl, theta_m_meas, theta_e0_ctrl)

        i_alpha_p, i_beta_p = inv_park(id_plant, iq_plant, theta_e_star)
        ia, ib, ic = inv_clarke(i_alpha_p, i_beta_p)
        ia_m = ia + noise_i[3 * k]
        ib_m = ib + noise_i[3 * k + 1]
        ic_m = ic + noise_i[3 * k + 2]
        a, b = clarke(ia_m, ib_m, ic_m)
        id_meas, iq_meas = park(a, b, hat_theta_e)

        err_d = ID_REF - id_meas
        err_q = IQ_REF - iq_meas
        int_d += err_d * DT  # no anti-windup (omitted)
        int_q += err_q * DT
        ud_raw = KP_D * err_d + KI_D * int_d
        uq_raw = KP_Q * err_q + KI_Q * int_q
        ud = max(-V_LIM, min(V_LIM, ud_raw))
        uq = max(-V_LIM, min(V_LIM, uq_raw))
        if ud != ud_raw or uq != uq_raw:
            sat_hits += 1  # soft ud/uq clamp only; not a real PWM rail

        ual, ubt = inv_park(ud, uq, hat_theta_e)
        ua, ub, uc = inv_clarke(ual, ubt)

        a_v, b_v = clarke(ua, ub, uc)
        ud_plant, uq_plant = park(a_v, b_v, theta_e_star)

        # R–L circuit; cross-coupling omitted on BOTH arms
        id_plant += ((ud_plant - R * id_plant - 0.0) / L) * DT
        iq_plant += ((uq_plant - R * iq_plant - e_q) / L) * DT

        if k >= WARM:
            s_ctrl_id += (id_meas - ID_REF) ** 2
            s_ctrl_iq += (iq_meas - IQ_REF) ** 2
            s_plant_id += (id_plant - ID_REF) ** 2
            s_plant_iq += (iq_plant - IQ_REF) ** 2
            s_ang += wrap(hat_theta_e - theta_e_star) ** 2
            n_metric += 1

        theta_m += OMEGA_M * DT

    return {
        "ctrl_id_rmse": math.sqrt(s_ctrl_id / n_metric),
        "ctrl_iq_rmse": math.sqrt(s_ctrl_iq / n_metric),
        "plant_id_rmse": math.sqrt(s_plant_id / n_metric),
        "plant_iq_rmse": math.sqrt(s_plant_iq / n_metric),
        "ang_rmse": math.sqrt(s_ang / n_metric),
        "sat_hits": sat_hits,
        "ua": ua, "ub": ub, "uc": uc,
    }


rng = random.Random(SEED)
noise_theta = [rng.gauss(0.0, NOISE_THETA) for _ in range(N)]
noise_i = [rng.gauss(0.0, NOISE_I) for _ in range(3 * N)]

ok = run_arm(P_TRUE, THETA_E0_TRUE, noise_theta, noise_i)
bad_off = run_arm(P_TRUE, THETA_E0_TRUE + 0.55, noise_theta, noise_i)
bad_p = run_arm(5, THETA_E0_TRUE, noise_theta, noise_i)

print(f"seed={SEED}")
print(f"dt={DT:.1e} N={N} warm={WARM}")
print(f"R_ohm={R:.2f} L_H={L:.4f}")
print("plant_model=R_L_circuit")
print(f"p_true={P_TRUE} theta_e0_true={THETA_E0_TRUE:.3f}")
print(f"iq_ref={IQ_REF:.1f} id_ref={ID_REF:.1f}")
print("cross_coupling=omitted_both_arms")
print(f"ok_ctrl_iq_rmse={ok['ctrl_iq_rmse']:.6f}")
print(f"ok_ctrl_id_rmse={ok['ctrl_id_rmse']:.6f}")
print(f"ok_plant_iq_rmse={ok['plant_iq_rmse']:.6f}")
print(f"ok_plant_id_rmse={ok['plant_id_rmse']:.6f}")
print(f"ok_ang_rmse={ok['ang_rmse']:.6f}")
print(f"bad_offset_ctrl_iq_rmse={bad_off['ctrl_iq_rmse']:.6f}")
print(f"bad_offset_plant_iq_rmse={bad_off['plant_iq_rmse']:.6f}")
print(f"bad_offset_plant_id_rmse={bad_off['plant_id_rmse']:.6f}")
print(f"bad_offset_ang_rmse={bad_off['ang_rmse']:.6f}")
print(f"bad_pp_ctrl_iq_rmse={bad_p['ctrl_iq_rmse']:.6f}")
print(f"bad_pp_plant_iq_rmse={bad_p['plant_iq_rmse']:.6f}")
print(f"bad_pp_plant_id_rmse={bad_p['plant_id_rmse']:.6f}")
print(f"bad_pp_ang_rmse={bad_p['ang_rmse']:.6f}")
print(f"ok_ua={ok['ua']:.6f} ok_ub={ok['ub']:.6f} ok_uc={ok['uc']:.6f}")
print(f"ok_sat={ok['sat_hits']} bad_offset_sat={bad_off['sat_hits']} bad_pp_sat={bad_p['sat_hits']}")
print("anti_windup=omitted")
print("pwm_rail_limit=omitted")  # V_LIM is soft ud/uq clamp only
print(f"omega_m_prescribed={OMEGA_M:.1f}")  # iq is torque proxy; does not drive mechanics
print(f"euler_dt={DT:.1e} L_over_R={L/R:.4e}")
print("plant_vs_controller=theta_e_star_not_fed_to_ctrl")

assert bad_off["ang_rmse"] > 10 * ok["ang_rmse"]
assert bad_p["ang_rmse"] > 10 * ok["ang_rmse"]
assert bad_off["plant_iq_rmse"] > 2 * ok["plant_iq_rmse"]
assert bad_p["plant_iq_rmse"] > 2 * ok["plant_iq_rmse"]
assert bad_off["plant_id_rmse"] > 2 * ok["plant_id_rmse"]
assert bad_p["plant_id_rmse"] > 2 * ok["plant_id_rmse"]
assert ok["sat_hits"] == 0 and bad_off["sat_hits"] == 0 and bad_p["sat_hits"] == 0
# Controller can still look OK under constant offset — do NOT require ctrl degrade
print("asserts_ok=true")
