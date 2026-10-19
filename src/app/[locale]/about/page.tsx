import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { COURSE_SOURCE } from "@/lib/curriculum";
import { REPO_URL } from "@/lib/site";
import { ResetProgressButton } from "@/components/progress/ResetProgressButton";

export async function generateMetadata({ params }: PageProps<"/[locale]/about">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "about" });
  return { title: t("title") };
}

export default async function AboutPage({ params }: PageProps<"/[locale]/about">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("about");
  const tp = await getTranslations("progress");

  const sections = [
    { title: t("sourceTitle"), body: t("source") },
    { title: t("copyrightTitle"), body: t("copyright") },
    { title: t("privacyTitle"), body: t("privacy") },
    { title: t("safetyTitle"), body: t("safety") },
  ];

  return (
    <div className="max-w-3xl space-y-10">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">{t("title")}</h1>
        <p className="mt-4 text-lg text-zinc-400">{t("lead")}</p>
      </header>
      {sections.map((s) => (
        <section key={s.title}>
          <h2 className="text-sm font-medium text-zinc-200">{s.title}</h2>
          <p className="mt-2 leading-relaxed text-zinc-400">{s.body}</p>
        </section>
      ))}
      <section className="rounded-xl border border-white/10 bg-card p-5 text-sm">
        <a href={COURSE_SOURCE.url} target="_blank" rel="noopener noreferrer" className="font-medium text-zinc-100 hover:text-white">
          {COURSE_SOURCE.title} ↗
        </a>
        <p className="mt-1 text-zinc-500">
          <a href={COURSE_SOURCE.authorUrl} target="_blank" rel="noopener noreferrer" className="hover:text-zinc-300">
            {COURSE_SOURCE.author}
          </a>{" "}
          · x.com
        </p>
      </section>
      <section className="flex flex-wrap items-center justify-between gap-4 border-t border-white/[0.06] pt-6 text-sm text-zinc-400">
        <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="hover:text-zinc-100">
          {t("openSource")} ↗
        </a>
        <ResetProgressButton labels={{ reset: tp("reset"), confirm: tp("confirmReset") }} />
      </section>
    </div>
  );
}
