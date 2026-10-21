"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { BINS, firstChunkValue, fromBins, JOINTS, ranges, toBins } from "@/lib/models/actionTokens";
import { Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

export function ActionTokenWidget() {
  const t = useTranslations("widget");
  const { lo, hi } = useMemo(() => ranges(), []);
  const start = useMemo(() => Math.round(firstChunkValue() * 10) / 10, []);
  const [joint, setJoint] = useState(0);
  const [angle, setAngle] = useState(start);
  const l = lo[joint];
  const h = hi[joint];
  const token = toBins(angle, l, h);
  const back = fromBins(token, l, h);
  const clipped = !(l <= angle && angle <= h);
  return (
    <WidgetShell
      title={t("tokTitle")}
      script="examples/month-6/vla-models/action_tokens.py"
      onReset={() => {
        setJoint(0);
        setAngle(start);
      }}
    >
      <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-zinc-300">
        {Array.from({ length: JOINTS }, (_, j) => (
          <label key={j} className="flex items-center gap-1.5">
            <input
              type="radio"
              name="tok-joint"
              checked={joint === j}
              onChange={() => setJoint(j)}
              data-testid={`tok-j${j}`}
              className="h-5 w-5 cursor-pointer accent-sky-400"
            />
            j{j}
          </label>
        ))}
      </div>
      <p className="mt-2 text-xs text-zinc-500" data-testid="tok-range">
        {t("tokRange", { lo: fixed(l, 1), hi: fixed(h, 1), w: fixed((h - l) / BINS, 2) })}
      </p>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <Readout label={t("tokToken")} value={String(token)} testId="tok-token" />
        <Readout label={t("tokBack")} value={`${fixed(back, 2)}°`} testId="tok-back" />
        <Readout label={t("error")} value={`${fixed(Math.abs(angle - back), 2)}°`} testId="tok-error" />
      </div>
      {clipped && (
        <p className="mt-2 text-xs text-red-300" data-testid="tok-clipped">
          {t("tokClipped")}
        </p>
      )}
      <div className="mt-4">
        <Slider label={t("tokAngle")} value={angle} min={-100} max={100} step={0.1} onChange={setAngle} format={(v) => fixed(v, 1)} unit="°" testId="tok-angle" />
      </div>
    </WidgetShell>
  );
}
