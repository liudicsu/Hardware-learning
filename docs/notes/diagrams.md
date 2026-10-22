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

The encoder diagrams stay `<QuadratureTiming>`: their columns are computed at render time from
`src/lib/models/encoder.ts`, which `check_widgets.mjs` compares with `encoder_sim.py`'s output. A registry spec is
plain data loaded by `check_diagrams.mjs` without a bundler, so moving them would mean copying the model's output
into the spec (two sources of truth) or adding a bundling step to the check.

## Consistency with scripts

If a diagram depicts the output of a lesson script, generate its columns from a TS port in `src/lib/models`
and check it in `tools/check_widgets.mjs`. First example: `QuadratureTiming` (motors-drivers) uses
`diagramColumns()` from `src/lib/models/encoder.ts`, a port of `tools/sim/models/encoder_sim.py`; the check
compares the decoder lines of `m2-encoder_sim.txt` byte for byte and the forward/reverse state order.
