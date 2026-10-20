"""make_views.py: render synthetic photos of a checkerboard through a known, distorted camera.

The "true" camera is a 640 x 480 webcam-like pinhole: fx = fy = 500 px, centre (320, 240),
radial distortion k1 = -0.12, k2 = 0.03. The board has 9 x 6 inner corners on 25 mm
squares. Fifteen views at different distances and tilts, plus table.png: the board lying
flat on a table, seen from 0.45 m above at an angle. Usage: python3 make_views.py <dir>
"""
import json
import math
import os
import sys

import cv2
import numpy as np

W, H = 640, 480
K = np.array([[500.0, 0, 320], [0, 500.0, 240], [0, 0, 1]])
DIST = np.array([-0.12, 0.03, 0.0, 0.0, 0.0])
COLS, ROWS, SQ = 9, 6, 0.025                    # inner corners, square size in m


def render(rvec, tvec, rng):
    """For every pixel: undo the lens, cast the ray onto the board plane, read the colour."""
    u, v = np.meshgrid(np.arange(W, dtype=np.float64), np.arange(H, dtype=np.float64))
    img = np.zeros((H, W))
    rot, _ = cv2.Rodrigues(rvec)
    h_inv = np.linalg.inv(np.column_stack([rot[:, 0], rot[:, 1], tvec]))
    for du, dv in ((-0.25, -0.25), (0.25, -0.25), (-0.25, 0.25), (0.25, 0.25)):   # 4x supersampling
        pts = np.stack([(u + du).ravel(), (v + dv).ravel()], axis=1).reshape(-1, 1, 2)
        n = cv2.undistortPoints(pts, K, DIST).reshape(-1, 2)
        b = h_inv @ np.vstack([n.T, np.ones(len(n))])
        x, y = b[0] / b[2], b[1] / b[2]                                            # metres on the board
        i, j = np.floor(x / SQ) + 1, np.floor(y / SQ) + 1
        on = (i >= 0) & (i <= COLS) & (j >= 0) & (j <= ROWS)
        white = ((i + j) % 2 == 0) | ~on
        img += np.where(white, 230.0, 25.0).reshape(H, W) / 4
    img += rng.normal(0, 2.0, img.shape)                                           # sensor noise
    return np.clip(img, 0, 255).astype(np.uint8)


def pose(tilt_x, tilt_y, dist, shift_x, shift_y):
    """Board centred in front of the camera at `dist` m, tilted by the given degrees."""
    rot = cv2.Rodrigues(np.array([math.radians(tilt_x), 0, 0]))[0] @ cv2.Rodrigues(np.array([0, math.radians(tilt_y), 0]))[0]
    centre = np.array([(COLS - 1) * SQ / 2, (ROWS - 1) * SQ / 2, 0])
    tvec = np.array([shift_x, shift_y, dist]) - rot @ centre
    return cv2.Rodrigues(rot)[0].ravel(), tvec


def main(out):
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(5)
    views = [(0, 0, 0.30, 0, 0), (25, 0, 0.32, 0, 0), (-25, 0, 0.32, 0, 0), (0, 25, 0.32, 0, 0),
             (0, -25, 0.32, 0, 0), (20, 20, 0.35, 0.05, 0.03), (-20, 20, 0.35, -0.05, 0.03),
             (20, -20, 0.35, 0.05, -0.03), (-20, -20, 0.35, -0.05, -0.03), (10, 0, 0.27, 0.07, 0.05),
             (-10, 0, 0.30, -0.04, -0.03), (0, 10, 0.30, 0.04, -0.03), (0, -10, 0.30, -0.04, 0.03),
             (35, 10, 0.40, 0, 0), (-10, 35, 0.40, 0, 0)]
    for k, v in enumerate(views):
        rvec, tvec = pose(*v)
        cv2.imwrite(os.path.join(out, f"view_{k:02d}.png"), render(rvec, tvec, rng))
    rvec, tvec = pose(40, 0, 0.45, 0, 0)            # the board flat on the table, camera above
    cv2.imwrite(os.path.join(out, "table.png"), render(rvec, tvec, rng))
    with open(os.path.join(out, "truth.json"), "w") as f:
        json.dump({"K": K.tolist(), "dist": DIST.tolist(), "table_rvec": rvec.tolist(), "table_tvec": tvec.tolist()}, f)
    print(f"wrote {len(views)} views, table.png and truth.json to {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "views")
