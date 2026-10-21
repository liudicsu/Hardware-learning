"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { simulate } from "@/lib/models/pid";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

const W = 600;
const H = 260;
const LEFT = 48;
const RIGHT = 16;
const TOP = 14;
const BOTTOM = 40;
const PLOT_W = W - LEFT - RIGHT;
const PLOT_H = H - TOP - BOTTOM;
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
  const x = (time: number) => LEFT + (time / SECONDS) * PLOT_W;
  const y = (value: number) => TOP + (1 - value / yMax) * PLOT_H;
  const points = sim.t.map((time, i) => `${x(time).toFixed(2)},${y(sim.deg[i]).toFixed(2)}`).join(" ");

  const xTicks: number[] = [];
  for (let tick = 0; tick <= SECONDS + 1e-9; tick += 0.5) xTicks.push(Number(tick.toFixed(1)));
  const yTicks: number[] = [];
  for (let tick = 0; tick <= yMax + 1e-9; tick += 20) yTicks.push(tick);

  function reset() {
    setKp(DEFAULTS.kp);
    setKi(DEFAULTS.ki);
    setKd(DEFAULTS.kd);
    setAntiWindup(DEFAULTS.antiWindup);
  }

  return (
    <WidgetShell title={t("pidTitle")} script="tools/sim/models/pid_sim.py" onReset={reset}>
      <div className="min-w-0 max-w-full">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="h-auto w-full"
          role="img"
          aria-label={t("pidTitle")}
        >
          <rect
            x={LEFT}
            y={y(61)}
            width={PLOT_W}
            height={Math.max(0, y(59) - y(61))}
            fill="rgba(56, 189, 248, 0.08)"
          />
          {yTicks.map((tick) => (
            <g key={`y-${tick}`}>
              <line
                x1={LEFT}
                y1={y(tick)}
                x2={LEFT + PLOT_W}
                y2={y(tick)}
                stroke="rgba(255,255,255,0.06)"
              />
              <text x={LEFT - 6} y={y(tick) + 3} textAnchor="end" fontSize="13" fill="#71717a">
                {fixed(tick, 0)}
              </text>
            </g>
          ))}
          {xTicks.map((tick) => (
            <g key={`x-${tick}`}>
              <line
                x1={x(tick)}
                y1={TOP}
                x2={x(tick)}
                y2={TOP + PLOT_H}
                stroke="rgba(255,255,255,0.06)"
              />
              <text x={x(tick)} y={TOP + PLOT_H + 17} textAnchor="middle" fontSize="13" fill="#71717a">
                {fixed(tick, 1)}
              </text>
            </g>
          ))}
          <line x1={LEFT} y1={TOP + PLOT_H} x2={LEFT + PLOT_W} y2={TOP + PLOT_H} stroke="#52525b" />
          <line x1={LEFT} y1={TOP} x2={LEFT} y2={TOP + PLOT_H} stroke="#52525b" />
          <line
            x1={LEFT}
            y1={y(60)}
            x2={LEFT + PLOT_W}
            y2={y(60)}
            stroke="#a1a1aa"
            strokeDasharray="5 4"
          />
          <polyline points={points} fill="none" stroke="#38bdf8" strokeWidth="2" />
          <text x={LEFT + PLOT_W / 2} y={H - 4} textAnchor="middle" fontSize="13" fill="#71717a">
            {t("time")}
          </text>
          <text
            x={12}
            y={TOP + PLOT_H / 2}
            textAnchor="middle"
            fontSize="13"
            fill="#71717a"
            transform={`rotate(-90 12 ${TOP + PLOT_H / 2})`}
          >
            {t("angle")}
          </text>
        </svg>
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
