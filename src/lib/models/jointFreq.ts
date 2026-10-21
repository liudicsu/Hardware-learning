// Line-by-line port of tools/sim/models/joint_freq.py (the Month 3 joint in the frequency domain).
// Complex arithmetic follows CPython: products as (ac - bd, ad + bc), quotients with Smith's
// method (_Py_c_quot), cmath.exp(jx) = (cos x, sin x), abs = hypot, phase = atan2.
import { fixed } from "./format";
import { pyFloat } from "./pyfmt";

type C = [number, number];
const add = (a: C, b: C): C => [a[0] + b[0], a[1] + b[1]];
const sub = (a: C, b: C): C => [a[0] - b[0], a[1] - b[1]];
const mul = (a: C, b: C): C => [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]];
const re = (x: number): C => [x, 0];
function div(a: C, b: C): C {
  const absBr = Math.abs(b[0]);
  const absBi = Math.abs(b[1]);
  if (absBr >= absBi) {
    const ratio = b[1] / b[0];
    const denom = b[0] + b[1] * ratio;
    return [(a[0] + a[1] * ratio) / denom, (a[1] - a[0] * ratio) / denom];
  }
  const ratio = b[0] / b[1];
  const denom = b[0] * ratio + b[1];
  return [(a[0] * ratio + a[1]) / denom, (a[1] * ratio - a[0]) / denom];
}
const cabs = (a: C) => Math.hypot(a[0], a[1]);
const phase = (a: C) => Math.atan2(a[1], a[0]);
const degrees = (x: number) => x * (180 / Math.PI); // math.degrees

export const J = 0.004;
export const B = 0.05;
export const GRAV = 0.4;
export const T = 0.005;
export const A = B / J; // 12.5 1/s, so the time constant J/B is 0.08 s
export const E = Math.exp(-A * T);
// exact discretisation of J*q'' + B*q' = u with the torque held over each period
const PHI = [
  [1.0, (1 - E) / A],
  [0.0, E],
];
const GAM = [(T - (1 - E) / A) / (A * J), (1 - E) / (A * J)];

function step(q: number, w: number, u: number): [number, number] {
  return [q + PHI[0][1] * w + GAM[0] * u, E * w + GAM[1] * u];
}

function identify(out: string[]) {
  out.push("Open-loop step: 0.2 N*m from rest, speed logged at 200 Hz");
  let q = 0.0;
  let w = 0.0;
  const log: [number, number][] = [];
  for (let k = 0; k < 101; k++) {
    log.push([k * T, w]);
    [q, w] = step(q, w, 0.2);
  }
  const every8 = log.filter((_, i) => i % 8 === 0).slice(0, 8);
  for (const [t, s] of every8) out.push(`  t = ${fixed(t, 2, 4)} s   speed ${fixed(s, 2, 5)} rad/s`);
  const final = log[log.length - 1][1];
  const t63 = log.find(([, s]) => s >= 0.632 * final)![0];
  const b = 0.2 / final;
  out.push(`  final speed ${fixed(final, 2)} rad/s -> B = 0.2 / ${fixed(final, 2)} = ${fixed(b, 3)} N*m per rad/s`);
  out.push(`  63 % of it at t = ${fixed(t63, 3)} s -> J = B x tau = ${fixed(b * t63, 4)} kg*m^2`);
  void q;
}

/** Loop gain L = C * P at angular frequency w (rad/s), with z = e^(jwT). */
export function loop(kp: number, kd: number, w: number): C {
  const jwT = mul(mul([0, 1], re(w)), re(T));
  const z: C = [Math.exp(jwT[0]) * Math.cos(jwT[1]), Math.exp(jwT[0]) * Math.sin(jwT[1])];
  const det = sub(mul(sub(z, re(PHI[0][0])), sub(z, re(PHI[1][1]))), re(PHI[0][1] * PHI[1][0]));
  const plant = div(add(mul(sub(z, re(PHI[1][1])), re(GAM[0])), re(PHI[0][1] * GAM[1])), det); // angle / torque
  const pd = add(re(kp), div(mul(re(kd), sub(re(1), div(re(1), z))), re(T)));
  return div(mul(pd, plant), z); // one sample of delay
}

export interface Margins {
  wc: number | null;
  pm: number | null;
  wpc: number | null;
  gm: number | null;
}

/** Gain and phase margins from a fine logarithmic sweep up to the Nyquist frequency. */
export function margins(kp: number, kd: number): Margins {
  const ws: number[] = [];
  const end = Math.trunc(2000 * Math.log10(Math.PI / T));
  for (let k = -2000; k < end; k++) ws.push(10 ** (k / 2000));
  let wc: number | null = null;
  let pm: number | null = null;
  let wpc: number | null = null;
  let gm: number | null = null;
  let lastPh: number | null = null;
  let unwrap = 0.0;
  let prev: [number, C, number] | null = null;
  for (const w of ws) {
    const l = loop(kp, kd, w);
    let ph = degrees(phase(l));
    if (lastPh !== null && ph - lastPh > 180) unwrap -= 360; // keep the phase continuous
    lastPh = ph;
    ph += unwrap;
    if (prev !== null) {
      if (wc === null && cabs(prev[1]) >= 1 && 1 > cabs(l)) {
        wc = w;
        pm = 180 + ph;
      }
      if (wpc === null && prev[2] > -180 && -180 >= ph) {
        wpc = w;
        gm = -20 * Math.log10(cabs(l));
      }
    }
    prev = [w, l, ph];
  }
  return { wc, pm, wpc, gm };
}

export interface BodeRow {
  w: number;
  db: number;
  ph: number;
}

/** |L| and phase (wrapped to (-360, 0]) at one frequency, as bode() prints them. */
export function bodePoint(kp: number, kd: number, w: number): BodeRow {
  const l = loop(kp, kd, w);
  let ph = degrees(phase(l));
  ph = ph > 0 ? ph - 360 : ph;
  return { w, db: 20 * Math.log10(cabs(l)), ph };
}

function bode(out: string[], kp: number, kd: number) {
  out.push(`Loop gain, kp = ${pyFloat(kp)} N*m/rad, kd = ${pyFloat(kd)} N*m/(rad/s)`);
  out.push("   w (rad/s)  |L| (dB)  phase (deg)");
  for (const w of [1, 3, 10, 30, 100, 300]) {
    const r = bodePoint(kp, kd, w);
    out.push(`  ${fixed(w, 0, 9)}  ${fixed(r.db, 1, 8)}  ${fixed(r.ph, 1, 11)}`);
  }
  const m = margins(kp, kd);
  out.push(`  gain crossover ${fixed(m.wc!, 1)} rad/s, phase margin ${fixed(m.pm!, 0)} deg`);
  out.push(`  phase crossover ${fixed(m.wpc!, 1)} rad/s, gain margin ${fixed(m.gm!, 1)} dB (x ${fixed(10 ** (m.gm! / 20), 1)})`);
}

/** Closed-loop step of 0.1 rad (about 6 degrees), small enough to stay linear. */
export function closed(kp: number, kd: number, target = 0.1, seconds = 2.0) {
  let q = 0.0;
  let w = 0.0;
  let u = 0.0;
  let prev = 0.0;
  let peak = 0.0;
  const hist: number[] = [];
  const qs: number[] = [];
  const n = Math.trunc(seconds / T);
  for (let k = 0; k < n; k++) {
    const rate = (q - prev) / T;
    prev = q;
    const nxt = kp * (target - q) - kd * rate; // computed now, applied next period
    [q, w] = step(q, w, u);
    u = nxt;
    peak = Math.max(peak, q);
    hist.push(q - target);
    qs.push(q);
  }
  const early = hist.slice(100, 200);
  const late = hist.slice(-100); // 0.5-1.0 s and the last 0.5 s
  const size = (h: number[]) => Math.max(...h) - Math.min(...h);
  const ups: number[] = [];
  for (let k = hist.length - 100; k < hist.length - 1; k++) if (hist[k] < 0 && 0 <= hist[k + 1]) ups.push(k);
  const freq = ups.length > 2 ? (2 * Math.PI * (ups.length - 1)) / ((ups[ups.length - 1] - ups[0]) * T) : null;
  return { over: (100 * Math.max(0.0, peak - target)) / target, early: size(early), late: size(late), freq, qs };
}

function sweep(out: string[]) {
  const m1 = margins(1.0, 0.0);
  out.push(`P only, kp = 1.0: gain margin ${fixed(m1.gm!, 1)} dB, so the loop should ring at ${fixed(m1.wpc!, 1)} rad/s`);
  const g = 10 ** (m1.gm! / 20);
  out.push(`and turn unstable near kp = 1.0 x ${fixed(g, 2)} = ${fixed(g, 2)}. Check it on 0.1 rad steps:`);
  out.push("     kp     kd   PM (deg)  overshoot  swing 0.5-1 s  swing 1.5-2 s  ringing at");
  const cases: [number, number][] = [[0.5, 0], [1.0, 0], [2.0, 0], [2.86, 0], [6.5, 0], [7.0, 0], [2.86, 0.115]];
  for (const [kp, kd] of cases) {
    const { pm } = margins(kp, kd);
    const { over, early, late, freq } = closed(kp, kd);
    const f = freq && late > 1e-4 ? `${fixed(freq, 1)} rad/s` : "-";
    const o = late < early ? `${fixed(over, 0, 6)} %` : "  grows";
    out.push(`  ${fixed(kp, 2, 5)}  ${fixed(kd, 3, 5)}  ${fixed(pm!, 0, 8)}   ${o}   ${fixed(1000 * early, 2, 8)} mrad  ${fixed(1000 * late, 2, 9)} mrad  ${f}`);
  }
}

/** The lines joint_freq.py prints. */
export function report(): string[] {
  const out: string[] = [];
  identify(out);
  out.push("");
  bode(out, 2.86, 0.115);
  out.push("");
  sweep(out);
  return out;
}
