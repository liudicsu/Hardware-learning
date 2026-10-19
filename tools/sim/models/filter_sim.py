"""filter_sim.py: gyro drift, accelerometer noise, and the complementary filter.

The board lies flat, is tilted to 30 degrees between t = 3 s and 4 s, held there,
and laid flat again between 7 s and 8 s. The gyro reads 1.5 deg/s too high (bias);
the accelerometer angle is noisy. Sample rate: 100 Hz.
"""
import math
import random

DT = 0.01
GYRO_BIAS = 1.5      # deg/s
GYRO_NOISE = 0.3     # deg/s, standard deviation
ACCEL_NOISE = 0.02   # g, standard deviation per axis


def true_pitch(t):
    if t < 3:
        return 0.0
    if t < 4:
        return 30.0 * (t - 3)
    if t < 7:
        return 30.0
    if t < 8:
        return 30.0 * (8 - t)
    return 0.0


def simulate(alpha, seconds=12.0, seed=7):
    rng = random.Random(seed)
    gyro_only = fused = 0.0
    rows = []
    for i in range(1, int(seconds / DT) + 1):
        t = i * DT
        rate = (true_pitch(t) - true_pitch(t - DT)) / DT
        gyro = rate + GYRO_BIAS + rng.gauss(0, GYRO_NOISE)
        th = math.radians(true_pitch(t))
        ax = math.sin(th) + rng.gauss(0, ACCEL_NOISE)
        az = math.cos(th) + rng.gauss(0, ACCEL_NOISE)
        accel = math.degrees(math.atan2(ax, az))
        gyro_only += gyro * DT
        fused = alpha * (fused + gyro * DT) + (1 - alpha) * accel
        rows.append((t, true_pitch(t), gyro_only, accel, fused))
    return rows


def summary(rows):
    """Error of the fused angle: mean and spread while flat (t > 10 s), and the worst error overall."""
    flat = [r[4] - r[1] for r in rows if r[0] > 10]
    mean = sum(flat) / len(flat)
    spread = math.sqrt(sum((e - mean) ** 2 for e in flat) / len(flat))
    worst = max(abs(r[4] - r[1]) for r in rows)
    return mean, spread, worst


if __name__ == "__main__":
    rows = simulate(alpha=0.98)
    print(" t_s  true  gyro_only  accel_only  fused")
    for t, true, g, a, f in rows:
        if abs(t - round(t)) < 1e-9 and round(t) in (1, 3, 4, 7, 8, 12):
            print(f"{t:4.0f} {true:5.1f} {g:10.1f} {a:11.1f} {f:6.1f}")
    print()
    print("alpha  offset_flat  noise_flat  worst_error")
    for alpha in (0.90, 0.98, 0.995):
        mean, spread, worst = summary(simulate(alpha))
        print(f"{alpha:<6} {mean:10.2f}  {spread:10.2f}  {worst:11.1f}")
