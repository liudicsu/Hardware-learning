import type { ReactNode } from "react";

type CalloutType = "info" | "warn" | "tip" | "danger";

const STYLE: Record<CalloutType, { border: string; text: string }> = {
  info: { border: "border-l-sky-400", text: "text-sky-400" },
  tip: { border: "border-l-emerald-400", text: "text-emerald-400" },
  warn: { border: "border-l-amber-400", text: "text-amber-400" },
  danger: { border: "border-l-rose-500", text: "text-rose-500" },
};

function TypeIcon({ type }: { type: CalloutType }) {
  const common = "h-4 w-4 shrink-0";
  if (type === "info") {
    return (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        aria-hidden="true"
        className={common}
      >
        <circle cx="12" cy="12" r="9" />
        <path d="M12 11v5" />
        <circle cx="12" cy="8" r="0.6" fill="currentColor" stroke="none" />
      </svg>
    );
  }
  if (type === "tip") {
    return (
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className={common}>
        <path d="M12 2c.7 3.8 2.2 5.3 6 6-3.8.7-5.3 2.2-6 6-.7-3.8-2.2-5.3-6-6 3.8-.7 5.3-2.2 6-6Zm6.5 11c.35 1.9 1.1 2.65 3 3-1.9.35-2.65 1.1-3 3-.35-1.9-1.1-2.65-3-3 1.9-.35 2.65-1.1 3-3Z" />
      </svg>
    );
  }
  if (type === "warn") {
    return (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        className={common}
      >
        <path d="M10.3 4.1 2.9 17a2 2 0 0 0 1.7 3h14.8a2 2 0 0 0 1.7-3L13.7 4.1a2 2 0 0 0-3.4 0Z" />
        <path d="M12 9.5V14" />
        <circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />
      </svg>
    );
  }
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      aria-hidden="true"
      className={common}
    >
      <circle cx="12" cy="12" r="9" />
      <path d="m15 9-6 6m0-6 6 6" />
    </svg>
  );
}

export interface CalloutProps {
  type?: CalloutType;
  title?: string;
  children: ReactNode;
}

export function Callout({ type = "info", title, children }: CalloutProps) {
  const style = STYLE[type];
  return (
    <div className={`my-6 rounded-lg border-l-2 border-y border-r border-white/10 bg-white/[0.03] p-4 ${style.border}`}>
      <div className="flex items-start gap-3">
        <div className={`${style.text} flex h-4 w-4 translate-y-0.5`}>
          <TypeIcon type={type} />
        </div>
        <div className="min-w-0 text-[0.95rem] leading-relaxed [&_p+p]:mt-2">
          {title !== undefined && (
            <p className="font-semibold text-zinc-100">{title}</p>
          )}
          <div className={title !== undefined ? "mt-1 text-zinc-300" : "text-zinc-300"}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
