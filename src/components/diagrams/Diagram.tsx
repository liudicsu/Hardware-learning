"use client";

import { useState, type ReactNode } from "react";
import { DIAGRAMS } from "@/lib/diagrams";
import { tx, type BlockDiagramSpec, type DiagramSpec, type Locale } from "@/lib/diagrams/types";
import { DIAGRAM_UI } from "@/lib/diagrams/ui";
import { BlockDiagramSvg } from "./BlockDiagram";
import { ByteFields } from "./ByteFields";
import { CircuitDiagram } from "./CircuitDiagram";
import { PoseGraph } from "./PoseGraph";
import { StepControls } from "./StepControls";
import { TimingDiagram } from "./TimingDiagram";

const REPO = "https://github.com/liudicsu/Hardware-learning/blob/main";

export interface DiagramProps {
  /** Key in the registry (src/lib/diagrams/index.ts). */
  id: string;
  locale: Locale;
}

/**
 * Registry entry point used from MDX as <Diagram id="..." />. The lesson page supplies the
 * locale, so zh.mdx and en.mdx contain the identical tag and the labels come from the spec.
 * Block diagrams show the narrow layout below 640 px and the wide one above it; circuits have
 * one layout of at most 360 units; timing diagrams scale with the width and are checked to fit a
 * 390 px screen. Nothing scrolls sideways.
 */
export function Diagram({ id, locale }: DiagramProps) {
  const spec = DIAGRAMS[id];
  if (!spec) throw new Error(`Unknown diagram id "${id}"`);
  return (
    <DiagramFrame spec={spec} locale={locale}>
      {spec.kind === "circuit" ? (
        <CircuitDiagram spec={spec} locale={locale} />
      ) : spec.kind === "timing" ? (
        <TimingDiagram spec={spec} locale={locale} />
      ) : spec.kind === "poseGraph" ? (
        <PoseGraph spec={spec} locale={locale} />
      ) : spec.kind === "bytes" ? (
        <ByteFields spec={spec} locale={locale} />
      ) : (
        <BlockBody spec={spec} locale={locale} />
      )}
    </DiagramFrame>
  );
}

function BlockBody({ spec, locale }: { spec: BlockDiagramSpec; locale: Locale }) {
  const [step, setStep] = useState(-1);
  const steps = spec.steps ?? [];
  const highlight = step >= 0 ? steps[step].highlight : undefined;
  return (
    <>
      <div className="min-w-0">
        <BlockDiagramSvg spec={spec} layout={spec.layouts.narrow} locale={locale} highlight={highlight} className="mx-auto block sm:hidden" />
        <BlockDiagramSvg spec={spec} layout={spec.layouts.wide} locale={locale} highlight={highlight} className="mx-auto hidden sm:block" />
      </div>
      {steps.length > 0 && (
        <StepControls locale={locale} n={steps.length} i={step} onChange={setStep} text={step >= 0 ? tx(steps[step].label, locale) : undefined} />
      )}
    </>
  );
}

function DiagramFrame({ spec, locale, children }: { spec: DiagramSpec; locale: Locale; children: ReactNode }) {
  const ui = DIAGRAM_UI[locale];
  return (
    <figure className="not-prose my-6 max-w-full overflow-hidden rounded-xl border border-zinc-800 bg-[var(--dg-card)] px-3 py-3 sm:px-4" data-diagram={spec.id}>
      <figcaption className="mb-2 text-sm font-medium text-zinc-200">{tx(spec.title, locale)}</figcaption>
      {children}
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
