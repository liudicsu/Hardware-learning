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

## Batch-20 PR3 / 第20批 PR3

`perception-to-grasp/graspvla_syngrasp_pretrain_toy.py`: standard-library synthetic appearance vectors with a nearest-sample grounding step (geometry only vs grounding first with DR vs no DR vs shuffled labels), no GPU, no weights; expected output in `expected/graspvla_syngrasp_pretrain_toy.txt`, included in `check.sh`. GraspVLA numbers 以论文为准; real grasp cell 本页未运行. / 标准库合成外观向量与最近样本定位（只看几何、先定位加 DR、不做 DR、标签错乱），不是 GPU 训练或真机结果，输出由 `check.sh` 核对。

## depth-pointcloud/ — PointVLA: a point cloud added to a frozen 2D policy / PointVLA：给冻结的二维策略加上点云

`depth-pointcloud/pointvla_frozen_injector_toy.py`: standard-library synthetic grasp-height scenes with an additive point-cloud correction injected into a frozen policy (2D only vs late-block injection vs early-block injection; training height, raised table, photos on a screen, corrupted cloud) on shared scene, noise and grip draws; no GPU, no weights; expected output in `expected/pointvla_frozen_injector_toy.txt`, included in `check.sh`. PointVLA numbers 以论文为准; DexVLA / real camera / robot 本页未运行. / 标准库合成的抓取高度场景，把加法点云修正注入冻结策略（只用二维、注入靠后的块、注入靠前的块；训练高度、升高桌面、屏幕照片、损坏点云），不是 GPU 训练或真机结果，输出由 `check.sh` 核对。

## rl-foundations/ — Generalized advantage estimation: λ between Monte Carlo and one-step TD / 广义优势估计：在蒙特卡洛与一步 TD 之间取 λ

`rl-foundations/gae_lambda_advantage_toy.py`: standard-library synthetic episodes with a two-action policy and closed-form true advantages (λ = 1 vs λ = 0.95 vs λ = 0; long noisy episode, one step, delayed reward with a coarse value) on shared actions, reward noise and value errors; no neural network, no GPU; expected output in `expected/gae_lambda_advantage_toy.txt`, included in `check.sh`. Paper results 以原文为准; SB3 / MuJoCo / GPU 本页未运行. / 标准库合成回合，两动作策略，真实优势有闭式解（λ = 1、λ = 0.95、λ = 0；长含噪回合、一步、粗糙价值下的延迟奖励），共用动作、奖励噪声和价值误差，不是神经网络或 GPU 训练，输出由 `check.sh` 核对。
