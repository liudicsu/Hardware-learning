import type { Locale } from "@/lib/diagrams/types";
import { TimingStepper } from "./TimingStepper";
import { diagramColumns, OFFSET_DEG, POLES } from "@/lib/models/encoder";

export interface QuadratureTimingProps {
  direction: "forward" | "reverse";
  title: string;
  countLabel: string;
  stateLabel: string;
  axisLabel: string;
  /** Supplied by the lesson page. */
  locale: Locale;
}

/** viewBox units per column of <QuadratureTiming> (8 columns). */
export const QUAD_COL = 39;

/** Encoder A/B timing diagram with a stepper; columns come from src/lib/models/encoder.ts. */
export function QuadratureTiming({ direction, title, countLabel, stateLabel, axisLabel, locale }: QuadratureTimingProps) {
  const cols = diagramColumns(direction, 8);
  const sgn = (d: number) => (d > 0 ? `+${d}` : d < 0 ? `−${-d}` : "0"); // typographic minus, as in the text
  return (
    <TimingStepper
      id={`quadrature-${direction}`}
      title={title}
      // 64 + 8 × 39 + 8 = 384 units, so the 14-unit axis label renders at 14 × 332 / 384 ≈ 12.1 px in the
      // 332 px box of a 390 px phone (checked by tools/check_diagrams.mjs)
      columnScale={QUAD_COL}
      axisLabel={axisLabel}
      signals={[
        { name: "A", levels: cols.map((c) => c.a), color: "var(--dg-a)" },
        { name: "B", levels: cols.map((c) => c.b), color: "var(--dg-b)" },
      ]}
      rows={[
        { name: stateLabel, cells: cols.map((c) => c.ab) },
        { name: countLabel, cells: cols.map((c) => sgn(c.count)), mono: false },
      ]}
      stepText={cols.map((c, i) => {
        // full-width colon and comma in Chinese text, ASCII in English
        const [colon, comma] = locale === "zh" ? ["：", "，"] : [": ", ", "];
        return i === 0
          ? `AB ${c.ab}${comma}${countLabel} 0`
          : `AB ${cols[i - 1].ab} → ${c.ab}${colon}${sgn(c.delta)}${comma}${countLabel} ${sgn(c.count)}`;
      })}
      locale={locale}
    />
  );
}

export interface EncoderDiscProps {
  title: string;
  sensorA: string;
  sensorB: string;
}

/** The magnetic disc seen from the rear of the motor: 6 alternating poles, Hall sensors A and B a quarter period apart. */
export function EncoderDisc({ title, sensorA, sensorB }: EncoderDiscProps) {
  const cx = 110;
  const cy = 126;
  const r = 70;
  const pt = (deg: number, rad: number) => {
    const t = ((deg - 90) * Math.PI) / 180;
    return [cx + rad * Math.cos(t), cy + rad * Math.sin(t)];
  };
  const sectors = Array.from({ length: POLES }, (_, i) => {
    const a0 = i * (360 / POLES);
    const a1 = a0 + 360 / POLES;
    const [x0, y0] = pt(a0, r);
    const [x1, y1] = pt(a1, r);
    const [lx, ly] = pt(a0 + 180 / POLES, r * 0.62);
    return { d: `M${cx},${cy} L${x0},${y0} A${r},${r} 0 0 1 ${x1},${y1} Z`, north: i % 2 === 0, lx, ly };
  });
  const sensor = (deg: number, label: string, color: string) => {
    const [x, y] = pt(deg, r + 14);
    const [tx, ty] = pt(deg, r + 34);
    return (
      <g>
        <rect x={x - 7} y={y - 7} width={14} height={14} fill={color} transform={`rotate(${deg} ${x} ${y})`} />
        <text x={tx} y={ty + 5} fill={color} fontSize={15} fontWeight={600} textAnchor="middle">{label}</text>
      </g>
    );
  };
  return (
    <figure className="not-prose my-6 max-w-full overflow-hidden rounded-xl border border-zinc-800 bg-[var(--dg-card)] px-3 py-3 sm:px-4">
      <svg viewBox="0 0 220 250" className="mx-auto w-full max-w-[16rem]" role="img" aria-label={title}>
        {sectors.map((s, i) => (
          <g key={i}>
            <path d={s.d} fill={s.north ? "#7f1d1d" : "#1e3a8a"} style={{ stroke: "var(--dg-card)" }} />
            <text x={s.lx} y={s.ly + 5} style={{ fill: "var(--dg-ink)" }} fontSize={15} textAnchor="middle">{s.north ? "N" : "S"}</text>
          </g>
        ))}
        <circle cx={cx} cy={cy} r={8} style={{ fill: "var(--dg-muted)" }} />
        {sensor(0, sensorA, "var(--dg-a)")}
        {sensor(OFFSET_DEG, sensorB, "var(--dg-b)")}
      </svg>
      <figcaption className="mt-2 text-center text-sm text-zinc-400">{title}</figcaption>
    </figure>
  );
}
