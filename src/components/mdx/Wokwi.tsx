import type { ReactNode } from "react";
import { useTranslations } from "next-intl";
import { REPO_URL } from "@/lib/site";

export interface WokwiProps {
  board: "uno" | "esp32-s3";
  /** Repository paths, e.g. the sketch .ino and its diagram.json. */
  files: string[];
  projectId?: string;
  title?: string;
  children?: ReactNode;
}

const NEW_PROJECT = {
  uno: "https://wokwi.com/projects/new/arduino-uno",
  "esp32-s3": "https://wokwi.com/projects/new/esp32-s3",
};

function ChipIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="h-4 w-4 shrink-0 text-sky-400"
    >
      <rect x="7" y="7" width="10" height="10" rx="1.5" />
      <path d="M10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4" />
    </svg>
  );
}

export function Wokwi({ board, files, projectId, title, children }: WokwiProps) {
  const t = useTranslations("wokwi");

  return (
    <figure className="not-prose my-8 rounded-xl border border-white/10 bg-[#111113] p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <ChipIcon />
          <figcaption className="min-w-0 text-sm font-medium text-zinc-100">
            {title ?? t("title")}
          </figcaption>
        </div>
        <span className="shrink-0 rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[11px] text-zinc-400">
          {t(`board.${board}`)}
        </span>
      </div>

      <div className="mt-3 min-w-0">
        <p className="text-xs text-zinc-500">{t("files")}</p>
        <ul className="mt-1 space-y-1">
          {files.map((path) => (
            <li key={path} className="min-w-0">
              <a
                href={`${REPO_URL}/blob/main/${path}`}
                target="_blank"
                rel="noreferrer"
                className="break-all font-mono text-xs text-sky-400 hover:text-sky-300"
              >
                {path} ↗
              </a>
            </li>
          ))}
        </ul>
      </div>

      {projectId ? (
        <a
          href={`https://wokwi.com/projects/${projectId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-4 inline-flex min-w-0 max-w-full items-center rounded-lg bg-sky-400 px-3 py-2 text-sm font-medium text-zinc-950 transition-colors hover:bg-sky-300"
        >
          <span className="min-w-0 break-words">{t("openProject")}</span>
        </a>
      ) : (
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-zinc-300">
          <li className="min-w-0">
            {t("step1")}{" "}
            <a
              href={NEW_PROJECT[board]}
              target="_blank"
              rel="noopener noreferrer"
              className="break-words text-sky-400 underline decoration-dotted underline-offset-2 hover:text-sky-300"
            >
              {t(`newProject.${board}`)}
            </a>
          </li>
          <li className="min-w-0">{t("step2")}</li>
          <li className="min-w-0">{t("step3")}</li>
        </ol>
      )}

      {children && <div className="mt-3 text-sm text-zinc-300">{children}</div>}

      <p className="mt-3 text-xs text-amber-300/90">{t("network")}</p>
    </figure>
  );
}
