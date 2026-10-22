"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { B, R, wheels } from "@/lib/models/diffDrive";
import { Readout } from "./Chart";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

// The lesson's worked example: turning on the spot at ω = 1.0 rad/s, with controllers.yaml's b and r.
const DEFAULTS = { v: 0.0, w: 1.0, b: B, r: R };
/** ros2_control clamps each wheel command to ±10 rad/s (m4bot_control.urdf.xacro). */
const WHEEL_LIMIT = 10;
const PX_PER_M = 200; // top view scale
const PX_PER_RADS = 6; // arrow length per rad/s (10 rad/s fits above and below the robot)

/** Arrow length is drawn up to 12 rad/s, so a clamped command still fits in the picture. */
const clip = (x: number) => Math.max(-12, Math.min(12, x));

function Arrow({ x, y, len, testId }: { x: number; y: number; len: number; testId: string }) {
  if (Math.abs(len) < 0.5) return <circle cx={x} cy={y} r={2} className="fill-zinc-500" data-testid={testId} />;
  const tip = y - len;
  const dir = len > 0 ? 1 : -1;
  return (
    <g className="stroke-sky-400" strokeWidth={2.5} data-testid={testId}>
      <line x1={x} y1={y} x2={x} y2={tip} />
      <polyline points={`${x - 5},${tip + 6 * dir} ${x},${tip} ${x + 5},${tip + 6 * dir}`} fill="none" />
    </g>
  );
}

export function DiffDriveWidget() {
  const t = useTranslations("widget");
  const [v, setV] = useState(DEFAULTS.v);
  const [w, setW] = useState(DEFAULTS.w);
  const [b, setB] = useState(DEFAULTS.b);
  const [r, setR] = useState(DEFAULTS.r);
  const [left, right] = wheels(v, w, b, r);
  const radius = w === 0 ? t("ddStraight") : v === 0 ? t("ddInPlace") : `${fixed(v / w, 2)} m`;
  const clamped = Math.abs(left) > WHEEL_LIMIT || Math.abs(right) > WHEEL_LIMIT;
  // top view: robot at (100, 85) facing up; its left is towards smaller x
  const cx = 100, cy = 85, half = (b / 2) * PX_PER_M;
  const icr = w === 0 ? null : cx - (v / w) * PX_PER_M;
  return (
    <WidgetShell
      title={t("ddTitle")}
      script="examples/month-4/ros2-control/diff_drive.py"
      onReset={() => {
        setV(DEFAULTS.v);
        setW(DEFAULTS.w);
        setB(DEFAULTS.b);
        setR(DEFAULTS.r);
      }}
    >
      <p className="font-mono text-xs text-zinc-400 [overflow-wrap:anywhere]">v_left = v − ω·b/2, v_right = v + ω·b/2, wheel = v_wheel / r</p>
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <Readout label={t("ddLeft")} value={`${fixed(left, 1)} rad/s`} testId="dd-left" />
        <Readout label={t("ddRight")} value={`${fixed(right, 1)} rad/s`} testId="dd-right" />
        <Readout label={t("ddRadius")} value={radius} testId="dd-radius" />
      </div>
      <p className="mt-1 font-mono text-xs text-zinc-500" data-testid="dd-rims">
        v_left = {fixed(v - (w * b) / 2, 3)} m/s, v_right = {fixed(v + (w * b) / 2, 3)} m/s
      </p>
      {clamped && (
        <p className="mt-1 text-xs text-red-400" data-testid="dd-clamped">
          {t("ddClamped", { limit: WHEEL_LIMIT })}
        </p>
      )}
      <svg viewBox="0 0 200 170" className="mx-auto mt-3 block h-auto w-full max-w-[260px]" role="img" aria-label={t("ddTitle")}>
        <rect x={cx - half - 6} y={cy - 30} width={2 * half + 12} height={60} rx={10} className="fill-white/[0.04] stroke-white/20" />
        <polygon points={`${cx},${cy - 22} ${cx - 6},${cy - 12} ${cx + 6},${cy - 12}`} className="fill-zinc-400" />
        <rect x={cx - half - 4} y={cy - 12} width={8} height={24} rx={2} className="fill-zinc-600" />
        <rect x={cx + half - 4} y={cy - 12} width={8} height={24} rx={2} className="fill-zinc-600" />
        <Arrow x={cx - half} y={cy} len={clip(left) * PX_PER_RADS} testId="dd-arrow-left" />
        <Arrow x={cx + half} y={cy} len={clip(right) * PX_PER_RADS} testId="dd-arrow-right" />
        {icr !== null && icr >= 4 && icr <= 196 && (
          <g className="fill-amber-300">
            <circle cx={icr} cy={cy} r={3} />
            <text x={icr} y={cy + 58} textAnchor="middle" className="fill-amber-300/80 text-xs">
              {t("ddCentre")}
            </text>
          </g>
        )}
        <text x={cx - half} y={cy + 44} textAnchor="middle" className="fill-zinc-500 text-xs">L</text>
        <text x={cx + half} y={cy + 44} textAnchor="middle" className="fill-zinc-500 text-xs">R</text>
      </svg>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Slider label={t("ddV")} value={v} min={-0.5} max={0.5} step={0.05} onChange={setV} format={(x) => fixed(x, 2)} unit="m/s" testId="dd-v" />
        <Slider label={t("ddW")} value={w} min={-2} max={2} step={0.1} onChange={setW} format={(x) => fixed(x, 1)} unit="rad/s" testId="dd-w" />
        <Slider label={t("ddB")} value={b} min={0.2} max={0.4} step={0.01} onChange={setB} format={(x) => fixed(x, 2)} unit="m" testId="dd-b" />
        <Slider label={t("ddR")} value={r} min={0.03} max={0.08} step={0.005} onChange={setR} format={(x) => fixed(x, 3)} unit="m" testId="dd-r" />
      </div>
      <p className="mt-2 text-xs text-zinc-500">{t("ddNote")}</p>
    </WidgetShell>
  );
}
