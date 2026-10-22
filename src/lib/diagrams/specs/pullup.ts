import type { CircuitPart, CircuitSpec, CircuitWire, DiagramFact, L10n, Point } from "../types";

/*
 * Pull-up + push button to GND, three states: floating / released (HIGH) / pressed (LOW).
 * One schematic shared by m2/arduino-io (internal pull-up switched in by INPUT_PULLUP, 20–50 kΩ,
 * ≈ 30 kΩ for the current) and m1/components (external 10 kΩ, as in the Falstad "pullupButton").
 */

const VCC = 5;

// geometry: pull-up column x 150, pin node y 176, button column x 280
const PIN: Point = [150, 176];
const BTN_X = 280;

interface Variant {
  id: string;
  internal: boolean;
  /** Ohms used for the pressed-current number. */
  rCalc: number;
  rLabel: string;
  pinLabel: L10n;
  title: L10n;
  caption: L10n;
  sources: string[];
  floating: { label: L10n; text: L10n };
  released: { label: L10n; text: L10n };
  pressed: { label: L10n; text: (mA: string) => L10n };
  expectMa: number;
  facts: DiagramFact[];
}

function pullup(v: Variant): CircuitSpec {
  const mA = (VCC / v.rCalc) * 1000;
  const mAs = mA < 1 ? mA.toFixed(2) : mA.toFixed(1);
  const parts: CircuitPart[] = [
    { id: "vcc", type: "supply", at: [150, 30], label: `${VCC} V`, labelAt: [164, 34], anchor: "start" },
    { id: "R", type: "resistor", at: [150, 124], len: 48, label: v.rLabel, labelAt: [138, 128], anchor: "end" },
    { id: "pin", type: "node", at: PIN },
    { id: "pinLabel", type: "text", at: [226, 168], label: v.pinLabel, labelAt: [226, 168], anchor: "start", mono: true, tone: "a" },
    { id: "btn", type: "button", at: [BTN_X, 206], label: { zh: "按钮", en: "button" }, labelAt: [298, 210], anchor: "start" },
    { id: "gnd", type: "ground", at: [BTN_X, 248] },
  ];
  const wires: CircuitWire[] = [
    { id: "wR", pts: [[150, 148], PIN] },
    { id: "wPin", pts: [PIN, [BTN_X, 176], [BTN_X, 188]] },
    { id: "wBtn", pts: [[BTN_X, 224], [BTN_X, 248]] },
  ];
  if (v.internal) {
    parts.push(
      { id: "chip", type: "box", at: [10, 44], size: [210, 162] },
      { id: "chipLabel", type: "text", at: [20, 62], label: "ATmega328P", labelAt: [20, 62], anchor: "start", mono: true, tone: "muted" },
      { id: "Spu", type: "switch", at: [150, 70], label: "INPUT_PULLUP", labelAt: [138, 78], anchor: "end", mono: true, tone: "b" },
      { id: "read", type: "text", at: [20, 196], label: "digitalRead(2)", labelAt: [20, 196], anchor: "start", mono: true, tone: "muted" },
    );
    wires.push({ id: "wV", pts: [[150, 30], [150, 52]] }, { id: "wSR", pts: [[150, 88], [150, 100]] });
  } else {
    wires.push({ id: "wV", pts: [[150, 30], [150, 100]] });
  }
  const closedPu = v.internal ? ["Spu"] : [];
  return {
    kind: "circuit",
    id: v.id,
    title: v.title,
    caption: v.caption,
    sources: v.sources,
    w: 350,
    h: 262,
    readoutAt: [292, 150],
    parts,
    wires,
    states: [
      {
        id: "floating",
        label: v.floating.label,
        text: v.floating.text,
        closed: [],
        hidden: v.internal ? [] : ["R", "wV", "wR"],
        tone: "danger",
        readout: { zh: "? 随机", en: "? random" },
      },
      { id: "released", label: v.released.label, text: v.released.text, closed: closedPu, tone: "a", readout: `${VCC} V → HIGH` },
      {
        id: "pressed",
        label: v.pressed.label,
        text: v.pressed.text(mAs),
        closed: [...closedPu, "btn"],
        tone: "ok",
        flow: [[150, 30], PIN, [BTN_X, 176], [BTN_X, 248]],
        readout: "0 V → LOW",
      },
    ],
    numbers: [{ note: `pressed current ${VCC} V / ${v.rCalc} Ω in mA`, value: mA, expect: v.expectMa, tol: 0.005 }],
    facts: v.facts,
  };
}

const IO_EN = "src/content/m2/arduino-io/en.mdx";
const IO_ZH = "src/content/m2/arduino-io/zh.mdx";
const BUTTON = "examples/month-2/arduino-io/button_pullup/button_pullup.ino";
const COMP_EN = "src/content/m1/components/en.mdx";
const COMP_ZH = "src/content/m1/components/zh.mdx";
const CIRCUITS = "src/lib/circuits.ts";

export const pullupInternal = pullup({
  id: "pullup-internal",
  internal: true,
  rCalc: 30000,
  rLabel: "20–50 kΩ",
  pinLabel: "D2",
  title: { zh: "INPUT_PULLUP：悬空、松开、按下", en: "INPUT_PULLUP: floating, released, pressed" },
  caption: {
    zh: "按钮一端接 D2，另一端必须接 GND。按下时的电流按内部上拉约 30 kΩ（20–50 kΩ 的中间值）计算。",
    en: "The button goes from D2 to GND, never to 5 V. The pressed current uses about 30 kΩ, the middle of the 20–50 kΩ range.",
  },
  sources: [BUTTON, IO_EN, IO_ZH],
  floating: {
    label: { zh: "INPUT：悬空", en: "INPUT: floating" },
    text: {
      zh: "pinMode(2, INPUT)：内部上拉没有接入，按钮也断开，引脚电压没有确定值，digitalRead(2) 随机返回 HIGH 或 LOW。",
      en: "pinMode(2, INPUT): the internal pull-up is disconnected and the button is open, so nothing defines the pin voltage; digitalRead(2) returns HIGH and LOW at random.",
    },
  },
  released: {
    label: { zh: "INPUT_PULLUP：松开", en: "INPUT_PULLUP: released" },
    text: {
      zh: "INPUT_PULLUP 把内部 20–50 kΩ 电阻接到 5 V。按钮断开时没有电流，电阻上没有压降，引脚为 5 V，读到 HIGH。",
      en: "INPUT_PULLUP connects the internal 20–50 kΩ resistor to 5 V. With the button open no current flows, the resistor drops nothing, and the pin sits at 5 V: HIGH.",
    },
  },
  pressed: {
    label: { zh: "按下", en: "pressed" },
    text: (mA) => ({
      zh: `按钮把 D2 接到 GND，引脚为 0 V，读到 LOW（低电平有效）。上拉电流约 5 V / 30 kΩ ≈ ${mA} mA。`,
      en: `The button ties D2 to GND, so the pin sits at 0 V and reads LOW (active low). The pull-up current is about 5 V / 30 kΩ ≈ ${mA} mA.`,
    }),
  },
  expectMa: 0.17,
  facts: [
    { file: BUTTON, pattern: "const int BUTTON_PIN = 2;", note: "button on pin 2" },
    { file: BUTTON, pattern: "pinMode\\(BUTTON_PIN, INPUT_PULLUP\\);", note: "internal pull-up enabled" },
    { file: IO_EN, pattern: "roughly 20–50 kΩ to 5 V", note: "lesson: internal pull-up 20–50 kΩ" },
    { file: IO_EN, pattern: "about 5 V / 30 kΩ ≈ 0\\.17 mA", note: "lesson: pressed current 0.17 mA" },
    { file: IO_EN, pattern: "the other side of the button must go to \\*\\*GND\\*\\*", note: "lesson: button to GND" },
    { file: IO_ZH, pattern: "大约 20–50 kΩ 接到 5 V", note: "zh lesson: internal pull-up 20–50 kΩ" },
    { file: IO_ZH, pattern: "按下时上拉电流约 5 V / 30 kΩ ≈ 0\\.17 mA", note: "zh lesson: pressed current 0.17 mA" },
    { file: IO_ZH, pattern: "按键另一端必须接 \\*\\*GND\\*\\*", note: "zh lesson: button to GND" },
  ],
});

export const pullupExternal = pullup({
  id: "pullup-external",
  internal: false,
  rCalc: 10000,
  rLabel: "10 kΩ",
  pinLabel: { zh: "引脚", en: "pin" },
  title: { zh: "上拉电阻 + 按钮：悬空、松开、按下", en: "Pull-up resistor + button: floating, released, pressed" },
  caption: {
    zh: "与下方 Falstad 电路相同：5 V、10 kΩ 上拉、按钮接 GND。Arduino 的 INPUT_PULLUP 用芯片内部的电阻代替这只 10 kΩ。",
    en: "Same circuit as the Falstad simulation below: 5 V, 10 kΩ pull-up, button to GND. Arduino's INPUT_PULLUP replaces this 10 kΩ with a resistor inside the chip.",
  },
  sources: [CIRCUITS, COMP_EN, COMP_ZH],
  floating: {
    label: { zh: "无上拉：悬空", en: "no pull-up: floating" },
    text: {
      zh: "没有上拉电阻、按钮断开：引脚悬空，像天线一样拾取干扰，读数随机。",
      en: "No pull-up and the button open: the pin floats, picks up stray charge like an antenna, and reads random values.",
    },
  },
  released: {
    label: { zh: "上拉：松开", en: "pull-up: released" },
    text: {
      zh: "10 kΩ 接到 VCC。按钮断开时没有电流，10 kΩ 上没有压降，引脚为 5 V，读到 HIGH。",
      en: "10 kΩ to VCC. With the button open no current flows, the 10 kΩ drops nothing, and the pin sits at 5 V: HIGH.",
    },
  },
  pressed: {
    label: { zh: "按下", en: "pressed" },
    text: (mA) => ({
      zh: `按钮把引脚直接接到 GND，读到 LOW（低电平有效）；电阻上流过 5 V / 10 kΩ = ${mA} mA。`,
      en: `The button ties the pin straight to GND, so it reads LOW (active low); 5 V / 10 kΩ = ${mA} mA flows through the resistor.`,
    }),
  },
  expectMa: 0.5,
  facts: [
    { file: CIRCUITS, pattern: "v 96 352 96 96 0 0 40 5 0 0 0\\.5\\nw 96 96 272 96 0\\nr 272 96 272 192 0 10000", note: "Falstad pullupButton: 5 V and 10 kΩ" },
    { file: CIRCUITS, pattern: "s 400 192 400 320 0 1 true", note: "Falstad pullupButton: momentary button from pin to GND" },
    { file: COMP_EN, pattern: "5 V / 10 kΩ = 0\\.5 mA", note: "lesson: 0.5 mA when pressed" },
    { file: COMP_EN, pattern: "\\*\\*Pull-up\\*\\*: 10 kΩ from the pin to VCC", note: "lesson: 10 kΩ pull-up" },
    { file: COMP_ZH, pattern: "5 V / 10 kΩ = 0\\.5 mA", note: "zh lesson: 0.5 mA when pressed" },
    { file: COMP_ZH, pattern: "\\*\\*上拉电阻（pull-up）\\*\\*：10 kΩ 从引脚拉到 VCC", note: "zh lesson: 10 kΩ pull-up" },
  ],
});

