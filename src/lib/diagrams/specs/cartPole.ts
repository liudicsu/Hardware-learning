import type { GeoShape, GeoSpec, Point } from "../types";

/*
 * m5/state-space-lqr "Two plants, one form" (D098): the cart-pole sign convention behind A and B.
 * tools/sim/models/lqr_sim.py: cartpole() has alpha = (g sin(theta) - a cos(theta)) / L, so a positive force
 * (cart accelerating to +x) makes theta negative, and a positive theta pushes the cart to -x: +theta is a lean
 * towards +x, the side the positive force points to. check_diagrams runs cartpole() to confirm these signs and
 * checks the drawing against them (cartPole below). The Wikimedia Cart-pendulum.svg draws theta the other way,
 * so it is not reused.
 */

const LQR = "tools/sim/models/lqr_sim.py";
const M = 0.5, m = 0.2, L = 0.3, G = 9.81;

const PIVOT: Point = [170, 150];
const THETA = 25; // drawn lean, degrees towards +x
const POLE = 100;
const rad = (THETA * Math.PI) / 180;
const TIP: Point = [Math.round((PIVOT[0] + POLE * Math.sin(rad)) * 10) / 10, Math.round((PIVOT[1] - POLE * Math.cos(rad)) * 10) / 10];
const at = (deg: number, r: number): Point => {
  const t = (deg * Math.PI) / 180;
  return [Math.round((PIVOT[0] + r * Math.sin(t)) * 10) / 10, Math.round((PIVOT[1] - r * Math.cos(t)) * 10) / 10];
};

const shapes: GeoShape[] = [
  { type: "line", from: [10, 204], to: [330, 204], tone: "muted", width: 1.5 },
  { type: "rect", at: [110, 150], size: [120, 40], tone: "a" },
  { type: "text", at: [170, 175], label: "M = 0.5 kg", tone: "a" },
  { type: "circle", at: [138, 196], r: 7, tone: "muted" },
  { type: "circle", at: [202, 196], r: 7, tone: "muted" },
  { id: "upright", type: "line", from: PIVOT, to: [170, 30], tone: "muted", dashed: true, width: 1.5 },
  { type: "text", at: [170, 22], label: { zh: "θ = 0：竖直", en: "θ = 0: upright" }, tone: "muted" },
  { id: "pole", type: "line", from: PIVOT, to: TIP, tone: "ink", width: 3 },
  { type: "circle", at: TIP, r: 9, tone: "ink", fill: true },
  { type: "text", at: [TIP[0] + 14, TIP[1] + 4], label: "m = 0.2 kg", anchor: "start" },
  { type: "text", at: [at(THETA, 38)[0] + 10, at(THETA, 38)[1] + 8], label: "L = 0.3 m", anchor: "start", tone: "muted" },
  { id: "theta", type: "arc", at: PIVOT, r: 56, from: 0, to: THETA, tone: "b", arrow: true },
  { id: "thetaLabel", type: "text", at: [at(THETA / 2, 74)[0], at(THETA / 2, 74)[1] + 4], label: "+θ", tone: "b", bold: true },
  { id: "force", type: "line", from: [24, 170], to: [106, 170], tone: "ok", width: 2.5, arrow: true },
  { id: "forceLabel", type: "text", at: [62, 162], label: "+F", tone: "ok", bold: true },
  { id: "axis", type: "line", from: [24, 230], to: [304, 230], tone: "muted", width: 1.5, arrow: true },
  { id: "axisLabel", type: "text", at: [311, 235], label: "+x", anchor: "start", tone: "muted", bold: true },
  { type: "text", at: [24, 222], label: { zh: "位置 x、速度", en: "position x, speed" }, anchor: "start", tone: "muted" },
];

export const cartPoleSigns: GeoSpec = {
  kind: "geo",
  id: "cartpole-signs",
  title: { zh: "小车倒立摆的正方向约定", en: "Cart-pole sign convention" },
  caption: {
    zh: "x、速度和力 F 都以向右为正；θ 从竖直量起，向 +x 倾为正。所以 B 的第 2 项 +1/M = +2.00（正力让小车向右加速），第 4 项 −1/(ML) = −6.67（正力让摆角变负，摆向左倒）；A 中 −3.92 表示正的倾角把小车向 −x（向左）推。",
    en: "x, speed and the force F are positive to the right; θ is measured from upright and is positive leaning towards +x. So B's second entry +1/M = +2.00 (a positive force accelerates the cart right) and its fourth −1/(ML) = −6.67 (a positive force makes the angle negative, tipping the pole left); A's −3.92 means a positive lean pushes the cart towards −x (to the left).",
  },
  sources: [LQR],
  w: 340,
  h: 244,
  shapes,
  cartPole: {
    axis: "axis",
    force: "force",
    pivot: PIVOT,
    pole: "pole",
    theta: "theta",
    labels: { axis: "axisLabel", force: "forceLabel", theta: "thetaLabel" },
  },
  numbers: [
    { note: "B[1] = 1/M", value: 1 / M, expect: 2.0, tol: 0.005 },
    { note: "B[3] = -1/(M L)", value: -1 / (M * L), expect: -6.67, tol: 0.005 },
    { note: "A[1][2] = -m g / M", value: (-m * G) / M, expect: -3.92, tol: 0.005 },
    { note: "A[3][2] = (M + m) g / (M L)", value: ((M + m) * G) / (M * L), expect: 45.78, tol: 0.005 },
  ],
  facts: [
    { file: LQR, pattern: "M, m, L, G, DT, FMAX = 0\\.5, 0\\.2, 0\\.3, 9\\.81,", note: "M, m, L, g as drawn" },
    { file: LQR, pattern: "B_CP = \\[\\[0\\], \\[1 / M\\], \\[0\\], \\[-1 / \\(M \\* L\\)\\]\\]", note: "B = [0, 1/M, 0, -1/(ML)]" },
    { file: LQR, pattern: "alpha = \\(G \\* s - acc \\* c\\) / L", note: "angle from upright; cart acceleration tips it negative" },
    { file: "src/content/m5/state-space-lqr/en.mdx", pattern: "a positive force tips the pole negative", note: "lesson text matches" },
    { file: "src/content/m5/state-space-lqr/en.mdx", pattern: "a positive lean pushes the cart backwards", note: "lesson text matches" },
    { file: "src/content/m5/state-space-lqr/zh.mdx", pattern: "正的力会把杆往负方向推", note: "zh lesson text matches: a positive force tips the pole negative" },
    { file: "src/content/m5/state-space-lqr/zh.mdx", pattern: "正的角度会让小车向后加速", note: "zh lesson text matches: a positive lean pushes the cart backwards" },
  ],
};
