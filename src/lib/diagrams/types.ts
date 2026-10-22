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
export type Tone = "ink" | "muted" | "a" | "b" | "c" | "ok" | "danger";

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
  /** check_diagrams runs `python3 <run>` and requires every line in `lines` to appear in its output. */
  script?: { run: string; lines: string[] };
  /** Ties drawn text and edge styles to the constants the facts use (see BlockBinding). */
  bindings?: BlockBinding[];
  facts: DiagramFact[];
}

/**
 * A node (label + sub), a step (1-based) or the caption whose text must match every regular expression in `has` and
 * none in `lacks` (per language when given as L10n), or an edge that must be dashed (or solid).
 */
export type BlockBinding =
  | { node: string; has?: L10n[]; lacks?: L10n[]; note: string; edge?: undefined; step?: undefined; caption?: undefined }
  | { step: number; has?: L10n[]; lacks?: L10n[]; note: string; node?: undefined; edge?: undefined; caption?: undefined }
  | { caption: true; has?: L10n[]; lacks?: L10n[]; note: string; node?: undefined; edge?: undefined; step?: undefined }
  | { edge: string; dashed: boolean; note: string; node?: undefined; step?: undefined; caption?: undefined };

/* ---------- circuit (current path) diagrams ---------- */

/**
 * Two-terminal parts (switch, button, resistor, motor) sit at `at`, run along `dir` and have their
 * terminals at at ± len/2. A switch or button conducts only in the states that list it in `closed`.
 */
export type CircuitPartType = "switch" | "button" | "resistor" | "motor" | "supply" | "ground" | "node" | "box" | "text";

export interface CircuitPart {
  id: string;
  type: CircuitPartType;
  at: Point;
  dir?: "v" | "h";
  /** Terminal-to-terminal length of a two-terminal part (default 36). */
  len?: number;
  /** box only: width and height, with `at` as the top-left corner. */
  size?: [number, number];
  label?: L10n;
  labelAt?: Point;
  anchor?: "start" | "middle" | "end";
  mono?: boolean;
  tone?: Tone;
}

export interface CircuitWire {
  id: string;
  pts: Point[];
}

export interface CircuitState {
  id: string;
  /** Short name on the state button. */
  label: L10n;
  /** One or two sentences shown under the diagram for this state. */
  text: L10n;
  /** Switch and button ids that are closed (all others are open). */
  closed: string[];
  /** Parts and wires not drawn in this state (e.g. a resistor that is not fitted). */
  hidden?: string[];
  /** Conventional current, drawn along these points; check_diagrams verifies it only runs over wires and conducting parts. */
  flow?: Point[];
  /**
   * A path normally starts at a supply and ends at a ground. A current that only circulates in a closed loop
   * (e.g. an H-bridge brake) sets this to the reason; the path must then be closed and must not touch a supply.
   */
  loopReason?: string;
  tone?: Tone;
  /** Short reading drawn at the spec's readoutAt (current, pin level). */
  readout?: L10n;
}

/** A number drawn in a diagram, computed in the spec from the circuit values and compared with the lesson. */
export interface DiagramNumber {
  note: string;
  value: number;
  expect: number;
  tol: number;
}

export interface CircuitSpec {
  kind: "circuit";
  id: string;
  title: L10n;
  caption?: L10n;
  sources: string[];
  /** One layout for every screen width; at most 360 units wide so it reads at 390 px. */
  w: number;
  h: number;
  parts: CircuitPart[];
  wires: CircuitWire[];
  states: CircuitState[];
  readoutAt?: Point;
  numbers?: DiagramNumber[];
  facts: DiagramFact[];
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
  /** viewBox units per unit of `columns` (one time scale for every line); default: 48 units per column. */
  columnScale?: number;
  /**
   * Column ranges [first, last] (inclusive), each drawn as its own line, one under the other, at one
   * common scale. Must cover every column in order. Default: one line with all columns.
   */
  lines?: [number, number][];
  /** Lines used below 640 px instead of `lines`; may leave columns out (e.g. show one PWM period). */
  narrowLines?: [number, number][];
  signals: TimingSpecSignal[];
  rows?: { name: L10n; cells: L10n[]; mono?: boolean }[];
  spans?: { from: number; to: number; label: L10n; side?: "top" | "bottom" }[];
  axisLabel?: L10n;
  steps?: TimingSpecStep[];
  numbers?: DiagramNumber[];
  facts: DiagramFact[];
}

export interface BytesSpecByte {
  /** Byte value 0..255. */
  v: number;
  /** Key into BytesSpec.fields (colour and field name). */
  field: string;
  /** What this byte means in this packet, e.g. "ID = 1". */
  note: L10n;
  /** Drawn in the danger colour (e.g. a corrupted byte). */
  bad?: boolean;
}

export interface BytesSpecPacket {
  id: string;
  /** Button label. */
  label: L10n;
  bytes: BytesSpecByte[];
  /** Brackets over (top) or under (bottom) a byte range, e.g. "00 08 → 0x0800 = 2048". */
  groups?: { from: number; to: number; label: L10n; side?: "top" | "bottom" }[];
  /** One or two sentences under the table. */
  summary: L10n;
}

/** A row of bytes coloured by field, with a per-byte table; one packet per button. */
export interface BytesSpec {
  kind: "bytes";
  id: string;
  title: L10n;
  caption?: L10n;
  sources: string[];
  fields: Record<string, { label: L10n; tone: Tone }>;
  packets: BytesSpecPacket[];
  /** check_diagrams runs `python3 <run>` and requires every line in `lines` to appear in its output. */
  script?: { run: string; lines: string[] };
  numbers?: DiagramNumber[];
  facts: DiagramFact[];
}

/* ---------- pose graphs (rendered by src/components/diagrams/PoseGraph.tsx) ---------- */

/** A pose in metres and radians (x forward at the start, y to the left). */
export interface PoseGraphPose {
  x: number;
  y: number;
  th: number;
}

export interface PoseGraphFrame {
  label: L10n;
  /** Number of graph nodes shown (nodes 0 .. upto - 1). */
  upto: number;
  /** Mark the spacing between nodes 0 and 1 with the travel thresholds. */
  spacing?: boolean;
  /** Draw the scan-match edges from this node to the previous `matchWindow` nodes. */
  match?: number;
  /** Mark the gap between the newest node's estimate and its true place next to node 0. */
  gap?: boolean;
  /** Draw the loop-closure edge and the corrected graph (the estimate stays faint behind it). */
  loop?: boolean;
}

/** One lidar scan: its time and the robot's pose by odometry and in truth. */
export interface PoseGraphScan {
  t: number;
  odom: PoseGraphPose;
  truth: PoseGraphPose;
}

export interface PoseGraphSpec {
  kind: "poseGraph";
  id: string;
  title: L10n;
  caption?: L10n;
  sources: string[];
  /** Every scan the lidar delivers along the route. */
  scans: PoseGraphScan[];
  /** Indices of the scans that became graph nodes. */
  nodes: number[];
  /** Where each node was stored, as odometry estimated it (= scans[nodes[i]].odom). */
  estimate: PoseGraphPose[];
  /** The same nodes after the loop closure. */
  corrected: PoseGraphPose[];
  /** Where each node really was (= scans[nodes[i]].truth). */
  truth: PoseGraphPose[];
  /**
   * The values the node rule uses; check_diagrams compares each with its source (slam.yaml, the URDF, the
   * Gazebo sensor, tour.py, SLAM Toolbox 2.8.5 defaults) and re-runs the rule on `scans`.
   */
  model: {
    /** minimum_travel_distance (m) and minimum_travel_heading (rad), slam.yaml. */
    distance: number;
    heading: number;
    /** shouldProcessScan drops a scan when dist^2 < factor * distance^2. */
    factor: number;
    /** minimum_time_interval (s), SLAM Toolbox default. */
    minInterval: number;
    /** lidar_link ahead of base_footprint (m), URDF. */
    lidarX: number;
    /** lidar rate (Hz), drive speed (m/s) and turn rate (rad/s). */
    rate: number;
    speed: number;
    turnRate: number;
  };
  matchWindow: number;
  /** SVG text drawn on the graph. */
  text: { start: L10n; spacing: L10n; gap: L10n };
  /** HTML legend under the graph. */
  legend: { odom: L10n; match: L10n; loop: L10n; estimate: L10n };
  frames: PoseGraphFrame[];
  numbers?: DiagramNumber[];
  facts: DiagramFact[];
}

/* ---------- 2-D geometry figures (rendered by src/components/diagrams/Geo2D.tsx) ---------- */

/** Angles in degrees measured from straight up, clockwise on screen positive. */
/** `group` names shapes that a step highlights together; shapes with neither id nor group are never dimmed. */
export type GeoShape = (
  | { type: "line"; from: Point; to: Point; tone?: Tone; width?: number; dashed?: boolean; arrow?: boolean }
  | { type: "polyline"; pts: Point[]; tone?: Tone; width?: number; dashed?: boolean }
  | { type: "rect"; at: Point; size: [number, number]; tone?: Tone; rx?: number }
  | { type: "circle"; at: Point; r: number; tone?: Tone; fill?: boolean; dashed?: boolean }
  | { type: "arc"; at: Point; r: number; from: number; to: number; tone?: Tone; arrow?: boolean }
  | { type: "text"; at: Point; label: L10n; anchor?: "start" | "middle" | "end"; tone?: Tone; mono?: boolean; bold?: boolean }
) & { id?: string; group?: string };

/**
 * A static figure drawn from shapes in one viewBox of at most 340 units (one layout for every width).
 * `cartPole` names the shapes that carry the cart-pole sign convention; check_diagrams compares their
 * directions with the model in tools/sim/models/lqr_sim.py.
 */
export interface GeoSpec {
  kind: "geo";
  id: string;
  title: L10n;
  caption?: L10n;
  sources: string[];
  w: number;
  h: number;
  shapes: GeoShape[];
  cartPole?: {
    axis: string;
    force: string;
    pivot: Point;
    pole: string;
    theta: string;
    /** Text shapes that name the positive directions ("+x", "+F", "+θ"); checked to sit at their shapes. */
    labels: { axis: string; force: string; theta: string };
  };
  /**
   * The behaviour-cloning corridor (bc_reach.py): shapes drawn in metres through `map` (viewBox x = x0 + s * x,
   * y = y0 - s * y). check_diagrams rebuilds the walls from the corridor constants and checks both runs against them.
   */
  corridor?: {
    map: { x0: number; y0: number; s: number };
    corner: Point;
    goal: Point;
    halfWidth: number;
    goalRadius: number;
    walls: string;
    success: string;
    fail: string;
  };
  /** Optional steps: each highlights shape ids or groups and dims the others (shapes without id/group stay). */
  steps?: DiagramStep[];
  numbers?: DiagramNumber[];
  facts: DiagramFact[];
}

export type DiagramSpec = BlockDiagramSpec | CircuitSpec | TimingSpec | BytesSpec | PoseGraphSpec | GeoSpec;

export function tx(text: L10n | undefined, locale: Locale): string {
  if (text === undefined) return "";
  return typeof text === "string" ? text : text[locale];
}
