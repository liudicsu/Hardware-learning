export type Locale = "zh" | "en";
export type L10n = Record<Locale, string>;

export type ResourceKind =
  | "simulator"
  | "textbook"
  | "video"
  | "course"
  | "interactive"
  | "guide"
  | "book"
  | "hardware"
  | "software"
  | "service"
  | "model";

export interface Resource {
  id: string;
  url: string;
  /** Optional locale-specific URL (e.g. a translated edition). */
  urlByLocale?: Partial<L10n>;
  title: L10n;
  /** Author / publisher who owns the content. */
  author: string;
  kind: ResourceKind;
  /** Cost note, e.g. "free", "free with account", "$29.99". */
  cost: L10n;
  /** Our own short summary (original text, not copied). */
  summary: L10n;
  /** Licence / copyright note shown on the card. */
  license: L10n;
  /** True when we added it as a supplement; not part of the original course list. */
  extra?: boolean;
}

export interface Task {
  id: string;
  text: L10n;
}

export interface Lesson {
  slug: string;
  title: L10n;
  summary: L10n;
  minutes: number;
  resources: string[];
  tasks: Task[];
  /** What the learner can do after the lesson: 3-5 checkable statements. */
  objectives?: L10n[];
  /** Slugs of earlier lessons this one builds on (rendered as links). */
  prereqs?: string[];
}

export interface Month {
  id: number;
  slug: string;
  title: L10n;
  goal: L10n;
  topics: L10n[];
  milestones: L10n[];
  lessons: Lesson[];
}
