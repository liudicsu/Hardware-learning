import type { PoseGraphPose, PoseGraphSpec } from "../types";

/*
 * m4/slam-nav: the pose graph in four frames (D091). Illustrative: the route (a 2.8 m x 2.0 m loop with
 * 0.4 m bends), the odometry error (every turn 3 % short) and the linear spreading of the correction are
 * assumptions of this diagram. What is not assumed: a node is stored after 0.2 m or 0.2 rad
 * (slam.yaml minimum_travel_distance / minimum_travel_heading), which check_diagrams verifies node by node
 * against the yaml values.
 */

const SLAM_YAML = "examples/month-4/slam-nav/m4_nav/config/slam.yaml";
const EN = "src/content/m4/slam-nav/en.mdx";
const ZH = "src/content/m4/slam-nav/zh.mdx";

const DISTANCE = 0.2; // m, minimum_travel_distance
const HEADING = 0.2; // rad, minimum_travel_heading
const STEP = 0.005; // m per integration step
const TURN_ERROR = -0.03; // odometry turns 3 % short (assumed)
const BEND = 0.4; // m, bend radius
const ARC = (Math.PI / 2) * BEND;
// [length m, curvature 1/m]: straight 2.0, bend, 1.2, bend, 2.0, bend, 1.2, bend -> back at the start
const ROUTE: [number, number][] = [
  [2.0, 0], [ARC, 1 / BEND], [1.2, 0], [ARC, 1 / BEND], [2.0, 0], [ARC, 1 / BEND], [1.2, 0], [ARC, 1 / BEND],
];

function drive() {
  const t: PoseGraphPose = { x: 0, y: 0, th: 0 };
  const o: PoseGraphPose = { x: 0, y: 0, th: 0 };
  const advance = (p: PoseGraphPose, ds: number, k: number) => {
    p.th += (k * ds) / 2;
    p.x += ds * Math.cos(p.th);
    p.y += ds * Math.sin(p.th);
    p.th += (k * ds) / 2;
  };
  const estimate: PoseGraphPose[] = [{ ...o }];
  const truth: PoseGraphPose[] = [{ ...t }];
  let lastTh = 0;
  let dist = 0;
  for (const [len, k] of ROUTE) {
    const n = Math.round(len / STEP);
    const ds = len / n;
    for (let i = 0; i < n; i++) {
      advance(t, ds, k);
      advance(o, ds, k * (1 + TURN_ERROR));
      dist += ds;
      // SLAM Toolbox: process a scan once the robot has moved minimum_travel_distance OR turned minimum_travel_heading
      if (dist >= DISTANCE - 1e-9 || Math.abs(o.th - lastTh) >= HEADING - 1e-9) {
        estimate.push({ ...o });
        truth.push({ ...t });
        lastTh = o.th;
        dist = 0;
      }
    }
  }
  return { estimate, truth, end: { ...t } };
}

const { estimate, truth, end } = drive();
const N = estimate.length - 1;
const last = estimate[N];
// Loop closure (illustrative): the last scan matches node 0's scan, which fixes the last node at its true
// place; the correction is spread along the chain in proportion to the node index.
const fix = { x: truth[N].x - last.x, y: truth[N].y - last.y, th: truth[N].th - last.th };
const corrected = estimate.map((p, i) => ({ x: p.x + (fix.x * i) / N, y: p.y + (fix.y * i) / N, th: p.th + (fix.th * i) / N }));
const gap = Math.hypot(fix.x, fix.y);
const GAP_LABEL = 0.28; // m, drawn on the graph

export const slamPoseGraph: PoseGraphSpec = {
  kind: "poseGraph",
  id: "slam-pose-graph",
  title: { zh: "SLAM Toolbox 的位姿图，分四步", en: "SLAM Toolbox's pose graph in four steps" },
  caption: {
    zh: "示意图：路线、每次转弯少算 3 % 的里程计误差，以及修正量的分摊方式都是假设的；0.2 m / 0.2 rad 的节点间隔取自 slam.yaml，检查脚本逐个节点复核。SLAM Toolbox 实际用图优化求出修正，而不是按节点序号线性分摊。",
    en: "Illustrative: the route, the odometry error (every turn 3 % short) and the way the correction is spread are assumed; the 0.2 m / 0.2 rad node spacing comes from slam.yaml and is checked node by node. SLAM Toolbox computes the correction by graph optimisation, not by spreading it linearly over the nodes.",
  },
  sources: [SLAM_YAML, EN, ZH],
  estimate,
  corrected,
  truth,
  travel: { distance: DISTANCE, heading: HEADING },
  step: STEP,
  matchWindow: 3,
  text: {
    start: { zh: "起点", en: "start" },
    spacing: "0.2 m",
    gap: `≈ ${GAP_LABEL} m`,
  },
  legend: {
    odom: { zh: "节点和里程计边", en: "nodes and odometry edges" },
    match: { zh: "扫描匹配", en: "scan matching" },
    loop: { zh: "回环边", en: "loop closure" },
    estimate: { zh: "修正前的估计", en: "estimate before the correction" },
  },
  frames: [
    {
      label: {
        zh: "机器人每走 0.2 m 或转过 0.2 rad，SLAM Toolbox 就把当前扫描连同此刻的位姿存成一个新节点；和上一个节点之间的边来自里程计。",
        en: "After every 0.2 m of travel or 0.2 rad of turning, SLAM Toolbox stores the current scan with the pose it was taken at as a new node; the edge to the previous node comes from odometry.",
      },
      upto: 6,
      spacing: true,
    },
    {
      label: {
        zh: "每个新扫描都和最近几个节点的扫描做匹配（橙色边），在里程计的小误差刚出现时就纠正它。",
        en: "Each new scan is matched against the scans of the most recent nodes (amber edges), which corrects small odometry errors as they appear.",
      },
      upto: 10,
      match: 9,
    },
    {
      label: {
        zh: `绕完一圈，机器人回到起点附近。弯道上每转过 0.2 rad 就存一个节点，所以那里的节点更密。扫描匹配之后仍有少量误差，并沿路累积：最后一个节点的估计位置离它的真实位置约 ${GAP_LABEL} m。`,
        en: `After one lap the robot is back near the start; on the bends a node is stored every 0.2 rad, so the nodes are closer together there. Scan matching leaves a small error that adds up along the way: the last node's estimate is about ${GAP_LABEL} m from where it really is.`,
      },
      upto: N + 1,
      gap: true,
    },
    {
      label: {
        zh: "回环检测：最后一帧扫描和起点节点的扫描对上了，图里多了一条回环边（绿色虚线）。SLAM Toolbox 随即调整整张图，让新旧视角一致；灰色是调整前的估计。地图按修正后的位姿重新画出。",
        en: "Loop closure: the last scan matches the scan of the start node, which adds a loop-closure edge (green, dashed). SLAM Toolbox then adjusts the whole graph so the old and new views agree; grey is the estimate before. The map is redrawn from the corrected poses.",
      },
      upto: N + 1,
      loop: true,
    },
  ],
  numbers: [
    { note: "gap drawn on the graph (m)", value: gap, expect: GAP_LABEL, tol: 0.005 },
    { note: "the route ends at the start: x (m)", value: end.x, expect: 0, tol: 1e-6 },
    { note: "the route ends at the start: y (m)", value: end.y, expect: 0, tol: 1e-6 },
    { note: "the route ends at the start: heading (rad)", value: end.th, expect: 2 * Math.PI, tol: 1e-9 },
    { note: "corrected last node = its true place (m)", value: Math.hypot(corrected[N].x - truth[N].x, corrected[N].y - truth[N].y), expect: 0, tol: 1e-9 },
    { note: "the last node really is within 0.2 m of node 0 (m)", value: Math.hypot(truth[N].x - truth[0].x, truth[N].y - truth[0].y), expect: 0, tol: 0.2 },
  ],
  facts: [
    { file: SLAM_YAML, pattern: "minimum_travel_distance: 0\\.2\\b", note: "a node after 0.2 m" },
    { file: SLAM_YAML, pattern: "minimum_travel_heading: 0\\.2\\b", note: "... or after 0.2 rad" },
    { file: EN, pattern: "every time the robot has moved 0\\.2 m or turned 0\\.2 rad", note: "lesson: 0.2 m or 0.2 rad (en)" },
    { file: ZH, pattern: "机器人每移动 0\\.2 m 或转过 0\\.2 rad", note: "lesson: 0.2 m or 0.2 rad (zh)" },
    { file: EN, pattern: "matched against the recent ones \\(scan matching\\)", note: "lesson: scan matching against recent scans" },
    { file: EN, pattern: "adjusts the whole graph", note: "lesson: loop closure adjusts the whole graph" },
    { file: ZH, pattern: "调整整张图", note: "lesson: loop closure adjusts the whole graph (zh)" },
  ],
};
