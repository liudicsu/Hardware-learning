import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { getMonth, lessonKey, months } from "@/lib/curriculum";
import { tr } from "@/lib/l10n";
import { StatusPill } from "@/components/course/MonthBadge";
import { MonthProgress } from "@/components/progress/MonthProgress";
import { LessonStatusDot } from "@/components/progress/LessonStatusDot";
import { MonthTabs } from "@/components/course/MonthTabs";

export const dynamicParams = false;

export function generateStaticParams() {
  return routing.locales.flatMap((locale) => months.map((m) => ({ locale, month: m.slug })));
}

export async function generateMetadata({ params }: PageProps<"/[locale]/month/[month]">): Promise<Metadata> {
  const { locale, month: slug } = await params;
  const month = getMonth(slug);
  if (!month) return {};
  const t = await getTranslations({ locale, namespace: "month" });
  return { title: `${t("label", { n: month.id })} · ${tr(month.title, locale)}`, description: tr(month.goal, locale) };
}

export default async function MonthPage({ params }: PageProps<"/[locale]/month/[month]">) {
  const { locale, month: slug } = await params;
  setRequestLocale(locale);
  const month = getMonth(slug);
  if (!month) notFound();
  const t = await getTranslations("month");
  const th = await getTranslations("home");
  const tl = await getTranslations("lesson");
  const ready = month.status === "ready";

  return (
    <div className="space-y-12">
      <MonthTabs current={month.id} labelFor={(n) => t("label", { n })} />

      <header className="max-w-3xl">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-zinc-500">{t("label", { n: month.id })}</span>
          <StatusPill ready={ready} label={ready ? th("statusReady") : th("statusOutline")} />
        </div>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">{tr(month.title, locale)}</h1>
        <p className="mt-5 text-xs font-medium uppercase tracking-wider text-zinc-500">{t("goal")}</p>
        <p className="mt-1.5 text-lg leading-relaxed text-zinc-300">{tr(month.goal, locale)}</p>
        {ready ? (
          <div className="mt-6 max-w-md">
            <MonthProgress monthId={month.id} label={t("progress")} />
          </div>
        ) : null}
      </header>

      {ready ? (
        <section>
          <h2 className="text-sm font-medium text-zinc-400">{t("lessons")}</h2>
          <ol className="mt-4 divide-y divide-white/[0.06] overflow-hidden rounded-xl border border-white/10 bg-card">
            {month.lessons.map((l, i) => (
              <li key={l.slug}>
                <Link
                  href={`/month/${month.slug}/${l.slug}`}
                  className="group flex items-start gap-4 p-5 transition-colors hover:bg-white/[0.03]"
                >
                  <span className="mt-0.5 w-6 shrink-0 font-mono text-sm text-zinc-500">{String(i + 1).padStart(2, "0")}</span>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-medium text-zinc-100 group-hover:text-white">{tr(l.title, locale)}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-zinc-400">{tr(l.summary, locale)}</p>
                    <p className="mt-2 text-xs text-zinc-500">
                      {t("minutes", { n: l.minutes })} · {l.tasks.length} {tl("tasks")}
                    </p>
                  </div>
                  <span className="mt-2">
                    <LessonStatusDot
                      lessonKey={lessonKey(month.id, l.slug)}
                      labels={{ done: tl("statusDone"), todo: tl("statusTodo") }}
                    />
                  </span>
                </Link>
              </li>
            ))}
          </ol>
          <div className="mt-6">
            <Link
              href={`/month/${month.slug}/${month.lessons[0].slug}`}
              className="inline-flex h-10 items-center rounded-xl bg-white px-4 text-sm font-medium text-black hover:bg-zinc-200"
            >
              {t("start")} →
            </Link>
          </div>
        </section>
      ) : (
        <section className="max-w-3xl space-y-6">
          <p className="rounded-xl border border-amber-300/20 bg-amber-300/[0.04] p-4 text-sm leading-relaxed text-amber-100/80">
            {t("outlineNotice")}
          </p>
          <div>
            <h2 className="text-sm font-medium text-zinc-400">{t("topics")}</h2>
            <ol className="mt-3 space-y-2">
              {month.topics.map((topic, i) => (
                <li key={i} className="flex gap-3 rounded-lg border border-white/[0.08] p-3 text-sm text-zinc-300">
                  <span className="font-mono text-zinc-500">{i + 1}.</span>
                  {tr(topic, locale)}
                </li>
              ))}
            </ol>
          </div>
        </section>
      )}

      <section id="milestone" className="max-w-3xl scroll-mt-20">
        <h2 className="text-sm font-medium text-zinc-400">{t("milestones")}</h2>
        <p className="mt-2 text-sm text-zinc-500">{t("milestonesLead")}</p>
        <ul className="mt-4 space-y-2">
          {month.milestones.map((m, i) => (
            <li key={i} className="flex gap-3 text-sm leading-relaxed text-zinc-300">
              <span aria-hidden className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-400/70" />
              {tr(m, locale)}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
