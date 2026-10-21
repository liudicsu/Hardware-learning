// Line-by-line port of the dataset and per-step-bins part of
// examples/month-6/vla-models/action_tokens.py (the DCT half is not part of the widget).
import { fixed } from "./format";
import { pySum } from "./pyfmt";
import { PyRandom } from "./pyRandom";

export const HZ = 30;
export const CHUNK = 30;
export const JOINTS = 6;
export const BINS = 256;

/** Smooth joint targets: a few slow sine components per joint, like a person moving a leader arm. */
export function episode(rng: PyRandom, seconds = 10): number[][] {
  const comps: [number, number, number][][] = [];
  for (let j = 0; j < JOINTS; j++) {
    const c: [number, number, number][] = [];
    for (let k = 0; k < 3; k++) c.push([rng.uniform(5, 40), rng.uniform(0.1, 0.8), rng.uniform(0, 2 * Math.PI)]);
    comps.push(c);
  }
  const offset: number[] = [];
  for (let j = 0; j < JOINTS; j++) offset.push(rng.uniform(-30, 30));
  const out: number[][] = [];
  for (let t = 0; t < seconds * HZ; t++) {
    const row: number[] = [];
    for (let j = 0; j < JOINTS; j++) {
      row.push(offset[j] + pySum(comps[j].map(([a, f, ph]) => a * Math.sin((((2 * Math.PI * f) * t) / HZ) + ph))));
    }
    out.push(row);
  }
  return out;
}

export function percentile(values: number[], q: number): number {
  const v = [...values].sort((a, b) => a - b);
  const k = (v.length - 1) * q;
  const lo = Math.trunc(k);
  return v[lo] + (v[Math.min(lo + 1, v.length - 1)] - v[lo]) * (k - lo);
}

export function toBins(x: number, lo: number, hi: number): number {
  const u = (Math.min(Math.max(x, lo), hi) - lo) / (hi - lo);
  return Math.min(Math.trunc(u * BINS), BINS - 1);
}

export function fromBins(token: number, lo: number, hi: number): number {
  return lo + ((token + 0.5) * (hi - lo)) / BINS;
}

export function errors(chunk: number[][], rebuilt: number[][]): [number, number] {
  const diffs: number[] = [];
  chunk.forEach((row, t) => row.forEach((a, j) => diffs.push(Math.abs(a - rebuilt[t][j]))));
  return [Math.sqrt(pySum(diffs.map((d) => d * d)) / diffs.length), Math.max(...diffs)];
}

const signed0 = (x: number) => {
  const s = fixed(x, 0);
  return s.startsWith("-") ? s : "+" + s;
};

let cache: { lo: number[]; hi: number[] } | null = null;

/** The dataset's 1st and 99th percentile per joint (50 episodes, random.Random(6)). */
export function ranges(): { lo: number[]; hi: number[] } {
  if (cache) return cache;
  const rng = new PyRandom(6);
  const data: number[][][] = [];
  for (let e = 0; e < 50; e++) data.push(episode(rng));
  const lo: number[] = [];
  const hi: number[] = [];
  for (let j = 0; j < JOINTS; j++) {
    const col = data.flatMap((ep) => ep.map((s) => s[j]));
    lo.push(percentile(col, 0.01));
    hi.push(percentile(col, 0.99));
  }
  cache = { lo, hi };
  return cache;
}

/** The first eight lines action_tokens.py prints (dataset and per-step bins). */
export function report(): string[] {
  const { lo, hi } = ranges();
  const out: string[] = [];
  out.push(`Dataset: 50 episodes of 10 s, ${JOINTS} joints at ${HZ} Hz; 1st..99th percentile per joint (deg):`);
  out.push("  " + lo.map((l, j) => `j${j} ${signed0(l)}..${signed0(hi[j])}`).join("  "));
  out.push(`  bin width = range / ${BINS}: ` + lo.map((l, j) => fixed((hi[j] - l) / BINS, 2)).join(", ") + " deg");

  const chunk = episode(new PyRandom(99)).slice(0, CHUNK); // a new episode, not in the dataset
  out.push("");
  out.push(`One ${CHUNK}-step chunk (1 s) from a new episode: ${CHUNK} x ${JOINTS} = ${CHUNK * JOINTS} numbers`);

  const tokens = chunk.map((row) => row.map((x, j) => toBins(x, lo[j], hi[j])));
  const rebuilt = tokens.map((row) => row.map((tk, j) => fromBins(tk, lo[j], hi[j])));
  const [rms, worst] = errors(chunk, rebuilt);
  let clipped = 0;
  chunk.forEach((row) => row.forEach((x, j) => { if (!(lo[j] <= x && x <= hi[j])) clipped++; }));
  out.push(
    `bins: ${CHUNK * JOINTS} tokens, error rms ${fixed(rms, 3)} deg, max ${fixed(worst, 3)} deg ` +
      `(${clipped} values outside the 1st..99th percentile, clipped)`,
  );
  out.push("  joint 0 tokens, first 12 steps: " + tokens.slice(0, 12).map((r) => String(r[0])).join(" "));
  let same = 0;
  let near = 0;
  for (let t = 1; t < CHUNK; t++) {
    for (let j = 0; j < JOINTS; j++) {
      if (tokens[t][j] === tokens[t - 1][j]) same++;
      if (Math.abs(tokens[t][j] - tokens[t - 1][j]) <= 2) near++;
    }
  }
  const total = (CHUNK - 1) * JOINTS;
  out.push(`  token equal to the previous step: ${same}/${total}; within 2 of it: ${near}/${total}`);
  return out;
}

/** Joint 0 at the first step of the script's new-episode chunk (its token is 158). */
export function firstChunkValue(): number {
  return episode(new PyRandom(99), 1)[0][0];
}
