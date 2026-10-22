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
- Next: D-7 slam-nav pose-graph frames.
