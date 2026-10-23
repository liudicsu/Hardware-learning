"use client";

import { useTranslations } from "next-intl";

export interface ProgressBarProps {
  value: number;
  label?: string;
}

export function ProgressBar({ value, label }: ProgressBarProps) {
  const t = useTranslations("progress");
  const percent = Math.min(100, Math.max(0, Math.round(value)));

  return (
    <div>
      {label ? (
        <div className="mb-2 flex items-center justify-between gap-4 text-xs">
          <span className="text-zinc-400">{t("barLabel", { label })}</span>
          <span className="tabular-nums text-zinc-500">{t("barValue", { percent })}</span>
        </div>
      ) : null}
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        className="h-1.5 overflow-hidden rounded-full bg-white/10"
      >
        <div
          className="h-full rounded-full bg-sky-400 transition-[width] duration-300 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
