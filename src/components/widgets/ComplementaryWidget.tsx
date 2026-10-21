"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { biasOffset, GYRO_BIAS, timeConstant } from "@/lib/models/complementary";
import { Chart, Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

const DEFAULT_ALPHA = 0.98;

export function ComplementaryWidget() {
  const t = useTranslations("widget");
  const [alpha, setAlpha] = useState(DEFAULT_ALPHA);
  const curve: [number, number][] = [];
  for (let a = 0.8; a <= 0.995 + 1e-9; a += 0.0025) curve.push([a, biasOffset(a)]);
  const here = biasOffset(alpha);
  return (
    <WidgetShell title={t("cfTitle")} script="tools/sim/models/filter_sim.py" onReset={() => setAlpha(DEFAULT_ALPHA)}>
      <p className="mb-3 rounded-lg border border-amber-400/20 bg-amber-400/[0.04] px-3 py-2 text-xs text-amber-200" data-testid="cf-approx">
        {t("cfApprox")}
      </p>
      <Chart
        series={[
          { points: curve, color: "#38bdf8" },
          { points: [[alpha, 0], [alpha, here]], color: "#a1a1aa", dashed: true },
        ]}
        xMin={0.8}
        xMax={1}
        yMin={0}
        yMax={3.5}
        xStep={0.05}
        yStep={0.5}
        xDigits={2}
        yDigits={1}
        xLabel="α"
        yLabel={t("cfOffsetAxis")}
        ariaLabel={t("cfTitle")}
      />
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <Readout label="τ" value={`${fixed(timeConstant(alpha), 2)} s`} testId="cf-tau" />
        <Readout label={t("cfOffset", { bias: fixed(GYRO_BIAS, 1) })} value={`${fixed(here, 1)}°`} testId="cf-offset" />
      </div>
      <div className="mt-4">
        <Slider label="α" value={alpha} min={0.8} max={0.995} step={0.005} onChange={setAlpha} format={(v) => fixed(v, 3)} testId="cf-alpha" />
      </div>
    </WidgetShell>
  );
}
