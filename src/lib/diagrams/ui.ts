import type { Locale } from "./types";

/** Interface strings of the diagram frame and step controls (kept here so specs and UI share one locale source). */
export const DIAGRAM_UI: Record<Locale, { prev: string; next: string; all: string; step: string; source: string; states: string; packets: string; byte: string; field: string; meaning: string }> = {
  zh: { prev: "上一步", next: "下一步", all: "全部", step: "第 {i} / {n} 步", source: "依据", states: "电路状态", packets: "数据包", byte: "字节", field: "字段", meaning: "含义" },
  en: { prev: "Previous", next: "Next", all: "All", step: "Step {i} / {n}", source: "Source", states: "Circuit states", packets: "Packets", byte: "Byte", field: "Field", meaning: "Meaning" },
};
