import { fixed } from "./format";

export const W = 640;
export const HEIGHT = 480;
export const FX = 500;
export const FY = 500;
export const CX = 320;
export const CY = 240;
export const K1 = -0.12;
export const K2 = 0.03;
export const COLS = 9;
export const ROWS = 6;
export const SQ = 0.025;

const DEG_TO_RAD = Math.PI / 180;

export interface Camera {
  fx: number;
  fy: number;
  cx: number;
  cy: number;
  k1: number;
  k2: number;
}

export const TRUE_CAMERA: Camera = {
  fx: FX,
  fy: FY,
  cx: CX,
  cy: CY,
  k1: K1,
  k2: K2,
};

// OpenCV projectPoints() with dist = [k1, k2, 0, 0, 0].
export function project(
  p: number[],
  cam: Camera = TRUE_CAMERA,
  ignoreDistortion = false,
): [number, number] {
  const x = p[0] / p[2];
  const y = p[1] / p[2];
  const r2 = x * x + y * y;
  const r4 = r2 * r2;
  const f = ignoreDistortion ? 1 : 1 + cam.k1 * r2 + cam.k2 * r4;
  const u = cam.fx * x * f + cam.cx;
  const v = cam.fy * y * f + cam.cy;
  return [u, v];
}

// OpenCV cv::undistortPoints() with k3 = p1 = p2 = 0 and its default 5 fixed-point iterations.
export function undistortPoint(
  u: number,
  v: number,
  cam: Camera = TRUE_CAMERA,
): [number, number] {
  const x0 = (u - cam.cx) / cam.fx;
  const y0 = (v - cam.cy) / cam.fy;
  let x = x0;
  let y = y0;
  for (let i = 0; i < 5; i++) {
    const r2 = x * x + y * y;
    const icdist = 1 / (1 + (cam.k2 * r2 + cam.k1) * r2);
    x = x0 * icdist;
    y = y0 * icdist;
  }
  return [x, y];
}

// OpenCV cv2.Rodrigues(): rotation vector to 3 x 3 rotation matrix.
export function rodrigues(r: number[]): number[][] {
  const theta = Math.sqrt(r[0] * r[0] + r[1] * r[1] + r[2] * r[2]);
  if (theta === 0) {
    return [
      [1, 0, 0],
      [0, 1, 0],
      [0, 0, 1],
    ];
  }
  const kx = r[0] / theta;
  const ky = r[1] / theta;
  const kz = r[2] / theta;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  const C = 1 - c;
  return [
    [c + kx * kx * C, kx * ky * C - kz * s, kx * kz * C + ky * s],
    [ky * kx * C + kz * s, c + ky * ky * C, ky * kz * C - kx * s],
    [kz * kx * C - ky * s, kz * ky * C + kx * s, c + kz * kz * C],
  ];
}

// Rotation about x by deg degrees, as OpenCV cv2.Rodrigues([radians(deg), 0, 0]).
export function rotX(deg: number): number[][] {
  return rodrigues([deg * DEG_TO_RAD, 0, 0]);
}

// Rotation about y by deg degrees, as OpenCV cv2.Rodrigues([0, radians(deg), 0]).
export function rotY(deg: number): number[][] {
  return rodrigues([0, deg * DEG_TO_RAD, 0]);
}

// The expected file was made with numpy's `@`, whose BLAS kernels on x86-64 round each
// multiply-add once (fused multiply-add). Plain JS `sum += a * b` rounds twice, which only
// changes the 1e-17 m rounding noise of the image-centre point, but that is enough to print
// "-0.0" instead of "0.0". fma() below is an exact (BigInt) fused multiply-add so the port
// reproduces the expected line byte for byte; it is used only by pose() and toPlane().
const BIG0 = BigInt(0);
const BIG1 = BigInt(1);
const BIG52 = BigInt(52);
const BIG53 = BigInt(53);
const BIG63 = BigInt(63);
const MASK52 = (BIG1 << BIG52) - BIG1;
const HIDDEN = BIG1 << BIG52;
const FMA_BUFFER = new ArrayBuffer(8);
const FMA_VIEW = new DataView(FMA_BUFFER);

function bitsOf(x: number): bigint {
  FMA_VIEW.setFloat64(0, x, false);
  return FMA_VIEW.getBigUint64(0, false);
}

function decompose(x: number): [bigint, number] {
  const bits = bitsOf(x);
  const negative = (bits >> BIG63) !== BIG0;
  const exponent = Number((bits >> BIG52) & BigInt(0x7ff));
  const fraction = bits & MASK52;
  let mantissa: bigint;
  let power: number;
  if (exponent === 0) {
    mantissa = fraction;
    power = -1074;
  } else {
    mantissa = fraction + HIDDEN;
    power = exponent - 1075;
  }
  if (negative) {
    mantissa = -mantissa;
  }
  return [mantissa, power];
}

function bitLength(value: bigint): number {
  let n = 0;
  let x = value;
  while (x > BIG0) {
    x >>= BIG1;
    n++;
  }
  return n;
}

function fma(a: number, b: number, c: number): number {
  if (!Number.isFinite(a) || !Number.isFinite(b) || !Number.isFinite(c)) {
    return a * b + c;
  }
  const [ma, ea] = decompose(a);
  const [mb, eb] = decompose(b);
  const [mc, ec] = decompose(c);
  const productMantissa = ma * mb;
  const productPower = ea + eb;
  const power = Math.min(productPower, ec);
  const sum = (productMantissa << BigInt(productPower - power)) +
    (mc << BigInt(ec - power));
  if (sum === BIG0) {
    return 0;
  }
  const negative = sum < BIG0;
  let mantissa = negative ? -sum : sum;
  let finalPower = power;
  const length = bitLength(mantissa);
  if (length > 53) {
    const shift = BigInt(length - 53);
    let rounded = mantissa >> shift;
    const rest = mantissa - (rounded << shift);
    const half = BIG1 << (shift - BIG1);
    if (rest > half || (rest === half && (rounded & BIG1) === BIG1)) {
      rounded += BIG1;
    }
    mantissa = rounded;
    finalPower = power + (length - 53);
  } else if (length < 53) {
    mantissa <<= BigInt(53 - length);
    finalPower = power - (53 - length);
  }
  if (mantissa >= (BIG1 << BIG53)) {
    mantissa >>= BIG1;
    finalPower += 1;
  }
  const unbiased = finalPower + 52;
  if (unbiased > 1023) {
    return negative ? -Infinity : Infinity;
  }
  let bits: bigint;
  if (unbiased >= -1022) {
    bits = (BigInt(unbiased + 1023) << BIG52) | (mantissa - HIDDEN);
  } else {
    const shift = BigInt(-(finalPower + 1074));
    let fraction = mantissa >> shift;
    const rest = mantissa - (fraction << shift);
    const half = BIG1 << (shift - BIG1);
    if (rest > half || (rest === half && (fraction & BIG1) === BIG1)) {
      fraction += BIG1;
    }
    bits = fraction >= (BIG1 << BIG52) ? BIG1 << BIG52 : fraction;
  }
  if (negative) {
    bits |= BIG1 << BIG63;
  }
  FMA_VIEW.setBigUint64(0, bits, false);
  return FMA_VIEW.getFloat64(0, false);
}

function matMul3(a: number[][], b: number[][]): number[][] {
  const out: number[][] = [];
  for (let i = 0; i < 3; i++) {
    const row: number[] = [];
    for (let j = 0; j < 3; j++) {
      let sum = 0;
      for (let k = 0; k < 3; k++) {
        sum = fma(a[i][k], b[k][j], sum);
      }
      row.push(sum);
    }
    out.push(row);
  }
  return out;
}

function matVec3(a: number[][], v: number[]): number[] {
  const out: number[] = [];
  for (let i = 0; i < 3; i++) {
    let sum = 0;
    for (let k = 0; k < 3; k++) {
      sum = fma(a[i][k], v[k], sum);
    }
    out.push(sum);
  }
  return out;
}

function matTVec3(a: number[][], v: number[]): number[] {
  const out: number[] = [];
  for (let i = 0; i < 3; i++) {
    let sum = 0;
    for (let k = 0; k < 3; k++) {
      sum = fma(a[k][i], v[k], sum);
    }
    out.push(sum);
  }
  return out;
}

// Python make_views.pose().
export function pose(
  tiltX: number,
  tiltY: number,
  dist: number,
  shiftX: number,
  shiftY: number,
): { rot: number[][]; tvec: number[] } {
  const rot = matMul3(rotX(tiltX), rotY(tiltY));
  const centre = [((COLS - 1) * SQ) / 2, ((ROWS - 1) * SQ) / 2, 0];
  const rotated = matVec3(rot, centre);
  const tvec = [shiftX - rotated[0], shiftY - rotated[1], dist - rotated[2]];
  return { rot, tvec };
}

export const TABLE = pose(40, 0, 0.45, 0, 0);

// Python pixel_to_table.to_plane() for one pixel; returns metres in the camera frame.
export function toPlane(
  u: number,
  v: number,
  cam: Camera = TRUE_CAMERA,
  rot: number[][] = TABLE.rot,
  tvec: number[] = TABLE.tvec,
): number[] {
  const n = undistortPoint(u, v, cam);
  const ray = matTVec3(rot, [n[0], n[1], 1.0]);
  const cameraCentre = matTVec3(rot, tvec);
  const origin = [-cameraCentre[0], -cameraCentre[1], -cameraCentre[2]];
  const s = -origin[2] / ray[2];
  const onPlane = [origin[0] + s * ray[0], origin[1] + s * ray[1], origin[2] + s * ray[2]];
  const inCamera = matVec3(rot, onPlane);
  return [inCamera[0] + tvec[0], inCamera[1] + tvec[1], inCamera[2] + tvec[2]];
}

// Python pixel_to_table.py's data-line pixel and "exact (mm)" columns.
export function pixelReport(
  pixels: [number, number][] = [[320, 240], [420, 300], [600, 440]],
): string[] {
  return pixels.map(([u, v]) => {
    const p = toPlane(u, v);
    const exact =
      "(" + [p[0] * 1000, p[1] * 1000, p[2] * 1000].map((c) => fixed(c, 1, 6)).join(", ") + ")";
    return "  (" + fixed(u, 0, 4) + ", " + fixed(v, 0, 4) + ")   " + exact;
  });
}
