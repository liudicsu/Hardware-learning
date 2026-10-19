# Lesson 2: state space, LQR and MPC / 第 2 课：状态空间、LQR 与 MPC

This lesson's program is a toy model and lives in [`tools/sim/models/lqr_sim.py`](../../../tools/sim/models/lqr_sim.py). It uses only the Python standard library (small matrix helpers are written out in the file).
本课的程序是一个玩具模型，放在 [`tools/sim/models/lqr_sim.py`](../../../tools/sim/models/lqr_sim.py)，只用 Python 标准库（文件里自带几个小的矩阵函数）。

```bash
python3 tools/sim/models/lqr_sim.py
```

What it does / 它做什么:
1. A cart-pole (M = 0.5 kg, m = 0.2 kg at L = 0.3 m, force input) in state space, linearised about upright and discretised at 100 Hz; LQR gains from the discrete Riccati equation for three Q/R choices, each tested on the full nonlinear cart-pole with a 10 N limit.
   小车倒立摆的状态空间模型（在直立处线性化，100 Hz 离散化）；用离散 Riccati 方程求三组 Q/R 的 LQR 增益，并在带 10 N 限幅的完整非线性模型上检验。
2. Lesson 1's arm joint moved through 1 rad with |torque| ≤ 0.6 N·m: LQR with its output clipped against an MPC (40-step horizon, projected gradient, warm-started).
   第 1 课的关节在 |力矩| ≤ 0.6 N·m 下转 1 rad：输出被削顶的 LQR 对比 MPC（40 步时域、投影梯度、热启动）。

The site editor cross-checked the LQR gains against an independent NumPy Riccati iteration (agreement to 1e-12) and checked that every closed loop is stable (largest eigenvalue magnitude below 1). Output quoted in the lesson as **simulated output / 仿真输出**; checked by `tools/sim/reproduce.sh` against `tools/sim/expected/m5-lqr_sim.txt`. Not run on a real robot.
本站编者用独立的 NumPy Riccati 迭代核对了 LQR 增益（误差在 1e-12 以内），并确认每个闭环都稳定（特征值模的最大值小于 1）。课程中以“仿真输出”引用；由 `tools/sim/reproduce.sh` 与 `tools/sim/expected/m5-lqr_sim.txt` 比对。没有在真机上运行过。
