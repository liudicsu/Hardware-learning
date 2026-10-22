import type { CircuitSpec, Point } from "../types";

/*
 * m2/motors-drivers H-bridge: the five switch states of the lesson, with the values of the
 * Falstad circuit "hBridge" in src/lib/circuits.ts (6 V, 0.5 Ω supply + wiring, motor 10 Ω + 10 mH).
 * Readouts are computed here and compared with the lesson's numbers by check_diagrams.
 * TB6612FNG: AO1 (OUT1) is the left half-bridge (S1/S2), AO2 the right one (S3/S4), so
 * IN1/IN2 = H/L drives AO1 high = S1 + S4 = forward, and H/H (both outputs low) = S2 + S4 = brake.
 */

const V = 6; // supply, V
const RS = 0.5; // supply and wiring resistance, Ω
const RM = 10; // motor resistance, Ω
const LM = 0.01; // motor inductance, H

const I_RUN = V / (RM + RS); // 0.571 A
const I_SHOOT = V / RS; // 12 A
const TAU_MS = (LM / RM) * 1000; // 1 ms
const DECAY_1MS = Math.exp(-1 / TAU_MS); // 0.368 of the current left after 1 ms
const fmt = (x: number, d: number) => x.toFixed(d);

const CIRCUITS = "src/lib/circuits.ts";
const EN = "src/content/m2/motors-drivers/en.mdx";
const ZH = "src/content/m2/motors-drivers/zh.mdx";
const ONE_REV = "examples/month-2/motors-drivers/one_rev/one_rev.ino";

// geometry: top rail y 44, motor y 154, bottom rail y 264; left leg x 90, right leg x 250
const TOP: Point[] = [[170, 30], [170, 44]];
const GND: Point[] = [[170, 264], [170, 276]];

export const hbridgeCurrentPath: CircuitSpec = {
  kind: "circuit",
  id: "hbridge-current-path",
  title: { zh: "H 桥的五种开关状态与电流路径", en: "H-bridge: five switch states and the current path" },
  caption: {
    zh: `开关位置与课文和 Falstad 电路一致（S1 左上、S2 左下、S3 右上、S4 右下）；电源 ${V} V，电源与导线电阻 ${RS} Ω，电机 ${RM} Ω + ${LM * 1000} mH。TB6612FNG 的 AO1（OUT1）是左桥臂（S1/S2），AO2 是右桥臂（S3/S4），按这个对应关系，驱动芯片的真值表正好对上这里的状态。彩色虚线是常规电流（从 + 到 −）。`,
    en: `Switch positions as in the lesson and the Falstad circuit (S1 top-left, S2 bottom-left, S3 top-right, S4 bottom-right); ${V} V supply, ${RS} Ω supply and wiring resistance, motor ${RM} Ω + ${LM * 1000} mH. On the TB6612FNG, AO1 (OUT1) is the left half-bridge (S1/S2) and AO2 the right one (S3/S4); with that mapping the driver's truth table matches these states. The coloured dashes show conventional current (+ to −).`,
  },
  sources: [CIRCUITS, EN, ZH, ONE_REV],
  w: 340,
  h: 312,
  readoutAt: [170, 204],
  parts: [
    { id: "vplus", type: "supply", at: [170, 30], label: `+V = ${V} V`, labelAt: [184, 34], anchor: "start" },
    { id: "S1", type: "switch", at: [90, 94], label: "S1", labelAt: [70, 98], anchor: "end" },
    { id: "S2", type: "switch", at: [90, 214], label: "S2", labelAt: [70, 218], anchor: "end" },
    { id: "S3", type: "switch", at: [250, 94], label: "S3", labelAt: [280, 98], anchor: "start" },
    { id: "S4", type: "switch", at: [250, 214], label: "S4", labelAt: [280, 218], anchor: "start" },
    { id: "motor", type: "motor", at: [170, 154], dir: "h", len: 40 },
    { id: "nL", type: "node", at: [90, 154] },
    { id: "nR", type: "node", at: [250, 154] },
    { id: "nT", type: "node", at: [170, 44] },
    { id: "nB", type: "node", at: [170, 264] },
    { id: "gnd", type: "ground", at: [170, 276] },
    { id: "ao1", type: "text", at: [98, 146], label: "AO1", labelAt: [98, 146], anchor: "start", mono: true, tone: "a" },
    { id: "ao2", type: "text", at: [242, 146], label: "AO2", labelAt: [242, 146], anchor: "end", mono: true, tone: "a" },
    { id: "legL", type: "text", at: [90, 294], label: { zh: "AO1（OUT1）\n左桥臂", en: "AO1 (OUT1)\nleft half-bridge" }, labelAt: [90, 294], tone: "a" },
    { id: "legR", type: "text", at: [250, 294], label: { zh: "AO2（OUT2）\n右桥臂", en: "AO2 (OUT2)\nright half-bridge" }, labelAt: [250, 294], tone: "a" },
  ],
  wires: [
    { id: "wV", pts: TOP },
    { id: "wTL", pts: [[170, 44], [90, 44]] },
    { id: "wTR", pts: [[170, 44], [250, 44]] },
    { id: "wS1a", pts: [[90, 44], [90, 76]] },
    { id: "wS1b", pts: [[90, 112], [90, 154]] },
    { id: "wS2a", pts: [[90, 154], [90, 196]] },
    { id: "wS2b", pts: [[90, 232], [90, 264]] },
    { id: "wS3a", pts: [[250, 44], [250, 76]] },
    { id: "wS3b", pts: [[250, 112], [250, 154]] },
    { id: "wS4a", pts: [[250, 154], [250, 196]] },
    { id: "wS4b", pts: [[250, 232], [250, 264]] },
    { id: "wML", pts: [[90, 154], [150, 154]] },
    { id: "wMR", pts: [[190, 154], [250, 154]] },
    { id: "wBL", pts: [[90, 264], [170, 264]] },
    { id: "wBR", pts: [[250, 264], [170, 264]] },
    { id: "wG", pts: GND },
  ],
  states: [
    {
      id: "off",
      label: { zh: "全部断开", en: "All open" },
      closed: [],
      tone: "muted",
      readout: "0 A",
      text: {
        zh: "四个开关都断开，没有电流。TB6612：IN1 = L、IN2 = L → 停止（滑行），电机自由减速。",
        en: "All four switches open, no current. TB6612: IN1 = L, IN2 = L → stop (coast); the motor spins down freely.",
      },
    },
    {
      id: "forward",
      label: { zh: "S1+S4 正转", en: "S1+S4 forward" },
      closed: ["S1", "S4"],
      tone: "a",
      flow: [...TOP, [90, 44], [90, 154], [250, 154], [250, 264], [170, 264], [170, 276]],
      readout: { zh: `电机电流 ≈ +${fmt(I_RUN, 2)} A`, en: `motor ≈ +${fmt(I_RUN, 2)} A` },
      text: {
        zh: `电流从 +V 经 S1、电机（AO1 → AO2）、S4 流到 GND：${V} V / (${RM} Ω + ${RS} Ω) ≈ ${fmt(I_RUN, 2)} A。TB6612：IN1 = H、IN2 = L（AO1 高、AO2 低）。`,
        en: `Current flows from +V through S1, the motor (AO1 → AO2) and S4 to GND: ${V} V / (${RM} Ω + ${RS} Ω) ≈ ${fmt(I_RUN, 2)} A. TB6612: IN1 = H, IN2 = L (AO1 high, AO2 low).`,
      },
    },
    {
      id: "reverse",
      label: { zh: "S2+S3 反转", en: "S2+S3 reverse" },
      closed: ["S2", "S3"],
      tone: "b",
      flow: [...TOP, [250, 44], [250, 154], [90, 154], [90, 264], [170, 264], [170, 276]],
      readout: { zh: `电机电流 ≈ −${fmt(I_RUN, 2)} A`, en: `motor ≈ −${fmt(I_RUN, 2)} A` },
      text: {
        zh: `电流从 +V 经 S3、电机（AO2 → AO1）、S2 流到 GND：大小相同，方向相反。TB6612：IN1 = L、IN2 = H。`,
        en: `Current flows from +V through S3, the motor (AO2 → AO1) and S2 to GND: same size, opposite direction. TB6612: IN1 = L, IN2 = H.`,
      },
    },
    {
      id: "brake",
      label: { zh: "S2+S4 刹车", en: "S2+S4 brake" },
      closed: ["S2", "S4"],
      tone: "ok",
      flow: [[90, 154], [250, 154], [250, 264], [90, 264], [90, 154]],
      loopReason: "brake: the current circulates in the lower loop S2–motor–S4 and never passes the supply; the loop is closed (first point = last point)",
      readout: { zh: "从静止开始：0 A", en: "from rest: 0 A" },
      text: {
        zh: `电机两端都接到 GND，从静止开始电流为 0。在这个模型（${RM} Ω + ${LM * 1000} mH）里，刚从正转切过来时，电流按箭头方向沿下方回路继续环流并衰减，τ = L / R = ${fmt(TAU_MS, 0)} ms，1 ms 后约剩 ${fmt(DECAY_1MS * 100, 0)} %（比三分之一稍多）。真实电机如果还在转，电机此时是一台发电机：反电动势会在同一回路里驱动一股反向电流，让电机制动直到停下。TB6612：IN1 = H、IN2 = H → 短路刹车（两个输出都为低），即 one_rev.ino 的 brake()。`,
        en: `Both motor terminals are tied to GND; from rest the current is 0. In this model (${RM} Ω + ${LM * 1000} mH), right after forward driving the current keeps circulating around this lower loop in the direction of the arrows and dies away, τ = L / R = ${fmt(TAU_MS, 0)} ms, about ${fmt(DECAY_1MS * 100, 0)} % (slightly more than a third) after 1 ms. A real motor that is still turning works as a generator: its back-EMF drives a reverse current around the same loop, and that current brakes it until it stops. TB6612: IN1 = H, IN2 = H → short brake (both outputs low), as brake() in one_rev.ino.`,
      },
    },
    {
      id: "shoot",
      label: { zh: "S1+S2 直通", en: "S1+S2 shoot-through" },
      closed: ["S1", "S2"],
      tone: "danger",
      flow: [...TOP, [90, 44], [90, 264], [170, 264], [170, 276]],
      readout: { zh: `≈ ${fmt(I_SHOOT, 0)} A：+V → GND\n电机 0 A`, en: `≈ ${fmt(I_SHOOT, 0)} A: +V → GND\nmotor 0 A` },
      text: {
        zh: `禁止状态：+V 经 S1、S2 直接接到 GND，电流约 ${V} V / ${RS} Ω = ${fmt(I_SHOOT, 0)} A，只受电源与导线电阻限制，电机拿到 0 A。S3 + S4 同理。TB6612 没有任何输入组合会产生这个状态。`,
        en: `Forbidden: +V is connected straight to GND through S1 and S2, about ${V} V / ${RS} Ω = ${fmt(I_SHOOT, 0)} A, limited only by the supply and wiring resistance, and the motor gets 0 A. S3 + S4 is the same. No TB6612 input combination produces this state.`,
      },
    },
  ],
  numbers: [
    { note: "forward/reverse current 6 V / 10.5 Ω (lesson: about 0.57 A)", value: I_RUN, expect: 0.57, tol: 0.005 },
    { note: "shoot-through current 6 V / 0.5 Ω (lesson: about 12 A)", value: I_SHOOT, expect: 12, tol: 0.01 },
    { note: "brake decay: after 1 ms, e^(-1 ms / τ) (lesson: about 37 %, slightly more than a third)", value: DECAY_1MS, expect: 0.37, tol: 0.005 },
  ],
  facts: [
    { file: CIRCUITS, pattern: "v 96 400 96 64 0 0 40 6 0 0 0\\.5\\nw 96 64 128 64 0\\nr 128 64 224 64 0 0\\.5", note: "Falstad hBridge: 6 V supply and 0.5 Ω supply/wiring resistance" },
    { file: CIRCUITS, pattern: "r 304 224 368 224 0 10\\n", note: "Falstad hBridge: motor 10 Ω" },
    { file: CIRCUITS, pattern: "l 384 224 448 224 0 0\\.01 0", note: "Falstad hBridge: motor 10 mH" },
    { file: CIRCUITS, pattern: "x 240 128 272 128 4 16 S1\\nx 240 288 272 288 4 16 S2\\nx 432 128 464 128 4 16 S3\\nx 432 288 464 288 4 16 S4", note: "Falstad labels: S1 top-left, S2 bottom-left, S3 top-right, S4 bottom-right" },
    { file: EN, pattern: "S1 is top-left, S2 bottom-left, S3 top-right, S4 bottom-right", note: "lesson switch positions" },
    { file: EN, pattern: "the ammeter reads about \\+0\\.57 A", note: "lesson: +0.57 A forward" },
    { file: EN, pattern: "about 12 A flows straight from \\+V to GND", note: "lesson: 12 A shoot-through" },
    { file: EN, pattern: "\\| H \\| L \\| PWM \\| Forward at that duty \\|\\n\\| L \\| H \\| PWM \\| Reverse \\|\\n\\| H \\| H \\| any \\| Short brake \\(fast stop\\) \\|\\n\\| L \\| L \\| any \\| Stop \\(coast\\) \\|", note: "lesson TB6612 table" },
    { file: ONE_REV, pattern: "void brake\\(\\) \\{\\s*// TB6612: IN1 = IN2 = HIGH shorts the motor", note: "one_rev.ino brake() = IN1 = IN2 = HIGH" },
    { file: ZH, pattern: "S1 在左上，S2 在左下，S3 在右上，S4 在右下", note: "zh lesson switch positions" },
    { file: ZH, pattern: "电流表读数约 \\+0\\.57 A", note: "zh lesson: +0.57 A forward" },
    { file: ZH, pattern: "约 12 A 直接从 \\+V 流到 GND", note: "zh lesson: 12 A shoot-through" },
    { file: ZH, pattern: "\\| H \\| L \\| PWM \\| 以该占空比正转 \\|\\n\\| L \\| H \\| PWM \\| 反转 \\|\\n\\| H \\| H \\| 任意 \\| 短路刹车（快速停下） \\|\\n\\| L \\| L \\| 任意 \\| 停止（滑行） \\|", note: "zh lesson TB6612 table" },
    { file: ZH, pattern: "AO1 就是上面 H 桥图里的左桥臂（S1/S2）", note: "zh lesson: AO1 (OUT1) = left half-bridge" },
    { file: EN, pattern: "in this model it falls to about 37 %, slightly more than a third, in 1 ms", note: "lesson: 37 % after 1 ms" },
    { file: ZH, pattern: "1 ms 时大约还剩 37 %，比三分之一稍多", note: "zh lesson: 37 % after 1 ms" },
    { file: EN, pattern: "its back-EMF drives a current the other way round the same loop", note: "lesson: back-EMF drives a reverse braking current" },
    { file: ZH, pattern: "反电动势会在同一个回路里驱动一股反向电流", note: "zh lesson: back-EMF drives a reverse braking current" },
    { file: EN, pattern: "AO1 is the left half-bridge of the H-bridge diagram above \\(S1/S2\\)", note: "lesson: AO1 (OUT1) = left half-bridge" },
    { file: "examples/month-2/motors-drivers/README.md", pattern: "\\| AO1 / AO2 \\| motor leads", note: "the motor is on AO1/AO2" },
  ],
};
