// Line-by-line port of tools/sim/models/line_sim.py (line follower, P and PD).
import { fixed } from "./format";
import { ljust, pyFloat, rjust } from "./pyfmt";

export const SPEED = 0.3; // forward speed, m/s
export const DT = 0.01; // control loop period, s (100 Hz)
export const MOTOR_TAU = 0.08; // how fast the turn rate follows the command, s
export const SPACING = 0.0095; // sensor spacing, m
export const LINE_HALF_WIDTH = 0.009;

/** Weighted average of 8 sensor readings: 0..7000, 3500 = line under the centre. */
export function readPosition(offsetM: number): number {
  let total = 0.0;
  let weighted = 0.0;
  for (let i = 0; i < 8; i++) {
    const x = (i - 3.5) * SPACING + offsetM; // sensor position relative to the line
    const r = 1000 * Math.exp(-((x / LINE_HALF_WIDTH) ** 2)); // 0 = white, 1000 = black
    total += r;
    weighted += r * i * 1000;
  }
  if (total < 50) return offsetM > 0 ? 0 : 7000; // line lost: report the nearest edge
  return weighted / total;
}

export type Log = [number, number][];

export function run(kp: number, kd: number, seconds = 3.0): Log {
  let y = 0.02; // start 20 mm to one side
  let heading = 0.0;
  let turnRate = 0.0;
  let lastError: number | null = null;
  const log: Log = [];
  const steps = Math.trunc(seconds / DT);
  for (let step = 0; step < steps; step++) {
    const error = 3500 - readPosition(y); // setpoint − measurement
    const dError = lastError === null ? 0.0 : (error - lastError) / DT;
    lastError = error;
    let command = kp * error + kd * dError; // rad/s of turning, positive turns towards -y
    command = Math.max(-6.0, Math.min(6.0, command));
    for (let k = 0; k < 10; k++) {
      // robot physics at 1 ms
      turnRate += ((command - turnRate) * 0.001) / MOTOR_TAU;
      heading -= turnRate * 0.001;
      y += SPEED * Math.sin(heading) * 0.001;
    }
    log.push([(step + 1) * DT, y]);
  }
  return log;
}

export interface Description {
  overshoot: number;
  crossings: number;
  settled: number | null;
}

export function describe(log: Log): Description {
  const ys = log.map(([, y]) => y);
  const overshoot = Math.max(0.0, -Math.min(...ys)) * 1000; // mm past the line on the other side
  let crossings = 0;
  for (let i = 0; i + 1 < ys.length; i++) if (ys[i] * ys[i + 1] < 0) crossings++;
  // Python: next(t for t, _ in log if all(abs(y) < 0.002 for tt, y in log if tt >= t)).
  // Same result, scanned from the end: the first t after the last sample outside 2 mm.
  let settled: number | null = null;
  for (let i = log.length - 1; i >= 0; i--) {
    if (Math.abs(log[i][1]) < 0.002) settled = log[i][0];
    else break;
  }
  return { overshoot, crossings, settled };
}

export const CASES: [string, number, number][] = [
  ["P only", 0.0003, 0.0],
  ["P + small D", 0.0003, 0.0001],
  ["P + D", 0.0003, 0.0002],
];

/** The lines line_sim.py prints. */
export function report(): string[] {
  const out: string[] = [];
  const logs = new Map(CASES.map(([name, kp, kd]) => [name, run(kp, kd, 4.0)]));
  out.push("offset from the line (mm), every 0.5 s");
  out.push("  t_s  " + CASES.map(([name]) => rjust(name, 11)).join("  "));
  for (let k = 0; k < 9; k++) {
    const t = k * 0.5;
    const row = CASES.map(([name]) => {
      const y = k === 0 ? 20.0 : logs.get(name)![Math.round(t / DT) - 1][1] * 1000;
      return fixed(y, 1, 11);
    });
    out.push(`  ${fixed(t, 1, 3)}  ` + row.join("  "));
  }
  out.push("");
  for (const [name, kp, kd] of CASES) {
    const { overshoot, crossings, settled } = describe(logs.get(name)!);
    const settledTxt = settled !== null ? `${fixed(settled, 2)} s` : "never";
    out.push(
      `${ljust(name, 11)} kp=${pyFloat(kp)} kd=${pyFloat(kd)}: overshoot ${fixed(overshoot, 1, 4)} mm, ` +
        `${crossings} line crossings, within 2 mm from ${settledTxt}`,
    );
  }
  return out;
}
