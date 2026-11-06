#!/usr/bin/env python3
"""Synthetic DMM spec limits -> Type-B standard uncertainty -> I=V/R.
No real meter datasheet opened: ALL specs below are synthetic, not Fluke claims.
A total spec half-width L = a*abs(reading) + f*full_scale is a LIMIT, not sigma.
Model each channel's total error as independent uniform[-L,L], so u=L/sqrt(3).
Do NOT RSS the two terms inside one manufacturer's total limit.
Propagate independent V,R with cV=1/R, cR=-V/R^2. RSS combines STANDARD
uncertainties; linear sum combines LIMITS. Neither is automatically 95 %.
Monte Carlo uses shared standardized errors for both spec arms, 20000 draws
per operating point; independent V vs R draws. No repeated-reading 1/sqrt(n)
claim for a systematic instrument offset. No CAT/IEC certification or live test.
"""
import math
import random

SEED = 113
DRAWS = 20000
# a reading fraction, f full-scale fraction, full scale [V or ohm]. Synthetic!
V_SPEC = (0.005, 0.001, 6.0)
R_SPEC = (0.008, 0.002, 2000.0)
POINTS = ((0.2, 1000.0), (5.0, 1000.0))


def limit(reading, spec, full_spec):
    a, f, fs = spec
    return a * abs(reading) + (f * fs if full_spec else 0.0)


def budget(v, r, lv, lr):
    uv, ur = lv / math.sqrt(3), lr / math.sqrt(3)
    cv, cr = 1 / r, -v / r**2
    rss = math.hypot(cv * uv, cr * ur)
    worst_linear = abs(cv) * lv + abs(cr) * lr
    # Exact ratio extrema for a positive denominator, not just linearization.
    exact = max(abs((v + lv) / (r - lr) - v / r),
                abs((v - lv) / (r + lr) - v / r))
    return uv, ur, cv, cr, rss, worst_linear, exact


def main():
    rng = random.Random(SEED)
    draws = tuple((rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(DRAWS))
    print(f"SYNTHETIC specs; seed={SEED} draws={DRAWS}; limits / sqrt(3) -> standard u")
    print("V: +/- (0.5 % reading + 0.1 % of 6 V FS); R: +/- (0.8 % reading + 0.2 % of 2000 ohm FS)")
    print("V_V arm L_V_V L_R_ohm u_V_V u_R_ohm cV_A/V cR_A/ohm RSS_uI_mA linear_limit_mA exact_limit_mA MC_sd_mA")
    for v, r in POINTS:
        for name, full in (("reading_only", False), ("reading_plus_FS", True)):
            lv, lr = limit(v, V_SPEC, full), limit(r, R_SPEC, full)
            uv, ur, cv, cr, rss, worst, exact = budget(v, r, lv, lr)
            values = [(v + dv * lv) / (r + dr * lr) for dv, dr in draws]
            mean = sum(values) / DRAWS
            sd = math.sqrt(sum((x - mean)**2 for x in values) / DRAWS)
            print(f"{v:.1f} {name} {lv:.6f} {lr:.3f} {uv:.6f} {ur:.6f} "
                  f"{cv:.6f} {cr:.9f} {rss*1000:.6f} {worst*1000:.6f} "
                  f"{exact*1000:.6f} {sd*1000:.6f}")
            assert lr < r and 0 < rss < worst <= exact
            assert abs(sd / rss - 1) < 0.03
    print("RSS is standard uncertainty, linear sum is a worst-case first-order limit; independence assumed")
    print("shared true V,R and standardized errors; physical DMM/calibration 本页未运行; not certification")


if __name__ == "__main__":
    main()
