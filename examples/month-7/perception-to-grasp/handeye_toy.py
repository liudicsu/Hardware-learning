#!/usr/bin/env python3
"""Synthetic eye-in-hand AX=XB solve mirroring OpenCV calibrateHandEye I/O.

OpenCV (calib3d.hpp):
  cv2.calibrateHandEye(R_gripper2base, t_gripper2base,
                       R_target2cam, t_target2cam,
                       R_cam2gripper, t_cam2gripper,
                       method=cv2.CALIB_HAND_EYE_TSAI)
returns ^{g}T_c for eye-in-hand (camera on gripper). Docs: ≥3 poses required
(2 motions, non-parallel rotation axes); more recommended. Eye-to-hand uses the
same API with inverted gripper↔base inputs (see OpenCV hand-eye figure notes).

This toy builds noise-free synthetic poses from a known X, then recovers X with
Park & Martin’s rotation Procrustes (SVD) + LS translation — one of the methods
OpenCV lists alongside Tsai89. Needs NumPy for the 3×3 SVD (CPU-only).
"""
from __future__ import annotations

import math

import numpy as np

SEED = 17
N_POSES = 8


def se3_inv(T: np.ndarray) -> np.ndarray:
    R, t = T[:3, :3], T[:3, 3]
    Ti = np.eye(4)
    Ti[:3, :3] = R.T
    Ti[:3, 3] = -R.T @ t
    return Ti


def make_T(R: np.ndarray, t: np.ndarray) -> np.ndarray:
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    return T


def rpy(r: float, p: float, y: float) -> np.ndarray:
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Rz @ Ry @ Rx


def log_so3(R: np.ndarray) -> np.ndarray:
    tr = np.trace(R)
    cos_th = max(-1.0, min(1.0, (tr - 1.0) / 2.0))
    th = math.acos(cos_th)
    if th < 1e-10:
        return np.zeros(3)
    w = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * math.sin(th))
    return w * th


def solve_axxb_park(Ts_g2b: list[np.ndarray], Ts_t2c: list[np.ndarray]) -> np.ndarray:
    """Park94: M = Σ α βᵀ, R = U diag(1,1,det) Vᵀ from SVD(M); then LS for t."""
    alphas, betas = [], []
    As_t, Bs_t = [], []
    for i in range(len(Ts_g2b) - 1):
        A = se3_inv(Ts_g2b[i + 1]) @ Ts_g2b[i]
        B = Ts_t2c[i + 1] @ se3_inv(Ts_t2c[i])
        alphas.append(log_so3(A[:3, :3]))
        betas.append(log_so3(B[:3, :3]))
        As_t.append(A)
        Bs_t.append(B)
    M = np.zeros((3, 3))
    for a, b in zip(alphas, betas):
        M += np.outer(a, b)  # Park: R β ≈ α → M = Σ α βᵀ
    U, _, Vt = np.linalg.svd(M)
    R = U @ np.diag([1.0, 1.0, np.linalg.det(U @ Vt)]) @ Vt
    # (R_a - I) t = R t_b - t_a
    A_stack = []
    b_stack = []
    I = np.eye(3)
    for A, B in zip(As_t, Bs_t):
        A_stack.append(A[:3, :3] - I)
        b_stack.append(R @ B[:3, 3] - A[:3, 3])
    A_ls = np.vstack(A_stack)
    b_ls = np.concatenate(b_stack)
    t, *_ = np.linalg.lstsq(A_ls, b_ls, rcond=None)
    return make_T(R, t)


def rot_err_deg(Ra: np.ndarray, Rb: np.ndarray) -> float:
    R = Ra.T @ Rb
    c = max(-1.0, min(1.0, (np.trace(R) - 1.0) / 2.0))
    return math.degrees(math.acos(c))


def main() -> None:
    rng = np.random.default_rng(SEED)
    T_true = make_T(rpy(0.05, -0.12, 0.08), np.array([0.02, -0.01, 0.05]))
    T_board = make_T(rpy(0.0, 0.0, 0.3), np.array([0.35, 0.05, 0.0]))

    Ts_g2b, Ts_t2c = [], []
    for i in range(N_POSES):
        yaw = -0.4 + 0.15 * i + float(rng.uniform(-0.02, 0.02))
        pitch = 0.1 * math.sin(0.7 * i)
        roll = 0.05 * math.cos(0.5 * i)
        tg = np.array([0.20 + 0.03 * i, 0.02 * math.sin(i), 0.18 + 0.01 * i])
        # diversify rotation axes across poses (non-parallel motions)
        Tg = make_T(rpy(roll, pitch, yaw), tg)
        Ts_g2b.append(Tg)
        # target2cam = inv(cam2base) @ target2base, cam2base = g2b @ X
        T_c2b = Tg @ T_true
        T_t2c = se3_inv(T_c2b) @ T_board
        Ts_t2c.append(T_t2c)

    T_hat = solve_axxb_park(Ts_g2b, Ts_t2c)
    r_err = rot_err_deg(T_hat[:3, :3], T_true[:3, :3])
    t_err = float(np.linalg.norm(T_hat[:3, 3] - T_true[:3, 3]))

    print("handeye_toy — eye-in-hand AX=XB (Park SVD, seed=%d, poses=%d)" % (SEED, N_POSES))
    print("OpenCV twin: calibrateHandEye(..., method=CALIB_HAND_EYE_TSAI)")
    print("true_t = [%s]" % ", ".join("%.4f" % x for x in T_true[:3, 3]))
    print("hat_t  = [%s]" % ", ".join("%.4f" % x for x in T_hat[:3, 3]))
    print("rot_err_deg=%.6f  trans_err_m=%.6e" % (r_err, t_err))
    assert r_err < 0.05, "rotation error too large: %.6f deg" % r_err
    assert t_err < 1e-5, "translation error too large: %.6e m" % t_err
    print("ok: recovered cam2gripper within tolerance (noise-free synthetic)")
    print("note: eye-to-hand → pass inverted gripper/base poses into the same API")


if __name__ == "__main__":
    main()
