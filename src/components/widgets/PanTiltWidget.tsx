"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { cameraTransform, echo } from "@/lib/models/panTilt";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

// The lesson's worked example: pan 30°, tilt 0.
const DEFAULTS = { pan: 30, tilt: 0 };
const RAD = Math.PI / 180;

export function PanTiltWidget() {
  const t = useTranslations("widget");
  const [pan, setPan] = useState(DEFAULTS.pan);
  const [tilt, setTilt] = useState(DEFAULTS.tilt);
  const lines = echo(cameraTransform(pan * RAD, tilt * RAD));
  return (
    <WidgetShell
      title={t("tfTitle")}
      script="examples/month-4/urdf-tf/m4_description/urdf/robot.urdf.xacro"
      sourceLabel={t("tfSource")}
      onReset={() => {
        setPan(DEFAULTS.pan);
        setTilt(DEFAULTS.tilt);
      }}
    >
      <p className="font-mono text-xs text-zinc-500">$ ros2 run tf2_ros tf2_echo base_link camera_link</p>
      <pre className="mt-2 overflow-x-auto whitespace-pre rounded-lg bg-black/30 p-2 text-xs leading-5 text-zinc-200" data-testid="tf-echo">
        {lines.join("\n")}
      </pre>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Slider label={t("tfPan")} value={pan} min={-90} max={90} step={1} onChange={setPan} format={(v) => fixed(v, 0)} unit="°" testId="tf-pan" />
        <Slider label={t("tfTilt")} value={tilt} min={-45} max={45} step={1} onChange={setTilt} format={(v) => fixed(v, 0)} unit="°" testId="tf-tilt" />
      </div>
      <p className="mt-2 text-xs text-zinc-500">{t("tfNote")}</p>
    </WidgetShell>
  );
}
