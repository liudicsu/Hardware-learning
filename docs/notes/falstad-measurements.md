# Falstad circuit measurements (PR demos-pr1)

Every number quoted in the lessons for the new Falstad circuits was read from the
real CircuitJS running at `https://www.falstad.com/circuit/circuitjs.html`, not
computed by hand. Measured 2026-10-21 (UTC+8) in headless Chrome.

How: [`falstad-measure.cjs`](./falstad-measure.cjs) reads each circuit's `cct`
text straight from `src/lib/circuits.ts`, sets the switch positions for each
variant, loads `circuitjs.html?running=false&cct=…`, installs an `ontimestep`
hook (peak current, fuse-blow time), starts the simulation through the
documented JS interface `window.CircuitJS1` (`setSimRunning`, `getElements`,
`getType`, `getCurrent`, `getVoltageDiff`, `getInfo`, `getNodeVoltage`,
`getTime`; see `war/jsinterface.html` and `JSInterface.java` in
pfalstad/circuitjs1), waits ≥ 50 ms of simulated time and prints every element.
The `DYNAMIC=1` run clicks the H-bridge switches on the canvas (CircuitJS has no
API to flip a switch) to record the brake transient.

```bash
NODE_PATH=/path/to/node_modules node docs/notes/falstad-measure.cjs           # static cases
DYNAMIC=1 NODE_PATH=/path/to/node_modules node docs/notes/falstad-measure.cjs # brake transient
```
(`playwright-core` and a Chrome binary are needed; they are not repo dependencies.)

## Summary (values quoted in the lessons)

| Lesson | Circuit key | Case | Measured in CircuitJS | Quoted as |
|---|---|---|---|---|
| m1/ohms-law | `loadedDivider` | S open (no load) | V(vout) = 1.5986 V | 1.60 V |
| m1/ohms-law | `loadedDivider` | S closed (10 kΩ load) | V(vout) = 1.2113 V; RL 121 µA, R2 258 µA | ≈1.21 V |
| m1/components | `ledLimit` | 5 V, 330 Ω, red LED (`default-led`) | I = 9.752 mA, LED Vd = 1.782 V | 约 9.8 mA, Vf ≈ 1.78 V |
| m1/components | `pullupButton` | released / pressed | pin 5.000 V / 0.000 V; 0 / 0.500 mA through 10 kΩ | 5 V / 0 V, 0.5 mA |
| m1/bench-multimeter | `ammeterSeriesParallel` | meter in series with 220 Ω on 9 V | I = 40.881 mA; shunt drop 4.09 mV | 约 41 mA, ≈4 mV |
| m1/bench-multimeter | `ammeterSeriesParallel` | meter across 9 V battery | peak 60.0 A, fuse blown at t = 0.145 ms | 60 A, ≈0.15 ms |
| m2/motors-drivers | `hBridge` | S1+S4 forward | motor +571.4 mA | 约 +0.57 A |
| m2/motors-drivers | `hBridge` | S2+S3 reverse | motor −571.4 mA | 约 −0.57 A |
| m2/motors-drivers | `hBridge` | S2+S4 brake (from rest) | 0 A | 0 |
| m2/motors-drivers | `hBridge` | forward → brake (S1 open, S2 closed) | 570 → 211 mA at 1 ms → 78 mA at 2 ms → 3.9 mA at 5 ms | decays in a few ms (τ ≈ 1 ms) |
| m2/motors-drivers | `hBridge` | S1+S2 or S3+S4 shoot-through | 12.0 A through the leg, 72 W in the 0.5 Ω, motor 0 A | 12 A |

Notes: the battery/supply is ideal in all circuits. The 0.5 Ω in the H-bridge
stands for supply and wiring resistance; without it the shoot-through current
would be unlimited. A real 9 V battery has internal resistance, so the real
short-circuit current is lower than 60 A, but still far above any mA range.

## Raw output

```text
### loadedDivider: S open (no load)  (sim t = 50.1 ms)
V(vout) = 1.5986 V
0 VoltageElm: I = 0.340 mA, Vdiff = 5.0000 V, peak|I| = 0.340 mA :: voltage source | I = 340.136 μA | Vd = 5 V | (R = 14.7 kΩ) | P = -1.701 mW
2 ResistorElm: I = 0.340 mA, Vdiff = 3.4014 V, peak|I| = 0.340 mA :: resistor | I = 340.136 μA | Vd = 3.401 V | R = 10 kΩ | P = 1.157 mW
4 ResistorElm: I = 0.340 mA, Vdiff = 1.5986 V, peak|I| = 0.340 mA :: resistor | I = 340.136 μA | Vd = 1.599 V | R = 4.7 kΩ | P = 543.755 μW
7 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: resistor | I = 0 A | Vd = 0 V | R = 10 kΩ | P = 0 W
8 SwitchElm: I = 0.000 mA, Vdiff = 1.5986 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 1.599 V

### loadedDivider: S closed (10 kΩ load)  (sim t = 50.1 ms)
V(vout) = 1.2113 V
0 VoltageElm: I = 0.379 mA, Vdiff = 5.0000 V, peak|I| = 0.379 mA :: voltage source | I = 378.866 μA | Vd = 5 V | (R = 13.197 kΩ) | P = -1.894 mW
2 ResistorElm: I = 0.379 mA, Vdiff = 3.7887 V, peak|I| = 0.379 mA :: resistor | I = 378.866 μA | Vd = 3.789 V | R = 10 kΩ | P = 1.435 mW
4 ResistorElm: I = 0.258 mA, Vdiff = 1.2113 V, peak|I| = 0.258 mA :: resistor | I = 257.732 μA | Vd = 1.211 V | R = 4.7 kΩ | P = 312.201 μW
7 ResistorElm: I = 0.121 mA, Vdiff = 1.2113 V, peak|I| = 0.121 mA :: resistor | I = 121.134 μA | Vd = 1.211 V | R = 10 kΩ | P = 146.735 μW
8 SwitchElm: I = 0.121 mA, Vdiff = 0.0000 V, peak|I| = 0.121 mA :: switch (SPST) | closed | V = 0 V | I = 121.134 μA

### ledLimit: as drawn  (sim t = 50.0 ms)
V(vled) = 1.7819 V
0 VoltageElm: I = 9.752 mA, Vdiff = 5.0000 V, peak|I| = 9.752 mA :: voltage source | I = 9.752 mA | Vd = 5 V | (R = 512.731 Ω) | P = -48.758 mW
2 ResistorElm: I = 9.752 mA, Vdiff = 3.2181 V, peak|I| = 9.752 mA :: resistor | I = 9.752 mA | Vd = 3.218 V | R = 330 Ω | P = 31.382 mW
3 AmmeterElm: I = 9.752 mA, Vdiff = 1.7819 V, peak|I| = 9.752 mA :: Ammeter | I = 9.752 mA
5 LEDElm: I = 9.752 mA, Vdiff = 1.7819 V, peak|I| = 9.791 mA :: LED (default-led) | I = 9.752 mA | Vd = 1.782 V | P = 17.377 mW

### pullupButton: button released  (sim t = 50.1 ms)
V(pin) = 5.0000 V
0 VoltageElm: I = 0.000 mA, Vdiff = 5.0000 V, peak|I| = 0.000 mA :: voltage source | I = 0 A | Vd = 5 V | P = 0 W
2 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: resistor | I = 0 A | Vd = 0 V | R = 10 kΩ | P = 0 W
6 SwitchElm: I = 0.000 mA, Vdiff = 5.0000 V, peak|I| = 0.000 mA :: push switch (SPST) | open | Vd = 5 V

### pullupButton: button pressed  (sim t = 50.2 ms)
V(pin) = 0.0000 V
0 VoltageElm: I = 0.500 mA, Vdiff = 5.0000 V, peak|I| = 0.500 mA :: voltage source | I = 500 μA | Vd = 5 V | (R = 10 kΩ) | P = -2.5 mW
2 ResistorElm: I = 0.500 mA, Vdiff = 5.0000 V, peak|I| = 0.500 mA :: resistor | I = 500 μA | Vd = 5 V | R = 10 kΩ | P = 2.5 mW
6 SwitchElm: I = 0.500 mA, Vdiff = 0.0000 V, peak|I| = 0.500 mA :: push switch (SPST) | closed | V = 0 V | I = 500 μA

### ammeterSeriesParallel: meter in series (Sser closed, Spar open)  (sim t = 50.1 ms)
0 VoltageElm: I = 40.881 mA, Vdiff = 9.0000 V, peak|I| = 40.881 mA :: voltage source | I = 40.881 mA | Vd = 9 V | (R = 220.15 Ω) | P = -367.931 mW
2 SwitchElm: I = 40.881 mA, Vdiff = 0.0000 V, peak|I| = 40.881 mA :: switch (SPST) | closed | V = 9 V | I = 40.881 mA
3 ResistorElm: I = 40.881 mA, Vdiff = 8.9939 V, peak|I| = 40.881 mA :: resistor | I = 40.881 mA | Vd = 8.994 V | R = 220 Ω | P = 367.68 mW
5 ResistorElm: I = 40.881 mA, Vdiff = 0.0041 V, peak|I| = 40.881 mA :: resistor | I = 40.881 mA | Vd = 4.088 mV | R = 100 mΩ | P = 167.127 μW
6 FuseElm: I = 40.881 mA, Vdiff = 0.0020 V, peak|I| = 40.881 mA :: fuse | I = 40.881 mA | Vd = 2.044 mV | R = 50 mΩ | I2t = 0.5 | 0% melted
11 SwitchElm: I = 0.000 mA, Vdiff = 8.9939 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 8.994 V

### ammeterSeriesParallel: meter across battery (Sser open, Spar closed)  (sim t = 50.1 ms)
fuse blown at sim t = 0.145 ms
0 VoltageElm: I = 0.000 mA, Vdiff = 9.0000 V, peak|I| = 60000.000 mA :: voltage source | I = 9 nA | Vd = 9 V | (R = 1 GΩ) | P = -81 nW
2 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 0 V
3 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: resistor | I = 0 A | Vd = 0 V | R = 220 Ω | P = 0 W
5 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 60000.000 mA :: resistor | I = 9 nA | Vd = 900 pV | R = 100 mΩ | P = 0 W
6 FuseElm: I = 0.000 mA, Vdiff = 9.0000 V, peak|I| = 60000.000 mA :: fuse (blown) | I = 9 nA | Vd = 9 V | R = 50 mΩ | I2t = 0.5
11 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | closed | V = 9 V | I = 9 nA

### hBridge: forward S1+S4  (sim t = 50.0 ms)
0 VoltageElm: I = 571.429 mA, Vdiff = 6.0000 V, peak|I| = 571.429 mA :: voltage source | I = 571.429 mA | Vd = 6 V | (R = 10.5 Ω) | P = -3.429 W
2 ResistorElm: I = 571.429 mA, Vdiff = 0.2857 V, peak|I| = 571.429 mA :: resistor | I = 571.429 mA | Vd = 285.714 mV | R = 500 mΩ | P = 163.265 mW
5 SwitchElm: I = 571.429 mA, Vdiff = 0.0000 V, peak|I| = 571.429 mA :: switch (SPST) | closed | V = 5.714 V | I = 571.429 mA
6 SwitchElm: I = 0.000 mA, Vdiff = 5.7143 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 5.714 V
7 SwitchElm: I = 0.000 mA, Vdiff = 5.7143 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 5.714 V
8 SwitchElm: I = 571.429 mA, Vdiff = 0.0000 V, peak|I| = 571.429 mA :: switch (SPST) | closed | V = 0 V | I = 571.429 mA
12 ResistorElm: I = 571.429 mA, Vdiff = 5.7143 V, peak|I| = 571.429 mA :: resistor | I = 571.429 mA | Vd = 5.714 V | R = 10 Ω | P = 3.265 W
14 InductorElm: I = 571.429 mA, Vdiff = 0.0000 V, peak|I| = 571.429 mA :: inductor | I = 571.429 mA | Vd = 0.22 pV | L = 10 mH | P = 0.126 pW
15 AmmeterElm: I = 571.429 mA, Vdiff = 0.0000 V, peak|I| = 571.429 mA :: Ammeter | I = 571.429 mA

### hBridge: reverse S2+S3  (sim t = 50.1 ms)
0 VoltageElm: I = 571.429 mA, Vdiff = 6.0000 V, peak|I| = 571.429 mA :: voltage source | I = 571.429 mA | Vd = 6 V | (R = 10.5 Ω) | P = -3.429 W
2 ResistorElm: I = 571.429 mA, Vdiff = 0.2857 V, peak|I| = 571.429 mA :: resistor | I = 571.429 mA | Vd = 285.714 mV | R = 500 mΩ | P = 163.265 mW
5 SwitchElm: I = 0.000 mA, Vdiff = 5.7143 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 5.714 V
6 SwitchElm: I = 571.429 mA, Vdiff = 0.0000 V, peak|I| = 571.429 mA :: switch (SPST) | closed | V = 0 V | I = 571.429 mA
7 SwitchElm: I = 571.429 mA, Vdiff = 0.0000 V, peak|I| = 571.429 mA :: switch (SPST) | closed | V = 5.714 V | I = 571.429 mA
8 SwitchElm: I = 0.000 mA, Vdiff = 5.7143 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 5.714 V
12 ResistorElm: I = -571.429 mA, Vdiff = -5.7143 V, peak|I| = 571.429 mA :: resistor | I = 571.429 mA | Vd = 5.714 V | R = 10 Ω | P = 3.265 W
14 InductorElm: I = -571.429 mA, Vdiff = -0.0000 V, peak|I| = 571.429 mA :: inductor | I = 571.429 mA | Vd = 0.219 pV | L = 10 mH | P = 0.125 pW
15 AmmeterElm: I = -571.429 mA, Vdiff = 5.7143 V, peak|I| = 571.429 mA :: Ammeter | I = -571.429 mA

### hBridge: brake S2+S4  (sim t = 50.1 ms)
0 VoltageElm: I = 0.000 mA, Vdiff = 6.0000 V, peak|I| = 0.000 mA :: voltage source | I = 0 A | Vd = 6 V | P = 0 W
2 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: resistor | I = 0 A | Vd = 0 V | R = 500 mΩ | P = 0 W
5 SwitchElm: I = 0.000 mA, Vdiff = 6.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 6 V
6 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | closed | V = 0 V | I = 0 A
7 SwitchElm: I = 0.000 mA, Vdiff = 6.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 6 V
8 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | closed | V = 0 V | I = 0 A
12 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: resistor | I = 0 A | Vd = 0 V | R = 10 Ω | P = 0 W
14 InductorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: inductor | I = 0 A | Vd = 0 V | L = 10 mH | P = 0 W
15 AmmeterElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: Ammeter | I = 0 A

### hBridge: coast (all open)  (sim t = 50.1 ms)
0 VoltageElm: I = 0.000 mA, Vdiff = 6.0000 V, peak|I| = 0.000 mA :: voltage source | I = 0 A | Vd = 6 V | P = 0 W
2 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: resistor | I = 0 A | Vd = 0 V | R = 500 mΩ | P = 0 W
5 SwitchElm: I = 0.000 mA, Vdiff = 6.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 6 V
6 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 0 V
7 SwitchElm: I = 0.000 mA, Vdiff = 6.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 6 V
8 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 0 V
12 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: resistor | I = 0 A | Vd = 0 V | R = 10 Ω | P = 0 W
14 InductorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: inductor | I = 0 A | Vd = 0 V | L = 10 mH | P = 0 W
15 AmmeterElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: Ammeter | I = 0 A

### hBridge: shoot-through S1+S2 (left leg)  (sim t = 50.1 ms)
0 VoltageElm: I = 12000.000 mA, Vdiff = 6.0000 V, peak|I| = 12000.000 mA :: voltage source | I = 12 A | Vd = 6 V | (R = 500 mΩ) | P = -72 W
2 ResistorElm: I = 12000.000 mA, Vdiff = 6.0000 V, peak|I| = 12000.000 mA :: resistor | I = 12 A | Vd = 6 V | R = 500 mΩ | P = 72 W
5 SwitchElm: I = 12000.000 mA, Vdiff = 0.0000 V, peak|I| = 12000.000 mA :: switch (SPST) | closed | V = 0 V | I = 12 A
6 SwitchElm: I = 12000.000 mA, Vdiff = 0.0000 V, peak|I| = 12000.000 mA :: switch (SPST) | closed | V = 0 V | I = 12 A
7 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 0 V
8 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 0 V
12 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: resistor | I = 0 A | Vd = 0 V | R = 10 Ω | P = 0 W
14 InductorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: inductor | I = 0 A | Vd = 0 V | L = 10 mH | P = 0 W
15 AmmeterElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: Ammeter | I = 0 A

### hBridge: shoot-through S3+S4 (right leg)  (sim t = 50.0 ms)
0 VoltageElm: I = 12000.000 mA, Vdiff = 6.0000 V, peak|I| = 12000.000 mA :: voltage source | I = 12 A | Vd = 6 V | (R = 500 mΩ) | P = -72 W
2 ResistorElm: I = 12000.000 mA, Vdiff = 6.0000 V, peak|I| = 12000.000 mA :: resistor | I = 12 A | Vd = 6 V | R = 500 mΩ | P = 72 W
5 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 0 V
6 SwitchElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: switch (SPST) | open | Vd = 0 V
7 SwitchElm: I = 12000.000 mA, Vdiff = 0.0000 V, peak|I| = 12000.000 mA :: switch (SPST) | closed | V = 0 V | I = 12 A
8 SwitchElm: I = 12000.000 mA, Vdiff = 0.0000 V, peak|I| = 12000.000 mA :: switch (SPST) | closed | V = 0 V | I = 12 A
12 ResistorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: resistor | I = 0 A | Vd = 0 V | R = 10 Ω | P = 0 W
14 InductorElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: inductor | I = 0 A | Vd = 0 V | L = 10 mH | P = 0 W
15 AmmeterElm: I = 0.000 mA, Vdiff = 0.0000 V, peak|I| = 0.000 mA :: Ammeter | I = 0 A

### hBridge dynamic: forward, then brake (S1 open, S2 closed; S4 stays closed)
switch positions S1S2S3S4 before (0 = closed): 0110  motor I = 571.4 mA
switch positions after clicks: 1010
t+0 ms: motor I = 570.0 mA
t+0.5 ms: motor I = 347.5 mA
t+1 ms: motor I = 210.7 mA
t+2 ms: motor I = 77.5 mA
t+3 ms: motor I = 28.5 mA
t+5 ms: motor I = 3.9 mA
```
