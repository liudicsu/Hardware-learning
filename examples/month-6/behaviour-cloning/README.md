# Lesson 1: imitation learning I, behaviour cloning and DAgger / 第 1 课：模仿学习（一），行为克隆与 DAgger

`bc_reach.py` uses only the Python standard library and fixed seeds. A point gripper moves through an L-shaped corridor
0.2 m wide; a scripted expert records demonstrations (one row per frame: `episode_index`, `frame_index`, observation
`x, y`, action `dx, dy`, the same layout as a LeRobot dataset), a 1-nearest-neighbour behaviour-cloning policy is
trained on 5, 20 and 80 demos and on 20 noisy demos, and three DAgger rounds start from the 5-demo policy.
Every policy is evaluated over the same 100 seeded rollouts with 1 cm of actuator noise per step.
`bc_reach.py` 只用 Python 标准库并固定随机种子。点状夹爪在 0.2 m 宽的 L 形走廊里移动；脚本专家录制示范（每帧一行：
`episode_index`、`frame_index`、观测 `x, y`、动作 `dx, dy`，与 LeRobot 数据集的列布局相同），用 1 最近邻行为克隆分别在
5、20、80 条示范和 20 条带噪声的示范上训练，再从 5 条示范的策略开始做三轮 DAgger。所有策略都在同样的 100 次带 1 cm/步
执行器噪声、固定种子的运行上评估。

```bash
python3 bc_reach.py demos.csv      # writes the first 20 demos to demos.csv
```

No hardware needed. Output quoted in the lesson as **simulated output / 仿真输出**; checked by
`examples/month-6/check.sh` against `examples/month-6/expected/bc_reach.txt` and `bc_demos_head.txt`.
不需要硬件。课程中以“仿真输出”引用；由 `examples/month-6/check.sh` 与 `examples/month-6/expected/` 下的文件比对。

The real-robot version (LeRobot `lerobot-record`, `lerobot-train`, `lerobot-rollout` on an SO-101) is in the lesson;
those commands were not run here. 真机版本（SO-101 上的 LeRobot 命令）见课程正文，这里没有运行。

## hamster_hierarchical_path_toy.py

HAMSTER-style hierarchy (arXiv 2502.05485, Sections 4.1–4.2): a coarse 2-D path with gripper states, then a path-conditioned low-level k-nearest-neighbour policy on 3-D features, compared with a monolithic k-nearest-neighbour policy that also sees background appearance and with an off-task path; four regimes (visual shift, matched, coarse path, and no appearance variation — the last added after the first run and disclosed), five seeds, common random numbers. No integration step (kinematic steps, no obstacles). Checked by `examples/month-6/check.sh`. The HAMSTER VLM, RVT-2 / 3D-DA, a real robot and a GPU are not run here; paper numbers are per the paper. Not an ACT / Diffusion Policy head, not MolmoAct traces.
HAMSTER 式分层（arXiv 2502.05485 第 4.1–4.2 节）：带夹爪状态的粗略二维路径 → 以路径为条件、使用三维特征的底层 k 近邻策略，与同时看到背景外观的整体式 k 近邻策略和偏离任务的路径比较；四种情形（视觉偏移、匹配、粗路径、无外观变化，最后一种在第一次运行后加入并已说明），5 个种子，共用随机数。没有积分步长（运动学步进，无障碍物）。由 `examples/month-6/check.sh` 核对。HAMSTER VLM、RVT-2 / 3D-DA、真机与 GPU 本页未运行；论文数字以论文为准。不是 ACT / Diffusion Policy 动作头，也不是 MolmoAct 轨迹。

```bash
python3 hamster_hierarchical_path_toy.py
```
