"use client";

import { useState } from "react";
import { DIAGRAMS } from "@/lib/diagrams";
import { tx, type Locale } from "@/lib/diagrams/types";
import { DIAGRAM_UI } from "@/lib/diagrams/ui";
import { BlockDiagramSvg } from "./BlockDiagram";
import { StepControls } from "./StepControls";

const REPO = "https://github.com/liudicsu/Hardware-learning/blob/main";

export interface DiagramProps {
  /** Key in the registry (src/lib/diagrams/index.ts). */
  id: string;
  locale: Locale;
}

/**
 * Registry entry point used from MDX as <Diagram id="..." />. The lesson page supplies the
 * locale, so zh.mdx and en.mdx contain the identical tag and the labels come from the spec.
 * Below 640 px the narrow layout is shown, above it the wide one; neither scrolls sideways.
 */
export function Diagram({ id, locale }: DiagramProps) {
  const spec = DIAGRAMS[id];
  const [step, setStep] = useState(-1);
  if (!spec) throw new Error(`Unknown diagram id "${id}"`);
  const steps = spec.steps ?? [];
  const highlight = step >= 0 ? steps[step].highlight : undefined;
  const ui = DIAGRAM_UI[locale];
  return (
    <figure className="not-prose my-6 max-w-full overflow-hidden rounded-xl border border-zinc-800 bg-[var(--dg-card)] px-3 py-3 sm:px-4" data-diagram={id}>
      <figcaption className="mb-2 text-sm font-medium text-zinc-200">{tx(spec.title, locale)}</figcaption>
      <div className="min-w-0">
        <BlockDiagramSvg spec={spec} layout={spec.layouts.narrow} locale={locale} highlight={highlight} className="mx-auto block sm:hidden" />
        <BlockDiagramSvg spec={spec} layout={spec.layouts.wide} locale={locale} highlight={highlight} className="mx-auto hidden sm:block" />
      </div>
      {steps.length > 0 && (
        <StepControls locale={locale} n={steps.length} i={step} onChange={setStep} text={step >= 0 ? tx(steps[step].label, locale) : undefined} />
      )}
      {spec.caption && <p className="mt-2 text-sm text-zinc-400">{tx(spec.caption, locale)}</p>}
      <p className="mt-2 flex flex-wrap gap-x-2 gap-y-1 text-xs text-zinc-500">
        <span>{ui.source}:</span>
        {spec.sources.map((s) => (
          <a key={s} href={`${REPO}/${s}`} target="_blank" rel="noreferrer" className="min-w-0 break-all font-mono text-sky-400 hover:text-sky-300">
            {s} ↗
          </a>
        ))}
      </p>
    </figure>
  );
}
