# Lesson 3: kinematics, forward, numerical IK and singularities / 第 3 课：运动学，正解、数值逆解与奇异点

This lesson's program lives in [`tools/sim/models/kinematics.py`](../../../tools/sim/models/kinematics.py) and uses only the Python standard library. The arm is laid out like the first three joints of an SO-101 (base yaw, shoulder, elbow) with round-number lengths (H = 0.05 m, L1 = 0.12 m, L2 = 0.14 m), not the SO-101's real dimensions.
本课程序放在 [`tools/sim/models/kinematics.py`](../../../tools/sim/models/kinematics.py)，只用 Python 标准库。模型臂的布局与 SO-101 前三个关节（底座偏航、肩、肘）相同，但连杆长度取整数（H = 0.05 m、L1 = 0.12 m、L2 = 0.14 m），不是 SO-101 的真实尺寸。

```bash
python3 tools/sim/models/kinematics.py
```

What it does / 它做什么: forward kinematics by a chain of homogeneous transforms and by hand; numerical IK by damped least squares (λ = 0.03, at most 2 cm per step) with a second solution and an unreachable target; the Jacobian determinant and joint speeds as the elbow straightens.
用齐次变换链和手算两种方式求正运动学；用阻尼最小二乘做数值逆解（λ = 0.03，每步最多 2 cm），包括第二组解和够不着的目标；肘部伸直时雅可比行列式与关节速度的变化。

To use it with your own arm, change `H`, `L1`, `L2` to your link lengths (measured joint axis to joint axis) and check the sign of each joint against the real arm before trusting any IK result. Output quoted in the lesson as **simulated output / 仿真输出**; checked by `tools/sim/reproduce.sh` against `tools/sim/expected/m5-kinematics.txt`.
用于你自己的机械臂时，把 `H`、`L1`、`L2` 改成实测的连杆长度（关节轴到关节轴），并先对照真机确认每个关节的正方向，再相信 IK 结果。课程中以“仿真输出”引用；由 `tools/sim/reproduce.sh` 与 `tools/sim/expected/m5-kinematics.txt` 比对。

## poe_vs_dh_fk_toy.py

```bash
python3 examples/month-5/kinematics-ik/poe_vs_dh_fk_toy.py
```

Standard-library synthetic forward kinematics on the same three-joint SO-101 model: Denavit–Hartenberg rows, a product of exponentials (screw twists) and a PoE with a 2° wrong elbow twist, on shared joint configurations and encoder noise (five seeds, common random numbers). Closed-form, no integration step; expected output in `expected/poe_vs_dh_fk_toy.txt`, checked by `check.sh`. No real arm was run.
标准库合成正运动学，用同一个三关节 SO-101 模型比较 DH 参数、指数积（螺旋运动旋量）和肘部旋量偏 2° 的指数积，共用关节构型和编码器噪声（5 个种子，共用随机数）。闭式计算，没有积分步长；期望输出在 `expected/poe_vs_dh_fk_toy.txt`，由 `check.sh` 核对。本页未运行真实机械臂。
