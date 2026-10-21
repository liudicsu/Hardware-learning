# Lesson content guide

Lessons live in `src/content/m<month>/<lesson-slug>/{zh,en}.mdx`. The page around
the MDX already renders: the lesson title, summary, the task checklist (from
`src/lib/curriculum.ts`), the resource cards for the lesson, the "mark done"
button and prev/next navigation. **Do not repeat those in the MDX** (no H1, no
final task list, no resource list at the end).

## Writing rules

- Original text only. Explain in your own words; never paste text from the
  linked resources. Short factual formulas/tables are fine.
- Technically accurate. Double-check every number in examples and quizzes.
- Each lesson is self-contained and genuinely teaches: concept → worked
  example → try it (simulator / quiz / exercise) → common mistakes.
- Use `##` for sections (4–7 per lesson) and `###` for sub-sections.
- zh and en files must have the same structure, same components, same quiz
  ids and the same numbers. zh is natural Simplified Chinese (not a literal
  translation); keep technical terms with English in brackets the first time,
  e.g. 分压器（voltage divider）.
- Units: use Ω, kΩ, µF, mA, V with a normal space between number and unit
  (`4.7 kΩ`). Use `×` for multiplication in prose.
- Code blocks use fenced code with a language (```python, ```bash, ```text).
- No raw HTML; no `import` statements.
- Images live under `public/m<N>/...` and are referenced with a normal Markdown image:
  `![alt text](/m3/servo_bracket.png)`. The site adds the base path, so the path starts with `/m<N>/`.
  Alt text is required and describes what the image shows; zh and en use the same image.
- MDX gotchas: `{` `}` `<` `>` in prose must be escaped or put in inline code
  (`` `a < b` ``). Write "less than" or use `&lt;` if needed.

## Components available in MDX (no import needed)

### Falstad

```mdx
<Falstad title="Voltage divider" circuit="dividerPractice" height={420} />
```
`circuit` is a key from `src/lib/circuits.ts`: `ohms`, `voltdivide`,
`dividerPractice`, `loadedDivider`, `ledLimit`, `pullupButton`,
`ammeterSeriesParallel`, `hBridge`, `resistors`, `transistorLed`, `pwmAverage`,
`levelDivider`, `i2cPullup`, `inductkick`, `inductkickBlock`, `capac`,
`transswitch`.

New circuits are `cct` text in `src/lib/circuits.ts` with a comment stating every
component value. Every reading quoted in lesson text must be measured in the real
CircuitJS (see `docs/notes/falstad-measure.cjs` and
`docs/notes/falstad-measurements.md`), then quoted with sensible rounding
(`约 9.8 mA`, not the raw `9.752 mA`).

### Wokwi

```mdx
<Wokwi
  board="uno"
  files={[
    "examples/month-2/arduino-io/blink_custom/blink_custom.ino",
    "examples/month-2/arduino-io/blink_custom/diagram.json",
  ]}
>
Optional note shown under the steps.
</Wokwi>
```
`board` is `uno` or `esp32-s3`; `files` are repo paths. Convention:
Wokwi is linked, never embedded in an iframe. The `diagram.json` lives next to
the sketch in `examples/`, and the `.ino` stays the repo file byte-for-byte (the
reader pastes both into a new Wokwi project). Part types and pins must come from
docs.wokwi.com (see `docs/notes/wokwi-parts-check.md`);
`tools/check_wokwi.py` validates the diagrams and the cards. Use `projectId` only
once a public project exists on the owner's account. Keep the default button
bounce (do not add `bounce: "0"`). The mainland-China network note is built into
the component, so do not repeat it in the lesson text.

```mdx
<Quiz id="q1" question="..." answer={1.6} unit="V" explanation="..." />
<Quiz id="q2" question="..." options={["A", "B", "C"]} answer={1} explanation="..." />
```
Numeric quizzes accept ±3 % by default (`tolerance={0.05}` to widen).
`id` must be unique within the lesson (q1, q2, ...). Strings are plain text.

```mdx
<Callout type="warn" title="Safety">Text with **markdown**.</Callout>
```
types: `info`, `tip`, `warn`, `danger`.

```mdx
<Formula label="Ohm's law">V = I × R</Formula>
<Resource id="falstad" />
```
`Resource` renders an inline resource card; ids are in `src/lib/resources.ts`.
Use at most 1–2 inline cards per lesson, where the reader should open it right
now (the full list is already shown at the end of the page).

### Formula widgets (simplified model)

Three interactive widgets replay the Python toy models that lessons already
quote. Put them on their own line with blank lines around, and add no `import`:

```mdx
<PidWidget />
<IkWidget />
<CameraWidget />
<LineFollowWidget />
<ComplementaryWidget />
```

- `PidWidget` mirrors `tools/sim/models/pid_sim.py` (PID step response, 0 → 60°).
- `IkWidget` mirrors `tools/sim/models/kinematics.py` (3-joint arm, forward and
  inverse kinematics, singularities).
- `CameraWidget` mirrors
  `examples/month-5/camera-calibration/make_views.py` (pinhole projection and
  radial distortion).
- `LineFollowWidget` mirrors `tools/sim/models/line_sim.py` (line follower,
  P and PD on 8 reflectance sensors).
- `ComplementaryWidget` is the one widget that is **not** a line-by-line port:
  `tools/sim/models/filter_sim.py` adds seeded random noise, so the widget uses the
  analytic steady-state offset α/(1−α)·bias·dt. It agrees with the script's
  `offset_flat` column to 1 decimal place, the check tests exactly that, and the
  widget says so on the page in zh and en.

Rules:

- A widget is a line-by-line TypeScript port of the Python model the lesson
  already quotes: same constants, step sizes, integration order and output
  formatting. The model lives as a pure module in `src/lib/models/`, separate
  from the React UI in `src/components/widgets/`.
- Every model has a check in `tools/check_widgets.mjs` that prints its output
  formatted exactly like the expected file and compares it byte for byte with
  the lines in `tools/sim/expected/`. It runs in CI and from
  `tools/sim/reproduce.sh`.
- The one exception to byte-for-byte checks is the kinematics "same with
  lambda = 0.01" line. That run never converges and is chaotic, and JavaScript
  and glibc trig functions differ by 1 ulp, so no port can byte-match it;
  `tools/check_widgets.mjs` checks it only qualitatively (same wording, and the
  TS run also fails to settle). The line is in the lesson only to show
  non-convergence.
- Every widget uses `WidgetShell`: the amber “简化模型 / Simplified model”
  label, a link to the script it mirrors, the note that real hardware values
  differ, and a reset button.
- Defaults equal the lesson's worked example, and the zh and en MDX use the
  same widget.
- It must work at 390 px width: no horizontal overflow, full-width sliders,
  and SVGs with a `viewBox` and `width: 100%`. Use plain SVG and React; no
  chart library.

## In-page table of contents

Every `## ` heading (outside code fences) becomes an entry in the lesson's "In this lesson / 本课内容" table of contents and gets an anchor id derived from its text. Keep h2 titles short and unique within a lesson; use `###` for sub-sections that should not appear in the TOC.

## Code, examples and simulated outputs (standard for every month)

- **Every runnable program quoted in a lesson lives in the repo**, byte-for-byte identical to the code block:
  sketches and scripts in `examples/month-N/<lesson-slug>/` (with a `README.md` listing hardware, wiring and build commands),
  simulators, harnesses and toy models in `tools/sim/`.
- **Link each such code block to its file** by putting `<CodeSource path="examples/month-2/motors-drivers/one_rev/one_rev.ino" />`
  on its own line (blank line before and after) directly above the fence. The link points at `blob/main/<path>`.
- **Label every output that comes from a simulator or toy model** by wrapping the fenced block:

  ~~~mdx
  <SimOutput source="avr">

  ```text
  done, count = 1441
  ```

  </SimOutput>
  ~~~

  `source="avr"` = firmware run in simavr with simulated parts; `source="model"` = a Python toy model.
  `source="ros"` = real ROS 2 software driving a simulated robot (Gazebo, or ros2_control mock hardware).
  `source="synthetic"` = real OpenCV code run on synthetic images rendered through a known camera (Month 5).
  Output of ROS 2 programs that need no robot at all (e.g. `ros2 topic list`, a bag of your own nodes) is a
  real run and is not labelled; it is checked by `examples/month-4/check.sh`.
  The component shows "Simulated output / 仿真输出" and the note that real hardware values will differ.
  Outputs from real runs on a computer (e.g. Month 1 Python, `overflow.c`) are not labelled.
- **Reproducibility:** add every simulated run to `tools/sim/reproduce.sh` and its quoted output to `tools/sim/expected/`;
  real computer runs go into a `check.sh` next to the examples (see `examples/month-1/check.sh`). Both must pass from a clean checkout.
- **Comparing quotes with the repo (`python3 tools/check_quotes.py`, also run by `tools/sim/reproduce.sh`):**
  every block under a `<CodeSource>` must be byte-for-byte its file, and every block inside a `<SimOutput>` must appear
  byte-for-byte, on whole lines, in a file in `tools/sim/expected/` or `examples/month-N/expected/`.
  **The one exception: shell command lines at the start of a block are not compared.** Leading lines that begin with
  `$ ` (dollar, space), up to the first line that does not, are left out on the lesson side, so a quote may show the
  `$ python3 …` prompt whether or not the expected file records it. Everything else, including a `$ ` line further
  down the block, still compares byte-for-byte; a block made only of `$ ` lines is an error.
- **Long code blocks fold automatically:** any fenced block over 30 lines shows its first 15 lines with an
  "Expand all / 展开全部" button. Every block has a Copy button. Nothing to do in MDX; just don't split code to avoid folding.

## Curriculum notes (decisions for later months)

- **PID lives in Month 3 as a site supplement** (`/month/month-3/pid-control`: P/I/D, windup, tuning, cascade loops,
  the balancer outer loop). When Month 5 ("Control theory, starting with PID") is written, do **not** repeat those basics:
  open with a "Review Month 3 PID / 复习第 3 个月的 PID" link to that lesson and go deeper — system modelling,
  the frequency domain (transfer functions, Bode plots, stability margins), and LQR.
- **Licence and price facts follow the official page** of the product (e.g. Autodesk Fusion for personal use: 1-year term,
  renewable) and add "check the official site when you sign up / 以注册时官网为准". Where the course text differs, the
  official page wins.
