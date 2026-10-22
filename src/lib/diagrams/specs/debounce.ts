import type { TimingSpec } from "../types";
import bounce from "../data/debounce-bounce.json";

/*
 * m2/timing-interrupts: the "quiet line" debounce of reaction_timer.ino applied to the simulated bounce of debounce_sim.py.
 * The edges come from debounce_sim.py (seed 1, 0.1 ms sampler) through tools/sim/models/debounce_export.py
 * into data/debounce-bounce.json; check_diagrams re-runs the exporter and requires an identical file.
 * Line 1 is the first press (100 ms), line 2 its release (400 ms); both lines share one time scale
 * (columnScale units per ms), so a 0.9 ms bounce and the 30 ms window are drawn in proportion.
 * ISR rule (firmware): on every edge t = millis(); a LOW edge is a press if t - lastEdge > DEBOUNCE_MS;
 * then lastEdge = t. So after an edge at time e the line counts as quiet again from floor(e) + 31 ms.
 */

type Edge = [number, number];
const EDGES = bounce.edges as Edge[];
const QUIET = bounce.debounce_ms;
const PRESSES = bounce.presses as [number, number][];
const [START, HOLD] = PRESSES[0];
const RELEASE = START + HOLD;

const near = (t0: number) => EDGES.filter(([t]) => t >= t0 - 1 && t < t0 + 20);
const quietFrom = (e: number) => Math.floor(e) + QUIET + 1; // first millis() value that passes "> QUIET"
const pressEdges = near(START);
const releaseEdges = near(RELEASE);
const lastOf = (es: Edge[]) => es[es.length - 1][0];

/** Column boundaries of one line: window start, every edge, the end of the quiet window, window end. */
const line = (from: number, es: Edge[], to: number) => [from, ...es.map(([t]) => t), quietFrom(lastOf(es)), to];
const B1 = line(START - 6, pressEdges, quietFrom(lastOf(pressEdges)) + 7);
const B2 = line(RELEASE - 4, releaseEdges, quietFrom(lastOf(releaseEdges)) + 3);
const starts = [...B1.slice(0, -1), ...B2.slice(0, -1)];
const columns = [...B1.slice(1).map((t, i) => +(t - B1[i]).toFixed(1)), ...B2.slice(1).map((t, i) => +(t - B2[i]).toFixed(1))];
const N1 = B1.length - 1;

const levelAt = (x: number) => EDGES.filter(([t]) => t <= x).reduce((_, [, l]) => l, 1);
const quietAt = (x: number) => (EDGES.some(([t]) => t <= x && x < quietFrom(t)) ? 0 : 1);
const countAt = (x: number) => String(bounce.accepted.filter((t) => t <= x).length);

const fmt = (t: number) => t.toFixed(1);
const falling = EDGES.filter(([, l]) => l === 0).length;
// bounce clusters: edges closer than QUIET to the previous edge belong to the same press or release
const clusters: Edge[][] = [];
for (const e of EDGES) {
  const c = clusters[clusters.length - 1];
  if (c && e[0] - c[c.length - 1][0] <= QUIET) c.push(e);
  else clusters.push([e]);
}
const durations = clusters.map((c) => c[c.length - 1][0] - c[0][0]);
const gaps = clusters.flatMap((c) => c.slice(1).map(([t], i) => t - c[i][0]));
const restEdges = pressEdges.slice(1);
const restLow = restEdges.filter(([, l]) => l === 0);
const relLow = releaseEdges.find(([, l]) => l === 0)!;
const relLowPrev = releaseEdges[releaseEdges.indexOf(relLow) - 1][0];

const INO = "examples/month-2/timing-interrupts/reaction_timer/reaction_timer.ino";
const SIM = "tools/sim/models/debounce_sim.py";
const EXPORT = "tools/sim/models/debounce_export.py";
const EN = "src/content/m2/timing-interrupts/en.mdx";
const ZH = "src/content/m2/timing-interrupts/zh.mdx";
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export const debounceQuiet: TimingSpec = {
  kind: "timing",
  id: "debounce-quiet-line",
  title: { zh: `“安静线路”消抖：DEBOUNCE_MS = ${QUIET}`, en: `"Quiet line" debounce: DEBOUNCE_MS = ${QUIET}` },
  caption: {
    zh: `D2 是 debounce_sim.py（种子 1，每 0.1 ms 采样）里第一次按下（${START} ms）和松开（${RELEASE} ms）时模型给出的弹跳边沿，两行时间比例相同。“安静”在距上一个边沿超过 ${QUIET} ms 时为高；“计数”是 reaction_timer.ino 中断规则接受的按下次数。`,
    en: `D2 shows the simulated bounce edges of the first press (${START} ms) and its release (${RELEASE} ms) in debounce_sim.py (seed 1, sampled every 0.1 ms); both lines use the same time scale. "idle" (the quiet line) is HIGH once more than ${QUIET} ms have passed since the previous edge; "n" is the number of presses the reaction_timer.ino ISR rule accepts.`,
  },
  sources: [INO, SIM, EXPORT, EN, ZH],
  columns,
  columnScale: 6,
  lines: [
    [0, N1 - 1],
    [N1, columns.length - 1],
  ],
  signals: [
    { name: "D2", levels: starts.map(levelAt), tone: "a" },
    { name: { zh: "安静", en: "idle" }, levels: starts.map(quietAt), tone: "ok" },
    { name: { zh: "计数", en: "n" }, kind: "bus", values: starts.map(countAt), tone: "b" },
  ],
  spans: [
    { from: 1, to: pressEdges.length - 1, label: { zh: `弹跳 ${fmt(lastOf(pressEdges) - pressEdges[0][0])} ms`, en: `bounce ${fmt(lastOf(pressEdges) - pressEdges[0][0])} ms` } },
    { from: pressEdges.length, to: pressEdges.length, side: "bottom", label: { zh: `超过 ${QUIET} ms 无边沿`, en: `no edge for > ${QUIET} ms` } },
    { from: N1 + 1, to: N1 + releaseEdges.length - 1, label: { zh: `松开 ${fmt(lastOf(releaseEdges) - releaseEdges[0][0])} ms`, en: `release ${fmt(lastOf(releaseEdges) - releaseEdges[0][0])} ms` } },
    { from: N1 + releaseEdges.length, to: N1 + releaseEdges.length, side: "bottom", label: { zh: `超过 ${QUIET} ms 无边沿`, en: `no edge for > ${QUIET} ms` } },
  ],
  steps: [
    {
      column: 0,
      label: {
        zh: `松开状态：上拉让 D2 为 HIGH，线路已经超过 ${QUIET} ms 没有边沿。`,
        en: `Released: the pull-up holds D2 HIGH, and there has been no edge for more than ${QUIET} ms.`,
      },
    },
    {
      column: 1,
      label: {
        zh: `${fmt(pressEdges[0][0])} ms：第一个下降沿。线路此前是安静的，中断立刻接受：pressedAt = millis() = ${Math.floor(pressEdges[0][0])}，计数变为 1，没有额外延迟。`,
        en: `${fmt(pressEdges[0][0])} ms: the first falling edge. The line was quiet, so the ISR accepts it at once: pressedAt = millis() = ${Math.floor(pressEdges[0][0])}, n = 1, no added latency.`,
      },
    },
    {
      column: 3,
      label: {
        zh: `${restEdges.map(([t]) => fmt(t)).join("、")} ms：又有 ${restEdges.length} 个弹跳边沿，每个距上一个边沿都不超过 ${QUIET} ms。其中为 LOW 的 ${restLow.map(([t]) => fmt(t)).join(" 和 ")} ms 被拒绝；每个边沿都会重置安静计时（lastEdge = t）。`,
        en: `${restEdges.map(([t]) => fmt(t)).join(", ")} ms: ${restEdges.length} more bounce edges, each no more than ${QUIET} ms after the previous one. The LOW ones at ${restLow.map(([t]) => fmt(t)).join(" and ")} ms are rejected; every edge restarts the quiet timer (lastEdge = t).`,
      },
    },
    {
      column: pressEdges.length,
      label: {
        zh: `最后一个边沿在 ${fmt(lastOf(pressEdges))} ms（millis() = ${Math.floor(lastOf(pressEdges))}）。只有 t − ${Math.floor(lastOf(pressEdges))} > ${QUIET}，即从 ${quietFrom(lastOf(pressEdges))} ms 起，新的 LOW 边沿才会再被接受。`,
        en: `The last edge is at ${fmt(lastOf(pressEdges))} ms (millis() = ${Math.floor(lastOf(pressEdges))}). A new LOW edge is accepted only when t − ${Math.floor(lastOf(pressEdges))} > ${QUIET}, that is from ${quietFrom(lastOf(pressEdges))} ms.`,
      },
    },
    {
      column: N1 + 1,
      label: {
        zh: `${fmt(releaseEdges[0][0])} ms 松开：上升沿读到 HIGH，永远不计数，但同样重置安静计时。`,
        en: `Release at ${fmt(releaseEdges[0][0])} ms: rising edges read HIGH and never count, but they restart the quiet timer too.`,
      },
    },
    {
      column: N1 + 1 + releaseEdges.indexOf(relLow),
      label: {
        zh: `${fmt(relLow[0])} ms：松开时的下降弹跳沿，距上一个边沿只有 ${fmt(relLow[0] - relLowPrev)} ms（millis() 之差 ${Math.floor(relLow[0])} − ${Math.floor(relLowPrev)} = ${Math.floor(relLow[0]) - Math.floor(relLowPrev)}），不超过 ${QUIET} ms，被拒绝。没有这条规则，它会被当成一次新的按下。`,
        en: `${fmt(relLow[0])} ms: a falling bounce edge during the release, only ${fmt(relLow[0] - relLowPrev)} ms after the previous edge (millis() difference ${Math.floor(relLow[0])} − ${Math.floor(relLowPrev)} = ${Math.floor(relLow[0]) - Math.floor(relLowPrev)}), not more than ${QUIET} ms: rejected. Without the rule it would count as a new press.`,
      },
    },
    {
      column: N1 + releaseEdges.length,
      label: {
        zh: `从 ${quietFrom(lastOf(releaseEdges))} ms 起线路重新安静，下一次按下的第一个边沿会被立即接受。`,
        en: `From ${quietFrom(lastOf(releaseEdges))} ms the line is quiet again, and the first edge of the next press will be accepted at once.`,
      },
    },
    {
      label: {
        zh: `整个模型（种子 1，${PRESSES.length} 次按下）：${EDGES.length} 个边沿，其中 ${falling} 个下降沿（课文里的朴素计数 ${bounce.naive_presses}）。安静线路规则只接受 ${bounce.accepted.length} 个：${bounce.accepted.map(fmt).join("、")} ms，正好是每次按下的第一个边沿。`,
        en: `The whole model run (seed 1, ${PRESSES.length} presses): ${EDGES.length} edges, ${falling} of them falling (the lesson's naive count, ${bounce.naive_presses}). The quiet-line rule accepts ${bounce.accepted.length}: ${bounce.accepted.map(fmt).join(", ")} ms, the first edge of each press.`,
      },
    },
  ],
  numbers: [
    { note: "firmware DEBOUNCE_MS (fact) = exported window", value: QUIET, expect: 30, tol: 0 },
    { note: "falling edges in the model = lesson naive edge count 19", value: falling, expect: 19, tol: 0 },
    { note: "exporter's naive count = lesson 19", value: bounce.naive_presses, expect: 19, tol: 0 },
    { note: "presses accepted by the quiet-line rule = real presses (5)", value: bounce.accepted.length, expect: PRESSES.length, tol: 0 },
    ...bounce.accepted.map((t, i) => ({ note: `accepted press ${i + 1} is the first edge of press ${i + 1} (within 1 ms of ${PRESSES[i][0]} ms)`, value: t, expect: PRESSES[i][0], tol: 1 })),
    { note: "bounce clusters = 2 per press", value: clusters.length, expect: 2 * PRESSES.length, tol: 0 },
    { note: "longest bounce cluster ≤ 8 ms (lesson: 3–8 ms of chatter)", value: Math.max(...durations), expect: 4, tol: 4 },
    { note: "bounce gaps within 0.2–3 ms (lesson), ± one 0.1 ms sample: largest", value: Math.max(...gaps), expect: 1.6, tol: 1.5 },
    { note: "bounce gaps within 0.2–3 ms (lesson), ± one 0.1 ms sample: smallest", value: Math.min(...gaps), expect: 1.6, tol: 1.5 },
    { note: "every line shares one time scale: line 1 columns sum to its window", value: columns.slice(0, N1).reduce((a, b) => a + b, 0), expect: B1[B1.length - 1] - B1[0], tol: 0.01 },
  ],
  facts: [
    { file: INO, pattern: `const unsigned long DEBOUNCE_MS = ${QUIET};`, note: "firmware debounce constant" },
    { file: INO, pattern: "if \\(isDown && t - lastEdge > DEBOUNCE_MS\\)", note: "firmware rule: strictly more than DEBOUNCE_MS" },
    { file: INO, pattern: "lastEdge = t;", note: "every edge restarts the quiet timer" },
    { file: INO, pattern: "attachInterrupt\\(digitalPinToInterrupt\\(BUTTON_PIN\\), onButton, CHANGE\\);", note: "ISR on every edge" },
    { file: SIM, pattern: esc(`presses = [${PRESSES.map(([a, b]) => `(${a}, ${b})`).join(", ")}]`), note: "exporter uses the presses of debounce_sim.py" },
    { file: SIM, pattern: "def bouncy_button\\(presses, seed=1\\)", note: "fixed seed 1" },
    { file: EN, pattern: "naive edge count:    19", note: "lesson output" },
    { file: EN, pattern: `if the line has been quiet for more than ${QUIET} ms`, note: "lesson quiet-line rule" },
    { file: ZH, pattern: `如果线路此前已超过 ${QUIET} ms 没有边沿`, note: "zh lesson quiet-line rule" },
  ],
};
