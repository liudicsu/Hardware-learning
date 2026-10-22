import { getTranslations } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { LocaleSwitcher } from "./LocaleSwitcher";
import { NavLink } from "./NavLink";

export async function Header() {
  const t = await getTranslations("nav");
  const site = await getTranslations("site");
  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-white">
          <svg aria-hidden viewBox="0 0 24 24" className="h-5 w-5 text-sky-400" fill="none" stroke="currentColor" strokeWidth="1.6">
            <rect x="5" y="5" width="14" height="14" rx="2.5" />
            <path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3" strokeLinecap="round" />
            <circle cx="12" cy="12" r="2.2" />
          </svg>
          <span>{site("name")}</span>
        </Link>
        <nav className="ml-2 hidden items-center gap-0.5 sm:flex">
          <NavLink href="/month/month-1" match="/month">{t("roadmap")}</NavLink>
          <NavLink href="/resources">{t("resources")}</NavLink>
          <NavLink href="/glossary">{t("glossary")}</NavLink>
          <NavLink href="/math">{t("math")}</NavLink>
          <NavLink href="/about">{t("about")}</NavLink>
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <LocaleSwitcher />
        </div>
      </div>
      <nav className="flex items-center gap-1 overflow-x-auto border-t border-white/[0.06] px-3 py-1.5 sm:hidden">
        <NavLink href="/month/month-1" match="/month">{t("roadmap")}</NavLink>
        <NavLink href="/resources">{t("resources")}</NavLink>
        <NavLink href="/glossary">{t("glossary")}</NavLink>
        <NavLink href="/math">{t("math")}</NavLink>
        <NavLink href="/about">{t("about")}</NavLink>
      </nav>
    </header>
  );
}
