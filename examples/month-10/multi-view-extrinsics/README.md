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
