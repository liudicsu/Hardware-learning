#!/usr/bin/env python3
"""Synthetic tactile calibration, not a magnetometer-to-Newton conversion.

Body x points right, y up on the skin, z inward. After a fictitious swap,
sensor a=-gy*load*y, b=gx*load*x, c=gz*load, plus rest bias and noise.
All conditions reuse the SAME recorded samples. Rest and known-location
probe records estimate bias and gains independently of evaluation contacts.
Load is dimensionless; positions and errors are in synthetic skin units.
The low-load gate is a first-contact teaching rule, NOT hardware safety.
"""
import math
import random
import statistics

SEED = 23
rng = random.Random(SEED)
BIAS = (0.14, -0.12, 0.12)
GAINS = (1.4, 0.7, 1.2)  # gx, gy, gz after synthetic skin swap
THRESHOLD, LOW_MAX = 0.06, 0.15  # dimensionless, NOT N


def measure(x, y, load):
    gx, gy, gz = GAINS
    signal = (-gy * load * y, gx * load * x, gz * load)
    return tuple(s + b + rng.uniform(-0.004, 0.004)
                 for s, b in zip(signal, BIAS))


rest = [measure(0, 0, 0) for _ in range(80)]
bias_hat = tuple(statistics.mean(row[j] for row in rest) for j in range(3))
# Independent calibration jig: known x=y=0.5, load=0.2 (synthetic only).
probes = [measure(0.5, 0.5, 0.2) for _ in range(80)]
a, b, c = (statistics.mean(row[j] for row in probes) - bias_hat[j]
           for j in range(3))
gains_hat = (b / 0.1, -a / 0.1, c / 0.2)

# Shared evaluation records: 30 rest, 30 gentle contact, 30 higher load.
truth, records = [], []
for i in range(90):
    x, y = 0.3 + 0.04 * math.sin(i), -0.2 + 0.03 * math.cos(i)
    load = 0 if i < 30 else (0.08 if i < 60 else 0.4)
    truth.append((x, y, load))
    records.append(measure(x, y, load))


def estimate(row, mode):
    a, b, c = row
    if mode != "raw":
        a, b, c = (v - offset for v, offset in zip(row, bias_hat))
    if mode in ("raw", "debiased"):
        return a / max(c, 1e-6), b / max(c, 1e-6), c
    gx, gy, gz = gains_hat if mode in ("recalibrated", "low_force_gated") else (1, 1, 1)
    load = c / gz
    return (b / gx / max(load, 1e-6), -a / gy / max(load, 1e-6), load)


print(f"seed={SEED}")
print("units=synthetic_skin_and_dimensionless_load_not_measured_Newtons")
print("noise=shared_records_all_conditions")
for mode in ("raw", "debiased", "sign_corrected", "recalibrated", "low_force_gated"):
    estimates = [estimate(row, mode) for row in records]
    # Same 60 real-contact records for localization: avoid selection bias.
    errors = [math.hypot(x - tx, y - ty)
              for (x, y, _), (tx, ty, load) in zip(estimates, truth) if load > 0]
    accepted = [i for i, (_, _, load) in enumerate(estimates)
                if load > THRESHOLD and (mode != "low_force_gated" or load <= LOW_MAX)]
    fp = sum(truth[i][2] == 0 for i in accepted)
    print(f"{mode}_localisation_mae={statistics.mean(errors):.4f}")
    print(f"{mode}_precontact_fp={fp}/30")
    if mode == "low_force_gated":
        print(f"gate_accepted={len(accepted)}/90")
        print(f"first_contact_index={accepted[0] if accepted else -1}")
        print("first_contact_action=stop_approach_then_verify")
print(f"contact_threshold={THRESHOLD:.2f}")
print(f"low_load_ceiling={LOW_MAX:.2f}")
