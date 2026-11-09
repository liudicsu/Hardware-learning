# Month 4 plan / 第4个月计划

Current / 当前：**M4 2310 min**, Batch-12 PR1. Earlier entries below retain their historical totals.

## Batch-12 PR1 / 本月 H2 (+180)

Base `a4b3b93` (batch-11 closed incl. polish #148; site **28050**). PR1 only on M4 host: **M4 2130→2310 (+180)**; M1 moves in the same PR on its own plan. Site **28050→28380**, still 71 lessons.

- **H2 / 4.4 gazebo-sim: 270→450 (+180).** Physics step size (`max_step_size`) vs contact stability on a synthetic linear Kelvin–Voigt stand-in (not DART, not bit-exact; ≠ MuJoCo `solref` sweep; ≠ `inertia_check.py`). Semi-implicit Euler criterion `ωΔt < 2(√(ζ²+1) − ζ)` (3.279 ms here) and explicit Euler `ωΔt < 2ζ` (0.800 ms), checked by spectral radius and by tests. Shared drop heights and step-averaged disturbance `f(t)` (common random numbers, 5 seeds); arms 3 ms / 1 ms / 0.1 ms vs a 10 µs reference; impact: coarse loses; gentle rest: **near-tie / small gap**, not a tie. Added a whole-lesson final Summary in en/zh (the host had none). Real Gazebo / DART 本页未运行.

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
