import type { CircuitSpec, Point } from "../types";

/*
 * m1/components "Bridge rectifier and ripple": which two diodes of the four-diode bridge conduct in each
 * half-cycle, and the current path through the load. Diode numbering as in the lesson text: D1 upper-left,
 * D2 upper-right, D3 lower-right, D4 lower-left; every diode has its anode below its cathode, so the top
 * rail is + and the bottom rail is −. Positive half-cycle (terminal a above b): D1 + D3; negative: D2 + D4.
 * The load RL is crossed from the + rail to the − rail in both half-cycles. The smoothing capacitor of the
 * toy (C in parallel with RL) is left out; with it, the same pairs conduct, only near each peak.
 * Peak numbers follow the lesson's worked example (12 V rms, two 0.7 V drops).
 */

const VRMS = 12; // secondary, V rms
const VF = 0.7; // drop per conducting silicon diode, V
const VPK = VRMS * Math.SQRT2; // 16.97 V
const VOUT_PK = VPK - 2 * VF; // about 15.6 V: two drops in every path
const fmt = (x: number, d: number) => x.toFixed(d);

const EN = "src/content/m1/components/en.mdx";
const ZH = "src/content/m1/components/zh.mdx";
const TOY = "examples/month-1/components/bridge_rectifier_ripple_toy.py";

// geometry: + rail y 50, ac line y 150, − rail y 250; left leg x 110, right leg x 230, load x 310
const A: Point = [152, 150]; // ac terminal a (left)
const B: Point = [188, 150]; // ac terminal b (right)

export const bridgeRectifierPaths: CircuitSpec = {
  kind: "circuit",
  id: "bridge-rectifier-paths",
  title: { zh: "四二极管整流桥：每个半周哪两个导通", en: "Four-diode bridge: which two diodes conduct each half-cycle" },
  caption: {
    zh: `编号与课文一致：D1 左上、D2 右上、D3 右下、D4 左下，四个二极管都是阳极在下、阴极在上，所以上轨是 +、下轨是 −。正半周（a 端高于 b 端）D1 与 D3 导通；负半周 D2 与 D4 导通。两个半周里负载 RL 的电流都从 + 轨流向 − 轨，方向不变，路径上总有两个二极管压降：${VRMS} V rms 的峰值 ${fmt(VPK, 2)} V，减去 2 × ${VF} V 约为 ${fmt(VOUT_PK, 1)} V。图里省略了与 RL 并联的平滑电容；加上电容后导通的仍是同样两对，只是只在峰值附近导通。彩色虚线是常规电流。`,
    en: `Numbering as in the lesson: D1 upper-left, D2 upper-right, D3 lower-right, D4 lower-left; every diode has its anode below its cathode, so the top rail is + and the bottom rail is −. Positive half-cycle (terminal a above b): D1 and D3 conduct; negative half-cycle: D2 and D4. In both half-cycles the load current flows through RL from the + rail to the − rail, the same direction, and the path always has two diode drops: a ${VRMS} V rms peak of ${fmt(VPK, 2)} V minus 2 × ${VF} V is about ${fmt(VOUT_PK, 1)} V. The smoothing capacitor in parallel with RL is left out; with it the same pairs conduct, only near each peak. The coloured dashes show conventional current.`,
  },
  sources: [EN, ZH, TOY],
  w: 340,
  h: 300,
  readoutAt: [170, 286],
  parts: [
    { id: "D1", type: "diode", at: [110, 100], dir: "v", len: 40, flip: true, label: "D1", labelAt: [96, 104], anchor: "end" },
    { id: "D4", type: "diode", at: [110, 200], dir: "v", len: 40, flip: true, label: "D4", labelAt: [96, 204], anchor: "end" },
    { id: "D2", type: "diode", at: [230, 100], dir: "v", len: 40, flip: true, label: "D2", labelAt: [244, 104], anchor: "start" },
    { id: "D3", type: "diode", at: [230, 200], dir: "v", len: 40, flip: true, label: "D3", labelAt: [244, 204], anchor: "start" },
    { id: "src", type: "ac", at: [170, 150], dir: "h", len: 36, label: { zh: "交流 12 V rms", en: "AC 12 V rms" }, labelAt: [170, 186] },
    { id: "RL", type: "resistor", at: [310, 150], dir: "v", len: 60, label: "RL", labelAt: [296, 154], anchor: "end" },
    { id: "ta", type: "text", at: [146, 138], label: "a", labelAt: [146, 138], anchor: "end", mono: true },
    { id: "tb", type: "text", at: [194, 138], label: "b", labelAt: [194, 138], anchor: "start", mono: true },
    { id: "plus", type: "text", at: [170, 42], label: { zh: "+ 轨", en: "+ rail" }, labelAt: [170, 42], tone: "a" },
    { id: "minus", type: "text", at: [170, 270], label: { zh: "− 轨", en: "− rail" }, labelAt: [170, 270], tone: "a" },
    { id: "nL", type: "node", at: [110, 150] },
    { id: "nR", type: "node", at: [230, 150] },
    { id: "nT", type: "node", at: [230, 50] },
    { id: "nB", type: "node", at: [230, 250] },
  ],
  wires: [
    { id: "wTop", pts: [[110, 80], [110, 50], [310, 50], [310, 120]] },
    { id: "wBot", pts: [[110, 220], [110, 250], [310, 250], [310, 180]] },
    { id: "wD2t", pts: [[230, 50], [230, 80]] },
    { id: "wD3b", pts: [[230, 220], [230, 250]] },
    { id: "wL", pts: [[110, 120], [110, 180]] },
    { id: "wR", pts: [[230, 120], [230, 180]] },
    { id: "wA", pts: [[110, 150], A] },
    { id: "wB", pts: [B, [230, 150]] },
  ],
  states: [
    {
      id: "positive",
      label: { zh: "正半周：D1 + D3", en: "Positive half: D1 + D3" },
      closed: ["D1", "D3"],
      tone: "a",
      flow: [A, [110, 150], [110, 50], [310, 50], [310, 250], [230, 250], [230, 150], B],
      readout: { zh: "D1、D3 导通；RL 电流 + → −", en: "D1, D3 on; RL current + → −" },
      text: {
        zh: "a 端为正：电流从 a 经 D1 上到 + 轨，自上而下流过 RL，再经 − 轨、D3 回到 b 端。D2 与 D4 反偏、不导通。",
        en: "Terminal a is positive: current flows from a up through D1 to the + rail, down through RL, along the − rail and up through D3 back to terminal b. D2 and D4 are reverse-biased and block.",
      },
    },
    {
      id: "negative",
      label: { zh: "负半周：D2 + D4", en: "Negative half: D2 + D4" },
      closed: ["D2", "D4"],
      tone: "b",
      flow: [B, [230, 150], [230, 50], [310, 50], [310, 250], [110, 250], [110, 150], A],
      readout: { zh: "D2、D4 导通；RL 电流 + → −", en: "D2, D4 on; RL current + → −" },
      text: {
        zh: "b 端为正：电流从 b 经 D2 上到 + 轨，仍然自上而下流过 RL，再经 − 轨、D4 回到 a 端。D1 与 D3 反偏、不导通。负载里的电流方向与正半周相同，这就是全波整流。",
        en: "Terminal b is positive: current flows from b up through D2 to the + rail, still down through RL, along the − rail and up through D4 back to terminal a. D1 and D3 are reverse-biased and block. The load current has the same direction as in the positive half-cycle: that is full-wave rectification.",
      },
    },
  ],
  numbers: [
    { note: "secondary peak 12 V rms × √2 (lesson: 16.97 V)", value: VPK, expect: 16.97, tol: 0.005 },
    { note: "bridge peak after two 0.7 V drops (lesson: about 15.6 V)", value: VOUT_PK, expect: 15.6, tol: 0.05 },
  ],
  facts: [
    { file: EN, pattern: "D1 upper-left, D2 upper-right, D3 lower-right, D4 lower-left", note: "lesson diode numbering" },
    { file: ZH, pattern: "D1 左上、D2 右上、D3 右下、D4 左下", note: "zh lesson diode numbering" },
    { file: EN, pattern: "on the positive half-cycle D1 and D3 conduct; on the negative half-cycle D2 and D4 conduct", note: "lesson: conducting pairs" },
    { file: ZH, pattern: "正半周 D1 与 D3 导通；负半周 D2 与 D4 导通", note: "zh lesson: conducting pairs" },
    { file: EN, pattern: "from the \\+ rail to the − rail in both half-cycles", note: "lesson: load current direction" },
    { file: ZH, pattern: "两个半周里都从 \\+ 轨流向 − 轨", note: "zh lesson: load current direction" },
    { file: EN, pattern: "`12 × √2 = 16\\.97 V`; after two 0\\.7 V drops a bridge charges to about 15\\.6 V", note: "lesson worked example" },
    { file: ZH, pattern: "`12 × √2 = 16\\.97 V`；减去两个 0\\.7 V 压降，整流桥充到约 15\\.6 V", note: "zh lesson worked example" },
    { file: TOY, pattern: "rect = src - vf if arm == \"A_half\" else abs\\(src\\) - 2\\.0 \\* vf", note: "toy: the bridge path always has two drops, |v| − 2 VF" },
  ],
};
