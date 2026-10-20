# Lesson 5: pick and place with MoveIt 2 / 第 5 课：用 MoveIt 2 做抓放

A collision-free pick and place on the Franka Panda arm from `moveit_resources`, planned with MoveIt 2's Python API (MoveItPy) and executed on ros2_control mock hardware (`mock_components/GenericSystem`: commands are copied to the joint states; no physics, no motors). Not the SO-101.
在 `moveit_resources` 里的 Franka Panda 机械臂上做一次无碰撞抓放：用 MoveIt 2 的 Python API（MoveItPy）规划，在 ros2_control 的 mock 硬件上执行（`mock_components/GenericSystem` 把命令直接拷到关节状态，没有物理、没有电机）。不是 SO-101。

| File / 文件 | What / 内容 |
| --- | --- |
| `bringup.launch.py` | static TF world → panda_link0, robot_state_publisher, controller manager with mock hardware, joint_state_broadcaster and the arm and hand controllers / 静态 TF、robot_state_publisher、带 mock 硬件的控制器管理器、关节状态广播器与手臂、夹爪控制器 |
| `moveit_py.yaml` | MoveItPy settings: planning scene monitor, the OMPL and Pilz pipelines, parameter sets `ompl_rrtc` and `pilz_lin` / MoveItPy 配置：规划场景监视器、OMPL 与 Pilz 管道、`ompl_rrtc` 和 `pilz_lin` 两组参数 |
| `pick_place.py` | table, wall and block; pick, attach, carry over the wall, place, detach; a collision check of the carry; a goal inside the wall that must fail / 桌子、墙和方块；抓取、附着、越墙搬运、放下、解除附着；检查搬运路径；一个必然失败的墙内目标 |

Run it (needs `examples/month-5/pixi.toml`, or ROS 2 Jazzy with the packages listed in [`../README.md`](../README.md)):
运行（需要 `examples/month-5/pixi.toml`，或装好 [`../README.md`](../README.md) 所列包的 ROS 2 Jazzy）：

```bash
cd examples/month-5/moveit-pick-place
ros2 launch bringup.launch.py        # terminal 1 / 终端 1: wait for three "Configured and activated" / 等到三行 "Configured and activated"
python3 pick_place.py                # terminal 2 / 终端 2
```

Output quoted in the lesson as **simulated output / 仿真输出** (real MoveIt 2 on mock hardware); checked by `tools/sim/m5/run.sh` against `tools/sim/expected/m5-moveit_pick_place.txt` and `m5-moveit_goal_invalid.txt`. OMPL is a random planner, so the OMPL waypoint counts, the carry's waypoint count and the `route:` line are masked in the comparison.
课程中以“仿真输出”引用（mock 硬件上的真实 MoveIt 2）；由 `tools/sim/m5/run.sh` 与 `tools/sim/expected/m5-moveit_pick_place.txt`、`m5-moveit_goal_invalid.txt` 比对。OMPL 是随机规划器，所以比对时屏蔽了 OMPL 的路点数、搬运路径的路点数和 `route:` 一行。
