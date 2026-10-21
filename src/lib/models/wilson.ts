// Line-by-line port of wilson() and section 1 of examples/month-6/policy-evaluation/eval_report.py.
// Only the Wilson interval: the script's "trials needed" section is deliberately not ported.
import { fixed, int } from "./format";
import { ljust } from "./pyfmt";

export const Z95 = 1.959964; // two-sided 95 % confidence

export function wilson(k: number, n: number, z = Z95): [number, number] {
  const p = k / n;
  const centre = (p + (z * z) / (2 * n)) / (1 + (z * z) / n);
  const half = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / (1 + (z * z) / n);
  return [centre - half, centre + half];
}

export function line(k: number, n: number): string {
  const [lo, hi] = wilson(k, n);
  return `  ${int(k, 3)}/${ljust(String(n), 3)}  ${fixed((100 * k) / n, 1, 5)} %   95 % interval ${fixed(100 * lo, 1, 5)} .. ${fixed(100 * hi, 1, 5)} %`;
}

/** Section 1 of what eval_report.py prints. */
export function report(): string[] {
  const out = ["1. Success with a Wilson 95 % interval"];
  for (const [k, n] of [
    [61, 100],
    [67, 100],
    [99, 100],
    [100, 100],
    [8, 10],
    [10, 10],
  ]) {
    out.push(line(k, n));
  }
  return out;
}
