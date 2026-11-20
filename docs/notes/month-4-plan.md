# Month 4 plan / 第4个月计划

Current / 当前：**M4 3930 min**, Batch-26 PR1. Earlier entries below retain their historical totals.

Current / 当前：**M4 3750 min**, Batch-25 PR1. Earlier entries below retain their historical totals.

## Batch-26 PR1 / 本月 H2 (+180)

Base `783242044cfd250be2d3747a5b31633f650b1369` (batch-25 PR3 #203 squash-merged; site **43380**). PR1 on M4 host: **M4 3750→3930 (+180)**; M3 moves in the same PR on its own plan. Site **43380→43740** (43740=43380+180+180), still 71 lessons.

- **H2 / 4.5 ros2-control: 420→600 (+180).** Official Jazzy controller chaining / cascade contract (`controller_chaining_cascade_toy.py`; common random numbers, 5 seeds; shared reference, measurement noise and inner-disturbance draws). Jazzy chaining page commit `b558c3ab693fbf9aa472392cafc0c0f14f9fc549` (2026-11-18 05:59:51 Asia/Shanghai), blob `0b91260a4064e51fce45e0de1e09101c5147fd02`; DiffBot example 16 commit `b34cc5917f216b36ff3bda1ca0cc0736ecc00235` (2025-07-10 15:15:16 Asia/Shanghai), blob `331f9881206b6a71a60b6c5b0463161c2039e99b`; 以文档为准. Activate following controllers first; chained mode disables subscribers; reference interfaces unavailable / unclaimed / claimed as documented. Declared stand-in: `DT=0.0020` s, `TAU_INNER=0.0250` s, `TAU_OUTER=0.6000` s, `T_REF=2.5000` s, `KP_SINGLE=1.8500`, `KP_OUTER=2.0000`, `KP_INNER=12.0000`, `SIG_Y=0.0100`, `DIST_AMP=0.3500`. Hand calc (printed): inner ZOH `0.9231` / `0.0769`, outer ZOH `0.9967` / `0.0033`, ratio `24.0000`, window `3500`, `0.2000`. slow_no_dist: B-A outer `1.234e-7+-1.824e-6`, **near-tie** (2 of 5 opposite; declared may near-tie **held**); A/B outer `0.2899`. inner_disturbance: B-A outer `-0.9775+-9.508e-5` and inner `-4.0858+-1.412e-5`, **clear**, 5/5 (held). broken_chain: C-B outer `0.5038+-5.723e-5`, **clear**, 5/5 (held). Alternatives (declared, same seeds): `KP_SINGLE=1.5000` turns the quiet B-A outer cell into a small consistent gap `-0.0398+-6.176e-6` (not adopted). No official toy or expected/ change after the first official run 2026-11-20 04:07:30 Asia/Shanghai. ≠ EtherCAT / Ziegler-Nichols / Deadline / rmw_zenoh. Real controller_manager / DiffBot 本页未运行. / 慢参考无扰动时单环与串级接近打平；内环扰动下串级稳定更好；随后控制器未激活则链断开失败。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

**Site accounting / 全站核算:** **43740=43380+360** with M3 +180 on month-3-plan.md; **M4=3930**, **71 lessons**.


## Batch-25 PR1 / 本月 H1 (+180)

Base `def8795172af98816d18a7c732ac33b2066f8ea3` (batch-24 polish #200 merged; site **42300**). PR1 on M4 host: **M4 3570→3750 (+180)**; M5 moves in the same PR on its own plan. Site **42300→42660** (42660=42300+180+180), still 71 lessons.

- **H1 / 4.1 ros2-setup: 360→540 (+180).** rmw_zenoh versus default Fast DDS (`rmw_zenoh_qos_discovery_toy.py`; common random numbers, 5 seeds; shared publication timeline, payload and Bernoulli drops at P_DROP=0.0500, N_PUB=40). Working with Zenoh bodies (Kilted `c16e4499d67f350e22dfec987a289e6e59ce506c`, Jazzy `1b19bccd1317223f5dab53b495426f177fdcddda`, byte-identical; 以文档为准): `export RMW_IMPLEMENTATION=rmw_zenoh_cpp`, `sudo apt install ros-{DISTRO}-rmw-zenoh-cpp`, `ros2 run rmw_zenoh_cpp rmw_zenohd`; without the router, multicast discovery is disabled by default and gossip goes via the router. Kilted vendors (`17d097028c3a8dd09725ea3ceeaba2a9db103c35`; 以文档为准): Fast DDS is the default RMW; “Zenoh offers a more lightweight alternative to DDS and maintains Quality of Service features (in Zenoh, there are essentially no ‘incompatible’ QoS settings)”; rmw_zenoh_cpp “Packaged with binary releases starting with Kilted Kaiju.” Jazzy vendors (`95dbbf32761f6dfca6e6f6327a3a2cfb9784a653`; 以文档为准): Fast DDS default; Zenoh is not in the packaged-RMW table (Fast DDS, RTI Connext Pro, Eclipse Cyclone DDS, GurumNetworks GurumDDS). Kilted release notes (`1f757343c8ed06b57896b5a5febc536919b10e7f`; 以文档为准): rmw_fastrtps_cpp* default Tier 1; rmw_zenoh_cpp Eclipse Zenoh Tier 1, all platforms. Course still starts on Jazzy; Zenoh is not called the default or Jazzy Tier 1. Declared stand-in parameters: N_PUB 40, P_DROP 0.0500, seeds 0–4, SMALL_FRAC 0.2000; stand-in rule treats reliable publisher + best-effort subscriber as incompatible under A only. Hand calc (printed): 40.0000, 38.0000, 0.2000, 32.0000. compatible_qos: B−A received `0.0000+-0.0000`, **tie: identical on every seed** (declared “may near-tie”, held as an exact tie). incompatible_qos: B−A received `38.0000+-1.0000`, **clear**, 5/5 (held); A received 0.0000. no_router: C−B received `-38.4000+-1.3416`, **clear**, 5/5 (held); C received 0.0000. Alternatives (declared, same seeds): P_DROP=0.2000 keeps the official labels (compatible tie at 32.4000+-2.5100; incompatible clear 33.6000+-1.1402); swapped best-effort publisher / reliable subscriber is compatible under the stand-in rule, so A and B tie at 38.0000+-1.0000 (not adopted). No code change after the first official run. ≠ SROS2 / Deadline / EtherCAT; the existing “newer Zenoh RMW supports neither” discovery-env sentence is untouched. Real rmw / rmw_zenohd / multi-machine multicast 本页未运行. / 相容 QoS 时 DDS 式与 Zenoh 式投递打平；不相容时只有 Zenoh 式送达；没有路由器时 Zenoh 式发现失败。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

Current / 当前：**M4 3570 min**, Batch-23 PR2. Earlier entries below retain their historical totals.

## Batch-23 PR2 / 本月 H3 (+180)

Base `5930053b6e4298a41f13906160965fd453365707` (batch-23 PR1 #193 merged; site **40500**). PR2 on M4 host: **M4 3390→3570 (+180)**; M7 moves in the same PR on its own plan. Site **40500→40860** (40860=40500+180+180), still 71 lessons.

- **H3 / 4.6 slam-nav: 810→990 (+180).** AMCL, particle-filter localization against a known map (`amcl_particle_filter_localization_toy.py`; common random numbers, 5 seeds; true start, motion directions and noise, beam noise and the kidnap pose drawn once per regime and seed, shared by all three arms). Wikipedia Monte Carlo localization body read (rev 1279828307; 以原文为准): particle filter localization on a given map, uniform start, motion and sensor updates, multimodal belief, particle deprivation and the kidnapped robot (M ≤ 50), random particles as remedy, KLD sampling. Archived ROS wiki `amcl` page (Wayback 2024-12-26; 以原文为准): adaptive (KLD-sampling) MCL against a known map; min_particles 100 / max_particles 5000, kld_err 0.01, recovery alphas 0.0 by default with 0.001 / 0.1 suggested, laser_model_type likelihood_field. Live ROS wiki and the Nav2 AMCL configuration page not cited. Declared toy parameters: rooms 10×6 m with three boxes and a 12×2 m corridor, heading known, 4 axis beams SIG_Z=0.1 m capped at 8 m, step 0.3 m with 0.05 scale and 0.02 m additive noise, SIG_L=0.2, Z_HIT/Z_RAND=0.9/0.1, EPS=0.05, Z_Q=2.326, 0.5 m bins, B 100–600 particles with recovery 0.05 / 0.5, C 30 particles without recovery; particles move without added noise. Hand calc (printed): KLD 65.8404 → 100, 216.9395, 749.3302 → 600; floor 0.0125; drift 0.1250 m. distinctive_unknown: B−A err `-2.9468±1.1879`, **clear**, 5/5 (held); C−B err `3.1153±2.1111` clear. known_short: B−A err `-0.0157±0.0066`, **clear**, 5/5 (declared near-tie **did not hold**). kidnapped: C−B err `4.4777±1.9964` and success `-1.0000±0.0000`, **clear**, 5/5 (held, kept); B−A err `-4.4787±2.0026`. corridor_multimodal: B−A err `-2.3561±1.0515` clear; the declared possible B failure did not occur (both end walls within 8 m of every point, 手算). Alternatives (declared, same seeds): B recovery off X−B err `4.4964±1.9985`; N_MAX=300 X−B err `-0.0115±0.0566` near-tie; C with recovery X−C err `-2.7986±1.3081`; none adopted. No code change after the first run. ≠ ICP, DWA/RPP, OctoMap/TSDF; the OctoMap wording is untouched. Real robot / Nav2 AMCL 本页未运行. / AMCL：起点未知或被绑架时带恢复的滤波胜过航位推算，粒子太少又不恢复会丢失位姿。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

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
