"use client";

import { setLessonDone, useHydrated, useProgress } from "@/lib/progress";

export interface LessonCompleteButtonProps {
  lessonKey: string;
  labels: { markDone: string; done: string };
}

function CheckIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 16 16"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3.5 8.5 6.5 11.5 12.5 4.5" />
    </svg>
  );
}

export function LessonCompleteButton({
  lessonKey,
  labels,
}: LessonCompleteButtonProps) {
  const progress = useProgress();
  const hydrated = useHydrated();
  const done = hydrated && progress.lessons[lessonKey]?.done === true;

  return (
    <button
      type="button"
      disabled={!hydrated}
      aria-pressed={done}
      onClick={() => setLessonDone(lessonKey, !done)}
      className={
        done
          ? "inline-flex items-center gap-2 rounded-xl border border-sky-400 bg-sky-400/10 px-4 py-2 text-sm font-medium text-sky-400 transition-colors hover:bg-sky-400/15 disabled:cursor-not-allowed disabled:opacity-60"
          : "inline-flex items-center gap-2 rounded-xl border border-white/15 px-4 py-2 text-sm font-medium text-zinc-300 transition-colors hover:border-white/30 hover:text-zinc-100 disabled:cursor-not-allowed disabled:opacity-60"
      }
    >
      {done ? <CheckIcon /> : null}
      <span>{done ? labels.done : labels.markDone}</span>
    </button>
  );
}
