"use client";

import { useLocale } from "next-intl";
import { Link } from "@/i18n/navigation";
import { months, lessonKey } from "@/lib/curriculum";
import { useHydrated, useProgress } from "@/lib/progress";
import { tr } from "@/lib/l10n";

/** Links to the first unfinished lesson once the visitor has started. */
export function ContinueLink({ label }: { label: string }) {
  const progress = useProgress();
  const locale = useLocale();
  const hydrated = useHydrated();
  if (!hydrated) return null;
  const started = Object.keys(progress.lessons).length + Object.keys(progress.tasks).length > 0;
  if (!started) return null;
  for (const m of months) {
    for (const l of m.lessons) {
      if (!progress.lessons[lessonKey(m.id, l.slug)]?.done) {
        return (
          <Link
            href={`/month/${m.slug}/${l.slug}`}
            className="inline-flex h-10 items-center rounded-xl border border-white/15 px-4 text-sm font-medium text-zinc-200 transition-colors hover:border-white/30 hover:text-white"
          >
            {label} · {tr(l.title, locale)}
          </Link>
        );
      }
    }
  }
  return null;
}
