import { exp, fixed, int } from "./format";

export const H = 0.05;
export const L1 = 0.12;
export const L2 = 0.14;

const DEG_TO_RAD = Math.PI / 180;
const RAD_TO_DEG = 180 / Math.PI;

// Python sum(): CPython's compensated (Neumaier) summation for floats.
function pySum(values: number[]): number {
  let sum = 0.0;
  let compensation = 0.0;
  for (const value of values) {
    const t = sum + value;
    if (Math.abs(sum) >= Math.abs(value)) {
      compensation += (sum - t) + value;
    } else {
      compensation += (value - t) + sum;
    }
    sum = t;
  }
  return sum + compensation;
}

// Python kinematics.rot_z().
export function rotZ(a: number): number[][] {
  const c = Math.cos(a);
  const s = Math.sin(a);
  return [
    [c, -s, 0, 0],
    [s, c, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
  ];
}

// Python kinematics.rot_y().
export function rotY(a: number): number[][] {
  const c = Math.cos(a);
  const s = Math.sin(a);
  return [
    [c, 0, -s, 0],
    [0, 1, 0, 0],
    [s, 0, c, 0],
    [0, 0, 0, 1],
  ];
}

// Python kinematics.trans().
export function trans(x: number, y: number, z: number): number[][] {
  return [
    [1, 0, 0, x],
    [0, 1, 0, y],
    [0, 0, 1, z],
    [0, 0, 0, 1],
  ];
}

// Python kinematics.mul().
export function mul(a: number[][], b: number[][]): number[][] {
  const out: number[][] = [];
  for (let i = 0; i < 4; i++) {
    const row: number[] = [];
    for (let j = 0; j < 4; j++) {
      const products: number[] = [];
      for (let k = 0; k < 4; k++) {
        products.push(a[i][k] * b[k][j]);
      }
      row.push(pySum(products));
    }
    out.push(row);
  }
  return out;
}

// Python kinematics.fk().
export function fk(q: number[]): number[] {
  let t = mul(rotZ(q[0]), trans(0, 0, H));
  t = mul(t, mul(rotY(q[1]), trans(L1, 0, 0)));
  t = mul(t, mul(rotY(q[2]), trans(L2, 0, 0)));
  return [t[0][3], t[1][3], t[2][3]];
}

// Python kinematics.jacobian().
export function jacobian(q: number[], h = 1e-6): number[][] {
  const p = fk(q);
  const cols: number[][] = [];
  for (let i = 0; i < 3; i++) {
    const dq = q.slice();
    dq[i] += h;
    const moved = fk(dq);
    cols.push(moved.map((a, k) => (a - p[k]) / h));
  }
  const out: number[][] = [];
  for (let i = 0; i < 3; i++) {
    const row: number[] = [];
    for (let j = 0; j < 3; j++) {
      row.push(cols[j][i]);
    }
    out.push(row);
  }
  return out;
}

// Python kinematics.det3().
export function det3(m: number[][]): number {
  return (
    m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
    m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) +
    m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
  );
}

// Python kinematics.solve3().
export function solve3(a: number[][], b: number[]): number[] {
  const d = det3(a);
  const out: number[] = [];
  for (let i = 0; i < 3; i++) {
    const m = a.map((row) => row.slice());
    for (let r = 0; r < 3; r++) {
      m[r][i] = b[r];
    }
    out.push(det3(m) / d);
  }
  return out;
}

// Python kinematics.dls_step().
export function dlsStep(q: number[], err: number[], lam: number): number[] {
  const j = jacobian(q);
  const jjt: number[][] = [];
  for (let r = 0; r < 3; r++) {
    const row: number[] = [];
    for (let c = 0; c < 3; c++) {
      const products: number[] = [];
      for (let k = 0; k < 3; k++) {
        products.push(j[r][k] * j[c][k]);
      }
      row.push(pySum(products) + (r === c ? lam * lam : 0));
    }
    jjt.push(row);
  }
  const y = solve3(jjt, err);
  const out: number[] = [];
  for (let i = 0; i < 3; i++) {
    const products: number[] = [];
    for (let k = 0; k < 3; k++) {
      products.push(j[k][i] * y[k]);
    }
    out.push(pySum(products));
  }
  return out;
}

// Python kinematics.wrap().
export function wrap(a: number): number {
  return Math.atan2(Math.sin(a), Math.cos(a));
}

export interface IkStep {
  q: number[];
  dist: number;
}

export interface IkResult {
  q: number[];
  it: number;
  dist: number;
  path: IkStep[];
}

// Python kinematics.ik(), recording the iterations that show=True prints.
export function ik(
  target: number[],
  q: number[],
  lam = 0.03,
  tol = 1e-5,
  maxStep = 0.02,
): IkResult {
  let current = q.slice();
  let it = 0;
  let dist = 0;
  const path: IkStep[] = [];
  for (let step = 0; step < 200; step++) {
    it = step;
    const p = fk(current);
    const err: number[] = [];
    const squares: number[] = [];
    for (let k = 0; k < 3; k++) {
      const e = target[k] - p[k];
      err.push(e);
      squares.push(e * e);
    }
    dist = Math.sqrt(pySum(squares));
    path.push({ q: current.slice(), dist });
    if (dist < tol) {
      break;
    }
    const scale = Math.min(1.0, maxStep / dist);
    const scaled = err.map((e) => e * scale);
    const dq = dlsStep(current, scaled, lam);
    current = current.map((a, i) => wrap(a + dq[i]));
  }
  return { q: current, it, dist, path };
}

// Python kinematics.det3(jacobian(q)) helper used by the report.
export function detJ(q: number[]): number {
  return det3(jacobian(q));
}

// Python round(x, digits): round-half-even on the exact binary value.
function roundHalfEven(x: number, digits: number): number {
  if (!Number.isFinite(x)) {
    return x;
  }
  const sign = x < 0 || Object.is(x, -0) ? -1 : 1;
  const ax = Math.abs(x);
  const text = ax.toFixed(20);
  const dot = text.indexOf(".");
  const intPart = dot >= 0 ? text.slice(0, dot) : text;
  const frac = dot >= 0 ? text.slice(dot + 1) : "";
  if (digits >= frac.length) {
    return x;
  }
  const kept = (intPart + frac.slice(0, digits)).split("");
  const firstDropped = frac.charCodeAt(digits);
  const rest = frac.slice(digits + 1);
  let roundUp = false;
  if (firstDropped > 53) {
    roundUp = true;
  } else if (firstDropped === 53) {
    if (/[1-9]/.test(rest)) {
      roundUp = true;
    } else {
      roundUp = (kept[kept.length - 1].charCodeAt(0) - 48) % 2 === 1;
    }
  }
  if (roundUp) {
    let i = kept.length - 1;
    while (i >= 0) {
      const d = kept[i].charCodeAt(0) - 48;
      if (d < 9) {
        kept[i] = String.fromCharCode(49 + d);
        break;
      }
      kept[i] = "0";
      i--;
    }
    if (i < 0) {
      kept.unshift("1");
    }
  }
  const all = kept.join("");
  const cut = all.length - digits;
  const value =
    cut > 0
      ? Number(all.slice(0, cut) + (digits > 0 ? "." + all.slice(cut) : ""))
      : Number("0." + "0".repeat(-cut) + all);
  return sign * value;
}

// Python kinematics.show_fk().
function showFk(): string[] {
  const q = [30 * DEG_TO_RAD, 45 * DEG_TO_RAD, -60 * DEG_TO_RAD];
  const p = fk(q);
  const r = L1 * Math.cos(q[1]) + L2 * Math.cos(q[1] + q[2]);
  const z = H + L1 * Math.sin(q[1]) + L2 * Math.sin(q[1] + q[2]);
  return [
    "Forward kinematics, q = [30, 45, -60] deg",
    "  by hand: reach r = " + fixed(r, 4) +
      " m, height z = " + fixed(z, 4) +
      " m, x = r cos 30 = " + fixed(r * Math.cos(q[0]), 4) +
      ", y = r sin 30 = " + fixed(r * Math.sin(q[0]), 4),
    "  transforms: tip = (" + fixed(p[0], 4) + ", " + fixed(p[1], 4) + ", " + fixed(p[2], 4) + ") m",
  ];
}

// Python kinematics.show_ik().
function showIk(): string[] {
  const target = [0.10, 0.15, 0.12];
  const lines: string[] = [
    "Numerical IK to (" + fixed(target[0], 2) + ", " + fixed(target[1], 2) + ", " + fixed(target[2], 2) +
      ") m from q = [0, 30, -30] deg",
  ];
  const first = ik(target, [0.0, 30 * DEG_TO_RAD, -30 * DEG_TO_RAD]);
  for (let i = 0; i < first.path.length; i++) {
    const step = first.path[i];
    const qText = step.q.map((v) => fixed(v * RAD_TO_DEG, 2, 7)).join(", ");
    lines.push(
      "  iter " + int(i, 2) + "  q = [" + qText + "] deg  error " + fixed(1000 * step.dist, 3, 8) + " mm",
    );
  }
  const p = fk(first.q);
  lines.push("  check with FK: (" + fixed(p[0], 4) + ", " + fixed(p[1], 4) + ", " + fixed(p[2], 4) + ") m");
  const second = ik(target, [0.0, 90 * DEG_TO_RAD, 60 * DEG_TO_RAD]);
  lines.push(
    "  from q = [0, 90, 60] deg instead: q = [" +
      second.q.map((v) => fixed(v * RAD_TO_DEG, 2)).join(", ") +
      "] deg after " + second.it + " iterations (base turned round, reaching back over the top)",
  );
  const far = [0.20, 0.20, 0.10];
  const third = ik(far, [0.0, 30 * DEG_TO_RAD, -30 * DEG_TO_RAD]);
  const out = Math.sqrt(0.20 ** 2 + 0.20 ** 2 + (0.10 - H) ** 2);
  lines.push(
    "  to (0.20, 0.20, 0.10) m, " + fixed(out, 3) +
      " m from the shoulder but L1 + L2 = " + fixed(L1 + L2, 2) +
      " m: stops " + fixed(1000 * third.dist, 1) +
      " mm short, elbow " + fixed(roundHalfEven(third.q[2] * RAD_TO_DEG, 2) + 0.0, 2) + " deg",
  );
  const fourth = ik(far, [0.0, 30 * DEG_TO_RAD, -30 * DEG_TO_RAD], 0.01);
  lines.push(
    "  same with lambda = 0.01: after " + (fourth.it + 1) +
      " iterations still " + fixed(1000 * fourth.dist, 1) +
      " mm short, elbow " + fixed(fourth.q[2] * RAD_TO_DEG, 2) + " deg (it never settles)",
  );
  return lines;
}

// Python kinematics.show_singular().
function showSingular(): string[] {
  const lines: string[] = [
    "Singularity: the elbow straightening, shoulder at 20 deg, base at 0",
    "  elbow (deg)  det J (m^3)  joint speed for 0.05 m/s straight out (deg/s)",
    "                            exact inverse        damped, lambda = 0.03",
  ];
  for (const e of [-60, -30, -10, -3, -1, -0.3]) {
    const q = [0.0, 20 * DEG_TO_RAD, e * DEG_TO_RAD];
    const j = jacobian(q);
    const d = det3(j);
    const p = fk(q);
    const r = Math.hypot(p[0], p[1]);
    const v = [0.05 * p[0] / r, 0.05 * p[1] / r, 0.0];
    let exact = 0.0;
    for (const x of solve3(j, v)) {
      exact = Math.max(exact, Math.abs(x * RAD_TO_DEG));
    }
    let damped = 0.0;
    for (const x of dlsStep(q, v, 0.03)) {
      damped = Math.max(damped, Math.abs(x * RAD_TO_DEG));
    }
    lines.push(
      "  " + fixed(e, 1, 10) + "  " + exp(d, 2, 11) + "  " + fixed(exact, 1, 18) + "  " + fixed(damped, 1, 22),
    );
  }
  lines.push("  formula: |det J| = L1 x L2 x r x |sin(elbow)|, r = the tip's horizontal reach");
  return lines;
}

// Python kinematics's __main__ block: show_fk, a blank line, show_ik, a blank line, show_singular.
export function report(): string[] {
  return [...showFk(), "", ...showIk(), "", ...showSingular()];
}
