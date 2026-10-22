import type { TimingSpec, Tone } from "../types";

/*
 * m2/arduino-io PWM: analogWrite(9, value) for value = 64, 128, 191 over two periods, with the
 * average voltage V_avg = value / 255 × 5 V drawn as a dashed line.
 * Column edges sit at the switching points 0, 64, 128, 191, 255 (of 255 per period), so every trace
 * is HIGH for exactly value/255 of the period; check_diagrams compares that drawn fraction, the
 * averages and the timer frequencies with the lesson.
 * Uno timer clocks: 16 MHz / 64 prescaler; pins 3, 9, 10, 11 phase-correct PWM (÷ 510) = 490.2 Hz,
 * pins 5, 6 fast PWM (÷ 256) = 976.6 Hz (the lesson's "about 980 Hz").
 */

const VCC = 5;
const VALUES = [64, 128, 191];
const TONES: Tone[] = ["a", "b", "ok"];
const BOUNDS = [64, 128, 191, 255]; // end of each column within one period, in 1/255
const PERIODS = 2;

const F_CPU = 16e6;
const PRESCALE = 64;
const F_PIN9 = F_CPU / PRESCALE / 510; // Hz
const F_PIN5 = F_CPU / PRESCALE / 256; // Hz
const T_PIN9_MS = 1000 / F_PIN9;

const periodCols = BOUNDS.map((b, k) => b - (k ? BOUNDS[k - 1] : 0)); // 64, 64, 63, 64
const columns = Array.from({ length: PERIODS }, () => periodCols).flat();
const levelsFor = (v: number) => Array.from({ length: PERIODS }, () => BOUNDS.map((b) => (b <= v ? 1 : 0))).flat();
/** Fraction of the drawing's total time that a trace is HIGH, computed from the columns it is drawn with. */
const drawnDuty = (v: number) => {
  const lv = levelsFor(v);
  return columns.reduce((acc, w, i) => acc + (lv[i] ? w : 0), 0) / columns.reduce((a, b) => a + b, 0);
};
const duty = (v: number) => v / 255;
const vavg = (v: number) => duty(v) * VCC;
const pct = (v: number) => (duty(v) * 100).toFixed(1);
const volts = (v: number) => vavg(v).toFixed(2);

const EN = "src/content/m2/arduino-io/en.mdx";
const POT = "examples/month-2/arduino-io/pot_pwm/pot_pwm.ino";

export const pwmDuty: TimingSpec = {
  kind: "timing",
  id: "pwm-duty-average",
  title: { zh: "PWM：同一频率，三种占空比及其平均电压", en: "PWM: one frequency, three duty cycles and their average voltage" },
  caption: {
    zh: `每条波形都只在 0 V 和 ${VCC} V 之间切换，变化的只是每个周期里 HIGH 所占的比例。比 PWM 周期反应慢的负载响应的是虚线所示的平均值：V_avg = value / 255 × ${VCC} V。`,
    en: `Each trace only switches between 0 V and ${VCC} V; what changes is the fraction of every period spent HIGH. A load that responds more slowly than the PWM period follows the dashed average: V_avg = value / 255 × ${VCC} V.`,
  },
  sources: [POT, EN],
  columns,
  signals: VALUES.map((v, k) => ({
    name: String(v),
    levels: levelsFor(v),
    tone: TONES[k],
    average: { level: duty(v), label: `${volts(v)} V` },
  })),
  spans: [
    {
      from: 0,
      to: BOUNDS.length - 1,
      label: { zh: `周期 T = 1 / 490 Hz ≈ ${T_PIN9_MS.toFixed(2)} ms`, en: `period T = 1 / 490 Hz ≈ ${T_PIN9_MS.toFixed(2)} ms` },
    },
  ],
  axisLabel: { zh: "引脚 9 上的 analogWrite(9, value)，两个周期", en: "analogWrite(9, value) on pin 9, two periods" },
  steps: [
    ...VALUES.map((v, k) => ({
      signals: [k],
      label: {
        zh: `analogWrite(9, ${v})：每个周期有 ${v} / 255 = ${pct(v)} % 的时间为 HIGH；V_avg = ${duty(v).toFixed(3)} × ${VCC} V ≈ ${volts(v)} V。`,
        en: `analogWrite(9, ${v}): HIGH for ${v} / 255 = ${pct(v)} % of every period; V_avg = ${duty(v).toFixed(3)} × ${VCC} V ≈ ${volts(v)} V.`,
      },
    })),
    {
      label: {
        zh: `频率由定时器决定：引脚 3、9、10、11 约 490 Hz（周期约 2 ms），引脚 5、6 约 980 Hz（周期约 1 ms）。同一个 value 在两种引脚上的占空比和平均电压相同。`,
        en: `The timers set the frequency: about 490 Hz on pins 3, 9, 10 and 11 (period about 2 ms), about 980 Hz on pins 5 and 6 (period about 1 ms). The same value gives the same duty cycle and average on both.`,
      },
    },
  ],
  numbers: [
    ...VALUES.map((v) => ({ note: `drawn HIGH fraction of the ${v} trace = ${v}/255`, value: drawnDuty(v), expect: v / 255, tol: 1e-9 })),
    { note: "duty of 64 (lesson quiz: 25.1 %)", value: duty(64) * 100, expect: 25.1, tol: 0.05 },
    { note: "V_avg of 128 (lesson: 2.51 V)", value: vavg(128), expect: 2.51, tol: 0.005 },
    { note: "V_avg of 191 (lesson quiz: 3.745 V)", value: vavg(191), expect: 3.745, tol: 0.0005 },
    { note: "V_avg of 64 = 64/255 × 5 V ≈ 1.25 V", value: vavg(64), expect: 1.255, tol: 0.0005 },
    { note: "pins 3/9/10/11: 16 MHz / 64 / 510 (lesson: about 490 Hz)", value: F_PIN9, expect: 490, tol: 0.5 },
    { note: "pins 5/6: 16 MHz / 64 / 256 (lesson: about 980 Hz)", value: F_PIN5, expect: 980, tol: 5 },
    { note: "period on pin 9 in ms (lesson: roughly 2 ms)", value: T_PIN9_MS, expect: 2.04, tol: 0.001 },
  ],
  facts: [
    { file: POT, pattern: "const int LED_PIN = 9;", note: "pot_pwm.ino drives pin 9" },
    { file: EN, pattern: "about \\*\\*490 Hz\\*\\* on pins 3, 9, 10 and 11, and about \\*\\*980 Hz\\*\\* on pins 5 and 6", note: "lesson PWM frequencies" },
    { file: EN, pattern: "V_avg = \\(value / 255\\) × 5 V", note: "lesson formula" },
    { file: EN, pattern: "V_avg = 0\\.50196 × 5 V = 2\\.510 V ≈ 2\\.51 V", note: "lesson worked example 128 → 2.51 V" },
    { file: EN, pattern: "Duty = 64 / 255 = 0\\.25098 ≈ 25\\.1 %", note: "lesson quiz 64 → 25.1 %" },
    { file: EN, pattern: "V_avg = 0\\.74902 × 5 V = 3\\.745 V ≈ 3\\.75 V", note: "lesson quiz 191 → 3.75 V" },
  ],
};
