import { useSyncExternalStore } from "react";
import { lessonKey } from "@/lib/curriculum";
import type { Month } from "@/lib/types";

export interface LessonProgress {
  done: boolean;
  doneAt?: string;
}

export interface ProgressState {
  lessons: Record<string, LessonProgress>;
  tasks: Record<string, boolean>;
  quizzes: Record<string, boolean>;
}

export interface MonthStats {
  doneLessons: number;
  totalLessons: number;
  doneTasks: number;
  totalTasks: number;
  percent: number;
}

const STORAGE_KEY = "hl-progress-v1";

const EMPTY: ProgressState = Object.freeze({
  lessons: Object.freeze({}) as Record<string, LessonProgress>,
  tasks: Object.freeze({}) as Record<string, boolean>,
  quizzes: Object.freeze({}) as Record<string, boolean>,
});

const listeners = new Set<() => void>();

let cached: ProgressState | undefined;
let cachedRaw: string | null | undefined;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function booleanRecord(value: unknown): Record<string, boolean> {
  const result: Record<string, boolean> = {};
  if (!isRecord(value)) return result;
  for (const [key, entry] of Object.entries(value)) {
    if (entry === true) result[key] = true;
  }
  return result;
}

function parseProgress(raw: string): ProgressState {
  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch {
    return EMPTY;
  }
  if (!isRecord(data)) return EMPTY;

  const lessons: Record<string, LessonProgress> = {};
  if (isRecord(data.lessons)) {
    for (const [key, value] of Object.entries(data.lessons)) {
      if (!isRecord(value)) continue;
      const done = value.done === true;
      const doneAt = typeof value.doneAt === "string" ? value.doneAt : undefined;
      lessons[key] = doneAt ? { done, doneAt } : { done };
    }
  }

  return {
    lessons,
    tasks: booleanRecord(data.tasks),
    quizzes: booleanRecord(data.quizzes),
  };
}

function readRaw(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function notify(): void {
  for (const listener of listeners) listener();
}

function commit(next: ProgressState): void {
  let raw: string | null = null;
  try {
    raw = JSON.stringify(next);
    window.localStorage.setItem(STORAGE_KEY, raw);
  } catch {
    raw = null;
  }
  cached = next;
  cachedRaw = raw;
  notify();
}

function update(mutate: (previous: ProgressState) => ProgressState): void {
  commit(mutate(getSnapshot()));
}

export function subscribe(callback: () => void): () => void {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

export function getSnapshot(): ProgressState {
  if (typeof window === "undefined") return EMPTY;
  const raw = readRaw();
  if (cached === undefined || raw !== cachedRaw) {
    cachedRaw = raw;
    cached = raw ? parseProgress(raw) : EMPTY;
  }
  return cached;
}

export function getServerSnapshot(): ProgressState {
  return EMPTY;
}

export function setLessonDone(key: string, done: boolean): void {
  update((previous) => {
    const lessons = { ...previous.lessons };
    if (done) {
      const doneAt = lessons[key]?.doneAt ?? new Date().toISOString();
      lessons[key] = { done: true, doneAt };
    } else {
      delete lessons[key];
    }
    return { ...previous, lessons };
  });
}

export function toggleTask(taskKey: string): void {
  update((previous) => {
    const tasks = { ...previous.tasks };
    if (tasks[taskKey]) {
      delete tasks[taskKey];
    } else {
      tasks[taskKey] = true;
    }
    return { ...previous, tasks };
  });
}

export function setQuizCorrect(quizKey: string, correct: boolean): void {
  update((previous) => {
    const quizzes = { ...previous.quizzes };
    if (correct) {
      quizzes[quizKey] = true;
    } else {
      delete quizzes[quizKey];
    }
    return { ...previous, quizzes };
  });
}

export function resetProgress(): void {
  commit({ lessons: {}, tasks: {}, quizzes: {} });
}

export function useProgress(): ProgressState {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

const noopSubscribe = (): (() => void) => () => {};
const hydratedSnapshot = (): boolean => true;
const serverHydratedSnapshot = (): boolean => false;

export function useHydrated(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    hydratedSnapshot,
    serverHydratedSnapshot,
  );
}

export function monthStats(progress: ProgressState, month: Month): MonthStats {
  let doneLessons = 0;
  let doneTasks = 0;
  let totalTasks = 0;

  for (const lesson of month.lessons) {
    const key = lessonKey(month.id, lesson.slug);
    if (progress.lessons[key]?.done) doneLessons += 1;
    totalTasks += lesson.tasks.length;
    for (const task of lesson.tasks) {
      if (progress.tasks[`${key}#${task.id}`]) doneTasks += 1;
    }
  }

  const totalLessons = month.lessons.length;
  const total = totalLessons + totalTasks;
  const percent =
    total === 0 ? 0 : Math.round(((doneLessons + doneTasks) / total) * 100);

  return { doneLessons, totalLessons, doneTasks, totalTasks, percent };
}

if (typeof window !== "undefined") {
  window.addEventListener("storage", (event: StorageEvent) => {
    if (event.key !== null && event.key !== STORAGE_KEY) return;
    cached = undefined;
    cachedRaw = undefined;
    notify();
  });
}
