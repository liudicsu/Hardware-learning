/**
 * Data model for the explanatory diagrams registered in src/lib/diagrams/index.ts.
 *
 * A diagram is plain data: nodes, edges and two hand-placed layouts (wide for >= 640 px,
 * narrow for phones, at most 360 units wide so it renders at roughly 1 unit = 1 px on a
 * 390 px screen). Nothing is computed in the browser; tools/check_diagrams.mjs validates
 * every spec (both languages present, Chinese labels in Chinese, geometry inside the
 * viewBox, labels fit their boxes) and checks each spec's facts against the lesson scripts.
 */

/** Text in both languages. A plain string is used unchanged in both (code identifiers, numbers). */
export type L10n = string | { zh: string; en: string };

export type Locale = "zh" | "en";

/** Colour roles; mapped to the --dg-* CSS variables in globals.css. */
export type Tone = "ink" | "muted" | "a" | "b" | "ok" | "danger";

export interface DiagramNode {
  id: string;
  label: L10n;
  /** Optional second line, drawn smaller. */
  sub?: L10n;
  /** box = process or component, state = state-machine state, text = bare label, file = tree entry. */
  shape?: "box" | "state" | "text" | "file";
  tone?: Tone;
  /** Draw the label in the monospace font (node names, topics, files). */
  mono?: boolean;
}

export interface DiagramEdge {
  id: string;
  label?: L10n;
  tone?: Tone;
  dashed?: boolean;
  mono?: boolean;
  /** Arrowhead at the last point (default true). */
  arrow?: boolean;
}

/** x, y, width, height of a node box. */
export type Rect = [number, number, number, number];
export type Point = [number, number];

export interface EdgeGeometry {
  /** Polyline from the first to the last point; the arrowhead sits at the last point. */
  pts: Point[];
  /** Where the label's text baseline starts (or is centred, see anchor). */
  label?: Point;
  anchor?: "start" | "middle" | "end";
}

export interface Layout {
  w: number;
  h: number;
  nodes: Record<string, Rect>;
  edges: Record<string, EdgeGeometry>;
}

export interface DiagramStep {
  label: L10n;
  /** Node and edge ids that stay bright in this step; everything else is dimmed. */
  highlight: string[];
}

/** A statement the check script verifies in a repository file (regular expression, multiline). */
export interface DiagramFact {
  file: string;
  pattern: string;
  note: string;
}

export interface BlockDiagramSpec {
  /** block = general block diagram; stateMachine = states with rounded shape and an initial-state marker. */
  kind: "block" | "stateMachine";
  id: string;
  title: L10n;
  caption?: L10n;
  /** Repository paths shown under the diagram as its sources. */
  sources: string[];
  nodes: DiagramNode[];
  edges: DiagramEdge[];
  layouts: { wide: Layout; narrow: Layout };
  steps?: DiagramStep[];
  /** stateMachine only: the state that receives the initial-state arrow. */
  initial?: string;
  facts: DiagramFact[];
}

/** A number drawn in a diagram, computed in the spec from its inputs and compared with the lesson. */
export interface DiagramNumber {
  note: string;
  value: number;
  expect: number;
  tol: number;
}

/* ---------- timing diagrams (rendered by <TimingSvg> from src/components/diagrams/Timing.tsx) ---------- */

export interface TimingSpecSignal {
  name: L10n;
  kind?: "digital" | "bus";
  /** digital: 1 / 0, "x" unknown, "z" released. */
  levels?: (number | "x" | "z")[];
  /** bus: one value per column. */
  values?: L10n[];
  tone?: Tone;
  /** Dashed line at this fraction of the trace height with a label at the right (e.g. PWM average voltage). */
  average?: { level: number; label: L10n };
}

export interface TimingSpecStep {
  label: L10n;
  /** Column to highlight. */
  column?: number;
  /** Signals drawn at full strength in this step (others dimmed). */
  signals?: number[];
}

export interface TimingSpec {
  kind: "timing";
  id: string;
  title: L10n;
  caption?: L10n;
  sources: string[];
  /** Relative column widths (e.g. durations); default equal. */
  columns?: number[];
  signals: TimingSpecSignal[];
  rows?: { name: L10n; cells: L10n[]; mono?: boolean }[];
  spans?: { from: number; to: number; label: L10n; side?: "top" | "bottom" }[];
  axisLabel?: L10n;
  steps?: TimingSpecStep[];
  numbers?: DiagramNumber[];
  facts: DiagramFact[];
}

export type DiagramSpec = BlockDiagramSpec | TimingSpec;

export function tx(text: L10n | undefined, locale: Locale): string {
  if (text === undefined) return "";
  return typeof text === "string" ? text : text[locale];
}
