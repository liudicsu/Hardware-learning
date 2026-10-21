// Line-by-line port of examples/month-3/fdm-printing/snap_fit.py (cantilever snap-fit arm).
import { fixed } from "./format";
import { ljust } from "./pyfmt";

export type Material = "PLA" | "PETG";

// E (MPa), strain we allow for a snap that is used many times
export const MATERIALS: Record<Material, [number, number]> = {
  PLA: [3500, 0.015],
  PETG: [2000, 0.025],
};

export interface Snap {
  eps: number;
  P: number;
  W: number;
  ok: boolean;
  allowed: number;
  line: string;
}

export function snap(L: number, t: number, y: number, b = 6.0, material: Material = "PLA", leadDeg = 30.0, mu = 0.3): Snap {
  const [E, allowed] = MATERIALS[material];
  const eps = (1.5 * y * t) / L ** 2;
  const P = (b * t ** 2 * E * eps) / (6 * L);
  const tanA = Math.tan((leadDeg * Math.PI) / 180);
  const W = (P * (mu + tanA)) / (1 - mu * tanA);
  const ok = eps <= allowed;
  const verdict = ok ? "ok" : `too much (limit ${fixed(allowed * 100, 1)} %)`;
  const line =
    `L ${fixed(L, 1, 4)}  t ${fixed(t, 1)}  hook ${fixed(y, 1)} mm, ${ljust(material + ",", 5)} lead-in ${fixed(leadDeg, 0, 2)} deg: ` +
    `strain ${fixed(eps * 100, 2, 4)} % ${ljust(verdict, 22)} push-on ${fixed(W, 1, 5)} N`;
  return { eps, P, W, ok, allowed, line };
}

/** The lines snap_fit.py prints. */
export function report(): string[] {
  return [
    snap(5, 1.5, 1.0).line, // short and thick: the first design people draw
    snap(10, 1.5, 1.0).line,
    snap(10, 1.2, 0.8).line, // the arm used in esp32_case.scad
    snap(10, 1.2, 0.8, 6.0, "PETG").line,
    snap(10, 1.2, 0.8, 6.0, "PLA", 60).line, // steep lead-in: hard to push on
  ];
}
