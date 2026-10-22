import { useId } from "react";
import { tx, type BlockDiagramSpec, type Layout, type Locale, type Tone } from "@/lib/diagrams/types";

export const TONE: Record<Tone, string> = {
  ink: "var(--dg-ink)",
  muted: "var(--dg-muted)",
  a: "var(--dg-a)",
  b: "var(--dg-b)",
  c: "var(--dg-c)",
  ok: "var(--dg-ok)",
  danger: "var(--dg-danger)",
};

export const DG_FONT = 12.3;
export const DG_SUB_FONT = 12.3;
export const MONO = "var(--font-mono)";

export interface BlockDiagramSvgProps {
  spec: BlockDiagramSpec;
  layout: Layout;
  locale: Locale;
  /** Ids that stay bright; undefined = everything bright. */
  highlight?: string[];
  className?: string;
}

/** One layout of a block diagram or state machine as a responsive SVG (width 100 %, no fixed pixel size). */
export function BlockDiagramSvg({ spec, layout, locale, highlight, className }: BlockDiagramSvgProps) {
  const uid = useId().replace(/:/g, "");
  const dim = (id: string) => (highlight && !highlight.includes(id) ? 0.18 : 1);
  const title = tx(spec.title, locale);
  const marker = (tone: Tone) => `dg-arrow-${uid}-${tone}`;
  const tones = Array.from(new Set(spec.edges.map((e) => e.tone ?? "muted")));
  return (
    <svg
      viewBox={`0 0 ${layout.w} ${layout.h}`}
      width="100%"
      role="img"
      aria-label={title}
      className={className}
      style={{ maxWidth: layout.w * 1.25, height: "auto" }}
    >
      <title>{title}</title>
      <defs>
        {tones.map((t) => (
          <marker key={t} id={marker(t)} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" style={{ fill: TONE[t] }} />
          </marker>
        ))}
      </defs>
      {spec.edges.map((e) => {
        const g = layout.edges[e.id];
        if (!g) return null;
        const tone = e.tone ?? "muted";
        const label = tx(e.label, locale);
        return (
          <g key={e.id} opacity={dim(e.id)} data-edge={e.id}>
            <polyline
              points={g.pts.map((p) => p.join(",")).join(" ")}
              style={{ fill: "none", stroke: TONE[tone], strokeWidth: 1.5, strokeDasharray: e.dashed ? "5 4" : undefined }}
              markerEnd={e.arrow === false ? undefined : `url(#${marker(tone)})`}
            />
            {label && g.label && (
              <text
                x={g.label[0]}
                y={g.label[1]}
                textAnchor={g.anchor ?? "middle"}
                style={{ fill: TONE[tone], fontSize: DG_SUB_FONT, fontFamily: e.mono ? MONO : undefined }}
              >
                {label.split("\n").map((line, k) => (
                  <tspan key={k} x={g.label![0]} dy={k === 0 ? 0 : DG_SUB_FONT + 2.5}>
                    {line}
                  </tspan>
                ))}
              </text>
            )}
          </g>
        );
      })}
      {spec.kind === "stateMachine" && spec.initial && layout.nodes[spec.initial] && (() => {
        const [x, y, , h] = layout.nodes[spec.initial];
        return (
          <g opacity={dim(spec.initial)}>
            <circle cx={x - 22} cy={y + h / 2} r={4} style={{ fill: TONE.ink }} />
            <line x1={x - 18} y1={y + h / 2} x2={x - 2} y2={y + h / 2} style={{ stroke: TONE.ink, strokeWidth: 1.5 }} markerEnd={`url(#${marker("muted")})`} />
          </g>
        );
      })()}
      {spec.nodes.map((n) => {
        const r = layout.nodes[n.id];
        if (!r) return null;
        const [x, y, w, h] = r;
        const tone = n.tone ?? "ink";
        const shape = n.shape ?? (spec.kind === "stateMachine" ? "state" : "box");
        const label = tx(n.label, locale);
        const sub = tx(n.sub, locale);
        const cx = shape === "file" ? x + 4 : x + w / 2;
        const anchor = shape === "file" ? "start" : "middle";
        const subLines = sub ? sub.split("\n") : [];
        // label + sub lines are centred as a block; each extra sub line moves the block up by half a line
        const ly = sub ? y + h / 2 - 2 - ((subLines.length - 1) * (DG_SUB_FONT + 2.5)) / 2 : y + h / 2 + DG_FONT * 0.36;
        return (
          <g key={n.id} opacity={dim(n.id)} data-node={n.id}>
            {(shape === "box" || shape === "state") && (
              <rect
                x={x}
                y={y}
                width={w}
                height={h}
                rx={shape === "state" ? h / 2 : 6}
                style={{ fill: "var(--dg-card)", stroke: TONE[tone], strokeWidth: 1.5 }}
              />
            )}
            <text x={cx} y={ly} textAnchor={anchor} style={{ fill: TONE[tone], fontSize: DG_FONT, fontFamily: n.mono ? MONO : undefined, fontWeight: 600 }}>
              {label}
            </text>
            {sub && (
              <text x={cx} y={ly + DG_SUB_FONT + 3} textAnchor={anchor} style={{ fill: TONE.muted, fontSize: DG_SUB_FONT }}>
                {subLines.map((line, k) => (
                  <tspan key={k} x={cx} dy={k === 0 ? 0 : DG_SUB_FONT + 2.5}>
                    {line}
                  </tspan>
                ))}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
