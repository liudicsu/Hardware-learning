"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { wilson } from "@/lib/models/wilson";
import { Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

// The lesson's first worked example: 61 successes out of 100.
const DEFAULTS = { k: 61, n: 100 };

function Bar({ lo, hi, p }: { lo: number; hi: number; p: number }) {
  const x = (v: number) => 10 + v * 580;
  return (
    <svg viewBox="0 0 600 44" className="h-auto w-full" role="img" aria-label={`${fixed(lo * 100, 1)} .. ${fixed(hi * 100, 1)} %`}>
      <line x1={10} y1={18} x2={590} y2={18} stroke="#3f3f46" strokeWidth="2" />
      <rect x={x(lo)} y={10} width={Math.max(1, x(hi) - x(lo))} height={16} rx={3} fill="rgba(56,189,248,0.35)" stroke="#38bdf8" />
      <line x1={x(p)} y1={6} x2={x(p)} y2={30} stroke="#f4f4f5" strokeWidth="2" />
      {[0, 0.25, 0.5, 0.75, 1].map((v) => (
        <text key={v} x={x(v)} y={42} textAnchor="middle" fontSize="12" fill="#71717a">
          {fixed(v * 100, 0)} %
        </text>
      ))}
    </svg>
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
