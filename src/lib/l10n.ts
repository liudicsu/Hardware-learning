import type { L10n, Locale } from "./types";

export function tr(value: L10n, locale: string): string {
  return value[(locale === "en" ? "en" : "zh") as Locale];
}

export function asLocale(locale: string): Locale {
  return locale === "en" ? "en" : "zh";
}
