"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fixed, int } from "@/lib/models/format";
import { planetary, tipError } from "@/lib/models/gears";
import { Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

const DEFAULTS = { sun: 12, ring: 48, planets: 3, reach: 0.3, backlash: 2.0 };

export function GearWidget() {
  const t = useTranslations("widget");
  const [sun, setSun] = useState(DEFAULTS.sun);
  const [ring, setRing] = useState(DEFAULTS.ring);
  const [planets, setPlanets] = useState(DEFAULTS.planets);
  const [reach, setReach] = useState(DEFAULTS.reach);
  const [backlash, setBacklash] = useState(DEFAULTS.backlash);
  const p = planetary(sun, ring, planets);
  const gap = ring - sun;
  let status: string;
  if (gap % 2) status = t("gearNoMesh", { teeth: fixed(gap / 2, 1) });
  else if ((sun + ring) % planets) status = t("gearNoSpace", { n: planets, q: fixed((sun + ring) / planets, 2) });
  else if (!p.ok)
    status = t("gearCollide", { n: planets, s: fixed((sun + p.planet!) * Math.sin(Math.PI / planets), 2), d: p.planet! + 2 });
  else status = t("gearOk", { ratio: fixed(p.ratio!, 3) });
  return (
    <WidgetShell
      title={t("gearTitle")}
      script="examples/month-3/transmissions/gear_calc.py"
      onReset={() => {
        setSun(DEFAULTS.sun);
        setRing(DEFAULTS.ring);
        setPlanets(DEFAULTS.planets);
        setReach(DEFAULTS.reach);
        setBacklash(DEFAULTS.backlash);
      }}
    >
      <p className="text-xs font-medium text-zinc-300">{t("gearPlanetary")}</p>
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <Readout label={t("gearPlanet")} value={p.planet === null ? "—" : int(p.planet, 0)} testId="gear-planet" />
        <p className={p.ok ? "text-emerald-300" : "text-red-300"} data-testid="gear-status">
          {status}
        </p>
      </div>
      <pre className="mt-2 overflow-x-auto whitespace-pre rounded-lg bg-black/30 p-2 text-[11px] text-zinc-300" data-testid="gear-line">
        {p.line}
      </pre>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        <Slider label={t("gearSun")} value={sun} min={8} max={30} step={1} onChange={setSun} testId="gear-sun" />
        <Slider label={t("gearRing")} value={ring} min={32} max={90} step={1} onChange={setRing} testId="gear-ring" />
        <Slider label={t("gearPlanets")} value={planets} min={2} max={6} step={1} onChange={setPlanets} testId="gear-planets" />
      </div>
      <p className="mt-5 text-xs font-medium text-zinc-300">{t("gearBacklash")}</p>
      <div className="mt-2 text-xs">
        <Readout label={t("gearTipError")} value={`${fixed(tipError(reach, backlash), 1)} mm`} testId="gear-tip" />
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <Slider label={t("gearReach")} value={reach} min={0.1} max={0.6} step={0.01} onChange={setReach} format={(v) => fixed(v, 2)} unit="m" testId="gear-reach" />
        <Slider label={t("gearBacklashDeg")} value={backlash} min={0} max={3} step={0.1} onChange={setBacklash} format={(v) => fixed(v, 1)} unit="°" testId="gear-backlash" />
      </div>
    </WidgetShell>
  );
}
