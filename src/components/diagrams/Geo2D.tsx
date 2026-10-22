import { tx, type GeoShape, type GeoSpec, type Locale } from "@/lib/diagrams/types";
import { MONO, TONE } from "./BlockDiagram";

// viewBox units (read by tools/check_diagrams.mjs). At most 340 units wide, so 13-unit text is >= 12 px at 390 px.
export const GEO_FONT = 13;
export const GEO_MAX_SCALE = 1.3; // px per unit on wide screens

/** Point at `deg` degrees clockwise from straight up, `r` units from `c`. */
export function geoPolar(c: [number, number], r: number, deg: number): [number, number] {
  const t = (deg * Math.PI) / 180;
  return [c[0] + r * Math.sin(t), c[1] - r * Math.cos(t)];
}

function arrowHead(tip: [number, number], from: [number, number], colour: string, k: string) {
  const a = Math.atan2(tip[1] - from[1], tip[0] - from[0]);
  const p = (d: number) => `${(tip[0] - 9 * Math.cos(a + d)).toFixed(1)},${(tip[1] - 9 * Math.sin(a + d)).toFixed(1)}`;
  return <polygon key={k} points={`${tip[0].toFixed(1)},${tip[1].toFixed(1)} ${p(0.45)} ${p(-0.45)}`} style={{ fill: colour }} />;
}

function shape(s: GeoShape, k: number, locale: Locale) {
  const c = TONE[s.tone ?? "ink"];
  switch (s.type) {
    case "polyline":
      return (
        <polyline
          key={k}
          points={s.pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ")}
          fill="none"
          style={{ stroke: c }}
          strokeWidth={s.width ?? 2}
          strokeLinejoin="round"
          strokeDasharray={s.dashed ? "5 4" : undefined}
        />
      );
    case "line":
      return (
        <g key={k}>
          <line x1={s.from[0]} y1={s.from[1]} x2={s.to[0]} y2={s.to[1]} style={{ stroke: c }} strokeWidth={s.width ?? 2} strokeDasharray={s.dashed ? "5 4" : undefined} />
          {s.arrow && arrowHead(s.to, s.from, c, "h")}
        </g>
      );
    case "rect":
      return <rect key={k} x={s.at[0]} y={s.at[1]} width={s.size[0]} height={s.size[1]} rx={s.rx ?? 4} style={{ stroke: c, fill: "var(--dg-card)" }} strokeWidth={2} />;
    case "circle":
      return <circle key={k} cx={s.at[0]} cy={s.at[1]} r={s.r} style={{ stroke: c, fill: s.fill ? c : s.dashed ? "none" : "var(--dg-card)" }} strokeWidth={2} strokeDasharray={s.dashed ? "4 3" : undefined} />;
    case "arc": {
      const p0 = geoPolar(s.at, s.r, s.from);
      const p1 = geoPolar(s.at, s.r, s.to);
      const sweep = s.to > s.from ? 1 : 0;
      const large = Math.abs(s.to - s.from) > 180 ? 1 : 0;
      const before = geoPolar(s.at, s.r, s.to - Math.sign(s.to - s.from) * 8);
      return (
        <g key={k}>
          <path d={`M${p0[0].toFixed(1)},${p0[1].toFixed(1)}A${s.r},${s.r} 0 ${large} ${sweep} ${p1[0].toFixed(1)},${p1[1].toFixed(1)}`} fill="none" style={{ stroke: c }} strokeWidth={2} />
          {s.arrow && arrowHead(p1, before, c, "h")}
        </g>
      );
    }
    case "text":
      return (
        <text key={k} x={s.at[0]} y={s.at[1]} textAnchor={s.anchor ?? "middle"} fontWeight={s.bold ? 600 : undefined} style={{ fill: c, fontSize: GEO_FONT, fontFamily: s.mono ? MONO : undefined }}>
          {tx(s.label, locale)}
        </text>
      );
  }
}

/**
 * Figure drawn from the spec's shapes (cart-pole sign convention, BC corridor). With `highlight`, shapes whose id or
 * group is not listed are dimmed; shapes with neither id nor group always stay bright.
 */
export function Geo2D({ spec, locale, highlight }: { spec: GeoSpec; locale: Locale; highlight?: string[] }) {
  const dim = (s: GeoShape) =>
    highlight && (s.id !== undefined || s.group !== undefined) && !highlight.includes(s.id ?? "") && !highlight.includes(s.group ?? "") ? 0.15 : 1;
  return (
    <svg viewBox={`0 0 ${spec.w} ${spec.h}`} width="100%" role="img" aria-label={tx(spec.title, locale)} className="mx-auto block" style={{ maxWidth: spec.w * GEO_MAX_SCALE, height: "auto" }}>
      {spec.shapes.map((s, k) => (
        <g key={k} opacity={dim(s)}>
          {shape(s, k, locale)}
        </g>
      ))}
    </svg>
  );
}
