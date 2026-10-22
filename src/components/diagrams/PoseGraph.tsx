"use client";

import { useState } from "react";
import { tx, type Locale, type PoseGraphFrame, type PoseGraphSpec } from "@/lib/diagrams/types";
import { TONE } from "./BlockDiagram";
import { StepControls } from "./StepControls";

// Layout in viewBox units (read by tools/check_diagrams.mjs).
export const PG_SCALE = 100; // units per metre
export const PG_PAD = 22;
export const PG_FONT = 13;
export const PG_NODE_R = 3.5;

/** Bounds of every pose drawn in any frame, so the view does not jump between steps. */
export function poseGraphView(spec: PoseGraphSpec) {
  const ps = [...spec.estimate, ...spec.corrected];
  const x0 = Math.min(...ps.map((p) => p.x));
  const x1 = Math.max(...ps.map((p) => p.x));
  const y0 = Math.min(...ps.map((p) => p.y));
  const y1 = Math.max(...ps.map((p) => p.y));
  const w = Math.ceil((x1 - x0) * PG_SCALE + 2 * PG_PAD);
  const h = Math.ceil((y1 - y0) * PG_SCALE + 2 * PG_PAD);
  // metres -> viewBox (y up in the world, down in SVG)
  const at = (p: { x: number; y: number }): [number, number] => [PG_PAD + (p.x - x0) * PG_SCALE, PG_PAD + (y1 - p.y) * PG_SCALE];
  return { w, h, at };
}

/** Where the SVG labels go (shared with the check). */
export function poseGraphLabels(spec: PoseGraphSpec) {
  const { at } = poseGraphView(spec);
  const n = spec.estimate.length - 1;
  const [sx, sy] = at(spec.estimate[0]);
  const [ax, ay] = at(spec.estimate[0]);
  const [bx, by] = at(spec.estimate[1]);
  const [ex, ey] = at(spec.estimate[n]);
  const [tx0, ty0] = at(spec.truth[n]);
  return {
    start: { x: sx + 8, y: sy + 18, anchor: "start" as const },
    spacing: { x: (ax + bx) / 2, y: Math.min(ay, by) - 10, anchor: "middle" as const },
    gap: { x: (ex + tx0) / 2 + 10, y: (ey + ty0) / 2 + 4, anchor: "start" as const },
  };
}

const ALL: PoseGraphFrame = { label: "", upto: Infinity, loop: true };

/** SLAM pose graph stepped through frame by frame: nodes, scan matching, drift, loop closure. */
export function PoseGraph({ spec, locale }: { spec: PoseGraphSpec; locale: Locale }) {
  const [i, setI] = useState(-1);
  const f = i >= 0 ? spec.frames[i] : ALL;
  const { w, h, at } = poseGraphView(spec);
  const L = poseGraphLabels(spec);
  const n = Math.min(f.upto, spec.estimate.length);
  const last = spec.estimate.length - 1;
  const shown = (f.loop ? spec.corrected : spec.estimate).slice(0, n).map(at);
  const pathOf = (pts: [number, number][]) => pts.map(([x, y], k) => `${k ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join("");
  const bulge = ([x0, y0]: [number, number], [x1, y1]: [number, number], s: number) => {
    const mx = (x0 + x1) / 2, my = (y0 + y1) / 2, dx = x1 - x0, dy = y1 - y0, l = Math.hypot(dx, dy) || 1;
    return `M${x0.toFixed(1)},${y0.toFixed(1)}Q${(mx - (dy / l) * s).toFixed(1)},${(my + (dx / l) * s).toFixed(1)} ${x1.toFixed(1)},${y1.toFixed(1)}`;
  };
  const matchFrom = f.match;
  const font = { fontSize: PG_FONT, style: { fill: "var(--dg-ink)" } };
  const swatch = (colour: string, dashed = false) => (
    <svg width="22" height="10" aria-hidden className="inline-block shrink-0">
      <line x1="1" y1="5" x2="21" y2="5" style={{ stroke: colour }} strokeWidth={2} strokeDasharray={dashed ? "4 3" : undefined} />
    </svg>
  );
  const [gx0, gy0] = at(spec.estimate[last]);
  const [gx1, gy1] = at(spec.truth[last]);
  const [lx0, ly0] = at(spec.corrected[last]);
  const [lx1, ly1] = at(spec.corrected[0]);
  return (
    <div data-pose-frame={i}>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img" aria-label={tx(spec.title, locale)} className="mx-auto block" style={{ maxWidth: w * 1.5, height: "auto" }}>
        {f.loop && (
          <g opacity={0.55}>
            <path d={pathOf(spec.estimate.map(at))} fill="none" style={{ stroke: "var(--dg-faint)" }} strokeWidth={1.5} />
            {spec.estimate.map((p, k) => {
              const [x, y] = at(p);
              return <circle key={k} cx={x} cy={y} r={PG_NODE_R - 1} style={{ fill: "var(--dg-faint)" }} />;
            })}
          </g>
        )}
        <path d={pathOf(shown)} fill="none" style={{ stroke: "var(--dg-muted)" }} strokeWidth={1.5} />
        {matchFrom !== undefined &&
          Array.from({ length: spec.matchWindow }, (_, k) => matchFrom - 1 - k)
            .filter((j) => j >= 0)
            .map((j, k) => <path key={j} d={bulge(shown[matchFrom], shown[j], 10 + 6 * k)} fill="none" style={{ stroke: TONE.b }} strokeWidth={2} />)}
        {shown.map(([x, y], k) => (
          <circle key={k} cx={x} cy={y} r={k === matchFrom ? PG_NODE_R + 1.5 : PG_NODE_R} style={{ fill: k === matchFrom ? TONE.b : TONE.a }} />
        ))}
        {f.gap && (
          <g>
            <line x1={gx0} y1={gy0} x2={gx1} y2={gy1} style={{ stroke: TONE.danger }} strokeWidth={2} strokeDasharray="4 3" />
            <circle cx={gx1} cy={gy1} r={PG_NODE_R + 1.5} fill="none" style={{ stroke: TONE.danger }} strokeWidth={1.5} />
            <text x={L.gap.x} y={L.gap.y} textAnchor={L.gap.anchor} {...font}>
              {tx(spec.text.gap, locale)}
            </text>
          </g>
        )}
        {f.loop && (
          <path
            d={`M${lx0.toFixed(1)},${ly0.toFixed(1)}C${(lx0 - 40).toFixed(1)},${(ly0 + 10).toFixed(1)} ${(lx1 - 30).toFixed(1)},${(ly1 + 34).toFixed(1)} ${lx1.toFixed(1)},${ly1.toFixed(1)}`}
            fill="none"
            style={{ stroke: TONE.ok }}
            strokeWidth={2}
            strokeDasharray="5 3"
          />
        )}
        {f.spacing && (
          <text x={L.spacing.x} y={L.spacing.y} textAnchor={L.spacing.anchor} {...font}>
            {tx(spec.text.spacing, locale)}
          </text>
        )}
        <text x={L.start.x} y={L.start.y} textAnchor={L.start.anchor} {...font}>
          {tx(spec.text.start, locale)}
        </text>
      </svg>
      <p className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-zinc-400">
        <span className="inline-flex items-center gap-1.5">{swatch(TONE.a)}{tx(spec.legend.odom, locale)}</span>
        <span className="inline-flex items-center gap-1.5">{swatch(TONE.b)}{tx(spec.legend.match, locale)}</span>
        <span className="inline-flex items-center gap-1.5">{swatch(TONE.ok, true)}{tx(spec.legend.loop, locale)}</span>
        <span className="inline-flex items-center gap-1.5">{swatch("var(--dg-faint)")}{tx(spec.legend.estimate, locale)}</span>
      </p>
      <StepControls locale={locale} n={spec.frames.length} i={i} onChange={setI} text={i >= 0 ? tx(f.label, locale) : undefined} />
    </div>
  );
}
