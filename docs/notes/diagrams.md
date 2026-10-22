# Explanatory diagrams (src/components/diagrams)

Diagrams that only explain (no live computation) are drawn by us as SVG in the page, unless a suitable
open-source diagram exists. Dark theme, zh/en labels passed as props, readable at 390 px
(SVG scales with `w-full`; text is 14–18 viewBox units on a ~450–500-unit-wide box, ≈ 12 px at 390 px).

## `<Timing>` (server-safe, no hooks)

```tsx
<Timing
  title="caption and accessible name"
  axisLabel="each column = …"            // optional, under the axis
  signals={[{ name: "A", levels: [0, 1, 1, 0] }, { name: "B", levels: [0, 0, 1, 1], color: "#f59e0b" }]}
  rows={[{ name: "AB", cells: ["00", "10", "11", "01"] }]}   // optional label rows, one cell per column
  highlight={2}                          // optional column highlight
/>
```

Equal-width columns; one logic level per signal per column. Intended reuse: PWM (duty as columns high/low),
UART frames (start/data/stop bits as rows), I²C (SCL/SDA with START/ACK rows), servo pulses.

## `<TimingStepper>` (client)

Same props plus `stepText: string[]` (one line per column). Previous/Next buttons move the highlight; the
lesson page injects the localized button labels from `messages/*.json` → `diagram`.

## Consistency with scripts

If a diagram depicts the output of a lesson script, generate its columns from a TS port in `src/lib/models`
and check it in `tools/check_widgets.mjs`. First example: `QuadratureTiming` (motors-drivers) uses
`diagramColumns()` from `src/lib/models/encoder.ts`, a port of `tools/sim/models/encoder_sim.py`; the check
compares the decoder lines of `m2-encoder_sim.txt` byte for byte and the forward/reverse state order.
