#!/usr/bin/env python3
"""Rectified parallel-pinhole stereo: shared depths and disparity errors.
f [pixels], B [m], sigma_d [pixels], Z [m]; d=f*B/Z. All values synthetic.
Uniform bounded errors have SD sigma_d. Antithetic +/- pairs ensure zero
sample-mean disparity error, isolating reciprocal-depth bias; pairs, not all
individual samples, are independent. The same errors feed EVERY baseline/depth.
Quantize disparity to q=1/8 px; q/sqrt(12) is only an approximate independent
quantization-error model, tested against actual rounding (not assumed exact).
Reject d<=0 or d>D_MAX, never clip to epsilon. Invalids count as tolerance misses.
Do not silently report a conditional mean as an unconditional depth result.
Bounded noise keeps the far positive-disparity experiment away from zero;
unbounded Gaussian reciprocal moments may be ill-behaved near that singularity.
Real rectification/matching 本页未运行. Not hand-eye, multi-view extrinsics or 3DGS.
"""
import math
import random
import statistics

SEED, N = 514, 20000
F_PX, SIGMA_D_PX, D_MAX_PX = 600., .25, 64.
BASELINES_M = (.06, .24)
DEPTHS_M = (.75, 2., 8., 60.)
Q_PX = .125


def reconstruct(d, fb):
    return None if not 0 < d <= D_MAX_PX else fb / d


def main():
    rng = random.Random(SEED)
    half_width = math.sqrt(3)*SIGMA_D_PX
    errors = tuple(e for _ in range(N//2) for x in [rng.uniform(-half_width, half_width)] for e in (x, -x))
    assert abs(sum(errors)) < 1e-12 and reconstruct(0., 36.) is None
    print(f"seed={SEED} N={N} (10000 antithetic pairs); f={F_PX} px sigma_d={SIGMA_D_PX} px q={Q_PX} px d_max={D_MAX_PX} px")
    print("same true depths and same disparity errors; bounded uniform noise, not Gaussian tail truncation")
    for b in BASELINES_M:
        print(f"B={b:.2f} m nominal_min_z=fB/d_max={F_PX*b/D_MAX_PX:.4f} m; occlusion/common-FOV cost not simulated")
    print("z_m B_m q_px d_true_px valid/N linear_sigma_m MC_sd_m MC_bias_m MC_RMSE_m within_10pct/N continuous_exact_bias_m")
    for z in DEPTHS_M:
        for b in BASELINES_M:
            fb, d0 = F_PX*b, F_PX*b/z
            exact_bias = fb/(2*half_width)*math.log((d0+half_width)/(d0-half_width))-z
            for q in (0., Q_PX):
                sigma_eff = math.hypot(SIGMA_D_PX, q/math.sqrt(12))
                linear = z*z/fb*sigma_eff
                values, hits = [], 0
                for e in errors:
                    d = d0+e
                    if q:
                        d = math.floor(d/q+.5)*q
                    value = reconstruct(d, fb)
                    if value is not None:
                        values.append(value)
                        hits += abs(value-z) <= .1*z
                prefix = f"{z:.2f} {b:.2f} {q:.3f} {d0:.3f} {len(values)}/{N} {linear:.6f}"
                if len(values) != N:
                    print(prefix + f" NA NA NA {hits}/{N} NA")
                    continue
                mean = statistics.fmean(values)
                sd = statistics.pstdev(values)
                rmse = math.sqrt(statistics.fmean((v-z)**2 for v in values))
                theory = f"{exact_bias:.6f}" if q == 0 else "NA"
                print(prefix + f" {sd:.6f} {mean-z:.6f} {rmse:.6f} {hits}/{N} {theory}")
    print("linear sigma is local; q/sqrt(12) approximation need not match rounding; E[fB/d] != z")
    print("long baseline costs minimum range and viewpoint occlusion; longer is NOT always better; hardware 本页未运行")


if __name__ == "__main__":
    main()
