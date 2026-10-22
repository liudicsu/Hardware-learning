"use client";

import { useState } from "react";
import { tx, type CircuitPart, type CircuitSpec, type Locale, type Point } from "@/lib/diagrams/types";
import { DIAGRAM_UI } from "@/lib/diagrams/ui";
import { DG_FONT, DG_SUB_FONT, MONO, TONE } from "./BlockDiagram";

/** Terminals of a two-terminal part: at ± len/2 along its direction. */
export function terminals(p: CircuitPart): [Point, Point] {
  const half = (p.len ?? 36) / 2;
  const [x, y] = p.at;
  return p.dir === "h" ? [[x - half, y], [x + half, y]] : [[x, y - half], [x, y + half]];
}

const INK = TONE.ink;
const line = (a: Point, b: Point, extra: Record<string, unknown> = {}) => (
  <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} style={{ stroke: INK, strokeWidth: 1.6 }} {...extra} />
);
const dot = (p: Point, r = 2.6) => <circle cx={p[0]} cy={p[1]} r={r} style={{ fill: INK }} />;

function Label({ p, locale }: { p: CircuitPart; locale: Locale }) {
  const text = tx(p.label, locale);
  if (!text || !p.labelAt) return null;
  const [x, y] = p.labelAt;
  return (
    <text x={x} y={y} textAnchor={p.anchor ?? "middle"} style={{ fill: TONE[p.tone ?? "ink"], fontSize: p.type === "text" ? DG_SUB_FONT : DG_FONT, fontFamily: p.mono ? MONO : undefined, fontWeight: p.type === "text" ? 400 : 600 }}>
      {text.split("\n").map((l, k) => (
        <tspan key={k} x={x} dy={k === 0 ? 0 : DG_SUB_FONT + 3}>
          {l}
        </tspan>
      ))}
    </text>
  );
}

function Part({ p, closed }: { p: CircuitPart; closed: boolean }) {
  const [x, y] = p.at;
  const v = p.dir !== "h";
  const len = p.len ?? 36;
  switch (p.type) {
    case "switch": {
      const [a, b] = terminals(p);
      const open: Point = v ? [x + len * 0.5, a[1] + len * 0.866] : [a[0] + len * 0.866, y - len * 0.5];
      return <g>{line(a, closed ? b : open)}{dot(a)}{dot(b)}</g>;
    }
    case "button": {
      // normally-open push button: a contact plate beside the two terminals, pressed onto them when closed
      const [a, b] = terminals(p);
      const off = closed ? 0 : 9;
      if (v) {
        const px = x + off;
        return (
          <g>
            {line([px, a[1] + 3], [px, b[1] - 3], { style: { stroke: INK, strokeWidth: 2.4 } })}
            {line([px, y], [px + 12, y])}
            {line([px + 12, y - 6], [px + 12, y + 6])}
            {closed ? null : line(a, [x, a[1] + 3])}
            {dot(a)}{dot(b)}
          </g>
        );
      }
      const py = y - off;
      return (
        <g>
          {line([a[0] + 3, py], [b[0] - 3, py], { style: { stroke: INK, strokeWidth: 2.4 } })}
          {line([x, py], [x, py - 12])}
          {line([x - 6, py - 12], [x + 6, py - 12])}
          {dot(a)}{dot(b)}
        </g>
      );
    }
    case "resistor": {
      const [a, b] = terminals(p);
      const body = len * 0.62;
      const r0: Point = v ? [x, y - body / 2] : [x - body / 2, y];
      const r1: Point = v ? [x, y + body / 2] : [x + body / 2, y];
      return (
        <g>
          {line(a, r0)}{line(r1, b)}
          <rect x={v ? x - 6 : x - body / 2} y={v ? y - body / 2 : y - 6} width={v ? 12 : body} height={v ? body : 12} style={{ fill: "var(--dg-card)", stroke: INK, strokeWidth: 1.6 }} />
        </g>
      );
    }
    case "motor": {
      const [a, b] = terminals(p);
      const r = len / 2 - 2;
      return (
        <g>
          {line(a, v ? [x, y - r] : [x - r, y])}{line(v ? [x, y + r] : [x + r, y], b)}
          <circle cx={x} cy={y} r={r} style={{ fill: "var(--dg-card)", stroke: INK, strokeWidth: 1.6 }} />
          <text x={x} y={y + 4.5} textAnchor="middle" style={{ fill: INK, fontSize: 13, fontWeight: 700 }}>M</text>
        </g>
      );
    }
    case "supply":
      return <g>{line([x - 10, y], [x + 10, y], { style: { stroke: INK, strokeWidth: 2.4 } })}</g>;
    case "ground":
      return <g>{line([x - 10, y], [x + 10, y])}{line([x - 6, y + 4], [x + 6, y + 4])}{line([x - 2, y + 8], [x + 2, y + 8])}</g>;
    case "node":
      return dot(p.at, 3.2);
    case "box": {
      const [w, h] = p.size ?? [0, 0];
      return <rect x={x} y={y} width={w} height={h} rx={6} style={{ fill: "none", stroke: TONE.muted, strokeWidth: 1.2, strokeDasharray: "4 4" }} />;
    }
    default:
      return null;
  }
}

/** Arrowheads at the middle of every flow segment longer than 30 units, pointing along the flow. */
function flowArrows(pts: Point[]) {
  const out: { x: number; y: number; deg: number }[] = [];
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1];
    const [x1, y1] = pts[i];
    if (Math.hypot(x1 - x0, y1 - y0) < 30) continue;
    out.push({ x: (x0 + x1) / 2, y: (y0 + y1) / 2, deg: (Math.atan2(y1 - y0, x1 - x0) * 180) / Math.PI });
  }
  return out;
}

/** Schematic with a row of state buttons; the selected state sets the switches and draws the current path. */
export function CircuitDiagram({ spec, locale }: { spec: CircuitSpec; locale: Locale }) {
  const [i, setI] = useState(0);
  const st = spec.states[i];
  const hidden = new Set(st.hidden ?? []);
  const closed = new Set(st.closed);
  const tone = TONE[st.tone ?? "a"];
  const readout = tx(st.readout, locale);
  const btn = "rounded-md border px-2.5 py-1 text-sm transition-colors";
  return (
    <div data-circuit-state={st.id}>
      <div className="flex flex-wrap gap-2" role="group" aria-label={`${DIAGRAM_UI[locale].states}${locale === "zh" ? "：" : ": "}${tx(spec.title, locale)}`}>
        {spec.states.map((s, k) => (
          <button
            key={s.id}
            type="button"
            aria-pressed={k === i}
            onClick={() => setI(k)}
            className={`${btn} ${k === i ? "border-sky-400 bg-sky-400/10 text-sky-200" : "border-zinc-700 text-zinc-300 hover:border-sky-400"}`}
          >
            {tx(s.label, locale)}
          </button>
        ))}
      </div>
      <svg viewBox={`0 0 ${spec.w} ${spec.h}`} width="100%" role="img" aria-label={tx(spec.title, locale)} className="mx-auto mt-3 block" style={{ maxWidth: spec.w * 1.3, height: "auto" }}>
        <title>{tx(spec.title, locale)}</title>
        {spec.wires.filter((w) => !hidden.has(w.id)).map((w) => (
          <polyline key={w.id} points={w.pts.map((p) => p.join(",")).join(" ")} style={{ fill: "none", stroke: INK, strokeWidth: 1.6 }} />
        ))}
        {st.flow && (
          <g data-flow>
            <polyline points={st.flow.map((p) => p.join(",")).join(" ")} className="dg-flow" style={{ fill: "none", stroke: tone, strokeWidth: 4, strokeOpacity: 0.85, strokeDasharray: "8 6", strokeLinejoin: "round" }} />
            {flowArrows(st.flow).map((a, k) => (
              <path key={k} d="M-6,-5 L5,0 L-6,5 z" transform={`translate(${a.x} ${a.y}) rotate(${a.deg})`} style={{ fill: tone }} />
            ))}
          </g>
        )}
        {spec.parts.filter((p) => !hidden.has(p.id)).map((p) => (
          <g key={p.id} data-part={p.id}>
            <Part p={p} closed={closed.has(p.id)} />
            <Label p={p} locale={locale} />
          </g>
        ))}
        {readout && spec.readoutAt && (
          <text x={spec.readoutAt[0]} y={spec.readoutAt[1]} textAnchor="middle" style={{ fill: tone, fontSize: DG_FONT, fontWeight: 700 }}>
            {readout.split("\n").map((l, k) => (
              <tspan key={k} x={spec.readoutAt![0]} dy={k === 0 ? 0 : DG_FONT + 3}>
                {l}
              </tspan>
            ))}
          </text>
        )}
      </svg>
      <p className="mt-2 min-h-[3em] text-sm text-zinc-300" aria-live="polite">
        {tx(st.text, locale)}
      </p>
    </div>
  );
}
