/**
 * Generic digital timing diagram (SVG, dark theme). Pure presentational component with no hooks,
 * so it renders on the server and inside client wrappers such as <TimingStepper>.
 *
 * The time axis is split into columns (equal width by default, or proportional to `columns`).
 * Signals:
 *   - "digital" (default): one level per column, 1 / 0, or "x" (unknown) / "z" (released, high impedance).
 *   - "bus": one text value per column, drawn as a data band; equal neighbouring values merge
 *     (UART bytes, I²C address/data, register values). "" or "x" draws an unknown band.
 * Rows: one text cell per column under the traces (states, counts, bit values).
 * Spans: labelled brackets over a column range (pulse widths, periods, frame fields).
 * Intended uses: quadrature encoders, PWM, UART frames, I²C transactions, servo pulses.
 */

/** 0 = low, any other number = high, "x" = unknown, "z" = released / high impedance. */
export type Level = number | "x" | "z";

export interface TimingSignal {
  /** Label at the left of the trace, e.g. "A", "SCL", "PWM". */
  name: string;
  /** "digital" (default) or "bus". */
  kind?: "digital" | "bus";
  /** digital: one level per column (1, 0, "x" unknown, "z" released / high impedance). */
  levels?: Level[];
  /** bus: one value per column; equal neighbours merge into one band. */
  values?: string[];
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

export interface TimingSpan {
  /** First column (inclusive) and last column (inclusive) of the bracket. */
  from: number;
  to: number;
  label: string;
  /** Draw the bracket above the traces (default) or below the rows. */
  side?: "top" | "bottom";
}

export interface TimingProps {
  signals: TimingSignal[];
  rows?: TimingRow[];
  spans?: TimingSpan[];
  /** Relative column widths (e.g. durations in µs); default: all equal. */
  columns?: number[];
  /** Caption under the axis inside the SVG, e.g. "each column = 30° of motor-shaft rotation". */
  axisLabel?: string;
  /** Accessible name and the visible figure caption. */
  title: string;
  /** Column to highlight (used by <TimingStepper>). */
  highlight?: number;
  /** Value of the data-timing attribute, for tests and anchors. */
  id?: string;
}

const PALETTE = ["#38bdf8", "#f59e0b", "#a78bfa", "#34d399", "#f472b6"];
const LEFT = 64;
const COL = 48; // width of an average column, viewBox units
const TRACE_H = 30;
const TRACE_GAP = 22;
const ROW_H = 26;
const SPAN_H = 28;
const SLOPE = 5; // bus band edge slant
const MIN_SCALE = 0.62; // smallest px per viewBox unit before the diagram scrolls horizontally

export function columnCount(p: Pick<TimingProps, "signals" | "rows" | "columns">): number {
  const lens = [
    ...(p.columns ? [p.columns.length] : []),
    ...p.signals.map((s) => (s.kind === "bus" ? s.values?.length ?? 0 : s.levels?.length ?? 0)),
    ...(p.rows ?? []).map((r) => r.cells.length),
  ];
  return Math.max(1, ...lens);
}

/** x position of every column edge (n + 1 values), widths proportional to `columns`. */
export function columnEdges(n: number, columns?: number[]): number[] {
  const w = Array.from({ length: n }, (_, i) => Math.max(0, columns?.[i] ?? 1));
  const total = w.reduce((a, b) => a + b, 0) || n;
  const edges = [LEFT];
  for (let i = 0; i < n; i++) edges.push(edges[i] + (w[i] / total) * n * COL);
  return edges;
}

function digitalPath(levels: Level[], edges: number[], yTop: number) {
  const yHi = yTop;
  const yLo = yTop + TRACE_H;
  const yMid = yTop + TRACE_H / 2;
  const parts: { d: string; dashed: boolean }[] = [];
  let d = "";
  let prevY: number | null = null;
  levels.forEach((lv, i) => {
    const x0 = edges[i];
    const x1 = edges[i + 1];
    if (lv === "x") {
      if (d) parts.push({ d, dashed: false });
      d = "";
      prevY = null;
      parts.push({ d: `M${x0},${yHi}L${x1},${yHi}M${x0},${yLo}L${x1},${yLo}M${x0},${yHi}L${x1},${yLo}M${x0},${yLo}L${x1},${yHi}`, dashed: true });
      return;
    }
    const y = lv === "z" ? yMid : lv ? yHi : yLo;
    d += prevY === null ? `M${x0},${y}` : `L${x0},${y}`;
    d += `L${x1},${y}`;
    prevY = y;
  });
  if (d) parts.push({ d, dashed: false });
  return parts;
}

function busBands(values: string[], edges: number[]) {
  const bands: { from: number; to: number; value: string }[] = [];
  values.forEach((raw, i) => {
    const v = raw === "x" ? "" : raw; // both mean "unknown"; merge them
    const last = bands[bands.length - 1];
    if (last && last.value === v) last.to = i;
    else bands.push({ from: i, to: i, value: v });
  });
  return bands.map((b) => ({ ...b, x0: edges[b.from], x1: edges[b.to + 1] }));
}

export function TimingSvg({ signals, rows = [], spans = [], columns, axisLabel, title, highlight }: Omit<TimingProps, "id">) {
  const n = columnCount({ signals, rows, columns });
  const edges = columnEdges(n, columns);
  const width = edges[n] + 8;
  const topSpans = spans.filter((s) => (s.side ?? "top") === "top");
  const bottomSpans = spans.filter((s) => s.side === "bottom");
  const top = 10 + (topSpans.length ? SPAN_H : 0);
  const tracesBottom = top + signals.length * (TRACE_H + TRACE_GAP);
  const rowsBottom = tracesBottom + rows.length * ROW_H;
  const spansBottom = rowsBottom + (bottomSpans.length ? SPAN_H : 0);
  const height = spansBottom + (axisLabel ? 26 : 8);
  const clamp = (i: number) => Math.min(n - 1, Math.max(0, i));
  const bracket = (s: TimingSpan, y: number, down: boolean, k: number) => {
    const x0 = edges[clamp(s.from)];
    const x1 = edges[clamp(s.to) + 1];
    const tick = down ? 6 : -6;
    return (
      <g key={`span-${k}`}>
        <path d={`M${x0},${y + tick}L${x0},${y}L${x1},${y}L${x1},${y + tick}`} fill="none" stroke="#a1a1aa" strokeWidth={1.5} />
        <text x={(x0 + x1) / 2} y={down ? y - 5 : y + 17} fill="#d4d4d8" fontSize={14} textAnchor="middle">
          {s.label}
        </text>
      </g>
    );
  };
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      // keep text at >= ~10 px: long frames scroll inside their own box instead of shrinking
      style={{ minWidth: `${Math.round(width * MIN_SCALE)}px` }}
      role="img"
      aria-label={title}
    >
      {highlight !== undefined && highlight >= 0 && highlight < n && (
        <rect x={edges[highlight]} y={top - 6} width={edges[highlight + 1] - edges[highlight]} height={rowsBottom - top + 6} fill="#38bdf8" fillOpacity={0.12} rx={3} />
      )}
      {edges.map((x, i) => (
        <line key={i} x1={x} x2={x} y1={top - 4} y2={rowsBottom} stroke="#3f3f46" strokeDasharray="3 3" />
      ))}
      {topSpans.map((s, k) => bracket(s, top - 10, true, k))}
      {signals.map((s, k) => {
        const yTop = top + k * (TRACE_H + TRACE_GAP);
        const color = s.color ?? PALETTE[k % PALETTE.length];
        return (
          <g key={`${s.name}-${k}`}>
            <text x={8} y={yTop + TRACE_H / 2 + 6} fill={color} fontSize={18} fontWeight={600}>
              {s.name}
            </text>
            {s.kind === "bus"
              ? busBands(s.values ?? [], edges).map((b, j) => {
                  const yHi = yTop;
                  const yLo = yTop + TRACE_H;
                  const yMid = yTop + TRACE_H / 2;
                  const e = Math.min(SLOPE, (b.x1 - b.x0) / 4);
                  const unknown = b.value === "";
                  return (
                    <g key={j}>
                      <path
                        d={`M${b.x0},${yMid}L${b.x0 + e},${yHi}L${b.x1 - e},${yHi}L${b.x1},${yMid}L${b.x1 - e},${yLo}L${b.x0 + e},${yLo}Z`}
                        fill={unknown ? "#27272a" : color}
                        fillOpacity={unknown ? 1 : 0.14}
                        stroke={color}
                        strokeWidth={2}
                      />
                      {!unknown && (
                        <text x={(b.x0 + b.x1) / 2} y={yMid + 6} fill="#e4e4e7" fontSize={16} textAnchor="middle" fontFamily="ui-monospace, monospace">
                          {b.value}
                        </text>
                      )}
                    </g>
                  );
                })
              : digitalPath(s.levels ?? [], edges, yTop).map((p, j) => (
                  <path key={j} d={p.d} fill="none" stroke={color} strokeWidth={p.dashed ? 1.5 : 3} strokeDasharray={p.dashed ? "4 3" : undefined} strokeLinejoin="round" />
                ))}
          </g>
        );
      })}
      {rows.map((r, k) => {
        const y = tracesBottom + k * ROW_H + 18;
        const mono = r.mono ?? true;
        return (
          <g key={`${r.name}-${k}`}>
            <text x={8} y={y} fill="#a1a1aa" fontSize={15}>
              {r.name}
            </text>
            {r.cells.map((c, i) => (
              <text
                key={i}
                x={(edges[i] + edges[i + 1]) / 2}
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
      {bottomSpans.map((s, k) => bracket(s, rowsBottom + 6, false, k))}
      {axisLabel && (
        <text x={(edges[0] + edges[n]) / 2} y={height - 8} fill="#71717a" fontSize={14} textAnchor="middle">
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
      <div className="max-w-2xl overflow-x-auto">
        <TimingSvg title={title} {...rest} />
      </div>
      <figcaption className="mt-2 text-sm text-zinc-400">{title}</figcaption>
    </figure>
  );
}
