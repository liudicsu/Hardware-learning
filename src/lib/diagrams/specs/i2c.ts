import type { TimingSpec } from "../types";

/*
 * m2/sensors-fusion: the I²C transaction behind readReg(REG_WHO_AM_I) in imu_pitch.ino, field by field.
 * Sequence from the MPU-6000/MPU-6050 Product Specification (PS-MPU-6000A-00, rev 3.4):
 *   §9.2 I²C Interface: 7-bit slave address b110100X, X = AD0 (0x68 with AD0 low);
 *   §9.3 I²C Communications Protocol, "Single-Byte Read Sequence":
 *        S, AD+W, ACK, RA, ACK, Sr, AD+R, ACK, DATA, NACK, P.
 * Register: Register Map and Descriptions (RM-MPU-6000A-00, rev 4.2) §4.32, register 117 = 0x75 WHO_AM_I,
 * reset value 0x68. The firmware constants are tied to these numbers by the facts below.
 */

const ADDR = 0x68; // MPU, AD0 low
const REG = 0x75; // REG_WHO_AM_I
const WHO = 0x68; // WHO_AM_I reset value, printed by the sketch
const hex = (v: number) => "0x" + v.toString(16).toUpperCase().padStart(2, "0");
const bin = (v: number, bits: number) => v.toString(2).padStart(bits, "0");
const AD_W = (ADDR << 1) | 0;
const AD_R = (ADDR << 1) | 1;

const UNO = "Uno";
const MPU = "MPU";
// one column per field; w = relative width (byte fields wider, one-letter fields narrower)
const FIELDS: { v: string; from: string; w?: number }[] = [
  { v: "S", from: UNO, w: 0.9 },
  { v: hex(ADDR), from: UNO, w: 1.4 },
  { v: "W", from: UNO, w: 0.9 },
  { v: "ACK", from: MPU, w: 1.2 },
  { v: hex(REG), from: UNO, w: 1.4 },
  { v: "ACK", from: MPU, w: 1.2 },
  { v: "Sr", from: UNO, w: 0.9 },
  { v: hex(ADDR), from: UNO, w: 1.4 },
  { v: "R", from: UNO, w: 0.9 },
  { v: "ACK", from: MPU, w: 1.2 },
  { v: hex(WHO), from: MPU, w: 1.4 },
  { v: "NACK", from: UNO, w: 1.4 },
  { v: "P", from: UNO, w: 0.9 },
];

const INO = "examples/month-2/sensors-fusion/imu_pitch/imu_pitch.ino";
const EN = "src/content/m2/sensors-fusion/en.mdx";
const ZH = "src/content/m2/sensors-fusion/zh.mdx";

export const i2cWhoAmI: TimingSpec = {
  kind: "timing",
  id: "i2c-read-who-am-i",
  title: { zh: "I2C 单字节读：readReg(REG_WHO_AM_I) 在总线上的样子", en: "I2C single-byte read: readReg(REG_WHO_AM_I) on the bus" },
  caption: {
    zh: `每一列是 SDA 上的一个字段。S、Sr、P 是 SCL 为高时 SDA 的跳变；地址占 7 个时钟，加上第 8 个时钟的读/写位；寄存器和数据字节各占 8 个时钟；ACK/NACK 是第 9 个时钟，由接收方给出。顺序与 MPU-6050 产品规格书（rev 3.4）§9.3 的“单字节读”序列一致；地址 b110100X 见 §9.2，WHO_AM_I（${hex(REG)}，复位值 ${hex(WHO)}）见寄存器手册（rev 4.2）§4.32。`,
    en: `Each column is one field on SDA. S, Sr and P are SDA edges while SCL is HIGH; an address takes 7 clocks plus the read/write bit on clock 8; the register and data bytes take 8 clocks each; ACK/NACK is clock 9, given by the receiver. The order is the "Single-Byte Read Sequence" of the MPU-6050 Product Specification (rev 3.4) §9.3; the address b110100X is in §9.2 and WHO_AM_I (${hex(REG)}, reset value ${hex(WHO)}) in the Register Map (rev 4.2) §4.32.`,
  },
  sources: [INO, EN, ZH],
  columns: FIELDS.map((f) => f.w ?? 1),
  columnScale: 42,
  signals: [{ name: "SDA", kind: "bus", values: FIELDS.map((f) => f.v), tone: "a" }],
  rows: [{ name: { zh: "发送方", en: "from" }, cells: FIELDS.map((f) => f.from) }],
  spans: [
    { from: 1, to: 5, label: { zh: "写入寄存器地址", en: "write the register address" } },
    { from: 7, to: 9, label: { zh: "读地址", en: "read address" } },
    { from: 10, to: 11, label: { zh: "1 个字节", en: "1 byte" } },
  ],
  lines: [
    [0, 5],
    [6, 12],
  ],
  narrowLines: [
    [0, 5],
    [6, 9],
    [10, 12],
  ],
  steps: [
    {
      column: 0,
      label: {
        zh: "START（S）：Uno 在 SCL 为高时把 SDA 拉低，总线被占用。Wire.beginTransmission(MPU) 只是填缓冲区，真正上总线发生在 endTransmission()。",
        en: "START (S): the Uno pulls SDA LOW while SCL is HIGH and the bus is busy. Wire.beginTransmission(MPU) only fills a buffer; the bus activity happens in endTransmission().",
      },
    },
    {
      column: 1,
      label: {
        zh: `7 位地址 ${hex(ADDR)} = ${bin(ADDR, 7)}（AD0 接低电平），高位先发。`,
        en: `7-bit address ${hex(ADDR)} = ${bin(ADDR, 7)} (AD0 low), most significant bit first.`,
      },
    },
    {
      column: 2,
      label: {
        zh: `第 8 位 W = 0（写）。线上的整个字节是 ${hex(ADDR)} × 2 + 0 = ${hex(AD_W)}。`,
        en: `Bit 8: W = 0 (write). The whole byte on the wire is ${hex(ADDR)} × 2 + 0 = ${hex(AD_W)}.`,
      },
    },
    {
      column: 3,
      label: {
        zh: "ACK：认出地址的 MPU-6050 在第 9 个时钟把 SDA 拉低。没有器件应答时 SDA 保持高（NACK），endTransmission() 返回 2。",
        en: "ACK: the MPU-6050 recognises its address and pulls SDA LOW on clock 9. If no device answers, SDA stays HIGH (NACK) and endTransmission() returns 2.",
      },
    },
    {
      column: 4,
      label: {
        zh: `Wire.write(reg)：寄存器地址 ${hex(REG)}（WHO_AM_I）= ${bin(REG, 8)}，设置 MPU-6050 的寄存器指针。`,
        en: `Wire.write(reg): register address ${hex(REG)} (WHO_AM_I) = ${bin(REG, 8)}, which sets the MPU-6050's register pointer.`,
      },
    },
    { column: 5, label: { zh: "ACK：MPU-6050 收下了寄存器地址。", en: "ACK: the MPU-6050 has taken the register address." } },
    {
      column: 6,
      label: {
        zh: "Wire.endTransmission(false)：不发 STOP，而是重复起始（Sr）。总线不释放，MPU-6050 保留刚设置的寄存器指针。",
        en: "Wire.endTransmission(false): no STOP but a repeated START (Sr). The bus stays busy and the MPU-6050 keeps the register pointer just set.",
      },
    },
    {
      column: 7,
      label: {
        zh: `Wire.requestFrom(MPU, 1)：再发一次同一个地址 ${hex(ADDR)}。`,
        en: `Wire.requestFrom(MPU, 1): the same address ${hex(ADDR)} again.`,
      },
    },
    {
      column: 8,
      label: {
        zh: `这次第 8 位 R = 1（读），线上的字节是 ${hex(ADDR)} × 2 + 1 = ${hex(AD_R)}。`,
        en: `This time bit 8 is R = 1 (read); the byte on the wire is ${hex(ADDR)} × 2 + 1 = ${hex(AD_R)}.`,
      },
    },
    { column: 9, label: { zh: "ACK：MPU-6050 应答，接下来由它驱动 SDA。", en: "ACK: the MPU-6050 answers and now drives SDA." } },
    {
      column: 10,
      label: {
        zh: `数据字节 ${hex(WHO)}：WHO_AM_I 的内容，程序打印 WHO_AM_I = 0x${WHO.toString(16)}。`,
        en: `Data byte ${hex(WHO)}: the content of WHO_AM_I; the sketch prints WHO_AM_I = 0x${WHO.toString(16)}.`,
      },
    },
    {
      column: 11,
      label: {
        zh: "NACK：Uno 在第 9 个时钟让 SDA 保持高，表示这是它要的最后一个字节。",
        en: "NACK: the Uno leaves SDA HIGH on clock 9: this is the last byte it wants.",
      },
    },
    {
      column: 12,
      label: { zh: "STOP（P）：SCL 为高时 SDA 由低变高，总线空闲。", en: "STOP (P): SDA rises while SCL is HIGH, and the bus is free." },
    },
  ],
  numbers: [
    { note: "address byte for a write = 0x68 << 1 | 0 = 0xD0", value: AD_W, expect: 0xd0, tol: 0 },
    { note: "address byte for a read = 0x68 << 1 | 1 = 0xD1", value: AD_R, expect: 0xd1, tol: 0 },
    { note: "datasheet §9.2: address b110100X with AD0 = 0 → 0b1101000", value: ADDR, expect: 0b1101000, tol: 0 },
    { note: "register map §4.32: WHO_AM_I is register 117", value: REG, expect: 117, tol: 0 },
    { note: "fields per datasheet single-byte read sequence (S, AD+W, ACK, RA, ACK, Sr, AD+R, ACK, DATA, NACK, P; address and R/W drawn separately)", value: FIELDS.length, expect: 13, tol: 0 },
  ],
  facts: [
    { file: INO, pattern: `const uint8_t MPU = ${hex(ADDR)};`, note: "firmware address" },
    { file: INO, pattern: `const uint8_t REG_WHO_AM_I = ${hex(REG)};`, note: "firmware WHO_AM_I register" },
    { file: INO, pattern: "uint8_t readReg\\(uint8_t reg\\) \\{\\n  Wire\\.beginTransmission\\(MPU\\);\\n  Wire\\.write\\(reg\\);\\n  Wire\\.endTransmission\\(false\\);.*\\n  Wire\\.requestFrom\\(MPU, \\(uint8_t\\)1\\);", note: "readReg: write register, repeated start, read 1 byte" },
    { file: INO, pattern: "readReg\\(REG_WHO_AM_I\\)", note: "firmware reads WHO_AM_I" },
    { file: EN, pattern: `WHO_AM_I = ${hex(WHO)}`, note: "simulated output WHO_AM_I = 0x68" },
    { file: EN, pattern: `\\| WHO_AM_I \\| ${hex(REG)} \\| Always reads ${hex(WHO)}`, note: "lesson register table" },
    { file: ZH, pattern: `\\| WHO_AM_I \\| ${hex(REG)} \\| 固定读出 ${hex(WHO)}`, note: "zh lesson register table" },
    { file: EN, pattern: "on the MPU-6050, AD0 LOW gives 0x68 and AD0 HIGH gives 0x69", note: "lesson AD0 address" },
    { file: ZH, pattern: "MPU-6050 的 AD0 接低电平是 0x68，接高电平是 0x69", note: "zh lesson AD0 address" },
    { file: EN, pattern: "A return value of 2 means the address was not acknowledged", note: "lesson: endTransmission() returns 2 on an address NACK" },
    { file: ZH, pattern: "返回 2 表示地址没有得到应答", note: "zh lesson: returns 2 on an address NACK" },
    { file: EN, pattern: "`endTransmission\\(false\\)` sends a repeated start instead of releasing the bus", note: "lesson repeated start" },
    { file: ZH, pattern: "`endTransmission\\(false\\)` 发出重复起始（repeated start）而不是释放总线", note: "zh lesson repeated start" },
  ],
};
