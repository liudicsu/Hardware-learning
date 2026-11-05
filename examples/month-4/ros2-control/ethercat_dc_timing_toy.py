#!/usr/bin/env python3
"""ethercat_dc_timing_toy.py: FreeRun / SM-sync / DC SYNC0 timing (stdlib).

Three EtherCAT SubDevice sync modes (ETG.2200 Slave Implementation Guide;
ethercat.org Technology; acontis EC-Master DC chapter) on ONE shared plant
and ONE shared master-frame jitter draw:

  FreeRun     local timer — ignores master frame arrival
  SM_sync     application latches on Sync Manager event (frame arrival);
              tracks master jitter 1:1
  DC_SYNC0    latch/output aligned to a distributed-clock SYNC0 schedule
              after propagation-delay and drift compensation (ETG.8000 /
              acontis). Aligns SubDevice sample/output INSTANTS; it does
              NOT remove master-side frame jitter from the on-the-wire
              cycle. "<1 µs" / "≤1 µs" is the ETG claim 以文档为准 — not
              measured on this page.

Plant: single axis, position integrates commanded velocity. The controller
estimates velocity with the NOMINAL cycle Δt (not the true sample spacing),
which amplifies timing jitter into velocity noise.

Real EtherCAT master/slave / Beckhoff stack: 本页未运行. Not a CiA 402 redo.
usage: python3 ethercat_dc_timing_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 55
N_CYCLES = 400
DT_NOM = 0.001             # s, nominal cycle (1 kHz)
# Master frame arrival jitter (shared draw), seconds stddev.
FRAME_JITTER_STD = 40e-6   # 40 µs — large enough to see in velocity
# FreeRun local timer jitter (independent, usually smaller crystal error)
LOCAL_TIMER_STD = 5e-6
# DC residual after propagation-delay + drift compensation (toy floor).
# ETG claims synchronization "much better than 1 µs" / ethercat.org "≤ 1 µs"
# jitter — we use a 0.3 µs residual as a lesson-chosen stand-in and label it
# 以文档为准, NOT a measurement.
DC_RESIDUAL_STD = 0.3e-6
V_CMD = 1.0                # rad/s constant command


def shared_frame_jitter(rng: random.Random) -> list[float]:
    """Master frame arrival offsets relative to nominal tick k*DT_NOM."""
    return [rng.gauss(0.0, FRAME_JITTER_STD) for _ in range(N_CYCLES)]


def run_mode(mode: str, frame_jit: list[float], rng: random.Random) -> dict:
    """Integrate plant; return position RMSE-to-ideal and velocity noise."""
    pos = 0.0
    prev_pos = 0.0
    # Ideal position if every sample were exactly DT_NOM apart.
    ideal_pos = 0.0
    pos_errs: list[float] = []
    vel_ests: list[float] = []
    true_dts: list[float] = []
    prev_sample_t = 0.0

    for k in range(N_CYCLES):
        t_nom = k * DT_NOM
        if mode == "FreeRun":
            # Local timer: nominal grid + small local jitter. Ignores frame_jit.
            t_sample = t_nom + rng.gauss(0.0, LOCAL_TIMER_STD)
        elif mode == "SM_sync":
            # Latch on frame arrival.
            t_sample = t_nom + frame_jit[k]
        elif mode == "DC_SYNC0":
            # SYNC0 grid after delay/drift compensation: nominal + tiny residual.
            # frame_jit is deliberately NOT added — DC does not kill wire jitter,
            # but the application trigger is the SYNC0 edge, not the frame event.
            t_sample = t_nom + rng.gauss(0.0, DC_RESIDUAL_STD)
        else:
            raise ValueError(mode)

        if k == 0:
            dt_true = DT_NOM
        else:
            dt_true = t_sample - prev_sample_t
        prev_sample_t = t_sample
        true_dts.append(dt_true)

        # Plant integrates commanded velocity over the TRUE sample spacing.
        pos = pos + V_CMD * dt_true
        ideal_pos = ideal_pos + V_CMD * DT_NOM
        pos_errs.append(pos - ideal_pos)

        # Velocity estimate uses NOMINAL Δt — jitter becomes velocity noise.
        if k == 0:
            vel_est = V_CMD
        else:
            vel_est = (pos - prev_pos) / DT_NOM
        prev_pos = pos
        vel_ests.append(vel_est)

    # Skip first sample for velocity stats (undefined / seeded).
    vel_noise = [v - V_CMD for v in vel_ests[1:]]
    vel_rms = math.sqrt(sum(e * e for e in vel_noise) / len(vel_noise))
    pos_rmse = math.sqrt(sum(e * e for e in pos_errs) / len(pos_errs))
    dt_std = math.sqrt(
        sum((d - DT_NOM) ** 2 for d in true_dts[1:]) / (len(true_dts) - 1)
    )
    return {
        "mode": mode,
        "pos_rmse": pos_rmse,
        "vel_rms": vel_rms,
        "dt_std_s": dt_std,
        "final_pos": pos,
        "final_ideal": ideal_pos,
    }


def main() -> None:
    master = random.Random(SEED)
    frame_jit = shared_frame_jitter(master)
    # Per-mode local RNG for FreeRun / DC residuals (derived, reproducible).
    local_seeds = [master.randrange(1 << 30) for _ in range(3)]
    modes = ["FreeRun", "SM_sync", "DC_SYNC0"]
    print(f"seed={SEED}")
    print(f"DT_nom={DT_NOM} frame_jitter_std_s={FRAME_JITTER_STD} "
          f"dc_residual_std_s={DC_RESIDUAL_STD}")
    print("shared plant + shared master-frame jitter draw")
    print("DC compensates propagation delay + drift and aligns SYNC0 "
          "sample/output instants; it does NOT eliminate master frame jitter "
          "on the wire")
    print("ETG / ethercat.org sync jitter ≤1 µs 以文档为准 (not measured here)")
    print(f"{'mode':<10} {'pos_rmse':>12} {'vel_rms':>12} {'dt_std_s':>14}")
    results = []
    for mode, sd in zip(modes, local_seeds):
        r = run_mode(mode, frame_jit, random.Random(sd))
        results.append(r)
        print(
            f"{r['mode']:<10} {r['pos_rmse']:12.6e} {r['vel_rms']:12.6e} "
            f"{r['dt_std_s']:14.6e}"
        )
    by = {r["mode"]: r for r in results}
    # SM tracks frame jitter → largest vel noise; DC smallest dt_std;
    # FreeRun between (local timer, ignores frames).
    assert by["SM_sync"]["vel_rms"] > by["DC_SYNC0"]["vel_rms"]
    assert by["SM_sync"]["dt_std_s"] > by["DC_SYNC0"]["dt_std_s"]
    assert by["FreeRun"]["dt_std_s"] > by["DC_SYNC0"]["dt_std_s"]
    print(
        "ok: three modes on shared plant/jitter; nominal-Δt velocity amplifies "
        "jitter; DC ≠ removing master frame jitter; EtherCAT NIC 本页未运行"
    )


if __name__ == "__main__":
    main()
