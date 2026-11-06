# Month 5 current plan / 第5个月当前计划

Current / 当前：M5 **1950 min** (Batch-7 PR2). Older batch entries retain historical totals.

Batch-5 PR2 base e5ac703 (20310). Historical observability additions remain in month-5-followup-pr3.md.

| Host | Before | After PR2 | Addition |
|---|---:|---:|---|
| 5.4 camera-calibration | 240 | 420 | stereo_depth_sigma_toy (+180) |
| M5 total,5 lessons | 1620 | 1800 | Other lessons unchanged / 其他课不变 |

f pixels,B metres,sigma_d pixels;shared depths/disparity noise;MC sigma/bias vs linearization,quantization and exact bounded-noise expectation. Long baseline min-range/occlusion cost;not hand-eye,multi-view extrinsics or3DGS. / 单位一致，共享输入，对照 MC 与线性化，解释量化、非线性偏差和长基线代价，不重做手眼。

All new sections/code/stdout/exercises before final Summary. Existing5.4 had no Summary in either language;add final bilingual Summary with legacy intrinsics/undistortion reminder plus new stereo sentence. Real rectification/matching 本页未运行.

This PR:20310+180+210=**20700**,71 lessons,M5=1800,M9=2550;M1/M2/M3 remain870/1650/1470. / 不提前计入本批 PR3。

## Batch-7 PR2 / 本月 H4 (+150)

5.3 kinematics-ik240→390; M5 **1800→1950**, five lessons. This PR only: site **22830→23190**, M4 **1620→1830** (+210), still71 lessons. No arithmetic mismatch or PR3 allocation.

Allocation:30+30+45+30+15=150 min (explicit ZYX/body Jacobian / gimbal rank and shared crossing / equal-endpoint interpolation / double-cover+norm / exercises). Existing SO-101 planar FK sign, position Jacobian, damped IK and checks remain unchanged. Added full final whole-lesson Summary in both languages because neither had one; all new code/stdout/exercises before it. New stdlib expected/harness entry; no robot/IMU/ROS run. Sources: batch-7-pr2-sources.md.
