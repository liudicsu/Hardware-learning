# Month 4 plan / 第4个月计划

Current / 当前：**M4 3390 min**, Batch-21 PR2. Earlier entries below retain their historical totals.

## Batch-21 PR2 / 本月 H3 (+180)

Base `33a4a703eced7372f71e0decc6b733655ee1cbb4` (batch-21 PR1 #185 merged; site **38340**). PR2 on M4 host: **M4 3210→3390 (+180)**; M2 moves in the same PR on its own plan. Site **38340→38700** (38700=38340+180+180), still 71 lessons.

- **H3 / 4.3 urdf-tf: 420→600 (+180).** Parallel-axis inertia and the URDF inertial origin (`urdf_parallel_axis_inertia_toy.py`; common random numbers, 5 seeds; one shared chassis mass and size draw per regime and seed). Wikipedia Parallel axis theorem body read (rev 1337841361; 以原文为准): I = I_cm + m d², tensor form J = I + m[(R·R)E₃ − R⊗R]. The ROS wiki URDF link page was a bot wall and is not cited. Arms A origin at the COM / B the same matrix at the joint (typo) / C the matrix moved to the joint. zero: every pair **tie** (identical). small (1 cm): B−A J_zz `-2.009e-4±2.789e-6`, **small but consistent**, 5/5 — the declared "may near-tie" did **not** happen. large (rear-edge joint, 0.15 m): B−A J_zz `-0.0448±4.431e-4`, **clear**, 5/5; B−A alpha_z `1.3520±0.0164`, clear, 5/5; C−A J_zz **tie**; C−A tau_g `-2.9280±0.0290`, **clear**, 5/5 (kept: C puts the mass at the joint). along_axis: B−A J_zz **tie**, B−A J_xx `-0.0032±6.824e-5`, clear. diagonal: B−A J_xy `0.0160±1.924e-4`, clear; C−A tau_g `-1.9610±0.0236`, clear. Alternatives d = 0.10 / 0.20 / 0.005 m printed; none replaced the defaults. No code change after the first run. Gazebo 本页未运行.

**Allocation / 安排:** 30+30+50+40+30=180 minutes.

## Batch-20 PR1 / 本月 H2 (+180)

Base `73b59b39de82a388c0a89514269680b5c04048f9` (batch-19 polish #180 merged; site **36900**). PR1 on M4 host: **M4 3030→3210 (+180)**; M3 moves in the same PR on its own plan. Site **36900→37230** (37230=36900+150+180), still 71 lessons.

- **H2 / 4.4 gazebo-sim: 450→630 (+180).** Lidar realism vs ideal rays (`gazebo_lidar_realism_toy.py`; common random numbers across arms, real-unit stand-in R on its own stream, 5 seeds). SDFormat 1.11 lidar.sdf / noise.sdf source and gz-sensors 8 Lidar.cc bodies read (以文档为准): per-beam Gaussian noise only; finite ranges clamped to [min, max]. MIN=0.20 m, MAX=8.0 m, SIGMA=0.01 m from this lesson's xacro; C_BIAS=0.015 m, P_DROP_C=0.50, R_BIAS=0.020 m, R_SIGMA=0.012 m, P_DROP_R=0.60, TOL=0.10 m declared toy parameters. clear_wall: paired B−A mean_err `0.0011±0.0013`, **near-tie** as declared; paired C−A mean_err `0.0161±0.0013`, **clear**, 5/5 (C's bias vs geometry, **kept**). glossy: paired A−C ret_err `0.2689±0.0563`, **clear**, 5/5, **kept**; beam-level paired A−C mismatch `3.6000±2.7928`, small but consistent (not declared a C win). min_range: paired A−C mismatch `19.0000±0.0000`, near_err `1.5834±0.0089`, **clear**, 5/5, **kept**. visual_only: paired A−C mismatch `27.0000±0.0000`, **clear**, 5/5, **kept**. Alternatives on the same seeds: TOL=0.05 m (clear_wall A−C mismatch `0.4000±0.5477`), P_DROP_C=0.90 (glossy A−C ret_err `0.2492±0.1052`), C_BIAS=0.000 (clear_wall C−A mean_err `0.0011±0.0013`). ≠ OctoMap/TSDF; ≠ DWA; ≠ physics-step section. Real lidar / Gazebo 本页未运行. / 雷达真实感：光亮、盲区、visual/collision 不一致时理想射线输。

**Allocation / 安排:** 30+30+50+40+30=180 minutes.

## Batch-18 PR2 / 本月 H3 (+180)

Base `26d4664edc52abc3a0c35b8c960ddc29d35b5057` (batch-18 PR1 merged as #173; site **35040**). PR2 on M4 host: **M4 2850→3030 (+180)**; M7 moves in the same PR on its own plan. Site **35040→35400**, still 71 lessons.

- **H3 / 4.6 slam-nav: 630→810 (+180).** OctoMap-style octree occupancy and TSDF fusion vs a 2-D floor grid. Toy `octomap_tsdf_volume_toy.py`: shared multi-view range of a hanging box (stdlib octree / TSDF stand-in, not liboctomap or Open3D); arms A 2-D floor projection / B octree log-odds (hit at the endpoint, miss along the ray, unknown otherwise) / C TSDF weighted average / S single-frame hit occupancy / C_bad TSDF with one mis-registered frame. Common random numbers, 5 seeds. overhang_multiview: B−A and C−A overhang recall **clear** (B 0.9861 on every seed, C 0.9833±0.0062 vs A 0.0000±0.0000). single_frame_clean: declared B vs S occupied-IoU **near-tie did not hold** — paired B−S 0.0316±0.0000, **small but consistent**, 5/5 (kept). noisy_multiview: C surface MAE 0.0631±0.0018 m vs raw 0.0953±0.0015 m, paired C−raw −0.0322±0.0024 **clear**, 5/5. bad_pose: C_bad−C 0.0026±0.0004 **small but consistent**, 5/5 (kept). `sdf_trunc=0.25` chosen after the first run; 0.50 printed as the alternative (at 0.50 C did not beat raw: +0.0131±0.0034, kept). Unknown voxels have seen neither a hit nor a clearing ray (count 0.0000±0.0000). ≠ PGM / DWA / depth-lesson voxels. Hornung AURO PDF HTTP 500, not cited. Real lidar / Open3D / octomap_server 本页未运行.

**Allocation / 安排:** 30+30+40+50+30=180 minutes.

**Site accounting / 全站核算:** **35400=35040+360** with M7 +180 on month-7-plan.md; **M4=3030**, **71 lessons**.

## Batch-17 PR1 / 本月 H2 (+180)

Base `2df7604` (batch-16 closed incl. polish #168; site **33600**). PR1 on M4 host: **M4 2670→2850 (+180)**; M3 moves in the same PR on its own plan. Site **33600→33930**, still 71 lessons.

- **H2 / 4.2 ros2-graph: 390→570 (+180).** QoS Deadline and Lifespan vs reliability only. ROS 2 Jazzy "Quality of Service settings" (HTML body read; 以原文为准; existing `ros2-qos` card extended). Toy `qos_deadline_lifespan_toy.py`: discrete-event stand-in (integer microseconds, no integration step), 10 ms period, controller ticks with a per-seed phase; arms A reliability only / B deadline 20 ms + lifespan 10 ms / C deadline 5 ms (offered = requested); shared publications, stalls, delays, losses (common random numbers, 5 seeds). late_sensor B−A stale −6.6633±1.6806 clear 5/5 (hold +6.9535±1.8594); on_time B−A stale / hold / age tie; lossy_reliable B−A hold +2.7814±0.3652 clear 5/5 (B loses), stale −1.0705±0.1824 clear (declared tie did not hold; printed as is). Not the reliability mismatch; not bag QoS; not FreeRTOS deadlines. Real ros2: 本页未运行.

**Allocation / 安排:** 30+30+40+50+30=180 minutes.

**Site accounting / 全站核算:** **33930=33600+330** with M3 +150 on month-3-plan.md; **M4=2850**, **71 lessons**.

## Batch-15 PR2 / 本月 H3 (+180)

Base `d0da082` (batch-15 PR1 merged as #161; site **31710**). PR2 on M4 host: **M4 2490→2670 (+180)**; M7 moves in the same PR on its own plan. Site **31710→32070**, still 71 lessons.

- **H3 / 4.6 slam-nav: 450→630 (+180).** Regulated Pure Pursuit vs the Dynamic Window Approach. Toy `dwa_vs_pure_pursuit_toy.py`: unicycle with acceleration limits, exact circular-arc steps H = 0.05 s inside a 0.25 s control period (H vs H/2 printed); arms A RPP-style tracker / B DWA with Fox eq. 14 / C window without admissibility / D DWA counting the held period (added after the first run, disclosed); shared obstacles, path and slip (common random numbers, 5 seeds × 6 trials). Admissibility checked at 0.98× / 1.02×. empty, open_slow: all **tie** (identical on every seed); clutter_slow: RPP blocked, B−A success 0.9000±0.0913 clear 5/5, RPP keeps more clearance; clutter_fast: B−A collision −0.6667±0.2041 clear 5/5, C−B 0.1333±0.1394 **near-tie** (§9 expected B safer than C: not met); narrow_gap: B−A time −1.0333±0.1896 small but consistent; winding (added after the first run, first geometry printed): RPP arrives on every trial, B and C collide 30/30, D 0.5000±0.2041 success with 0 collisions. PAD 0.05 m chosen after the first run (0.0 and 0.1 printed). Real Nav2 / DWB 本页未运行.

**Allocation / 安排:** 30+30+40+50+30=180 minutes.

**Site accounting / 全站核算:** **32070=31710+360** with M7 +180 on month-7-plan.md; **M4=2670**, **71 lessons**.

## Batch-14 PR2 / 本月 H3 (+180)

Base `4b996f7` (batch-14 PR1 merged as #157; site **30600**). PR2 on M4 host: **M4 2310→2490 (+180)**; M5 moves in the same PR on its own plan. Site **30600→30960**, still 71 lessons.

- **H3 / 4.3 urdf-tf: 240→420 (+180).** tf2 Buffer lookup time. Toy `tf_buffer_time_lookup_toy.py`: closed-form joint trajectory and a lookup-table buffer (no time step), arms A time 0 / B stamped lookup with a 50 ms timeout / C hand-written extrapolation; shared trajectory, broadcast stamps and latencies, image stamps and delivery lags (common random numbers, 5 seeds). static_tree: all **tie** (identical on every seed); lagging_stamp: A−B err 170.5300±37.6692 mm, clear, 5/5, C−B **tie**; fresh_stamp: C−B err 15.5360±3.4333, clear, 5/5, B waits 30.4452±0.4321 ms (B loses on latency); tf_dropout: B fails on 19.7531±0.5040 % of images (B loses on failures, clear, 5/5). Added a whole-lesson final Summary in en/zh (the host had none). ≠ SROS2 / composition; ≠ Gazebo Δt. Real `ros2 run tf2_ros` 本页未运行.

**Allocation / 安排:** 30+30+40+40+40=180 minutes.

**Site accounting / 全站核算:** **30960=30600+360** with M5 +180 on month-5-plan.md; **M4=2490**, **71 lessons**.

## Batch-12 PR1 / 本月 H2 (+180)

Base `a4b3b93` (batch-11 closed incl. polish #148; site **28050**). PR1 only on M4 host: **M4 2130→2310 (+180)**; M1 moves in the same PR on its own plan. Site **28050→28380**, still 71 lessons.

- **H2 / 4.4 gazebo-sim: 270→450 (+180).** Physics step size (`max_step_size`) vs contact stability on a synthetic linear Kelvin–Voigt stand-in (not DART, not bit-exact; ≠ MuJoCo `solref` sweep; ≠ `inertia_check.py`). Semi-implicit Euler criterion `ωΔt < 2(√(ζ²+1) − ζ)` (3.279 ms here) and explicit Euler `ωΔt < 2ζ` (0.800 ms), checked by spectral radius and by tests. Shared drop heights and step-averaged disturbance `f(t)` (common random numbers, 5 seeds); arms 3 ms / 1 ms / 0.1 ms vs a 10 µs reference; impact: coarse loses; gentle rest: small next to the ~39 µm static sag but **consistent** (`|paired mean| > sd`, same sign on 5/5 seeds; relabelled in the batch-12 polish from an earlier near-tie label). Added a whole-lesson final Summary in en/zh (the host had none). Real Gazebo / DART 本页未运行.

**Allocation / 安排:** 30+40+40+40+30=180 minutes.

**Site accounting / 全站核算:** **28380=28050+330** with M1 +150 on month-1-plan.md; **M4=2310**, **71 lessons**.

## Batch-7 PR2 / 本月 H3 (+210)

4.6 slam-nav240→450; M4 **1620→1830**, six lessons. This PR only: site **22830→23190** (+210+150), M5 **1800→1950**, still71 lessons; no arithmetic mismatch. No PR3 minutes included.

Allocation:45+45+45+45+30=210 min (shared surface matching / plane linearization / five-seed rotation sweep / corridor rank / exercises). Same measured target polyline adjacency and noisy source returns to both arms, no true correspondence IDs; same caps/stop/trust bounds. Point-point frozen pairs versus plane linearization are distinguished from the re-associated physical objective. Both lack corridor along-wall information even though frozen point-point pairs look full rank.

Existing odometry calibration, SLAM Toolbox mapping/saving, Nav2 goals and TF/costmap/time diagnosis remain. Added full whole-lesson final Summary in en/zh (neither previously had one). New code/stdout/exercises precede it. Stdlib toy and independent numerical tests, expected output and check_py execute before the existing ROS guard. ROS/Open3D/real-lidar parts 本页未运行; no workflow changes. Sources: batch-7-pr2-sources.md.


## Batch-8 PR1 — SROS2 and composition (Month 4 hosts only)

Base6afd383, after #132. H1 ros2-setup210→360 (+150), H2 ros2-graph240→390 (+150).
M4 **1830→2130**; site **23610→23910** (+300), still71 lessons. No arithmetic mismatch.
Proposal §4–5 explicitly places H3 IBVS in PR2, not PR1; §9 lists its locks for the batch, not an extra PR1 host.

- H1: 30 min keystore/enclave reading +35 min exhaustive ACL table +45 min shared grant/domain perturbations +40 min negative-test design =150.
- H2: 35 min component-container reading +35 min shared workload accounting +40 min crash-domain perturbations +40 min real-run trace design =150.
- Deterministic stdlib toys need no stochastic seeds; all24 ACL requests and N=2/4/8 deployments are exhaustively compared.
- Both original hosts lacked Summary: add a full whole-lesson final Summary, including one added-topic sentence, in en and zh.
- Real ROS/DDS/robot/intra-process measurements 本页未运行. No zero-copy, encryption, wall-clock speedup or certification inference from counters.
- This PR excludes IBVS, escalation, VQ-BeT, dual-system and all deferred hardware topics. Historical plan entries above retain their own PR-only totals.
