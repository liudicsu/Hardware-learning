"use client";

import type { ReactNode } from "react";
import { useTranslations } from "next-intl";

const REPO = "https://github.com/liudicsu/Hardware-learning/blob/main";

export interface WidgetShellProps {
  title: string;
  /** Repository path of the Python script this widget mirrors. */
  script: string;
  onReset: () => void;
  children: ReactNode;
}

/** Shared frame for the small, interactive ports of the Python lesson models. */
export function WidgetShell({ title, script, onReset, children }: WidgetShellProps) {
  const t = useTranslations("widget");
  return (
    <figure className="not-prose my-6 max-w-full overflow-hidden rounded-xl border border-amber-400/25 bg-amber-400/[0.03]">
      <figcaption className="border-b border-amber-400/15 px-4 py-2 text-xs">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="rounded-full border border-amber-400/40 px-2 py-0.5 font-semibold uppercase tracking-wide text-amber-300">
            {t("label")}
          </span>
          <span className="min-w-0 flex-1 font-medium text-zinc-200">{title}</span>
          <button
            type="button"
            onClick={onReset}
            className="shrink-0 rounded-lg border border-white/10 px-2.5 py-1 text-xs text-zinc-300 transition-colors hover:border-white/20 hover:bg-white/[0.05] hover:text-white"
          >
            {t("reset")}
          </button>
        </div>
        <div className="mt-1.5 space-y-1 text-zinc-500">
          <p className="flex flex-wrap items-baseline gap-x-1.5 gap-y-1">
            <span>{t("mirrors")}</span>
            <a
              href={`${REPO}/${script}`}
              target="_blank"
              rel="noreferrer"
              className="min-w-0 break-all font-mono text-sky-400 hover:text-sky-300"
            >
              {script} ↗
            </a>
          </p>
          <p>{t("note")}</p>
        </div>
      </figcaption>
      <div className="min-w-0 max-w-full px-4 pb-4 pt-3">{children}</div>
    </figure>
  );
}
