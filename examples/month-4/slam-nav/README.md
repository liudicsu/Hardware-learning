# Lesson 6: SLAM and navigation / 第 6 课：SLAM 与导航

- **`m4_nav/`** (`ament_python`; needs `m4_control` and `m4_drive_interfaces` from [`../ros2-control/`](../ros2-control/), `m4_gazebo` from [`../gazebo-sim/`](../gazebo-sim/) and `m4_description` from [`../urdf-tf/`](../urdf-tf/)):
  `config/odom_calibration.yaml` (`wheel_separation_multiplier` found with `spin_check.py`), `config/slam.yaml` and `config/slam_localization.yaml` (SLAM Toolbox in mapping and localization mode), `config/nav2.yaml` (Nav2 for m4bot; the m4bot-specific lines are marked), `launch/slam.launch.py` (Lesson 5's robot + SLAM Toolbox mapping), `launch/nav.launch.py` (argument `map:=<pose graph without .posegraph>`: Lesson 5's robot + SLAM Toolbox localization + Nav2), `rviz/nav.rviz`.
  导航包：里程计校准参数、SLAM Toolbox 建图与定位两种模式的参数、m4bot 的 Nav2 参数（专门为 m4bot 改的行已标注）、建图 launch 文件和导航 launch 文件（参数 `map:=<不带 .posegraph 的位姿图路径>`），以及 RViz 配置。
- **`spin_check.py`**: turns the robot one full turn by odometry and measures the real angle with the lidar. 按里程计原地转一整圈，再用激光雷达测出真实转了多少。
- **`tour.py`**: drives a fixed tour of the obstacles room so SLAM Toolbox sees every corner (a repeatable stand-in for teleop). 按固定路线开遍障碍物房间，让 SLAM Toolbox 扫到每个角落（可重复的遥控替代品）。
- **`map_check.py <map.yaml>`**: reads a saved map (standard library only) and checks the walls and obstacles are where the world put them. 读取保存的地图（只用标准库），检查墙和障碍物是否在世界文件里的位置。

```bash
cp -r ../urdf-tf/m4_description ../gazebo-sim/m4_gazebo ../ros2-control/m4_control \
      ../ros2-control/m4_drive_interfaces m4_nav ~/ros2_ws/src/
cd ~/ros2_ws && colcon build && source install/setup.bash
ros2 launch m4_nav slam.launch.py                                # mapping, Gazebo + RViz / 建图
python3 spin_check.py && python3 tour.py                         # second terminal / 另开终端
mkdir -p ~/maps
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '$HOME/maps/room'}"
ros2 run nav2_map_server map_saver_cli -f ~/maps/room --ros-args -p use_sim_time:=true
python3 map_check.py ~/maps/room.yaml
# stop slam.launch.py, then / 停掉 slam.launch.py 后：
ros2 launch m4_nav nav.launch.py map:=$HOME/maps/room            # localization + Nav2 / 定位 + 导航
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
    "{pose: {header: {frame_id: map}, pose: {position: {x: 2.0, y: -2.0}, orientation: {w: 1.0}}}}"
```

Needs ROS 2 Jazzy with `ros-jazzy-slam-toolbox` and `ros-jazzy-nav2-bringup` on top of Lesson 5's packages, see [`../README.md`](../README.md). These runs are real ROS 2 software driving a **simulated** robot in Gazebo; [`../../../tools/sim/ros/run.sh`](../../../tools/sim/ros/run.sh) repeats every one the lesson quotes. The package licence is left as the `TODO` placeholder on purpose.
需要在第 5 课的基础上再装 `ros-jazzy-slam-toolbox` 和 `ros-jazzy-nav2-bringup` 的 ROS 2 Jazzy，见 [`../README.md`](../README.md)。这些都是真实的 ROS 2 软件驱动 Gazebo 里的**仿真**机器人；[`../../../tools/sim/ros/run.sh`](../../../tools/sim/ros/run.sh) 会重复课程引用的每一次运行。包的许可证故意保留 `TODO` 占位符。
