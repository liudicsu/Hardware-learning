"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { fixed } from "@/lib/models/format";
import {
  GOAL_POSITION,
  hexs,
  packet,
  parseHex,
  parseStatus,
  PING,
  PRESENT_POSITION,
  READ,
  stepsToDeg,
  TORQUE_ENABLE,
  WRITE,
} from "@/lib/models/stsPacket";
import { Slider } from "./Slider";
import { WidgetShell } from "./WidgetShell";

type Kind = "ping" | "torque" | "goal" | "read";
const DEFAULTS = { kind: "goal" as Kind, id: 1, goal: 2048, torque: 1, reply: "FF FF 06 04 00 2C 0C BD" };

function build(kind: Kind, id: number, goal: number, torque: number): number[] {
  if (kind === "ping") return packet(id, PING);
  if (kind === "torque") return packet(id, WRITE, [TORQUE_ENABLE, torque]);
  if (kind === "goal") return packet(id, WRITE, [GOAL_POSITION, goal & 0xff, goal >> 8]);
  return packet(id, READ, [PRESENT_POSITION, 2]);
}

export function StsPacketWidget() {
  const t = useTranslations("widget");
  const [kind, setKind] = useState<Kind>(DEFAULTS.kind);
  const [id, setId] = useState(DEFAULTS.id);
  const [goal, setGoal] = useState(DEFAULTS.goal);
  const [torque, setTorque] = useState(DEFAULTS.torque);
  const [reply, setReply] = useState(DEFAULTS.reply);
  const bytes = build(kind, id, goal, torque);

  let parsed: string;
  let good = false;
  const data = parseHex(reply);
  if (!data) parsed = t("stsNotHex");
  else if (data.length < 6 || data.length < 4 + data[3]) parsed = t("stsShort");
  else {
    try {
      const [sid, err, params] = parseStatus(data);
      good = true;
      if (params.length >= 2) {
        const steps = params[0] | (params[1] << 8);
        parsed = t("stsReplyPos", { id: sid, err, steps, deg: fixed(stepsToDeg(steps), 1) });
      } else parsed = t("stsReplyOk", { id: sid, err });
    } catch (e) {
      parsed = (e as Error).message.startsWith("bad checksum") ? t("stsBadChecksum") : t("stsNoHeader");
    }
  }

  const kinds: Kind[] = ["ping", "torque", "goal", "read"];
  return (
    <WidgetShell
      title={t("stsTitle")}
      script="examples/month-3/so101-arm/sts_packet.py"
      onReset={() => {
        setKind(DEFAULTS.kind);
        setId(DEFAULTS.id);
        setGoal(DEFAULTS.goal);
        setTorque(DEFAULTS.torque);
        setReply(DEFAULTS.reply);
      }}
    >
      <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-zinc-300">
        {kinds.map((k) => (
          <label key={k} className="flex items-center gap-2">
            <input
              type="radio"
              name="sts-kind"
              checked={kind === k}
              onChange={() => setKind(k)}
              data-testid={`sts-kind-${k}`}
              className="h-5 w-5 cursor-pointer accent-sky-400"
            />
            {t(`sts_${k}`)}
          </label>
        ))}
      </div>
      <p className="mt-3 break-all font-mono text-sm text-sky-300" data-testid="sts-bytes">
        {hexs(bytes)}
      </p>
      <p className="mt-1 text-xs text-zinc-500">{t("stsLayout")}</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <Slider label={t("stsId")} value={id} min={0} max={253} step={1} onChange={setId} testId="sts-id" />
        {kind === "goal" && (
          <Slider
            label={t("stsGoal")}
            value={goal}
            min={0}
            max={4095}
            step={1}
            onChange={setGoal}
            format={(v) => `${v} = ${fixed(stepsToDeg(v), 1)}°`}
            testId="sts-goal"
          />
        )}
        {kind === "torque" && (
          <Slider label={t("stsTorque")} value={torque} min={0} max={1} step={1} onChange={setTorque} testId="sts-torque" />
        )}
      </div>
      <label className="mt-5 block text-xs text-zinc-400">
        {t("stsReply")}
        <input
          type="text"
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          data-testid="sts-reply"
          spellCheck={false}
          className="mt-1 block w-full min-w-0 rounded-lg border border-white/10 bg-black/30 px-2 py-1.5 font-mono text-sm text-zinc-100"
        />
      </label>
      <p className={`mt-2 text-xs ${good ? "text-emerald-300" : "text-red-300"}`} data-testid="sts-parsed">
        {parsed}
      </p>
    </WidgetShell>
  );
}
