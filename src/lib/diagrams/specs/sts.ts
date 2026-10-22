import type { BytesSpec, BytesSpecByte, L10n } from "../types";

/*
 * m3/so101-arm: the Feetech STS3215 packets of sts_packet.py, byte by byte.
 * The bytes are built here with the same rules as the script (LENGTH = params + 2,
 * CHECKSUM = ~(ID + LENGTH + INSTRUCTION/ERROR + PARAMS) & 0xFF, two-byte values little-endian), and
 * check_diagrams runs `python3 sts_packet.py` and requires each packet's hex line in its output.
 */

const PING = 0x01, READ = 0x02, WRITE = 0x03;
const TORQUE_ENABLE = 40, GOAL_POSITION = 42, PRESENT_POSITION = 56;
const STEPS_PER_TURN = 4096;
const GOAL = 2048;

const hex = (v: number) => v.toString(16).toUpperCase().padStart(2, "0");
const hexs = (bs: number[]) => bs.map(hex).join(" ");
const checksum = (body: number[]) => ~body.reduce((a, b) => a + b, 0) & 0xff;
const sumHex = (body: number[]) => "0x" + hex(body.reduce((a, b) => a + b, 0) & 0xff);

type Note = L10n;
const b = (v: number, field: string, note: Note, bad = false): BytesSpecByte => ({ v, field, note, ...(bad ? { bad } : {}) });

const HEADER: BytesSpecByte[] = [
  b(0xff, "header", { zh: "包头第 1 字节", en: "header, first byte" }),
  b(0xff, "header", { zh: "包头第 2 字节", en: "header, second byte" }),
];
const INSTR: Record<number, L10n> = {
  [PING]: "PING (0x01)",
  [READ]: { zh: "READ（0x02）读寄存器", en: "READ (0x02): read registers" },
  [WRITE]: { zh: "WRITE（0x03）写寄存器", en: "WRITE (0x03): write registers" },
};

/** An instruction packet: FF FF ID LENGTH INSTRUCTION PARAMS CHECKSUM. */
function request(id: number, instr: number, params: BytesSpecByte[]): BytesSpecByte[] {
  const body = [id, params.length + 2, instr, ...params.map((p) => p.v)];
  return [
    ...HEADER,
    b(id, "id", { zh: `舵机 ${id}`, en: `servo ${id}` }),
    b(body[1], "length", { zh: `${params.length} 个参数 + 2 = ${body[1]}`, en: `${params.length} params + 2 = ${body[1]}` }),
    b(instr, "instruction", INSTR[instr]),
    ...params,
    b(checksum(body), "checksum", `~${sumHex(body)} & 0xFF = 0x${hex(checksum(body))}`),
  ];
}
const sumLabel = (bs: BytesSpecByte[], from: number, to: number, cs: number): L10n => {
  const body = bs.slice(from, to + 1).map((x) => x.v);
  const want = checksum(body);
  const t = want === cs ? `Σ = ${sumHex(body)} → ~ = ${hex(want)}` : `Σ = ${sumHex(body)} → ~ = ${hex(want)} ≠ ${hex(cs)}`;
  return t;
};

const ping = request(1, PING, []);
const torque = request(1, WRITE, [
  b(TORQUE_ENABLE, "param", { zh: `地址 ${TORQUE_ENABLE} = Torque_Enable`, en: `address ${TORQUE_ENABLE} = Torque_Enable` }),
  b(1, "param", { zh: "值 1：扭矩使能", en: "value 1: torque on" }),
]);
const goal = request(1, WRITE, [
  b(GOAL_POSITION, "param", { zh: `地址 ${GOAL_POSITION} = Goal_Position`, en: `address ${GOAL_POSITION} = Goal_Position` }),
  b(GOAL & 0xff, "param", { zh: `低字节（${GOAL} & 0xFF）`, en: `low byte (${GOAL} & 0xFF)` }),
  b(GOAL >> 8, "param", { zh: `高字节（${GOAL} >> 8）`, en: `high byte (${GOAL} >> 8)` }),
]);
const read = request(6, READ, [
  b(PRESENT_POSITION, "param", { zh: `起始地址 ${PRESENT_POSITION} = Present_Position`, en: `start address ${PRESENT_POSITION} = Present_Position` }),
  b(2, "param", { zh: "读 2 个字节", en: "read 2 bytes" }),
]);

/** A status packet: FF FF ID LENGTH ERROR PARAMS CHECKSUM, with the checksum the servo sent. */
const POS_LO = 0x2c, POS_HI = 0x0c;
function status(hi: number, cs: number, bad: boolean): BytesSpecByte[] {
  return [
    ...HEADER,
    b(6, "id", { zh: "舵机 6 回复", en: "reply from servo 6" }),
    b(4, "length", { zh: "错误字节 + 2 个数据字节 + 校验和 = 4", en: "error byte + 2 data bytes + checksum = 4" }),
    b(0, "error", { zh: "0：没有错误", en: "0: no error" }),
    b(POS_LO, "param", { zh: "位置低字节", en: "position, low byte" }),
    b(hi, "param", bad ? { zh: `位置高字节，一个比特被翻转（0C → ${hex(hi)}）`, en: `position, high byte, one bit flipped (0C → ${hex(hi)})` } : { zh: "位置高字节", en: "position, high byte" }, bad),
    b(cs, "checksum", bad ? { zh: `收到 ${hex(cs)}，按收到的字节应为 ${hex(checksum([6, 4, 0, POS_LO, hi]))}`, en: `received ${hex(cs)}; the received bytes need ${hex(checksum([6, 4, 0, POS_LO, hi]))}` } : `~${sumHex([6, 4, 0, POS_LO, hi])} & 0xFF = 0x${hex(cs)}`),
  ];
}
const REPLY_CS = checksum([6, 4, 0, POS_LO, POS_HI]);
const reply = status(POS_HI, REPLY_CS, false);
const broken = status(POS_HI ^ 0x01, REPLY_CS, true);
const STEPS = POS_LO | (POS_HI << 8);
const DEG = (STEPS * 360) / STEPS_PER_TURN;

const bytesOf = (bs: BytesSpecByte[]) => bs.map((x) => x.v);
const last = (bs: BytesSpecByte[]) => bs.length - 1;

const PY = "examples/month-3/so101-arm/sts_packet.py";
const EN = "src/content/m3/so101-arm/en.mdx";
const ZH = "src/content/m3/so101-arm/zh.mdx";
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const LINES = {
  ping: `ping servo 1:                    ${hexs(bytesOf(ping))}`,
  torque: `torque on, servo 1:              ${hexs(bytesOf(torque))}`,
  goal: `goal position 2048, servo 1:     ${hexs(bytesOf(goal))}`,
  read: `read present position, servo 6:  ${hexs(bytesOf(read))}`,
  reply: `reply ${hexs(bytesOf(reply))} -> servo 6, error 0, position ${STEPS} = ${DEG.toFixed(1)} deg`,
  broken: `reply ${hexs(bytesOf(broken))} -> bad checksum: the bytes were corrupted on the wire`,
};

export const stsPackets: BytesSpec = {
  kind: "bytes",
  id: "sts-packet-fields",
  title: { zh: "STS3215 数据包：每个字节是什么", en: "STS3215 packets: what every byte means" },
  caption: {
    zh: "颜色表示字段：包头、ID、LENGTH、指令（回复里是错误字节）、参数、校验和。下方括号是校验和覆盖的字节；两字节的数值低字节在前（小端序）。字节与 sts_packet.py 的输出逐字相同。",
    en: "Colours mark the fields: header, ID, LENGTH, instruction (the error byte in a reply), parameters, checksum. The lower bracket spans the bytes the checksum covers; two-byte values are little-endian (low byte first). The bytes are identical to the output of sts_packet.py.",
  },
  sources: [PY, EN, ZH],
  fields: {
    header: { label: { zh: "包头", en: "header" }, tone: "muted" },
    id: { label: "ID", tone: "a" },
    length: { label: { zh: "长度 LENGTH", en: "LENGTH" }, tone: "b" },
    instruction: { label: { zh: "指令", en: "instruction" }, tone: "ok" },
    error: { label: { zh: "错误字节", en: "error" }, tone: "ok" },
    param: { label: { zh: "参数", en: "parameter" }, tone: "ink" },
    checksum: { label: { zh: "校验和", en: "checksum" }, tone: "c" },
  },
  packets: [
    {
      id: "ping",
      label: { zh: "ping 1 号", en: "ping 1" },
      bytes: ping,
      groups: [{ from: 2, to: last(ping) - 1, side: "bottom", label: sumLabel(ping, 2, last(ping) - 1, ping[last(ping)].v) }],
      summary: { zh: "没有参数，所以 LENGTH = 2（指令 + 校验和）。", en: "No parameters, so LENGTH = 2 (instruction + checksum)." },
    },
    {
      id: "torque",
      label: { zh: "扭矩使能", en: "torque on" },
      bytes: torque,
      groups: [{ from: 2, to: last(torque) - 1, side: "bottom", label: sumLabel(torque, 2, last(torque) - 1, torque[last(torque)].v) }],
      summary: { zh: `两个参数：寄存器地址 ${TORQUE_ENABLE} 和值 1，所以 LENGTH = 4。`, en: `Two parameters, register address ${TORQUE_ENABLE} and the value 1, so LENGTH = 4.` },
    },
    {
      id: "goal",
      label: { zh: `目标 ${GOAL}`, en: `goal ${GOAL}` },
      bytes: goal,
      groups: [
        { from: 6, to: 7, label: `0x${GOAL.toString(16).toUpperCase().padStart(4, "0")} = ${GOAL}` },
        { from: 2, to: last(goal) - 1, side: "bottom", label: sumLabel(goal, 2, last(goal) - 1, goal[last(goal)].v) },
      ],
      summary: {
        zh: `三个参数：地址 ${GOAL_POSITION} 和 ${GOAL} 的两个字节。${GOAL} = 0x0800，低字节 00 在前，高字节 08 在后。`,
        en: `Three parameters: address ${GOAL_POSITION} and the two bytes of ${GOAL}. ${GOAL} = 0x0800, low byte 00 first, high byte 08 second.`,
      },
    },
    {
      id: "read",
      label: { zh: "读 6 号位置", en: "read servo 6" },
      bytes: read,
      groups: [{ from: 2, to: last(read) - 1, side: "bottom", label: sumLabel(read, 2, last(read) - 1, read[last(read)].v) }],
      summary: { zh: `请 6 号舵机从寄存器 ${PRESENT_POSITION} 开始回 2 个字节。`, en: `Asks servo 6 for 2 bytes starting at register ${PRESENT_POSITION}.` },
    },
    {
      id: "reply",
      label: { zh: "回复", en: "reply" },
      bytes: reply,
      groups: [
        { from: 5, to: 6, label: `0x${hex(POS_HI)}${hex(POS_LO)} = ${STEPS} = ${DEG.toFixed(1)}°` },
        { from: 2, to: last(reply) - 1, side: "bottom", label: sumLabel(reply, 2, last(reply) - 1, reply[last(reply)].v) },
      ],
      summary: {
        zh: `回复里第 5 个字节是错误字节，不是指令。位置 ${STEPS} 步 × 360 / ${STEPS_PER_TURN} = ${DEG.toFixed(1)}°。`,
        en: `In a reply the fifth byte is the error byte, not an instruction. Position ${STEPS} steps × 360 / ${STEPS_PER_TURN} = ${DEG.toFixed(1)}°.`,
      },
    },
    {
      id: "broken",
      label: { zh: "校验和不对", en: "bad checksum" },
      bytes: broken,
      groups: [{ from: 2, to: last(broken) - 1, side: "bottom", label: sumLabel(broken, 2, last(broken) - 1, broken[last(broken)].v) }],
      summary: {
        zh: "高位数据字节翻转了一个比特。按收到的字节重算的校验和与收到的不一致，所以整包被拒绝，0x0D2C 不会被当成位置。",
        en: "One bit of the high data byte flipped. The checksum recomputed from the received bytes differs from the one received, so the packet is refused and 0x0D2C is never taken as a position.",
      },
    },
  ],
  script: { run: PY, lines: Object.values(LINES) },
  numbers: [
    { note: "LENGTH of the goal packet = 3 params + 2", value: goal[3].v, expect: 5, tol: 0 },
    { note: "goal checksum sum 0x3B (lesson: decimal 59)", value: [1, 5, 3, 42, 0, 8].reduce((a, c) => a + c, 0), expect: 59, tol: 0 },
    { note: "reply position 0x0C2C = 3116 steps (lesson)", value: STEPS, expect: 3116, tol: 0 },
    { note: "3116 × 360 / 4096 = 273.9° (lesson)", value: DEG, expect: 273.9, tol: 0.05 },
    { note: "flipped byte is the high data byte (index 6 of the reply)", value: broken.findIndex((x) => x.bad), expect: 6, tol: 0 },
  ],
  facts: [
    ...Object.entries(LINES).map(([k, line]) => ({ file: EN, pattern: esc(line), note: `lesson output line: ${k}` })),
    ...Object.entries(LINES).map(([k, line]) => ({ file: ZH, pattern: esc(line), note: `zh lesson output line: ${k}` })),
    { file: PY, pattern: "TORQUE_ENABLE, GOAL_POSITION, PRESENT_POSITION = 40, 42, 56", note: "register addresses" },
    { file: PY, pattern: "PING, READ, WRITE = 0x01, 0x02, 0x03", note: "instruction codes" },
    { file: PY, pattern: "STEPS_PER_TURN = 4096", note: "encoder steps per turn" },
    { file: EN, pattern: "2048 = 0x0800 → low byte 00, high byte 08", note: "lesson little-endian split" },
    { file: ZH, pattern: "2048 = 0x0800 → 低字节 00，高字节 08", note: "zh lesson little-endian split" },
    { file: EN, pattern: "flips one bit in the high data byte, 0C becomes 0D", note: "lesson: the flipped byte is the high data byte" },
    { file: ZH, pattern: "把高位数据字节的一个比特翻转，0C 变成 0D", note: "zh lesson: the flipped byte is the high data byte" },
  ],
};
