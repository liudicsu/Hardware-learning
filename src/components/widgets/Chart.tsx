"use client";

import { fixed } from "@/lib/models/format";
import { useBoxWidth } from "./useBoxWidth";

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
  /** Shaded horizontal band [from, to] in y units (e.g. a tolerance band). */
  band?: [number, number];
}

const W_MAX = 600;
const W_MIN = 280;
const FONT = 13; // viewBox units; one unit is one CSS px below W_MAX, so text never renders under 12 px
const LEFT = 52;
const RIGHT = 16;
const TOP = 14;
const BOTTOM = 40;

/** Label every m-th tick so that labels are at least `need` units apart (m = 1 labels them all). */
export function tickEvery(pitch: number, need: number): number {
  return Math.max(1, Math.ceil(need / pitch - 1e-9));
}
const labelWidth = (s: string) => s.length * 0.6 * FONT;

/**
 * Plain SVG line chart shared by the formula widgets (no chart library). The viewBox is as wide as the chart's
 * box (up to 600 units), so text keeps its size on a phone; on a narrow screen fewer ticks are labelled instead
 * of shrinking the font. Ticks are k * step and the labelled ones have k divisible by m, so 0 stays labelled.
 */
export function Chart(props: ChartProps) {
  const { series, xMin, xMax, yMin, yMax, xStep, yStep, xLabel, yLabel, ariaLabel } = props;
  const [box, boxW] = useBoxWidth<HTMLDivElement>();
  // Before the box is measured (server HTML, first paint, JS disabled) draw at W_MIN: the browser only scales it up, so on any box at least W_MIN wide the text is not drawn below FONT px.
  const W = boxW ? Math.max(W_MIN, Math.min(W_MAX, Math.round(boxW))) : W_MIN;
  const H = W < W_MAX ? 230 : 260;
  const PW = W - LEFT - RIGHT;
  const PH = H - TOP - BOTTOM;
  const x = (v: number) => LEFT + ((v - xMin) / (xMax - xMin)) * PW;
  const y = (v: number) => TOP + (1 - (Math.min(yMax, Math.max(yMin, v)) - yMin) / (yMax - yMin)) * PH;
  const xk: number[] = [];
  for (let k = Math.ceil(xMin / xStep - 1e-9); k * xStep <= xMax + 1e-9; k++) xk.push(k);
  const yk: number[] = [];
  for (let k = Math.ceil(yMin / yStep - 1e-9); k * yStep <= yMax + 1e-9; k++) yk.push(k);
  const xText = (v: number) => (props.xTickLabel ? props.xTickLabel(v) : fixed(v, props.xDigits ?? 1));
  const yText = (v: number) => fixed(v, props.yDigits ?? 0);
  // + 0 turns -0 into 0
  const xm = tickEvery((PW * xStep) / (xMax - xMin), Math.max(...xk.map((k) => labelWidth(xText(k * xStep + 0)))) + 10);
  const ym = tickEvery((PH * yStep) / (yMax - yMin), FONT + 6);
  const xt = xk.map((k) => ({ v: k * xStep + 0, label: k % xm === 0 }));
  const yt = yk.map((k) => ({ v: k * yStep + 0, label: k % ym === 0 }));
  return (
    <div ref={box} className="w-full" data-widget="chart">
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={ariaLabel} data-chart-ticks={`${xm},${ym}`}>
        {props.band && (
          <rect x={LEFT} y={y(props.band[1])} width={PW} height={Math.max(0, y(props.band[0]) - y(props.band[1]))} fill="rgba(56, 189, 248, 0.08)" />
        )}
        {yt.map(({ v, label }) => (
          <g key={`y${v}`}>
            <line x1={LEFT} y1={y(v)} x2={LEFT + PW} y2={y(v)} stroke="rgba(255,255,255,0.06)" />
            {label && (
              <text x={LEFT - 6} y={y(v) + 4} textAnchor="end" fontSize={FONT} fill="#71717a">
                {yText(v)}
              </text>
            )}
          </g>
        ))}
        {xt.map(({ v, label }) => (
          <g key={`x${v}`}>
            <line x1={x(v)} y1={TOP} x2={x(v)} y2={TOP + PH} stroke="rgba(255,255,255,0.06)" />
            {label && (
              <text x={x(v)} y={TOP + PH + 17} textAnchor="middle" fontSize={FONT} fill="#71717a">
                {xText(v)}
              </text>
            )}
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
        <text x={LEFT + PW / 2} y={H - 4} textAnchor="middle" fontSize={FONT} fill="#71717a">
          {xLabel}
        </text>
        <text x={12} y={TOP + PH / 2} textAnchor="middle" fontSize={FONT} fill="#71717a" transform={`rotate(-90 12 ${TOP + PH / 2})`}>
          {yLabel}
        </text>
      </svg>
    </div>
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
