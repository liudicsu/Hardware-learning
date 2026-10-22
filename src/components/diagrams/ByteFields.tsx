"use client";

import { useState } from "react";
import { tx, type BytesSpec, type Locale } from "@/lib/diagrams/types";
import { DIAGRAM_UI } from "@/lib/diagrams/ui";
import { TONE } from "./BlockDiagram";

// Layout in viewBox units (read by tools/check_diagrams.mjs).
export const BF_CELL = 40;
export const BF_GAP = 4;
export const BF_PAD = 8;
export const BF_HEX_FONT = 18;
export const BF_LABEL_FONT = 15;
export const BF_BRACKET_H = 28;

const hex = (v: number) => v.toString(16).toUpperCase().padStart(2, "0");

/** Bytes of one packet in a row, coloured by field, with brackets and a byte-by-byte table; one button per packet. */
export function ByteFields({ spec, locale }: { spec: BytesSpec; locale: Locale }) {
  const [i, setI] = useState(0);
  const ui = DIAGRAM_UI[locale];
  const pk = spec.packets[i];
  const n = pk.bytes.length;
  const top = (pk.groups ?? []).filter((g) => (g.side ?? "top") === "top");
  const bottom = (pk.groups ?? []).filter((g) => g.side === "bottom");
  // every packet uses the width of the longest one, so the cells keep their size when switching
  const maxN = Math.max(...spec.packets.map((p) => p.bytes.length));
  const w = 2 * BF_PAD + maxN * BF_CELL + (maxN - 1) * BF_GAP;
  const y0 = BF_PAD + (spec.packets.some((p) => p.groups?.some((g) => (g.side ?? "top") === "top")) ? BF_BRACKET_H : 0);
  const h = y0 + BF_CELL + (spec.packets.some((p) => p.groups?.some((g) => g.side === "bottom")) ? BF_BRACKET_H : 0) + BF_PAD;
  const x = (k: number) => BF_PAD + k * (BF_CELL + BF_GAP);
  const colour = (k: number) => (pk.bytes[k].bad ? TONE.danger : TONE[spec.fields[pk.bytes[k].field].tone]);
  const bracket = (g: { from: number; to: number; label: { zh: string; en: string } | string }, down: boolean, k: number) => {
    const x0 = x(g.from) + 2;
    const x1 = x(g.to) + BF_CELL - 2;
    const y = down ? y0 + BF_CELL + 6 : y0 - 6;
    const t = down ? 6 : -6;
    return (
      <g key={`${down ? "b" : "t"}${k}`}>
        <path d={`M${x0},${y - t}L${x0},${y}L${x1},${y}L${x1},${y - t}`} fill="none" style={{ stroke: "var(--dg-muted)" }} strokeWidth={1.5} />
        <text x={(x0 + x1) / 2} y={down ? y + 18 : y - 6} textAnchor="middle" fontSize={BF_LABEL_FONT} style={{ fill: "var(--dg-ink)" }}>
          {tx(g.label, locale)}
        </text>
      </g>
    );
  };
  const btn = "rounded-md border px-2.5 py-1 text-sm transition-colors";
  return (
    <div data-bytes-packet={pk.id}>
      <div className="flex flex-wrap gap-2" role="group" aria-label={`${ui.packets}${locale === "zh" ? "：" : ": "}${tx(spec.title, locale)}`}>
        {spec.packets.map((p, k) => (
          <button
            key={p.id}
            type="button"
            aria-pressed={k === i}
            onClick={() => setI(k)}
            className={`${btn} ${k === i ? "border-sky-400 bg-sky-400/10 text-sky-200" : "border-zinc-700 text-zinc-300 hover:border-sky-400"}`}
          >
            {tx(p.label, locale)}
          </button>
        ))}
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img" aria-label={pk.bytes.map((b) => hex(b.v)).join(" ")} className="mt-3 block" style={{ maxWidth: w * 1.3, height: "auto" }}>
        {top.map((g, k) => bracket(g, false, k))}
        {pk.bytes.map((b, k) => (
          <g key={k} data-byte={k}>
            <rect x={x(k)} y={y0} width={BF_CELL} height={BF_CELL} rx={5} style={{ fill: colour(k), stroke: colour(k) }} fillOpacity={0.16} strokeWidth={b.bad ? 3 : 2} />
            <text x={x(k) + BF_CELL / 2} y={y0 + BF_CELL / 2 + 6} textAnchor="middle" fontSize={BF_HEX_FONT} fontFamily="ui-monospace, monospace" style={{ fill: "var(--dg-ink)" }}>
              {hex(b.v)}
            </text>
          </g>
        ))}
        {bottom.map((g, k) => bracket(g, true, k))}
      </svg>
      <table className="mt-3 w-full border-collapse text-sm">
        <thead>
          <tr className="text-left text-xs text-zinc-500">
            <th className="w-8 py-1 pr-2 font-normal">#</th>
            <th className="py-1 pr-2 font-normal">{ui.byte}</th>
            <th className="py-1 pr-2 font-normal">{ui.field}</th>
            <th className="py-1 font-normal">{ui.meaning}</th>
          </tr>
        </thead>
        <tbody>
          {pk.bytes.map((b, k) => (
            <tr key={k} className="border-t border-zinc-800 align-top">
              <td className="py-1 pr-2 text-zinc-500">{k}</td>
              <td className="py-1 pr-2">
                <span className="inline-block rounded border-l-4 bg-zinc-900 px-1.5 font-mono text-zinc-100" style={{ borderColor: colour(k) }}>
                  {hex(b.v)}
                </span>
              </td>
              <td className="py-1 pr-2 text-zinc-300">{tx(spec.fields[b.field].label, locale)}</td>
              <td className="py-1 text-zinc-300">{tx(b.note, locale)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-sm text-zinc-200" aria-live="polite">
        {tx(pk.summary, locale)}
      </p>
    </div>
  );
}
