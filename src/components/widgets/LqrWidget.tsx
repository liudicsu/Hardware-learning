"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { balance, cartpoleDiscrete, diag4, FMAX, lqr } from "@/lib/models/lqr";
import { Chart, Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

// The lesson's baseline: Q = diag(1, 1, 10, 1), R = 1, starting 10° off upright.
// Sliders move log10 of each weight, so 1 -> 100 and 0.01 -> 10 are reachable.
const DEFAULTS = { q1: 0, q3: 1, r: 0 };

export function LqrWidget() {
  const t = useTranslations("widget");
  const [q1, setQ1] = useState(DEFAULTS.q1);
  const [q3, setQ3] = useState(DEFAULTS.q3);
  const [r, setR] = useState(DEFAULTS.r);
  const Q1 = 10 ** q1;
  const Q3 = 10 ** q3;
  const R = 10 ** r;
  const k = useMemo(() => {
    const [phi, gam] = cartpoleDiscrete();
    return lqr(phi, gam, diag4([Q1, 1, Q3, 1]), R);
  }, [Q1, Q3, R]);
  const run = useMemo(() => balance(k, 10, 4.0, null, true), [k]);
  const angle = run.log.map(([time, , deg]) => [time, deg] as [number, number]);
  const pos = run.log.map(([time, x]) => [time, x * 100] as [number, number]);
  const show = (v: number) => (v >= 10 ? fixed(v, 0) : v >= 1 ? fixed(v, 1) : fixed(v, 2));
  return (
    <WidgetShell
      title={t("lqrTitle")}
      script="tools/sim/models/lqr_sim.py"
      onReset={() => {
        setQ1(DEFAULTS.q1);
        setQ3(DEFAULTS.q3);
        setR(DEFAULTS.r);
      }}
    >
      <Chart
        series={[
          { points: angle, color: "#38bdf8" },
          { points: pos, color: "#f59e0b", dashed: true },
        ]}
        xMin={0}
        xMax={4}
        yMin={-10}
        yMax={30}
        xStep={0.5}
        yStep={10}
        hLines={[0]}
        xLabel={t("time")}
        yLabel={t("lqrAxis")}
        ariaLabel={t("lqrTitle")}
      />
      <p className="mt-1 text-xs text-zinc-500">
        <span className="text-sky-400">—</span> {t("lqrAngle")} &nbsp; <span className="text-amber-400">- -</span> {t("lqrPos")}
      </p>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <Readout label="K" value={"[" + k.map((v) => fixed(v, 2)).join(", ") + "]"} testId="lqr-k" />
        <Readout
          label={t("lqrPeak")}
          value={`${fixed(run.fpeak, 2)} N${run.fpeak >= FMAX - 1e-9 ? " " + t("lqrAtLimit") : ""}`}
          testId="lqr-peak"
        />
        {run.x === null && (
          <p className="text-red-300" data-testid="lqr-fell">
            {t("lqrFell")}
          </p>
        )}
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Slider label={t("lqrQ1")} value={q1} min={-1} max={2} step={0.1} onChange={setQ1} format={(v) => show(10 ** v)} testId="lqr-q1" />
        <Slider label={t("lqrQ3")} value={q3} min={0} max={2} step={0.1} onChange={setQ3} format={(v) => show(10 ** v)} testId="lqr-q3" />
        <Slider label="R" value={r} min={-2} max={1} step={0.1} onChange={setR} format={(v) => show(10 ** v)} testId="lqr-r" />
      </div>
      <p className="mt-2 text-xs text-zinc-500">{t("lqrNote")}</p>
    </WidgetShell>
  );
}
