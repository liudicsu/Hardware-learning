# Month 7 examples

CPU-reproducible scripts for Month 7 (site supplement). Run `./check.sh` from this folder.

| lesson | script | needs |
|--------|--------|-------|
| mujoco-so101 | `mujoco-so101/grip_sweep.py` | `pip install mujoco` in a private venv (set `M7_PYTHON` to that interpreter) |
| rl-foundations | `rl-foundations/ppo_reach.py` | stdlib |
| rl-manipulation-sim | `rl-manipulation-sim/reward_shaping.py` | stdlib |
| sim-to-real | `sim-to-real/sysid_fit.py`, `randomize_eval.py`, `contact_dr_toy.py` | stdlib |
| depth-pointcloud | `depth-pointcloud/cloud_pipeline.py` | stdlib |
| perception-to-grasp | `perception-to-grasp/handeye_toy.py` (numpy), `grasp_from_mask.py` | stdlib |

Batch-4 PR2: `depth-pointcloud/gsplat_collision_toy.py` (stdlib CPU), reproduced by `check.sh`; output in `expected/gsplat_collision_toy.txt`. Shared synthetic scene / queries; independent distance truth, conservative AABB vs sampled ellipsoid; no 3DGS training.
