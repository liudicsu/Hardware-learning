// Line-by-line port of examples/month-3/so101-arm/sts_packet.py (Feetech STS3215 packets).
import { fixed } from "./format";
import { ljust } from "./pyfmt";

export const PING = 0x01;
export const READ = 0x02;
export const WRITE = 0x03;
export const TORQUE_ENABLE = 40;
export const GOAL_POSITION = 42;
export const PRESENT_POSITION = 56;
export const STEPS_PER_TURN = 4096; // 12-bit magnetic encoder

export function checksum(body: number[]): number {
  return ~body.reduce((a, b) => a + b, 0) & 0xff;
}

export function packet(servoId: number, instruction: number, params: number[] = []): number[] {
  const body = [servoId, params.length + 2, instruction, ...params];
  return [0xff, 0xff, ...body, checksum(body)];
}

export function hexs(data: number[]): string {
  return data.map((b) => b.toString(16).toUpperCase().padStart(2, "0")).join(" ");
}

/** Check a reply and return [id, error byte, params]; throws like the Python. */
export function parseStatus(data: number[]): [number, number, number[]] {
  if (data[0] !== 0xff || data[1] !== 0xff) throw new Error("no 0xFF 0xFF header");
  const [servoId, length, error] = [data[2], data[3], data[4]];
  const params = data.slice(5, 5 + length - 2);
  if (checksum(data.slice(2, 5 + length - 2)) !== data[5 + length - 2]) {
    throw new Error("bad checksum: the bytes were corrupted on the wire");
  }
  return [servoId, error, params];
}

/** Parse "FF FF 06 ..." into bytes; null if any token is not a hex byte. */
export function parseHex(text: string): number[] | null {
  const tokens = text.trim().split(/[\s,]+/).filter(Boolean);
  if (!tokens.length || tokens.some((s) => !/^(0x)?[0-9a-fA-F]{1,2}$/.test(s))) return null;
  return tokens.map((s) => parseInt(s.replace(/^0x/, ""), 16));
}

export function stepsToDeg(steps: number): number {
  return (steps * 360) / STEPS_PER_TURN;
}

/** The lines sts_packet.py prints. */
export function report(): string[] {
  const out: string[] = [];
  const goal = 2048; // half a turn = the middle of the range
  out.push(ljust("ping servo 1:", 32) + " " + hexs(packet(1, PING)));
  out.push(ljust("torque on, servo 1:", 32) + " " + hexs(packet(1, WRITE, [TORQUE_ENABLE, 1])));
  out.push(ljust("goal position 2048, servo 1:", 32) + " " + hexs(packet(1, WRITE, [GOAL_POSITION, goal & 0xff, goal >> 8])));
  out.push(ljust("read present position, servo 6:", 32) + " " + hexs(packet(6, READ, [PRESENT_POSITION, 2])));

  let reply = [0xff, 0xff, 0x06, 0x04, 0x00, 0x2c, 0x0c]; // a made-up answer from servo 6
  reply = [...reply, checksum(reply.slice(2))];
  const [sid, err, params] = parseStatus(reply);
  const steps = params[0] | (params[1] << 8);
  out.push(`reply ${hexs(reply)} -> servo ${sid}, error ${err}, position ${steps} = ${fixed(stepsToDeg(steps), 1)} deg`);
  const broken = [...reply.slice(0, -2), reply[reply.length - 2] ^ 0x01, ...reply.slice(-1)]; // flip one bit on the wire
  try {
    parseStatus(broken);
  } catch (e) {
    out.push(`reply ${hexs(broken)} -> ${(e as Error).message}`);
  }
  return out;
}
