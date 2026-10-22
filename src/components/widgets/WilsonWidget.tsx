"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { wilson } from "@/lib/models/wilson";
import { Readout } from "./Chart";
import { useBoxWidth } from "./useBoxWidth";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

// The lesson's first worked example: 61 successes out of 100.
const DEFAULTS = { k: 61, n: 100 };

// The viewBox follows the box width (up to 600 units), so the 12-unit tick labels render at 12 px on a phone.
function Bar({ lo, hi, p }: { lo: number; hi: number; p: number }) {
  const [box, boxW] = useBoxWidth<HTMLDivElement>();
  // Before the box is measured (server HTML, first paint, JS disabled) draw at the minimum width, so the labels can only scale up.
  const W = boxW ? Math.max(240, Math.min(600, Math.round(boxW))) : 240;
  const M = 22; // room for half of a "100 %" label at each end
  const x = (v: number) => M + v * (W - 2 * M);
  return (
    <div ref={box} className="w-full" data-widget="wilson-bar">
      <svg viewBox={`0 0 ${W} 44`} className="h-auto w-full" role="img" aria-label={`${fixed(lo * 100, 1)} .. ${fixed(hi * 100, 1)} %`}>
        <line x1={M} y1={18} x2={W - M} y2={18} stroke="#3f3f46" strokeWidth="2" />
        <rect x={x(lo)} y={10} width={Math.max(1, x(hi) - x(lo))} height={16} rx={3} fill="rgba(56,189,248,0.35)" stroke="#38bdf8" />
        <line x1={x(p)} y1={6} x2={x(p)} y2={30} stroke="#f4f4f5" strokeWidth="2" />
        {[0, 0.25, 0.5, 0.75, 1].map((v) => (
          <text key={v} x={x(v)} y={42} textAnchor="middle" fontSize="12" fill="#71717a">
            {fixed(v * 100, 0)} %
          </text>
        ))}
      </svg>
    </div>
  );
}

export function WilsonWidget() {
  const t = useTranslations("widget");
  const [k, setK] = useState(DEFAULTS.k);
  const [n, setN] = useState(DEFAULTS.n);
  const kk = Math.min(k, n);
  const [lo, hi] = wilson(kk, n);
  return (
    <WidgetShell
      title={t("wilsonTitle")}
      script="examples/month-6/policy-evaluation/eval_report.py"
      onReset={() => {
        setK(DEFAULTS.k);
        setN(DEFAULTS.n);
      }}
    >
      <Bar lo={lo} hi={hi} p={kk / n} />
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <Readout label={t("wilsonRate")} value={`${kk}/${n} = ${fixed((100 * kk) / n, 1)} %`} testId="wilson-rate" />
        <Readout label={t("wilsonInterval")} value={`${fixed(100 * lo, 1)} .. ${fixed(100 * hi, 1)} %`} testId="wilson-interval" />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Slider label={t("wilsonN")} value={n} min={1} max={200} step={1} onChange={(v) => { setN(v); if (k > v) setK(v); }} testId="wilson-n" />
        <Slider label={t("wilsonK")} value={kk} min={0} max={n} step={1} onChange={setK} testId="wilson-k" />
      </div>
    </WidgetShell>
  );
}
