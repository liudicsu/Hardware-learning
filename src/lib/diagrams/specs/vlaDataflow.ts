import type { BlockDiagramSpec, Layout } from "../types";

/*
 * m6/vla-models "What a VLA is" (D118): the three parts of a VLA and its two kinds of action output.
 * Model placement, checked against the papers (arXiv ids) and bound to both lesson texts by facts + bindings:
 *  - RT-2 (2307.15818 §3.2): 256 uniform bins, one step = 8 integers. OpenVLA (2406.09246 §3.3): 256 bins between
 *    the 1st and 99th quantile (instead of RT-2's min-max), 7-D, one step. Neither reads joint state.
 *  - pi0-FAST (2501.09747 §V-B, Table I): whole 1 s chunk -> DCT per dimension -> scale and round -> BPE (vocab
 *    1024), ~30 tokens per arm per chunk (DROID: 29 vs 105 binned); still decoded one token after another.
 *  - pi0 (2410.24164 §3), SmolVLA (2506.01844 §3.1), GR00T N1 (2503.14734 §2.1): VLM + flow-matching action expert
 *    / DiT. pi0 and GR00T feed the joint state to the action expert / DiT, SmolVLA and pi0-FAST to the VLM.
 *  - pi0.5 (2504.16054 Fig. 3, §IV-B): pretrained with FAST tokens only, flow-matching action expert added in
 *    post-training and used at inference.
 *  - Octo (2405.12213 §III-A): diffusion head, but no VLM: shallow CNN patches + frozen t5-base, 27M/93M transformer
 *    trained from scratch.
 * The numbers (256 bins; this lesson's 1 s chunk = 30 steps x 6 joints = 180 tokens) come from action_tokens.py:
 * check_diagrams runs the script and needs the chunk line in its output.
 */

const SCRIPT = "examples/month-6/vla-models/action_tokens.py";
const EN = "src/content/m6/vla-models/en.mdx";
const ZH = "src/content/m6/vla-models/zh.mdx";

// Same values as action_tokens.py:16 (HZ, CHUNK, JOINTS, BINS); a fact and the script run below tie them to the file.
const HZ = 30, CHUNK = 30, JOINTS = 6, BINS = 256;
const TOKENS = CHUNK * JOINTS;
const SECONDS = CHUNK / HZ;

// Model names: used in the drawn boxes, the step text and the lesson facts, so they cannot drift apart.
const STEP_MODELS = ["RT-2", "OpenVLA"] as const; // one step per call, 256 bins per dimension
const FAST_MODEL = "π0-FAST"; // whole chunk, DCT + BPE
const HEAD_MODELS = ["π0", "SmolVLA", "GR00T"] as const; // VLM + flow-matching action head
const LATE_HEAD = "π0.5"; // FAST tokens in pretraining, action expert from post-training on
const NO_VLM = "Octo"; // diffusion head, no VLM
const MOST = { zh: "多数模型", en: "most models" };
// Where the joint state goes (pi0-FAST 2501.09747 App. C and pi0.5 §IV-A: as text tokens; SmolVLA §3.1: into the VLM;
// pi0 §3 and GR00T §2.1: into the action expert / DiT; RT-2, OpenVLA and the released Octo: not used).
const STATE_IN_LM = [FAST_MODEL, LATE_HEAD, "SmolVLA"] as const;
const STATE_IN_HEAD = ["π0", "GR00T"] as const;
const NO_STATE = ["RT-2", "OpenVLA", NO_VLM] as const;
// Tokens per call: RT-2 8 integers (2307.15818 §3.2), OpenVLA 7-D (2406.09246 §3.3); FAST about 30 per arm per 1 s
// chunk (2501.09747 §VI-B). The lesson's token bullet is a fact with the same numbers.
const STEP_TOKENS = [8, 7] as const;
const FAST_PER_ARM = 30;
// pi0.5's qualifier in the head box and the step: FAST tokens only in pretraining, head added in post-training.
const LATE_NOTE = { zh: "（后训练才加此头）", en: " (head added\nin post-training)" };
const andList = (xs: readonly string[]) => (xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`);
const zhList = (xs: readonly string[]) => xs.join("、");
const esc = (t: string) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// "π0" alone, not the start of π0-FAST or π0.5
const bare = (t: string) => `${esc(t)}(?![-.\\w])`;

// Wide (xl and up): inputs on the left, language model in the middle, the two outputs on the right,
// motor targets underneath. tokens -> motors runs around the right edge so no lines cross.
const wide: Layout = {
  w: 750,
  h: 300,
  nodes: {
    image: [10, 0, 150, 40],
    instr: [10, 64, 150, 40],
    joint: [10, 126, 150, 46],
    encoder: [200, 0, 150, 46],
    tok: [200, 64, 150, 46],
    lm: [390, 0, 150, 230],
    tokens: [570, 0, 150, 112],
    head: [570, 120, 150, 112],
    motors: [390, 262, 330, 36],
  },
  edges: {
    imgEnc: { pts: [[160, 20], [198, 20]] },
    instrTok: { pts: [[160, 84], [198, 84]] },
    feat: { pts: [[350, 23], [388, 23]] },
    text: { pts: [[350, 87], [388, 87]] },
    state: { pts: [[160, 149], [388, 149]] },
    lmTok: { pts: [[540, 56], [568, 56]] },
    lmHead: { pts: [[540, 176], [568, 176]] },
    tokMot: { pts: [[720, 56], [740, 56], [740, 280], [722, 280]] },
    headMot: { pts: [[645, 232], [645, 260]] },
  },
};

// Narrow (phones): the same blocks top to bottom.
const narrow: Layout = {
  w: 340,
  h: 476,
  nodes: {
    image: [10, 0, 150, 40],
    instr: [180, 0, 150, 40],
    encoder: [10, 64, 150, 46],
    tok: [180, 64, 150, 46],
    joint: [220, 132, 110, 46],
    lm: [10, 200, 320, 64],
    tokens: [10, 294, 150, 112],
    head: [180, 294, 150, 112],
    motors: [10, 438, 320, 36],
  },
  edges: {
    imgEnc: { pts: [[85, 40], [85, 62]] },
    instrTok: { pts: [[255, 40], [255, 62]] },
    feat: { pts: [[85, 110], [85, 198]] },
    text: { pts: [[195, 110], [195, 198]] },
    state: { pts: [[275, 178], [275, 198]] },
    lmTok: { pts: [[85, 264], [85, 292]] },
    lmHead: { pts: [[255, 264], [255, 292]] },
    tokMot: { pts: [[85, 406], [85, 436]] },
    headMot: { pts: [[255, 406], [255, 436]] },
  },
};

const [RT2, OPENVLA] = STEP_MODELS;
const [PI0, SMOLVLA, GR00T] = HEAD_MODELS;

export const vlaDataflow: BlockDiagramSpec = {
  kind: "block",
  id: "vla-dataflow",
  title: { zh: "VLA 的三个部分与两种动作输出", en: "The three parts of a VLA and its two action outputs" },
  caption: {
    zh: `示意图，不对应某个具体模型的层数或尺寸。关节状态在 ${zhList(STATE_IN_LM)} 里进语言模型，在 ${zhList(STATE_IN_HEAD)} 里进动作头；${zhList(NO_STATE.slice(0, -1))} 和发布版 ${NO_VLM} 不读关节状态。虚线箭头只画出进语言模型的这条路径；在 ${zhList(STATE_IN_HEAD)} 里，关节状态绕过语言模型，直接进动作头。${BINS} 个区间和 ${TOKENS} 个词元来自本课的 action_tokens.py（6 关节、${HZ} Hz、1 秒一块）。`,
    en: `A sketch, not the layers or sizes of any one model. The joint state goes into the language model in ${andList(STATE_IN_LM)}, and into the action head in ${andList(STATE_IN_HEAD)}; ${NO_STATE.slice(0, -1).join(", ")} and the released ${NO_VLM} do not read it. The dashed arrow draws only the route into the language model; in ${andList(STATE_IN_HEAD)} the joint state bypasses the language model and goes straight to the action head. The ${BINS} bins and ${TOKENS} tokens come from this lesson's action_tokens.py (6 joints, ${HZ} Hz, 1 s chunks).`,
  },
  sources: [SCRIPT],
  nodes: [
    { id: "image", label: { zh: "相机图像", en: "camera image" }, tone: "ink" },
    { id: "instr", label: { zh: "文字指令", en: "instruction" }, tone: "ink" },
    { id: "joint", label: { zh: "关节状态", en: "joint state" }, sub: { zh: `（${MOST.zh}）`, en: `(${MOST.en})` }, tone: "muted" },
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
      sub: {
        zh: `一个接一个生成\n${RT2}、${OPENVLA}：\n每步、每维 ${BINS} 区间\n${FAST_MODEL}：整块\nDCT + BPE 压缩`,
        en: `one after another\n${RT2}, ${OPENVLA}:\none step, ${BINS}\nbins per dimension\n${FAST_MODEL}: whole\nchunk, DCT + BPE`,
      },
      tone: "a",
    },
    {
      id: "head",
      label: { zh: "② 动作头", en: "② action head" },
      sub: {
        zh: `扩散或流匹配\n一次一整块\n${PI0}、${SMOLVLA}、${GR00T}\n${LATE_HEAD}${LATE_NOTE.zh}\n${NO_VLM}（不基于 VLM）`,
        en: `diffusion or flow\nmatching, one chunk\n${PI0}, ${SMOLVLA}, ${GR00T}\n${LATE_HEAD}${LATE_NOTE.en}\n${NO_VLM} (no VLM)`,
      },
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
        zh: `输入：视觉编码器把每张相机图像变成一串特征向量；指令被分成文字词元；${MOST.zh}还读入机器人的关节状态（有的进语言模型，${PI0} 和 ${GR00T} 则进动作头）。`,
        en: `Inputs: the vision encoder turns each camera image into a sequence of feature vectors; the instruction is split into text tokens; ${MOST.en} also read the robot's joint state (some in the language model, ${PI0} and ${GR00T} in the action head).`,
      },
      highlight: ["image", "imgEnc", "encoder", "instr", "instrTok", "tok", "joint"],
    },
    {
      label: {
        zh: `语言模型读入图像特征和文字词元（关节状态只在 ${zhList(STATE_IN_LM)} 里进语言模型）。视觉编码器和语言模型来自预训练的视觉-语言模型（${NO_VLM} 例外：它从零训练，文字由冻结的 T5 编码器处理）；与机器人相关的学习主要在动作输出和微调里。`,
        en: `The language model reads the image features and the text tokens (the joint state too, but only in ${andList(STATE_IN_LM)}). The vision encoder and the language model come from a pretrained vision-language model (${NO_VLM} is the exception: it is trained from scratch, with a frozen T5 text encoder); the robot-specific learning is mostly in the action output and the fine-tuning.`,
      },
      highlight: ["encoder", "feat", "tok", "text", "joint", "state", "lm"],
    },
    {
      label: {
        zh: `做法 ①：语言模型一个接一个地生成动作词元。${RT2} 和 ${OPENVLA} 每次只输出一步（${STEP_TOKENS[0]} 个和 ${STEP_TOKENS[1]} 个词元），每个动作维度 ${BINS} 个区间。${FAST_MODEL} 先用 DCT + BPE 把一整块压缩，每条手臂每秒约 ${FAST_PER_ARM} 个词元。本课自己的例子里，按区间编码的 1 秒（${CHUNK} 步 × ${JOINTS} 个关节）是 ${TOKENS} 个词元。`,
        en: `Way ①: the language model generates action tokens one after another. ${RT2} and ${OPENVLA} output one step per call (${STEP_TOKENS.join(" and ")} tokens), ${BINS} bins per action dimension. ${FAST_MODEL} first compresses a whole chunk with DCT + BPE, about ${FAST_PER_ARM} tokens per arm per second. In this lesson's own example, ${SECONDS} s of binned actions (${CHUNK} steps × ${JOINTS} joints) is ${TOKENS} tokens.`,
      },
      highlight: ["lm", "lmTok", "tokens", "tokMot", "motors"],
    },
    {
      label: {
        zh: `做法 ②：语言模型的特征送进一个较小的网络，用扩散或流匹配一次生成一整块连续动作（${PI0}、${SMOLVLA}、${GR00T}）。${LATE_HEAD} 预训练时只用 FAST 词元，运行时用后训练才加上的流匹配动作专家。${NO_VLM} 也有扩散头，但不基于视觉-语言模型。`,
        en: `Way ②: the language model's features go into a smaller network that produces a whole chunk of continuous actions by diffusion or flow matching (${PI0}, ${SMOLVLA}, ${GR00T}). ${LATE_HEAD} uses FAST tokens only in pretraining and runs the flow-matching action expert added in post-training. ${NO_VLM} also has a diffusion head, but no vision-language model.`,
      },
      highlight: ["lm", "lmHead", "head", "headMot", "motors"],
    },
  ],
  script: { run: SCRIPT, lines: [`One ${CHUNK}-step chunk (${SECONDS} s) from a new episode: ${CHUNK} x ${JOINTS} = ${TOKENS} numbers`] },
  bindings: [
    {
      node: "tokens",
      has: [...STEP_MODELS.map(esc), esc(FAST_MODEL), `${BINS}`, { zh: "整块", en: "whole\\s+chunk" }, "DCT \\+ BPE"],
      lacks: [bare(PI0), esc(SMOLVLA), esc(GR00T), esc(LATE_HEAD), esc(NO_VLM)],
      note: "token box: step models with 256 bins, π0-FAST with whole-chunk DCT + BPE, no head models",
    },
    {
      node: "head",
      has: [bare(PI0), esc(SMOLVLA), esc(GR00T), esc(LATE_HEAD), `${esc(NO_VLM)}[^\\n]*VLM`],
      lacks: [...STEP_MODELS.map(esc), esc(FAST_MODEL), "\\b\\d{3}\\b"],
      note: "head box: head models, π0.5 qualified, Octo marked as no VLM; no bins",
    },
    { node: "joint", has: [{ zh: esc(MOST.zh), en: esc(MOST.en) }], note: "joint state: only most models (lesson)" },
    { node: "lm", has: [{ zh: "预训练", en: "pretrained" }], note: "language model from a pretrained VLM" },
    { edge: "state", dashed: true, note: "joint state is optional, so its arrow is dashed" },
    {
      node: "head",
      has: [{ zh: `${esc(LATE_HEAD)}${esc(LATE_NOTE.zh)}`, en: `${esc(LATE_HEAD)}${esc(LATE_NOTE.en)}` }],
      note: "π0.5: action head only from post-training on",
    },
    {
      step: 2,
      has: [{ zh: `关节状态只在 ${zhList(STATE_IN_LM).replace(/\./g, "\\.")} 里进语言模型`, en: `only in ${esc(andList(STATE_IN_LM))}` }],
      note: "step 2: the language model reads the joint state only in some models",
    },
    {
      step: 3,
      has: [
        { zh: `${STEP_TOKENS[0]} 个和 ${STEP_TOKENS[1]} 个词元`, en: `\\(${STEP_TOKENS.join(" and ")} tokens\\)` },
        { zh: `约 ${FAST_PER_ARM} 个词元`, en: `about ${FAST_PER_ARM} tokens per arm` },
      ],
      note: "step 3: tokens per call (RT-2 8, OpenVLA 7) and FAST's ~30 per arm",
    },
    {
      step: 4,
      has: [{ zh: `${esc(LATE_HEAD)} 预训练时只用 FAST 词元`, en: `${esc(LATE_HEAD)} uses FAST tokens only in pretraining` }],
      note: "step 4: π0.5 qualifier",
    },
    {
      caption: true,
      has: [
        { zh: `在 ${zhList(STATE_IN_LM).replace(/\./g, "\\.")} 里进语言模型，在 ${zhList(STATE_IN_HEAD)} 里进动作头`, en: `into the language model in ${esc(andList(STATE_IN_LM))}, and into the action head in ${esc(andList(STATE_IN_HEAD))}` },
        { zh: `${NO_STATE.slice(0, -1).join("、")} 和发布版 ${NO_VLM} 不读`, en: `${NO_STATE.slice(0, -1).join(", ")} and the released ${NO_VLM} do not read it` },
      ],
      note: "caption: where the joint state goes",
    },
  ],
  facts: [
    { file: SCRIPT, pattern: `^HZ, CHUNK, JOINTS, BINS = ${HZ}, ${CHUNK}, ${JOINTS}, ${BINS}$`, note: "constants match action_tokens.py" },
    { file: EN, pattern: `${RT2} and ${OPENVLA} give each action dimension ${BINS} tokens`, note: "en: 256 bins per dimension" },
    { file: ZH, pattern: `${RT2} 和 ${OPENVLA} 给每个动作维度 ${BINS} 个词元`, note: "zh: 256 bins per dimension" },
    { file: EN, pattern: "RT-2 uses the whole range of the data\\. OpenVLA sets the range with the dataset's 1st and 99th percentile", note: "en: percentiles are OpenVLA's, not RT-2's" },
    { file: ZH, pattern: "RT-2 用数据的整个范围。OpenVLA 改用数据集的第 1 和第 99 百分位数确定范围", note: "zh: percentiles are OpenVLA's, not RT-2's" },
    { file: EN, pattern: `one second of a ${JOINTS}-joint arm is ${TOKENS} tokens`, note: "en: 1 s = 180 tokens" },
    { file: ZH, pattern: `一台 ${JOINTS} 关节机械臂的 1 秒动作就是 ${TOKENS} 个词元`, note: "zh: 1 s = 180 tokens" },
    { file: EN, pattern: `\\(and, in ${esc(MOST.en)}, the robot's joint state, fed into the language model or the action head\\)`, note: "en: joint state in most models, into the LM or the action head" },
    { file: ZH, pattern: `（${esc(MOST.zh)}还会读入机器人的关节状态，送进语言模型或动作头）`, note: "zh: joint state in most models, into the LM or the action head" },
    { file: EN, pattern: `The first two come from a pretrained vision-language model \\(in every model below except ${NO_VLM}\\)`, note: "en: encoder + LM pretrained, except Octo" },
    { file: ZH, pattern: `前两部分来自预训练好的视觉-语言模型（下面除 ${NO_VLM} 外的模型都是如此）`, note: "zh: encoder + LM pretrained, except Octo" },
    { file: EN, pattern: `${RT2} and ${OPENVLA} work like this, one action step per call \\(${STEP_TOKENS.join(" and ")} tokens\\); ${esc(FAST_MODEL)} does too, but its tokeniser, FAST, compresses a whole chunk first`, note: "en: token models, π0-FAST on whole chunks" },
    { file: ZH, pattern: `${RT2} 和 ${OPENVLA} 是这样做的，每次调用输出一步动作（分别是 ${STEP_TOKENS[0]} 个和 ${STEP_TOKENS[1]} 个词元）；${esc(FAST_MODEL)} 也是，但它的分词器 FAST 会先把一整块动作压缩`, note: "zh: token models, π0-FAST on whole chunks" },
    { file: EN, pattern: `by diffusion or flow matching[^\\n]*${HEAD_MODELS.slice(0, -1).map(esc).join(", ")} and ${GR00T} work like this\\. ${esc(LATE_HEAD)} is pretrained on FAST tokens only, gets a flow-matching action expert in post-training`, note: "en: action-head models, π0.5 qualified" },
    { file: ZH, pattern: `通过扩散或流匹配[^\\n]*${HEAD_MODELS.slice(0, -1).map(esc).join("、")} 和 ${GR00T} 是这样做的。${esc(LATE_HEAD)} 预训练时只用 FAST 词元，后训练时加上流匹配动作专家`, note: "zh: action-head models, π0.5 qualified" },
    { file: EN, pattern: `${NO_VLM} also has a diffusion head but no vision-language model: it is a small transformer trained from scratch, with a frozen T5 text encoder`, note: "en: Octo has no VLM" },
    { file: ZH, pattern: `${NO_VLM} 也有扩散动作头，但没有视觉-语言模型：它是一个从零训练的小型 Transformer，文字由冻结的 T5 编码器处理`, note: "zh: Octo has no VLM" },
    { file: EN, pattern: `\\| ${NO_VLM} \\| [^|]*\\| small transformer trained from scratch \\(no vision-language model\\)`, note: "en table: Octo has no VLM" },
    { file: ZH, pattern: `\\| ${NO_VLM} \\| [^|]*\\| 从零训练的小型 Transformer（没有视觉-语言模型）`, note: "zh table: Octo has no VLM" },
    { file: EN, pattern: `${esc(LATE_HEAD)} is pretrained on FAST tokens only and adds the action expert in post-training \\|`, note: "en table: π0.5 qualified" },
    { file: ZH, pattern: `${esc(LATE_HEAD)} 预训练只用 FAST 词元，后训练加上动作专家 \\|`, note: "zh table: π0.5 qualified" },
  ],
};
