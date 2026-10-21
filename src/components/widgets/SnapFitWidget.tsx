"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { snap, type Material } from "@/lib/models/snapFit";
import { Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

// The arm used in esp32_case.scad (the lesson's worked example).
const DEFAULTS = { L: 10, t: 1.2, y: 0.8, material: "PLA" as Material, lead: 30 };

export function SnapFitWidget() {
  const t = useTranslations("widget");
  const [L, setL] = useState(DEFAULTS.L);
  const [th, setTh] = useState(DEFAULTS.t);
  const [y, setY] = useState(DEFAULTS.y);
  const [material, setMaterial] = useState<Material>(DEFAULTS.material);
  const [lead, setLead] = useState(DEFAULTS.lead);
  const s = snap(L, th, y, 6.0, material, lead);
  const finite = Number.isFinite(s.W) && s.W > 0;
  return (
    <WidgetShell
      title={t("snapTitle")}
      script="examples/month-3/fdm-printing/snap_fit.py"
      onReset={() => {
        setL(DEFAULTS.L);
        setTh(DEFAULTS.t);
        setY(DEFAULTS.y);
        setMaterial(DEFAULTS.material);
        setLead(DEFAULTS.lead);
      }}
    >
      <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <Readout label={t("snapStrain")} value={`${fixed(s.eps * 100, 2)} %`} testId="snap-strain" />
        <p className={s.ok ? "text-emerald-300" : "text-red-300"} data-testid="snap-verdict">
          {s.ok ? t("snapOk") : t("snapTooMuch", { limit: fixed(s.allowed * 100, 1) })}
        </p>
        <Readout label={t("snapPush")} value={finite ? `${fixed(s.W, 1)} N` : t("snapLocks")} testId="snap-push" />
      </div>
      <pre className="mt-3 overflow-x-auto whitespace-pre rounded-lg bg-black/30 p-2 text-[11px] text-zinc-300" data-testid="snap-line">
        {s.line}
      </pre>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Slider label={t("snapL")} value={L} min={3} max={20} step={0.5} onChange={setL} format={(v) => fixed(v, 1)} unit="mm" testId="snap-L" />
        <Slider label={t("snapT")} value={th} min={0.6} max={3} step={0.1} onChange={setTh} format={(v) => fixed(v, 1)} unit="mm" testId="snap-t" />
        <Slider label={t("snapY")} value={y} min={0.2} max={2} step={0.1} onChange={setY} format={(v) => fixed(v, 1)} unit="mm" testId="snap-y" />
        <Slider label={t("snapLead")} value={lead} min={10} max={70} step={5} onChange={setLead} format={(v) => fixed(v, 0)} unit="°" testId="snap-lead" />
      </div>
      <div className="mt-3 flex gap-4 text-xs text-zinc-300">
        {(["PLA", "PETG"] as Material[]).map((m) => (
          <label key={m} className="flex items-center gap-2">
            <input
              type="radio"
              name="snap-material"
              checked={material === m}
              onChange={() => setMaterial(m)}
              data-testid={`snap-${m}`}
              className="h-5 w-5 cursor-pointer accent-sky-400"
            />
            {m}
          </label>
        ))}
      </div>
      <p className="mt-2 text-xs text-zinc-500">{t("snapFixed")}</p>
    </WidgetShell>
  );
}
