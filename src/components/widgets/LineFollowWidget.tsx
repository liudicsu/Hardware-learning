"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { describe, run } from "@/lib/models/lineFollow";
import { Chart, Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

const DEFAULTS = { kp: 0.0003, kd: 0.0002 };

export function LineFollowWidget() {
  const t = useTranslations("widget");
  const [kp, setKp] = useState(DEFAULTS.kp);
  const [kd, setKd] = useState(DEFAULTS.kd);
  const log = useMemo(() => run(kp, kd, 4.0), [kp, kd]);
  const d = describe(log);
  const points: [number, number][] = [[0, 20], ...log.map(([time, y]) => [time, y * 1000] as [number, number])];
  return (
    <WidgetShell
      title={t("lineTitle")}
      script="tools/sim/models/line_sim.py"
      onReset={() => {
        setKp(DEFAULTS.kp);
        setKd(DEFAULTS.kd);
      }}
    >
      <Chart
        series={[{ points, color: "#38bdf8" }]}
        xMin={0}
        xMax={4}
        yMin={-80}
        yMax={80}
        xStep={0.5}
        yStep={20}
        hLines={[0]}
        xLabel={t("time")}
        yLabel={t("lineOffset")}
        ariaLabel={t("lineTitle")}
      />
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <Readout label={t("overshoot")} value={`${fixed(d.overshoot, 1)} mm`} testId="line-overshoot" />
        <Readout label={t("lineCrossings")} value={String(d.crossings)} testId="line-crossings" />
        <Readout
          label={t("lineSettle")}
          value={d.settled === null ? t("never") : `${fixed(d.settled, 2)} s`}
          testId="line-settle"
        />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Slider label="kp" value={kp} min={0} max={0.0008} step={0.00005} onChange={setKp} format={(v) => fixed(v, 5)} testId="line-kp" />
        <Slider label="kd" value={kd} min={0} max={0.0004} step={0.00001} onChange={setKd} format={(v) => fixed(v, 5)} testId="line-kd" />
      </div>
    </WidgetShell>
  );
}
