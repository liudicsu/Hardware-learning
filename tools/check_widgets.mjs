// Check that the TypeScript models behind the formula widgets reproduce the Python outputs.
// Run with: node tools/check_widgets.mjs
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const ts = require("typescript");

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");
const models = join(root, "src/lib/models");
const expectedDir = join(root, "tools/sim/expected");

function transpile(source) {
  return ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
}

function dataUrl(source) {
  return "data:text/javascript;base64," + Buffer.from(source).toString("base64");
}

const formatUrl = dataUrl(transpile(readFileSync(join(models, "format.ts"), "utf8")));
const pyfmtUrl = dataUrl(transpile(readFileSync(join(models, "pyfmt.ts"), "utf8")));
const pyRandomUrl = dataUrl(transpile(readFileSync(join(models, "pyRandom.ts"), "utf8")));

async function loadModel(name) {
  let source = transpile(readFileSync(join(models, name + ".ts"), "utf8"));
  source = source.replace(/from\s+["']\.\/format["']/g, "from " + JSON.stringify(formatUrl));
  source = source.replace(/from\s+["']\.\/pyfmt["']/g, "from " + JSON.stringify(pyfmtUrl));
  source = source.replace(/from\s+["']\.\/pyRandom["']/g, "from " + JSON.stringify(pyRandomUrl));
  return import(dataUrl(source));
}

const format = await import(formatUrl);
const fixed = format.fixed;

let checks = 0;
let failed = 0;

function compare(name, label, want, got) {
  checks++;
  const same = want === got;
  if (!same) {
    failed++;
  }
  console.log((same ? "same  " : "DIFF  ") + name + " " + label);
  console.log("  expected " + JSON.stringify(want));
  console.log("  got      " + JSON.stringify(got));
}

const encoder = await loadModel("encoder");
{
  // first 15 lines of the encoder script output (the decoder part), byte for byte
  const want = readFileSync(join(expectedDir, "m2-encoder_sim.txt"), "utf8").split("\n").slice(0, 15);
  const got = encoder.report();
  compare("encoder", "decoder line count", String(want.length), String(got.length));
  want.forEach((line, i) => compare("encoder", `line ${i + 1}`, line, got[i]));
  // the timing-diagram columns follow the same state order and direction convention as the text
  const fwd = encoder.diagramColumns("forward", 8);
  const rev = encoder.diagramColumns("reverse", 8);
  compare("encoder", "forward diagram states", "00 10 11 01 00 10 11 01", fwd.map((c) => c.ab).join(" "));
  compare("encoder", "forward diagram counts", "0 1 2 3 4 5 6 7", fwd.map((c) => c.count).join(" "));
  compare("encoder", "reverse diagram states", "00 01 11 10 00 01 11 10", rev.map((c) => c.ab).join(" "));
  compare("encoder", "reverse diagram counts", "0 -1 -2 -3 -4 -5 -6 -7", rev.map((c) => c.count).join(" "));
}

const pid = await loadModel("pid");
{
  // all 8 lines of the expected file, byte for byte (and nothing extra)
  const want = readFileSync(join(expectedDir, "m3-pid_sim.txt"), "utf8");
  const got = pid.report().join("\n") + "\n";
  compare("pid", "whole file", want, got);
  const wl = want.split("\n"), gl = got.split("\n");
  wl.forEach((line, i) => { if (line) compare("pid", `line ${i + 1}`, line, gl[i]); });
}

const kinematics = await loadModel("kinematics");
{
  // Every line of the expected file is compared byte for byte, except ONE: the
  // "same with lambda = 0.01" line. That run never converges: 200 DLS steps bounce
  // around the unreachable target, so its final numbers depend on the last bit of
  // every sin/cos/atan2 call. Shifting the start pose by 1e-16 rad in Python alone
  // changes it from "37.1 mm, elbow -2.34" to "42.9 mm, elbow 15.81", and V8's libm
  // differs from glibc's by 1 ulp on some inputs, so no port can match it byte for
  // byte. For that line we check the text up to the numbers and that the TS run also
  // fails to settle (all 200 iterations used, still more than 20 mm short).
  // Why only qualitatively: the run is chaotic and V8 and glibc trig differ by 1 ulp,
  // so byte-matching it is impossible, not merely hard. The lesson prints this line
  // only to show that a too-small lambda does not converge, and that is what we test.
  const CHAOTIC = "  same with lambda = 0.01: after ";
  const want = readFileSync(join(expectedDir, "m5-kinematics.txt"), "utf8").split("\n");
  const got = (kinematics.report().join("\n") + "\n").split("\n");
  compare("kinematics", "line count", String(want.length), String(got.length));
  want.forEach((line, i) => {
    if (line.startsWith(CHAOTIC)) {
      const shape = (s) => s.replace(/-?\d+(\.\d+)?/g, "#");
      compare("kinematics", `line ${i + 1} (chaotic lambda = 0.01 run: wording only)`, shape(line), shape(got[i] ?? ""));
      return;
    }
    compare("kinematics", `line ${i + 1}`, line, got[i]);
  });
  const far = kinematics.ik([0.2, 0.2, 0.1], [0, (30 * Math.PI) / 180, (-30 * Math.PI) / 180], 0.01);
  compare("kinematics", "lambda = 0.01 never settles (200 iterations, > 20 mm short)", "true", String(far.it === 199 && far.dist > 0.02));
  // IkWidget guided experiment (kinematics-ik, both languages): every number the list tells the
  // reader to expect, computed with the widget's own calls and formatting.
  {
    const R = Math.PI / 180;
    const tip = (q) => "(" + kinematics.fk(q.map((v) => v * R)).map((v) => fixed(v, 4)).join(", ") + ")";
    const rr = (q) => { const t = kinematics.fk(q.map((v) => v * R)); return fixed(Math.hypot(t[0], t[1]), 4); };
    const det = (q) => format.exp(Math.abs(kinematics.detJ(q.map((v) => v * R))), 2);
    const solve = (t) => {
      const r = kinematics.ik(t, [0, 30 * R, -30 * R]);
      const n = r.dist < 1e-5 ? r.it : r.it + 1; // as IkWidget shows it
      return [`${n} iterations`, "[" + r.q.map((v) => fixed(v / R, 2)).join(", ") + "]", fixed(r.dist * 1000, 2) + " mm"];
    };
    const a = solve([0.1, 0.15, 0.12]), b = solve([0.2, 0.2, 0.1]);
    const rows = [
      ["default tip", "(0.1840, 0.1062, 0.1637)", tip([30, 45, -60])], ["default r", "0.2124", rr([30, 45, -60])], ["default det", "2.88e-03", det([30, 45, -60])],
      ["base 0 tip", "(0.2124, 0.0000, 0.1637)", tip([0, 45, -60])],
      ["elbow -10 det", "6.77e-04", det([0, 0, -10])], ["elbow -5 det", "3.42e-04", det([0, 0, -5])],
      ["straight tip", "(0.2510, 0.0000, 0.1166)", tip([0, 0, 0])], ["straight r", "0.2510", rr([0, 0, 0])], ["straight det", "2.65e-13", det([0, 0, 0])],
      ["solve near", "15 iterations", a[0]], ["solve near q", "[56.31, 49.54, -88.48]", a[1]], ["solve near error", "0.00 mm", a[2]],
      ["solve far", "200 iterations", b[0]], ["solve far error", "32.33 mm", b[2]],
    ];
    const block = (loc) => {
      const text = readFileSync(join(root, "src/content/m5/kinematics-ik", loc + ".mdx"), "utf8").replace(/\u2212/g, "-");
      const marker = loc === "zh" ? "<strong>动手实验。</strong>" : "**Guided experiment.**";
      const i = text.indexOf(marker);
      return i < 0 ? "" : text.slice(i, text.indexOf("\n\n<", i));
    };
    const zhSteps = (s) => s.replace(/(\d+) iterations/, "$1 次迭代");
    for (const [label, want, got] of rows) {
      compare("guided Ik", label, want, got);
      compare("guided Ik", `en states ${want}`, "yes", block("en").includes(want) ? "yes" : "no");
      compare("guided Ik", `zh states ${want}`, "yes", block("zh").includes(zhSteps(want)) ? "yes" : "no");
    }
  }
  // Model angles -> real SO-101 joint angles (kinematics-ik, both languages). Forward kinematics of
  // the URDF (SO-ARM100 @ a758567, Simulation/SO101/so101_new_calib.urdf: shoulder_pan line 435,
  // shoulder_lift 415, elbow_flex 395, wrist_flex 374; limits 439, 419, 399) gives the zero offsets;
  // the two IK branches converted with them must match the lesson's table and the limit verdicts.
  {
    const D = 180 / Math.PI;
    const mul = (A, B) => A.map((r, i) => B[0].map((_, j) => r.reduce((s, _, k) => s + A[i][k] * B[k][j], 0)));
    const rpy = (r, p, y) => {
      const [cr, sr, cp, sp, cy, sy] = [Math.cos(r), Math.sin(r), Math.cos(p), Math.sin(p), Math.cos(y), Math.sin(y)];
      return mul(mul([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]], [[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]]), [[1, 0, 0], [0, cr, -sr], [0, sr, cr]]);
    };
    const tf = (xyz, r, q) => {
      const R = mul(rpy(...r), [[Math.cos(q), -Math.sin(q), 0], [Math.sin(q), Math.cos(q), 0], [0, 0, 1]]);
      return [[...R[0], xyz[0]], [...R[1], xyz[1]], [...R[2], xyz[2]], [0, 0, 0, 1]];
    };
    const J = [
      [[0.0388353, -8.97657e-9, 0.0624], [3.14159, 4.18253e-17, -3.14159]], // shoulder_pan
      [[-0.0303992, -0.0182778, -0.0542], [-1.5708, -1.5708, 0]], // shoulder_lift
      [[-0.11257, -0.028, 1.73763e-16], [-3.63608e-16, 8.74301e-16, 1.5708]], // elbow_flex
      [[-0.1349, 0.0052, 3.62355e-17], [4.02456e-15, 8.67362e-16, -1.5708]], // wrist_flex
    ];
    const lim = { pan: 1.91986 * D, lift: 1.74533 * D, elbow: 1.69 * D };
    const pts = (q) => { let M = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]; return J.map(([x, r], i) => (M = mul(M, tf(x, r, (q[i] ?? 0) / D)), [M[0][3], M[1][3], M[2][3]])); };
    const elev = (a, b) => Math.atan2(b[2] - a[2], Math.hypot(b[0] - a[0], b[1] - a[1])) * D;
    const p0 = pts([0, 0, 0]);
    const liftOff = elev(p0[1], p0[2]), elbowOff = elev(p0[2], p0[3]) - liftOff;
    const p1 = pts([0, 10, 0]), p2 = pts([0, 0, 10]), p3 = pts([10, 0, 0]);
    const az = (p) => Math.atan2(p[2][1] - p[1][1], p[2][0] - p[1][0]) * D;
    compare("SO-101 map", "lift zero offset", "76.03", fixed(liftOff, 2));
    compare("SO-101 map", "elbow zero offset", "-73.82", fixed(elbowOff, 2));
    compare("SO-101 map", "signs (lift, elbow, pan opposite to q1, q2, q0)", "-10.00 -10.00 -10.00",
      [elev(p1[1], p1[2]) - liftOff, elev(p2[2], p2[3]) - elev(p2[1], p2[2]) - elbowOff, az(p3) - az(p0)].map((v) => fixed(v, 2)).join(" "));
    const R = Math.PI / 180;
    const first = kinematics.ik([0.1, 0.15, 0.12], [0, 30 * R, -30 * R]).q.map((v) => v / R);
    const second = kinematics.ik([0.1, 0.15, 0.12], [0, 90 * R, 60 * R]).q.map((v) => v / R);
    const conv = (q) => [-q[0], liftOff - q[1], elbowOff - q[2]];
    const within = (c) => [Math.abs(c[0]) <= lim.pan, Math.abs(c[1]) <= lim.lift, Math.abs(c[2]) <= lim.elbow].map(String).join(" ");
    const line = (q) => { const c = conv(q); return `pan ${fixed(c[0], 2)}, lift ${fixed(c[1], 2)}, elbow ${fixed(c[2], 2)}`; };
    compare("SO-101 map", "first branch", "pan -56.31, lift 26.49, elbow 14.66", line(first));
    compare("SO-101 map", "first branch within limits", "true true true", within(conv(first)));
    compare("SO-101 map", "second branch", "pan 123.69, lift -54.43, elbow -162.31", line(second));
    compare("SO-101 map", "second branch: pan and elbow outside", "false true false", within(conv(second)));
    compare("SO-101 map", "limits deg", "110.00 100.00 96.83", [lim.pan, lim.lift, lim.elbow].map((v) => fixed(v, 2)).join(" "));
    for (const loc of ["en", "zh"]) {
      const text = readFileSync(join(root, "src/content/m5/kinematics-ik", loc + ".mdx"), "utf8").replace(/\u2212/g, "-");
      for (const want of ["76.03 deg - q1", "-73.82 deg - q2", "±110.00 deg", "±100.00 deg", "±96.83 deg",
        line(first).replace(/, /g, loc === "zh" ? "，" : ", "), line(second).replace(/, /g, loc === "zh" ? "，" : ", ")])
        compare("SO-101 map", `${loc} states ${want}`, "yes", text.includes(want) ? "yes" : "no");
    }
  }
}

const camera = await loadModel("camera");
{
  const lines = readFileSync(join(expectedDir, "m5-cam_pixel.txt"), "utf8")
    .split("\n")
    .filter((line) => line.startsWith("  ("));

  // Data-line layout from pixel_to_table.py:
  //   "  (u:4.0f, v:4.0f)   (3D point)   (exact mm)   error   ignoring distortion"
  // The pixel column is characters [0, 14), the 3D-point column [17, 41), and the
  // exact (mm) column [44, 68). Keep the pixel and exact columns, separated by 3 spaces.
  const pixelCol = (line) => line.slice(0, 14);
  const exactCol = (line) => line.slice(44, 68);

  const gotPixels = camera.pixelReport();
  const projectExpected = [
    ["(320.0, 240.0)", "(320.0, 240.0)"],
    ["(420.0, 300.0)", "(420.6, 300.4)"],
    ["(600.0, 440.0)", "(616.3, 451.7)"],
  ];

  lines.forEach((line, i) => {
    const want = pixelCol(line) + "   " + exactCol(line);
    compare("camera", "pixel " + (i + 1), want, gotPixels[i]);

    const mm = exactCol(line).match(/-?\d+\.\d+/g).map(Number);
    const point = [mm[0] / 1000, mm[1] / 1000, mm[2] / 1000];
    const show = ([u, v]) => "(" + fixed(u, 1) + ", " + fixed(v, 1) + ")";
    compare(
      "camera",
      "project pixel " + (i + 1),
      projectExpected[i][0],
      show(camera.project(point)),
    );
    compare(
      "camera",
      "project ignoreDistortion pixel " + (i + 1),
      projectExpected[i][1],
      show(camera.project(point, camera.TRUE_CAMERA, true)),
    );
  });
}

const lineFollow = await loadModel("lineFollow");
{
  // line_sim.py: whole file and every line, byte for byte
  const want = readFileSync(join(expectedDir, "m2-line_sim.txt"), "utf8");
  const got = lineFollow.report().join("\n") + "\n";
  compare("lineFollow", "whole file", want, got);
  const wl = want.split("\n"), gl = got.split("\n");
  wl.forEach((line, i) => { if (line) compare("lineFollow", `line ${i + 1}`, line, gl[i]); });
}

const complementary = await loadModel("complementary");
{
  // NOT byte for byte: filter_sim.py adds seeded Gaussian noise (Python's Mersenne Twister),
  // which the widget does not reproduce. The widget uses the analytic steady-state offset
  // alpha / (1 - alpha) * bias * dt; the reviewer accepted it on the condition that it agrees
  // with the script's offset_flat column to 1 decimal place, and the lesson says so.
  const rows = readFileSync(join(root, "tools/sim/expected/m2-filter_sim.txt"), "utf8")
    .split("\n")
    .filter((line) => /^0\.\d+ +-?\d/.test(line));
  const got = complementary.offsetTable();
  compare("complementary", "alpha rows", "3", String(rows.length));
  rows.forEach((line, i) => {
    const [alpha, offset] = line.trim().split(/\s+/);
    compare("complementary", `alpha ${alpha} offset to 1 decimal place`, fixed(Number(offset), 1), got[i]);
  });
}

const snapFit = await loadModel("snapFit");
{
  // fdm-snap_fit.txt: whole file and every line, byte for byte
  const want = readFileSync(join(root, "examples/month-3/expected/fdm-snap_fit.txt"), "utf8");
  const got = snapFit.report().join("\n") + "\n";
  compare("snapFit", "whole file", want, got);
  const wl = want.split("\n"), gl = got.split("\n");
  wl.forEach((line, i) => { if (line) compare("snapFit", `line ${i + 1}`, line, gl[i]); });
}

const gears = await loadModel("gears");
{
  // tr-gear_calc.txt: whole file and every line, byte for byte
  const want = readFileSync(join(root, "examples/month-3/expected/tr-gear_calc.txt"), "utf8");
  const got = gears.report().join("\n") + "\n";
  compare("gears", "whole file", want, got);
  const wl = want.split("\n"), gl = got.split("\n");
  wl.forEach((line, i) => { if (line) compare("gears", `line ${i + 1}`, line, gl[i]); });
}

const stsPacket = await loadModel("stsPacket");
{
  // arm-sts_packet.txt: whole file and every line, byte for byte
  const want = readFileSync(join(root, "examples/month-3/expected/arm-sts_packet.txt"), "utf8");
  const got = stsPacket.report().join("\n") + "\n";
  compare("stsPacket", "whole file", want, got);
  const wl = want.split("\n"), gl = got.split("\n");
  wl.forEach((line, i) => { if (line) compare("stsPacket", `line ${i + 1}`, line, gl[i]); });
}

const gripForce = await loadModel("gripForce");
{
  // grip-force.txt: whole file and every line, byte for byte
  const want = readFileSync(join(root, "examples/month-3/expected/grip-force.txt"), "utf8");
  const got = gripForce.report().join("\n") + "\n";
  compare("gripForce", "whole file", want, got);
  const wl = want.split("\n"), gl = got.split("\n");
  wl.forEach((line, i) => { if (line) compare("gripForce", `line ${i + 1}`, line, gl[i]); });
}

const panTilt = await loadModel("panTilt");
{
  // tf2_echo base_link camera_link at pan 30 deg (examples/month-4/check.sh). Line 1 is
  // "At time <stamp>", masked like check.sh does; every other line byte for byte.
  const want = readFileSync(join(root, "examples/month-4/expected/ros-tf_pan30.txt"), "utf8").split("\n");
  const got = panTilt.report();
  compare("panTilt", "line 1 (time stamp masked)", want[0].replace(/At time [0-9.]+/, "At time #"), "At time #");
  compare("panTilt", "lines 2..end", want.slice(1).join("\n"), got.join("\n") + "\n");
  want.slice(1).forEach((line, i) => { if (line) compare("panTilt", `line ${i + 2}`, line, got[i]); });
}

const wilson = await loadModel("wilson");
{
  // eval_report.py section 1 only (the Wilson intervals), byte for byte; the rest of that
  // script needs the behaviour-cloning rollouts and is not part of the widget.
  const want = readFileSync(join(root, "examples/month-6/expected/eval_report.txt"), "utf8").split("\n").slice(0, 7);
  const got = wilson.report();
  compare("wilson", "section 1 (7 lines)", want.join("\n"), got.join("\n"));
  want.forEach((line, i) => compare("wilson", `line ${i + 1}`, line, got[i]));
}

const actionTokens = await loadModel("actionTokens");
{
  // action_tokens.py lines 1-8 (dataset percentiles and per-step bins), byte for byte.
  // The data come from Python's random.Random(6) and (99), replayed by pyRandom.ts (MT19937).
  // The DCT half of the script (lines 9-) is not part of the widget and is not ported.
  const want = readFileSync(join(root, "examples/month-6/expected/action_tokens.txt"), "utf8").split("\n").slice(0, 8);
  const got = actionTokens.report();
  compare("actionTokens", "lines 1-8", want.join("\n"), got.join("\n"));
  want.forEach((line, i) => { if (line) compare("actionTokens", `line ${i + 1}`, line, got[i]); });
}

const jointFreq = await loadModel("jointFreq");
{
  // m5-joint_freq.txt: whole file and every line, byte for byte
  const want = readFileSync(join(root, "tools/sim/expected/m5-joint_freq.txt"), "utf8");
  const got = jointFreq.report().join("\n") + "\n";
  compare("jointFreq", "whole file", want, got);
  const wl = want.split("\n"), gl = got.split("\n");
  wl.forEach((line, i) => { if (line) compare("jointFreq", `line ${i + 1}`, line, gl[i]); });
}

const lqrModel = await loadModel("lqr");
{
  // lqr_sim.py part 1 (cart-pole, 17 lines), byte for byte. Part 2 (MPC on the arm
  // joint) is not part of the widget and is not ported.
  const want = readFileSync(join(expectedDir, "m5-lqr_sim.txt"), "utf8").split("\n").slice(0, 17);
  const got = lqrModel.report();
  compare("lqr", "part 1 (17 lines)", want.join("\n"), got.join("\n"));
  want.forEach((line, i) => compare("lqr", `line ${i + 1}`, line, got[i]));
}

const diffDrive = await loadModel("diffDrive");
{
  // ctl-diff_drive.txt (examples/month-4/ros2-control/diff_drive.py): whole file and every
  // line, byte for byte. The script's first line depends on what controllers.yaml says, so
  // read it here with the same regular expressions and hand the numbers to the port.
  const yaml = readFileSync(join(root, "examples/month-4/ros2-control/m4_control/config/controllers.yaml"), "utf8");
  const sep = yaml.match(/^\s*wheel_separation:\s*([0-9.]+)/m), rad = yaml.match(/^\s*wheel_radius:\s*([0-9.]+)/m);
  const want = readFileSync(join(root, "examples/month-4/expected/ctl-diff_drive.txt"), "utf8");
  const got = diffDrive.report([Number(sep[1]), Number(rad[1])]).join("\n") + "\n";
  compare("diffDrive", "whole file", want, got);
  const wl = want.split("\n"), gl = got.split("\n");
  wl.forEach((line, i) => { if (line) compare("diffDrive", `line ${i + 1}`, line, gl[i]); });
  // the widget's defaults are the lesson's worked example (spin left, 1.0 rad/s); the quiz is 0.3 m/s straight
  compare("diffDrive", "worked example: spin left 1.0 rad/s", "-2.8 2.8", diffDrive.wheels(0, 1).map((x) => fixed(x, 1)).join(" "));
  compare("diffDrive", "quiz: 0.3 m/s straight", "6.0 6.0", diffDrive.wheels(0.3, 0).map((x) => fixed(x, 1)).join(" "));
}

console.log(`widgets: ${checks} checks, ${failed} failed`);
process.exitCode = failed === 0 ? 0 : 1;
