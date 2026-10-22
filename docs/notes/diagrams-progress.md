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
  ros2-workspace-tree drafted by opencode (deepseek-v4.1-flash-free), reviewed and fixed by hand; the rest hand-written.
  Next after D-2: Top 10, starting with H-bridge CurrentPath + INPUT_PULLUP.
- D-2 merged as f34b529 (#20). Live check of #17 (encoder) and #20 lessons: /workspace/hl-audit/encoder-live-check.md, all pass.
- D-3 (branch diagrams/d3-hbridge-pullup from f34b529): `kind: "circuit"` specs + CircuitDiagram (state buttons,
  animated conventional-current path); check_diagrams verifies the path only runs over wires, resistors/motors and
  closed switches, and compares computed numbers (`numbers`) with the lesson. Diagrams: hbridge-current-path
  (motors-drivers, AO1/OUT1 = left half-bridge, lesson sentence added), pullup-internal (arduino-io),
  pullup-external (components; same generator). Reviewer nits from #20 fixed (file-node height check, tree
  connectors at name height, set_parameters label next to its arrow). All hand-written.
- Next: D-4 PWM duty + average voltage on Timing, `kind: "timing"` in the registry and check_diagrams.
- D-4 (branch diagrams/d4-pwm-timing from f34b529, parallel to #21): `kind: "timing"` registry spec
  (TimingDiagram.tsx + checkTiming), Timing `average` line and `activeSignals`, PWM diagram pwm-duty-average
  (arduino-io), zh full-width ：， in the encoder stepper. Encoder not migrated (model-generated columns).
  Expected merge conflicts with #21 (types.ts, Diagram.tsx, index.ts, check_diagrams.mjs): when #21 lands,
  merge origin/main, keep both branches (circuit + timing), and keep one DiagramNumber and one numbers check.
  All hand-written.
- D-4 update: #21 squash-merged as adbfcdc and merged into D-4 (merge commit, no rebase). Reviewer nits folded in:
  brake text "in this model" + back-EMF reverse braking current (diagram and lesson zh/en); 0.37 → "about 37 %
  (slightly more than a third)"; INPUT_PULLUP label moved down 4 units; zh.mdx facts for hbridge and pullup;
  aria-label on the circuit state group; check_diagrams path rules (start at a supply, end at a ground, every
  closed switch on the path; closed-loop states need an explicit `loopReason`, used by the H-bridge brake).
  13 diagrams, 2305 checks. Live check of the adbfcdc circuits: 12/12 OK (hl-audit/encoder-live-check.md).
- D-4 merged (#23, squash 7de9d0a). Live check after the deploy: PWM, brake text, encoder punctuation and the
  pull-up label are OK (hl-audit/encoder-live-check.md). PWM at 390 px was 9 px; fixed in D-5.
- D-5 (branch diagrams/d5-i2c-debounce from 7de9d0a):
  - `i2c-read-who-am-i` (sensors-fusion): readReg(REG_WHO_AM_I), field by field, following the MPU-6050
    datasheet's single-byte read (PS rev 3.4 §9.2/§9.3, RM rev 4.2 §4.32).
  - `debounce-quiet-line` (timing-interrupts): real edges from debounce_sim.py (seed 1) via debounce_export.py
    into a committed JSON, which check_diagrams regenerates; the 30 ms rule is the firmware's
    `t - lastEdge > DEBOUNCE_MS`.
  - Timing `columnScale`, `lines` / `narrowLines`, and a text-size check (>= 12 px).
  - #23 nits: PWM zh facts, phase-correct note, one-period narrow layout; zh brake generator wording; zh aria
    colon.
  - Lesson wording fixed to match the firmware: "quiet for more than 30 ms", each bounce measured from the
    previous edge.
  - All hand-written.
- D-5 merged (#25, squash e20ae6e, on top of #22 7293e6f). Live check: 24/24 OK (hl-audit/prc-live-check.md).
- D-5 nits (branch diagrams/d5-nits):
  - The debounce caption now says "simulated" / 模型给出的 bounce edges.
  - check_diagrams pins the I2C field and sender sequences (`PINNED`, datasheet §9.3).
  - Bus values need 4 units of padding inside the flat part of their band, and row cells 2 units on each side.
  - I2C columns are weighted by field (bytes 1.4, ACK 1.2, one-letter fields 0.9) with `columnScale` 42.
  - The debounce line 1 window starts 2 ms earlier, so the "0" band fits.
  - All hand-written.
- D-6 (branch diagrams/d6-sts-bytes from e20ae6e, main a53581a merged in): new `kind: "bytes"` (ByteFields.tsx + checkBytes) and
  `sts-packet-fields` in so101-arm: the six packets printed by sts_packet.py (ping, torque on, goal 2048, read,
  reply 3116 = 273.9 deg, broken checksum). check_diagrams runs the script and requires each drawn line in its
  output. New tone `c` (--dg-c, violet) for the checksum. Lesson fix: the bit flip is in the high data byte
  (0C -> 0D), zh and en. All hand-written.
- D-5 nits merged (#26, squash a53581a); D-6 merged (#28, squash bc5d0da), merged into D-7 (#29).
- (已废弃 / obsolete: the "0.2 m / 0.2 rad" node rule below was replaced by the review fix that follows) D-7 (branch diagrams/d7-slam-pose-graph from e20ae6e, parallel to #26/#28): `kind: "poseGraph"`
  (PoseGraph.tsx + checkPoseGraph) and `slam-pose-graph` in slam-nav (D091 part 2; the TF chain is D-2's
  slam-tf-chain): 4 frames — a node every 0.2 m / 0.2 rad, scan matching, drift gap after one lap (0.28 m),
  loop closure with the corrected graph. Node spacing checked against slam.yaml node by node; route, 3 % turn
  error and linear correction marked illustrative. All hand-written.
- D-7 review fix (#29): the node rule follows SLAM Toolbox 2.8.5 (shouldProcessScan's straight-line
  sqrt(0.8) x 0.2 = 0.179 m filter, heading ignored there; then Karto's 0.2 m / 0.2 rad). Route now turns on the
  spot like tour.py (turns add no nodes); lesson L11 and the slam.yaml comments fixed in zh and en; caption: rolling
  scan buffer (10 scans / 10 m), Ceres solver; loop-closure step: loop_search_maximum_distance 3 m, chain >= 10.
- D-7 second review (#29): node 0 is the first scan (first_measurement_ branch, slam_toolbox_common.cpp:771-777,
  before every other test), 41 nodes; "first 5" comments fixed (callbacks 2-4 are dropped: scan_ctr++ at :769
  before scan_ctr < 5 at :795); hand-computed nodes 0, 1, 12, 13 pinned in check_diagrams.
- D-7 merged (#29, squash 2bfb55e). Live check of #26/#28/#29: 16/16 OK (hl-audit/prc-live-check.md).
- Text size >= 12 px (branch text-size-12px from 2bfb55e): block-diagram and circuit fonts 12.3 units; narrow
  layouts <= 340 units, wide <= 752 units, wide layout from 1280 px (xl); cascade, slam-tf-chain,
  urdf-two-publishers, ros2-workspace-tree (layout now generated), hbridge and pullup re-laid out. `<Chart>`
  follows its box width and labels fewer ticks on narrow screens (PidWidget now uses Chart); the Wilson bar
  the same; IK axis letters 15 units; diff-drive labels text-xs; text-[11px] -> text-xs (resource credits,
  Wokwi badge, gear and snap-fit readouts, diff-drive wheel speeds); QuadratureTiming 39 units per column, en
  axis labels shortened. check_diagrams guards against small sizes; tools/check_text_size.mjs is the rendered
  check. All hand-written.
- D093 (branch diagrams/d093-nav2-pipeline from aa8832d): `nav2-pipeline` in slam-nav "What Nav2 runs", a block
  diagram in 4 steps: NavigateToPose goal -> bt_navigator -> planner_server (NavFn, global costmap static +
  obstacle + inflation) and controller_server (RPP <= 0.25 m/s, 3 m x 3 m local costmap) -> velocity_smoother ->
  collision_monitor -> /diff_drive_controller/cmd_vel (TwistStamped). Values checked against nav2.yaml (11 facts);
  cmd_vel_nav is nav2_bringup navigation_launch.py 1.3.13's remapping (L137, L215), named in the caption.
  behavior_server's recoveries are left out (caption). All hand-written.
