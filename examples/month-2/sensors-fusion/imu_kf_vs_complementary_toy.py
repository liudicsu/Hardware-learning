#!/usr/bin/env python3
"""Shared tilt-only sensor stream; no filter receives true gyro bias.
Units: angle deg, rate deg/s, time s. Synthetic gravity-only accelerometer
angle (no translational acceleration), white gyro/accel noise, bias random walk.
During each sample gyro = finite-difference true rate + previous bias + noise;
bias then takes an independent random-walk increment. Model for x=[angle,bias]:
F=[[1,-dt],[0,1]], control=[dt*gyro,0], H=[1,0].
Q0=diag((sigma_g*dt)^2, sigma_rw^2*dt), R0=sigma_a^2.
P0=diag(R0,sigma_b0^2); bias prior MEAN=0, not the sampled true bias.
KF tests 3x3 scale factors of the declared Q0,R0. Plain complementary tests
9 alphas. Bias-adaptive complementary tests 3x3 alpha,bias-gain settings.
Each gets 9 candidates x 3 tuning seeds x 1500 updates=40500 updates, same
squared-error objective. Tuning truth is training-only supervision; held-out
truth scores frozen filters. Model knowledge is shared, not oracle bias.
Model capacity differs: plain complementary has no bias state; adaptive/KF do.
This is not an EKF INS, Allan-variance characterization or MPU6050 measurement.
"""
import itertools
import math
import random
import statistics

DT, N = 0.02, 1500
SIGMA_G, SIGMA_A = 0.5, 1.5
SIGMA_B0, SIGMA_RW = 0.5, 0.03
TUNE = (201, 202, 203)
EVAL = (221, 222, 223, 224, 225)
GRIDS = {
    "complementary": tuple((a, 0.) for a in (.5, .65, .8, .9, .95, .97, .985, .995, .999)),
    "bias_complementary": tuple(itertools.product((.9, .97, .995), (.01, .05, .2))),
    "KF": tuple(itertools.product((.5, 1., 2.), repeat=2)),
}


def angle(t):
    return 12 * math.sin(2 * math.pi * t / 6) + 3 * math.sin(2 * math.pi * t / 2)


def sensors(seed):
    rng = random.Random(seed)
    bias = rng.gauss(0, SIGMA_B0)
    truth = tuple(angle(k * DT) for k in range(N + 1))
    accel = [truth[0] + rng.gauss(0, SIGMA_A)]
    gyro = []
    for prev, now in zip(truth, truth[1:]):
        gyro.append((now - prev) / DT + bias + rng.gauss(0, SIGMA_G))
        bias += rng.gauss(0, SIGMA_RW * math.sqrt(DT))
        accel.append(now + rng.gauss(0, SIGMA_A))
    return tuple(gyro), tuple(accel), truth


def estimate(kind, config, gyro, accel):
    # No truth or true-bias argument; all arms initialize from the same z0.
    a, bhat = accel[0], 0.
    out = [a]
    p00, p01, p11 = SIGMA_A**2, 0., SIGMA_B0**2
    for g, z in zip(gyro, accel[1:]):
        pred = a + DT * (g - bhat)
        innovation = z - pred
        if kind == "gyro":
            a = pred
        elif kind == "accel":
            a = z
        elif kind in ("complementary", "bias_complementary"):
            alpha, kb = config
            a = pred + (1 - alpha) * innovation
            bhat -= kb * DT * innovation
        else:
            qscale, rscale = config
            qtheta = qscale * (SIGMA_G * DT)**2
            qbias = qscale * SIGMA_RW**2 * DT
            r = rscale * SIGMA_A**2
            pp00 = p00 - 2 * DT * p01 + DT**2 * p11 + qtheta
            pp01 = p01 - DT * p11
            pp11 = p11 + qbias
            k0, k1 = pp00 / (pp00 + r), pp01 / (pp00 + r)
            a, bhat = pred + k0 * innovation, bhat + k1 * innovation
            p00, p01, p11 = (1-k0)*pp00, (1-k0)*pp01, pp11-k1*pp01
            assert p00 >= 0 and p11 >= 0 and p00*p11-p01*p01 > -1e-12
        out.append(a)
    return out


def mse(estimate_values, truth):
    return statistics.fmean((a-b)**2 for a, b in zip(estimate_values, truth))


def main():
    assert set(TUNE).isdisjoint(EVAL) and all(len(g) == 9 for g in GRIDS.values())
    tuning = [sensors(s) for s in TUNE]
    chosen = {}
    for kind, grid in GRIDS.items():
        chosen[kind] = min(grid, key=lambda cfg: statistics.fmean(
            mse(estimate(kind, cfg, g, z), truth) for g, z, truth in tuning))
    print(f"dt={DT} N={N}; sigma_g={SIGMA_G} deg/s sigma_a={SIGMA_A} deg sigma_b0={SIGMA_B0} deg/s sigma_rw={SIGMA_RW} deg/s/sqrt(s)")
    print(f"Q0_diag={(SIGMA_G*DT)**2:.6f},{SIGMA_RW**2*DT:.6f}; R0={SIGMA_A**2:.6f}; bias_prior_mean=0 (not truth)")
    print("tune_seeds=201,202,203; held_out=221..225; 9 candidates x 3 x 1500 = 40500 updates/filter")
    for kind, cfg in chosen.items():
        print(f"selected {kind} {cfg}")
    arms = ("gyro", "accel", "complementary", "bias_complementary", "KF")
    scores = {a: [] for a in arms}
    print("held_out_seed gyro_RMSE_deg accel_RMSE_deg complementary_RMSE_deg bias_complementary_RMSE_deg KF_RMSE_deg")
    for seed in EVAL:
        g, z, truth = sensors(seed)
        row = [math.sqrt(mse(estimate(a, chosen.get(a), g, z), truth)) for a in arms]
        for a, value in zip(arms, row):
            scores[a].append(value)
        print(str(seed) + " " + " ".join(f"{v:.6f}" for v in row))
    print("arm mean_RMSE_deg population_sd min max")
    for a, values in scores.items():
        print(f"{a} {statistics.fmean(values):.6f} {statistics.pstdev(values):.6f} {min(values):.6f} {max(values):.6f}")
    print("shared data/prior model; neither filter knows true bias; no universal winner; IMU hardware 本页未运行")


if __name__ == "__main__":
    main()
