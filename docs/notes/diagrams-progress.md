# Diagrams progress (diagram-audit implementation)

Plan: /workspace/hl-audit/diagram-audit.md (reviewed). Working clone: /workspace/hl-diagram-audit-src.
Rules: one small PR per item from latest origin/main, never merge, never force-push; CI green locally
(check_widgets, lint, check_wokwi, check_quotes, check_diagrams, next typegen, tsc, build) and on the PR;
390 px screenshots with no horizontal overflow. `<Timing>` belongs to the encoder PR (#17, branch
opencode/encoder-section) — do not build it here; build on it only after it is merged into main.

## Component foundation (PR D-1, branch diagrams/d1-foundation)

- `src/lib/diagrams/types.ts` data model (L10n, layouts wide + narrow ≤ 360 units, steps, facts)
- `src/lib/diagrams/ui.ts` zh/en strings of the frame and step controls
- `src/lib/diagrams/index.ts` registry; specs in `src/lib/diagrams/specs/*.ts`
- `src/components/diagrams/{Diagram,BlockDiagram,StepControls}.tsx`; `--dg-*` tokens in globals.css
- MDX: `<Diagram id="..." />`, identical in zh.mdx and en.mdx; page.tsx passes the locale
- `tools/check_diagrams.mjs` (added to CI): both languages, Chinese labels, geometry, label fit, facts vs scripts, zh/en tag parity

## The 8 ASCII diagrams that overflow at 390 px

| # | lesson | diagram id | PR | status |
|---|---|---|---|---|
| 1 | m3/pid-control cascade | pid-cascade | D-1 | done |
| 2 | m2/first-robots cascade | first-robots-cascade | D-1 | done |
| 3 | m2/timing-interrupts state machine | reaction-timer-states | D-1 | done |
| 4 | m4/ros2-graph system graph | ros2-graph-system | D-2 | done |
| 5 | m4/urdf-tf two publishers | urdf-two-publishers | D-2 | done |
| 6 | m4/slam-nav TF chain | slam-tf-chain | D-2 | done (laser_link → lidar_link) |
| 7 | m4/ros2-setup workspace tree | ros2-workspace-tree | D-2 | done |
| 8 | m1/git-github three areas + branches | git-areas, git-branches | D-2 | done |

## Next (Top 10, after D-2)

H-bridge CurrentPath (motors-drivers, not the encoder section); INPUT_PULLUP (arduino-io + components);
PWM (needs Timing → wait for #17); I²C step-through; debounce (debounce_sim.py fixed seed); STS ByteFields;
slam-nav pose graph / loop closure frames. Reviewer decisions B (α explanation, line-follower KD, missing
numbers, cart-pole direction, TB6612 OUT1) go into the PR that touches each lesson.

## Log

- D-1: foundation + 3 diagrams (#1–#3). Hand-written (see PR body).
- D-1 merged as b6134d8 (#18). Live check on Pages after deploy: pid-cascade, first-robots-cascade,
  reaction-timer-states in zh/en at 390 and 1280 px: render, steps work, no overflow, no console errors.
- D-2: branch diagrams/d2-ascii-main from b6134d8 (not stacked). Remaining 5 ASCII diagrams (6 specs).
  Node `sub` may now have several lines ("\n"); check_diagrams checks width per line and height.
  ros2-workspace-tree drafted by opencode (glm-5.3-flash-free), reviewed and fixed by hand; the rest hand-written.
  Next after D-2: Top 10, starting with H-bridge CurrentPath + INPUT_PULLUP.
