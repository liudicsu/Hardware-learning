"use client";

import { resetProgress } from "@/lib/progress";

export interface ResetProgressButtonProps {
  labels: { reset: string; confirm: string };
}

export function ResetProgressButton({
  labels,
}: ResetProgressButtonProps) {
  function handleClick() {
    if (window.confirm(labels.confirm)) {
      resetProgress();
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className="rounded-xl border border-white/10 px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:border-white/20 hover:text-zinc-100"
    >
      {labels.reset}
    </button>
  );
}
