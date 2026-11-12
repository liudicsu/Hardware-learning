# Month 7 examples

CPU-reproducible scripts for Month 7 (site supplement). Run `./check.sh` from this folder.

| lesson | script | needs |
|--------|--------|-------|
| mujoco-so101 | `mujoco-so101/grip_sweep.py` | `pip install mujoco` in a private venv (set `M7_PYTHON` to that interpreter) |
| rl-foundations | `rl-foundations/ppo_reach.py` | stdlib |
| rl-manipulation-sim | `rl-manipulation-sim/reward_shaping.py`, `her_sparse_grasp_toy.py` | stdlib |
| sim-to-real | `sim-to-real/sysid_fit.py`, `randomize_eval.py`, `contact_dr_toy.py` | stdlib |
| depth-pointcloud | `depth-pointcloud/cloud_pipeline.py` | stdlib |
| perception-to-grasp | `perception-to-grasp/handeye_toy.py` (numpy), `grasp_from_mask.py` | stdlib |

Batch-4 PR2: `depth-pointcloud/gsplat_collision_toy.py` (stdlib CPU), reproduced by `check.sh`; output in `expected/gsplat_collision_toy.txt`. Shared synthetic scene / queries; independent distance truth, conservative AABB vs sampled ellipsoid; no 3DGS training.

Batch-4 PR3: `rl-foundations/residual_action_mismatch_toy.py` (stdlib CPU); `check.sh` compares `expected/residual_action_mismatch_toy.txt`. Same160 Plant-B samples/arm,5 shared seeds, policy-only deployment; not humanoid training.

## Batch-20 PR2 / 第20批 PR2

`sim-to-real/tobin_visual_domain_randomization_toy.py`: standard-library synthetic 1-D camera row with a k-NN detector (canonical texture vs Tobin-style random textures vs random textures plus a wrong τ), no GPU, no hardware; expected output in `expected/tobin_visual_domain_randomization_toy.txt`, included in `check.sh`. Real camera / robot 本页未运行. / 标准库合成的一维相机行与 k 近邻检测器（固定纹理、Tobin 式随机纹理、随机纹理加错误 τ），不是 GPU 训练或硬件结果，输出由 `check.sh` 核对。
