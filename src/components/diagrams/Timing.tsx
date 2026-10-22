/**
 * Generic digital timing diagram (SVG, dark theme). Pure presentational component with no hooks,
 * so it renders on the server and inside client wrappers such as <TimingStepper>.
 *
 * The time axis is split into equal columns. Each signal gives one logic level per column; each
 * row gives one text label per column (e.g. a bus state, a count, a bit value). Reusable for
 * quadrature encoders, PWM, UART frames, I²C, servo pulses and similar diagrams.
 */

export interface TimingSignal {
  /** Label at the left of the trace, e.g. "A", "SCL", "PWM". */
  name: string;
  /** Logic level per column: 1 = high, 0 = low. */
  levels: number[];
  /** Stroke colour; defaults cycle through a dark-theme palette. */
  color?: string;
}

export interface TimingRow {
  /** Label at the left of the row, e.g. "AB", "count". */
  name: string;
  /** One text cell per column. */
  cells: string[];
  /** Render cells in the monospace font and brighter (default true). */
  mono?: boolean;
}

export interface TimingProps {
  signals: TimingSignal[];
  rows?: TimingRow[];
  /** Caption under the axis inside the SVG, e.g. "each column = 30° of motor-shaft rotation". */
  axisLabel?: string;
  /** Accessible name and the visible figure caption. */
  title: string;
  /** Column to highlight (used by <TimingStepper>). */
  highlight?: number;
  /** Optional data attribute value for tests, rendered as data-timing. */
  id?: string;
}

const PALETTE = ["#38bdf8", "#f59e0b", "#a78bfa", "#34d399", "#f472b6"];
const LEFT = 64;
const COL_MIN = 48;
const TRACE_H = 30;
const TRACE_GAP = 22;
const ROW_H = 26;

export function timingWidth(columns: number) {
  return LEFT + columns * COL_MIN + 8;
}

export function TimingSvg({ signals, rows = [], axisLabel, title, highlight }: Omit<TimingProps, "id">) {
  const n = Math.max(...signals.map((s) => s.levels.length), ...rows.map((r) => r.cells.length));
  const w = COL_MIN;
  const width = timingWidth(n);
  const tracesBottom = 10 + signals.length * (TRACE_H + TRACE_GAP);
  const rowsBottom = tracesBottom + rows.length * ROW_H;
  const height = rowsBottom + (axisLabel ? 26 : 8);
  const path = (levels: number[], yTop: number) => {
    const yLo = yTop + TRACE_H;
    return levels
      .map((lv, i) => {
        const y = lv ? yTop : yLo;
        const x = LEFT + i * w;
        return `${i === 0 ? "M" : "L"}${x},${y}L${x + w},${y}`;
      })
      .join("");
  };
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label={title}>
      {highlight !== undefined && highlight >= 0 && highlight < n && (
        <rect x={LEFT + highlight * w} y={4} width={w} height={rowsBottom - 4} fill="#38bdf8" fillOpacity={0.12} rx={3} />
      )}
      {Array.from({ length: n + 1 }, (_, i) => (
        <line key={i} x1={LEFT + i * w} x2={LEFT + i * w} y1={6} y2={rowsBottom} stroke="#3f3f46" strokeDasharray="3 3" />
      ))}
      {signals.map((s, k) => {
        const yTop = 10 + k * (TRACE_H + TRACE_GAP);
        const color = s.color ?? PALETTE[k % PALETTE.length];
        return (
          <g key={s.name}>
            <text x={8} y={yTop + TRACE_H / 2 + 6} fill={color} fontSize={18} fontWeight={600}>
              {s.name}
            </text>
            <path d={path(s.levels, yTop)} fill="none" stroke={color} strokeWidth={3} strokeLinejoin="round" />
          </g>
        );
      })}
      {rows.map((r, k) => {
        const y = tracesBottom + k * ROW_H + 18;
        const mono = r.mono ?? true;
        return (
          <g key={r.name}>
            <text x={8} y={y} fill="#a1a1aa" fontSize={15}>
              {r.name}
            </text>
            {r.cells.map((c, i) => (
              <text
                key={i}
                x={LEFT + i * w + w / 2}
                y={y}
                fill={mono ? "#e4e4e7" : "#a1a1aa"}
                fontSize={17}
                textAnchor="middle"
                fontFamily={mono ? "ui-monospace, monospace" : undefined}
              >
                {c}
              </text>
            ))}
          </g>
        );
      })}
      {axisLabel && (
        <text x={LEFT + (n * w) / 2} y={height - 8} fill="#71717a" fontSize={14} textAnchor="middle">
          {axisLabel}
        </text>
      )}
    </svg>
  );
}

/** Static timing diagram with a caption. */
export function Timing({ id, title, ...rest }: TimingProps) {
  return (
    <figure className="not-prose my-6" data-timing={id ?? ""}>
      <div className="max-w-2xl">
        <TimingSvg title={title} {...rest} />
      </div>
      <figcaption className="mt-2 text-sm text-zinc-400">{title}</figcaption>
    </figure>
  );
}
