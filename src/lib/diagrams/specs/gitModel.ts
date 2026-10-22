import type { BlockDiagramSpec } from "../types";

/*
 * m1/git-github: the three areas (git add / git commit) and the branch picture
 * (main A-B-C, feature D-E from C, HEAD -> feature -> E), as described in the lesson text.
 */

const EN = "src/content/m1/git-github/en.mdx";
const ZH = "src/content/m1/git-github/zh.mdx";

export const gitAreas: BlockDiagramSpec = {
  kind: "block",
  id: "git-areas",
  title: { zh: "Git 的三个区域", en: "Git's three areas" },
  sources: [EN, ZH],
  nodes: [
    { id: "wd", label: { zh: "工作区", en: "working directory" }, sub: { zh: "你的修改", en: "your edits" } },
    { id: "stage", label: { zh: "暂存区", en: "staging area" }, sub: { zh: "索引（index）", en: "index" }, tone: "b" },
    { id: "repo", label: { zh: "仓库", en: "repository" }, sub: { zh: ".git 目录", en: ".git folder" }, tone: "a" },
  ],
  edges: [
    { id: "add", label: "git add", mono: true, tone: "b" },
    { id: "commit", label: "git commit", mono: true, tone: "a" },
  ],
  layouts: {
    wide: {
      w: 700,
      h: 56,
      nodes: { wd: [0, 5, 170, 46], stage: [265, 5, 170, 46], repo: [530, 5, 170, 46] },
      edges: {
        add: { pts: [[170, 28], [263, 28]], label: [216, 21] },
        commit: { pts: [[435, 28], [528, 28]], label: [481, 21] },
      },
    },
    narrow: {
      w: 340,
      h: 220,
      nodes: { wd: [80, 4, 180, 44], stage: [80, 88, 180, 44], repo: [80, 172, 180, 44] },
      edges: {
        add: { pts: [[170, 48], [170, 86]], label: [176, 71], anchor: "start" },
        commit: { pts: [[170, 132], [170, 170]], label: [176, 155], anchor: "start" },
      },
    },
  },
  facts: [
    { file: EN, pattern: "filled by `git add`\\), and the \\*\\*repository\\*\\* \\(the `\\.git` folder", note: "lesson text: git add fills the staging area; repository is .git" },
    { file: EN, pattern: "`git commit` turns whatever is staged into a new commit", note: "lesson text: git commit takes the staged content" },
  ],
};

export const gitBranches: BlockDiagramSpec = {
  kind: "block",
  id: "git-branches",
  title: { zh: "分支是指向提交的标签，HEAD 指向当前分支", en: "A branch is a label on a commit; HEAD points to the current branch" },
  sources: [EN, ZH],
  nodes: [
    { id: "A", label: "A", shape: "state" },
    { id: "B", label: "B", shape: "state" },
    { id: "C", label: "C", shape: "state" },
    { id: "D", label: "D", shape: "state" },
    { id: "E", label: "E", shape: "state" },
    { id: "main", label: "main", mono: true, tone: "a" },
    { id: "feature", label: "feature", mono: true, tone: "ok" },
    { id: "head", label: "HEAD", mono: true, tone: "b" },
  ],
  edges: [
    { id: "ab", arrow: false },
    { id: "bc", arrow: false },
    { id: "cd", arrow: false },
    { id: "de", arrow: false },
    { id: "mainC", tone: "a" },
    { id: "featE", tone: "ok" },
    { id: "headF", tone: "b" },
  ],
  layouts: {
    wide: {
      w: 540,
      h: 196,
      nodes: {
        A: [40, 50, 36, 36],
        B: [130, 50, 36, 36],
        C: [220, 50, 36, 36],
        D: [310, 110, 36, 36],
        E: [400, 110, 36, 36],
        main: [208, 4, 60, 26],
        feature: [383, 166, 70, 26],
        head: [474, 166, 56, 26],
      },
      edges: {
        ab: { pts: [[76, 68], [130, 68]] },
        bc: { pts: [[166, 68], [220, 68]] },
        cd: { pts: [[250, 81], [314, 116]] },
        de: { pts: [[346, 128], [400, 128]] },
        mainC: { pts: [[238, 30], [238, 48]] },
        featE: { pts: [[418, 166], [418, 148]] },
        headF: { pts: [[474, 179], [455, 179]] },
      },
    },
    narrow: {
      w: 340,
      h: 196,
      nodes: {
        A: [10, 50, 32, 32],
        B: [80, 50, 32, 32],
        C: [150, 50, 32, 32],
        D: [210, 110, 32, 32],
        E: [280, 110, 32, 32],
        main: [136, 4, 60, 26],
        feature: [256, 166, 70, 26],
        head: [178, 166, 56, 26],
      },
      edges: {
        ab: { pts: [[42, 66], [80, 66]] },
        bc: { pts: [[112, 66], [150, 66]] },
        cd: { pts: [[178, 78], [214, 114]] },
        de: { pts: [[242, 126], [280, 126]] },
        mainC: { pts: [[166, 30], [166, 48]] },
        featE: { pts: [[296, 166], [296, 144]] },
        headF: { pts: [[234, 179], [254, 179]] },
      },
    },
  },
  steps: [
    {
      label: { zh: "A、B、C 在 main 上；main 这个标签指向最新的提交 C。", en: "A, B and C are on main; the main label points at the newest commit, C." },
      highlight: ["A", "B", "C", "ab", "bc", "main", "mainC"],
    },
    {
      label: { zh: "feature 从 C 分出，又多了两个提交 D 和 E；feature 标签指向 E。", en: "feature started at C and has two more commits, D and E; the feature label points at E." },
      highlight: ["C", "D", "E", "cd", "de", "feature", "featE"],
    },
    {
      label: {
        zh: "HEAD 指向 feature，所以磁盘上的文件就是快照 E。切换到 main，文件变成快照 C；D 和 E 依然存在，因为 feature 还指着它们。",
        en: "HEAD points to feature, so the files on disk look like snapshot E. Switch to main and they become snapshot C; D and E still exist because feature still points at them.",
      },
      highlight: ["head", "headF", "feature", "featE", "E"],
    },
  ],
  facts: [
    { file: EN, pattern: "A, B and C are on `main`\\. `feature` started at C and has two more commits, D and E\\.", note: "lesson text: main A-B-C, feature D-E from C" },
    { file: EN, pattern: "HEAD points to `feature`, so the files on disk look like snapshot E", note: "lesson text: HEAD -> feature -> E" },
  ],
};
