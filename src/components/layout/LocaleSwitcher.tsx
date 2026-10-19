"use client";

import { useLocale, useTranslations } from "next-intl";
import { useParams } from "next/navigation";
import { useTransition } from "react";
import { usePathname, useRouter } from "@/i18n/navigation";

export function LocaleSwitcher() {
  const t = useTranslations("nav");
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams();
  const [pending, startTransition] = useTransition();
  const next = locale === "zh" ? "en" : "zh";

  return (
    <button
      type="button"
      aria-label={`${t("language")}: ${t("switchTo")}`}
      disabled={pending}
      onClick={() =>
        startTransition(() => {
          // Keep the hash so the reader stays at the same section.
          const hash = typeof window !== "undefined" ? window.location.hash : "";
          router.replace(
            // @ts-expect-error -- pathname + params always match the current route
            { pathname, params },
            { locale: next, scroll: false },
          );
          if (hash) {
            window.setTimeout(() => {
              document.getElementById(hash.slice(1))?.scrollIntoView();
            }, 300);
          }
        })
      }
      className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-white/10 px-2.5 text-xs font-medium text-zinc-300 transition-colors hover:border-white/25 hover:text-white disabled:opacity-60"
    >
      <svg aria-hidden viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.4">
        <circle cx="8" cy="8" r="6.25" />
        <path d="M1.75 8h12.5M8 1.75c1.8 1.9 2.6 3.9 2.6 6.25S9.8 12.35 8 14.25M8 1.75C6.2 3.65 5.4 5.65 5.4 8s.8 4.35 2.6 6.25" />
      </svg>
      {t("switchTo")}
    </button>
  );
}
