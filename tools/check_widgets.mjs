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


// ---------------------------------------------------------------------------------------------
// Guided experiments: every number the lesson's "Guided experiment" list tells the reader to
// expect is recomputed here from the same model call and formatting the widget uses, and must
// appear in that list in both languages (the list starts at **Guided experiment.** /
// <strong>动手实验。</strong> and ends at the first paragraph that is not a numbered step).
function guidedBlock(lesson, locale) {
  const text = readFileSync(join(root, "src/content", lesson, locale + ".mdx"), "utf8");
  const marker = locale === "zh" ? "<strong>动手实验。</strong>" : "**Guided experiment.**";
  const start = text.indexOf(marker);
  if (start < 0) return null;
  const lines = text.slice(start).split("\n");
  const out = [lines[0]];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim() === "") { out.push(line); continue; }
    if (/^\d+\.\s/.test(line) || /^\s{2,}\S/.test(line)) { out.push(line); continue; }
    break;
  }
  return out.join("\n").replace(/\u2212/g, "-");
}
function guided(widget, lesson, rows) {
  const blocks = { en: guidedBlock(lesson, "en"), zh: guidedBlock(lesson, "zh") };
  for (const loc of ["en", "zh"]) compare("guided " + widget, `${loc} list present`, "yes", blocks[loc] ? "yes" : "no");
  for (const [label, want, got] of rows) {
    compare("guided " + widget, label, want, got);
    for (const loc of ["en", "zh"]) {
      if (!blocks[loc]) continue;
      compare("guided " + widget, `${loc} states ${want}`, "yes", blocks[loc].includes(want.replace(/\u2212/g, "-")) ? "yes" : "no");
    }
  }
}
{
  const c = complementary;
  guided("Complementary", "m2/sensors-fusion", [
    ["α 0.98 τ", "0.49 s", fixed(c.timeConstant(0.98), 2) + " s"],
    ["α 0.98 offset", "0.7°", fixed(c.biasOffset(0.98), 1) + "°"],
    ["α 0.90 τ", "0.09 s", fixed(c.timeConstant(0.9), 2) + " s"],
    ["α 0.90 offset", "0.1°", fixed(c.biasOffset(0.9), 1) + "°"],
    ["α 0.995 τ", "1.99 s", fixed(c.timeConstant(0.995), 2) + " s"],
    ["α 0.995 offset", "3.0°", fixed(c.biasOffset(0.995), 1) + "°"],
  ]);
}
{
  const d = (kp, kd) => lineFollow.describe(lineFollow.run(kp, kd, 4.0));
  const a = d(0.0003, 0.0002), b = d(0.0003, 0), e = d(0.0003, 0.0001), f = d(0.0003, 0.0004);
  const st = (x) => (x.settled === null ? "never" : fixed(x.settled, 2) + " s");
  guided("LineFollow", "m2/first-robots", [
    ["default overshoot", "0.0 mm", fixed(a.overshoot, 1) + " mm"],
    ["default settle", "1.30 s", st(a)],
    ["kd 0 overshoot", "62.3 mm", fixed(b.overshoot, 1) + " mm"],
    ["kd 0 crossings", "3", String(b.crossings)],
    ["kd 0.0001 overshoot", "4.8 mm", fixed(e.overshoot, 1) + " mm"],
    ["kd 0.0001 settle", "1.47 s", st(e)],
    ["kd 0.0004 settle", "2.97 s", st(f)],
  ]);
  compare("guided LineFollow", "kd 0 never settles", "never", st(b));
}
{
  const sn = (L, t, y, mat, lead) => snapFit.snap(L, t, y, 6.0, mat, lead);
  const pct = (x) => fixed(x.eps * 100, 2) + " %", n = (x) => fixed(x.W, 1) + " N";
  const a = sn(10, 1.2, 0.8, "PLA", 30), b = sn(5, 1.5, 1.0, "PLA", 30), c = sn(10, 1.5, 1.0, "PLA", 30);
  const d = sn(10, 1.2, 0.8, "PLA", 60), e = sn(10, 1.2, 0.8, "PETG", 30);
  guided("SnapFit", "m3/fdm-printing", [
    ["default strain", "1.44 %", pct(a)], ["default force", "7.7 N", n(a)],
    ["L5 strain", "9.00 %", pct(b)], ["L5 force", "150.4 N", n(b)],
    ["L10 t1.5 strain", "2.25 %", pct(c)], ["L10 t1.5 force", "18.8 N", n(c)],
    ["lead 60 force", "30.7 N", n(d)], ["PETG force", "4.4 N", n(e)],
  ]);
}
{
  const g = (m, mu, a, sf) => fixed(gripForce.squeeze(m / 1000, mu, sf, a), 1) + " N";
  const tilt = (mu) => fixed((Math.atan(mu) * 180) / Math.PI, 0) + "°";
  guided("GripForce", "m3/gripper-fingers", [
    ["default force", "2.6 N", g(60, 0.3, 3, 2)], ["default tilt", "17°", tilt(0.3)],
    ["μ 0.6 force", "1.3 N", g(60, 0.6, 3, 2)], ["μ 0.6 tilt", "31°", tilt(0.6)],
    ["a 0 force", "2.0 N", g(60, 0.3, 0, 2)],
    ["350 g force", "14.9 N", g(350, 0.3, 3, 2)], ["350 g μ 0.8 force", "5.6 N", g(350, 0.8, 3, 2)],
  ]);
}
{
  const p = (s, r, n) => gears.planetary(s, r, n);
  const tip = (r, b) => fixed(gears.tipError(r, b), 1) + " mm";
  guided("Gear", "m3/transmissions", [
    ["default ratio", "5.000", fixed(p(12, 48, 3).ratio, 3)],
    ["default planet", "18", String(p(12, 48, 3).planet)],
    ["ring 46 spacing", "19.33", fixed((12 + 46) / 3, 2)],
    ["ring 47 planet", "17.5", fixed((47 - 12) / 2, 1)],
    ["5 planets spacing", "17.63", fixed((12 + 18) * Math.sin(Math.PI / 5), 2)],
    ["tip 0.30 m 2°", "10.5 mm", tip(0.3, 2)], ["tip 0.30 m 0.5°", "2.6 mm", tip(0.3, 0.5)], ["tip 0.60 m 2°", "20.9 mm", tip(0.6, 2)],
  ]);
  compare("guided Gear", "4 planets assemble", "true", String(p(12, 48, 4).ok));
  compare("guided Gear", "5 planets rejected", "false", String(p(12, 48, 5).ok));
}
{
  const s = (kp, ki, kd, aw) => pid.simulate(kp, ki, kd, aw);
  const a = s(0.05, 0.1, 0.002, true), b = s(0.05, 0.4, 0.002, true), c = s(0.05, 0.4, 0.002, false);
  const d = s(0.05, 0, 0.002, true), e = s(0.05, 0.1, 0, true);
  const deg = (x) => fixed(x, 1) + "°", sec = (x) => (x === null ? "never" : fixed(x, 2) + " s");
  guided("Pid", "m3/pid-control", [
    ["default final", "60.0°", deg(a.finalDeg)], ["default overshoot", "0.1°", deg(a.overshoot)], ["default settle", "0.24 s", sec(a.settle)],
    ["Ki 0.4 overshoot", "8.9°", deg(b.overshoot)], ["Ki 0.4 settle", "0.56 s", sec(b.settle)],
    ["no anti-windup overshoot", "39.0°", deg(c.overshoot)], ["no anti-windup settle", "0.64 s", sec(c.settle)],
    ["Ki 0 final", "55.5°", deg(d.finalDeg)],
    ["Kd 0 overshoot", "11.5°", deg(e.overshoot)], ["Kd 0 settle", "0.92 s", sec(e.settle)],
    ["Ki 0 steady error = gravity / Kp", "4.5°", deg((0.4 * Math.cos((d.finalDeg * Math.PI) / 180)) / 0.05)],
  ]);
  compare("guided Pid", "Ki 0 never settles", "never", sec(d.settle));
}
{
  const m = stsPacket;
  const goal = (id, g) => m.hexs(m.packet(id, m.WRITE, [m.GOAL_POSITION, g & 0xff, g >> 8]));
  const [sid, err, params] = m.parseStatus(m.parseHex("FF FF 06 04 00 2C 0C BD"));
  const steps = params[0] | (params[1] << 8);
  let bad = "";
  try { m.parseStatus(m.parseHex("FF FF 06 04 00 2C 0D BD")); } catch (e) { bad = e.message; }
  guided("StsPacket", "m3/so101-arm", [
    ["goal 2048 id 1", "FF FF 01 05 03 2A 00 08 C4", goal(1, 2048)],
    ["goal 1024 id 1", "FF FF 01 05 03 2A 00 04 C8", goal(1, 1024)],
    ["goal 2048 id 2", "FF FF 02 05 03 2A 00 08 C3", goal(2, 2048)],
    ["reply position", "3116", String(steps)],
    ["reply degrees", "273.9°", fixed(m.stepsToDeg(steps), 1) + "°"],
  ]);
  compare("guided StsPacket", "reply id/error", "6 0", `${sid} ${err}`);
  compare("guided StsPacket", "flipped bit rejected", "true", String(bad.startsWith("bad checksum")));
}
{
  const w = (v, om, b, r) => diffDrive.wheels(v, om, b, r).map((x) => fixed(x, 1));
  guided("DiffDrive", "m4/ros2-control", [
    ["spin left", "-2.8", w(0, 1, 0.28, 0.05)[0]],
    ["straight 0.2", "4.0", w(0.2, 0, 0.28, 0.05)[1]],
    ["arc left", "2.6", w(0.2, 0.5, 0.28, 0.05)[0]], ["arc right", "5.4", w(0.2, 0.5, 0.28, 0.05)[1]],
    ["arc radius", "0.40 m", fixed(0.2 / 0.5, 2) + " m"],
    ["b 0.34 arc left", "2.3", w(0.2, 0.5, 0.34, 0.05)[0]], ["b 0.34 arc right", "5.7", w(0.2, 0.5, 0.34, 0.05)[1]],
    ["r 0.04 arc left", "3.3", w(0.2, 0.5, 0.28, 0.04)[0]], ["r 0.04 arc right", "6.8", w(0.2, 0.5, 0.28, 0.04)[1]],
    ["0.5 m/s 2 rad/s left", "4.4", w(0.5, 2, 0.28, 0.05)[0]], ["0.5 m/s 2 rad/s right", "15.6", w(0.5, 2, 0.28, 0.05)[1]],
  ]);
  compare("guided DiffDrive", "b 0.34 straight unchanged", "4.0 4.0", w(0.2, 0, 0.34, 0.05).join(" "));
}
{
  const R = Math.PI / 180;
  const tr = (p, t) => panTilt.echo(panTilt.cameraTransform(p * R, t * R))[0].replace("- Translation: ", "");
  guided("PanTilt", "m4/urdf-tf", [
    ["pan 30", "[-0.043, 0.010, 0.305]", tr(30, 0)],
    ["pan 0", "[-0.040, 0.000, 0.305]", tr(0, 0)],
    ["tilt 30", "[-0.043, 0.000, 0.295]", tr(0, 30)],
    ["tilt -30", "[-0.043, 0.000, 0.315]", tr(0, -30)],
  ]);
}
{
  const px = (x, y, z, k1 = -0.12, k2 = 0.03) => {
    const cam = { ...camera.TRUE_CAMERA, fx: 500, fy: 500, k1, k2 };
    const p = [x / 1000, y / 1000, z / 1000];
    const d = camera.project(p, cam, false), i = camera.project(p, cam, true);
    return { d: `(${fixed(d[0], 1)}, ${fixed(d[1], 1)})`, i: `(${fixed(i[0], 1)}, ${fixed(i[1], 1)})`, e: fixed(Math.hypot(d[0] - i[0], d[1] - i[1]), 1) + " px" };
  };
  const a = px(100.8, 60.5, 500.8), b = px(100.8, 60.5, 500.8, 0, 0), c = px(413.7, 295.5, 698.0), d = px(100.8, 60.5, 250.4);
  guided("Camera", "m5/camera-calibration", [
    ["default with distortion", "(420.0, 300.0)", a.d], ["default without", "(420.6, 300.4)", a.i], ["default difference", "0.8 px", a.e],
    ["k1 = k2 = 0 difference", "0.0 px", b.e],
    ["corner with distortion", "(600.0, 440.0)", c.d], ["corner without", "(616.3, 451.7)", c.i], ["corner difference", "20.1 px", c.e],
    ["Z 250.4 difference", "5.9 px", d.e],
  ]);
}
{
  const b = (kp, kd) => { const m = jointFreq.margins(kp, kd), s = jointFreq.closed(kp, kd); return { m, over: fixed(s.over, 0) + " %" }; };
  const a = b(2.86, 0.115), c = b(2.86, 0), d = b(5, 0.115), e = b(8, 0.115);
  guided("Bode", "m5/control-modelling", [
    ["default ωc", "34.6 rad/s", fixed(a.m.wc, 1) + " rad/s"], ["default PM", "56°", fixed(a.m.pm, 0) + "°"],
    ["default phase crossover", "150.8 rad/s", fixed(a.m.wpc, 1) + " rad/s"],
    ["default GM", "14.2 dB", fixed(a.m.gm, 1) + " dB"], ["default GM factor", "5.1", fixed(10 ** (a.m.gm / 20), 1)],
    ["default overshoot", "2 %", a.over],
    ["kd 0 PM", "15°", fixed(c.m.pm, 0) + "°"], ["kd 0 GM", "7.5 dB", fixed(c.m.gm, 1) + " dB"], ["kd 0 overshoot", "66 %", c.over],
    ["kp 5 PM", "40°", fixed(d.m.pm, 0) + "°"], ["kp 5 overshoot", "16 %", d.over],
    ["kp 8 PM", "26°", fixed(e.m.pm, 0) + "°"], ["kp 8 overshoot", "38 %", e.over],
  ]);
}
{
  const [phi, gam] = lqrModel.cartpoleDiscrete();
  const run = (q1, q3, r) => {
    const k = lqrModel.lqr(phi, gam, lqrModel.diag4([q1, 1, q3, 1]), r);
    return { k: "[" + k.map((v) => fixed(v, 2)).join(", ") + "]", peak: fixed(lqrModel.balance(k, 10, 4.0, null, true).fpeak, 2) + " N" };
  };
  const a = run(1, 10, 1), b = run(1, 10, 0.01), c = run(100, 10, 1), d = run(1, 10, 10);
  guided("Lqr", "m5/state-space-lqr", [
    ["default K", "[-0.92, -1.75, -18.76, -3.03]", a.k], ["default peak", "3.28 N", a.peak],
    ["R 0.01 K", "[-6.86, -10.95, -59.07, -11.51]", b.k], ["R 0.01 peak", "10.00 N", b.peak],
    ["Q1 100 K", "[-9.01, -6.54, -29.74, -4.91]", c.k], ["Q1 100 peak", "5.19 N", c.peak],
    ["R 10 K", "[-0.29, -0.78, -15.51, -2.37]", d.k], ["R 10 peak", "2.71 N", d.peak],
  ]);
}
{
  const iv = (k, n) => { const [lo, hi] = wilson.wilson(k, n); return `${fixed(100 * lo, 1)} .. ${fixed(100 * hi, 1)} %`; };
  const width = (k, n) => { const [lo, hi] = wilson.wilson(k, n); return 100 * (hi - lo); };
  guided("Wilson", "m6/policy-evaluation", [
    ["61/100", "51.2 .. 70.0 %", iv(61, 100)], ["122/200", "54.1 .. 67.5 %", iv(122, 200)],
    ["10/10", "72.2 .. 100.0 %", iv(10, 10)], ["9/10", "59.6 .. 98.2 %", iv(9, 10)], ["50/50", "92.9 .. 100.0 %", iv(50, 50)],
    ["width n 100", "18.8", fixed(width(61, 100), 1)], ["width n 200", "13.4", fixed(width(122, 200), 1)],
  ]);
}
{
  const { lo, hi } = actionTokens.ranges();
  const at = (a) => { const t = actionTokens.toBins(a, lo[0], hi[0]); const b = actionTokens.fromBins(t, lo[0], hi[0]); return [String(t), fixed(b, 2) + "°", fixed(Math.abs(a - b), 2) + "°"]; };
  const start = Math.round(actionTokens.firstChunkValue() * 10) / 10;
  const a = at(start), z = at(0), c = at(100);
  guided("ActionToken", "m6/vla-models", [
    ["joint 0 low", "-83.73°", fixed(lo[0], 2) + "°"], ["joint 0 high", "77.37°", fixed(hi[0], 2) + "°"],
    ["bin width", "0.629°", fixed((hi[0] - lo[0]) / 256, 3) + "°"],
    ["default angle", "16.3°", fixed(start, 1) + "°"],
    ["16.3 token", "158", a[0]], ["16.3 decoded", "16.02°", a[1]], ["16.3 error", "0.28°", a[2]],
    ["0 token", "133", z[0]], ["0 decoded", "0.28°", z[1]],
    ["100 token", "255", c[0]], ["100 decoded", "77.06°", c[1]], ["100 error", "22.94°", c[2]],
  ]);
}

console.log(`widgets: ${checks} checks, ${failed} failed`);
process.exitCode = failed === 0 ? 0 : 1;
