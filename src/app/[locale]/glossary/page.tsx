import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { months } from "@/lib/curriculum";
import { glossary } from "@/lib/glossary";
import { asLocale, tr } from "@/lib/l10n";

export async function generateMetadata({ params }: PageProps<"/[locale]/glossary">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "glossary" });
  return { title: t("title") };
}

export default async function GlossaryPage({ params }: PageProps<"/[locale]/glossary">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const loc = asLocale(locale);
  const other = loc === "zh" ? "en" : "zh";
  const t = await getTranslations("glossary");
  const tm = await getTranslations("month");

  // Group terms by the lesson that first explains them, in course order.
  const groups = months.flatMap((m) =>
    m.lessons
      .map((l) => ({ month: m, lesson: l, terms: glossary.filter((g) => g.lesson === l.slug) }))
      .filter((g) => g.terms.length > 0),
  );

  return (
    <div className="max-w-3xl space-y-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">{t("title")}</h1>
        <p className="mt-4 leading-relaxed text-zinc-400">{t("lead")}</p>
        <p className="mt-2 text-xs text-zinc-500">{t("count", { n: glossary.length })}</p>
      </header>
      {groups.map(({ month, lesson, terms }) => (
        <section key={lesson.slug} aria-labelledby={`g-${lesson.slug}`}>
          <h2 id={`g-${lesson.slug}`} className="text-sm text-zinc-400">
            <span className="font-mono text-zinc-500">{tm("label", { n: month.id })}</span>
            {" · "}
            <Link href={`/month/${month.slug}/${lesson.slug}`} className="text-zinc-300 hover:text-white">
              {tr(lesson.title, locale)}
            </Link>
          </h2>
          <dl className="mt-3 divide-y divide-white/[0.06] rounded-xl border border-white/10">
            {terms.map((g) => (
              <div key={g.id} id={g.id} className="scroll-mt-24 p-4 target:bg-sky-400/[0.05]">
                <dt className="flex flex-wrap items-baseline gap-x-2">
                  <span className="font-medium text-zinc-100">{g.term[loc]}</span>
                  <span className="text-xs text-zinc-500">{g.term[other]}</span>
                </dt>
                <dd className="mt-1 text-sm leading-relaxed text-zinc-400">{tr(g.def, locale)}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </div>
  );
}
