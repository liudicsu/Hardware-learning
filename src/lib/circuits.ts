/**
 * Circuit definitions for the embedded Falstad simulator, in CircuitJS text
 * format. Authored for this site. Each entry is either one of Falstad's
 * built-in example files (`startCircuit`) or our own circuit text (`cct`).
 */
export type CircuitDef = { startCircuit: string } | { cct: string };

export const circuits = {
  /** Falstad built-in: Ohm's law with two resistors on one source. */
  ohms: { startCircuit: "ohms.txt" },
  /** Falstad built-in: voltage dividers. */
  voltdivide: { startCircuit: "voltdivide.txt" },
  /** Practice: 5 V across 10 kΩ over 4.7 kΩ, output probe at the midpoint. */
  dividerPractice: {
    cct: `$ 1 0.000005 10 50 5 50
v 112 368 112 64 0 0 40 5 0 0 0.5
w 112 64 288 64 0
r 288 64 288 208 0 10000
r 288 208 288 368 0 4700
w 112 368 288 368 0
O 288 208 400 208 1
g 112 368 112 400 0`,
  },
  /** Falstad built-in: resistors in series/parallel with switches. */
  resistors: { startCircuit: "resistors.txt" },
  /** Practice: 3.3 V logic input switching a 5 V LED through an NPN transistor. */
  transistorLed: {
    cct: `$ 1 0.000005 10 50 5 50
v 96 400 96 64 0 0 40 5 0 0 0.5
w 96 64 400 64 0
r 400 64 400 144 0 220
162 400 144 400 224 0 1 0 0
w 400 224 400 240 0
t 336 256 400 256 0 1 0 0 100
w 400 272 400 400 0
w 400 400 208 400 0
w 208 400 96 400 0
v 208 400 208 160 0 0 40 3.3 0 0 0.5
s 208 160 272 160 0 1 false
r 272 160 272 256 0 1000
w 272 256 336 256 0
g 96 400 96 432 0`,
  },
  /** Practice: a 490 Hz, 25 % duty PWM signal averaged by an RC low-pass (1 kΩ, 10 µF). */
  pwmAverage: {
    cct: `$ 1 0.000005 10 50 5 50
v 96 352 96 96 0 2 490 2.5 2.5 0 0.25
w 96 96 240 96 0
r 240 96 384 96 0 1000
c 384 96 384 352 0 0.00001 0
w 96 352 384 352 0
O 384 96 496 96 1
g 96 352 96 384 0
o 0 64 0 34 5 0.05 0 -1
o 3 64 0 34 5 0.05 1 -1`,
  },
  /** Falstad built-in: RC charging from a square wave. */
  capac: { startCircuit: "capac.txt" },
  /** Falstad built-in: transistor used as a switch. */
  transswitch: { startCircuit: "transswitch.txt" },
} satisfies Record<string, CircuitDef>;

export type CircuitId = keyof typeof circuits;
