import type { BlockDiagramSpec, DiagramFact, L10n, Layout } from "../types";

/*
 * Cascade (balancer) block diagrams for m3/pid-control and m2/first-robots.
 * Inner loop: PERIOD_US = 5000 -> 200 Hz. Outer loop: every OUTER_EVERY = 8 ticks -> 25 Hz.
 * Setpoint clamp: SETPOINT_MAX = 3.0 deg. Checked against balancer_cascade.ino by check_diagrams.
 */

const CASCADE_INO = "examples/month-3/pid-control/balancer_cascade/balancer_cascade.ino";

const wide: Layout = {
  w: 750,
  h: 172,
  nodes: {
    target: [0, 26, 100, 38],
    outer: [118, 22, 172, 46],
    setpoint: [308, 26, 100, 38],
    inner: [426, 22, 172, 46],
    motors: [616, 22, 130, 46],
  },
  edges: {
    e1: { pts: [[100, 45], [116, 45]] },
    e2: { pts: [[290, 45], [306, 45]] },
    e3: { pts: [[408, 45], [424, 45]] },
    e4: { pts: [[598, 45], [614, 45]] },
    pitch: { pts: [[660, 68], [660, 110], [512, 110], [512, 70]], label: [586, 104] },
    speed: { pts: [[716, 68], [716, 160], [204, 160], [204, 70]], label: [460, 140] },
  },
};

const narrow: Layout = {
  w: 340,
  h: 270,
  nodes: {
    target: [15, 2, 172, 30],
    outer: [15, 42, 172, 44],
    setpoint: [15, 104, 172, 32],
    inner: [15, 156, 172, 44],
    motors: [15, 222, 172, 36],
  },
  edges: {
    e1: { pts: [[101, 32], [101, 40]] },
    e2: { pts: [[101, 86], [101, 102]] },
    e3: { pts: [[101, 138], [101, 154]] },
    e4: { pts: [[101, 200], [101, 220]] },
    pitch: { pts: [[187, 240], [222, 240], [222, 178], [189, 178]], label: [228, 213], anchor: "start" },
    speed: { pts: [[187, 250], [325, 250], [325, 64], [189, 64]], label: [256, 42] },
  },
};

const sharedFacts: DiagramFact[] = [
  { file: CASCADE_INO, pattern: "PERIOD_US = 5000;\\s*// inner loop: 200 Hz", note: "inner loop 5 ms = 200 Hz" },
  { file: CASCADE_INO, pattern: "OUTER_EVERY = 8;", note: "outer loop every 8th tick: 200 / 8 = 25 Hz" },
  { file: CASCADE_INO, pattern: "SETPOINT_MAX = 3\\.0;", note: "setpoint clamped to +-3 deg" },
  { file: CASCADE_INO, pattern: "constrain\\(KP_S \\* error \\+ KI_S \\* integral, -SETPOINT_MAX, SETPOINT_MAX\\)", note: "outer loop is PI and its output is the clamped setpoint" },
];

function cascade(
  id: string,
  title: L10n,
  labels: { target: [L10n, L10n?]; outer: L10n; setpoint: [L10n, L10n]; inner: L10n; motors: L10n; pitch: L10n; speed: L10n },
  extra: { sources: string[]; facts: DiagramFact[]; caption?: L10n; setpointMono?: boolean; outerStep: L10n },
): BlockDiagramSpec {
  return {
    kind: "block",
    id,
    title,
    caption: extra.caption,
    sources: extra.sources,
    nodes: [
      { id: "target", label: labels.target[0], sub: labels.target[1], shape: "text", tone: "b" },
      { id: "outer", label: { zh: "外环 PI", en: "outer PI" }, sub: labels.outer, tone: "b" },
      { id: "setpoint", label: labels.setpoint[0], sub: labels.setpoint[1], shape: "text", tone: "b", mono: extra.setpointMono },
      { id: "inner", label: { zh: "内环 PD", en: "inner PD" }, sub: labels.inner, tone: "a" },
      { id: "motors", label: labels.motors, tone: "ink" },
    ],
    edges: [
      { id: "e1", tone: "b" },
      { id: "e2", tone: "b" },
      { id: "e3", tone: "b" },
      { id: "e4", tone: "a" },
      { id: "pitch", label: labels.pitch, tone: "a" },
      { id: "speed", label: labels.speed, tone: "b" },
    ],
    layouts: { wide, narrow },
    steps: [
      {
        label: {
          zh: "内环：每 5 ms（200 Hz）读一次俯仰角，驱动电机保持倾角设定值。",
          en: "Inner loop: every 5 ms (200 Hz) it reads the pitch and drives the motors to hold the pitch setpoint.",
        },
        highlight: ["setpoint", "e3", "inner", "e4", "motors", "pitch"],
      },
      {
        label: extra.outerStep,
        highlight: ["target", "e1", "outer", "e2", "setpoint", "motors", "speed"],
      },
    ],
    facts: [...sharedFacts, ...extra.facts],
  };
}

export const pidCascade = cascade(
  "pid-cascade",
  { zh: "串级控制：外环（速度）给内环（俯仰角）设定值", en: "Cascade: the outer (speed) loop sets the inner (pitch) loop's target" },
  {
    target: [{ zh: "目标速度", en: "target speed" }],
    outer: "25 Hz",
    setpoint: [{ zh: "倾角设定值", en: "pitch setpoint" }, "±3°"],
    inner: "200 Hz",
    motors: { zh: "电机", en: "motors" },
    pitch: { zh: "俯仰角（IMU）", en: "pitch (IMU)" },
    speed: { zh: "轮速（编码器）", en: "wheel speed\n(encoders)" },
  },
  {
    sources: [CASCADE_INO, "tools/sim/models/cascade_sim.py"],
    outerStep: {
      zh: "外环：每 8 个内环周期（25 Hz）读一次轮速，只改变倾角设定值，并限幅在 ±3° 以内；它不直接驱动电机。",
      en: "Outer loop: every 8th inner tick (25 Hz) it reads the wheel speed and only moves the pitch setpoint, clamped to ±3°; it never drives the motors directly.",
    },
    facts: [
      { file: "src/content/m3/pid-control/en.mdx", pattern: "Here the inner loop is 200 Hz and the outer loop is 25 Hz, eight times slower\\.", note: "lesson text matches" },
      { file: "src/content/m3/pid-control/en.mdx", pattern: "clamped to ±3° of lean", note: "lesson text matches" },
    ],
  },
);

export const firstRobotsCascade = cascade(
  "first-robots-cascade",
  { zh: "可选挑战：在平衡环外再加一个速度环", en: "Optional challenge: a speed loop around the balance loop" },
  {
    target: [{ zh: "目标速度", en: "target speed" }, "0"],
    outer: { zh: "速度误差 · 25–50 Hz", en: "speed error · 25–50 Hz" },
    setpoint: ["SETPOINT", { zh: "限幅 ±3°", en: "clamped to ±3°" }],
    inner: { zh: "角度误差 · 200 Hz", en: "angle error · 200 Hz" },
    motors: { zh: "电机 PWM", en: "motor PWM" },
    pitch: { zh: "滤波后的俯仰角", en: "pitch from\nthe filter" },
    speed: { zh: "轮速（编码器）", en: "wheel speed\n(encoders)" },
  },
  {
    sources: ["examples/month-2/first-robots/balancer/balancer.ino", CASCADE_INO],
    setpointMono: true,
    outerStep: {
      zh: "外环：每 4–8 个内环周期（25–50 Hz）读一次轮速，只改变 SETPOINT，并限幅在 ±3° 以内；它不直接驱动电机。",
      en: "Outer loop: every 4th to 8th inner tick (25–50 Hz) it reads the wheel speed and only changes SETPOINT, clamped to ±3°; it never drives the motors directly.",
    },
    caption: {
      zh: "外环每 4–8 个 200 Hz 节拍运行一次（25–50 Hz），轮速在每个外环节拍测量一次。第 3 个月 PID 一课的完整固件取每 8 个节拍（25 Hz）。",
      en: "The outer loop runs every 4th to 8th 200 Hz tick (25–50 Hz) and measures wheel speed once per outer tick. The finished firmware in Month 3's PID lesson uses every 8th tick (25 Hz).",
    },
    facts: [
      { file: "examples/month-2/first-robots/balancer/balancer.ino", pattern: "PERIOD_US = 5000;\\s*// 200 Hz control loop", note: "inner loop 200 Hz in the month-2 balancer" },
      { file: "src/content/m2/first-robots/en.mdx", pattern: "every 4th to 8th tick, so 25–50 Hz", note: "lesson text: 200/8 = 25, 200/4 = 50" },
      { file: "examples/month-2/first-robots/balancer/balancer.ino", pattern: "const float SETPOINT = 0\\.0;", note: "the month-2 balancer names the pitch target SETPOINT" },
    ],
  },
);
