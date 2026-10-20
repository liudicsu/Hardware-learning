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
