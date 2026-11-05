#!/usr/bin/env python3
"""soc_coulomb_thermal_toy.py: coulomb-counting SoC drift + thermal derate (stdlib).

Sign convention (stated, fixed for this toy):
  I > 0  discharge (SoC falls)
  I < 0  charge    (SoC rises)
Coulombic efficiency η applies ONLY on charge (I < 0). Discharge uses η = 1.
Integrator (discrete, Δt seconds):
  SoC_{k+1} = SoC_k - η_eff(I_k) * I_k * Δt / Q
  η_eff = η if I_k < 0 else 1.0

Four estimators share ONE current profile (same I[k] sequence):
  ideal          true I, true Q, true SoC0
  shunt_bias     I_meas = I + BIAS_A  (constant current-shunt offset)
  q_error        Q_hat = Q * Q_SCALE   (capacity mis-estimate)
  soc0_error     SoC_hat0 = SoC0 + SOC0_BIAS

Truth SoC uses ideal parameters. Drift from a constant shunt bias grows
~linearly in time under a non-zero mean current. Capacity and initial-SoC
errors are separate sources; OCV rest re-anchoring is named as a concept
only (no OCV curve is invented as a datasheet).

Thermal hygiene: lesson-defined continuous derate
  I_allow(T) = I_cont_nom * max(0, 1 - K_DERATE * max(0, T - T_REF))
A derate_flag rises when |I| would exceed I_allow at the current T proxy.
Not a fuel-gauge IC; not a BMS flash; no charging procedure taught.
Real LiPo / BMS / thermal chamber: 本页未运行.
usage: python3 soc_coulomb_thermal_toy.py
"""
from __future__ import annotations

SEED = 41
DT = 1.0                 # s
N = 600                  # 10 min profile
Q_AS = 3600.0            # 1 A·h in ampere-seconds
ETA_CHARGE = 0.98        # coulombic efficiency on charge only
SOC0 = 0.80
BIAS_A = 0.05            # shunt offset (A), discharge-positive convention
Q_SCALE = 0.92           # capacity underestimated by 8 %
SOC0_BIAS = -0.05        # started 5 points low
I_CONT_NOM = 2.5         # A continuous rating at T_REF (lesson-defined)
T_REF = 25.0             # °C
K_DERATE = 0.02          # per °C above T_REF (lesson-defined curve)
T_COOL = 0.01            # 1/s cool toward T_REF
T0 = 27.0                # start temperature proxy °C
T_RISE_PER_W = 0.004     # toy thermal rise vs |I|*V_nom proxy
V_NOM = 14.8             # V, example assumption only


def eta_eff(i: float) -> float:
    return ETA_CHARGE if i < 0.0 else 1.0


def current_profile() -> list[float]:
    """Shared profile: discharge, rest, charge, discharge. Fixed, not random."""
    i: list[float] = []
    # 0..199: discharge 1.5 A
    i += [1.5] * 200
    # 200..249: rest
    i += [0.0] * 50
    # 250..399: charge -1.0 A
    i += [-1.0] * 150
    # 400..599: discharge 2.2 A (will trip derate as T rises)
    i += [2.2] * 200
    assert len(i) == N
    return i


def integrate(i_seq: list[float], q: float, soc0: float) -> list[float]:
    soc = soc0
    out = [soc]
    for i in i_seq:
        soc = soc - eta_eff(i) * i * DT / q
        # clip only for display sanity; estimators do not "know" 0/1 walls
        # differently — clip after record so error stays visible
        out.append(max(0.0, min(1.0, soc)))
        soc = out[-1]
    return out  # length N+1


def thermal_series(i_seq: list[float]) -> tuple[list[float], list[bool]]:
    t = T0
    temps: list[float] = []
    flags: list[bool] = []
    for i in i_seq:
        # Lesson-defined proxy: heat ~ |I| * V_nom; cool toward T_REF.
        # Not a cell datasheet; numbers are lesson-chosen.
        t = t + T_RISE_PER_W * abs(i) * V_NOM * DT - T_COOL * (t - T_REF) * DT
        i_allow = I_CONT_NOM * max(0.0, 1.0 - K_DERATE * max(0.0, t - T_REF))
        temps.append(t)
        flags.append(abs(i) > i_allow + 1e-12)
    return temps, flags


def main() -> None:
    i_true = current_profile()
    soc_true = integrate(i_true, Q_AS, SOC0)

    i_bias = [i + BIAS_A for i in i_true]
    soc_bias = integrate(i_bias, Q_AS, SOC0)
    soc_q = integrate(i_true, Q_AS * Q_SCALE, SOC0)
    soc_s0 = integrate(i_true, Q_AS, SOC0 + SOC0_BIAS)

    temps, derate = thermal_series(i_true)

    def err(est: list[float]) -> list[float]:
        return [a - b for a, b in zip(est, soc_true)]

    e_bias, e_q, e_s0 = err(soc_bias), err(soc_q), err(soc_s0)

    # Report at a few anchors + end
    anchors = [0, 200, 250, 400, N]
    print(f"seed={SEED}")
    print("sign: I>0 discharge, I<0 charge; eta applies only on charge")
    print(f"eta_charge={ETA_CHARGE} Q_As={Q_AS:.1f} SoC0={SOC0:.2f} dt={DT}")
    print(f"shunt_bias_A={BIAS_A} Q_scale={Q_SCALE} SoC0_bias={SOC0_BIAS}")
    print("same current profile for all arms")
    print("t_s  SoC_true  err_shunt  err_Q  err_SoC0  T_C  derate")
    for t in anchors:
        print(
            f"{t:4d}  {soc_true[t]:8.4f}  {e_bias[t]:+8.4f}  {e_q[t]:+7.4f}  "
            f"{e_s0[t]:+8.4f}  {temps[t-1] if t else T0:5.2f}  "
            f"{int(derate[t-1]) if t else 0}"
        )

    # Linear-growth check for shunt bias over the first discharge block (mean I > 0)
    # Expected rough slope ≈ -BIAS_A / Q  (SoC/s) under discharge with eta=1
    slope_est = (e_bias[200] - e_bias[0]) / 200.0
    slope_theory = -BIAS_A / Q_AS
    print(f"shunt_err_slope_per_s={slope_est:+.6e}  theory_neg_bias_over_Q={slope_theory:+.6e}")
    print(f"final_err_shunt={e_bias[N]:+.4f} final_err_Q={e_q[N]:+.4f} final_err_SoC0={e_s0[N]:+.4f}")
    print(f"derate_ticks={sum(derate)}/{N}  T_final_C={temps[-1]:.2f}")
    print("OCV rest re-anchor: concept only (no OCV curve / datasheet invented here)")
    print("not a fuel-gauge IC; no charging procedure; LiPo/BMS/thermal chamber 本页未运行")
    # Assertions for CI-style honesty
    assert abs(slope_est - slope_theory) < 5e-7, (slope_est, slope_theory)
    assert abs(e_s0[0] - SOC0_BIAS) < 1e-12
    assert e_q[0] == 0.0
    assert sum(derate) > 0
    print("ok: shared profile; shunt drift ~linear; Q and SoC0 errors separated; derate fires")


if __name__ == "__main__":
    main()
