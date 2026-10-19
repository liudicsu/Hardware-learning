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
- No raw HTML; no images (we have none yet); no `import` statements.
- MDX gotchas: `{` `}` `<` `>` in prose must be escaped or put in inline code
  (`` `a < b` ``). Write "less than" or use `&lt;` if needed.

## Components available in MDX (no import needed)

```mdx
<Falstad title="Voltage divider" circuit="dividerPractice" height={420} />
```
`circuit` is a key from `src/lib/circuits.ts`: `ohms`, `voltdivide`,
`dividerPractice`, `resistors`, `transistorLed`, `capac`, `transswitch`.

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
  The component shows "Simulated output / 仿真输出" and the note that real hardware values will differ.
  Outputs from real runs on a computer (e.g. Month 1 Python, `overflow.c`) are not labelled.
- **Reproducibility:** add every simulated run to `tools/sim/reproduce.sh` and its quoted output to `tools/sim/expected/`;
  real computer runs go into a `check.sh` next to the examples (see `examples/month-1/check.sh`). Both must pass from a clean checkout.
- **Long code blocks fold automatically:** any fenced block over 30 lines shows its first 15 lines with an
  "Expand all / 展开全部" button. Every block has a Copy button. Nothing to do in MDX; just don't split code to avoid folding.
