import { fixed } from "./format";

export const J = 0.004;
export const B = 0.05;
export const GRAV = 0.4;
export const MAX_TORQUE = 1.0;
export const DT = 0.005;

const RAD_TO_DEG = 180 / Math.PI;

export interface PidResult {
  t: number[];
  deg: number[];
  finalDeg: number;
  overshoot: number;
  settle: number | null;
}

// Python pid_sim.run(): the simulation loop, with every 5 ms control step recorded.
export function simulate(
  kp: number,
  ki = 0,
  kd = 0,
  antiWindup = true,
  target = 60,
  seconds = 3,
): PidResult {
  let q = 0.0;
  let w = 0.0;
  let integral = 0.0;
  let t = 0.0;
  let peak = 0.0;
  let settle: number | null = null;
  let prev = q;
  const ts = [0];
  const degs = [0];

  while (t < seconds) {
    const error = target - q * RAD_TO_DEG;
    const rate = (q * RAD_TO_DEG - prev * RAD_TO_DEG) / DT;
    prev = q;
    const unclipped = kp * error + ki * integral - kd * rate;
    const torque = Math.max(-MAX_TORQUE, Math.min(MAX_TORQUE, unclipped));
    if (!antiWindup || torque === unclipped) {
      integral += error * DT;
    }
    for (let i = 0; i < 5; i++) {
      const alpha = (torque - B * w - GRAV * Math.cos(q)) / J;
      w += alpha * 0.001;
      q += w * 0.001;
    }
    t += DT;
    const deg = q * RAD_TO_DEG;
    peak = Math.max(peak, deg);
    if (Math.abs(deg - target) > 1.0) {
      settle = null;
    } else if (settle === null) {
      settle = t;
    }
    ts.push(t);
    degs.push(deg);
  }

  return {
    t: ts,
    deg: degs,
    finalDeg: q * RAD_TO_DEG,
    overshoot: Math.max(0.0, peak - target),
    settle,
  };
}

// Python pid_sim.run(): the formatted summary string it returns.
export function run(
  kp: number,
  ki = 0,
  kd = 0,
  antiWindup = true,
  target = 60,
  seconds = 3,
): string {
  const result = simulate(kp, ki, kd, antiWindup, target, seconds);
  const s = result.settle !== null ? fixed(result.settle, 2) + " s" : "never";
  return (
    "final " + fixed(result.finalDeg, 1, 5) +
    " deg, overshoot " + fixed(result.overshoot, 1, 4) +
    " deg, within 1 deg from " + s
  );
}

// Python pid_sim's __main__ block: the eight labelled runs it prints.
export function report(): string[] {
  return [
    "P    kp 0.05                  " + " " + run(0.05),
    "P    kp 0.2                   " + " " + run(0.2),
    "PD   kp 0.05, kd 0.002        " + " " + run(0.05, 0, 0.002),
    "PI   kp 0.05, ki 0.1          " + " " + run(0.05, 0.1),
    "PID  kp 0.05, ki 0.1, kd 0.002" + " " + run(0.05, 0.1, 0.002),
    "  ...same, no anti-windup     " + " " + run(0.05, 0.1, 0.002, false),
    "PID  kp 0.05, ki 0.4, kd 0.002" + " " + run(0.05, 0.4, 0.002),
    "  ...same, no anti-windup     " + " " + run(0.05, 0.4, 0.002, false),
  ];
}
