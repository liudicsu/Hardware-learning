// Line-by-line port of examples/month-4/ros2-control/diff_drive.py.
import { fixed } from "./format";
import { ljust, pyFloat, rjust } from "./pyfmt";

export const B = 0.28; // m, wheel_separation
export const R = 0.05; // m, wheel_radius

export const CASES: [string, number, number][] = [
  // name, v (m/s), w (rad/s)
  ["straight", 0.2, 0.0],
  ["straight, quiz", 0.3, 0.0],
  ["spin left", 0.0, 1.0],
  ["arc left", 0.2, 0.5],
  ["arc right", 0.3, -1.0],
  ["spin right, max", 0.0, -2.0],
  ["reverse, yaw left", -0.2, 0.5],
];

/** Left and right wheel speeds in rad/s. */
export function wheels(v: number, w: number, b = B, r = R): [number, number] {
  const vLeft = v - (w * b) / 2;
  const vRight = v + (w * b) / 2;
  return [vLeft / r, vRight / r];
}

function radiusText(v: number, w: number): string {
  return w === 0 ? "none (straight)" : v === 0 ? "0 (in place)" : `${fixed(v / w, 2)} m`;
}

/** One table row, as the script prints it. */
export function row(name: string, v: number, w: number): string {
  const [left, right] = wheels(v, w);
  return `${ljust(name, 17)} ${fixed(v, 2, 6)} ${fixed(w, 2, 7)}  ${fixed(left, 1, 10)} ${fixed(right, 1, 11)}  ${radiusText(v, w)}`;
}

/**
 * The lines diff_drive.py prints. `found` is what it reads from controllers.yaml
 * (wheel_separation, wheel_radius), or null when the file is missing.
 */
export function report(found: [number, number] | null): string[] {
  const out: string[] = [];
  if (found === null) {
    out.push("controllers.yaml not found: using b and r from this script");
  } else if (found[0] === B && found[1] === R) {
    out.push(`controllers.yaml: wheel_separation ${pyFloat(found[0])} m, wheel_radius ${pyFloat(found[1])} m (same as this script)`);
  } else {
    out.push(`WARNING: controllers.yaml says (${pyFloat(found[0])}, ${pyFloat(found[1])}), this script uses (${pyFloat(B)}, ${pyFloat(R)})`);
  }
  out.push(`b/2 = ${fixed(B / 2, 2)} m`);
  out.push(`${ljust("case", 17)} ${rjust("v m/s", 6)} ${rjust("w rad/s", 7)}  ${rjust("left rad/s", 10)} ${rjust("right rad/s", 11)}  turn radius`);
  for (const [name, v, w] of CASES) out.push(row(name, v, w));
  return out;
}
