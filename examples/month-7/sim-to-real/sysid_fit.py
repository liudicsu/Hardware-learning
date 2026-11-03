#!/usr/bin/env python3
"""Fit a 1st-order lag model to a synthetic joint step response (stdlib).

System identification (sysid) estimates real dynamics so the sim can be
calibrated before domain randomization. We synthesize:

    y[k+1] = y[k] + dt/tau * (u[k] - y[k]) + noise

then recover ``tau_hat`` by least-squares on the discrete update. Relative
error must stay under 5 % for the CI gate (proposal §2.4).
"""
from __future__ import annotations

import math
import random

SEED = 11
DT = 0.01
TRUE_TAU = 0.08  # seconds
NOISE_STD = 0.002
N_STEPS = 400
STEP_AMPLITUDE = 1.0


def simulate(tau: float, rng: random.Random) -> list[tuple[float, float, float]]:
    """Return list of (t, u, y)."""
    y = 0.0
    rows = []
    for k in range(N_STEPS):
        t = k * DT
        u = 0.0 if t < 0.2 else STEP_AMPLITUDE
        y = y + (DT / tau) * (u - y) + rng.gauss(0.0, NOISE_STD)
        rows.append((t, u, y))
    return rows


def fit_tau(rows: list[tuple[float, float, float]]) -> float:
    """LS fit of y_{k+1}-y_k = (dt/tau)(u_k - y_k) → beta=dt/tau."""
    # beta * x = dy  with x = (u - y)
    num = 0.0
    den = 0.0
    for i in range(len(rows) - 1):
        _, u, y = rows[i]
        _, _, y2 = rows[i + 1]
        x = u - y
        dy = y2 - y
        num += x * dy
        den += x * x
    beta = num / den
    if beta <= 1e-9:
        raise RuntimeError("degenerate fit")
    return DT / beta


def main() -> None:
    rng = random.Random(SEED)
    rows = simulate(TRUE_TAU, rng)
    tau_hat = fit_tau(rows)
    rel_err = abs(tau_hat - TRUE_TAU) / TRUE_TAU
    print("sysid_fit — 1st-order lag step response (seed=%d)" % SEED)
    print("dt=%.3f  true_tau=%.4f  noise_std=%.4f  n=%d" % (DT, TRUE_TAU, NOISE_STD, N_STEPS))
    print("tau_hat=%.6f  rel_err=%.4f (%.2f%%)" % (tau_hat, rel_err, 100 * rel_err))
    assert rel_err < 0.05, "sysid relative error %.4f exceeds 5%%" % rel_err
    print("ok: |tau_hat - true_tau|/true_tau < 5%")


if __name__ == "__main__":
    main()
