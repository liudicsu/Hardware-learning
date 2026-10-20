# Hardware Learning · 硬件学习

A bilingual (简体中文 / English) study site for becoming a robotics engineer in six months. The structure,
monthly goals, milestones and resource list follow
[“How to become a Robotics Engineer in 6 months (RESOURCES)”](https://x.com/DeRonin_/status/2095180126359105955)
by [@DeRonin_](https://x.com/DeRonin_). Every lesson text, worked example, quiz and exercise on the site is original;
external resources are shown as cards with a link, and their copyright stays with their authors.

一个中英双语的机器人工程学习网站。课程结构、每月目标、里程碑和资源清单来自 @DeRonin_ 的六个月路线；
每节课的讲解、例题、小测验和练习都是本站原创，外部资源以卡片 + 外链形式提供，版权归原作者。

## What the site contains / 网站内容

Six months, 34 lessons, all in Chinese (default, `/zh`) and English (`/en`):

| Month | Topic | Lessons |
| --- | --- | --- |
| 1 | Electronics, the bench & your tools / 电子基础、工作台与工具 | 6 |
| 2 | Microcontrollers, motors & sensors / 单片机、电机与传感器 | 6 |
| 3 | Mechanical design, CAD & manufacturing (plus a PID supplement) / 机械设计、CAD 与制造 | 6 |
| 4 | ROS 2 & simulation / ROS 2 与仿真 | 6 |
| 5 | The maths that makes robots work: control, kinematics, perception, MoveIt 2 / 控制、运动学、感知 | 5 |
| 6 | Robot learning, specialisation & getting hired / 机器人学习、专精与求职 | 5 |

Each lesson has an explanation, worked examples, quizzes with instant feedback, a hands-on task checklist and
resource cards; Month 1 embeds the official [Falstad](https://www.falstad.com/circuit/) circuit simulator.
Progress (lessons, tasks, quizzes) is stored in the browser's `localStorage` only; there is no login and no tracking.

**Every program quoted in a lesson is in this repository** (`examples/`, `tools/sim/`), byte for byte, and every
quoted output can be re-created with the scripts below. Outputs that come from a simulator or a toy model are
labelled “Simulated output / 仿真输出” on the site; nothing in the repository is a measurement on real hardware.

## Run the site locally / 本地运行

Prerequisites: **Node.js 20.9 or newer** (Next.js 16 requires it; tested with Node 20.19 and npm 11) and npm.

```bash
git clone https://github.com/liudicsu/Hardware-learning.git
cd Hardware-learning
npm ci              # install the exact versions from package-lock.json
npm run dev         # http://localhost:3000 → redirects to /zh; /en for English
```

Production build:

```bash
npm run build       # prerenders every page (2 locales × home, about, resources, 6 months, 34 lessons)
npm start           # serves the build on http://localhost:3000 (npm start -- -p 3100 for another port)
```

### Static export for GitHub Pages / GitHub Pages 静态导出

The static export is only enabled when `PAGES_BASE_PATH` is set at build time, so the commands above are unchanged.

```bash
PAGES_BASE_PATH=/Hardware-learning npm run build   # writes out/
```

This builds the site under `/Hardware-learning` as static HTML. The next-intl proxy is not used; `/` is served by
`public/index.html`, which redirects to `/zh/`, and `out/404.html` comes from `src/app/global-not-found.tsx`.
To preview it, copy `out/` into a folder named `Hardware-learning` inside a temporary directory, serve that
directory, and open <http://localhost:8000/Hardware-learning/>:

```bash
mkdir -p /tmp/pages-preview/Hardware-learning
cp -R out/. /tmp/pages-preview/Hardware-learning/
(cd /tmp/pages-preview && python3 -m http.server 8000)
```

`.github/workflows/pages.yml` deploys every push to `main` to <https://liudicsu.github.io/Hardware-learning/>.

Code checks: `npx tsc --noEmit` and `npm run lint` (ESLint). `.github/workflows/ci.yml` runs `npm run lint`, `npx tsc --noEmit` and `npm run build` on every pull request and push to `main`.

## Reproduce the lesson outputs / 复现课程中的输出

All commands run from the repository root. Each check prints `same <name>` for every output that matches and
`DIFF <name>` (with a diff file) for one that does not, and exits non-zero on any difference.
Tested on Debian 13 (x86-64); Ubuntu 24.04 should work the same way.

### Lesson quotes vs. repository files: `tools/check_quotes.py`

```bash
python3 tools/check_quotes.py
```

Python 3.9+ only. Checks that every code block under a `<CodeSource>` is byte-for-byte its file, and every block
inside a `<SimOutput>` appears in a file under `tools/sim/expected/` or `examples/month-N/expected/`
(rules in [docs/CONTENT_GUIDE.md](docs/CONTENT_GUIDE.md)). Prints e.g.
`180 code blocks, 136 simulated outputs checked, 0 problems`.

### Simulated outputs, Months 2, 3, 5 and 6: `tools/sim/reproduce.sh`

Needs gcc, [simavr](https://github.com/buserror/simavr) (the library, used by the harness in `tools/sim/avrrun/`),
libelf, Python 3 and [arduino-cli](https://arduino.github.io/arduino-cli/latest/installation/) with the AVR core:

```bash
sudo apt install gcc make libsimavr-dev libelf-dev python3   # add `simavr` if you also want the stand-alone CLI
arduino-cli core update-index
arduino-cli core install arduino:avr     # tested with 1.8.8 (arduino-cli 1.5.1)
tools/sim/reproduce.sh                   # about 1 minute
```

It builds the simavr harness, compiles the Uno sketches, runs them with simulated parts, runs the Python toy models,
diffs everything against `tools/sim/expected/`, then runs `tools/check_quotes.py`, `tools/sim/ros/run.sh`,
`tools/sim/m5/run.sh` and `examples/month-6/check.sh`. The ROS and OpenCV parts print `skip …` unless their
environment (below) is active. `tools/sim/reproduce.sh --compile-only-too` also compiles the ESP32 and
line-follower sketches (needs `arduino-cli core install esp32:esp32` and `arduino-cli lib install QTRSensors`).
Details and how to run one case by hand: [tools/sim/README.md](tools/sim/README.md).

### Real runs on a computer: `examples/month-N/check.sh`

| Check | Needs | Command |
| --- | --- | --- |
| Month 1: Python command-line tools | Python 3 | `bash examples/month-1/check.sh` |
| Month 3: OpenSCAD parts and Python calculators | Python 3, [OpenSCAD](https://openscad.org/) (tested with 2021.01), and for `arm-compare_sdk` the pinned Feetech SDK (below) | `bash examples/month-3/check.sh` |
| Month 4: ROS 2 programs that need no robot | ROS 2 Jazzy (pixi environment below) | `cd examples/month-4 && pixi run check` |
| Month 6: imitation-learning toy models, evaluation and portfolio check | Python 3 (standard library only) | `bash examples/month-6/check.sh` |

Month 2 and Month 5 have no `check.sh`; their outputs are simulated and covered by `tools/sim/reproduce.sh`
and `tools/sim/m5/run.sh`.

**Month 3 with `feetech-servo-sdk==1.0.0`.** Without the SDK, `examples/month-3/check.sh` reports
`skip  arm-compare_sdk.txt`; with it, all 12 outputs are compared. Install it in a virtual environment so your
system Python stays untouched:

```bash
python3 -m venv /tmp/m3venv
/tmp/m3venv/bin/pip install -r examples/month-3/requirements.txt   # feetech-servo-sdk==1.0.0, pyserial==3.5
PATH=/tmp/m3venv/bin:$PATH bash examples/month-3/check.sh           # 12 same, 0 DIFF, 0 skipped
```

### ROS 2 Jazzy, Gazebo, OpenCV and MoveIt 2 (Months 4 and 5): pixi + RoboStack

The Month 4 and 5 runs use ROS 2 Jazzy from [RoboStack](https://robostack.github.io/) (conda packages) through
[pixi](https://pixi.sh). This works on any 64-bit Linux and installs nothing system-wide; Gazebo runs headless,
no GPU is needed. Each month has its own `pixi.toml`:

```bash
curl -fsSL https://pixi.sh/install.sh | bash    # installs pixi into ~/.pixi/bin; open a new shell afterwards

cd examples/month-4
pixi install          # ROS 2 Jazzy, Gazebo Harmonic, ros2_control, SLAM Toolbox, Nav2, colcon (about 2 GB)
pixi run check        # examples/month-4/check.sh: real runs of the ROS 2 programs
pixi run sim          # tools/sim/ros/run.sh: Gazebo and mock-hardware runs, SLAM and Nav2 (several minutes)

cd ../month-5
pixi install          # NumPy, OpenCV, ROS 2 Jazzy and MoveIt 2
pixi run sim          # tools/sim/m5/run.sh: camera calibration on synthetic photos, MoveIt 2 pick and place
```

`pixi shell` (in either folder) opens a shell with `ros2`, `colcon` and `gz` on the PATH. The Gazebo and MoveIt
runs differ slightly from run to run, so `examples/month-4/compare.py` compares their numbers with a tolerance and
masks timestamps. A few lines of `examples/month-4/check.sh` (`ros2 topic hz`, `ros2 bag info` counts, the first
`tf2_echo` line) depend on startup timing: on a busy machine one of them can show a `DIFF`; run it again on an idle
machine before treating it as a real difference. `pixi install` writes `.pixi/` and `pixi.lock` next to the
`pixi.toml`; both are git-ignored (and ignored by ESLint and TypeScript). On Ubuntu 24.04 you can use the official apt packages instead
(see [examples/month-4/README.md](examples/month-4/README.md)).

## Writing or changing a lesson / 编写课程

Read **[docs/CONTENT_GUIDE.md](docs/CONTENT_GUIDE.md)** first; it is the binding standard (structure, zh/en parity,
MDX components, `CodeSource` / `SimOutput`, reproducibility). Decision notes and verification records are in
[docs/notes/](docs/notes/).

## Project layout / 目录结构

| Path | What |
| --- | --- |
| `src/app/[locale]/…` | Pages: home, month overview, lesson, resources, about (Next.js 16 App Router) |
| `src/content/m<N>/<lesson>/{zh,en}.mdx` | Lesson bodies |
| `src/lib/curriculum.ts` | Months, lessons, tasks, milestones (bilingual) |
| `src/lib/resources.ts` | Resource cards: URL, author, licence, original summary; `extra: true` = our supplement, not in the original list |
| `src/lib/circuits.ts` | Falstad circuits |
| `src/components/mdx/*` | `Falstad`, `Quiz`, `Callout`, `Formula`, `CodeSource`, `SimOutput`, code blocks |
| `src/components/progress/*` | localStorage progress UI |
| `messages/{zh,en}.json` | UI strings (next-intl) |
| `examples/month-N/` | Every program quoted in the lessons, with `check.sh` and `expected/` where there are real runs |
| `tools/sim/` | simavr harness, toy models, ROS/MoveIt runners, `expected/` outputs, `reproduce.sh` |
| `tools/check_quotes.py` | Lesson quotes vs. repository files |
| `docs/` | Content guide and notes |

Stack: Next.js 16 (App Router, static generation) · React 19 · Tailwind CSS v4 · next-intl v4 · MDX (`@next/mdx`).

## Credits & copyright / 版权

- Course structure, goals, milestones and resource list: @DeRonin_.
- Every linked resource belongs to its author; this repository contains only original summaries and links.
- Falstad CircuitJS by Paul Falstad and Iain Sharp (GPLv2), embedded from falstad.com.
