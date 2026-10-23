import type { GeoShape, GeoSpec, Point } from "../types";
import d from "../data/bc-corridor.json";

/*
 * m6/behaviour-cloning "Covariate shift" (D113): the L-shaped corridor of bc_reach.py drawn to scale, with one
 * fixed-seed run of each kind. data/bc-corridor.json is written by tools/sim/models/bc_corridor_export.py, which
 * imports bc_reach.py itself: the first 5 noise-free demos (Random(6)) and BC-5's evaluation exactly as
 * bc_reach.evaluate runs it (seed 2026, 100 runs). check_diagrams re-runs the exporter and requires the same file,
 * rebuilds the walls from the corridor constants and checks that the drawn success run stays inside and ends at the
 * goal and the drawn failure leaves through the goal-end wall without ever coming within 5 cm of the goal.
 */

const BC = "examples/month-6/behaviour-cloning/bc_reach.py";
const OUT = "examples/month-6/expected/bc_reach.txt";
const EN = "src/content/m6/behaviour-cloning/en.mdx";
const ZH = "src/content/m6/behaviour-cloning/zh.mdx";

const MAP = { x0: 43, y0: 280, s: 230 };
const P = (q: number[]): Point => [Math.round((MAP.x0 + MAP.s * q[0]) * 10) / 10, Math.round((MAP.y0 - MAP.s * q[1]) * 10) / 10];
const [cx, cy] = d.corner, [gx, gy] = d.goal, hw = d.half_width;
const GOAL_R = 0.05; // bc_reach.rollout: success when within 0.05 m of the goal

const ev = d.eval, ok = d.success_run, bad = d.wall_run, nf = d.nearest_frame;
const okWorst = ok.worst_cm.toFixed(1), badOff = nf.offset_cm.toFixed(1);
const closest = Math.min(...bad.path.map((q) => Math.hypot(q[0] - gx, q[1] - gy)));
const closestCm = (closest * 100).toFixed(1);
const act = `(${nf.action[0].toFixed(2)}, +${nf.action[1].toFixed(2)})`;

const WALLS = [[-hw, -hw], [cx + hw, -hw], [gx + hw, gy + hw], [gx - hw, gy + hw], [cx - hw, hw], [-hw, hw], [-hw, -hw]];
const ARROW_SCALE = 3; // the 5 cm action drawn 3x longer so the arrowhead is visible
const from = P(nf.from), tip = P([nf.from[0] + ARROW_SCALE * nf.action[0], nf.from[1] + ARROW_SCALE * nf.action[1]]);

const LEG = 48; // legend: sample line from x 24 to 44, text from 50
const legend = (y: number, group: string, tone: GeoShape["tone"], label: { zh: string; en: string }, dashed = false): GeoShape[] => [
  { group, type: "line", from: [24, y - 4], to: [44, y - 4], tone, width: 2, dashed },
  { group, type: "text", at: [LEG + 2, y], label, anchor: "start", tone },
];

const shapes: GeoShape[] = [
  { id: "walls", type: "polyline", pts: WALLS.map(P), tone: "muted", width: 2 },
  { id: "endwall", group: "end", type: "line", from: P([gx - hw, gy + hw]), to: P([gx + hw, gy + hw]), tone: "danger", width: 3 },
  { group: "demo", type: "polyline", pts: [P(d.start), P(d.corner), P(d.goal)], tone: "muted", width: 1, dashed: true },
  ...d.demos.map((ep): GeoShape => ({ group: "demo", type: "polyline", pts: ep.map(P), tone: "b", width: 1.5 })),
  { id: "success", group: "ok", type: "polyline", pts: ok.path.map(P), tone: "ok", width: 1.5 },
  { id: "fail", group: "bad", type: "polyline", pts: bad.path.map(P), tone: "danger", width: 1.5 },
  { group: "bad", type: "circle", at: P(bad.path[bad.path.length - 1]), r: 3, tone: "danger", fill: true },
  { id: "goal", type: "circle", at: P(d.goal), r: GOAL_R * MAP.s, tone: "ok", dashed: true },
  { group: "why", type: "line", from, to: P(nf.at), tone: "muted", width: 1, dashed: true },
  { group: "why", type: "circle", at: P(nf.at), r: 3, tone: "b", fill: true },
  { group: "why", type: "line", from, to: tip, tone: "a", width: 2, arrow: true },
  { type: "text", at: [20, 320], label: { zh: "起点 (0, 0)", en: "start (0, 0)" }, anchor: "start", tone: "muted" },
  { type: "text", at: [296, 320], label: { zh: "拐角 (1, 0)", en: "corner (1, 0)" }, anchor: "end", tone: "muted" },
  { type: "text", at: [P(d.goal)[0] - 30, P(d.goal)[1] + 5], label: { zh: "目标 (1, 1)", en: "goal (1, 1)" }, anchor: "end", tone: "ok" },
  { type: "text", at: [P([cx - hw, 0.3])[0] - 6, P([0, 0.3])[1]], label: { zh: "宽 0.2 m", en: "0.2 m wide" }, anchor: "end", tone: "muted" },
  ...legend(110, "demo", "b", { zh: "5 条示范（无噪声）", en: "5 demos (no noise)" }),
  ...legend(132, "ok", "ok", { zh: `BC 第 ${ok.run + 1} 次：到达目标`, en: `BC run ${ok.run + 1}: reaches goal` }),
  ...legend(154, "bad", "danger", { zh: `BC 第 ${bad.run + 1} 次：撞端墙`, en: `BC run ${bad.run + 1}: hits end wall` }),
  ...legend(176, "why", "a", { zh: "最近帧的动作（×3）", en: "nearest frame's action (×3)" }),
];

export const bcCorridor: GeoSpec = {
  kind: "geo",
  id: "bc-corridor",
  title: { zh: "L 形走廊里的协变量偏移", en: "Covariate shift in the L-shaped corridor" },
  caption: {
    zh: `按比例画出 bc_reach.py 的走廊。用固定种子各取一次运行：前 ${d.demos.length} 条无噪声示范（共 ${d.demo_frames} 帧，其中只有 ${d.demo_frames_over_3cm} 帧偏离中心线 3 cm 以上），以及只用这 ${d.demos.length} 条示范的 BC 在评估中（种子 ${ev.seed}，每步 1 cm 噪声）的第 ${ok.run + 1} 次和第 ${bad.run + 1} 次运行。虚线圆是 5 cm 的成功范围。`,
    en: `bc_reach.py's corridor to scale, with one fixed-seed run of each kind: the first ${d.demos.length} noise-free demos (${d.demo_frames} frames, only ${d.demo_frames_over_3cm} of them more than 3 cm off the centre line) and runs ${ok.run + 1} and ${bad.run + 1} of the evaluation (seed ${ev.seed}, 1 cm noise per step) of BC trained on those ${d.demos.length} demos. The dashed circle is the 5 cm success radius.`,
  },
  sources: [BC, "tools/sim/models/bc_corridor_export.py", OUT],
  w: 340,
  h: 328,
  shapes,
  corridor: { map: MAP, corner: [cx, cy], goal: [gx, gy], halfWidth: hw, goalRadius: GOAL_R, walls: "walls", success: "success", fail: "fail" },
  steps: [
    {
      label: {
        zh: `示范：专家在没有噪声时录制，几步之内就收拢到中心线上。${d.demo_frames} 帧里只有 ${d.demo_frames_over_3cm} 帧偏离中心线 3 cm 以上，没有一帧示范“偏了怎么回来”。`,
        en: `The demos: recorded with no noise, the expert settles onto the centre line within a few steps. Only ${d.demo_frames_over_3cm} of the ${d.demo_frames} frames are more than 3 cm off it, and none shows how to come back.`,
      },
      highlight: ["demo"],
    },
    {
      label: {
        zh: `BC 第 ${ok.run + 1} 次运行：每步 1 cm 的执行噪声把夹爪推离中心线，最远偏离 ${okWorst} cm，仍然到达了目标。`,
        en: `BC run ${ok.run + 1}: 1 cm of actuator noise per step pushes the gripper off the centre line, up to ${okWorst} cm, and it still reaches the goal.`,
      },
      highlight: ["ok", "demo"],
    },
    {
      label: {
        zh: `BC 第 ${bad.run + 1} 次运行：在第二段偏到中心线右侧 ${badOff} cm。最近的录制帧在中心线上，动作是 ${act}，继续往 +y 走。它离目标最近也有 ${closestCm} cm（成功要 5 cm 以内），于是撞上尽头的墙。`,
        en: `BC run ${bad.run + 1}: in leg 2 it drifts ${badOff} cm right of the centre line. The nearest recorded frame is on the centre line and its action is ${act}: keep going +y. It never gets closer than ${closestCm} cm to the goal (success needs 5 cm) and drives into the end wall.`,
      },
      highlight: ["bad", "why", "end"],
    },
    {
      label: {
        zh: `100 次里成功 ${ev.counts.success} 次，撞墙 ${ev.counts.wall} 次，其中 ${ev.walls["goal end"]} 次在目标端：示范一进入目标 5 cm 就结束，偏着到达目标附近时没有任何帧可学。`,
        en: `Of the 100 runs, ${ev.counts.success} succeed and ${ev.counts.wall} hit a wall, ${ev.walls["goal end"]} of them at the goal end: the demos stop within 5 cm of the goal, so no frame says what to do when you arrive off-centre.`,
      },
      highlight: ["bad", "end"],
    },
  ],
  numbers: [
    { note: "bc_reach.py START, CORNER, GOAL", value: Math.abs(d.start[0]) + Math.abs(d.start[1]) + Math.abs(cx - 1) + Math.abs(cy) + Math.abs(gx - 1) + Math.abs(gy - 1), expect: 0, tol: 0 },
    { note: "corridor half-width (lesson: 0.2 m wide)", value: 2 * hw, expect: 0.2, tol: 1e-9 },
    { note: "BC-5 successes (lesson SimOutput)", value: ev.counts.success, expect: 61, tol: 0 },
    { note: "BC-5 wall hits (lesson SimOutput)", value: ev.counts.wall, expect: 39, tol: 0 },
    { note: "BC-5 wall hits at the goal end (lesson SimOutput)", value: ev.walls["goal end"], expect: 29, tol: 0 },
    { note: "BC-5 training frames (lesson SimOutput)", value: d.demo_frames, expect: 190, tol: 0 },
    { note: "share of demo frames > 3 cm off centre (lesson: almost nothing)", value: d.demo_frames_over_3cm / d.demo_frames, expect: 0, tol: 0.02 },
    { note: "nearest frame lies on the centre line (lesson: a centre-line frame)", value: Math.abs(nf.at[0] - cx), expect: 0, tol: 0.005 },
    { note: "its action is pure +y, full step (lesson: says go straight)", value: Math.abs(nf.action[0]) + Math.abs(nf.action[1] - d.step), expect: 0, tol: 1e-9 },
    { note: "the failed run is off by about 5 cm there (lesson: pushes the gripper 5 cm to the side)", value: nf.offset_cm, expect: 5, tol: 2.5 },
  ],
  facts: [
    { file: BC, pattern: "^START, CORNER, GOAL = \\(0\\.0, 0\\.0\\), \\(1\\.0, 0\\.0\\), \\(1\\.0, 1\\.0\\)$", note: "corridor corners as drawn" },
    { file: BC, pattern: "^HALF_WIDTH, STEP, NOISE, MAX_STEPS = 0\\.10, 0\\.05, 0\\.01, 80$", note: "half-width 0.10 m, 5 cm steps, 1 cm noise" },
    { file: BC, pattern: "^def evaluate\\(policy, seed, n=100\\):$", note: "100 runs per evaluation, as exported" },
    { file: BC, pattern: `^    c, med, walls = evaluate\\(policy, seed=${ev.seed}\\)$`, note: "evaluation seed used by the exporter" },
    { file: BC, pattern: "^    rng = random\\.Random\\(6\\)\\n    demos = record_demos\\(80, rng\\)$", note: "demo seed used by the exporter" },
    { file: BC, pattern: "^        frames = \\[f for f in demos if f\\[0\\] < n\\]$", note: "BC on n demos = the first n episodes, as exported" },
    { file: OUT, pattern: `^BC, 5 demos +${d.demo_frames} frames +success +${ev.counts.success}/100 +wall +${ev.counts.wall} `, note: "expected output matches the exported counts" },
    { file: OUT, pattern: `^ +wall hits at: leg 1 ${ev.walls["leg 1"]}, corner ${ev.walls.corner}, leg 2 ${ev.walls["leg 2"]}, goal end ${ev.walls["goal end"]}$`, note: "first 'wall hits at' line is BC-5's, as exported" },
    { file: EN, pattern: `^BC, 5 demos +${d.demo_frames} frames +success +${ev.counts.success}/100 +wall +${ev.counts.wall} `, note: "en lesson SimOutput matches" },
    { file: ZH, pattern: `^BC, 5 demos +${d.demo_frames} frames +success +${ev.counts.success}/100 +wall +${ev.counts.wall} `, note: "zh lesson SimOutput matches" },
    { file: EN, pattern: "L-shaped corridor 0\\.2 m wide: from \\(0, 0\\) along x to the corner at \\(1, 0\\), then along y to the goal at \\(1, 1\\)", note: "en geometry sentence" },
    { file: EN, pattern: "within 5 cm of the goal inside 80 steps", note: "en success rule (dashed circle)" },
    { file: EN, pattern: "almost nothing more than 3 cm off it", note: "en: demos hug the centre line (step 1)" },
    { file: EN, pattern: "the nearest frame still says \"go straight\"", note: "en: step 3" },
    { file: EN, pattern: "The policy keeps going in \\+y and drives into the end wall", note: "en: goal-end failure (step 3/4)" },
    { file: ZH, pattern: "L 形走廊里移动的点状夹爪，走廊宽 0\\.2 m：从 \\(0, 0\\) 沿 x 走到拐角 \\(1, 0\\)，再沿 y 走到目标 \\(1, 1\\)", note: "zh geometry sentence" },
    { file: ZH, pattern: "在 80 步之内到达目标 5 cm 以内", note: "zh success rule (dashed circle)" },
    { file: ZH, pattern: "几乎没有偏离中心线 3 cm 以上的帧", note: "zh: step 1" },
    { file: ZH, pattern: "最近帧仍然说“直走”", note: "zh: step 3" },
    { file: ZH, pattern: "策略继续往 \\+y 走，撞上了尽头的墙", note: "zh: goal-end failure" },
    { file: EN, pattern: "^<Diagram id=\"bc-corridor\" />$", note: "placed in the en lesson" },
    { file: ZH, pattern: "^<Diagram id=\"bc-corridor\" />$", note: "placed in the zh lesson" },
  ],
};
