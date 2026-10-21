# Month 4 examples / 第 4 个月示例

One folder per lesson; each folder's README lists what it contains and how to run it. Folders hold ROS 2 packages: copy (or symlink) them into the `src/` folder of your own workspace, e.g. `~/ros2_ws/src`.
每课一个目录，目录里的 README 写明内容和运行方法。目录里是 ROS 2 包：把它们复制（或软链接）到你自己工作空间的 `src/` 下，例如 `~/ros2_ws/src`。

| Lesson / 课程 | Folder / 目录 | What / 内容 | Checked by / 验证方式 |
| --- | --- | --- | --- |
| 1 Which ROS 2, first workspace / 选哪个 ROS 2、第一个工作空间 | [`ros2-setup/`](ros2-setup/) | `m4_hello`: a first Python node / 第一个 Python 节点 | `check.sh` (real runs / 真实运行) |
| 2 Nodes, topics, services and actions / 节点、话题、服务与动作 | [`ros2-graph/`](ros2-graph/) | `m4_interfaces`, `m4_graph_cpp`, `m4_graph`: a four-node graph with msg/srv/action, launch, bag, QoS / 四节点图：msg/srv/action、launch、bag、QoS | `check.sh` (real runs / 真实运行) |
| 3 URDF and TF / URDF 与 TF | [`urdf-tf/`](urdf-tf/) | `m4_description` (m4bot in xacro), `inertia_check.py`, `pose_head.py` / m4bot 的 xacro 描述、惯量检查、云台姿态脚本 | `check.sh` (real runs / 真实运行); figures: `render_figures.sh` / 配图：`render_figures.sh` |
| 4 Simulation in Gazebo / Gazebo 仿真 | [`gazebo-sim/`](gazebo-sim/) | `m4_gazebo` (world, sensors, bridge), `scan_probe.py`, `snap_camera.py` / 世界、传感器、桥接、激光与相机脚本 | `tools/sim/ros/run.sh` (simulated robot / 仿真机器人) |
| 5 ros2_control | [`ros2-control/`](ros2-control/) | `m4_control` (`<ros2_control>` tags, controllers, `drive_distance` action server), `m4_drive_interfaces`, `drive_client.py`, `diff_drive.py` (wheel-speed arithmetic) / ros2_control 标签、控制器、开指定距离的动作服务器与客户端、轮速计算脚本 | `tools/sim/ros/run.sh` (Gazebo and mock hardware / Gazebo 与 mock 硬件); `diff_drive.py`: `check.sh` and `tools/sim/reproduce.sh` (plain Python / 普通 Python) |
| 6 SLAM and navigation / SLAM 与导航 | [`slam-nav/`](slam-nav/) | `m4_nav` (odometry calibration, SLAM Toolbox, Nav2 for m4bot), `spin_check.py`, `tour.py`, `map_check.py` / 里程计校准、SLAM Toolbox 建图与定位、Nav2 参数，转圈检查、巡游与地图检查脚本 | `tools/sim/ros/run.sh` (simulated robot / 仿真机器人) |

## Install ROS 2 Jazzy / 安装 ROS 2 Jazzy

- **Ubuntu 24.04:** the official apt packages (`ros-jazzy-desktop`, `ros-dev-tools`), as in Lesson 1, plus the packages listed in `pixi.toml` (same names with `ros-jazzy-` and dashes, e.g. `sudo apt install ros-jazzy-xacro`).
  官方 apt 包，见第 1 课；再按 `pixi.toml` 里的列表安装其余包（名字相同，例如 `sudo apt install ros-jazzy-xacro`）。
- **Any 64-bit Linux, without touching the system / 任意 64 位 Linux，不改动系统:** [pixi](https://pixi.sh) with RoboStack's packages, from this folder:
  在本目录用 pixi 安装 RoboStack 的包：

```bash
curl -fsSL https://pixi.sh/install.sh | bash
pixi install          # ROS 2 Jazzy, Gazebo Harmonic, colcon, ... (about 2 GB / 约 2 GB)
pixi run check        # = bash check.sh
pixi shell            # a shell with ros2, colcon and gz / 带 ros2、colcon、gz 的 shell
```

The site editor ran everything on Debian 13 with this `pixi.toml` (ROS 2 Jazzy from RoboStack), not on Ubuntu and not on a real robot.
本站编者在 Debian 13 上用这份 `pixi.toml`（RoboStack 的 ROS 2 Jazzy）运行了全部示例，不是在 Ubuntu 上，也没有用真机。

## Run the checks / 运行检查

```bash
examples/month-4/check.sh             # with ROS 2 Jazzy sourced, or: cd examples/month-4 && pixi run check
```

`check.sh` builds the packages in a temporary workspace, runs every command the lessons quote and compares the output with `expected/`. Timestamps, build timings and process numbers change from run to run and are masked by `compare.py`.
`check.sh` 在临时工作空间里构建这些包，运行课程中引用的每条命令，并与 `expected/` 比较。时间戳、构建耗时和进程编号每次都不同，由 `compare.py` 屏蔽。
