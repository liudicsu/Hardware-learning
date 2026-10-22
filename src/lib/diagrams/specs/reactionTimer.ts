import type { BlockDiagramSpec } from "../types";

/*
 * State machine of examples/month-2/timing-interrupts/reaction_timer: WAITING, LIT, SHOW_RESULT.
 * random(2000, 5001) -> 2000..5000 ms; SHOW_RESULT -> WAITING after 2000 ms.
 */
const INO = "examples/month-2/timing-interrupts/reaction_timer/reaction_timer.ino";

export const reactionTimerStates: BlockDiagramSpec = {
  kind: "stateMachine",
  id: "reaction-timer-states",
  title: { zh: "反应计时器的状态机", en: "State machine of the reaction timer" },
  caption: {
    zh: "每条箭头都带一个条件，没有“在这里等待”。每次 loop() 只检查当前状态的条件，检查只需几微秒。",
    en: "Every arrow carries a condition; none says “wait here”. Each pass through loop() checks only the current state's conditions, which takes microseconds.",
  },
  sources: [INO],
  initial: "waiting",
  nodes: [
    { id: "waiting", label: "WAITING", sub: { zh: "等待（LED 灭）", en: "LED off" }, mono: true },
    { id: "lit", label: "LIT", sub: { zh: "LED 亮，开始计时", en: "LED on, timing" }, mono: true, tone: "a" },
    { id: "result", label: "SHOW_RESULT", sub: { zh: "显示结果", en: "showing result" }, mono: true, tone: "b" },
  ],
  edges: [
    { id: "wl", label: { zh: "随机 2–5 s 到时", en: "random 2–5 s elapsed" }, tone: "a" },
    { id: "wr", label: { zh: "按下按钮：\n打印 “Foul!”", en: "button pressed:\nprint “Foul!”" }, tone: "danger" },
    { id: "lr", label: { zh: "按下按钮：\n打印反应时间", en: "button pressed:\nprint reaction time" }, tone: "b" },
    { id: "rw", label: { zh: "2 s 到时", en: "2 s elapsed" }, tone: "muted" },
  ],
  layouts: {
    wide: {
      w: 640,
      h: 250,
      nodes: { waiting: [40, 85, 140, 44], lit: [450, 10, 150, 44], result: [450, 160, 150, 44] },
      edges: {
        wl: { pts: [[110, 85], [110, 32], [448, 32]], label: [280, 25] },
        wr: { pts: [[110, 129], [110, 182], [448, 182]], label: [280, 162] },
        lr: { pts: [[525, 54], [525, 158]], label: [516, 100], anchor: "end" },
        rw: { pts: [[525, 204], [525, 232], [60, 232], [60, 131]], label: [290, 226] },
      },
    },
    narrow: {
      w: 340,
      h: 370,
      nodes: { waiting: [110, 24, 140, 40], lit: [110, 170, 140, 40], result: [110, 316, 140, 40] },
      edges: {
        wl: { pts: [[180, 64], [180, 168]], label: [186, 112], anchor: "start" },
        wr: { pts: [[116, 58], [40, 58], [40, 336], [108, 336]], label: [46, 100], anchor: "start" },
        lr: { pts: [[180, 210], [180, 314]], label: [186, 255], anchor: "start" },
        rw: { pts: [[250, 336], [325, 336], [325, 44], [252, 44]], label: [319, 150], anchor: "end" },
      },
    },
  },
  facts: [
    { file: INO, pattern: "enum State \\{ WAITING, LIT, SHOW_RESULT \\};", note: "three states with these names" },
    { file: INO, pattern: "waitTime = random\\(2000, 5001\\);", note: "random wait 2000..5000 ms = 2-5 s" },
    { file: INO, pattern: "Foul! You pressed too early\\.", note: "early press prints Foul!" },
    { file: INO, pattern: "now - resultAt >= 2000\\) startRound\\(\\)", note: "back to WAITING after 2 s" },
    { file: "src/content/m2/timing-interrupts/en.mdx", pattern: "<Diagram id=\"reaction-timer-states\" />", note: "lesson shows this diagram" },
  ],
};
