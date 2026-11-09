# Month 4 plan / 第4个月计划

Current / 当前：**M4 2670 min**, Batch-15 PR2. Earlier entries below retain their historical totals.

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
