import type { L10n } from "./types";

/**
 * Course glossary. One entry per term; `lesson` is the slug of the lesson that first explains it.
 * zh and en names here are the canonical translations used across the site.
 * Definitions are short, precise and use the course's own hardware (SO-101, Uno, ESP32-S3, m4bot).
 */
export interface GlossaryEntry {
  id: string;
  term: L10n;
  def: L10n;
  lesson: string;
}

export const glossary: GlossaryEntry[] = [
  {
    id: "gnd",
    term: { zh: "地（GND）", en: "ground (GND)" },
    def: {
      zh: "电路中约定为 0 V 的参考节点，所有电压都相对它测量。Uno 与电机驱动板必须共地，否则信号电平没有共同参考。",
      en: "The node defined as 0 V; every voltage in the circuit is measured relative to it. An Uno and a motor driver must share GND, otherwise their logic levels have no common reference.",
    },
    lesson: "ohms-law",
  },
];

export function getTerm(id: string): GlossaryEntry | undefined {
  return glossary.find((g) => g.id === id);
}
