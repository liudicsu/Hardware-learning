"use client";

import { useState } from "react";
import { tx, type Locale, type TimingSpec, type Tone } from "@/lib/diagrams/types";
import { StepControls } from "./StepControls";
import { TimingSvg } from "./Timing";

const TONE: Record<Tone, string> = {
  ink: "var(--dg-ink)",
  muted: "var(--dg-muted)",
  a: "var(--dg-a)",
  b: "var(--dg-b)",
  ok: "var(--dg-ok)",
  danger: "var(--dg-danger)",
};

/** A registry timing spec (kind "timing") drawn with <TimingSvg>, with optional steps. */
export function TimingDiagram({ spec, locale }: { spec: TimingSpec; locale: Locale }) {
  const [i, setI] = useState(-1);
  const steps = spec.steps ?? [];
  const st = i >= 0 ? steps[i] : undefined;
  const title = tx(spec.title, locale);
  return (
    <div data-timing={spec.id} data-timing-step={i}>
      <div className="max-w-2xl overflow-x-auto">
        <TimingSvg
          title={title}
          columns={spec.columns}
          axisLabel={spec.axisLabel ? tx(spec.axisLabel, locale) : undefined}
          signals={spec.signals.map((s) => ({
            name: tx(s.name, locale),
            kind: s.kind,
            levels: s.levels,
            values: s.values?.map((v) => tx(v, locale)),
            color: s.tone ? TONE[s.tone] : undefined,
            average: s.average ? { level: s.average.level, label: tx(s.average.label, locale) } : undefined,
          }))}
          rows={spec.rows?.map((r) => ({ name: tx(r.name, locale), cells: r.cells.map((c) => tx(c, locale)), mono: r.mono }))}
          spans={spec.spans?.map((s) => ({ from: s.from, to: s.to, side: s.side, label: tx(s.label, locale) }))}
          highlight={st?.column}
          activeSignals={st?.signals}
        />
      </div>
      {steps.length > 0 && <StepControls locale={locale} n={steps.length} i={i} onChange={setI} text={st ? tx(st.label, locale) : undefined} />}
    </div>
  );
}
