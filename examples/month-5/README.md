# Month 5 examples / 第 5 个月示例

One folder per lesson; each folder's README lists what it contains and how to run it.
每课一个目录，目录里的 README 写明内容和运行方法。

| Lesson / 课程 | Folder / 目录 | What / 内容 | Checked by / 验证方式 |
| --- | --- | --- | --- |
| 1 Control theory: model, then frequency domain / 控制理论：建模与频域 | [`control-modelling/`](control-modelling/) | `joint_freq.py` (in `tools/sim/models/`): identification, Bode data, margins / 参数辨识、伯德数据、裕度 | `tools/sim/reproduce.sh` (toy model / 玩具模型) |
| 2 State space, LQR and MPC / 状态空间、LQR 与 MPC | [`state-space-lqr/`](state-space-lqr/) | `lqr_sim.py` (in `tools/sim/models/`): cart-pole LQR, MPC on the arm joint / 小车倒立摆 LQR、关节 MPC | `tools/sim/reproduce.sh` (toy model / 玩具模型) |
| 3 Kinematics: FK, numerical IK, singularities / 运动学：正解、数值逆解、奇异点 | [`kinematics-ik/`](kinematics-ik/) | `kinematics.py` (in `tools/sim/models/`) / 正运动学、阻尼最小二乘逆解、奇异点 | `tools/sim/reproduce.sh` (toy model / 玩具模型) |
