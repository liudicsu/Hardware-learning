# Explanatory diagrams (src/components/diagrams)

Diagrams that only explain (no live computation) are drawn by us as SVG in the page, unless a suitable
open-source diagram exists. Dark theme, zh/en labels passed as props, readable at 390 px
(SVG scales with `w-full`; text is 14–18 viewBox units on a ~450–500-unit-wide box, ≈ 12 px at 390 px).

## `<Timing>` (server-safe, no hooks) — `src/components/diagrams/Timing.tsx`

```tsx
<Timing
  title="caption and accessible name"
  axisLabel="time →"                         // optional, under the axis
  columns={[1, 3, 1, 3]}                      // optional relative widths (e.g. µs); default equal
  signals={[
    { name: "PWM", levels: [1, 0, 1, 0] },                    // digital: 0 low, other numbers high,
    { name: "SDA", kind: "bus", values: ["", "0x68", "ACK"] }, //   "x" unknown, "z" released (mid line)
  ]}                                          // bus: data bands, equal neighbours merge, "" / "x" = unknown
  rows={[{ name: "bit", cells: ["S", "0", "1"] }]}            // optional text rows, one cell per column
  spans={[{ from: 0, to: 0, label: "0.5 ms" }, { from: 0, to: 1, label: "period 2.0 ms", side: "bottom" }]}
  highlight={2}                               // optional column highlight
/>
```

Column edges come from `columnEdges(n, columns)`. Text is 14–18 viewBox units; the SVG never scales below
0.62 px per unit (≈ 10 px text) — a long frame (e.g. a 12-bit UART frame) scrolls horizontally inside its
own box rather than overflowing the page. Intended reuse: PWM (`columns` = high/low durations, `spans` for
pulse width and period), UART (start/data/stop bits as a digital signal plus a `bit` row), I²C (SCL digital,
SDA `bus` with address/ACK bands, "z" for the released line), servo pulses (1.0–2.0 ms `spans` in a 20 ms frame).

## `<TimingStepper>` (client)

Same props plus `stepText: string[]` (one line per column). Uses the shared `<StepControls>` from the diagram
foundation (#18): Previous / All / Next, labels from `src/lib/diagrams/ui.ts`; the lesson page injects `locale`.
Colours use the `--dg-*` tokens from `globals.css`, the frame matches `<Diagram>`.

### In the registry: `kind: "timing"`

A timing diagram can also be a registry spec (`TimingSpec` in `src/lib/diagrams/types.ts`), used from MDX as
`<Diagram id="..." />` and drawn by `TimingDiagram.tsx` with `<TimingSvg>`: signals / rows / spans / axis label in
`L10n`, optional `steps` (`column` to highlight and/or `signals` to keep bright), `numbers` (values computed in the
spec and compared with the lesson) and `facts`. `tools/check_diagrams.mjs` checks both languages, equal column counts,
span and label widths, and that the diagram fits a 390 px phone at the minimum text scale (layout constants are read
from `Timing.tsx`). Signals may carry `average: { level, label }`, a dashed line at that fraction of the trace height.
First user: `pwm-duty-average` (arduino-io).

Layout options (D-5):
- `columnScale`: viewBox units per unit of `columns`. Every line then shares one time scale, e.g. the debounce
  diagram draws a 0.9 ms bounce and the 30 ms window in proportion.
- `lines`: column ranges drawn one under the other. They must cover all columns in order.
- `narrowLines`: the ranges used below 640 px. They may leave columns out; PWM shows one period on phones.
- Each line's box is sized to its own viewBox width, capped at 1.3 px per unit, so every line shares one scale.
- check_diagrams requires the smallest SVG text (14 units) to render at >= 12 px: at 390 px, the narrow lines
  in a 332 px box; at 640 px, the wide lines in a 582 px box. It also checks that bus values fit their bands,
  row cells their columns, and that spans do not cross a line break.

Data files: `src/lib/diagrams/data/*.json` may be imported by a spec (the check inlines them). Each file names
the script that writes it in `"source"`; check_diagrams re-runs `python3 <source>` and requires identical
output. First file: `debounce-bounce.json` from `tools/sim/models/debounce_export.py` (debounce_sim.py, seed 1).

The encoder diagrams stay `<QuadratureTiming>`: their columns are computed at render time from
`src/lib/models/encoder.ts`, which `check_widgets.mjs` compares with `encoder_sim.py`'s output. A registry spec is
plain data loaded by `check_diagrams.mjs` without a bundler, so moving them would mean copying the model's output
into the spec (two sources of truth) or adding a bundling step to the check.

### In the registry: `kind: "bytes"` (D-6)

`BytesSpec` draws protocol packets byte by byte with `ByteFields.tsx` (client): one button per packet, a strip of
cells coloured by field (`fields: { key: { label, tone } }`), brackets above (`side: "top"`, e.g. a little-endian
value) and below (`side: "bottom"`, e.g. the checksum range), and an HTML table (#, byte, field, meaning) that wraps
on phones. A byte with `bad: true` is drawn in the danger tone. The strip uses the longest packet's width so cells
keep their size when switching. Optional `script: { run, lines }`: check_diagrams runs `python3 run` from the
script's folder and requires every line in its output, so the drawn bytes are the script's bytes.
check_diagrams also checks field keys, byte ranges, notes in both languages, bracket ranges and label widths,
non-overlapping brackets per side, hex text inside a cell, and >= 12 px labels at 390 px (constants read from
`ByteFields.tsx`). First user: `sts-packet-fields` (so101-arm, `sts_packet.py`).
### In the registry: `kind: "poseGraph"` (D-7)

`PoseGraphSpec` steps through a SLAM pose graph with `PoseGraph.tsx` (client): `estimate` (where each node was
stored, as odometry saw it), `corrected` (after the loop closure) and `truth`, plus `frames` that show the first
`upto` nodes, the spacing label, scan-match edges from one node to the previous `matchWindow`, the drift gap, or the
loop closure with the corrected graph over the faint estimate. "All" shows the final state. One viewBox for every
frame (100 units per metre, at most 360 wide). The spec also carries every lidar scan (`scans`, odometry and true
pose) and the indices that became nodes. check_diagrams re-derives the nodes with SLAM Toolbox 2.8.5's rule
(shouldProcessScan: drop a scan closer than sqrt(0.8) x minimum_travel_distance in a straight line from the last
scan that passed, heading ignored; then Karto HasMovedEnough: 0.2 m or 0.2 rad from the last node), with the
values read from slam.yaml, the URDF lidar offset, the Gazebo lidar rate and tour.py's speeds, and the 2.8.5
defaults (factor 0.8, minimum_time_interval 0.5 s) written in the check with their source lines. It fails if
pixi.lock stops pinning 2.8.5 or slam.yaml starts setting a parameter the rule assumes at its default. Labels must
fit the viewBox and render at >= 12 px on a 390 px phone. First user: `slam-pose-graph` (slam-nav); the route, the
3 % turn error, the 3 matching edges and the linear correction are illustrative and the caption says so.

## Consistency with scripts

If a diagram depicts the output of a lesson script, generate its columns from a TS port in `src/lib/models`
and check it in `tools/check_widgets.mjs`. First example: `QuadratureTiming` (motors-drivers) uses
`diagramColumns()` from `src/lib/models/encoder.ts`, a port of `tools/sim/models/encoder_sim.py`; the check
compares the decoder lines of `m2-encoder_sim.txt` byte for byte and the forward/reverse state order.
