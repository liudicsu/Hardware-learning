# Lesson 4: camera calibration and pixel to 3D / 第 4 课：相机标定与像素到三维

Three scripts, run in order. They need Python 3 with NumPy and OpenCV (`cv2`); `pixi shell` in [`../`](../) provides both.
三个脚本，按顺序运行。需要带 NumPy 和 OpenCV（`cv2`）的 Python 3；在 [`../`](../) 里执行 `pixi shell` 就有。

```bash
cd examples/month-5/camera-calibration
python3 make_views.py views        # 15 synthetic checkerboard photos, table.png, truth.json / 15 张合成棋盘格照片、table.png、truth.json
python3 calibrate.py views         # calibrateCamera with and without k1, k2; writes views/camera.json / 有无 k1、k2 两次标定，写出 views/camera.json
python3 pixel_to_table.py views    # solvePnP on table.png, then three pixels to 3D points on the table / 对 table.png 做 solvePnP，再把三个像素换成桌面上的三维点
```

- `make_views.py` renders the photos through a known camera (fx = fy = 500 px, centre (320, 240), k1 = -0.12, k2 = 0.03, 640 × 480) and a 9 × 6 inner-corner board with 25 mm squares, so the calibration can be compared with the truth.
  用一台已知参数的相机（fx = fy = 500 px、主点 (320, 240)、k1 = -0.12、k2 = 0.03、640 × 480）和 9 × 6 内角点、25 mm 方格的棋盘格渲染照片，这样标定结果可以和真值对比。
- `calibrate.py` does not depend on the generator: put your own photos in a folder as `view_*.png` and it calibrates your camera. Change `COLS, ROWS, SQ` if your board differs (`SQ` in metres).
  `calibrate.py` 不依赖生成器：把你自己的照片以 `view_*.png` 命名放进一个目录，它就能标定你的相机。棋盘格不同时修改 `COLS, ROWS, SQ`（`SQ` 以米为单位）。
- `pixel_to_table.py` compares its 3D points with `truth.json` when that file exists; with your own `table.png` (and no `truth.json`) it only prints the points. Edit the pixel list to your own pixels.
  `pixel_to_table.py` 在 `truth.json` 存在时会和它比较；换成你自己的 `table.png`（没有 `truth.json`）时只打印三维点。把像素列表改成你自己的像素即可。

Output quoted in the lesson as **simulated output / 仿真输出** (synthetic photos, real OpenCV); checked by `tools/sim/m5/run.sh` against `tools/sim/expected/m5-cam_views.txt`, `m5-cam_calibrate.txt` and `m5-cam_pixel.txt`. The `views/` folder is ignored by git.
课程中以“仿真输出”引用（合成照片，真实的 OpenCV）；由 `tools/sim/m5/run.sh` 与 `tools/sim/expected/m5-cam_views.txt`、`m5-cam_calibrate.txt`、`m5-cam_pixel.txt` 比对。`views/` 目录已被 git 忽略。
