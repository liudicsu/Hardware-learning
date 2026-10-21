"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { G, squeeze } from "@/lib/models/gripForce";
import { Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

// The lesson's worked example: an egg, PLA fingers.
const DEFAULTS = { mass: 60, mu: 0.3, accel: 3.0, safety: 2.0 };

export function GripForceWidget() {
  const t = useTranslations("widget");
  const [mass, setMass] = useState(DEFAULTS.mass);
  const [mu, setMu] = useState(DEFAULTS.mu);
  const [accel, setAccel] = useState(DEFAULTS.accel);
  const [safety, setSafety] = useState(DEFAULTS.safety);
  const f = squeeze(mass / 1000, mu, safety, accel);
  const tilt = (Math.atan(mu) * 180) / Math.PI;
  return (
    <WidgetShell
      title={t("gripTitle")}
      script="examples/month-3/gripper-fingers/grip_force.py"
      onReset={() => {
        setMass(DEFAULTS.mass);
        setMu(DEFAULTS.mu);
        setAccel(DEFAULTS.accel);
        setSafety(DEFAULTS.safety);
      }}
    >
      <p className="font-mono text-xs text-zinc-400">F = S · m · (g + a) / (2μ), g = {fixed(G, 2)} m/s²</p>
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <Readout label={t("gripForce")} value={`${fixed(f, 1)} N`} testId="grip-force" />
        <Readout label={t("gripTilt")} value={`${fixed(tilt, 0)}°`} testId="grip-tilt" />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Slider label={t("gripMass")} value={mass} min={5} max={500} step={1} onChange={setMass} unit="g" testId="grip-mass" />
        <Slider label="μ" value={mu} min={0.1} max={1.2} step={0.05} onChange={setMu} format={(v) => fixed(v, 2)} testId="grip-mu" />
        <Slider label={t("gripAccel")} value={accel} min={0} max={10} step={0.5} onChange={setAccel} format={(v) => fixed(v, 1)} unit="m/s²" testId="grip-accel" />
        <Slider label={t("gripSafety")} value={safety} min={1} max={4} step={0.5} onChange={setSafety} format={(v) => fixed(v, 1)} testId="grip-safety" />
      </div>
      <p className="mt-2 text-xs text-zinc-500">{t("gripMuNote")}</p>
    </WidgetShell>
  );
}
