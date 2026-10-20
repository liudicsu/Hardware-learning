# Hardware Learning · 硬件学习

A bilingual (简体中文 / English) study site for becoming a robotics engineer in
six months, built on the curriculum structure of
[“How to become a Robotics Engineer in 6 months (RESOURCES)”](https://x.com/DeRonin_/status/2095180126359105955)
by [@DeRonin_](https://x.com/DeRonin_).

一个中英双语的机器人工程学习网站。课程结构来自 @DeRonin_ 的六个月路线；
每节课的讲解与练习为本站原创，外部资源以卡片 + 外链形式提供，版权归原作者。

## What's in it

- **Month 1 — Electronics, the bench & your tools** (complete): 6 lessons with
  original zh/en text, worked examples, quizzes with instant feedback, an
  embedded [Falstad](https://www.falstad.com/circuit/) simulator (official page
  via iframe, with a fallback link), hands-on task checklists and resource cards.
- **Months 2–6**: goal, topic outline and milestones (lessons to follow).
- Progress (lessons, tasks, quizzes) is saved in `localStorage` only.
- No self-built simulators; Tinkercad, The Construct, Gazebo etc. are external links.

## Stack

Next.js 16 (App Router, static generation) · Tailwind CSS v4 · next-intl v4 ·
MDX (`@next/mdx`).

```bash
npm install
npm run dev      # http://localhost:3000 → redirects to /zh
npm run build && npm start
```

## Checks (local; there is no CI)

The repository has no CI workflow, so the example checks run locally. Each month's
`examples/month-N/check.sh` re-runs the quoted real outputs, `tools/sim/reproduce.sh` the
simulated ones, and `python3 tools/check_quotes.py` checks that every quoted code block and
simulated output in the lessons matches its file in the repo. Pinned extra dependencies:

| Check | Install | Pinned |
| --- | --- | --- |
| `examples/month-3/check.sh` (`arm-compare_sdk`) | `pip install -r examples/month-3/requirements.txt` | `feetech-servo-sdk==1.0.0`, `pyserial==3.5` |
| Months 4–5 ROS 2 / OpenCV / MoveIt runs | `pixi install` in `examples/month-4/` or `examples/month-5/` | see `pixi.toml` |

Without feetech-servo-sdk, `examples/month-3/check.sh` reports `skip  arm-compare_sdk.txt`;
with it, all 12 outputs are compared.

## Project layout

| Path | What |
| --- | --- |
| `src/lib/curriculum.ts` | Months, lessons, tasks, milestones (bilingual) |
| `src/lib/resources.ts` | Resource cards: URL, author, licence, original summary |
| `src/lib/circuits.ts` | Falstad circuits (built-in examples or our own circuit text) |
| `src/content/m1/<lesson>/{zh,en}.mdx` | Lesson bodies |
| `src/components/mdx/*` | `Falstad`, `Quiz`, `Callout`, `Formula` |
| `src/components/progress/*` | localStorage progress UI |
| `messages/{zh,en}.json` | UI strings |
| `docs/CONTENT_GUIDE.md` | How to write a lesson |

## Credits & copyright

- Course structure, goals, milestones and resource list: @DeRonin_.
- Every linked resource belongs to its author; this repository only contains
  original summaries and links.
- Falstad CircuitJS by Paul Falstad and Iain Sharp (GPLv2), embedded from
  falstad.com.
