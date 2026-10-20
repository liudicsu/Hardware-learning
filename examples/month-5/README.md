# Month 5 examples / 第 5 个月示例

One folder per lesson; each folder's README lists what it contains and how to run it.
每课一个目录，目录里的 README 写明内容和运行方法。

| Lesson / 课程 | Folder / 目录 | What / 内容 | Checked by / 验证方式 |
| --- | --- | --- | --- |
| 1 Control theory: model, then frequency domain / 控制理论：建模与频域 | [`control-modelling/`](control-modelling/) | `joint_freq.py` (in `tools/sim/models/`): identification, Bode data, margins / 参数辨识、伯德数据、裕度 | `tools/sim/reproduce.sh` (toy model / 玩具模型) |
| 2 State space, LQR and MPC / 状态空间、LQR 与 MPC | [`state-space-lqr/`](state-space-lqr/) | `lqr_sim.py` (in `tools/sim/models/`): cart-pole LQR, MPC on the arm joint / 小车倒立摆 LQR、关节 MPC | `tools/sim/reproduce.sh` (toy model / 玩具模型) |
| 3 Kinematics: FK, numerical IK, singularities / 运动学：正解、数值逆解、奇异点 | [`kinematics-ik/`](kinematics-ik/) | `kinematics.py` (in `tools/sim/models/`) / 正运动学、阻尼最小二乘逆解、奇异点 | `tools/sim/reproduce.sh` (toy model / 玩具模型) |
| 4 Camera calibration and pixel to 3D / 相机标定与像素到三维 | [`camera-calibration/`](camera-calibration/) | `make_views.py`, `calibrate.py`, `pixel_to_table.py`: synthetic photos, OpenCV calibration, ray-plane intersection / 合成照片、OpenCV 标定、射线与平面求交 | `tools/sim/m5/run.sh` (synthetic images, real OpenCV / 合成图像、真实 OpenCV) |

## Install for Lessons 4 and 5 / 第 4、5 课的安装

Lessons 1–3 need only Python 3. Lesson 4 needs NumPy and OpenCV; Lesson 5 needs ROS 2 Jazzy with MoveIt 2. [`pixi.toml`](pixi.toml) installs all of it from RoboStack's packages on any 64-bit Linux, without touching the system:
第 1–3 课只需要 Python 3。第 4 课需要 NumPy 和 OpenCV；第 5 课需要带 MoveIt 2 的 ROS 2 Jazzy。[`pixi.toml`](pixi.toml) 在任意 64 位 Linux 上用 RoboStack 的包装好全部依赖，不改动系统：

```bash
cd examples/month-5
pixi install          # Python, NumPy, OpenCV, ROS 2 Jazzy, MoveIt 2 (about 4 GB / 约 4 GB)
pixi run sim          # = bash ../../tools/sim/m5/run.sh
pixi shell            # a shell with python3 (numpy, cv2), ros2 and MoveIt 2 / 带 python3（numpy、cv2）、ros2 与 MoveIt 2 的 shell
```

For Lesson 4 alone, `pip install numpy opencv-python` is enough. On Ubuntu 24.04, Lesson 5's packages are the apt packages with the same names (`sudo apt install ros-jazzy-moveit ros-jazzy-moveit-py ros-jazzy-moveit-resources-panda-moveit-config`, plus `ros-jazzy-ros2-control ros-jazzy-ros2-controllers`).
只做第 4 课的话，`pip install numpy opencv-python` 就够了。在 Ubuntu 24.04 上，第 5 课的依赖就是同名的 apt 包（`sudo apt install ros-jazzy-moveit ros-jazzy-moveit-py ros-jazzy-moveit-resources-panda-moveit-config`，再加 `ros-jazzy-ros2-control ros-jazzy-ros2-controllers`）。

The site editor ran everything on Debian 13 with this `pixi.toml`, not on Ubuntu and not on a real robot or camera.
本站编者在 Debian 13 上用这份 `pixi.toml` 运行了全部示例，不是在 Ubuntu 上，也没有用真机或真实相机。
