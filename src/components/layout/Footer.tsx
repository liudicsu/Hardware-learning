import { getTranslations } from "next-intl/server";
import { COURSE_SOURCE } from "@/lib/curriculum";
import { REPO_URL } from "@/lib/site";

export async function Footer() {
  const t = await getTranslations("footer");
  return (
    <footer className="border-t border-white/[0.06]">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-8 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="space-y-1">
          <p>
            {t("course")}
            <a href={COURSE_SOURCE.url} target="_blank" rel="noopener noreferrer" className="text-zinc-300 underline decoration-white/20 underline-offset-2 hover:decoration-white/60">
              {t("courseBy")}
            </a>
          </p>
          <p>{t("copyright")}</p>
        </div>
        <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="text-zinc-400 hover:text-zinc-100">
          {t("repo")} ↗
        </a>
      </div>
    </footer>
  );
}
