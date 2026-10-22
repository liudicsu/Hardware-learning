"use client";

import { useState } from "react";
import { TimingSvg, type TimingProps } from "./Timing";

export interface TimingStepperProps extends Omit<TimingProps, "highlight"> {
  /** Text shown for each column when it is selected, e.g. "AB 10 → 11: +1, count 2". */
  stepText: string[];
  prevLabel: string;
  nextLabel: string;
  /** Format of the position indicator, with {i} and {n} placeholders, e.g. "step {i} / {n}". */
  positionLabel: string;
}

/** A <Timing> diagram with previous/next buttons that highlight one column and explain it. */
export function TimingStepper({ id, title, stepText, prevLabel, nextLabel, positionLabel, ...rest }: TimingStepperProps) {
  const n = stepText.length;
  const [i, setI] = useState(0);
  const btn =
    "rounded-md border border-zinc-700 px-3 py-1.5 text-sm text-zinc-200 hover:border-sky-400 disabled:cursor-not-allowed disabled:opacity-40";
  return (
    <figure className="not-prose my-6" data-timing={id ?? ""} data-timing-step={i}>
      <div className="max-w-2xl">
        <TimingSvg title={title} highlight={i} {...rest} />
      </div>
      <div className="mt-2 flex max-w-2xl flex-wrap items-center gap-2">
        <button type="button" className={btn} onClick={() => setI((v) => Math.max(0, v - 1))} disabled={i === 0}>
          ← {prevLabel}
        </button>
        <button type="button" className={btn} onClick={() => setI((v) => Math.min(n - 1, v + 1))} disabled={i === n - 1}>
          {nextLabel} →
        </button>
        <span className="text-xs text-zinc-500">{positionLabel.replace("{i}", String(i + 1)).replace("{n}", String(n))}</span>
      </div>
      <p className="mt-2 max-w-2xl font-mono text-sm text-zinc-200" aria-live="polite">
        {stepText[i]}
      </p>
      <figcaption className="mt-1 text-sm text-zinc-400">{title}</figcaption>
    </figure>
  );
}
