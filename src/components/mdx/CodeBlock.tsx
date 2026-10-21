"use client";

import { isValidElement, useState, type ComponentProps, type ReactNode } from "react";
import { useTranslations } from "next-intl";

/** Blocks longer than this many lines start collapsed. */
const COLLAPSE_OVER = 30;
/** Lines visible while collapsed. */
const PREVIEW_LINES = 15;

function textOf(node: ReactNode): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(textOf).join("");
  if (isValidElement<{ children?: ReactNode }>(node)) return textOf(node.props.children);
  return "";
}

/**
 * Replaces MDX's <pre>. Short blocks render as before (plus a copy button); long blocks
 * show the first lines with an "Expand all" button. The full code is always in the DOM,
 * so selecting, copying and searching still see every line.
 */
export function CodeBlock({ children, style, ...rest }: ComponentProps<"pre">) {
  const t = useTranslations("code");
  const text = textOf(children).replace(/\n$/, "");
  const lines = text.split("\n").length;
  const collapsible = lines > COLLAPSE_OVER;
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const collapsed = collapsible && !expanded;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard blocked: the text can still be selected by hand */
    }
  };

  return (
    <div className="code-block group relative my-5 min-w-0 max-w-full" data-lines={lines} data-collapsed={collapsed || undefined}>
      <pre
        {...rest}
        style={{
          ...style,
          margin: 0,
          // 15 lines of 0.85rem × 1.65 line height, plus the 1rem top padding
          ...(collapsed ? { maxHeight: `calc(1rem + ${PREVIEW_LINES} * 0.85rem * 1.65)`, overflowY: "hidden" } : {}),
        }}
      >
        {children}
      </pre>
      <button
        type="button"
        onClick={copy}
        aria-label={t("copy")}
        className="absolute right-2 top-2 rounded-md border border-white/10 bg-[#18181b]/90 px-2 py-1 text-xs text-zinc-400 opacity-0 transition-opacity hover:text-zinc-100 focus:opacity-100 group-hover:opacity-100"
      >
        {copied ? t("copied") : t("copy")}
      </button>
      {collapsed && (
        <div className="pointer-events-none absolute inset-x-px bottom-px h-16 rounded-b-xl bg-gradient-to-t from-[#0f0f11] to-transparent" />
      )}
      {collapsible && (
        <div className={collapsed ? "absolute inset-x-0 bottom-2 flex justify-center" : "mt-2 flex justify-center"}>
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
            className="rounded-full border border-white/15 bg-[#18181b] px-3 py-1 text-xs font-medium text-zinc-200 hover:border-sky-400/50 hover:text-white"
          >
            {expanded ? t("collapse") : t("expandAll", { lines })}
          </button>
        </div>
      )}
    </div>
  );
}
