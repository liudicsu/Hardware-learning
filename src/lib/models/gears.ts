// Line-by-line port of examples/month-3/transmissions/gear_calc.py.
import { fixed, int } from "./format";
import { pyFloat } from "./pyfmt";

const radians = (deg: number) => deg * (Math.PI / 180); // Python math.radians

export interface Planetary {
  ok: boolean;
  planet: number | null;
  ratio: number | null;
  line: string;
}

export function planetary(sun: number, ring: number, planets: number): Planetary {
  const gap = ring - sun;
  if (gap % 2) {
    return { ok: false, planet: null, ratio: null, line: `sun ${int(sun, 2)}, ring ${int(ring, 2)}: no whole planet size (${pyFloat(gap / 2)} teeth) -> will not mesh` };
  }
  const planet = Math.floor(gap / 2);
  if ((sun + ring) % planets) {
    return {
      ok: false,
      planet,
      ratio: null,
      line:
        `sun ${int(sun, 2)}, ring ${int(ring, 2)}, planet ${int(planet, 2)}: ${planets} planets cannot be spaced ` +
        `evenly ((sun + ring) / ${planets} = ${fixed((sun + ring) / planets, 2)})`,
    };
  }
  const ratio = 1 + ring / sun;
  return { ok: true, planet, ratio, line: `sun ${int(sun, 2)}, ring ${int(ring, 2)}, planet ${int(planet, 2)}, ${planets} planets: ratio ${fixed(ratio, 3)} : 1` };
}

export function cycloidal(pins: number): string {
  const lobes = pins - 1;
  return `${pins} ring pins, ${lobes} lobes: ratio ${fixed(lobes / (pins - lobes), 0)} : 1, output turns the opposite way`;
}

export function stack(ratios: number[], efficiencyPerStage = 0.9): [number, number] {
  const total = ratios.reduce((a, b) => a * b, 1);
  const eff = efficiencyPerStage ** ratios.length;
  return [total, eff];
}

/** Backlash at the joint -> position error at the tip, in mm. */
export function tipError(reachM: number, deg: number): number {
  return reachM * radians(deg) * 1000;
}

/** The lines gear_calc.py prints. */
export function report(): string[] {
  const out: string[] = [];
  out.push("-- planetary stages");
  out.push(planetary(12, 48, 3).line);
  out.push(planetary(12, 46, 3).line);
  out.push(planetary(13, 47, 3).line);
  out.push(planetary(14, 46, 4).line);
  out.push(planetary(12, 45, 3).line);

  out.push("-- cycloidal stages");
  out.push(cycloidal(10));
  out.push(cycloidal(16));

  out.push("-- two 5:1 planetary stages, 90 % per stage (a guess for printed gears; measure yours)");
  const [total, eff] = stack([5, 5]);
  const motorTorque = 0.05; // N*m and rpm of a small brushless motor
  const motorRpm = 6000;
  out.push(
    `ratio ${total}:1, efficiency ${fixed(eff * 100, 0)} %: output ${fixed(motorTorque * total * eff, 2)} N*m ` +
      `at ${fixed(motorRpm / total, 0)} rpm (motor: ${pyFloat(motorTorque)} N*m at ${motorRpm} rpm)`,
  );

  out.push("-- turning the output by hand (backdriving), relative to a 147:1 gearbox");
  for (const n of [147, 191, 345]) {
    // the STS3215 ratios in the SO-101 leader arm
    out.push(`${int(n, 3)}:1  friction felt x${fixed(n / 147, 2, 4)}   rotor inertia felt x${fixed((n / 147) ** 2, 2, 4)}`);
  }

  out.push("-- backlash at the joint -> error at the tip of a 0.30 m arm");
  for (const deg of [0.5, 1.0, 2.0]) {
    out.push(`${fixed(deg, 1, 3)} deg -> ${fixed(0.3 * radians(deg) * 1000, 1, 4)} mm`);
  }
  return out;
}
