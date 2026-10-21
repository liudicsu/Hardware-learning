// Analytic approximation of tools/sim/models/filter_sim.py, NOT a line-by-line port.
// The script adds Gaussian noise from Python's random.Random(seed=7) (Mersenne Twister +
// gauss()), which we do not reproduce in the browser. Its flat-board offset is instead
// predicted by the steady state of the same filter equation with a constant gyro bias:
//   fused = alpha * (fused + bias * DT) + (1 - alpha) * 0  ->  alpha / (1 - alpha) * bias * DT
// tools/check_widgets.mjs checks that this agrees with the script's offset_flat column to
// 1 decimal place (the lesson says so next to the widget).
import { fixed } from "./format";

export const DT = 0.01; // s, 100 Hz (filter_sim.py)
export const GYRO_BIAS = 1.5; // deg/s (filter_sim.py)

/** Correction time constant tau = alpha * dt / (1 - alpha), seconds. */
export function timeConstant(alpha: number, dt = DT): number {
  return (alpha * dt) / (1 - alpha);
}

/** Steady offset left by a constant gyro bias, degrees. */
export function biasOffset(alpha: number, bias = GYRO_BIAS, dt = DT): number {
  return (alpha / (1 - alpha)) * bias * dt;
}

/** The three alphas of the script's table, with the offset rounded to 1 decimal place. */
export function offsetTable(): string[] {
  return [0.9, 0.98, 0.995].map((a) => fixed(biasOffset(a), 1));
}
