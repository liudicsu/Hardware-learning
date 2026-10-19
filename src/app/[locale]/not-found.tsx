import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

export default function NotFound() {
  const t = useTranslations("notFound");
  return (
    <div className="py-24 text-center">
      <p className="font-mono text-sm text-zinc-500">404</p>
      <h1 className="mt-3 text-2xl font-semibold text-white">{t("title")}</h1>
      <Link href="/" className="mt-6 inline-block text-sm text-sky-400 hover:text-sky-300">
        {t("back")} →
      </Link>
    </div>
  );
}
