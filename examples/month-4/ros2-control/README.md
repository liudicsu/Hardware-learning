# Lesson 5: ros2_control / 第 5 课：ros2_control

- **`m4_drive_interfaces/`** (`ament_cmake`): the `DriveDistance` action (goal: distance and speed; result: distance really travelled, reached or not; feedback: travelled and remaining).
  `DriveDistance` 动作定义（目标：距离和速度；结果：实际走了多远、是否到达；反馈：已走和剩余距离）。
- **`m4_control/`** (`ament_python`; needs `m4_description` from [`../urdf-tf/`](../urdf-tf/) and `m4_gazebo` from [`../gazebo-sim/`](../gazebo-sim/)):
  `urdf/m4bot_control.urdf.xacro` (the `<ros2_control>` tags, argument `hardware:=gazebo|mock`), `config/controllers.yaml` (controller manager, `diff_drive_controller`, `joint_state_broadcaster`, `head_controller`), `config/bridge.yaml` (only the clock and the sensors now), `launch/control.launch.py` (arguments `hardware:=gazebo|mock`, `headless:=true|false`, and for Lesson 6 `rviz_config:=<file>` and `drive_params:=<extra diff_drive_controller parameter file>`) and the `drive_distance` action server.
  ros2_control 包：带 `<ros2_control>` 标签的 xacro、控制器 YAML、只剩时钟和传感器的桥接配置、launch 文件（第 6 课还会用到 `rviz_config` 和 `drive_params` 两个参数），以及 `drive_distance` 动作服务器。
- **`drive_client.py <distance> <speed> [cancel after s]`**: sends one goal, prints feedback and result, optionally cancels. 发送一个目标，打印反馈和结果，可选在中途取消。
- **`diff_drive.py`**: the wheel-speed arithmetic of `diff_drive_controller` (b = 0.28 m, r = 0.05 m, checked against `m4_control/config/controllers.yaml`), plain Python, no ROS; output in `../expected/ctl-diff_drive.txt`. `diff_drive_controller` 的轮速算术（b = 0.28 m、r = 0.05 m，并与 controllers.yaml 核对），普通 Python，不需要 ROS；输出见 `../expected/ctl-diff_drive.txt`。

```bash
cp -r ../urdf-tf/m4_description ../gazebo-sim/m4_gazebo m4_control m4_drive_interfaces ~/ros2_ws/src/
cd ~/ros2_ws && colcon build && source install/setup.bash
ros2 launch m4_control control.launch.py                       # Gazebo + RViz / Gazebo + RViz
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true \
    -p use_sim_time:=true -r cmd_vel:=/diff_drive_controller/cmd_vel   # second terminal / 另开终端
python3 drive_client.py 1.0 0.2                                 # third terminal / 第三个终端
ros2 launch m4_control control.launch.py hardware:=mock headless:=true   # no simulator / 不用仿真器
```

Needs ROS 2 Jazzy with `ros-jazzy-ros2-control`, `ros-jazzy-ros2-controllers` and `ros-jazzy-gz-ros2-control`, see [`../README.md`](../README.md). These runs are real ROS 2 software driving a **simulated** robot (Gazebo, or ros2_control's mock hardware); [`../../../tools/sim/ros/run.sh`](../../../tools/sim/ros/run.sh) repeats every one the lesson quotes. The package licences are left as the `TODO` placeholder on purpose.
需要装有 `ros-jazzy-ros2-control`、`ros-jazzy-ros2-controllers` 和 `ros-jazzy-gz-ros2-control` 的 ROS 2 Jazzy，见 [`../README.md`](../README.md)。这些都是真实的 ROS 2 软件驱动**仿真**机器人（Gazebo，或 ros2_control 的 mock 硬件）；[`../../../tools/sim/ros/run.sh`](../../../tools/sim/ros/run.sh) 会重复课程引用的每一次运行。包的许可证故意保留 `TODO` 占位符。
