"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { bodePoint, closed, margins, T } from "@/lib/models/jointFreq";
import { Chart, Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

// The lesson's worked example: kp = 2.86 N*m/rad (0.05 N*m per degree), kd = 0.115.
const DEFAULTS = { kp: 2.86, kd: 0.115 };
const NYQUIST = Math.PI / T;

export function BodeWidget() {
  const t = useTranslations("widget");
  const [kp, setKp] = useState(DEFAULTS.kp);
  const [kd, setKd] = useState(DEFAULTS.kd);
  const m = useMemo(() => margins(kp, kd), [kp, kd]);
  const step = useMemo(() => closed(kp, kd), [kp, kd]);
  const { mag, ph } = useMemo(() => {
    const mag: [number, number][] = [];
    const ph: [number, number][] = [];
    let unwrap = 0;
    let last: number | null = null;
    for (let x = 0; x <= Math.log10(NYQUIST) + 1e-9; x += 0.01) {
      const r = bodePoint(kp, kd, 10 ** x);
      // bodePoint wraps the phase into (-360, 0]; keep the curve continuous for drawing
      let p = r.ph;
      if (last !== null && p - last > 180) unwrap -= 360;
      last = p;
      p += unwrap;
      mag.push([x, r.db]);
      ph.push([x, p]);
    }
    return { mag, ph };
  }, [kp, kd]);
  const dash = (v: number | null, d: number, unit: string) => (v === null ? "—" : `${fixed(v, d)} ${unit}`);
  const stable = step.late < step.early;
  const logTick = (v: number) => (v === 0 ? "1" : v === 1 ? "10" : v === 2 ? "100" : "");
  return (
    <WidgetShell
      title={t("bodeTitle")}
      script="tools/sim/models/joint_freq.py"
      onReset={() => {
        setKp(DEFAULTS.kp);
        setKd(DEFAULTS.kd);
      }}
    >
      <Chart
        series={[{ points: mag, color: "#38bdf8" }]}
        xMin={0}
        xMax={Math.log10(NYQUIST)}
        yMin={-60}
        yMax={60}
        xStep={1}
        yStep={20}
        hLines={[0]}
        xTickLabel={logTick}
        xLabel={t("bodeW")}
        yLabel="|L| (dB)"
        ariaLabel={t("bodeTitle")}
      />
      <Chart
        series={[{ points: ph, color: "#f59e0b" }]}
        xMin={0}
        xMax={Math.log10(NYQUIST)}
        yMin={-480}
        yMax={-60}
        xStep={1}
        yStep={60}
        hLines={[-180]}
        xTickLabel={logTick}
        xLabel={t("bodeW")}
        yLabel={t("bodePhase")}
        ariaLabel={t("bodePhase")}
      />
      <div className="mt-3 grid gap-x-5 gap-y-2 text-xs sm:grid-cols-2">
        <Readout label={t("bodeWc")} value={dash(m.wc, 1, "rad/s")} testId="bode-wc" />
        <Readout label={t("bodePm")} value={m.pm === null ? "—" : `${fixed(m.pm, 0)}°`} testId="bode-pm" />
        <Readout label={t("bodeWpc")} value={dash(m.wpc, 1, "rad/s")} testId="bode-wpc" />
        <Readout
          label={t("bodeGm")}
          value={m.gm === null ? "—" : `${fixed(m.gm, 1)} dB (× ${fixed(10 ** (m.gm / 20), 1)})`}
          testId="bode-gm"
        />
        <Readout label={t("bodeOvershoot")} value={stable ? `${fixed(step.over, 0)} %` : t("bodeGrows")} testId="bode-overshoot" />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Slider label="kp (N·m/rad)" value={kp} min={0.1} max={8} step={0.01} onChange={setKp} format={(v) => fixed(v, 2)} testId="bode-kp" />
        <Slider label="kd (N·m/(rad/s))" value={kd} min={0} max={0.3} step={0.005} onChange={setKd} format={(v) => fixed(v, 3)} testId="bode-kd" />
      </div>
    </WidgetShell>
  );
}
