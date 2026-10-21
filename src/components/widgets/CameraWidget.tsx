"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import { HEIGHT, TRUE_CAMERA, W, project } from "@/lib/models/camera";
import type { Camera } from "@/lib/models/camera";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

const DEFAULTS = {
  x: 100.8,
  y: 60.5,
  z: 500.8,
  fx: 500,
  k1: -0.12,
  k2: 0.03,
};

function gridPath(cam: Camera, depthMm: number, ignoreDistortion: boolean): string {
  const z = depthMm / 1000;
  const line = (points: number[][]) =>
    points
      .map(([u, v], index) => `${index === 0 ? "M" : "L"}${u.toFixed(1)},${v.toFixed(1)}`)
      .join("");
  const parts: string[] = [];

  for (let x = -400; x <= 400; x += 50) {
    const points: number[][] = [];
    for (let y = -300; y <= 300; y += 10) {
      points.push(project([x / 1000, y / 1000, z], cam, ignoreDistortion));
    }
    parts.push(line(points));
  }
  for (let y = -300; y <= 300; y += 50) {
    const points: number[][] = [];
    for (let x = -400; x <= 400; x += 10) {
      points.push(project([x / 1000, y / 1000, z], cam, ignoreDistortion));
    }
    parts.push(line(points));
  }
  return parts.join(" ");
}

export function CameraWidget() {
  const t = useTranslations("widget");
  const [pointX, setPointX] = useState(DEFAULTS.x);
  const [pointY, setPointY] = useState(DEFAULTS.y);
  const [pointZ, setPointZ] = useState(DEFAULTS.z);
  const [fx, setFx] = useState(DEFAULTS.fx);
  const [k1, setK1] = useState(DEFAULTS.k1);
  const [k2, setK2] = useState(DEFAULTS.k2);
  const [ignore, setIgnore] = useState(false);

  const cam = useMemo<Camera>(() => ({ ...TRUE_CAMERA, fx, fy: fx, k1, k2 }), [fx, k1, k2]);
  const grid = useMemo(
    () => ({
      distorted: gridPath(cam, pointZ, false),
      ideal: gridPath(cam, pointZ, true),
    }),
    [cam, pointZ],
  );

  const point = [pointX / 1000, pointY / 1000, pointZ / 1000];
  const distorted = project(point, cam, false);
  const ideal = project(point, cam, true);
  const error = Math.hypot(distorted[0] - ideal[0], distorted[1] - ideal[1]);
  const answer = ignore ? ideal : distorted;
  const other = ignore ? distorted : ideal;

  function reset() {
    setPointX(DEFAULTS.x);
    setPointY(DEFAULTS.y);
    setPointZ(DEFAULTS.z);
    setFx(DEFAULTS.fx);
    setK1(DEFAULTS.k1);
    setK2(DEFAULTS.k2);
    setIgnore(false);
  }

  return (
    <WidgetShell
      title={t("camTitle")}
      script="examples/month-5/camera-calibration/make_views.py"
      onReset={reset}
    >
      <div className="min-w-0 max-w-full">
        <svg
          viewBox={`0 0 ${W} ${HEIGHT}`}
          className="h-auto w-full overflow-hidden rounded-lg border border-white/10 bg-[#0a0a0b]"
          role="img"
          aria-label={t("imagePlane")}
        >
          <defs>
            <clipPath id="camera-image-clip">
              <rect x="0" y="0" width={W} height={HEIGHT} />
            </clipPath>
          </defs>
          <g clipPath="url(#camera-image-clip)">
            <path d={grid.ideal} fill="none" stroke="#a1a1aa" strokeOpacity="0.3" strokeWidth="1" />
            <path d={grid.distorted} fill="none" stroke="#38bdf8" strokeOpacity="0.6" strokeWidth="1.4" />
            <line
              x1={distorted[0]}
              y1={distorted[1]}
              x2={ideal[0]}
              y2={ideal[1]}
              stroke="#f59e0b"
              strokeWidth="2"
            />
            <circle cx={other[0]} cy={other[1]} r="7" fill="none" stroke="#f59e0b" strokeWidth="2" />
            <circle cx={answer[0]} cy={answer[1]} r="7" fill="#38bdf8" stroke="#0a0a0b" strokeWidth="1" />
          </g>
        </svg>
      </div>

      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs">
        <p className="text-zinc-400">
          {t("pixel")}{" "}
          <span data-testid="cam-pixel" className="font-mono text-zinc-100">
            ({fixed(distorted[0], 1)}, {fixed(distorted[1], 1)})
          </span>
        </p>
        <p className="text-zinc-400">
          {t("pixelIdeal")}{" "}
          <span data-testid="cam-pixel-ideal" className="font-mono text-zinc-100">
            ({fixed(ideal[0], 1)}, {fixed(ideal[1], 1)})
          </span>
        </p>
        <p className="text-zinc-400">
          {t("pixelDiff")}{" "}
          <span data-testid="cam-err" className="font-mono text-zinc-100">
            {fixed(error, 1)} px
          </span>
        </p>
      </div>

      {ignore && (
        <p className="mt-2 text-xs text-amber-300">{t("ignoreError", { err: fixed(error, 1) })}</p>
      )}

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Slider
          label={t("pointX")}
          value={pointX}
          min={-300}
          max={450}
          step={0.1}
          onChange={setPointX}
          format={(value) => fixed(value, 1)}
          unit="mm"
          testId="cam-X"
        />
        <Slider
          label={t("pointY")}
          value={pointY}
          min={-250}
          max={320}
          step={0.1}
          onChange={setPointY}
          format={(value) => fixed(value, 1)}
          unit="mm"
          testId="cam-Y"
        />
        <Slider
          label={t("pointZ")}
          value={pointZ}
          min={200}
          max={1000}
          step={0.1}
          onChange={setPointZ}
          format={(value) => fixed(value, 1)}
          unit="mm"
          testId="cam-Z"
        />
        <Slider
          label={t("focal")}
          value={fx}
          min={300}
          max={800}
          step={1}
          onChange={setFx}
          format={(value) => fixed(value, 0)}
          unit="px"
          testId="cam-fx"
        />
        <Slider
          label={t("k1")}
          value={k1}
          min={-0.4}
          max={0.2}
          step={0.005}
          onChange={setK1}
          format={(value) => fixed(value, 3)}
          testId="cam-k1"
        />
        <Slider
          label={t("k2")}
          value={k2}
          min={-0.1}
          max={0.1}
          step={0.005}
          onChange={setK2}
          format={(value) => fixed(value, 3)}
          testId="cam-k2"
        />
      </div>

      <div className="mt-3">
        <label className="flex items-center gap-2 text-xs text-zinc-300">
          <input
            data-testid="cam-ignore"
            type="checkbox"
            checked={ignore}
            onChange={(event) => setIgnore(event.target.checked)}
            className="h-5 w-5 cursor-pointer accent-sky-400"
          />
          <span>{t("ignoreDistortion")}</span>
        </label>
      </div>
    </WidgetShell>
  );
}
