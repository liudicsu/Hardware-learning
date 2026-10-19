import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { months } from "@/lib/curriculum";
import { asLocale, tr } from "@/lib/l10n";
import { resources } from "@/lib/resources";
import { ResourceCard } from "@/components/ResourceCard";
import { Link } from "@/i18n/navigation";

export async function generateMetadata({ params }: PageProps<"/[locale]/resources">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "resource" });
  return { title: t("allTitle") };
}

export default async function ResourcesPage({ params }: PageProps<"/[locale]/resources">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const loc = asLocale(locale);
  const t = await getTranslations("resource");
  const tm = await getTranslations("month");

  // Group resources by the month/lesson that first uses them.
  const seen = new Set<string>();
  const groups = months
    .filter((m) => m.lessons.length > 0)
    .flatMap((m) =>
      m.lessons.map((l) => {
        const ids = l.resources.filter((id) => !seen.has(id));
        ids.forEach((id) => seen.add(id));
        return { month: m, lesson: l, ids };
      }),
    )
    .filter((g) => g.ids.length > 0);
  const rest = Object.keys(resources).filter((id) => !seen.has(id));

  const card = (id: string) => (
    <ResourceCard
      key={id}
      id={id}
      locale={loc}
      labels={{ open: t("open"), supplement: t("supplement"), kind: t(`kind.${resources[id].kind}`) }}
    />
  );

  return (
    <div className="space-y-12">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">{t("allTitle")}</h1>
        <p className="mt-4 leading-relaxed text-zinc-400">{t("allLead")}</p>
      </header>
      {groups.map(({ month, lesson, ids }) => (
        <section key={`${month.id}-${lesson.slug}`}>
          <h2 className="text-sm text-zinc-400">
            <span className="font-mono text-zinc-500">{tm("label", { n: month.id })}</span>
            {" · "}
            <Link href={`/month/${month.slug}/${lesson.slug}`} className="text-zinc-300 hover:text-white">
              {tr(lesson.title, locale)}
            </Link>
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{ids.map(card)}</div>
        </section>
      ))}
      {rest.length > 0 ? (
        <section>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{rest.map(card)}</div>
        </section>
      ) : null}
    </div>
  );
}
