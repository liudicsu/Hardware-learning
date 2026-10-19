"use client";

import { useHydrated, useProgress } from "@/lib/progress";

export interface LessonStatusDotProps {
  lessonKey: string;
  labels: { done: string; todo: string };
}

export function LessonStatusDot({ lessonKey, labels }: LessonStatusDotProps) {
  const progress = useProgress();
  const hydrated = useHydrated();
  const done = hydrated && progress.lessons[lessonKey]?.done === true;

  return (
    <span
      role="img"
      aria-label={done ? labels.done : labels.todo}
      className={
        done
          ? "inline-block h-2 w-2 shrink-0 rounded-full bg-sky-400"
          : "inline-block h-2 w-2 shrink-0 rounded-full ring-1 ring-inset ring-white/20"
      }
    />
  );
}
