"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { circuits, type CircuitId } from "@/lib/circuits";

export interface FalstadProps {
  title: string;
  /** Key of a circuit defined in src/lib/circuits.ts. */
  circuit?: CircuitId;
  startCircuit?: string;
  cct?: string;
  height?: number;
}

const BASE = "https://www.falstad.com/circuit/circuitjs.html";

function buildSrc(startCircuit?: string, cct?: string): string {
  const params: string[] = [];
  if (startCircuit) params.push(`startCircuit=${encodeURIComponent(startCircuit)}`);
  if (cct) params.push(`cct=${encodeURIComponent(cct.trim())}`);
  params.push("running=true");
  return `${BASE}?${params.join("&")}`;
}

function BoltIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
      className="h-4 w-4 shrink-0 text-sky-400"
    >
      <path d="M13 2 3.4 14H10l-1.2 8L18.6 10H12l1-8Z" />
    </svg>
  );
}

export function Falstad({ title, circuit, startCircuit, cct, height = 420 }: FalstadProps) {
  const t = useTranslations("falstad");
  const def = circuit ? circuits[circuit] : undefined;
  const sc = def && "startCircuit" in def ? def.startCircuit : startCircuit;
  const raw = def && "cct" in def ? def.cct : cct;
  const src = useMemo(() => buildSrc(sc, raw), [sc, raw]);
  const boxRef = useRef<HTMLDivElement>(null);
  // The iframe is only mounted once the box scrolls near the viewport, so the
  // load timer measures real loading time and onLoad is never missed during
  // hydration.
  const [visible, setVisible] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    const el = boxRef.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      // Very old browsers: mount on the next frame instead of observing.
      const id = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(id);
    }
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setVisible(true);
          io.disconnect();
        }
      },
      { rootMargin: "300px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (!visible || loaded) return;
    const timer = setTimeout(() => setTimedOut(true), 15000);
    return () => clearTimeout(timer);
  }, [visible, loaded]);

  return (
    <figure className="not-prose my-8 rounded-xl border border-white/10 bg-[#111113] p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <BoltIcon />
          <figcaption className="truncate text-sm font-medium text-zinc-100">
            {title}
          </figcaption>
        </div>
        <a
          href={src}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 text-xs text-sky-400 transition-colors hover:text-sky-300"
        >
          {t("openNew")}
        </a>
      </div>

      <div
        ref={boxRef}
        className="relative mt-3 overflow-hidden rounded-lg border border-white/10 bg-white"
        style={{ height }}
      >
        {visible && (
          <iframe
            src={src}
            title={title}
            width="100%"
            height={height}
            allow="fullscreen"
            onLoad={() => setLoaded(true)}
            className="block w-full bg-white"
            style={{ height }}
          />
        )}
        {!loaded && (
          <div
            aria-hidden="true"
            className="absolute inset-0 flex items-center justify-center bg-[#111113] text-sm text-zinc-400"
          >
            {t("loading")}
          </div>
        )}
      </div>

      {timedOut && !loaded && (
        <p className="mt-3 rounded-lg bg-white/[0.03] p-3 text-xs text-amber-300/90">
          <a
            href={src}
            target="_blank"
            rel="noopener noreferrer"
            className="underline decoration-dotted underline-offset-2 hover:text-amber-200"
          >
            {t("fallback")}
          </a>
        </p>
      )}

      <p className="mt-3 text-xs text-zinc-500">{t("hint")}</p>
      <p className="mt-1 text-xs text-zinc-500">{t("credit")}</p>
    </figure>
  );
}
