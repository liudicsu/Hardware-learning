"use client";

import { DIAGRAM_UI } from "@/lib/diagrams/ui";
import type { Locale } from "@/lib/diagrams/types";

export interface StepControlsProps {
  locale: Locale;
  /** Number of steps. */
  n: number;
  /** Current step, or -1 for "all" (nothing dimmed). */
  i: number;
  onChange: (i: number) => void;
  /** Text describing the current step. */
  text?: string;
}

/** Previous / All / Next buttons with a position indicator, shared by every step-through diagram. */
export function StepControls({ locale, n, i, onChange, text }: StepControlsProps) {
  const ui = DIAGRAM_UI[locale];
  const btn =
    "rounded-md border border-zinc-700 px-3 py-1.5 text-sm text-zinc-200 transition-colors hover:border-sky-400 disabled:cursor-not-allowed disabled:opacity-40";
  return (
    <div className="mt-3">
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" className={btn} onClick={() => onChange(i <= 0 ? -1 : i - 1)} disabled={i === -1}>
          ← {ui.prev}
        </button>
        <button type="button" className={btn} onClick={() => onChange(-1)} aria-pressed={i === -1}>
          {ui.all}
        </button>
        <button type="button" className={btn} onClick={() => onChange(i + 1)} disabled={i === n - 1}>
          {ui.next} →
        </button>
        {i >= 0 && (
          <span className="text-xs text-zinc-500">{ui.step.replace("{i}", String(i + 1)).replace("{n}", String(n))}</span>
        )}
      </div>
      <p className="mt-2 min-h-[1.5em] text-sm text-zinc-300" aria-live="polite">
        {text}
      </p>
    </div>
  );
}
