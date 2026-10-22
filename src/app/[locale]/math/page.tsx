import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { tr } from "@/lib/l10n";
import { findLessonBySlug, lessonHref } from "@/lib/lessonIndex";
import { mathEntries } from "@/lib/mathRef";

export async function generateMetadata({ params }: PageProps<"/[locale]/math">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "math" });
  return { title: t("title") };
}

export default async function MathPage({ params }: PageProps<"/[locale]/math">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("math");
  const tm = await getTranslations("month");

  return (
    <div className="max-w-3xl space-y-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">{t("title")}</h1>
        <p className="mt-4 leading-relaxed text-zinc-400">{t("lead")}</p>
        <nav className="mt-5 flex flex-wrap gap-2 text-xs">
          {mathEntries.map((e) => (
            <a key={e.id} href={`#${e.id}`} className="rounded-full border border-white/10 px-2.5 py-1 text-zinc-400 hover:border-white/20 hover:text-zinc-200">
              {tr(e.title, locale)}
            </a>
          ))}
        </nav>
      </header>
      {mathEntries.map((e) => (
        <section key={e.id} id={e.id} className="scroll-mt-24 rounded-xl border border-white/10 p-4 sm:p-5">
          <h2 className="text-lg font-semibold text-zinc-100">{tr(e.title, locale)}</h2>
          <h3 className="mt-3 text-xs font-medium uppercase tracking-wider text-zinc-500">{t("definition")}</h3>
          <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-zinc-300">{tr(e.definition, locale)}</p>
          <h3 className="mt-4 text-xs font-medium uppercase tracking-wider text-zinc-500">{t("example")}</h3>
          <pre className="mt-1 whitespace-pre-wrap break-words rounded-lg border border-white/[0.06] bg-black/30 p-3 font-mono text-[0.8rem] leading-relaxed text-zinc-300">
            {tr(e.example, locale)}
          </pre>
          <h3 className="mt-4 text-xs font-medium uppercase tracking-wider text-zinc-500">{t("usedIn")}</h3>
          <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
            {e.lessons.map((slug) => {
              const found = findLessonBySlug(slug);
              if (!found) throw new Error(`Unknown lesson "${slug}" in math entry ${e.id}`);
              return (
                <li key={slug}>
                  <Link href={lessonHref(slug)} className="text-sky-400 hover:text-sky-300">
                    {tm("label", { n: found.month.id })} · {tr(found.lesson.title, locale)}
                  </Link>
                </li>
              );
            })}
          </ul>
          <h3 className="mt-4 text-xs font-medium uppercase tracking-wider text-zinc-500">{t("read")}</h3>
          <ul className="mt-1 space-y-1 text-sm">
            {e.links.map((l) => (
              <li key={l.label}>
                <a href={l.url} target="_blank" rel="noopener noreferrer" className="break-words text-zinc-300 underline decoration-white/20 underline-offset-2 hover:decoration-white/60">
                  {l.label} ↗
                </a>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
