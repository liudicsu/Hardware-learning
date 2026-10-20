"""pixel_to_table.py: turn a pixel into a 3D point on the table.

Uses camera.json from calibrate.py and a photo of the same checkerboard lying flat on the
table (table.png). solvePnP gives the board's pose, i.e. where the table plane is; each
pixel is then undistorted, turned into a ray and intersected with that plane. Points are
given in the camera frame (x right, y down, z forward, in mm). If truth.json
from make_views.py is there, the answers are compared with the exact ones.
Usage: python3 pixel_to_table.py <folder> [u,v ...]
"""
import json
import os
import sys

import cv2
import numpy as np

COLS, ROWS, SQ = 9, 6, 0.025


def to_plane(pixels, k, dist, rvec, tvec):
    """Pixels -> 3D points on the board plane (z = 0), in camera coordinates (m)."""
    n = cv2.undistortPoints(np.array(pixels, np.float64).reshape(-1, 1, 2), k, dist).reshape(-1, 2)
    rot, _ = cv2.Rodrigues(np.asarray(rvec, np.float64))
    t = np.asarray(tvec, np.float64).ravel()
    out = []
    for x, y in n:
        ray = rot.T @ np.array([x, y, 1.0])            # ray direction in board coordinates
        origin = -rot.T @ t                            # camera centre in board coordinates
        s = -origin[2] / ray[2]                        # where the ray reaches z = 0
        out.append(rot @ (origin + s * ray) + t)        # back into camera coordinates
    return np.array(out), np.linalg.norm(origin)


folder = sys.argv[1] if len(sys.argv) > 1 else "views"
pixels = [tuple(map(float, a.split(","))) for a in sys.argv[2:]] or [(320, 240), (420, 300), (600, 440)]
cam = json.load(open(os.path.join(folder, "camera.json")))
k, dist = np.array(cam["K"]), np.array(cam["dist"])
gray = cv2.imread(os.path.join(folder, "table.png"), cv2.IMREAD_GRAYSCALE)
found, corners = cv2.findChessboardCorners(gray, (COLS, ROWS))
corners = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
board = np.zeros((ROWS * COLS, 3), np.float32)
board[:, :2] = np.mgrid[0:COLS, 0:ROWS].T.reshape(-1, 2) * SQ
_, rvec, tvec = cv2.solvePnP(board, corners, k, dist)
pts, cam_dist = to_plane(pixels, k, dist, rvec, tvec)
flat, _ = to_plane(pixels, k, np.zeros(5), *cv2.solvePnP(board, corners, k, np.zeros(5))[1:])
truth_path = os.path.join(folder, "truth.json")
truth = json.load(open(truth_path)) if os.path.exists(truth_path) else None
if truth:
    exact, _ = to_plane(pixels, np.array(truth["K"]), np.array(truth["dist"]), truth["table_rvec"], truth["table_tvec"])
print(f"table plane from solvePnP: camera {cam_dist:.3f} m from the board origin")
print("   pixel (u, v)   3D point, camera frame (mm)    exact (mm)               error    ignoring distortion")
for i, (u, v) in enumerate(pixels):
    p = "(" + ", ".join(f"{1000 * c:6.1f}" for c in pts[i]) + ")"
    ex = "(" + ", ".join(f"{1000 * c:6.1f}" for c in exact[i]) + ")" if truth else "-"
    err = f"{1000 * np.linalg.norm(pts[i] - exact[i]):4.1f} mm" if truth else "-"
    off = f"{1000 * np.linalg.norm(flat[i] - exact[i]):5.1f} mm off" if truth else "-"
    print(f"  ({u:4.0f}, {v:4.0f})   {p}   {ex}   {err}   {off}")
