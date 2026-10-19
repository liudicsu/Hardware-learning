import { Link } from "@/i18n/navigation";
import { months } from "@/lib/curriculum";

export function MonthTabs({ current, labelFor }: { current: number; labelFor: (n: number) => string }) {
  return (
    <nav aria-label="months" className="-mx-1 flex gap-1 overflow-x-auto pb-1">
      {months.map((m) => (
        <Link
          key={m.id}
          href={`/month/${m.slug}`}
          aria-current={m.id === current ? "page" : undefined}
          className={`shrink-0 rounded-lg px-3 py-1.5 text-sm transition-colors ${
            m.id === current
              ? "bg-white/10 text-white"
              : m.status === "ready"
                ? "text-zinc-300 hover:bg-white/5"
                : "text-zinc-500 hover:bg-white/5 hover:text-zinc-300"
          }`}
        >
          {labelFor(m.id)}
        </Link>
      ))}
    </nav>
  );
}
