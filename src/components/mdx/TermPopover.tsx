"use client";

import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "@/i18n/navigation";

export interface TermPopoverProps {
  id: string;
  children: ReactNode;
  /** Term in the page locale. */
  title: string;
  /** Term in the other locale, shown small so translations stay visible. */
  alt: string;
  def: string;
  lessonHref: string;
  lessonLabel: string;
  glossaryLabel: string;
  closeLabel: string;
}

const GAP = 6;
const MARGIN = 8;
const MAX_W = 304;

/**
 * Inline glossary term. Opens on mouse hover, keyboard focus, or tap/click (toggle); Escape, a tap
 * outside, or moving focus away closes it. The panel is position: fixed and clamped to the viewport,
 * so it never widens the page on a 390 px screen.
 */
export function TermPopover({ id, children, title, alt, def, lessonHref, lessonLabel, glossaryLabel, closeLabel }: TermPopoverProps) {
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number; width: number } | null>(null);
  const wrapRef = useRef<HTMLSpanElement>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLSpanElement>(null);
  const pointerDown = useRef(false);
  const hoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const panelId = `term-${id}-${useId().replace(/:/g, "")}`;

  const close = useCallback(() => {
    setOpen(false);
    setPinned(false);
  }, []);

  const place = useCallback(() => {
    const btn = btnRef.current;
    if (!btn) return;
    const r = btn.getBoundingClientRect();
    const vw = document.documentElement.clientWidth;
    const vh = window.innerHeight;
    const width = Math.min(MAX_W, vw - 2 * MARGIN);
    const left = Math.max(MARGIN, Math.min(r.left, vw - width - MARGIN));
    const h = panelRef.current?.offsetHeight ?? 0;
    const below = r.bottom + GAP;
    const top = below + h > vh - MARGIN && r.top - GAP - h > MARGIN ? r.top - GAP - h : below;
    setPos({ top, left, width });
  }, []);

  useLayoutEffect(() => {
    if (!open) return;
    place();
    // second pass once the panel has its real height
    const raf = requestAnimationFrame(place);
    return () => cancelAnimationFrame(raf);
  }, [open, place]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        close();
        btnRef.current?.focus();
      }
    };
    const onDown = (e: PointerEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) close();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("pointerdown", onDown);
    window.addEventListener("scroll", place, { passive: true });
    window.addEventListener("resize", place);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("pointerdown", onDown);
      window.removeEventListener("scroll", place);
      window.removeEventListener("resize", place);
    };
  }, [open, close, place]);

  const clearHover = () => {
    if (hoverTimer.current) clearTimeout(hoverTimer.current);
    hoverTimer.current = null;
  };

  return (
    <span
      ref={wrapRef}
      className="relative"
      onPointerEnter={(e) => {
        if (e.pointerType !== "mouse") return;
        clearHover();
        setOpen(true);
      }}
      onPointerLeave={(e) => {
        if (e.pointerType !== "mouse" || pinned) return;
        clearHover();
        hoverTimer.current = setTimeout(() => setOpen(false), 150);
      }}
      onBlur={(e) => {
        if (!wrapRef.current?.contains(e.relatedTarget as Node | null)) close();
      }}
    >
      <button
        ref={btnRef}
        type="button"
        data-term={id}
        aria-expanded={open}
        aria-controls={panelId}
        onPointerDown={() => {
          pointerDown.current = true;
        }}
        onFocus={() => {
          // keyboard focus opens; a tap is handled by onClick
          if (!pointerDown.current) setOpen(true);
        }}
        onClick={() => {
          pointerDown.current = false;
          if (pinned) close();
          else {
            setOpen(true);
            setPinned(true);
          }
        }}
        className="cursor-help rounded-sm text-inherit underline decoration-sky-400/60 decoration-dotted underline-offset-4 hover:decoration-sky-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
      >
        {children}
      </button>
      <span
        ref={panelRef}
        id={panelId}
        role="dialog"
        aria-label={title}
        hidden={!open}
        style={pos ? { position: "fixed", top: pos.top, left: pos.left, width: pos.width } : { position: "fixed", top: 0, left: 0, visibility: "hidden" }}
        className="z-50 block rounded-xl border border-white/10 bg-[#111113] p-3 text-left text-sm leading-relaxed text-zinc-300 shadow-xl shadow-black/50"
      >
        <span className="flex items-start justify-between gap-3">
          <span className="block">
            <span className="block font-semibold text-zinc-100">{title}</span>
            <span className="block text-xs text-zinc-500">{alt}</span>
          </span>
          <button
            type="button"
            onClick={() => {
              close();
              btnRef.current?.focus();
            }}
            aria-label={closeLabel}
            className="-m-1 rounded p-1 text-zinc-500 hover:text-zinc-200"
          >
            ×
          </button>
        </span>
        <span className="mt-2 block">{def}</span>
        <span className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs">
          <Link href={lessonHref} className="text-sky-400 hover:text-sky-300">
            {lessonLabel}
          </Link>
          <Link href={`/glossary#${id}`} className="text-sky-400 hover:text-sky-300">
            {glossaryLabel} →
          </Link>
        </span>
      </span>
    </span>
  );
}
