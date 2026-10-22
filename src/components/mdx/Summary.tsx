import type { ReactNode } from "react";

export interface SummaryProps {
  title: string;
  children: ReactNode;
}

/** End-of-lesson summary: key points, common mistakes, self-check, what the next lesson reuses. */
export function Summary({ title, children }: SummaryProps) {
  return (
    <section
      aria-label={title}
      data-summary
      className="my-10 rounded-xl border border-sky-400/25 bg-sky-400/[0.03] p-5 [&_p]:my-2 [&_strong]:text-zinc-100 [&_ul]:my-2"
    >
      <p className="!mt-0 text-xs font-medium uppercase tracking-wider text-sky-400">{title}</p>
      {children}
    </section>
  );
}
