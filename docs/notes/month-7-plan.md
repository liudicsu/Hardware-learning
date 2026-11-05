# Month 7 plan: Simulation, reinforcement learning & 3D perception

Site supplement beyond @DeRonin_'s 6-month roadmap. Proposal: `/workspace/proposals/m7-m8-proposal.md` §2 / §5 / §6.
Batch 1 (merged #83): scaffold all six lessons; full MDX + examples for **7.1, 7.2, 7.5**.
Batch 2 (this PR): full MDX + examples for **7.3, 7.4, 7.6**; curriculum promoted; portfolio / grip mass nits.
Electives E7-a/b/c stay on the month page topics only (not formal lessons, not in minutes).

Constraints: no shared month-4 pixi; private venv for MuJoCo (`M7_PYTHON`). Runnable toys prefer stdlib / NumPy CPU with fixed seeds. GPU / GUI / true SB3 / ManiSkill / Open3D / SAM2 / Menagerie meshes marked「本页未运行」or「本页未强制」/「需硬件」. Hard facts re-fetched from primary sources (2026-11-04 UTC+8), not copied from the proposal.

| # | slug | minutes | this batch | runnable | verified against |
|---|------|---------|------------|----------|------------------|
| 1 | `mujoco-so101` | 240 | batch 1 | `grip_sweep.py` + `grip_scene.xml` (needs mujoco) | Menagerie robotstudio_so101; MuJoCo modeling/XMLreference; SO-ARM100 Simulation/SO101 |
| 2 | `rl-foundations` | 240 | batch 1 | `ppo_reach.py` (stdlib) | SB3 PPO docs; Gymnasium; Spinning Up; arXiv 1707.06347 |
| 3 | `rl-manipulation-sim` | 240 | **full** | `reward_shaping.py` (stdlib) | ManiSkill install + PickCubeSO100-v1; SB3 SAC; arXiv 1801.01290 / 2410.00425 |
| 4 | `sim-to-real` | 240 | **full** | `sysid_fit.py` + `randomize_eval.py` (stdlib) | Tobin arXiv 1703.06907; Peng arXiv 1710.06537; Isaac Lab README (Sim 6.2); ISO 10218-1 403 → soft safety wording |
| 5 | `depth-pointcloud` | 240 | batch 1 | `cloud_pipeline.py` (stdlib) | Open3D APIs; Depth Anything V2 licences |
| 6 | `perception-to-grasp` | 300 | **full** | `handeye_toy.py` (NumPy) + `grasp_from_mask.py` (stdlib) | OpenCV `calib3d.hpp` calibrateHandEye (TSAI/Park; ≥3 poses; eye-in-hand vs eye-to-hand); SAM2 LICENSE Apache-2.0 |

Rechecks from proposal §6 (batch 2):
- OpenCV `calibrateHandEye` via raw `calib3d.hpp` (HTML previously 403) — signature + ≥3 poses + eye-in-hand/eye-to-hand notes confirmed.
- ISO 10218-1 still Cloudflare/403 — not cited as hard clause numbers; general e-stop / torque / speed language only.
- Isaac Lab README: GPU-accelerated; Isaac Sim workflows target Isaac Sim 6.2 — elective only, no invented install steps (install HTML scrape empty / path 404).
- micro.ros.org hardware page still not used (M8).

Widgets: RewardCurveWidget / PointCloudWidget deferred (must be measurable via check_widgets; not in this batch).

Verification: `examples/month-7/check.sh` (hooked into `tools/sim/reproduce.sh`), check_diagrams bindings + mutations, check_quotes, lint, tsc, CI build, check_text_size.

Batch-after-obs PR3 (G5, +150): 7.4 `sim-to-real` 240→390 — `contact_dr_toy.py`: contact-parameter DR (friction µ, mass) vs latency-only randomisation tuning one push speed on the same budget (41 candidates × 200 episodes) and seed stream; nominal and shifted µ / mass reported (DR ties nominal success but pays cycle time 0.72 → 1.08 s; fails outside its range at µ = 0.15). No τ refit, no PE narrative; toy friction ≠ MuJoCo. Month 7 **6 lessons / 1 650 min**; site **71 lessons / 18 570 min**.
