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
