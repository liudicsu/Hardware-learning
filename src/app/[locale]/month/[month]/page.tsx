import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { getMonth, lessonKey, months, monthStats } from "@/lib/curriculum";
import { tr } from "@/lib/l10n";
import { MonthProgress } from "@/components/progress/MonthProgress";
import { LessonStatusDot } from "@/components/progress/LessonStatusDot";
import { MonthTabs } from "@/components/course/MonthTabs";
import { TaskChecklist } from "@/components/progress/TaskChecklist";

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
  const tl = await getTranslations("lesson");
  const stats = monthStats(month);

  return (
    <div className="space-y-12">
      <MonthTabs current={month.id} labelFor={(n) => t("label", { n })} />

      <header className="max-w-3xl">
        <span className="font-mono text-xs text-zinc-500">{t("label", { n: month.id })}</span>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">{tr(month.title, locale)}</h1>
        <p className="mt-5 text-xs font-medium uppercase tracking-wider text-zinc-500">{t("goal")}</p>
        <p className="mt-1.5 text-lg leading-relaxed text-zinc-300">{tr(month.goal, locale)}</p>
        <p className="mt-4 text-sm text-zinc-400">
          {t("stats", { lessons: stats.lessons, hours: stats.hours, tasks: stats.tasks })}
        </p>
        <div className="mt-6 max-w-md">
          <MonthProgress monthId={month.id} label={t("progress")} />
        </div>
      </header>

      <section className="max-w-3xl">
        <h2 className="text-sm font-medium text-zinc-400">{t("topics")}</h2>
        <ul className="mt-3 flex flex-wrap gap-2">
          {month.topics.map((topic, i) => (
            <li key={i} className="rounded-lg border border-white/[0.08] px-3 py-1.5 text-sm text-zinc-300">
              {tr(topic, locale)}
            </li>
          ))}
        </ul>
      </section>

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

      <section id="milestone" className="max-w-3xl scroll-mt-20">
        <p className="mb-3 text-sm text-zinc-500">{t("milestonesLead")}</p>
        <TaskChecklist
          lessonKey={`m${month.id}/milestone`}
          title={t("milestones")}
          tasks={month.milestones.map((m, i) => ({ id: `ms${i + 1}`, text: tr(m, locale) }))}
        />
      </section>
    </div>
  );
}
