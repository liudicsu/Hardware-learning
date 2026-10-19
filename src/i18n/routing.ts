import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["zh", "en"],
  defaultLocale: "zh",
  // Always start in Chinese; switching to English is explicit via the header switcher.
  localeDetection: false,
});

export type Locale = (typeof routing.locales)[number];
