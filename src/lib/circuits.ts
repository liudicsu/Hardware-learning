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
  /**
   * Practice: 5 V source, R1 = 10 kΩ, R2 = 4.7 kΩ, and RL = 10 kΩ behind
   * SPST switch S (open), with labeled node vout and an output probe.
   */
  loadedDivider: {
    cct: `$ 1 0.000005 10 50 5 50
v 112 368 112 64 0 0 40 5 0 0 0.5
w 112 64 288 64 0
r 288 64 288 208 0 10000
w 288 208 448 208 0
r 288 208 288 368 0 4700
w 112 368 288 368 0
g 112 368 112 400 0
r 448 208 448 320 0 10000
s 448 320 448 400 0 1 false
g 448 400 448 432 0
207 288 208 320 176 4 vout
O 288 208 176 208 1
x 240 128 272 128 4 16 R1
x 240 288 272 288 4 16 R2
x 384 256 416 256 4 16 RL
x 464 352 496 352 4 16 S`,
  },
  /**
   * Practice: 5 V source, 330 Ω resistor, ammeter, and red LED
   * (`2 default-led 1 0 0 0.01`) to ground, with labeled node vled at the
   * LED anode.
   */
  ledLimit: {
    cct: `$ 1 0.000005 10 50 5 50
v 96 400 96 64 0 0 40 5 0 0 0.5
w 96 64 288 64 0
r 288 64 288 160 0 330
370 288 160 288 208 1 0
w 288 208 288 240 0
162 288 240 288 320 2 default-led 1 0 0 0.01
w 288 320 288 400 0
w 96 400 288 400 0
g 96 400 96 432 0
207 288 240 320 208 4 vled`,
  },
  /**
   * Practice: 5 V source, 10 kΩ pull-up, labeled pin node with an output
   * probe, and a momentary pushbutton (open) from pin to ground.
   */
  pullupButton: {
    cct: `$ 1 0.000005 10 50 5 50
v 96 352 96 96 0 0 40 5 0 0 0.5
w 96 96 272 96 0
r 272 96 272 192 0 10000
w 272 192 400 192 0
207 400 192 432 224 4 pin
O 400 192 512 192 1
s 400 192 400 320 0 1 true
w 400 320 400 352 0
w 96 352 400 352 0
g 96 352 96 384 0
x 192 128 224 128 4 16 10k
x 432 256 464 256 4 16 button`,
  },
  /**
   * Practice: 9 V source, 220 Ω load, and a current meter made of a 0.1 Ω
   * shunt plus a fuse (0.05 Ω, 0.5 A²s). Sser (closed) puts the meter in
   * series with the load; Spar (open) puts it directly across the battery.
   */
  ammeterSeriesParallel: {
    cct: `$ 1 0.000005 10 50 5 50
v 96 400 96 64 0 0 40 9 0 0 0.5
w 96 64 160 64 0
s 160 64 288 64 0 0 false
r 288 64 288 224 0 220
w 288 224 352 224 0
r 352 224 352 288 0 0.1
404 352 288 352 352 0 0.05 0.5 0 false
w 352 352 352 400 0
w 96 400 352 400 0
w 96 64 96 32 0
w 96 32 384 32 0
s 384 32 384 224 0 1 false
w 384 224 352 224 0
g 96 400 96 432 0
x 208 48 240 48 4 16 Sser
x 400 96 432 96 4 16 Spar
x 296 256 328 256 4 16 shunt
x 304 320 336 320 4 16 fuse
x 240 144 272 144 4 16 load`,
  },
  /**
   * Practice: 6 V motor supply with 0.5 Ω supply/wiring resistance, H-bridge
   * switches S1/S4 closed and S2/S3 open, and a motor made of 10 Ω + 10 mH +
   * an ammeter between the left and right motor nodes.
   */
  hBridge: {
    cct: `$ 1 0.000005 10 50 5 50
v 96 400 96 64 0 0 40 6 0 0 0.5
w 96 64 128 64 0
r 128 64 224 64 0 0.5
w 224 64 288 64 0
w 288 64 480 64 0
s 288 64 288 224 0 0 false
s 288 224 288 400 0 1 false
s 480 64 480 224 0 1 false
s 480 224 480 400 0 0 false
w 96 400 288 400 0
w 288 400 480 400 0
w 288 224 304 224 0
r 304 224 368 224 0 10
w 368 224 384 224 0
l 384 224 448 224 0 0.01 0
370 448 224 480 224 1 0
g 96 400 96 432 0
x 240 128 272 128 4 16 S1
x 240 288 272 288 4 16 S2
x 432 128 464 128 4 16 S3
x 432 288 464 288 4 16 S4
x 352 192 384 192 4 16 MOTOR`,
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
  /** Practice: a 5 V logic signal divided down to ≈3.3 V for an ESP32 input (1 kΩ over 2 kΩ). */
  levelDivider: {
    cct: `$ 1 0.000005 10 50 5 50
v 96 352 96 96 0 2 2 2.5 2.5 0 0.5
w 96 96 288 96 0
r 288 96 288 224 0 1000
r 288 224 288 352 0 2000
w 96 352 288 352 0
O 288 224 416 224 1
g 96 352 96 384 0
o 0 64 0 34 5 0.05 0 -1
o 5 64 0 34 5 0.05 1 -1`,
  },
  /** Practice: an open-drain I2C line — 4.7 kΩ pull-up to 3.3 V, two devices that can only pull it low. */
  i2cPullup: {
    cct: `$ 1 0.000005 10 50 5 50
v 96 352 96 96 0 0 40 3.3 0 0 0.5
w 96 96 224 96 0
r 224 96 224 192 0 4700
w 224 192 320 192 0
w 320 192 448 192 0
O 448 192 528 192 1
s 320 192 320 352 0 1 true
s 448 192 448 352 0 1 true
w 96 352 320 352 0
w 320 352 448 352 0
g 96 352 96 384 0`,
  },
  /** Falstad built-in: inductive kickback when a switch opens an inductor's circuit. */
  inductkick: { startCircuit: "inductkick.txt" },
  /** Falstad built-in: the same circuit with a flyback diode across the inductor. */
  inductkickBlock: { startCircuit: "inductkick-block.txt" },
  /** Falstad built-in: RC charging from a square wave. */
  capac: { startCircuit: "capac.txt" },
  /** Falstad built-in: transistor used as a switch. */
  transswitch: { startCircuit: "transswitch.txt" },
} satisfies Record<string, CircuitDef>;

export type CircuitId = keyof typeof circuits;
