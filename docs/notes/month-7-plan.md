# Month 7 plan: Simulation, reinforcement learning & 3D perception

Site supplement beyond @DeRonin_'s 6-month roadmap. Proposal: `/workspace/proposals/m7-m8-proposal.md` §2 / §5 / §6.
Batch 1 (this PR): scaffold all six lessons; full MDX + examples for **7.1, 7.2, 7.5** only.
Electives E7-a/b/c stay on the month page topics only (not formal lessons, not in minutes).

Constraints: no shared month-4 pixi; private venv for MuJoCo (`M7_PYTHON`). 7.2 / 7.5 examples are stdlib-only toys with fixed seeds. GPU / GUI / true SB3 / Open3D / Menagerie meshes marked「本页未运行」. Hard facts re-fetched from primary sources (2026-11-04 UTC+8), not copied from the proposal.

| # | slug | minutes | this batch | runnable | verified against |
|---|------|---------|------------|----------|------------------|
| 1 | `mujoco-so101` | 240 | full | `grip_sweep.py` + `grip_scene.xml` (needs mujoco) | Menagerie robotstudio_so101 README / so101.xml; MuJoCo modeling.rst + XMLreference.rst (solref/solimp/impratio/cone); SO-ARM100 Simulation/SO101 |
| 2 | `rl-foundations` | 240 | full | `ppo_reach.py` (stdlib clipped-ratio toy) | SB3 PPO docs (“primarily on the CPU”); Gymnasium; Spinning Up rl_intro; arXiv 1707.06347 |
| 3 | `rl-manipulation-sim` | 240 | outline shell | — | deferred |
| 4 | `sim-to-real` | 240 | outline shell | — | deferred |
| 5 | `depth-pointcloud` | 240 | full | `cloud_pipeline.py` (stdlib) | Open3D pointcloud / RGBDImage APIs; Depth Anything V2 + metric_depth licences |
| 6 | `perception-to-grasp` | 300 | outline shell | — | deferred (OpenCV calibrateHandEye was 403; not needed this batch) |

Rechecks from proposal §6 (this batch):
- Isaac Lab install URL redirects to `source/isaaclab/installation.html`; current page uses Newton/Warp by default, CUDA Turing+ for GPU training — electives only.
- micro.ros.org/docs/overview/hardware/ → **404** (use GitHub READMEs when M8 touches micro-ROS).
- ISO 10218-1 still Cloudflare/403 — not cited as a hard fact this batch.

Widgets: RewardCurveWidget / PointCloudWidget deferred (must be measurable via check_widgets; not in this batch).

Verification: `examples/month-7/check.sh` (hooked into `tools/sim/reproduce.sh`), check_diagrams bindings + mutations, check_quotes, lint, tsc, CI build, check_text_size.
