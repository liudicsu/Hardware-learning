import type { PoseGraphPose, PoseGraphScan, PoseGraphSpec } from "../types";

/*
 * m4/slam-nav: the pose graph in four frames (D091). Illustrative: the route (a 2.4 m x 1.6 m rectangle
 * driven like tour.py: straight at 0.25 m/s, turns on the spot at 0.6 rad/s), the odometry error (every turn
 * 3 % short) and the linear spreading of the correction. Not assumed: which scans become nodes. That follows
 * SLAM Toolbox 2.8.5 (the version in examples/month-4/pixi.lock) with this lesson's slam.yaml:
 *  1. SlamToolbox::shouldProcessScan (src/slam_toolbox_common.cpp:756-817, tag 2.8.5 = commit ec8f763): with
 *     check_min_dist_and_heading_precisely false (default, :413), a scan is dropped when the base pose's
 *     squared straight-line distance from the last scan that passed is < 0.8 * minimum_travel_distance^2
 *     (:807), i.e. closer than sqrt(0.8) * 0.2 = 0.179 m; heading is not looked at here. It is also dropped
 *     within minimum_time_interval (default 0.5 s, :400-411). The first callback passes via the first_measurement_
 *     branch; callbacks 2-4 are dropped (第 1 次回调走 first_measurement_ 分支直接通过，第 2–4 次被丢弃): scan_ctr++ (:769) comes
 *     before the scan_ctr < 5 test (:795), and callback 1 has already returned true through the
 *     first_measurement_ branch (:771-777), which comes before the pause, throttle, time, scan_ctr and distance
 *     checks and sets last_pose to the first pose. So node 0 is the first scan, at the start (Karto accepts a
 *     sensor's first scan: HasMovedEnough returns true without a last scan, Mapper.cpp:3150-3152).
 *  2. Karto Mapper::HasMovedEnough (lib/karto_sdk/src/Mapper.cpp:3147-3178) then keeps it as a node if the
 *     lidar pose has turned >= minimum_travel_heading or moved >= minimum_travel_distance since the last node
 *     (its time escape, MinimumTimeInterval, defaults to 3600 s, :2108-2118, and slam_toolbox never sets it).
 * check_diagrams re-runs this rule on the scans with the values read from slam.yaml, the URDF, the Gazebo
 * sensor and tour.py, and requires the same nodes.
 */

const SLAM_YAML = "examples/month-4/slam-nav/m4_nav/config/slam.yaml";
const EN = "src/content/m4/slam-nav/en.mdx";
const ZH = "src/content/m4/slam-nav/zh.mdx";

const DISTANCE = 0.2; // m, minimum_travel_distance (slam.yaml)
const HEADING = 0.2; // rad, minimum_travel_heading (slam.yaml)
const FACTOR = 0.8; // shouldProcessScan: dist^2 < 0.8 * min_dist^2 is dropped
const MIN_INTERVAL = 0.5; // s, minimum_time_interval default
const LIDAR_X = 0.12; // m, lidar_link ahead of base_footprint (URDF)
const RATE = 10; // Hz, Gazebo lidar update_rate
const SPEED = 0.25; // m/s, tour.py drive speed
const TURN_RATE = 0.6; // rad/s, tour.py turn rate limit
const TURN_ERROR = -0.03; // odometry turns 3 % short (assumed)
// [straight m] or [0, turn rad]: the rectangle, turning on the spot at each corner, back to heading 0 at the end
const ROUTE: [number, number][] = [
  [2.4, 0], [0, Math.PI / 2], [1.6, 0], [0, Math.PI / 2], [2.4, 0], [0, Math.PI / 2], [1.6, 0], [0, Math.PI / 2],
];
const duration = ([len, turn]: [number, number]) => (len ? len / SPEED : Math.abs(turn) / TURN_RATE);
const TOTAL = ROUTE.reduce((a, ph) => a + duration(ph), 0);

/** Pose at time t; `turnScale` 1 for the truth, 1 + TURN_ERROR for odometry. */
function poseAt(t: number, turnScale: number): PoseGraphPose {
  let p = { x: 0, y: 0, th: 0 };
  let t0 = 0;
  for (const ph of ROUTE) {
    const d = duration(ph);
    const f = Math.min(Math.max(t - t0, 0), d);
    const next = ph[0]
      ? { x: p.x + SPEED * f * Math.cos(p.th), y: p.y + SPEED * f * Math.sin(p.th), th: p.th }
      : { ...p, th: p.th + Math.sign(ph[1]) * TURN_RATE * f * turnScale };
    if (t <= t0 + d) return next;
    p = next;
    t0 += d;
  }
  return p;
}

const scans: PoseGraphScan[] = [];
for (let k = 0; k / RATE <= TOTAL + 1e-9; k++) {
  const t = k / RATE;
  scans.push({ t, odom: poseAt(t, 1 + TURN_ERROR), truth: poseAt(t, 1) });
}

const normalize = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));
const lidar = (p: PoseGraphPose) => ({ x: p.x + LIDAR_X * Math.cos(p.th), y: p.y + LIDAR_X * Math.sin(p.th) });
const d2 = (a: { x: number; y: number }, b: { x: number; y: number }) => (a.x - b.x) ** 2 + (a.y - b.y) ** 2;

function selectNodes(): number[] {
  const nodes = [0]; // the first scan passes (first_measurement_, :771-777) and Karto keeps it (:3150-3152)
  let passed = scans[0];
  for (let k = 1; k < scans.length; k++) {
    const s = scans[k];
    if (k + 1 < 5) continue; // scan_ctr = k + 1 after the increment; < 5 drops callbacks 2-4 (k = 1..3)
    if (s.t - passed.t < MIN_INTERVAL) continue;
    if (d2(s.odom, passed.odom) < FACTOR * DISTANCE * DISTANCE) continue; // straight-line distance only
    passed = s;
    const last = scans[nodes[nodes.length - 1]].odom;
    const turned = Math.abs(normalize(s.odom.th - last.th)) >= HEADING;
    const moved = d2(lidar(s.odom), lidar(last)) >= DISTANCE * DISTANCE - 1e-6;
    if (turned || moved) nodes.push(k);
  }
  return nodes;
}

const nodes = selectNodes();
const estimate = nodes.map((k) => scans[k].odom);
const truth = nodes.map((k) => scans[k].truth);
const end = poseAt(TOTAL, 1);
const N = nodes.length - 1;
const last = estimate[N];
// Loop closure (illustrative): the last scan matches node 0's scan, which fixes the last node at its true
// place; the correction is spread along the chain in proportion to the node index.
const fix = { x: truth[N].x - last.x, y: truth[N].y - last.y, th: truth[N].th - last.th };
const corrected = estimate.map((p, i) => ({ x: p.x + (fix.x * i) / N, y: p.y + (fix.y * i) / N, th: p.th + (fix.th * i) / N }));
const gap = Math.hypot(fix.x, fix.y);
const GAP_LABEL = 0.28; // m, drawn on the graph
// nodes stored while the robot was turning on the spot (expected: none)
const turnNodes = nodes.filter((k) => k > 0 && scans[k].odom.x === scans[k - 1].odom.x && scans[k].odom.y === scans[k - 1].odom.y).length;

export const slamPoseGraph: PoseGraphSpec = {
  kind: "poseGraph",
  id: "slam-pose-graph",
  title: { zh: "SLAM Toolbox 的位姿图，分四步", en: "SLAM Toolbox's pose graph in four steps" },
  caption: {
    zh: "示意图：路线（照 tour.py 的方式，直线 0.25 m/s、原地转弯）、每次转弯少算 3 % 的里程计误差、只画 3 条的扫描匹配边，以及修正量的分摊方式都是假设的。实际的扫描匹配用的是滚动扫描缓冲区（scan_buffer_size 默认 10 帧，scan_buffer_maximum_scan_distance 默认 10 m）。哪些扫描成为节点则按 SLAM Toolbox 2.8.5 的规则和 slam.yaml 计算，检查脚本逐帧复核。SLAM Toolbox 实际用图优化（Ceres 求解器，solver_plugins::CeresSolver）求出修正，而不是按节点序号线性分摊。",
    en: "Illustrative: the route (driven like tour.py, straight at 0.25 m/s, turning on the spot), the odometry error (every turn 3 % short), the 3 scan-matching edges drawn, and the way the correction is spread are assumed. Real scan matching uses the rolling scan buffer (scan_buffer_size default 10 scans, scan_buffer_maximum_scan_distance default 10 m). Which scans become nodes follows SLAM Toolbox 2.8.5's rule with slam.yaml and is checked scan by scan. SLAM Toolbox computes the correction by graph optimisation (Ceres solver, solver_plugins::CeresSolver), not by spreading it linearly over the nodes.",
  },
  sources: [SLAM_YAML, EN, ZH],
  scans,
  nodes,
  estimate,
  corrected,
  truth,
  model: { distance: DISTANCE, heading: HEADING, factor: FACTOR, minInterval: MIN_INTERVAL, lidarX: LIDAR_X, rate: RATE, speed: SPEED, turnRate: TURN_RATE },
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
        zh: "激光雷达每秒送来 10 帧扫描。SLAM Toolbox 先丢掉离上一帧通过的扫描直线距离不到 √0.8 × 0.2 ≈ 0.179 m 的扫描（这一步不看朝向）；通过的扫描离上一个节点至少 0.2 m 或转过至少 0.2 rad，才存成新节点。以 0.25 m/s 行驶时每 0.025 m 来一帧，第一帧超过 0.179 m 的正好在 0.200 m 处，所以直线上每 0.2 m 一个节点。",
        en: "The lidar delivers 10 scans a second. SLAM Toolbox first drops every scan less than √0.8 × 0.2 ≈ 0.179 m in a straight line from the last scan that passed (heading is not looked at here); a scan that passes becomes a node if it is at least 0.2 m or 0.2 rad from the last node. At 0.25 m/s a scan arrives every 0.025 m and the first one past 0.179 m is at 0.200 m, so on a straight there is a node every 0.2 m.",
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
        zh: `绕完一圈，机器人回到起点。在四个角上原地转弯时底盘没有移动，这些扫描在第一步距离筛选就被丢掉，所以转弯本身不产生节点。扫描匹配之后仍有少量误差沿路累积：最后一个节点的估计位置离它的真实位置约 ${GAP_LABEL} m。`,
        en: `After one lap the robot is back at the start. While it turns on the spot at the corners the base does not move, so those scans fail the first distance filter and the turns add no nodes. Scan matching leaves a small error that adds up along the way: the last node's estimate is about ${GAP_LABEL} m from where it really is.`,
      },
      upto: N + 1,
      gap: true,
    },
    {
      label: {
        zh: "回环检测：SLAM Toolbox 在新节点 loop_search_maximum_distance（默认 3 m）以内、且和它没有直接连在一起的旧节点里找候选，至少要有 loop_match_minimum_chain_size（默认 10）个连续节点才去匹配。最后一帧扫描和起点附近的扫描对上了，图里多了一条回环边（绿色虚线），整张图随之调整，让新旧视角一致；灰色是调整前的估计。地图按修正后的位姿重新画出。",
        en: "Loop closure: SLAM Toolbox looks for candidates among older nodes within loop_search_maximum_distance (default 3 m) of the new node that are not already linked to it, and only tries a match when at least loop_match_minimum_chain_size (default 10) consecutive nodes qualify. The last scan matches the scans near the start, which adds a loop-closure edge (green, dashed), and the whole graph is adjusted so the old and new views agree; grey is the estimate before. The map is redrawn from the corrected poses.",
      },
      upto: N + 1,
      loop: true,
    },
  ],
  numbers: [
    { note: "gap drawn on the graph (m)", value: gap, expect: GAP_LABEL, tol: 0.005 },
    { note: "the route ends at the start: x (m)", value: end.x, expect: 0, tol: 1e-9 },
    { note: "the route ends at the start: y (m)", value: end.y, expect: 0, tol: 1e-9 },
    { note: "the route ends at the start: heading (rad)", value: end.th, expect: 2 * Math.PI, tol: 1e-9 },
    { note: "corrected last node = its true place (m)", value: Math.hypot(corrected[N].x - truth[N].x, corrected[N].y - truth[N].y), expect: 0, tol: 1e-9 },
    { note: "the last node really is within 0.2 m of node 0 (m)", value: Math.hypot(truth[N].x - truth[0].x, truth[N].y - truth[0].y), expect: 0, tol: 0.2 },
    { note: "drop threshold sqrt(0.8) x 0.2 (lesson: 0.179 m)", value: Math.sqrt(FACTOR) * DISTANCE, expect: 0.179, tol: 0.0005 },
    { note: "distance between scans at 0.25 m/s and 10 Hz (lesson: 0.025 m)", value: SPEED / RATE, expect: 0.025, tol: 1e-12 },
    { note: "nodes stored while turning on the spot", value: turnNodes, expect: 0, tol: 0 },
  ],
  facts: [
    { file: SLAM_YAML, pattern: "minimum_travel_distance: 0\\.2\\b", note: "minimum_travel_distance 0.2" },
    { file: SLAM_YAML, pattern: "minimum_travel_heading: 0\\.2\\b", note: "minimum_travel_heading 0.2" },
    { file: SLAM_YAML, pattern: "sqrt\\(0\\.8\\) x 0\\.2 = 0\\.18 m", note: "slam.yaml comment: the sqrt(0.8) filter" },
    { file: EN, pattern: "about 0\\.18 m in a straight line", note: "lesson: about 0.18 m in a straight line (en)" },
    { file: ZH, pattern: "直线距离约 0\\.18 m", note: "lesson: about 0.18 m in a straight line (zh)" },
    { file: EN, pattern: "check_min_dist_and_heading_precisely: true", note: "lesson: when heading counts on its own (en)" },
    { file: ZH, pattern: "check_min_dist_and_heading_precisely: true", note: "lesson: when heading counts on its own (zh)" },
    { file: EN, pattern: "matched against the recent ones \\(scan matching\\)", note: "lesson: scan matching against recent scans" },
    { file: EN, pattern: "adjusts the whole graph", note: "lesson: loop closure adjusts the whole graph" },
    { file: ZH, pattern: "调整整张图", note: "lesson: loop closure adjusts the whole graph (zh)" },
  ],
};
