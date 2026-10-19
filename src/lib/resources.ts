import type { Resource } from "./types";

const seeSite = {
  zh: "版权归原作者所有，使用条款见原网站",
  en: "© the original author; see the site for terms",
};

export const resources: Record<string, Resource> = {
  falstad: {
    id: "falstad",
    url: "https://www.falstad.com/circuit/",
    title: { zh: "Falstad 电路模拟器", en: "Falstad Circuit Simulator" },
    author: "Paul Falstad & Iain Sharp (CircuitJS1)",
    kind: "simulator",
    cost: { zh: "免费 · 浏览器内", en: "Free · in-browser" },
    summary: {
      zh: "动画显示电流流动、用颜色表示电压，先在这里接错电路，零成本看清它为什么不工作。",
      en: "Animated current flow and colour-coded voltages, so you can wire things wrong at zero cost and see exactly why they fail.",
    },
    license: {
      zh: "开源（GPLv2），© Paul Falstad / Iain Sharp；本站仅以 iframe 嵌入官方页面",
      en: "Open source (GPLv2), © Paul Falstad / Iain Sharp; embedded here via iframe of the official page",
    },
  },
  tinkercad: {
    id: "tinkercad",
    url: "https://www.tinkercad.com/circuits",
    title: { zh: "Tinkercad Circuits", en: "Tinkercad Circuits" },
    author: "Autodesk",
    kind: "simulator",
    cost: { zh: "免费 · 需注册账号", en: "Free · account required" },
    summary: {
      zh: "虚拟面包板 + 虚拟 Arduino + 虚拟万用表三合一，在买元件之前就能发现接线错误。",
      en: "A virtual breadboard, Arduino and multimeter in one place, so wiring mistakes show up before you own any parts.",
    },
    license: { zh: "© Autodesk，仅提供外链", en: "© Autodesk; external link only" },
  },
  aac: {
    id: "aac",
    url: "https://www.allaboutcircuits.com/textbook/",
    title: {
      zh: "All About Circuits《Lessons in Electric Circuits》",
      en: "All About Circuits — Lessons in Electric Circuits",
    },
    author: "Tony R. Kuphaldt / All About Circuits",
    kind: "textbook",
    cost: { zh: "免费", en: "Free" },
    summary: {
      zh: "六卷开放许可的电子工程教材。视频讲得含糊时，用它查清楚原理。",
      en: "A six-volume, openly licensed EE textbook. Use it when a video hand-waves something you need to really understand.",
    },
    license: {
      zh: "Design Science License（开放许可），© Tony R. Kuphaldt",
      en: "Design Science License (open), © Tony R. Kuphaldt",
    },
  },
  afrotechmods: {
    id: "afrotechmods",
    url: "https://afrotechmods.com/tutorials/",
    title: { zh: "Afrotechmods 教程视频", en: "Afrotechmods Tutorials" },
    author: "Afrotechmods",
    kind: "video",
    cost: { zh: "免费", en: "Free" },
    summary: {
      zh: "短小、节奏快、幽默的视频，按入门/中级/高级分类。不喜欢讲座式教学就看它。",
      en: "Short, fast, funny videos grouped by level — the right pick if lecture-style teaching doesn't stick for you.",
    },
    license: seeSite,
  },
  "make-electronics": {
    id: "make-electronics",
    url: "https://www.makershed.com/products/make-electronics-3rd-edition-print",
    title: { zh: "《Make: Electronics》第三版", en: "Make: Electronics, 3rd edition" },
    author: "Charles Platt (Make Community)",
    kind: "book",
    cost: { zh: "约 $29.99（纸书）", en: "≈ $29.99 (print)" },
    summary: {
      zh: "给从没拿过万用表的人的最佳纸质书：通过“故意烧坏元件”来理解它们的极限。",
      en: "The best single paper book for absolute beginners, built around deliberately destroying parts to learn their limits.",
    },
    license: { zh: "© Charles Platt，付费书籍，仅外链", en: "© Charles Platt; paid book, link only" },
  },
  "elegoo-super": {
    id: "elegoo-super",
    url: "https://www.elegoo.com/products/elegoo-uno-r3-super-starter-kit",
    title: { zh: "Elegoo UNO R3 Super Starter Kit", en: "Elegoo UNO R3 Super Starter Kit" },
    author: "Elegoo",
    kind: "hardware",
    cost: { zh: "约 $42.99", en: "≈ $42.99" },
    summary: {
      zh: "性价比首选，大多数入门课程用的就是它，附带 22 课 PDF。免焊接。",
      en: "Best-value pick and the kit most beginner courses target; solderless, with a 22-lesson PDF.",
    },
    license: { zh: "商品链接，价格以官网为准", en: "Product link; check the store for current price" },
  },
  "elegoo-basic": {
    id: "elegoo-basic",
    url: "https://www.elegoo.com/products/elegoo-uno-basic-starter-kit",
    title: { zh: "Elegoo UNO Basic Starter Kit", en: "Elegoo UNO Basic Starter Kit" },
    author: "Elegoo",
    kind: "hardware",
    cost: { zh: "约 $19.99", en: "≈ $19.99" },
    summary: {
      zh: "预算紧张时最便宜的正经入门套件：一块 Uno 兼容板加基础无源元件。",
      en: "The cheapest real entry point when money is tight: an Uno clone plus basic passives.",
    },
    license: { zh: "商品链接，价格以官网为准", en: "Product link; check the store for current price" },
  },
  "sparkfun-sik": {
    id: "sparkfun-sik",
    url: "https://www.sparkfun.com/sparkfun-inventor-s-kit-v4-1-2.html",
    title: { zh: "SparkFun Inventor's Kit v4.1.2", en: "SparkFun Inventor's Kit v4.1.2" },
    author: "SparkFun Electronics",
    kind: "hardware",
    cost: { zh: "约 $99.95", en: "≈ $99.95" },
    summary: {
      zh: "课程设计最好的套件：5 个项目 16 个电路，最终做出一台小车。即使买别的套件，它的免费指南也值得读。",
      en: "The best curriculum of any kit — 16 circuits over 5 projects ending in a robot. Its free guide is worth reading even with a cheaper kit.",
    },
    license: { zh: "商品链接，价格以官网为准", en: "Product link; check the store for current price" },
  },
  "adafruit-dmm": {
    id: "adafruit-dmm",
    url: "https://www.adafruit.com/product/2034",
    title: { zh: "Adafruit 9205B+ 数字万用表", en: "Adafruit 9205B+ Digital Multimeter" },
    author: "Adafruit Industries",
    kind: "hardware",
    cost: { zh: "约 $17.50", en: "≈ $17.50" },
    summary: {
      zh: "电压、最高 20A 电流、通断、电阻、电容都能测——够你用好几年。",
      en: "Voltage, current up to 20 A, continuity, resistance and capacitance — everything you need for years.",
    },
    license: { zh: "商品链接，价格以官网为准", en: "Product link; check the store for current price" },
  },
  pinecil: {
    id: "pinecil",
    url: "https://pine64.com/product/pinecil-smart-mini-portable-soldering-iron/",
    title: { zh: "Pinecil V2 智能烙铁", en: "Pinecil V2 Soldering Iron" },
    author: "PINE64",
    kind: "hardware",
    cost: { zh: "约 $26–36", en: "≈ $26–36" },
    summary: {
      zh: "玩具价格的真·恒温烙铁，USB-C 供电，兼容 TS100 / T12 烙铁头。",
      en: "A real temperature-controlled iron for the price of a toy one; USB-C powered, takes TS100 / T12 tips.",
    },
    license: { zh: "商品链接，价格以官网为准", en: "Product link; check the store for current price" },
  },
  "adafruit-soldering": {
    id: "adafruit-soldering",
    url: "https://learn.adafruit.com/adafruit-guide-excellent-soldering",
    title: { zh: "Adafruit 优秀焊接指南", en: "Adafruit Guide to Excellent Soldering" },
    author: "Adafruit Industries",
    kind: "guide",
    cost: { zh: "免费", en: "Free" },
    summary: {
      zh: "烙铁选择、焊点手法、各种常见失败焊点的照片和安全须知——业内公认的参考。",
      en: "Iron choice, joint technique, photos of every common failure, and safety — the reference everyone points to.",
    },
    license: seeSite,
  },
  "sparkfun-multimeter": {
    id: "sparkfun-multimeter",
    url: "https://learn.sparkfun.com/tutorials/how-to-use-a-multimeter",
    title: { zh: "SparkFun：如何使用万用表", en: "SparkFun: How to Use a Multimeter" },
    author: "SparkFun Electronics",
    kind: "guide",
    cost: { zh: "免费", en: "Free" },
    summary: {
      zh: "把电压、电阻、电流、通断讲清楚，还告诉你保险丝烧了怎么办（你一定会烧）。",
      en: "Voltage, resistance, current and continuity done properly — including what to do when you blow the fuse (you will).",
    },
    license: seeSite,
  },
  "sparkfun-resistors": {
    id: "sparkfun-resistors",
    url: "https://learn.sparkfun.com/tutorials/resistors",
    title: { zh: "SparkFun：电阻（含色环读法）", en: "SparkFun: Resistors (incl. colour codes)" },
    author: "SparkFun Electronics",
    kind: "guide",
    cost: { zh: "免费", en: "Free" },
    summary: {
      zh: "电阻的种类、色环读法、串并联计算，适合配合万用表练习。",
      en: "Resistor types, reading colour bands, and series/parallel maths — pairs well with multimeter practice.",
    },
    license: seeSite,
    extra: true,
  },
  cs50p: {
    id: "cs50p",
    url: "https://cs50.harvard.edu/python/",
    title: { zh: "CS50P：Python 编程入门（哈佛）", en: "CS50P: Introduction to Programming with Python" },
    author: "Harvard University (David J. Malan)",
    kind: "course",
    cost: { zh: "免费", en: "Free" },
    summary: {
      zh: "比多数入门课更严谨，有习题集和期末项目；正是这种结构让人能坚持学完。",
      en: "More rigorous than most beginner courses, with problem sets and a final project — the structure is what gets people to finish.",
    },
    license: {
      zh: "CC BY-NC-SA 4.0，© Harvard University",
      en: "CC BY-NC-SA 4.0, © Harvard University",
    },
  },
  py4e: {
    id: "py4e",
    url: "https://www.coursera.org/specializations/python",
    title: { zh: "Python for Everybody（Coursera）", en: "Python for Everybody (Coursera)" },
    author: "University of Michigan (Charles Severance)",
    kind: "course",
    cost: { zh: "可免费旁听", en: "Free to audit" },
    summary: {
      zh: "如果 CS50P 太陡，这是最温和的起点，讲师以对新手友好著称。",
      en: "The gentlest start if CS50P feels too steep, from one of the most beginner-friendly instructors online.",
    },
    license: seeSite,
  },
  "missing-semester": {
    id: "missing-semester",
    url: "https://missing.csail.mit.edu/",
    title: { zh: "MIT《计算机教育中缺失的一课》", en: "The Missing Semester of Your CS Education (MIT)" },
    author: "MIT CSAIL (Anish Athalye, Jon Gjengset, Jose Javier Gonzalez Ortiz)",
    kind: "course",
    cost: { zh: "免费", en: "Free" },
    summary: {
      zh: "Shell、脚本和命令行熟练度——大学课程跳过的部分，而机器人开发全靠命令行。",
      en: "Shell, scripting and command-line fluency that university courses skip — and robotics runs on the command line.",
    },
    license: { zh: "CC BY-NC-SA 4.0，© MIT Missing Semester 作者", en: "CC BY-NC-SA 4.0, © the Missing Semester authors" },
  },
  "learn-git-branching": {
    id: "learn-git-branching",
    url: "https://learngitbranching.js.org/",
    urlByLocale: { zh: "https://learngitbranching.js.org/?locale=zh_CN" },
    title: { zh: "Learn Git Branching（交互式）", en: "Learn Git Branching (interactive)" },
    author: "Peter Cottle & contributors",
    kind: "interactive",
    cost: { zh: "免费 · 支持中文", en: "Free · has a Chinese UI" },
    summary: {
      zh: "理解分支与合并的最佳可视化工具，而这正是 Git 最让人困惑的部分。",
      en: "The best visual tool for branches and merges — the part of Git that confuses everyone.",
    },
    license: { zh: "MIT 开源许可，© Peter Cottle", en: "MIT licence, © Peter Cottle" },
  },
  "pro-git": {
    id: "pro-git",
    url: "https://git-scm.com/book/en/v2",
    urlByLocale: { zh: "https://git-scm.com/book/zh/v2" },
    title: { zh: "《Pro Git》第二版（官方中文版）", en: "Pro Git, 2nd edition (book)" },
    author: "Scott Chacon & Ben Straub",
    kind: "book",
    cost: { zh: "免费在线阅读", en: "Free online" },
    summary: {
      zh: "Git 官方推荐的完整教材，遇到命令细节时当作字典查。",
      en: "The complete Git book recommended by git-scm.com; use it as a reference for command details.",
    },
    license: { zh: "CC BY-NC-SA 3.0，© Scott Chacon & Ben Straub", en: "CC BY-NC-SA 3.0, © Scott Chacon & Ben Straub" },
    extra: true,
  },
  "python-tutorial": {
    id: "python-tutorial",
    url: "https://docs.python.org/3/tutorial/",
    urlByLocale: { zh: "https://docs.python.org/zh-cn/3/tutorial/" },
    title: { zh: "Python 官方教程（中文）", en: "The official Python Tutorial" },
    author: "Python Software Foundation",
    kind: "guide",
    cost: { zh: "免费", en: "Free" },
    summary: {
      zh: "官方、准确、更新及时；venv、模块、文件读写等细节以它为准。",
      en: "Official and accurate; the source of truth for venv, modules, file I/O and the rest.",
    },
    license: { zh: "PSF 文档许可，© Python Software Foundation", en: "PSF documentation licence, © Python Software Foundation" },
    extra: true,
  },
};

export function resourceUrl(r: Resource, locale: "zh" | "en"): string {
  return r.urlByLocale?.[locale] ?? r.url;
}

export function getResource(id: string): Resource {
  const r = resources[id];
  if (!r) throw new Error(`Unknown resource id: ${id}`);
  return r;
}
