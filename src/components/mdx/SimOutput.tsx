import type { ReactNode } from "react";
import { useTranslations } from "next-intl";

const REPO = "https://github.com/liudicsu/Hardware-learning/blob/main";

export interface SimOutputProps {
  /**
   * "avr": firmware run in the simavr simulator with simulated parts; "model": a Python toy model;
   * "ros": real ROS 2 software driving a simulated robot (Gazebo or ros2_control mock hardware);
   * "synthetic": real OpenCV code run on synthetic images rendered through a known camera.
   */
  source: "avr" | "model" | "ros" | "synthetic";
  children: ReactNode;
}

/** The one label for every output that comes from a simulator or a toy model, not from hardware. */
export function SimOutput({ source, children }: SimOutputProps) {
  const t = useTranslations("sim");
  return (
    <figure className="sim-output my-5 rounded-xl border border-amber-400/25 bg-amber-400/[0.03]">
      <figcaption className="not-prose flex flex-wrap items-center gap-x-2 gap-y-1 border-b border-amber-400/15 px-4 py-2 text-xs">
        <span className="rounded-full border border-amber-400/40 px-2 py-0.5 font-semibold uppercase tracking-wide text-amber-300">
          {t("label")}
        </span>
        <span className="text-zinc-300">{t(source)}</span>
        <span className="text-zinc-500">{t("note")}</span>
        <a href={`${REPO}/tools/sim/README.md`} target="_blank" rel="noreferrer" className="ml-auto text-sky-400 hover:text-sky-300">
          {t("reproduce")} ↗
        </a>
      </figcaption>
      <div className="sim-output-body px-2 pb-1">{children}</div>
    </figure>
  );
}
