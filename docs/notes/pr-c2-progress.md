# PR-C2 progress — guided widget experiments and conclusion-only sections

Branch `opencode/prc2-guided`, cut from `origin/main` f2a4373. Companion of PR-C1 (#19).

## Guided experiments (14 widgets; the 15th, IkWidget, is in #19)
Each widget is followed by a numbered "Guided experiment" / "动手实验" list with the exact values the
widget shows. Every value is re-computed by `tools/check_widgets.mjs` (`guided(...)` checks) from the
TS models, so a model change that breaks a step fails CI. Drafted by opencode (deepseek-v4.1-flash-free);
label fixes, value corrections and the checks are hand-written.

## Conclusion-only audit
Full per-month lists: `docs/notes/conclusion-audit/` (m1, m2, m3 section B, m4, m5, m6). Drafted by opencode, reviewed by hand.

Fixed in this PR (derivation added, en + zh, each number checked by script):
- m1 components — RC charge 1 − e^−1 = 0.632, 1 − e^−5 = 0.993.
- m1 bench-multimeter — 0.1 Ω shunt + 0.05 Ω fuse = 0.15 Ω; 40.9 mA, 4.1 mV, 60 A.
- m2 arduino-io — ADC 13 cycles / 125 kHz = 104 µs; PWM 16 MHz / 64 / 256 = 976.6 Hz, / 510 = 490.2 Hz.
- m2 sensors-fusion — 32768 / 2 g = 16384 LSB/g, 32768 / 250 = 131.07 LSB/(°/s).
- m3 transmissions — planetary neighbour rule (25.98 / 21.21 / 17.63 vs 20), also in the model and widget.
- m4 urdf-tf — optical-frame rotation R = Rz(−90°)·Rx(−90°) applied to each axis.
- m4 gazebo-sim — mast offset 0.12 − (−0.06) = 0.18 m from the xacro joints.
- m6 policy-evaluation — 80 % vs 90 % trial-count worked example (198.96 → 199).
- m5 moveit-pick-place reach (0.251 m) — fixed in #19, since that section is new there.

Listed, not fixed here: the remaining rows in the audit files. They either need a new simulation run or
datasheet source (m4 Isaac requirements, setup prices, scan smear), or sit in lessons that #19 edits
(m5 kinematics-ik, moveit-pick-place, state-space-lqr), where a second edit would conflict. They are
the next follow-up.
