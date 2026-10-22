// Line-by-line port of the decoder part of tools/sim/models/encoder_sim.py
// (6-pole disc, two Hall sensors a quarter period apart, QDEC state table as in one_rev.ino).
// report() reproduces the first 15 lines of tools/sim/expected/m2-encoder_sim.txt; the diagram
// columns used by <QuadratureTiming> come from the same functions.
import { fixed } from "./format";

export const POLES = 6;
export const PERIOD_DEG = 360 / (POLES / 2);
export const OFFSET_DEG = PERIOD_DEG / 4;
export const QDEC = [0, -1, +1, 0, +1, 0, 0, -1, -1, 0, 0, +1, 0, +1, -1, 0];

const pmod = (a: number, m: number) => ((a % m) + m) % m; // Python's % for floats

export function hall(angleDeg: number): number {
  return pmod(angleDeg, PERIOD_DEG) < PERIOD_DEG / 2 ? 1 : 0;
}

export function ab(angleDeg: number): number {
  return (hall(angleDeg) << 1) | hall(angleDeg - OFFSET_DEG);
}

export function bits(s: number): string {
  return `${s >> 1}${s & 1}`;
}

type Row = [number, string, string, number, number];

export function run(angles: number[]): { count: number; illegal: number; rows: Row[] } {
  let count = 0;
  let illegal = 0;
  const rows: Row[] = [];
  let last = ab(angles[0]);
  for (const a of angles.slice(1)) {
    const s = ab(a);
    if (s !== last) {
      if ((s ^ last) === 0b11) illegal += 1;
      count += QDEC[(last << 2) | s];
      rows.push([a, bits(last), bits(s), QDEC[(last << 2) | s], count]);
    }
    last = s;
  }
  return { count, illegal, rows };
}

export function edgesPerRev(): [number, number, number] {
  let x1 = 0, x2 = 0, x4 = 0;
  let prev = ab(0.5);
  for (let i = 1; i < 3601; i++) {
    const s = ab(0.5 + i * 0.1);
    const a0 = prev >> 1, a1 = s >> 1, b0 = prev & 1, b1 = s & 1;
    x1 += a0 === 0 && a1 === 1 ? 1 : 0;
    x2 += a0 !== a1 ? 1 : 0;
    x4 += (a0 !== a1 ? 1 : 0) + (b0 !== b1 ? 1 : 0);
    prev = s;
  }
  return [x1, x2, x4];
}

const sgn = (d: number) => (d >= 0 ? `+${d}` : `${d}`); // Python f"{d:+d}"

export function report(): string[] {
  const out: string[] = [];
  out.push(`disc: ${POLES} poles -> ${POLES / 2} square-wave periods per motor turn, ${fixed(PERIOD_DEG, 0)} deg each; sensor B offset ${fixed(OFFSET_DEG, 0)} deg = 1/4 period = 90 deg phase`);
  const fwd = Array.from({ length: 721 }, (_, i) => 0.5 + i * 0.5);
  let r = run(fwd);
  out.push("forward, first period:");
  for (const [a, p, s, d, c] of r.rows.slice(0, 4)) out.push(`  ${fixed(a, 1, 6)} deg  AB ${p} -> ${s}  ${sgn(d)}  count ${c}`);
  out.push(`forward, one motor turn: count ${sgn(r.count)}, illegal jumps ${r.illegal}`);
  r = run([...fwd].reverse());
  out.push("reverse, first period:");
  for (const [a, p, s, d, c] of r.rows.slice(0, 4)) out.push(`  ${fixed(a + 0.5, 1, 6)} deg  AB ${p} -> ${s}  ${sgn(d)}  count ${c}`);
  out.push(`reverse, one motor turn: count ${sgn(r.count)}, illegal jumps ${r.illegal}`);
  const slow = Array.from({ length: 7 }, (_, i) => 0.5 + i * 60);
  r = run(slow);
  out.push(`sampled every 60 deg (too slow): count ${sgn(r.count)}, illegal jumps ${r.illegal} (should be +12)`);
  const [x1, x2, x4] = edgesPerRev();
  out.push(`counts per motor turn: x1 ${x1}, x2 ${x2}, x4 ${x4}  (${POLES / 2} pulses x 2 edges x 2 channels = ${(POLES / 2) * 2 * 2})`);
  return out;
}

export interface QuadColumn {
  ab: string;
  a: number;
  b: number;
  delta: number;
  count: number;
}

/**
 * Columns of the timing diagram: n states, 30° of motor-shaft rotation each, starting in the
 * 00 state just before 0°; forward = increasing shaft angle (the script's forward run).
 */
export function diagramColumns(direction: "forward" | "reverse", n = 8): QuadColumn[] {
  const step = direction === "forward" ? OFFSET_DEG : -OFFSET_DEG;
  const cols: QuadColumn[] = [];
  let count = 0;
  let last = -1;
  for (let i = 0; i < n; i++) {
    const s = ab(-OFFSET_DEG / 2 + step * i);
    const delta = last < 0 ? 0 : QDEC[(last << 2) | s];
    count += delta;
    cols.push({ ab: bits(s), a: s >> 1, b: s & 1, delta, count });
    last = s;
  }
  return cols;
}
