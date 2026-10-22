"use client";

import { useState } from "react";
import type { Locale } from "@/lib/diagrams/types";
import { StepControls } from "./StepControls";
import { TimingSvg, type TimingProps } from "./Timing";

export interface TimingStepperProps extends Omit<TimingProps, "highlight"> {
  /** Text shown for each column when it is selected, e.g. "AB 10 → 11: +1, count 2". */
  stepText: string[];
  /** Supplied by the lesson page; selects the StepControls labels. */
  locale: Locale;
}

/**
 * A <Timing> diagram with the shared <StepControls> (Previous / All / Next): each step
 * highlights one column and shows its line of text; "All" shows the diagram undimmed.
 */
export function TimingStepper({ id, title, stepText, locale, ...rest }: TimingStepperProps) {
  const [i, setI] = useState(-1);
  return (
    <figure
      className="not-prose my-6 max-w-full overflow-hidden rounded-xl border border-zinc-800 bg-[var(--dg-card)] px-3 py-3 sm:px-4"
      data-timing={id ?? ""}
      data-timing-step={i}
    >
      <figcaption className="mb-2 text-sm font-medium text-zinc-200">{title}</figcaption>
      <div className="max-w-2xl overflow-x-auto">
        <TimingSvg title={title} highlight={i >= 0 ? i : undefined} {...rest} />
      </div>
      <StepControls locale={locale} n={stepText.length} i={i} onChange={setI} text={i >= 0 ? stepText[i] : undefined} />
    </figure>
  );
}
