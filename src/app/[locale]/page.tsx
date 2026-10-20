import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { months, monthStats, COURSE_SOURCE } from "@/lib/curriculum";
import { tr } from "@/lib/l10n";
import { MonthProgress } from "@/components/progress/MonthProgress";
import { ContinueLink } from "@/components/course/ContinueLink";

export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("home");
  const tm = await getTranslations("month");

  return (
    <div className="space-y-20">
      <section className="pt-6 sm:pt-12">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-sky-400">{t("eyebrow")}</p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
          {t("title")}
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-relaxed text-zinc-400 sm:text-lg">{t("lead")}</p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link
            href="/month/month-1"
            className="inline-flex h-10 items-center rounded-xl bg-white px-4 text-sm font-medium text-black transition-colors hover:bg-zinc-200"
          >
            {t("start")} →
          </Link>
          <ContinueLink label={t("continue")} />
        </div>
        <p className="mt-6 text-xs text-zinc-500">
          <a href={COURSE_SOURCE.url} target="_blank" rel="noopener noreferrer" className="hover:text-zinc-300">
            {COURSE_SOURCE.title} — {COURSE_SOURCE.author} ↗
          </a>
        </p>
      </section>

      <section>
        <h2 className="text-sm font-medium text-zinc-400">{t("roadmap")}</h2>
        <ol className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {months.map((m) => {
            const stats = monthStats(m);
            return (
              <li key={m.id}>
                <Link
                  href={`/month/${m.slug}`}
                  className="group flex h-full flex-col rounded-xl border border-white/10 bg-card p-5 transition-colors hover:border-white/20 hover:bg-white/[0.03]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-xs text-zinc-500">{tm("label", { n: m.id })}</span>
                    <span className="text-xs text-zinc-500">
                      {t("lessons", { count: stats.lessons })} · {t("hours", { n: stats.hours })}
                    </span>
                  </div>
                  <h3 className="mt-3 font-medium text-zinc-100 group-hover:text-white">{tr(m.title, locale)}</h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-zinc-400">{tr(m.goal, locale)}</p>
                  <div className="mt-5">
                    <MonthProgress monthId={m.id} label={tm("progress")} />
                  </div>
                </Link>
              </li>
            );
          })}
        </ol>
      </section>

      <section>
        <h2 className="text-sm font-medium text-zinc-400">{t("howTitle")}</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          {(["1", "2", "3"] as const).map((n) => (
            <div key={n} className="rounded-xl border border-white/10 p-5">
              <span className="font-mono text-xs text-sky-400">0{n}</span>
              <h3 className="mt-2 font-medium text-zinc-100">{t(`how${n}Title`)}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-zinc-400">{t(`how${n}`)}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-zinc-500">
          {t("progressLocal")}
        </p>
      </section>
    </div>
  );
}
