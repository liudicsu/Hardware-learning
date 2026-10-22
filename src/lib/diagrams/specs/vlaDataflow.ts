import type { BlockDiagramSpec, Layout } from "../types";

/*
 * m6/vla-models "What a VLA is" (D118): the three parts of a VLA and its two kinds of action output.
 * The model names and the three-part structure are checked against both lesson texts.
 * The numbers (256 bins; a 1 s chunk = 30 steps x 6 joints = 180 tokens) come from action_tokens.py:
 * check_diagrams runs the script and needs the chunk line in its output.
 */

const SCRIPT = "examples/month-6/vla-models/action_tokens.py";
const EN = "src/content/m6/vla-models/en.mdx";
const ZH = "src/content/m6/vla-models/zh.mdx";

// Same values as action_tokens.py:16 (HZ, CHUNK, JOINTS, BINS); a fact and the script run below tie them to the file.
const HZ = 30, CHUNK = 30, JOINTS = 6, BINS = 256;
const TOKENS = CHUNK * JOINTS;
const SECONDS = CHUNK / HZ;

// Wide (xl and up): inputs on the left, language model in the middle, the two outputs on the right,
// motor targets underneath. tokens -> motors runs around the right edge so no lines cross.
const wide: Layout = {
  w: 750,
  h: 240,
  nodes: {
    image: [10, 0, 150, 40],
    instr: [10, 64, 150, 40],
    joint: [10, 126, 150, 46],
    encoder: [200, 0, 150, 46],
    tok: [200, 64, 150, 46],
    lm: [390, 0, 150, 172],
    tokens: [570, 0, 150, 84],
    head: [570, 92, 150, 84],
    motors: [390, 202, 330, 36],
  },
  edges: {
    imgEnc: { pts: [[160, 20], [198, 20]] },
    instrTok: { pts: [[160, 84], [198, 84]] },
    feat: { pts: [[350, 23], [388, 23]] },
    text: { pts: [[350, 87], [388, 87]] },
    state: { pts: [[160, 149], [388, 149]] },
    lmTok: { pts: [[540, 42], [568, 42]] },
    lmHead: { pts: [[540, 134], [568, 134]] },
    tokMot: { pts: [[720, 42], [740, 42], [740, 220], [722, 220]] },
    headMot: { pts: [[645, 176], [645, 200]] },
  },
};

// Narrow (phones): the same blocks top to bottom.
const narrow: Layout = {
  w: 340,
  h: 446,
  nodes: {
    image: [10, 0, 150, 40],
    instr: [180, 0, 150, 40],
    encoder: [10, 64, 150, 46],
    tok: [180, 64, 150, 46],
    joint: [220, 132, 110, 46],
    lm: [10, 200, 320, 64],
    tokens: [10, 294, 150, 84],
    head: [180, 294, 150, 84],
    motors: [10, 408, 320, 36],
  },
  edges: {
    imgEnc: { pts: [[85, 40], [85, 62]] },
    instrTok: { pts: [[255, 40], [255, 62]] },
    feat: { pts: [[85, 110], [85, 198]] },
    text: { pts: [[195, 110], [195, 198]] },
    state: { pts: [[275, 178], [275, 198]] },
    lmTok: { pts: [[85, 264], [85, 292]] },
    lmHead: { pts: [[255, 264], [255, 292]] },
    tokMot: { pts: [[85, 378], [85, 406]] },
    headMot: { pts: [[255, 378], [255, 406]] },
  },
};

export const vlaDataflow: BlockDiagramSpec = {
  kind: "block",
  id: "vla-dataflow",
  title: { zh: "VLA 的三个部分与两种动作输出", en: "The three parts of a VLA and its two action outputs" },
  caption: {
    zh: `示意图，不对应某个具体模型的层数或尺寸。${BINS} 个区间和 ${TOKENS} 个词元来自本课的 action_tokens.py（6 关节、${HZ} Hz、1 秒一块）。`,
    en: `A sketch, not the layers or sizes of any one model. The ${BINS} bins and ${TOKENS} tokens come from this lesson's action_tokens.py (6 joints, ${HZ} Hz, 1 s chunks).`,
  },
  sources: [SCRIPT],
  nodes: [
    { id: "image", label: { zh: "相机图像", en: "camera image" }, tone: "ink" },
    { id: "instr", label: { zh: "文字指令", en: "instruction" }, tone: "ink" },
    { id: "joint", label: { zh: "关节状态", en: "joint state" }, sub: { zh: "（多数模型）", en: "(most models)" }, tone: "muted" },
    { id: "encoder", label: { zh: "视觉编码器", en: "vision encoder" }, sub: { zh: "→ 特征向量", en: "→ feature vectors" }, tone: "b" },
    { id: "tok", label: { zh: "分词", en: "tokeniser" }, sub: { zh: "→ 文字词元", en: "→ text tokens" }, tone: "b" },
    {
      id: "lm",
      label: { zh: "语言模型", en: "language model" },
      sub: { zh: "来自预训练的\n视觉-语言模型", en: "from a pretrained\nvision-language\nmodel" },
      tone: "b",
    },
    {
      id: "tokens",
      label: { zh: "① 动作词元", en: "① action tokens" },
      sub: { zh: `每维 ${BINS} 个区间\n一个接一个生成\nRT-2、OpenVLA、\nπ0-FAST`, en: `${BINS} bins per dim.\none after another\nRT-2, OpenVLA,\nπ0-FAST` },
      tone: "a",
    },
    {
      id: "head",
      label: { zh: "② 动作头", en: "② action head" },
      sub: { zh: "扩散或流匹配\n一次输出一整块\nOcto、π0、π0.5、\nSmolVLA、GR00T", en: "diffusion or flow\nmatching, one chunk\nOcto, π0, π0.5,\nSmolVLA, GR00T" },
      tone: "c",
    },
    { id: "motors", label: { zh: "给电机的数字（关节目标）", en: "numbers for the motors (joint targets)" }, tone: "ok" },
  ],
  edges: [
    { id: "imgEnc", tone: "ink" },
    { id: "instrTok", tone: "ink" },
    { id: "feat", tone: "b" },
    { id: "text", tone: "b" },
    { id: "state", tone: "muted", dashed: true },
    { id: "lmTok", tone: "a" },
    { id: "lmHead", tone: "c" },
    { id: "tokMot", tone: "a" },
    { id: "headMot", tone: "c" },
  ],
  layouts: { wide, narrow },
  steps: [
    {
      label: {
        zh: "输入：视觉编码器把每张相机图像变成一串特征向量；指令被分成文字词元；多数模型还读入机器人的关节状态。",
        en: "Inputs: the vision encoder turns each camera image into a sequence of feature vectors; the instruction is split into text tokens; most models also read the robot's joint state.",
      },
      highlight: ["image", "imgEnc", "encoder", "instr", "instrTok", "tok", "joint"],
    },
    {
      label: {
        zh: "语言模型把这些一起读入。视觉编码器和语言模型来自预训练的视觉-语言模型；与机器人相关的学习主要在动作输出和微调里。",
        en: "The language model reads them all together. The vision encoder and the language model come from a pretrained vision-language model; the robot-specific learning is mostly in the action output and the fine-tuning.",
      },
      highlight: ["encoder", "feat", "tok", "text", "joint", "state", "lm"],
    },
    {
      label: {
        zh: `做法 ①：语言模型一个接一个地生成动作词元，每个动作维度 ${BINS} 个区间。本课的例子里，1 秒（${CHUNK} 步 × ${JOINTS} 个关节）就是 ${TOKENS} 个词元，再按区间换回角度。`,
        en: `Way ①: the language model generates action tokens one after another, ${BINS} bins per action dimension. In this lesson's example, ${SECONDS} s (${CHUNK} steps × ${JOINTS} joints) is ${TOKENS} tokens, turned back into angles bin by bin.`,
      },
      highlight: ["lm", "lmTok", "tokens", "tokMot", "motors"],
    },
    {
      label: {
        zh: "做法 ②：语言模型的特征送进一个较小的网络，用扩散或流匹配一次生成一整块连续动作，不经过词元。",
        en: "Way ②: the language model's features go into a smaller network that produces a whole chunk of continuous actions by diffusion or flow matching, with no tokens in between.",
      },
      highlight: ["lm", "lmHead", "head", "headMot", "motors"],
    },
  ],
  script: { run: SCRIPT, lines: [`One ${CHUNK}-step chunk (${SECONDS} s) from a new episode: ${CHUNK} x ${JOINTS} = ${TOKENS} numbers`] },
  facts: [
    { file: SCRIPT, pattern: `^HZ, CHUNK, JOINTS, BINS = ${HZ}, ${CHUNK}, ${JOINTS}, ${BINS}$`, note: "constants match action_tokens.py" },
    { file: EN, pattern: `RT-2 and OpenVLA give each action dimension ${BINS} tokens`, note: "en: 256 bins per dimension" },
    { file: ZH, pattern: `RT-2 和 OpenVLA 给每个动作维度 ${BINS} 个词元`, note: "zh: 256 bins per dimension" },
    { file: EN, pattern: `one second of a ${JOINTS}-joint arm is ${TOKENS} tokens`, note: "en: 1 s = 180 tokens" },
    { file: ZH, pattern: `一台 ${JOINTS} 关节机械臂的 1 秒动作就是 ${TOKENS} 个词元`, note: "zh: 1 s = 180 tokens" },
    { file: EN, pattern: "\\(and, in most models, the robot's joint state\\)", note: "en: joint state in most models" },
    { file: ZH, pattern: "（多数模型还会读入机器人的关节状态）", note: "zh: joint state in most models" },
    { file: EN, pattern: "The first two come from a pretrained vision-language model", note: "en: encoder + LM are pretrained" },
    { file: ZH, pattern: "前两部分来自预训练好的视觉-语言模型", note: "zh: encoder + LM are pretrained" },
    { file: EN, pattern: "RT-2 and OpenVLA work like this; π0-FAST does too", note: "en: token models" },
    { file: ZH, pattern: "RT-2 和 OpenVLA 是这样做的；π0-FAST 也是", note: "zh: token models" },
    { file: EN, pattern: "by diffusion or flow matching[^\\n]*Octo, π0, π0\\.5, SmolVLA and GR00T work like this", note: "en: action-head models" },
    { file: ZH, pattern: "通过扩散或流匹配[^\\n]*Octo、π0、π0\\.5、SmolVLA 和 GR00T 是这样做的", note: "zh: action-head models" },
  ],
};
