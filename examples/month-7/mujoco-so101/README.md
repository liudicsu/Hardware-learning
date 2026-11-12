# mujoco-so101

`grip_sweep.py` loads `grip_scene.xml` (a two-jaw soft-contact gripper + free cube) and sweeps
3 timesteps × 3 `solref` time constants. Soft contacts + large dt slip; penetration grows with
the time constant. The lesson maps this onto Menagerie's `robotstudio_so101` (MuJoCo ≥ 3.1.3,
Apache-2.0, 6 DoF).

```bash
$ cd ~/Hardware-learning/examples/month-7/mujoco-so101
$ python3 -m venv ~/Hardware-learning/.venv && source ~/Hardware-learning/.venv/bin/activate && python3 -m pip install mujoco  # Menagerie models need >= 3.1.3
$ python3 grip_sweep.py
# viewer on your machine (not run in the lesson page):
$ python3 -m mujoco.viewer --mjcf grip_scene.xml
```

## mujoco_integrator_energy_toy.py — integrator energy / 积分器能量

Standard-library stand-in of the explicit, semi-implicit and implicit-in-velocity updates in the MuJoCo Computation documentation. Pendulum energy drift and a tumbling spinner; stable-step test at 0.98× / 1.02× `h*` and a half step. Five seeds, common random numbers. Expected output in `../expected/mujoco_integrator_energy_toy.txt`, compared by `../check.sh` without MuJoCo. Not `mujoco.step`, not a redo of `grip_sweep`. Real MuJoCo / Menagerie 本页未运行.
标准库替身：按 MuJoCo Computation 文档里的显式、半隐式与对速度相关力隐式的更新比较能量漂移（摆与翻滚刚体）；稳定步长在 0.98× / 1.02× `h*` 与半步上测试。五个种子，共用随机数。输出在 `../expected/mujoco_integrator_energy_toy.txt`，没有 MuJoCo 时 `../check.sh` 也会核对。不是 `mujoco.step`，也不是 `grip_sweep` 的重写。真实 MuJoCo / Menagerie 本页未运行。

```bash
python3 mujoco_integrator_energy_toy.py
```
