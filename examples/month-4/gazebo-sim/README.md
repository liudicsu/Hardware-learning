# Lesson 4: Simulation: your robot in Gazebo / 第 4 课：仿真：把机器人放进 Gazebo

- **`m4_gazebo/`** (`ament_python`, no code; needs `m4_description` from [`../urdf-tf/`](../urdf-tf/)): `worlds/obstacles.sdf` (a walled 6 m × 6 m room with three obstacles, no downloaded models), `urdf/m4bot_gz.urdf.xacro` (the Lesson 3 robot plus friction, a 360-beam lidar, a camera, and Gazebo's diff-drive, joint-state and joint-position plugins), `config/bridge.yaml` (`ros_gz_bridge` topics), `launch/sim.launch.py` (argument `headless:=true|false`) and `rviz/sim.rviz`.
  Gazebo 包：带三个障碍物的 6 m × 6 m 封闭房间（不下载在线模型）、在第 3 课机器人基础上加了摩擦、360 线激光雷达、相机和 Gazebo 插件的 xacro、桥接配置、launch 文件和 RViz 配置。
- **`scan_probe.py`**: averages five `/scan` messages and prints what the lidar sees (straight ahead, nearest hit). 平均五帧 `/scan`，打印正前方距离和最近障碍物。
- **`snap_camera.py [out.png]`**: saves one camera frame as a PNG (needs Pillow). 把一帧相机图像存成 PNG（需要 Pillow）。

```bash
cp -r ../urdf-tf/m4_description m4_gazebo ~/ros2_ws/src/
cd ~/ros2_ws && colcon build && source install/setup.bash
ros2 launch m4_gazebo sim.launch.py                  # Gazebo window + RViz / Gazebo 窗口 + RViz
ros2 run teleop_twist_keyboard teleop_twist_keyboard # second terminal: drive / 另开终端开车
python3 scan_probe.py                                # third terminal / 第三个终端
```

Needs ROS 2 Jazzy with `ros-jazzy-ros-gz` (Gazebo Harmonic), see [`../README.md`](../README.md). On a machine without a network connection, `export GZ_IP=127.0.0.1` first. These runs are real ROS 2 software driving a **simulated** robot; [`../../../tools/sim/ros/run.sh`](../../../tools/sim/ros/run.sh) repeats every one the lesson quotes (headless, no GPU needed), and `../render_figures.sh` re-renders the Gazebo pictures in `public/m4/`. The package licence is left as the `TODO` placeholder on purpose.
需要装有 `ros-jazzy-ros-gz`（Gazebo Harmonic）的 ROS 2 Jazzy，见 [`../README.md`](../README.md)。没有联网的机器上先 `export GZ_IP=127.0.0.1`。这些都是真实的 ROS 2 软件驱动**仿真**机器人；[`../../../tools/sim/ros/run.sh`](../../../tools/sim/ros/run.sh) 会重复课程引用的每一次运行（无界面，不需要 GPU），`../render_figures.sh` 会重新渲染 `public/m4/` 里的 Gazebo 图片。包的许可证故意保留 `TODO` 占位符。
