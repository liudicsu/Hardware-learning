# Month 5 current plan / 第5个月当前计划

Current / 当前：**M5 2310 min**, Batch-12 PR2. Older batch entries retain historical totals.

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
