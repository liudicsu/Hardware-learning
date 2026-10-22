"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { simulate } from "@/lib/models/pid";
import { Chart } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

const SECONDS = 3;

const DEFAULTS = { kp: 0.05, ki: 0.1, kd: 0.002, antiWindup: true };

export function PidWidget() {
  const t = useTranslations("widget");
  const [kp, setKp] = useState(DEFAULTS.kp);
  const [ki, setKi] = useState(DEFAULTS.ki);
  const [kd, setKd] = useState(DEFAULTS.kd);
  const [antiWindup, setAntiWindup] = useState(DEFAULTS.antiWindup);

  const sim = useMemo(() => simulate(kp, ki, kd, antiWindup), [kp, ki, kd, antiWindup]);
  const yMax = Math.max(100, ...sim.deg);
  const points: [number, number][] = sim.t.map((time, i) => [time, sim.deg[i]]);

  function reset() {
    setKp(DEFAULTS.kp);
    setKi(DEFAULTS.ki);
    setKd(DEFAULTS.kd);
    setAntiWindup(DEFAULTS.antiWindup);
  }

  return (
    <WidgetShell title={t("pidTitle")} script="tools/sim/models/pid_sim.py" onReset={reset}>
      <div className="min-w-0 max-w-full">
        <Chart
          series={[{ points, color: "#38bdf8" }]}
          xMin={0}
          xMax={SECONDS}
          yMin={0}
          yMax={yMax}
          xStep={0.5}
          yStep={20}
          xDigits={1}
          yDigits={0}
          xLabel={t("time")}
          yLabel={t("angle")}
          ariaLabel={t("pidTitle")}
          band={[59, 61]}
          hLines={[60]}
        />
      </div>

      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <p className="text-zinc-400">
          {t("finalAngle")}{" "}
          <span data-testid="pid-final" className="font-mono text-zinc-100">
            {fixed(sim.finalDeg, 1)}°
          </span>
        </p>
        <p className="text-zinc-400">
          {t("overshoot")}{" "}
          <span data-testid="pid-overshoot" className="font-mono text-zinc-100">
            {fixed(sim.overshoot, 1)}°
          </span>
        </p>
        <p className="text-zinc-400">
          {t("settle")}{" "}
          <span data-testid="pid-settle" className="font-mono text-zinc-100">
            {sim.settle === null ? t("never") : `${fixed(sim.settle, 2)} s`}
          </span>
        </p>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Slider label="Kp" value={kp} min={0} max={0.3} step={0.005} onChange={setKp} format={(v) => fixed(v, 3)} testId="pid-kp" />
        <Slider label="Ki" value={ki} min={0} max={0.6} step={0.01} onChange={setKi} format={(v) => fixed(v, 2)} testId="pid-ki" />
        <Slider label="Kd" value={kd} min={0} max={0.01} step={0.0005} onChange={setKd} format={(v) => fixed(v, 4)} testId="pid-kd" />
      </div>

      <div className="mt-3">
        <label className="flex items-center gap-2 text-xs text-zinc-300">
          <input
            data-testid="pid-aw"
            type="checkbox"
            checked={antiWindup}
            onChange={(event) => setAntiWindup(event.target.checked)}
            className="h-5 w-5 cursor-pointer accent-sky-400"
          />
          <span>{t("antiWindup")}</span>
        </label>
      </div>
    </WidgetShell>
  );
}
