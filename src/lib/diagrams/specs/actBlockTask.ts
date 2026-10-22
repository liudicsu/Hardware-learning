import type { GeoShape, GeoSpec, Point } from "../types";
import d from "../data/act-fork.json";

/*
 * m6/act-diffusion "The block task" (D115): multimodal.py's block task to scale, and the one decision the lesson's
 * first table looks at. data/act-fork.json is written by tools/sim/models/act_fork_export.py, which imports
 * multimodal.py: its 40 demos (Random(5)), the 10 recorded frames nearest (0, 0.23) with their actions, and their
 * mean (average_policy's action there). check_diagrams re-runs the exporter, rebuilds the block, goal, fork and
 * waypoints from multimodal.py's constants, and checks that the drawn mean is the mean of the drawn demo actions and
 * that its ray meets the block's near face.
 */

const MM = "examples/month-6/act-diffusion/multimodal.py";
const OUT = "examples/month-6/expected/multimodal.txt";
const EN = "src/content/m6/act-diffusion/en.mdx";
const ZH = "src/content/m6/act-diffusion/zh.mdx";

const MAP = { x0: 170, y0: 296, s: 260 };
const r1 = (v: number) => Math.round(v * 10) / 10;
const P = (q: number[]): Point => [r1(MAP.x0 + MAP.s * q[0]), r1(MAP.y0 - MAP.s * q[1])];
const ARROW = 3; // actions (at most 5 cm) drawn 3x longer
const WAY = 0.3, WAY_Y = 0.4; // multimodal.expert's waypoints (±0.3, 0.4)

const [gx, gy] = d.goal, half = d.half, by = d.block_y;
const at = P(d.at);
const tipOf = (p: number[], a: number[]): Point => P([p[0] + ARROW * a[0], p[1] + ARROW * a[1]]);
const left = d.near.filter((n) => n.a[0] < 0), right = d.near.filter((n) => n.a[0] > 0);
const sideCm = (ns: typeof d.near) => ns.map((n) => Math.abs(n.a[0]) * 100);
const allSide = sideCm(d.near);
const lo = Math.min(...allSide).toFixed(1), hi = Math.max(...allSide).toFixed(1);
const meanCm = (d.mean[0] * 100).toFixed(1).replace("-", "−");
// the mean's ray from (0, 0.23) to the block's near face y = BLOCK_Y - HALF
const faceY = by - half;
const hitX = d.at[0] + (d.mean[0] / d.mean[1]) * (faceY - d.at[1]);

const shapes: GeoShape[] = [
  // expert paths: straight to the fork, then a waypoint beside the block, then the goal
  { type: "line", from: P([0, 0]), to: P([0, d.fork_y]), tone: "muted", width: 1.5, dashed: true },
  { type: "line", from: P([0, d.fork_y]), to: P([-WAY, WAY_Y]), tone: "a", width: 1.5, dashed: true },
  { type: "line", from: P([-WAY, WAY_Y]), to: P([gx, gy]), tone: "a", width: 1.5, dashed: true },
  { type: "line", from: P([0, d.fork_y]), to: P([WAY, WAY_Y]), tone: "c", width: 1.5, dashed: true },
  { type: "line", from: P([WAY, WAY_Y]), to: P([gx, gy]), tone: "c", width: 1.5, dashed: true },
  { id: "block", type: "rect", at: P([-half, by + half]), size: [r1(2 * half * MAP.s), r1(2 * half * MAP.s)], tone: "muted", rx: 0 },
  { type: "text", at: [P([0, by])[0], P([0, by])[1] - 4], label: { zh: "方块", en: "block" }, tone: "muted" },
  { type: "text", at: [P([0, by])[0], P([0, by])[1] + 14], label: "0.3 m", tone: "muted" },
  { id: "goal", type: "circle", at: P(d.goal), r: r1(0.05 * MAP.s), tone: "ok" },
  { type: "text", at: [P(d.goal)[0] + 20, P(d.goal)[1] + 5], label: { zh: "目标 (0, 1)", en: "goal (0, 1)" }, anchor: "start", tone: "ok" },
  { id: "start", type: "circle", at: P([0, 0]), r: 3, tone: "muted", fill: true },
  { type: "text", at: [P([0, 0])[0] + 10, P([0, 0])[1] + 5], label: { zh: "起点 (0, 0)", en: "start (0, 0)" }, anchor: "start", tone: "muted" },
  { id: "fork", type: "circle", at: P([0, d.fork_y]), r: 3, tone: "muted", fill: true },
  { type: "text", at: [P([0, d.fork_y])[0] + 10, P([0, d.fork_y])[1] + 14], label: { zh: "岔口 (0, 0.2)", en: "fork (0, 0.2)" }, anchor: "start", tone: "muted" },
  { id: "wayL", type: "circle", at: P([-WAY, WAY_Y]), r: 3, tone: "a", fill: true },
  { id: "wayR", type: "circle", at: P([WAY, WAY_Y]), r: 3, tone: "c", fill: true },
  { type: "text", at: [P([-WAY, WAY_Y])[0], P([-WAY, WAY_Y])[1] + 18], label: "(−0.3, 0.4)", tone: "a" },
  { type: "text", at: [P([WAY, WAY_Y])[0], P([WAY, WAY_Y])[1] + 18], label: "(0.3, 0.4)", tone: "c" },
  // the 10 nearest frames' actions, then their mean and where its ray meets the block
  ...d.near.map((n, k): GeoShape => ({ id: `demo${k}`, type: "line", from: P(n.p), to: tipOf(n.p, n.a), tone: n.a[0] < 0 ? "a" : "c", width: 1.5, arrow: true })),
  { type: "text", at: [tipOf(left[0].p, left[0].a)[0] - 4, tipOf(left[0].p, left[0].a)[1] + 4], label: `${left.length}×`, anchor: "end", tone: "a", bold: true },
  { type: "text", at: [tipOf(right[0].p, right[0].a)[0] + 4, tipOf(right[0].p, right[0].a)[1] + 4], label: `${right.length}×`, anchor: "start", tone: "c", bold: true },
  { id: "meanRay", type: "line", from: tipOf(d.at, d.mean), to: P([hitX, faceY]), tone: "danger", width: 1.5, dashed: true },
  { id: "mean", type: "line", from: at, to: tipOf(d.at, d.mean), tone: "danger", width: 2.5, arrow: true },
  { id: "hit", type: "circle", at: P([hitX, faceY]), r: 3, tone: "danger", fill: true },
  // legend
  { type: "line", from: [20, 318], to: [40, 318], tone: "a", width: 1.5 },
  { type: "text", at: [46, 322], label: { zh: `示范动作（×${ARROW}）：${left.length} 条向左、${right.length} 条向右`, en: `demo actions (×${ARROW}): ${left.length} left, ${right.length} right` }, anchor: "start", tone: "ink" },
  { type: "line", from: [20, 338], to: [40, 338], tone: "danger", width: 2.5 },
  { type: "text", at: [46, 342], label: { zh: `平均：dx ${meanCm} cm，冲向方块`, en: `mean: dx ${meanCm} cm, into the block` }, anchor: "start", tone: "danger" },
];

export const actBlockTask: GeoSpec = {
  kind: "geo",
  id: "act-block-task",
  title: { zh: "方块任务：两条正确路线，平均却撞上方块", en: "The block task: two right ways round, and a mean that hits the block" },
  caption: {
    zh: `按比例画出 multimodal.py 的任务。虚线是专家的两种路线（到岔口后经左或右路点去目标）。箭头是 (0, 0.23) 处最近的 ${d.k} 个录制帧的动作（放大 ${ARROW} 倍）：${left.length} 条向左、${right.length} 条向右，横向各 ${lo}–${hi} cm；红色是它们的平均 (${meanCm}, +${(d.mean[1] * 100).toFixed(1)}) cm，沿它走会撞上方块的下沿。`,
    en: `multimodal.py's task to scale. Dashed: the expert's two routes (up to the fork, then past the left or right waypoint to the goal). Arrows: the actions of the ${d.k} recorded frames nearest (0, 0.23), drawn ${ARROW}x: ${left.length} left and ${right.length} right, ${lo}–${hi} cm sideways each. Red: their mean, (${meanCm}, +${(d.mean[1] * 100).toFixed(1)}) cm, which heads into the block's near face.`,
  },
  sources: [MM, "tools/sim/models/act_fork_export.py", OUT],
  w: 340,
  h: 350,
  shapes,
  blockTask: {
    map: MAP,
    block: "block",
    goal: "goal",
    start: "start",
    fork: "fork",
    waypoints: ["wayL", "wayR"],
    at: d.at as Point,
    demos: d.near.map((_, k) => `demo${k}`),
    mean: "mean",
    meanRay: "meanRay",
    arrowScale: ARROW,
  },
  numbers: [
    { note: "demos passing left (expected output: 19)", value: d.lefts, expect: 19, tol: 0 },
    { note: "nearest frames swerving left at (0, 0.23) (lesson table: 7)", value: left.length, expect: 7, tol: 0 },
    { note: "nearest frames swerving right (lesson table: 3)", value: right.length, expect: 3, tol: 0 },
    { note: "mean sideways action, cm (lesson: −1.7)", value: d.mean[0] * 100, expect: -1.7, tol: 0.05 },
    { note: "every demo action is 4.3–4.4 cm sideways (lesson: 4.3 to 4.4 cm)", value: Math.max(...allSide.map((v) => Math.abs(v - 4.35))), expect: 0, tol: 0.05 },
    { note: "mean ray meets the block's near face inside it (|x| < HALF)", value: Math.abs(hitX) < half ? 1 : 0, expect: 1, tol: 0 },
  ],
  facts: [
    { file: MM, pattern: "^GOAL, BLOCK_Y, HALF, FORK_Y = \\(0\\.0, 1\\.0\\), 0\\.5, 0\\.15, 0\\.2$", note: "goal, block centre and half-side, fork" },
    { file: MM, pattern: "^STEP, NOISE, MAX_STEPS, K = 0\\.05, 0\\.005, 60, 10$", note: "5 cm steps, K = 10 neighbours" },
    { file: MM, pattern: `return toward\\(p, \\(${WAY} \\* side, ${WAY_Y}\\)\\)`, note: "waypoints (±0.3, 0.4) as drawn" },
    { file: MM, pattern: "^    episodes = record_demos\\(40, random\\.Random\\(5\\)\\)$", note: "demo seed used by the exporter" },
    { file: MM, pattern: "demos\\.nearest\\(\\(0\\.0, 0\\.23\\)\\)", note: "the table's point (0, 0.23), as exported" },
    { file: OUT, pattern: `^40 expert demos: ${d.lefts} pass on the left, ${40 - d.lefts} on the right`, note: "expected output matches the export" },
    { file: OUT, pattern: `^  10 demo frames +${left.length} +0 +0 +0 +${right.length}$`, note: "expected table: 7 left, 3 right" },
    { file: EN, pattern: "A 0\\.3 m square block sits in between, centred at \\(0, 0\\.5\\)", note: "en block" },
    { file: EN, pattern: "drives straight up to a fork at \\(0, 0\\.2\\), then heads for a waypoint at \\(−0\\.3, 0\\.4\\) or \\(\\+0\\.3, 0\\.4\\)", note: "en fork and waypoints" },
    { file: EN, pattern: "The demonstrations at this spot are 7 left and 3 right, each 4\\.3 to 4\\.4 cm sideways", note: "en table sentence" },
    { file: EN, pattern: "\\(−7 \\+ 3\\) / 10 × 4\\.2 = −1\\.7 cm", note: "en mean (idealised 4.2 cm at the fork)" },
    { file: ZH, pattern: "边长 0\\.3 m 的方块，中心在 \\(0, 0\\.5\\)", note: "zh block" },
    { file: ZH, pattern: "直行到 \\(0, 0\\.2\\) 的岔口", note: "zh fork" },
    { file: ZH, pattern: "\\(−0\\.3, 0\\.4\\) 或 \\(\\+0\\.3, 0\\.4\\)", note: "zh waypoints" },
    { file: ZH, pattern: "这里的示范是 7 条向左、3 条向右，每条横向 4\\.3 到 4\\.4 cm", note: "zh table sentence" },
    { file: ZH, pattern: "\\(−7 \\+ 3\\) / 10 × 4\\.2 = −1\\.7 cm", note: "zh mean (idealised 4.2 cm at the fork)" },
    { file: EN, pattern: "^<Diagram id=\"act-block-task\" />$", note: "placed in the en lesson" },
    { file: ZH, pattern: "^<Diagram id=\"act-block-task\" />$", note: "placed in the zh lesson" },
  ],
};
