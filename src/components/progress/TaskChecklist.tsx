"use client";

import { toggleTask, useHydrated, useProgress } from "@/lib/progress";

export interface TaskChecklistProps {
  lessonKey: string;
  tasks: { id: string; text: string }[];
  title: string;
}

export function TaskChecklist({
  lessonKey,
  tasks,
  title,
}: TaskChecklistProps) {
  const progress = useProgress();
  const hydrated = useHydrated();

  const doneCount = tasks.filter(
    (task) => hydrated && progress.tasks[`${lessonKey}#${task.id}`] === true,
  ).length;

  return (
    <section className="rounded-xl border border-white/10 bg-[#111113] p-5">
      <header className="flex items-center justify-between gap-4">
        <h2 className="text-sm font-semibold text-zinc-100">{title}</h2>
        <span className="text-xs tabular-nums text-zinc-400">
          {doneCount} / {tasks.length}
        </span>
      </header>
      <ul className="mt-4 space-y-3">
        {tasks.map((task) => {
          const checked =
            hydrated && progress.tasks[`${lessonKey}#${task.id}`] === true;
          return (
            <li key={task.id}>
              <label
                className={`flex cursor-pointer items-start gap-3 text-sm transition-colors ${
                  checked ? "text-zinc-500 line-through" : "text-zinc-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={!hydrated}
                  onChange={() => toggleTask(`${lessonKey}#${task.id}`)}
                  className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer rounded border-white/20 bg-transparent accent-sky-400 disabled:cursor-not-allowed"
                />
                <span className="min-w-0 break-words">{task.text}</span>
              </label>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
