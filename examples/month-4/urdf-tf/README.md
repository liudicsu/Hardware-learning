# Lesson 3: URDF and TF: describing a robot / 第 3 课：URDF 与 TF：描述一台机器人

- **`m4_description/`** (`ament_python`, no code): m4bot, a differential-drive base with a caster, a lidar, and a pan-tilt camera head on a mast. `urdf/robot.urdf.xacro` (properties, a wheel macro, separate visual and collision geometry), `urdf/inertial_macros.xacro` (box, cylinder and sphere inertia), `launch/display.launch.py` (argument `joints:=gui|zero|none`, `rviz:=true|false`) and `rviz/display.rviz`.
  m4bot 的描述包：差速底盘加万向球、激光雷达、桅杆上的云台相机；xacro 主文件（属性、轮子宏、视觉与碰撞几何分开）、惯量宏、显示用 launch 文件和 RViz 配置。
- **`inertia_check.py`**: prints mass and inertia per link and flags missing, non-positive or impossible values. 逐个连杆打印质量和惯量，标出缺失、非正或不可能的值。
- **`pose_head.py PAN TILT`**: publishes `/joint_states` with the head at exact angles (degrees), instead of the sliders. 以精确角度（度）发布 `/joint_states`，代替滑块。

```bash
cp -r m4_description ~/ros2_ws/src/
cd ~/ros2_ws && colcon build && source install/setup.bash
ros2 launch m4_description display.launch.py            # sliders + RViz / 滑块 + RViz
xacro ~/ros2_ws/src/m4_description/urdf/robot.urdf.xacro > /tmp/robot.urdf
check_urdf /tmp/robot.urdf && python3 inertia_check.py /tmp/robot.urdf
```

Needs ROS 2 Jazzy (see [`../README.md`](../README.md)). These are real runs on a computer; RViz only draws the model, there is no simulator and no robot. `../check.sh` repeats every command quoted in the lesson, and `../render_figures.sh` re-renders the two pictures in `public/m4/` (also needs graphviz, xvfb and Pillow). The package licence is left as the `TODO` placeholder on purpose.
需要 ROS 2 Jazzy（见 [`../README.md`](../README.md)）。这些都是电脑上的真实运行；RViz 只是把模型画出来，没有仿真器，也没有机器人。`../check.sh` 会重复课程里引用的每一条命令，`../render_figures.sh` 会重新渲染 `public/m4/` 里的两张图（另需 graphviz、xvfb 和 Pillow）。包的许可证故意保留 `TODO` 占位符。

## tf_buffer_time_lookup_toy.py — lookup time / 查询时间

Standard-library synthetic tf2 Buffer stand-in, no ROS needed: one pan joint at 50 Hz, a 30 Hz camera, and three lookup rules (time 0, the image stamp with a 50 ms timeout, hand-written extrapolation); five seeds, common random numbers. Expected output in `../expected/tf_buffer_time_lookup_toy.txt`, compared by `../check.sh` even without ROS. Not tf2 itself; real `ros2 run tf2_ros …` 本页未运行.
标准库合成的 tf2 缓冲区替身，不需要 ROS：50 Hz 的云台关节、30 Hz 的相机，比较三种查询规则（时间 0、带 50 ms 超时的图像时间戳、手写外推）；5 个种子，共用随机数。输出在 `../expected/tf_buffer_time_lookup_toy.txt`，没有 ROS 时 `../check.sh` 也会核对。不是 tf2 本身；真实 `ros2 run tf2_ros …` 本页未运行。

```bash
python3 tf_buffer_time_lookup_toy.py
```

## urdf_parallel_axis_inertia_toy.py — parallel-axis inertia / 平行轴惯量

Standard-library synthetic bookkeeping, no ROS needed: the lesson's chassis box (2.0 kg, 0.30 × 0.24 × 0.08 m, with a small tolerance draw) whose COM sits at an offset from the joint, and three ways to write its `<inertial>` (origin at the COM, the same matrix at the joint, the matrix moved to the joint with I = I_cm + m d²); five seeds, common random numbers. Expected output in `../expected/urdf_parallel_axis_inertia_toy.txt`, compared by `../check.sh` even without ROS. Not Gazebo; a real inertia measurement 本页未运行.
标准库合成的惯量记账，不需要 ROS：课程里的底盘盒（2.0 kg、0.30 × 0.24 × 0.08 m，带少量公差抽样），质心偏离关节一段距离，比较 `<inertial>` 的三种写法（原点在质心、同一矩阵写在关节处、用 I = I_cm + m d² 移到关节处）；5 个种子，共用随机数。输出在 `../expected/urdf_parallel_axis_inertia_toy.txt`，没有 ROS 时 `../check.sh` 也会核对。不是 Gazebo；真实惯量测量本页未运行。

```bash
python3 urdf_parallel_axis_inertia_toy.py
```
