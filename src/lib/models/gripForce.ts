// Line-by-line port of examples/month-3/gripper-fingers/grip_force.py.
import { fixed } from "./format";
import { ljust, pyFloat } from "./pyfmt";

export const G = 9.81;
export const SAFETY = 2.0;
export const ARM_ACCEL = 3.0; // m/s^2: a brisk move of the arm

export const OBJECTS: [string, number][] = [
  // name, mass (kg)
  ["egg", 0.06],
  ["full 330 ml can", 0.35],
  ["AA battery", 0.023],
];
export const FINGERS: [string, number][] = [
  ["PLA", 0.3],
  ["TPU", 0.8],
];

/** Squeeze force per finger, N: F = S * m * (g + a) / (2 * mu). */
export function squeeze(mass: number, mu: number, safety = SAFETY, accel = ARM_ACCEL): number {
  return (safety * mass * (G + accel)) / (2 * mu);
}

/** The lines grip_force.py prints. */
export function report(): string[] {
  const out = [`safety factor ${pyFloat(SAFETY)}, arm acceleration ${pyFloat(ARM_ACCEL)} m/s^2`];
  for (const [name, mass] of OBJECTS) {
    const row = FINGERS.map(([f, mu]) => `${f} (mu ${pyFloat(mu)}): ${fixed(squeeze(mass, mu), 1, 4)} N`).join(", ");
    out.push(`${ljust(name, 16)} ${fixed(mass * 1000, 0, 4)} g  ->  ${row}`);
  }
  return out;
}
