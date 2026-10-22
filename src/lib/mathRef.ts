import type { L10n } from "./types";

/**
 * Math quick reference ("enough and no more"). Each entry: a definition, one worked example taken
 * from the course (numbers verified by script or formula), the lessons that use it, and free
 * authoritative textbooks. Source list: the math-prerequisite table of the Months 4-6 beginner audit.
 */
export interface MathLink {
  label: string;
  url: string;
}

export interface MathEntry {
  id: string;
  title: L10n;
  definition: L10n;
  /** Worked example from a lesson or script; plain text, line breaks kept. */
  example: L10n;
  /** Lesson slugs that use the concept. */
  lessons: string[];
  links: MathLink[];
}

export const mathEntries: MathEntry[] = [];
