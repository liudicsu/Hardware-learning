# 10.4 multi-view-extrinsics

- `extrinsics_chain_toy.py` — two static cameras and one board, stdlib 4×4 maths: checks the `AX = ZB` convention of OpenCV's `calibrateRobotWorldHandEye` on exact poses, estimates cam1→cam2 from 8 noisy shared board views, then closes the chain `T_base_cam1 · T_cam1_cam2 ≈ T_base_cam2` and alarms when cam2 is bumped 2°.

```bash
python3 extrinsics_chain_toy.py    # ../expected/extrinsics_chain_toy.txt
```

Not run here / 本页未运行 (CI installs nothing extra; no second camera needed for the toy): real ChArUco capture, `solvePnP`, `calibrateRobotWorldHandEye`. Sketch only, check the current OpenCV 4.x docs:

```python
import cv2
# Rs_w2c, ts_w2c: board(world)->camera poses from solvePnP, one per robot pose
# Rs_b2g, ts_b2g: base->gripper poses (inverse of forward kinematics), same order
R_b2w, t_b2w, R_g2c, t_g2c = cv2.calibrateRobotWorldHandEye(
    Rs_w2c, ts_w2c, Rs_b2g, ts_b2g, method=cv2.CALIB_ROBOT_WORLD_HAND_EYE_SHAH)
```

For a static camera with the board on the gripper the roles swap (see the lesson); the toy checks both identities numerically.


- `corevla_training_view_restore_toy.py` — CoRe-VLA-style training-view restore under an external-camera shift (arXiv 2609.37150): a shared table of markers, a training view and a translated mount; arm A uses the shifted view as if it were the training view, arm B lifts with the correct shifted extrinsics and reprojects, arm C uses a leaked identity. Two regimes (no shift, official 0.2000 m shift), 5 seeds, common random numbers; not Ego3D, AX=ZB or AnyCamVLA. Checked by `examples/month-10/check.sh`. Real RGB-D, a point-cloud renderer and VLA weights: 本页未运行; paper figures 以论文为准.
  / CoRe-VLA 式训练视角还原：共享标记桌、训练视角与被平移的支座；A 把平移后的视图当作训练视角，B 用正确外参还原，C 使用泄漏的单位外参。两种情形，5 个种子，共用随机数。

```bash
python3 corevla_training_view_restore_toy.py
```
