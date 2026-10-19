import { useTranslations } from "next-intl";

const REPO = "https://github.com/liudicsu/Hardware-learning/blob/main";

/** A link from a lesson code block to the same file in the repository. */
export function CodeSource({ path }: { path: string }) {
  const t = useTranslations("code");
  return (
    <p className="not-prose -mb-3 mt-5 flex items-center gap-2 text-xs text-zinc-500">
      <span>{t("source")}</span>
      <a href={`${REPO}/${path}`} target="_blank" rel="noreferrer" className="font-mono text-sky-400 hover:text-sky-300">
        {path} ↗
      </a>
    </p>
  );
}
