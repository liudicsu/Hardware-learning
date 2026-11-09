# Month 7 plan: Simulation, reinforcement learning & 3D perception

Current / 当前：**M7 2250 min**, Batch-12 PR2. Earlier entries below retain their historical totals.

## Batch-12 PR2 / 本月 H4 (+180)

Base `ad9407a` (batch-12 PR1 merged; site **28380**). PR2 on M7 host: **M7 2070→2250 (+180)**; M5 moves in the same PR on its own plan. Site **28380→28740**, still 71 lessons.

- **H4 / depth-pointcloud: 450→630 (+180).** Local PCA normals: k-NN covariance, eigenvector of the smallest eigenvalue (stdlib cyclic Jacobi), flipped toward the viewpoint; neighbourhood size vs noise / curvature; orientation ambiguity. Toy `pointcloud_pca_normals_toy.py`: shared height-field cloud, depth-noise draws and queries (common random numbers, 5 seeds); arms global plane (no per-point normals) / PCA k = 20 / PCA k = 4. flat_low_noise: k = 20 loses to the global plane on angle (paired B−A 0.7449±0.0397°), residual a small but consistent gap in B's favour (metric rewards fitting noise); ripple_noisy: k = 20 wins; fine_ripple_low_noise: k = 4 beats k = 20 on angle (paired B−C 5.2476±0.4954°). ≠ voxel/RANSAC-only; ≠ ICP. Open3D / PCL on a real sensor 本页未运行.

**Allocation / 安排:** 30+30+40+50+30=180 minutes.

**Site accounting / 全站核算:** **28740=28380+360** with M5 +180 on month-5-plan.md; **M7=2250**, **71 lessons**.

Site supplement beyond @DeRonin_'s 6-month roadmap. Proposal: `/workspace/proposals/m7-m8-proposal.md` §2 / §5 / §6.
Batch 1 (merged #83): scaffold all six lessons; full MDX + examples for **7.1, 7.2, 7.5**.
Batch 2 (this PR): full MDX + examples for **7.3, 7.4, 7.6**; curriculum promoted; portfolio / grip mass nits.
Electives E7-a/b/c stay on the month page topics only (not formal lessons, not in minutes).

Constraints: no shared month-4 pixi; private venv for MuJoCo (`M7_PYTHON`). Runnable toys prefer stdlib / NumPy CPU with fixed seeds. GPU / GUI / true SB3 / ManiSkill / Open3D / SAM2 / Menagerie meshes marked「本页未运行」or「本页未强制」/「需硬件」. Hard facts re-fetched from primary sources (2026-11-04 UTC+8), not copied from the proposal.

| # | slug | minutes | this batch | runnable | verified against |
|---|------|---------|------------|----------|------------------|
| 1 | `mujoco-so101` | 240 | batch 1 | `grip_sweep.py` + `grip_scene.xml` (needs mujoco) | Menagerie robotstudio_so101; MuJoCo modeling/XMLreference; SO-ARM100 Simulation/SO101 |
| 2 | `rl-foundations` | 450 | batch 1 | `ppo_reach.py` (stdlib) | SB3 PPO docs; Gymnasium; Spinning Up; arXiv 1707.06347 |
| 3 | `rl-manipulation-sim` | 240 | **full** | `reward_shaping.py` (stdlib) | ManiSkill install + PickCubeSO100-v1; SB3 SAC; arXiv 1801.01290 / 2410.00425 |
| 4 | `sim-to-real` | 390 | **full** | `sysid_fit.py` + `randomize_eval.py` + `contact_dr_toy.py` (stdlib) | Tobin arXiv 1703.06907; Peng arXiv 1710.06537; Isaac Lab README (Sim 6.2); ISO 10218-1 403 → soft safety wording |
| 5 | `depth-pointcloud` | 450 | batch 1 | `cloud_pipeline.py` (stdlib) | Open3D APIs; Depth Anything V2 licences |
| 6 | `perception-to-grasp` | 300 | **full** | `handeye_toy.py` (NumPy) + `grasp_from_mask.py` (stdlib) | OpenCV `calib3d.hpp` calibrateHandEye (TSAI/Park; ≥3 poses; eye-in-hand vs eye-to-hand); SAM2 LICENSE Apache-2.0 |

Rechecks from proposal §6 (batch 2):
- OpenCV `calibrateHandEye` via raw `calib3d.hpp` (HTML previously 403) — signature + ≥3 poses + eye-in-hand/eye-to-hand notes confirmed.
- ISO 10218-1 still Cloudflare/403 — not cited as hard clause numbers; general e-stop / torque / speed language only.
- Isaac Lab README: GPU-accelerated; Isaac Sim workflows target Isaac Sim 6.2 — elective only, no invented install steps (install HTML scrape empty / path 404).
- micro.ros.org hardware page still not used (M8).

Widgets: RewardCurveWidget / PointCloudWidget deferred (must be measurable via check_widgets; not in this batch).

Verification: `examples/month-7/check.sh` (hooked into `tools/sim/reproduce.sh`), check_diagrams bindings + mutations, check_quotes, lint, tsc, CI build, check_text_size.

Batch-after-obs PR3 (G5, +150): 7.4 `sim-to-real` 240→390 — `contact_dr_toy.py`: contact-parameter DR (friction µ, mass) vs latency-only randomisation tuning one push speed on the same budget (41 candidates × 200 episodes) and seed stream; nominal and shifted µ / mass reported (DR ties nominal success but pays cycle time 0.72 → 1.08 s; fails outside its range at µ = 0.15). No τ refit, no PE narrative; toy friction ≠ MuJoCo. Month 7 **6 lessons / 1 650 min**; site **71 lessons / 18 570 min**.

## Batch-4 PR2 (locked H1/H6)

H1 7.5 240→450 (+210): thresholded Gaussians are not hard surfaces; shared scene/query sphere collision, independent distance truth vs conservative AABB and finite-s K(s) witness test. Month 7 **1 860 min** (1 650 + 210); **2 070 is the future PR3 total after H2 +210**, not this PR. No occupancy A* redo; GPU 本页未运行.

Site: **71 lessons / 19 440 min** (19 050 + 390). See `batch-4-pr2-sources.md` for source checks and the M7 arithmetic correction.

## Batch-4 PR3 (last planned PR)

H2 7.2 240→450 (+210): Plant-A pretrained tracker → shared160 Plant-B transitions per arm → SysID-retune/DR-widen/residual-action simulation fine-tuning → policy-only B deployment. Five seeds with spread; no universal winner; not PPO/contact-DR/PE redo. M7 **2070 min** (1860+210).

Site **71 lessons /19830 min** (19440+390); M7=2070,M11=3000. New material precedes final bilingual Summary. Source/limit audit: `batch-4-pr3-sources.md`.
