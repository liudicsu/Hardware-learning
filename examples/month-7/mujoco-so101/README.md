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
