"""extrinsics_chain_toy.py: two static cameras, one board, one closed chain (stdlib).

Notation: T_a_b is the 4x4 pose of frame b expressed in frame a, so it maps
points written in b into a (T_base_cam1 maps cam1 points into the base frame).

1. AX = ZB identity. OpenCV's calibrateRobotWorldHandEye solves A X = Z B with
   A = cam<-world, X = world<-base, Z = cam<-gripper, B = gripper<-base
   (camera on the gripper, board = world). For a *static* camera watching a
   board on the gripper the roles swap; we only check both identities on
   exact synthetic poses here.
2. cam1 -> cam2 from shared board views. Both cameras see the same board in
   N placements; each sees it with pose noise (a stand-in for solvePnP error).
   Per view T_cam1_cam2 = T_cam1_board * inv(T_cam2_board); average them.
3. Chain closure. T_base_cam1 * T_cam1_cam2 should equal the separately
   calibrated T_base_cam2. Report the rotation (deg) and translation (mm)
   gap; alarm above the thresholds.
4. Bump. cam2 is knocked 2 deg after calibration; fresh board views now
   disagree with the stored T_base_cam2 and the check must alarm.
No numpy, no OpenCV, no camera.
"""

import math
import random

SEED = 11
N_VIEWS = 8
ROT_NOISE_DEG = 0.3   # per-view board pose noise, 1 sigma per axis
TRANS_NOISE_MM = 1.0
CAL_ROT_DEG = 0.2     # error left in each stored base->cam calibration
CAL_TRANS_MM = 2.0
ALARM_DEG = 1.0
ALARM_MM = 10.0
BUMP_DEG = 2.0
WORK_DIST_M = 0.5


def rot(axis, deg):
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    x, y, z = x / n, y / n, z / n
    a = math.radians(deg)
    c, s, v = math.cos(a), math.sin(a), 1 - math.cos(a)
    return [[c + x * x * v, x * y * v - z * s, x * z * v + y * s],
            [y * x * v + z * s, c + y * y * v, y * z * v - x * s],
            [z * x * v - y * s, z * y * v + x * s, c + z * z * v]]


def tf(r, t):
    return [r[0] + [t[0]], r[1] + [t[1]], r[2] + [t[2]], [0.0, 0.0, 0.0, 1.0]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def inv(t):
    r = [[t[j][i] for j in range(3)] for i in range(3)]
    p = [-sum(r[i][k] * t[k][3] for k in range(3)) for i in range(3)]
    return tf(r, p)


def rot_of(t):
    return [row[:3] for row in t[:3]]


def angle_deg(r):
    c = (r[0][0] + r[1][1] + r[2][2] - 1) / 2
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def gap(a, b):
    """Rotation angle (deg) and translation distance (mm) between two poses."""
    d = mul(inv(a), b)
    return angle_deg(rot_of(d)), 1000 * math.sqrt(sum(d[i][3] ** 2 for i in range(3)))


def max_abs_diff(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(4) for j in range(4))


def perturb(t, rng, rot_deg, trans_mm):
    axis = [rng.gauss(0, 1) for _ in range(3)]
    r = rot(axis, rng.gauss(0, rot_deg))
    dt = [rng.gauss(0, trans_mm / 1000) for _ in range(3)]
    return mul(tf(r, dt), t)


def quat(r):
    w = math.sqrt(max(0.0, 1 + r[0][0] + r[1][1] + r[2][2])) / 2
    return [w, (r[2][1] - r[1][2]) / (4 * w), (r[0][2] - r[2][0]) / (4 * w), (r[1][0] - r[0][1]) / (4 * w)]


def quat_to_rot(q):
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def average(poses):
    """Sign-aligned quaternion mean for rotation, plain mean for translation."""
    qs = [quat(rot_of(p)) for p in poses]
    ref = qs[0]
    acc = [0.0] * 4
    for q in qs:
        s = 1 if sum(a * b for a, b in zip(q, ref)) >= 0 else -1
        acc = [a + s * b for a, b in zip(acc, q)]
    n = math.sqrt(sum(a * a for a in acc))
    t = [sum(p[i][3] for p in poses) / len(poses) for i in range(3)]
    return tf(quat_to_rot([a / n for a in acc]), t)


# Ground truth (metres): two cameras on stands looking at the table.
def look(yaw_deg, tilt_deg, pos):
    """Camera pose in base: yaw about base z, then tilt about the camera x axis."""
    return mul(tf(rot((0, 0, 1), yaw_deg), pos), tf(rot((1, 0, 0), tilt_deg), [0, 0, 0]))


T_BASE_CAM1 = look(30, -120, [0.45, -0.30, 0.40])
T_BASE_CAM2 = look(-40, -115, [0.40, 0.35, 0.45])


def board_poses(rng):
    """N board placements on the table, in the base frame."""
    out = []
    for _ in range(N_VIEWS):
        r = rot((rng.uniform(-1, 1), rng.uniform(-1, 1), 1), rng.uniform(-25, 25))
        out.append(tf(r, [rng.uniform(0.15, 0.30), rng.uniform(-0.10, 0.10), rng.uniform(0.0, 0.05)]))
    return out


def estimate_cam1_cam2(rng, base_cam2_now):
    views = []
    for t_base_board in board_poses(rng):
        obs1 = perturb(mul(inv(T_BASE_CAM1), t_base_board), rng, ROT_NOISE_DEG, TRANS_NOISE_MM)
        obs2 = perturb(mul(inv(base_cam2_now), t_base_board), rng, ROT_NOISE_DEG, TRANS_NOISE_MM)
        views.append(mul(obs1, inv(obs2)))
    est = average(views)
    spread = max(gap(est, v)[0] for v in views)
    return est, spread


def closure(label, cal_base_cam1, cal_base_cam2, est_cam1_cam2):
    d_deg, d_mm = gap(mul(cal_base_cam1, est_cam1_cam2), cal_base_cam2)
    alarm = d_deg > ALARM_DEG or d_mm > ALARM_MM
    shift = 1000 * WORK_DIST_M * math.tan(math.radians(d_deg))
    print(f"{label:<10} {d_deg:>8.2f} {d_mm:>8.1f} {shift:>13.1f}  {'ALARM' if alarm else 'ok'}")


def main() -> None:
    rng = random.Random(SEED)
    print(f"seed={SEED}  views={N_VIEWS}  view noise {ROT_NOISE_DEG} deg / {TRANS_NOISE_MM} mm  "
          f"stored-cal error {CAL_ROT_DEG} deg / {CAL_TRANS_MM} mm")

    # 1. AX = ZB on exact poses (camera on gripper, board = world), then the static-camera swap.
    t_base_world = tf(rot((0, 0, 1), 10), [0.25, 0.0, 0.0])
    t_gripper_cam = tf(rot((1, 0, 0), 180), [0.0, 0.03, 0.05])
    worst_a = worst_b = 0.0
    for t_base_gripper in board_poses(random.Random(SEED + 1)):
        t_base_gripper = mul(t_base_gripper, tf(rot((1, 0, 0), 180), [0, 0, 0.20]))
        A = mul(inv(mul(t_base_gripper, t_gripper_cam)), t_base_world)      # cam <- world
        B = inv(t_base_gripper)                                             # gripper <- base
        X, Z = inv(t_base_world), inv(t_gripper_cam)                        # world <- base, cam <- gripper
        worst_a = max(worst_a, max_abs_diff(mul(A, X), mul(Z, B)))
        t_gripper_board = t_gripper_cam                                     # static cam1, board on gripper
        A2 = inv(mul(inv(T_BASE_CAM1), mul(t_base_gripper, t_gripper_board)))  # board <- cam1
        X2, Z2 = inv(T_BASE_CAM1), inv(t_gripper_board)                     # cam1 <- base, board <- gripper
        worst_b = max(worst_b, max_abs_diff(mul(A2, X2), mul(Z2, B)))
    print("OpenCV 4.x calib3d.hpp: calibrateRobotWorldHandEye, method SHAH=0 (default) or LI=1, needs >= 3 poses")
    print(f"AX=ZB camera-on-gripper (A=cam<-world, X=world<-base): max |AX-ZB| < 1e-12: {worst_a < 1e-12}")
    print(f"AX=ZB static camera, board on gripper (A=board<-cam, X=cam<-base): max |AX-ZB| < 1e-12: {worst_b < 1e-12}")

    # Stored calibrations carry a small error each.
    cal1 = perturb(T_BASE_CAM1, rng, CAL_ROT_DEG, CAL_TRANS_MM)
    cal2 = perturb(T_BASE_CAM2, rng, CAL_ROT_DEG, CAL_TRANS_MM)
    print(f"stored base->cam1 error: {gap(cal1, T_BASE_CAM1)[0]:.2f} deg {gap(cal1, T_BASE_CAM1)[1]:.1f} mm")
    print(f"stored base->cam2 error: {gap(cal2, T_BASE_CAM2)[0]:.2f} deg {gap(cal2, T_BASE_CAM2)[1]:.1f} mm")

    true12 = mul(inv(T_BASE_CAM1), T_BASE_CAM2)
    one, _ = estimate_cam1_cam2(random.Random(SEED + 2), T_BASE_CAM2)
    est, spread = estimate_cam1_cam2(rng, T_BASE_CAM2)
    print(f"cam1->cam2 from 1 view : {gap(one, true12)[0]:.2f} deg {gap(one, true12)[1]:.1f} mm off truth")
    print(f"cam1->cam2 mean of {N_VIEWS}: {gap(est, true12)[0]:.2f} deg {gap(est, true12)[1]:.1f} mm off truth "
          f"(worst view {spread:.2f} deg from mean)")

    print(f"closure: T_base_cam1 * T_cam1_cam2 vs T_base_cam2; alarm if > {ALARM_DEG} deg or > {ALARM_MM:.0f} mm")
    print(f"{'case':<10} {'rot_deg':>8} {'trans_mm':>8} {'shift@0.5m_mm':>13}  check")
    closure("as-built", cal1, cal2, est)
    bumped = mul(T_BASE_CAM2, tf(rot((0, 1, 0), BUMP_DEG), [0, 0, 0]))  # cam2 knocked about its own y axis
    est_b, _ = estimate_cam1_cam2(rng, bumped)
    closure(f"bump {BUMP_DEG:.0f}deg", cal1, cal2, est_b)
    print("fix after an alarm: re-run the board views and the base->cam calibration; do not patch one number.")


if __name__ == "__main__":
    main()
