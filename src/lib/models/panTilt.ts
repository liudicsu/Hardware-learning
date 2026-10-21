// The pan/tilt chain base_link -> camera_link from
// examples/month-4/urdf-tf/m4_description/urdf/robot.urdf.xacro, printed the way
// `ros2 run tf2_ros tf2_echo base_link camera_link` prints it.
// There is no Python script for this lesson: the model is the URDF's joint origins and
// axes, composed as quaternions (as TF does), and the quaternion -> matrix -> RPY steps
// follow tf2::Matrix3x3 (setRotation, getEulerYPR) so the signs of zeros match.
import { fixed } from "./format";

export type V3 = [number, number, number];
export type Q = [number, number, number, number]; // x, y, z, w

// robot.urdf.xacro: chassis_z 0.08, chassis_top = chassis_z - 0.01, mast_height 0.20
const CHASSIS_TOP = 0.08 - 0.01;
const MAST_HEIGHT = 0.2;
export const MAST: V3 = [-0.06, 0, CHASSIS_TOP]; // mast_joint origin
export const PAN: V3 = [0, 0, MAST_HEIGHT]; // pan_joint origin, axis z
export const TILT: V3 = [0, 0, 0.035]; // tilt_joint origin, axis y
export const CAMERA: V3 = [0.02, 0, 0]; // camera_joint origin

const qAxis = (axis: V3, angle: number): Q => {
  const s = Math.sin(angle / 2);
  return [axis[0] * s, axis[1] * s, axis[2] * s, Math.cos(angle / 2)];
};

function qMul(a: Q, b: Q): Q {
  const [ax, ay, az, aw] = a;
  const [bx, by, bz, bw] = b;
  return [
    aw * bx + ax * bw + ay * bz - az * by,
    aw * by + ay * bw + az * bx - ax * bz,
    aw * bz + az * bw + ax * by - ay * bx,
    aw * bw - ax * bx - ay * by - az * bz,
  ];
}

/** tf2::Matrix3x3::setRotation(quaternion). */
export function matrix(q: Q): number[][] {
  const [x, y, z, w] = q;
  const d = x * x + y * y + z * z + w * w;
  const s = 2 / d;
  const xs = x * s, ys = y * s, zs = z * s;
  const wx = w * xs, wy = w * ys, wz = w * zs;
  const xx = x * xs, xy = x * ys, xz = x * zs;
  const yy = y * ys, yz = y * zs, zz = z * zs;
  return [
    [1 - (yy + zz), xy - wz, xz + wy],
    [xy + wz, 1 - (xx + zz), yz - wx],
    [xz - wy, yz + wx, 1 - (xx + yy)],
  ];
}

const rotate = (m: number[][], v: V3): V3 => [
  m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
  m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
  m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
];
const add = (a: V3, b: V3): V3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];

/** tf2::Matrix3x3::getRPY (getEulerYPR, solution 1). */
export function rpy(m: number[][]): V3 {
  if (Math.abs(m[2][0]) >= 1) {
    const yaw = 0;
    if (m[2][0] < 0) return [Math.atan2(m[0][1], m[0][2]), Math.PI / 2, yaw];
    return [Math.atan2(-m[0][1], -m[0][2]), -Math.PI / 2, yaw];
  }
  const pitch = -Math.asin(m[2][0]);
  const c = Math.cos(pitch);
  return [Math.atan2(m[2][1] / c, m[2][2] / c), pitch, Math.atan2(m[1][0] / c, m[0][0] / c)];
}

export interface Transform {
  t: V3;
  q: Q;
  m: number[][];
  rpy: V3;
}

/** base_link -> camera_link for the given pan and tilt angles (radians). */
export function cameraTransform(pan: number, tilt: number): Transform {
  // base -> mast: translation only; mast -> pan: translate then rotate about z
  const qPan = qAxis([0, 0, 1], pan);
  const qTilt = qAxis([0, 1, 0], tilt);
  const mPan = matrix(qPan);
  const q = qMul(qPan, qTilt);
  const m = matrix(q);
  // origin of tilt_link, then camera_link offset in the tilted frame
  let t = add(MAST, PAN);
  t = add(t, rotate(mPan, TILT));
  t = add(t, rotate(m, CAMERA));
  return { t, q, m, rpy: rpy(m) };
}

const list = (v: number[]) => "[" + v.map((x) => fixed(x, 3)).join(", ") + "]";

/** What tf2_echo prints after its "At time ..." line. */
export function echo(tr: Transform): string[] {
  const deg = tr.rpy.map((a) => (a * 180) / Math.PI);
  const out = [
    `- Translation: ${list(tr.t)}`,
    `- Rotation: in Quaternion (xyzw) ${list(tr.q)}`,
    `- Rotation: in RPY (radian) ${list(tr.rpy)}`,
    `- Rotation: in RPY (degree) ${list(deg)}`,
    "- Matrix:",
  ];
  const rows = [
    [...tr.m[0], tr.t[0]],
    [...tr.m[1], tr.t[1]],
    [...tr.m[2], tr.t[2]],
    [0, 0, 0, 1],
  ];
  for (const r of rows) out.push(r.map((x) => fixed(x, 3, 7)).join(""));
  return out;
}

/** The expected file is pan 30°, tilt 0. */
export function report(): string[] {
  return echo(cameraTransform((30 * Math.PI) / 180, 0));
}
