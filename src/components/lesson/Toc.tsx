"use client";

import { useEffect, useState } from "react";
import type { TocItem } from "@/lib/toc";

/** Section list with the section currently in view highlighted. */
export function Toc({ items, title, variant }: { items: TocItem[]; title: string; variant: "side" | "inline" }) {
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    if (variant !== "side" || typeof IntersectionObserver === "undefined") return;
    const els = items.map((i) => document.getElementById(i.id)).filter((e): e is HTMLElement => !!e);
    const visible = new Set<string>();
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) visible.add(e.target.id);
          else visible.delete(e.target.id);
        }
        // Topmost visible heading wins; otherwise keep the last one scrolled past.
        const first = els.find((el) => visible.has(el.id));
        if (first) setActive(first.id);
        else {
          const passed = els.filter((el) => el.getBoundingClientRect().top < 80);
          if (passed.length) setActive(passed[passed.length - 1].id);
        }
      },
      { rootMargin: "-64px 0px -55% 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [items, variant]);

  if (items.length === 0) return null;

  const list = (
    <ol className="space-y-0.5 text-[13px] leading-snug">
      {items.map((i) => (
        <li key={i.id}>
          <a
            href={`#${i.id}`}
            className={`block border-l py-1 pl-3 transition-colors ${
              active === i.id
                ? "border-sky-400 text-sky-300"
                : "border-white/10 text-zinc-500 hover:border-white/30 hover:text-zinc-300"
            }`}
          >
            {i.text}
          </a>
        </li>
      ))}
    </ol>
  );

  if (variant === "inline") {
    return (
      <details className="mt-8 rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3 lg:hidden">
        <summary className="cursor-pointer text-sm text-zinc-300">{title}</summary>
        <div className="mt-3">{list}</div>
      </details>
    );
  }
  return (
    <nav aria-label={title}>
      <p className="mb-2 text-xs font-medium text-zinc-400">{title}</p>
      {list}
    </nav>
  );
}
