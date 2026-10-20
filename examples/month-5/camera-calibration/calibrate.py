"""calibrate.py: calibrate a camera from photos of a 9 x 6 checkerboard with 25 mm squares.

Works on your own photos as well as on the synthetic ones from make_views.py.
Usage: python3 calibrate.py <folder with view_*.png>      writes <folder>/camera.json
"""
import glob
import json
import os
import sys

import cv2
import numpy as np

COLS, ROWS, SQ = 9, 6, 0.025

folder = sys.argv[1] if len(sys.argv) > 1 else "views"
board = np.zeros((ROWS * COLS, 3), np.float32)
board[:, :2] = np.mgrid[0:COLS, 0:ROWS].T.reshape(-1, 2) * SQ          # corner positions in m
obj_pts, img_pts, size = [], [], None
for name in sorted(glob.glob(os.path.join(folder, "view_*.png"))):
    gray = cv2.imread(name, cv2.IMREAD_GRAYSCALE)
    size = gray.shape[::-1]
    found, corners = cv2.findChessboardCorners(gray, (COLS, ROWS))
    if not found:
        print(f"  {os.path.basename(name)}: board not found, skipped")
        continue
    corners = cv2.cornerSubPix(gray, corners, (5, 5), (-1, -1),
                               (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
    obj_pts.append(board)
    img_pts.append(corners)
print(f"board found in {len(img_pts)} images of {size[0]} x {size[1]} px")

for label, flags in (("no distortion model", cv2.CALIB_FIX_K1 | cv2.CALIB_FIX_K2 | cv2.CALIB_FIX_K3 | cv2.CALIB_ZERO_TANGENT_DIST),
                     ("k1, k2 (radial)", cv2.CALIB_FIX_K3 | cv2.CALIB_ZERO_TANGENT_DIST)):
    rms, k, dist, _, _ = cv2.calibrateCamera(obj_pts, img_pts, size, None, None, flags=flags)
    print(f"{label}:")
    print(f"  reprojection error (RMS) {rms:.3f} px")
    print(f"  fx = {k[0, 0]:.1f}  fy = {k[1, 1]:.1f}  cx = {k[0, 2]:.1f}  cy = {k[1, 2]:.1f} px")
    print(f"  k1 = {dist[0, 0]:+.4f}  k2 = {dist[0, 1]:+.4f}")
with open(os.path.join(folder, "camera.json"), "w") as f:
    json.dump({"K": k.tolist(), "dist": dist.ravel().tolist(), "size": list(size)}, f)
print(f"saved {os.path.join(folder, 'camera.json')}")
