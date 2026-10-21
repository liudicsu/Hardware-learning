"use client";

import { fixed } from "@/lib/models/format";

export interface Series {
  points: [number, number][];
  color: string;
  dashed?: boolean;
}

export interface ChartProps {
  series: Series[];
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  xStep: number;
  yStep: number;
  xLabel: string;
  yLabel: string;
  ariaLabel: string;
  xDigits?: number;
  yDigits?: number;
  /** Horizontal reference lines (dashed grey). */
  hLines?: number[];
  /** Map x before plotting (e.g. Math.log10 for a log axis); ticks are given in mapped units. */
  xTickLabel?: (tick: number) => string;
}

const W = 600;
const H = 260;
const LEFT = 52;
const RIGHT = 16;
const TOP = 14;
const BOTTOM = 40;
const PW = W - LEFT - RIGHT;
const PH = H - TOP - BOTTOM;

/** Plain SVG line chart shared by the formula widgets (no chart library). */
export function Chart(props: ChartProps) {
  const { series, xMin, xMax, yMin, yMax, xStep, yStep, xLabel, yLabel, ariaLabel } = props;
  const x = (v: number) => LEFT + ((v - xMin) / (xMax - xMin)) * PW;
  const y = (v: number) => TOP + (1 - (Math.min(yMax, Math.max(yMin, v)) - yMin) / (yMax - yMin)) * PH;
  const xt: number[] = [];
  for (let k = Math.ceil(xMin / xStep - 1e-9); k * xStep <= xMax + 1e-9; k++) xt.push(k * xStep);
  const yt: number[] = [];
  for (let k = Math.ceil(yMin / yStep - 1e-9); k * yStep <= yMax + 1e-9; k++) yt.push(k * yStep);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={ariaLabel}>
      {yt.map((v) => (
        <g key={`y${v}`}>
          <line x1={LEFT} y1={y(v)} x2={LEFT + PW} y2={y(v)} stroke="rgba(255,255,255,0.06)" />
          <text x={LEFT - 6} y={y(v) + 4} textAnchor="end" fontSize="13" fill="#71717a">
            {fixed(v, props.yDigits ?? 0)}
          </text>
        </g>
      ))}
      {xt.map((v) => (
        <g key={`x${v}`}>
          <line x1={x(v)} y1={TOP} x2={x(v)} y2={TOP + PH} stroke="rgba(255,255,255,0.06)" />
          <text x={x(v)} y={TOP + PH + 17} textAnchor="middle" fontSize="13" fill="#71717a">
            {props.xTickLabel ? props.xTickLabel(v) : fixed(v, props.xDigits ?? 1)}
          </text>
        </g>
      ))}
      <line x1={LEFT} y1={TOP + PH} x2={LEFT + PW} y2={TOP + PH} stroke="#52525b" />
      <line x1={LEFT} y1={TOP} x2={LEFT} y2={TOP + PH} stroke="#52525b" />
      {(props.hLines ?? []).map((v) => (
        <line key={`h${v}`} x1={LEFT} y1={y(v)} x2={LEFT + PW} y2={y(v)} stroke="#a1a1aa" strokeDasharray="5 4" />
      ))}
      {series.map((s, i) => (
        <polyline
          key={i}
          points={s.points.map(([a, b]) => `${x(a).toFixed(2)},${y(b).toFixed(2)}`).join(" ")}
          fill="none"
          stroke={s.color}
          strokeWidth="2"
          strokeDasharray={s.dashed ? "6 4" : undefined}
        />
      ))}
      <text x={LEFT + PW / 2} y={H - 4} textAnchor="middle" fontSize="13" fill="#71717a">
        {xLabel}
      </text>
      <text
        x={12}
        y={TOP + PH / 2}
        textAnchor="middle"
        fontSize="13"
        fill="#71717a"
        transform={`rotate(-90 12 ${TOP + PH / 2})`}
      >
        {yLabel}
      </text>
    </svg>
  );
}

export function Readout({ label, value, testId }: { label: string; value: string; testId: string }) {
  return (
    <p className="text-zinc-400">
      {label}{" "}
      <span data-testid={testId} className="font-mono text-zinc-100">
        {value}
      </span>
    </p>
  );
}
