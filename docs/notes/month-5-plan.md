# Month 5 current plan / 第5个月当前计划

Current / 当前：**M5 3210 min**, Batch-17 PR2. Older batch entries retain historical totals.

## Batch-17 PR2 — S-curve on moveit-pick-place and computed torque on control-modelling (+360)

Base `d6e1f35` (batch-17 PR1 merged as #169; site **33930**). PR2 is M5 only: **M5 2850→3210 (+360)**. Site **33930→34290**, still 71 lessons.

- **H3 / moveit-pick-place: 300→**480** (+180).** Seven-segment jerk-limited S-curve vs trapezoid. Toy `scurve_jerk_limit_toy.py`: shared VMAX 0.5 m/s, AMAX 2 m/s²; A trapezoid / B S-curve JMAX 8 m/s³ / C JMAX 2 m/s³; spring-damper plant (ζ 0.05, f per seed, common random numbers, 5 seeds), semi-implicit Euler DT 0.5 ms, stable step H* = 2(√(1+ζ²) − ζ)/ω = 6.0558 ms at 50 Hz, checked at 0.98× / 1.02× and half step. flexible: B−A residual −1.5305±0.1620 mm and cycle −1.3455±0.2599 s, clear, 5/5; B−A profile +0.2500 s. rigid_short (declared lose): B−A profile +0.2309 s and cycle +0.2310 s, clear, 5/5. C misses the window in both. ≠ MoveIt scaling; ≠ Pilz / OMPL. Real arm 本页未运行.
- **H4 / control-modelling: 600→**780** (+180).** Computed torque vs PD + gravity. Toy `computed_torque_inverse_dynamics_toy.py`: planar 2R, point masses, unmodelled friction 0.3 N m, held noise; KP 400, KD 40; semi-implicit Euler DT 1 ms, H* = 41.4214 ms for the matched error dynamics, checked at 0.98× / 1.02× and half step. fast_coupled: B−A rms −100.9081±33.6992 mrad, clear, 5/5; slow_quasi_static: declared near-tie did not hold, B−A +16.7587±13.6344, clear, 5/5 (friction; FC = 0 side run −0.1168±0.0515); payload_mismatch (declared lose): C−A +133.6632±28.8934, clear, 5/5. ≠ LQR / MPC; ≠ Smith; ≠ 2-DOF. Real arm 本页未运行.

**Allocation / 安排:** 2 × (30+30+40+40+40) = 360 minutes.

**Site accounting / 全站核算:** **34290=33930+360**; **M5=3210**, **71 lessons**.

## Batch-16 PR2 — product of exponentials on kinematics-ik (+180)

Base `208706f` (batch-16 PR1 merged as #165; site **32820**). PR2 on M5 host: **M5 2670→2850 (+180)**; M7 moves in the same PR on its own plan. Site **32820→33180**, still 71 lessons.

**H / 5.x kinematics-ik:** `kinematics-ik` 570→**750**. Toy `poe_vs_dh_fk_toy.py`: the lesson's three-joint SO-101 model written as standard DH rows (q0, H, 0, +90°), (q1, 0, L1, 0), (q2, 0, L2, 0) plus a fixed Rx(−90°) tool rotation (A), as a space-frame product of exponentials with twists ξ = (ω, −ω × q) and home pose M (B), and as PoE with the elbow axis tilted 2° about x (C, a wrong twist); truth is the lesson's closed form; 200 shared configurations per seed (common random numbers, 5 seeds). No integration step; correctness criterion: max ||T_DH − T_PoE||_F and ||RᵀR − I||_F below 1e-12 asserted on noise-free regimes. matched / near_singular / encoder_noise: B−A **numerically zero** in every regime (floating-point residue, not a bit tie); C−B tip error 3.3504±0.1425 / 0.0397±0.0020 / 2.6701±0.0984 mm, clear, 5/5. Real-arm FK check 本页未运行.

**Allocation / 安排:** 30+40+40+40+30=180 minutes.

**Site accounting / 全站核算:** **33180=32820+360** with M7 +180 on month-7-plan.md; **M5=2850**, **71 lessons**.

## Batch-14 PR2 / 本月 H4 (+180)

Base `4b996f7` (batch-14 PR1 merged as #157; site **30600**). PR2 on M5 host: **M5 2490→2670 (+180)**; M4 moves in the same PR on its own plan. Site **30600→30960**, still 71 lessons.

- **H4 / 5.1 control-modelling: 420→600 (+180).** Smith predictor `C̄ = C / (1 + C G (1 − z^−k))`. Toy `smith_predictor_delay_toy.py`: first-order plant with a pure input delay, explicit Euler `H = 1 ms` with `H < 2τ` asserted (2τ_min 0.8233 s); arms A PI ignoring the delay / B Smith with the true model / C Smith with a wrong delay and gain model; shared plant, reference, load, noise and C's model errors (common random numbers, 5 seeds). zero_delay: all **tie** (identical on every seed); long_delay: A−B overshoot 87.3189±0.1214, clear, 5/5; C−B settle 0.6180±0.2675 clear but ISE / overshoot near-tie; short_delay: the plain PI wins (A−B settle −0.1920±0.0045, clear, 5/5); wrong_delay_big: C−B loses on every metric, clear, 5/5. Added a whole-lesson final Summary in en/zh (the host had none). ≠ lead–lag; ≠ discrete LQR; ≠ anti-windup. Real delayed plant 本页未运行.

**Allocation / 安排:** 30+30+40+40+40=180 minutes.

**Site accounting / 全站核算:** **30960=30600+360** with M4 +180 on month-4-plan.md; **M5=2670**, **71 lessons**.

## Batch-13 PR2 / 本月 H3 (+180)

Base `a95f352` (batch-13 PR1 merged; site **29490**). PR2 on M5 host: **M5 2310→2490 (+180)**; M7 moves in the same PR on its own plan. Site **29490→29850**, still 71 lessons.

- **H3 / camera-calibration: 420→600 (+180).** Essential matrix `E = [t]× R`, `(y′)ᵀ E y = 0`, eight-point rows, null vector by one-sided Jacobi SVD (no `YᵀY`), internal constraint `(s, s, 0)`, four-solution pose recovery with a cheirality vote; Hartley normalisation (centroid, mean distance √2). Toy `eight_point_essential_toy.py`: shared pose, 40 points, 40 held-out points and pixel noise (common random numbers, 5 seeds); arms raw pixels → F → E / Hartley pixels / calibrated `K⁻¹` coordinates. noise_free: all arms at round-off, B−A `t_deg` **tie: identical on every seed**, `e_err` and `epi_px` (B−A and C−B) **numerically zero (floating-point residue), effectively a tie** (|m|, sd < 1e-9); pixel_noise: B−A `e_err` −0.0683±0.0510 and `t_deg` −3.8675±2.8843 clear 5/5, `epi_px` near-tie; clustered (900, 500) ± 100 px: log10(s₁/s₈) 6.54 vs 1.17, B−A `epi_px` −204.7447±197.8867 clear 5/5; every noisy C−B line a near-tie; tiny_baseline 1 cm: every arm loses the translation direction (64–90°) while `epi_px` stays ≈ 1 px (metric blind to t). ≠ stereo depth σ rewrite; ≠ IBVS; ≠ PCA normals. Real camera / OpenCV 本页未运行.

**Allocation / 安排:** 30+40+40+40+30=180 minutes.

**Site accounting / 全站核算:** **29850=29490+360** with M7 +180 on month-7-plan.md; **M5=2490**, **71 lessons**.

## Batch-12 PR2 / 本月 H3 (+180)

Base `ad9407a` (batch-12 PR1 merged; site **28380**). PR2 on M5 host: **M5 2130→2310 (+180)**; M7 moves in the same PR on its own plan. Site **28380→28740**, still 71 lessons.

- **H3 / kinematics-ik: 390→570 (+180).** Yoshikawa manipulability `w = √det(J Jᵀ) = σ1 σ2 = L1 L2 |sin q2|` and condition number `κ = σ1/σ2` (= Modern Robotics µ1; κ² = µ2) on a planar 2R stand-in with the lesson's link lengths. Toy `manipulability_yoshikawa_toy.py`: shared heading, actuator-rate noise and tip-measurement noise (common random numbers, 5 seeds); arms ignore-w (exact inverse) / keep-w (reach capped where w = 0.3·L1L2) / DLS λ = 0.01 m; resolved-rate explicit Euler with KP·DT = 0.1 < 2. far_from_singularity: A and B **tie, identical on every seed** (monitor never fires); C−A final error a near-tie / small gap within seed noise, RMS and hold rate small but consistent gaps. near_singularity: keep-w loses on tracking (final 2.393±0.032 mm vs 0.029±0.014 mm) but keeps the largest w and calmest hold. ≠ DLS redo; ≠ quaternion chart. Real SO-101 / MoveIt 本页未运行.

**Allocation / 安排:** 30+40+40+40+30=180 minutes.

**Site accounting / 全站核算:** **28740=28380+360** with M7 +180 on month-7-plan.md; **M5=2310**, **71 lessons**.

## Batch-11 PR2 — discrete LQR / ZOH on state-space-lqr (+180)

Base `014a8ba` (site **27270**). PR2 on M5 host: **M5 1950→2130 (+180)**; M3 +180 on month-3-plan. Site **27270→27630**, still 71 lessons.

**Host / 宿主:** `state-space-lqr` 420→**600**. Toy `discrete_lqr_zoh_toy.py`: shared plant/Q/R/noise CRN; cont+ZOH vs discrete at coarse/fine Ts; ZOH via expm; DARE tol explicit; |λ|<1; fine-Ts near-tie; ≠ Bode redo.

**Allocation / 安排:** 30+30+45+45+30=180 minutes.

**Site accounting / 全站核算:** **27630=27270+360**; **M5=2130**, **71 lessons**.


Batch-5 PR2 base e5ac703 (20310). Historical observability additions remain in month-5-followup-pr3.md.

| Host | Before | After PR2 | Addition |
|---|---:|---:|---|
| 5.4 camera-calibration | 240 | 420 | stereo_depth_sigma_toy (+180) |
| M5 total,5 lessons | 1620 | 1800 | Other lessons unchanged / 其他课不变 |

f pixels,B metres,sigma_d pixels;shared depths/disparity noise;MC sigma/bias vs linearization,quantization and exact bounded-noise expectation. Long baseline min-range/occlusion cost;not hand-eye,multi-view extrinsics or3DGS. / 单位一致，共享输入，对照 MC 与线性化，解释量化、非线性偏差和长基线代价，不重做手眼。

All new sections/code/stdout/exercises before final Summary. Existing5.4 had no Summary in either language;add final bilingual Summary with legacy intrinsics/undistortion reminder plus new stereo sentence. Real rectification/matching 本页未运行.

This PR:20310+180+210=**20700**,71 lessons,M5=1800,M9=2550;M1/M2/M3 remain870/1650/1470. / 不提前计入本批 PR3。

## Batch-7 PR2 / 本月 H4 (+150)

5.3 kinematics-ik240→390; M5 **1800→1950**, five lessons. This PR only: site **22830→23190**, M4 **1620→1830** (+210), still71 lessons. No arithmetic mismatch or PR3 allocation.

Allocation:30+30+45+30+15=150 min (explicit ZYX/body Jacobian / gimbal rank and shared crossing / equal-endpoint interpolation / double-cover+norm / exercises). Existing SO-101 planar FK sign, position Jacobian, damped IK and checks remain unchanged. Added full final whole-lesson Summary in both languages because neither had one; all new code/stdout/exercises before it. New stdlib expected/harness entry; no robot/IMU/ROS run. Sources: batch-7-pr2-sources.md.
