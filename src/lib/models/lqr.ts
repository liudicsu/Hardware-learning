// Line-by-line port of part 1 (cart-pole LQR) of tools/sim/models/lqr_sim.py.
// Part 2 (MPC on the arm joint) is not part of the widget and is not ported.
// Sums use Python's compensated float sum() (Python >= 3.12), see pySum.
import { fixed } from "./format";
import { pySum } from "./pyfmt";

type Mat = number[][];

// ---------------------------------------------------------------- small matrix helpers
export function mul(a: Mat, b: Mat): Mat {
  return a.map((_, i) => b[0].map((__, j) => pySum(b.map((___, k) => a[i][k] * b[k][j]))));
}
export function add(a: Mat, b: Mat, s = 1.0): Mat {
  return a.map((row, i) => row.map((v, j) => v + s * b[i][j]));
}
export const tr = (a: Mat): Mat => a[0].map((_, j) => a.map((r) => r[j]));
export const eye = (n: number, v = 1.0): Mat =>
  Array.from({ length: n }, (_, i) => Array.from({ length: n }, (__, j) => (i === j ? v : 0.0)));

/** Zero-order-hold discretisation by a Taylor series of the matrix exponential. */
export function discretise(a: Mat, b: Mat, dt: number): [Mat, Mat] {
  const n = a.length;
  let phi = eye(n);
  let gam: Mat = b.map((x) => [dt * x[0]]);
  let term = eye(n);
  for (let k = 1; k < 25; k++) {
    term = mul(term, a).map((r) => r.map((v) => (v * dt) / k)); // (A dt)^k / k!
    phi = add(phi, term);
    gam = add(gam, mul(term, b).map((r) => r[0]).map((v) => [(v * dt) / (k + 1)]));
  }
  return [phi, gam];
}

/** Iterate P = Q + A'PA - A'PB (R + B'PB)^-1 B'PA; return K for u = -K x. */
export function lqr(phi: Mat, gam: Mat, q: Mat, r: number, iters = 5000): number[] {
  let p = q;
  let k: Mat = [[]];
  for (let it = 0; it < iters; it++) {
    const bp = mul(tr(gam), p);
    const s = r + mul(bp, gam)[0][0];
    k = [mul(bp, phi)[0].map((v) => v / s)];
    p = add(q, mul(tr(phi), mul(p, add(phi, mul(gam, k), -1.0))));
  }
  return k[0];
}

// ---------------------------------------------------------------- part 1: cart-pole
export const M = 0.5, m = 0.2, L = 0.3, G = 9.81, DT = 0.01, FMAX = 10.0;
export const A_CP: Mat = [[0, 1, 0, 0], [0, 0, (-m * G) / M, 0], [0, 0, 0, 1], [0, 0, ((M + m) * G) / (M * L), 0]];
export const B_CP: Mat = [[0], [1 / M], [0], [-1 / (M * L)]];
const radians = (x: number) => x * (Math.PI / 180);
const degrees = (x: number) => x * (180 / Math.PI);

/** Full nonlinear cart-pole (point mass m at distance L), angle from upright. */
export function cartpole(x: number[], f: number, dt = 0.001): number[] {
  const [p, v, th, w] = x;
  const s = Math.sin(th);
  const c = Math.cos(th);
  const acc = (f + m * L * w * w * s - m * G * s * c) / (M + m - m * c * c);
  const alpha = (G * s - acc * c) / L;
  return [p + v * dt, v + acc * dt, th + w * dt, w + alpha * dt];
}

export interface Balance {
  x: number[] | null;
  fpeak: number;
  log: [number, number, number, number][]; // t, position, angle (deg), force every control step
}

export function balance(k: number[], deg: number, seconds = 4.0, show: string[] | null = null, keepLog = false): Balance {
  let x = [0.0, 0.0, radians(deg), 0.0];
  let fpeak = 0.0;
  const log: Balance["log"] = [];
  const n = Math.trunc(seconds / DT);
  for (let i = 0; i < n; i++) {
    const f = Math.max(-FMAX, Math.min(FMAX, -pySum(k.map((ki, j) => ki * x[j]))));
    fpeak = Math.max(fpeak, Math.abs(f));
    if (keepLog) log.push([i * DT, x[0], degrees(x[2]), f]);
    if (show && i % 50 === 0) {
      show.push(`  t = ${fixed(i * DT, 1, 3)} s  x = ${fixed(x[0], 3, 6)} m  angle = ${fixed(degrees(x[2]), 2, 6)} deg  force = ${fixed(f, 2, 6)} N`);
    }
    for (let s = 0; s < 10; s++) x = cartpole(x, f);
    if (Math.abs(x[2]) > Math.PI / 2) return { x: null, fpeak, log };
  }
  return { x, fpeak, log };
}

export const diag4 = (qd: number[]): Mat => qd.map((v, i) => qd.map((_, j) => (i === j ? v : 0.0)));

let disc: [Mat, Mat] | null = null;
export function cartpoleDiscrete(): [Mat, Mat] {
  if (!disc) disc = discretise(A_CP, B_CP, DT);
  return disc;
}

/** The part-1 lines lqr_sim.py prints. */
export function report(): string[] {
  const out: string[] = [];
  const [phi, gam] = cartpoleDiscrete();
  out.push("Cart-pole, x = [position, speed, angle, rate], 100 Hz");
  out.push("  A (continuous) rows: " + A_CP.map((r) => "[" + r.map((v) => fixed(v, 2)).join(", ") + "]").join("  "));
  out.push("  B (continuous):      " + "[" + B_CP.map((r) => fixed(r[0], 2)).join(", ") + "]");
  let kFirst: number[] = [];
  const cases: [string, number[], number][] = [
    ["Q = diag(1, 1, 10, 1), R = 1   ", [1, 1, 10, 1], 1.0],
    ["Q = diag(100, 1, 10, 1), R = 1 ", [100, 1, 10, 1], 1.0],
    ["Q = diag(1, 1, 10, 1), R = 0.01", [1, 1, 10, 1], 0.01],
  ];
  for (const [name, qd, r] of cases) {
    const k = lqr(phi, gam, diag4(qd), r);
    out.push(`${name}  K = [` + k.map((v) => fixed(v, 2, 7)).join(", ") + "]");
    if (name.startsWith("Q = diag(1, 1, 10, 1), R = 1 ")) kFirst = k;
    const { x, fpeak } = balance(k, 10);
    out.push(`    from 10 deg: after 4 s x = ${fixed(x![0], 3, 6)} m, angle = ${fixed(degrees(x![2]), 2, 5)} deg, peak force ${fixed(fpeak, 2, 5)} N`);
  }
  out.push("Nonlinear run with the first K, starting 10 deg off upright:");
  balance(kFirst, 10, 3.0, out);
  let biggest = -Infinity;
  for (let d = 1; d < 90; d++) {
    const b = balance(kFirst, d, 6.0).x;
    if (b !== null && Math.abs(balance(kFirst, d, 6.0).x![2]) < 0.01) biggest = Math.max(biggest, d);
  }
  out.push(`  largest start angle it still recovers from (force limit ${fixed(FMAX, 0)} N): ${biggest} deg`);
  return out;
}
