import { months } from "./curriculum";
import type { Lesson, Month } from "./types";

/** Lesson slugs are unique across the course, so a slug alone identifies a lesson. */
export function findLessonBySlug(slug: string): { month: Month; lesson: Lesson } | undefined {
  for (const month of months) {
    const lesson = month.lessons.find((l) => l.slug === slug);
    if (lesson) return { month, lesson };
  }
  return undefined;
}

/** Internal href (without locale prefix) for a lesson slug; throws on an unknown slug so typos fail the build. */
export function lessonHref(slug: string): string {
  const found = findLessonBySlug(slug);
  if (!found) throw new Error(`Unknown lesson slug "${slug}"`);
  return `/month/${found.month.slug}/${slug}`;
}
