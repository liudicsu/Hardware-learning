"use client";

import { useState } from "react";
import { tx, type Locale, type TimingSpec } from "@/lib/diagrams/types";
import { TONE } from "./BlockDiagram";
import { StepControls } from "./StepControls";
import { TimingSvg, columnCount, timingWidth, type TimingProps } from "./Timing";

type Range = [number, number];
type Step = NonNullable<TimingSpec["steps"]>[number] | undefined;

/** TimingSvg props for the columns first..last of a spec (spans outside the range are dropped). */
function lineProps(spec: TimingSpec, locale: Locale, [a, b]: Range, step: Step): Omit<TimingProps, "id"> {
  const cut = <T,>(xs: T[] | undefined) => xs?.slice(a, b + 1);
  return {
    title: tx(spec.title, locale),
    columns: cut(spec.columns),
    columnScale: spec.columnScale,
    axisLabel: spec.axisLabel ? tx(spec.axisLabel, locale) : undefined,
    signals: spec.signals.map((s) => ({
      name: tx(s.name, locale),
      kind: s.kind,
      levels: cut(s.levels),
      values: cut(s.values)?.map((v) => tx(v, locale)),
      color: s.tone ? TONE[s.tone] : undefined,
      average: s.average ? { level: s.average.level, label: tx(s.average.label, locale) } : undefined,
    })),
    rows: spec.rows?.map((r) => ({ name: tx(r.name, locale), cells: r.cells.slice(a, b + 1).map((c) => tx(c, locale)), mono: r.mono })),
    spans: spec.spans
      ?.filter((s) => s.from >= a && s.to <= b)
      .map((s) => ({ from: s.from - a, to: s.to - a, side: s.side, label: tx(s.label, locale) })),
    highlight: step?.column !== undefined && step.column >= a && step.column <= b ? step.column - a : undefined,
    activeSignals: step?.signals,
  };
}

/** Lines one under the other; each line's box is sized to its viewBox width, so all share one scale. */
function Lines({ spec, locale, lines, step, className }: { spec: TimingSpec; locale: Locale; lines: Range[]; step: Step; className?: string }) {
  const props = lines.map((r) => lineProps(spec, locale, r, step));
  const widths = props.map((p) => timingWidth(p));
  const max = Math.max(...widths);
  return (
    <div className={className} style={{ maxWidth: Math.round(max * 1.3) }}>
      {props.map((p, k) => (
        <div key={k} data-timing-line={k} className={k ? "mt-2" : undefined} style={{ width: `${(widths[k] / max) * 100}%` }}>
          <TimingSvg {...p} />
        </div>
      ))}
    </div>
  );
}

/** A registry timing spec (kind "timing") drawn with <TimingSvg>, with optional steps and line breaks. */
export function TimingDiagram({ spec, locale }: { spec: TimingSpec; locale: Locale }) {
  const [i, setI] = useState(-1);
  const steps = spec.steps ?? [];
  const st = i >= 0 ? steps[i] : undefined;
  const n = columnCount({ signals: spec.signals.map((s) => ({ name: "", kind: s.kind, levels: s.levels, values: s.values?.map(() => "") })), rows: spec.rows?.map((r) => ({ name: "", cells: r.cells.map(() => "") })), columns: spec.columns });
  const lines = spec.lines ?? [[0, n - 1]];
  const narrow = spec.narrowLines;
  return (
    <div data-timing={spec.id} data-timing-step={i}>
      {narrow ? (
        <>
          <Lines spec={spec} locale={locale} lines={narrow} step={st} className="sm:hidden" />
          <Lines spec={spec} locale={locale} lines={lines} step={st} className="hidden sm:block" />
        </>
      ) : (
        <Lines spec={spec} locale={locale} lines={lines} step={st} />
      )}
      {steps.length > 0 && <StepControls locale={locale} n={steps.length} i={i} onChange={setI} text={st ? tx(st.label, locale) : undefined} />}
    </div>
  );
}
