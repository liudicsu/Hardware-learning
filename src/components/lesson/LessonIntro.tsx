import { Link } from "@/i18n/navigation";

export interface LessonIntroProps {
  objectives: string[];
  prereqs: { href: string; label: string }[];
  labels: { objectives: string; prereqs: string; none: string; math: string; glossary: string };
}

/** "After this lesson you can" + "Before you start" block shown under the lesson title. */
export function LessonIntro({ objectives, prereqs, labels }: LessonIntroProps) {
  if (objectives.length === 0 && prereqs.length === 0) return null;
  return (
    <section data-lesson-intro className="mt-6 grid gap-4 rounded-xl border border-white/10 bg-white/[0.02] p-4 text-sm sm:grid-cols-[3fr_2fr]">
      {objectives.length > 0 && (
        <div className="min-w-0">
          <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500">{labels.objectives}</h2>
          <ul className="mt-2 space-y-1.5 text-zinc-300">
            {objectives.map((o) => (
              <li key={o} className="flex gap-2">
                <span aria-hidden className="mt-[0.55em] h-1 w-1 shrink-0 rounded-full bg-sky-400" />
                <span className="min-w-0">{o}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="min-w-0">
        <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500">{labels.prereqs}</h2>
        {prereqs.length > 0 ? (
          <ul className="mt-2 space-y-1.5">
            {prereqs.map((p) => (
              <li key={p.href}>
                <Link href={p.href} className="text-sky-400 hover:text-sky-300">
                  {p.label}
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-zinc-400">{labels.none}</p>
        )}
        <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs">
          <Link href="/math" className="text-zinc-400 hover:text-zinc-200">{labels.math} →</Link>
          <Link href="/glossary" className="text-zinc-400 hover:text-zinc-200">{labels.glossary} →</Link>
        </p>
      </div>
    </section>
  );
}
