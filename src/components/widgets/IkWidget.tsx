"use client";

import type { MouseEvent } from "react";
import { useState } from "react";
import { useTranslations } from "next-intl";
import { exp, fixed } from "@/lib/models/format";
import { detJ, fk, H, ik, L1, L2 } from "@/lib/models/kinematics";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

type Vec3 = [number, number, number];
type IkResult = ReturnType<typeof ik>;

const DEFAULTS = {
  q: [30, 45, -60] as Vec3,
  target: [0.1, 0.15, 0.12] as Vec3,
};

const SIDE = {
  w: 320,
  h: 300,
  left: 38,
  right: 12,
  top: 12,
  bottom: 28,
  rMin: -0.3,
  rMax: 0.35,
  zMin: -0.2,
  zMax: 0.4,
};

const TOP = {
  w: 320,
  h: 260,
  left: 24,
  right: 24,
  top: 12,
  bottom: 24,
  min: -0.3,
  max: 0.3,
};

const toRad = (degrees: number) => (degrees * Math.PI) / 180;
const toDeg = (radians: number) => (radians * 180) / Math.PI;
const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

export function IkWidget() {
  const t = useTranslations("widget");
  const [qDeg, setQDeg] = useState<Vec3>(DEFAULTS.q);
  const [target, setTarget] = useState<Vec3>(DEFAULTS.target);
  const [result, setResult] = useState<IkResult | null>(null);

  const q = qDeg.map((value) => toRad(value));
  const tip = fk(q);
  const r = Math.hypot(tip[0], tip[1]);
  const absDet = Math.abs(detJ(q));
  const nearSingular = absDet < 5e-4;

  const sidePlotW = SIDE.w - SIDE.left - SIDE.right;
  const sidePlotH = SIDE.h - SIDE.top - SIDE.bottom;
  const sideX = (value: number) => SIDE.left + ((value - SIDE.rMin) / (SIDE.rMax - SIDE.rMin)) * sidePlotW;
  const sideY = (value: number) => SIDE.top + (1 - (value - SIDE.zMin) / (SIDE.zMax - SIDE.zMin)) * sidePlotH;

  const topPlotW = TOP.w - TOP.left - TOP.right;
  const topPlotH = TOP.h - TOP.top - TOP.bottom;
  const topX = (value: number) => TOP.left + ((value - TOP.min) / (TOP.max - TOP.min)) * topPlotW;
  const topY = (value: number) => TOP.top + (1 - (value - TOP.min) / (TOP.max - TOP.min)) * topPlotH;

  // Side view = the arm's own vertical plane, so the reach is signed (negative when the arm
  // reaches back over the base), as r = L1 cos q1 + L2 cos(q1 + q2) in kinematics.py.
  const reach = (qq: number[]) => L1 * Math.cos(qq[1]) + L2 * Math.cos(qq[1] + qq[2]);
  const armR = reach(q);
  const elbowR = L1 * Math.cos(q[1]);
  const elbowZ = H + L1 * Math.sin(q[1]);
  // the target projected onto the arm's plane (azimuth q0)
  const targetR = target[0] * Math.cos(q[0]) + target[1] * Math.sin(q[0]);
  const targetZ = target[2];

  const sidePath = result?.path.map((step) => {
    const p = fk(step.q);
    return [sideX(reach(step.q)), sideY(p[2])] as const;
  });
  const topPath = result?.path.map((step) => {
    const p = fk(step.q);
    return [topX(p[0]), topY(p[1])] as const;
  });

  function solveFor(next: Vec3) {
    const res = ik(next, [0, toRad(30), toRad(-30)]);
    setResult(res);
    setQDeg(res.q.map((value) => toDeg(value)) as Vec3);
  }

  function reset() {
    setQDeg(DEFAULTS.q);
    setTarget(DEFAULTS.target);
    setResult(null);
  }

  function updateQ(index: number, value: number) {
    setQDeg((current) => {
      const next: Vec3 = [...current];
      next[index] = value;
      return next;
    });
  }

  function updateTarget(index: number, value: number) {
    if (!Number.isFinite(value)) return;
    setTarget((current) => {
      const next: Vec3 = [...current];
      next[index] = value;
      return next;
    });
    setResult(null);
  }

  function sidePoint(event: MouseEvent<SVGSVGElement>) {
    const matrix = event.currentTarget.getScreenCTM();
    if (!matrix) return;
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    const nextR = clamp(SIDE.rMin + ((point.x - SIDE.left) / sidePlotW) * (SIDE.rMax - SIDE.rMin), SIDE.rMin, SIDE.rMax);
    const nextZ = clamp(
      SIDE.zMin + (1 - (point.y - SIDE.top) / sidePlotH) * (SIDE.zMax - SIDE.zMin),
      SIDE.zMin,
      SIDE.zMax,
    );
    const azimuth = q[0];
    const next: Vec3 = [nextR * Math.cos(azimuth), nextR * Math.sin(azimuth), nextZ];
    setTarget(next);
    solveFor(next);
  }

  function topPoint(event: MouseEvent<SVGSVGElement>) {
    const matrix = event.currentTarget.getScreenCTM();
    if (!matrix) return;
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
    const nextX = clamp(TOP.min + ((point.x - TOP.left) / topPlotW) * (TOP.max - TOP.min), TOP.min, TOP.max);
    const nextY = clamp(TOP.min + (1 - (point.y - TOP.top) / topPlotH) * (TOP.max - TOP.min), TOP.min, TOP.max);
    const next: Vec3 = [nextX, nextY, target[2]];
    setTarget(next);
    solveFor(next);
  }

  return (
    <WidgetShell title={t("ikTitle")} script="tools/sim/models/kinematics.py" onReset={reset}>
      <div className="grid min-w-0 gap-3 sm:grid-cols-2">
        <div className="min-w-0">
          <p className="mb-1 text-xs text-zinc-500">{t("sideView")}</p>
          <svg
            viewBox={`0 0 ${SIDE.w} ${SIDE.h}`}
            className="h-auto w-full cursor-crosshair overflow-hidden rounded-lg border border-white/10 bg-black/20"
            role="img"
            aria-label={t("sideView")}
            onClick={sidePoint}
          >
            <line x1={SIDE.left} y1={sideY(0)} x2={SIDE.left + sidePlotW} y2={sideY(0)} stroke="rgba(255,255,255,0.16)" />
            <line x1={sideX(0)} y1={SIDE.top} x2={sideX(0)} y2={SIDE.top + sidePlotH} stroke="rgba(255,255,255,0.16)" />
            <line
              x1={sideX(0)}
              y1={sideY(H)}
              x2={sideX(0)}
              y2={sideY(0)}
              stroke="#a1a1aa"
              strokeWidth="4"
              strokeLinecap="round"
            />
            <line
              x1={sideX(0)}
              y1={sideY(H)}
              x2={sideX(elbowR)}
              y2={sideY(elbowZ)}
              stroke="#e4e4e7"
              strokeWidth="5"
              strokeLinecap="round"
            />
            <line
              x1={sideX(elbowR)}
              y1={sideY(elbowZ)}
              x2={sideX(armR)}
              y2={sideY(tip[2])}
              stroke="#a1a1aa"
              strokeWidth="4"
              strokeLinecap="round"
            />
            {sidePath && sidePath.length > 1 && (
              <>
                <polyline
                  points={sidePath.map(([px, py]) => `${px},${py}`).join(" ")}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="1"
                  strokeDasharray="3 3"
                  opacity="0.7"
                />
                {sidePath.map(([px, py], index) => (
                  <circle key={index} cx={px} cy={py} r="1.6" fill="#38bdf8" opacity="0.8" />
                ))}
              </>
            )}
            <circle cx={sideX(elbowR)} cy={sideY(elbowZ)} r="3.5" fill="#38bdf8" />
            <circle cx={sideX(armR)} cy={sideY(tip[2])} r="3.5" fill="#38bdf8" />
            <circle
              cx={sideX(targetR)}
              cy={sideY(targetZ)}
              r="6"
              fill="none"
              stroke="#f59e0b"
              strokeWidth="1.5"
            />
            <line x1={sideX(targetR) - 9} y1={sideY(targetZ)} x2={sideX(targetR) + 9} y2={sideY(targetZ)} stroke="#f59e0b" />
            <line x1={sideX(targetR)} y1={sideY(targetZ) - 9} x2={sideX(targetR)} y2={sideY(targetZ) + 9} stroke="#f59e0b" />
            <text x={SIDE.left + sidePlotW - 4} y={sideY(0) - 6} textAnchor="end" fontSize="10" fill="#71717a">r</text>
            <text x={sideX(0) + 6} y={SIDE.top + 10} fontSize="10" fill="#71717a">z</text>
          </svg>
        </div>

        <div className="min-w-0">
          <p className="mb-1 text-xs text-zinc-500">{t("topView")}</p>
          <svg
            viewBox={`0 0 ${TOP.w} ${TOP.h}`}
            className="h-auto w-full cursor-crosshair overflow-hidden rounded-lg border border-white/10 bg-black/20"
            role="img"
            aria-label={t("topView")}
            onClick={topPoint}
          >
            <line x1={TOP.left} y1={topY(0)} x2={TOP.left + topPlotW} y2={topY(0)} stroke="rgba(255,255,255,0.16)" />
            <line x1={topX(0)} y1={TOP.top} x2={topX(0)} y2={TOP.top + topPlotH} stroke="rgba(255,255,255,0.16)" />
            <line
              x1={topX(0)}
              y1={topY(0)}
              x2={topX(tip[0])}
              y2={topY(tip[1])}
              stroke="#e4e4e7"
              strokeWidth="4"
              strokeLinecap="round"
            />
            {topPath && topPath.length > 1 && (
              <>
                <polyline
                  points={topPath.map(([px, py]) => `${px},${py}`).join(" ")}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="1"
                  strokeDasharray="3 3"
                  opacity="0.7"
                />
                {topPath.map(([px, py], index) => (
                  <circle key={index} cx={px} cy={py} r="1.6" fill="#38bdf8" opacity="0.8" />
                ))}
              </>
            )}
            <circle cx={topX(tip[0])} cy={topY(tip[1])} r="3.5" fill="#38bdf8" />
            <circle
              cx={topX(target[0])}
              cy={topY(target[1])}
              r="6"
              fill="none"
              stroke="#f59e0b"
              strokeWidth="1.5"
            />
            <line x1={topX(target[0]) - 9} y1={topY(target[1])} x2={topX(target[0]) + 9} y2={topY(target[1])} stroke="#f59e0b" />
            <line x1={topX(target[0])} y1={topY(target[1]) - 9} x2={topX(target[0])} y2={topY(target[1]) + 9} stroke="#f59e0b" />
            <text x={TOP.left + topPlotW - 4} y={topY(0) - 5} textAnchor="end" fontSize="10" fill="#71717a">x</text>
            <text x={topX(0) + 6} y={TOP.top + 10} fontSize="10" fill="#71717a">y</text>
          </svg>
        </div>
      </div>

      <div className="mt-4 grid gap-2 text-xs text-zinc-400">
        <p>
          {t("tip")}{" "}
          <span data-testid="ik-tip" className="font-mono text-zinc-100">
            ({fixed(tip[0], 4)}, {fixed(tip[1], 4)}, {fixed(tip[2], 4)})
          </span>{" "}
          m
        </p>
        <p>
          r ={" "}
          <span data-testid="ik-r" className="font-mono text-zinc-100">
            {fixed(r, 4)}
          </span>{" "}
          m
        </p>
        <p className={nearSingular ? "text-red-400" : "text-zinc-400"}>
          |det J| ={" "}
          <span data-testid="ik-det" className={`font-mono${nearSingular ? " text-red-400" : ""}`}>
            {exp(absDet, 2)}
          </span>{" "}
          m³
          {nearSingular && <span className="ml-2 text-red-400">· {t("nearSingular")}</span>}
        </p>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Slider
          label={t("base")}
          value={qDeg[0]}
          min={-180}
          max={180}
          step={1}
          onChange={(value) => updateQ(0, value)}
          format={(value) => fixed(value, 0)}
          unit="°"
          testId="ik-q0"
        />
        <Slider
          label={t("shoulder")}
          value={qDeg[1]}
          min={-90}
          max={180}
          step={1}
          onChange={(value) => updateQ(1, value)}
          format={(value) => fixed(value, 0)}
          unit="°"
          testId="ik-q1"
        />
        <Slider
          label={t("elbow")}
          value={qDeg[2]}
          min={-180}
          max={180}
          step={1}
          onChange={(value) => updateQ(2, value)}
          format={(value) => fixed(value, 0)}
          unit="°"
          testId="ik-q2"
        />
      </div>

      <div className="mt-4 rounded-lg border border-white/10 p-3">
        <p className="text-xs text-zinc-400">{t("ikTarget")}</p>
        <div className="mt-2 flex flex-wrap items-end gap-2">
          {(["x", "y", "z"] as const).map((axis, index) => (
            <label key={axis} className="min-w-0 flex-1 text-xs text-zinc-500">
              <span className="block">{t(`axis${axis.toUpperCase()}`)}</span>
              <input
                type="number"
                step={0.01}
                value={target[index]}
                data-testid={`ik-t${axis}`}
                onChange={(event) => updateTarget(index, Number(event.target.value))}
                className="mt-1 w-full min-w-0 rounded-lg border border-white/10 bg-transparent px-2 py-1.5 font-mono text-xs text-zinc-100 outline-none transition-colors focus:border-sky-400/60"
              />
            </label>
          ))}
          <button
            type="button"
            data-testid="ik-solve"
            onClick={() => solveFor(target)}
            className="rounded-lg bg-sky-400/10 px-3 py-1.5 text-xs font-medium text-sky-400 transition-colors hover:bg-sky-400/20"
          >
            {t("solve")}
          </button>
        </div>
        {result && (
          <p className="mt-2 text-xs text-zinc-400">
            <span data-testid="ik-result" className="font-mono text-zinc-100">
              {t("iterations", {
                // update steps taken: `it` is the index of the last iteration, which made no
                // step when it converged; as in kinematics.py ("after {it4 + 1} iterations")
                n: result.dist < 1e-5 ? result.it : result.it + 1,
                q: `[${result.q.map((value) => fixed(toDeg(value), 2)).join(", ")}]`,
              })}
            </span>
            <span className="ml-2 text-zinc-500">
              {t("error")} {fixed(result.dist * 1000, 2)} mm
            </span>
          </p>
        )}
      </div>
    </WidgetShell>
  );
}
