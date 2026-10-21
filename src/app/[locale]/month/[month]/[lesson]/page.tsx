import type { Metadata } from "next";
import type { ComponentProps, ComponentType } from "react";
import type { MDXComponents } from "mdx/types";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { withBasePath } from "@/lib/basePath";
import { getLesson, lessonKey, months } from "@/lib/curriculum";
import { asLocale, tr } from "@/lib/l10n";
import { getResource } from "@/lib/resources";
import { ResourceCard } from "@/components/ResourceCard";
import { TaskChecklist } from "@/components/progress/TaskChecklist";
import { LessonCompleteButton } from "@/components/progress/LessonCompleteButton";
import { LessonStatusDot } from "@/components/progress/LessonStatusDot";
import { MonthProgress } from "@/components/progress/MonthProgress";
import { Quiz } from "@/components/mdx/Quiz";
import { Falstad } from "@/components/mdx/Falstad";
import { Callout } from "@/components/mdx/Callout";
import { Formula } from "@/components/mdx/Formula";
import { H2 } from "@/components/lesson/Heading";
import { CodeBlock } from "@/components/mdx/CodeBlock";
import { SimOutput } from "@/components/mdx/SimOutput";
import { CodeSource } from "@/components/mdx/CodeSource";
import { Wokwi } from "@/components/mdx/Wokwi";
import { PidWidget } from "@/components/widgets/PidWidget";
import { IkWidget } from "@/components/widgets/IkWidget";
import { CameraWidget } from "@/components/widgets/CameraWidget";
import { BodeWidget } from "@/components/widgets/BodeWidget";
import { ActionTokenWidget } from "@/components/widgets/ActionTokenWidget";
import { WilsonWidget } from "@/components/widgets/WilsonWidget";
import { PanTiltWidget } from "@/components/widgets/PanTiltWidget";
import { GripForceWidget } from "@/components/widgets/GripForceWidget";
import { StsPacketWidget } from "@/components/widgets/StsPacketWidget";
import { GearWidget } from "@/components/widgets/GearWidget";
import { SnapFitWidget } from "@/components/widgets/SnapFitWidget";
import { ComplementaryWidget } from "@/components/widgets/ComplementaryWidget";
import { LineFollowWidget } from "@/components/widgets/LineFollowWidget";
import { Toc } from "@/components/lesson/Toc";
import { lessonToc } from "@/lib/toc";

export const dynamicParams = false;

export function generateStaticParams() {
  return routing.locales.flatMap((locale) =>
    months.flatMap((m) => m.lessons.map((l) => ({ locale, month: m.slug, lesson: l.slug }))),
  );
}

type Params = PageProps<"/[locale]/month/[month]/[lesson]">;

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { locale, month, lesson } = await params;
  const found = getLesson(month, lesson);
  if (!found) return {};
  return { title: tr(found.lesson.title, locale), description: tr(found.lesson.summary, locale) };
}

async function loadContent(monthId: number, slug: string, locale: string) {
  try {
    const mod = (await import(`@/content/m${monthId}/${slug}/${locale}.mdx`)) as {
      default: ComponentType<{ components?: MDXComponents }>;
    };
    return mod.default;
  } catch {
    return null;
  }
}

export default async function LessonPage({ params }: Params) {
  const { locale, month: monthSlug, lesson: lessonSlug } = await params;
  setRequestLocale(locale);
  const found = getLesson(monthSlug, lessonSlug);
  if (!found) notFound();
  const { month, lesson, index, prev, next } = found;
  const key = lessonKey(month.id, lesson.slug);
  const loc = asLocale(locale);
  const t = await getTranslations("lesson");
  const tm = await getTranslations("month");
  const tn = await getTranslations("nav");
  const tr_ = await getTranslations("resource");
  const Content = await loadContent(month.id, lesson.slug, loc);
  if (!Content) notFound();
  const toc = await lessonToc(month.id, lesson.slug, loc);

  const components: MDXComponents = {
    Quiz: (props: Omit<ComponentProps<typeof Quiz>, "lessonKey">) => <Quiz lessonKey={key} {...props} />,
    Falstad,
    Callout,
    Formula,
    h2: H2,
    pre: CodeBlock,
    SimOutput,
    CodeSource,
    Wokwi,
    PidWidget,
    IkWidget,
    CameraWidget,
    BodeWidget,
    ActionTokenWidget,
    WilsonWidget,
    PanTiltWidget,
    GripForceWidget,
    StsPacketWidget,
    GearWidget,
    SnapFitWidget,
    ComplementaryWidget,
    LineFollowWidget,
    img: ({ src, alt, ...rest }: ComponentProps<"img">) => (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={typeof src === "string" ? withBasePath(src) : src} alt={alt ?? ""} loading="lazy" {...rest} />
    ),
    Resource: ({ id }: { id: string }) => (
      <div className="not-prose my-6">
      <ResourceCard
        id={id}
        locale={loc}
        labels={{
          open: tr_("open"),
          supplement: tr_("supplement"),
          kind: tr_(`kind.${getResource(id).kind}`),
        }}
      />
      </div>
    ),
  };

  return (
    <div className="lg:grid lg:grid-cols-[minmax(0,1fr)_260px] lg:gap-12">
      <article className="min-w-0 max-w-3xl">
        <nav className="flex flex-wrap items-center gap-1.5 text-xs text-zinc-500">
          <Link href="/" className="hover:text-zinc-300">{tn("home")}</Link>
          <span>/</span>
          <Link href={`/month/${month.slug}`} className="hover:text-zinc-300">
            {tm("label", { n: month.id })}
          </Link>
          <span>/</span>
          <span className="text-zinc-400">
            {t("lesson", { n: index + 1 })} {t("of", { total: month.lessons.length })}
          </span>
        </nav>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-white sm:text-4xl">{tr(lesson.title, locale)}</h1>
        <p className="mt-4 text-lg leading-relaxed text-zinc-400">{tr(lesson.summary, locale)}</p>
        <p className="mt-3 text-xs text-zinc-500">
          {tm("minutes", { n: lesson.minutes })} · {lesson.tasks.length} {t("tasks")}
        </p>

        <Toc items={toc} title={t("onThisPage")} variant="inline" />

        <div className="prose-lesson mt-10">
          <Content components={components} />
        </div>

        <section id="tasks" className="mt-14 scroll-mt-20">
          <TaskChecklist
            lessonKey={key}
            title={t("tasks")}
            tasks={lesson.tasks.map((task) => ({ id: task.id, text: tr(task.text, locale) }))}
          />
        </section>

        <section id="resources" className="mt-10 scroll-mt-20">
          <h2 className="text-sm font-medium text-zinc-400">{t("resources")}</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {lesson.resources.map((id) => (
              <ResourceCard
                key={id}
                id={id}
                locale={loc}
                labels={{
                  open: tr_("open"),
                  supplement: tr_("supplement"),
                  kind: tr_(`kind.${getResource(id).kind}`),
                }}
              />
            ))}
          </div>
        </section>

        <div className="mt-12 flex flex-wrap items-center justify-between gap-4 border-t border-white/[0.06] pt-8">
          <LessonCompleteButton lessonKey={key} labels={{ markDone: t("markDone"), done: t("done") }} />
        </div>

        <nav className="mt-8 grid gap-3 sm:grid-cols-2" aria-label="lesson navigation">
          {prev ? (
            <Link
              href={`/month/${month.slug}/${prev.slug}`}
              className="group rounded-xl border border-white/10 p-4 transition-colors hover:border-white/20 hover:bg-white/[0.03]"
            >
              <span className="text-xs text-zinc-500">← {t("prev")}</span>
              <span className="mt-1 block text-sm font-medium text-zinc-200 group-hover:text-white">{tr(prev.title, locale)}</span>
            </Link>
          ) : (
            <Link
              href={`/month/${month.slug}`}
              className="group rounded-xl border border-white/10 p-4 transition-colors hover:border-white/20 hover:bg-white/[0.03]"
            >
              <span className="text-xs text-zinc-500">← {t("backToMonth")}</span>
              <span className="mt-1 block text-sm font-medium text-zinc-200 group-hover:text-white">{tr(month.title, locale)}</span>
            </Link>
          )}
          {next ? (
            <Link
              href={`/month/${month.slug}/${next.slug}`}
              className="group rounded-xl border border-white/10 p-4 text-right transition-colors hover:border-white/20 hover:bg-white/[0.03] sm:col-start-2"
            >
              <span className="text-xs text-zinc-500">{t("next")} →</span>
              <span className="mt-1 block text-sm font-medium text-zinc-200 group-hover:text-white">{tr(next.title, locale)}</span>
            </Link>
          ) : (
            <Link
              href={`/month/${month.slug}#milestone`}
              className="group rounded-xl border border-sky-400/30 bg-sky-400/[0.04] p-4 text-right transition-colors hover:border-sky-400/60 sm:col-start-2"
            >
              <span className="text-xs text-sky-300/80">{t("finishMonth")} →</span>
              <span className="mt-1 block text-sm font-medium text-zinc-100">{tm("milestones")}</span>
            </Link>
          )}
        </nav>
      </article>

      <aside className="mt-16 lg:mt-0">
        <div className="space-y-5 lg:sticky lg:top-20 lg:max-h-[calc(100vh-6rem)] lg:overflow-y-auto lg:pb-8">
          <Link href={`/month/${month.slug}`} className="block text-xs text-zinc-500 hover:text-zinc-300">
            {tm("label", { n: month.id })} · {tr(month.title, locale)}
          </Link>
          <MonthProgress monthId={month.id} label={tm("progress")} />
          <ol className="space-y-0.5">
            {month.lessons.map((l, i) => {
              const active = l.slug === lesson.slug;
              return (
                <li key={l.slug}>
                  <Link
                    href={`/month/${month.slug}/${l.slug}`}
                    aria-current={active ? "page" : undefined}
                    className={`flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors ${
                      active ? "bg-white/[0.07] text-white" : "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-200"
                    }`}
                  >
                    <LessonStatusDot
                      lessonKey={lessonKey(month.id, l.slug)}
                      labels={{ done: t("statusDone"), todo: t("statusTodo") }}
                    />
                    <span className="font-mono text-xs text-zinc-500">{i + 1}</span>
                    <span className="min-w-0 flex-1 truncate">{tr(l.title, locale)}</span>
                  </Link>
                </li>
              );
            })}
          </ol>
          <div className="hidden border-t border-white/[0.06] pt-4 lg:block">
            <Toc items={toc} title={t("onThisPage")} variant="side" />
          </div>
          <div className="space-y-1 border-t border-white/[0.06] pt-4 text-xs">
            <a href="#tasks" className="block text-zinc-500 hover:text-zinc-300">↓ {t("tasks")}</a>
            <a href="#resources" className="block text-zinc-500 hover:text-zinc-300">↓ {t("resources")}</a>
          </div>
        </div>
      </aside>
    </div>
  );
}
