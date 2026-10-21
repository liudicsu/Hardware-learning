# PR-3 progress (branch `opencode/demos-pr3`)

Resume from git: each finished item is its own commit. Checks run before every push:
`npm run lint`, `npx next typegen`, `npx tsc --noEmit`, `npm run build`,
`python3 tools/check_wokwi.py`, `node tools/check_widgets.mjs`, `python3 tools/check_quotes.py`.

| # | Item | Status | Notes |
|---|---|---|---|
| 0 | lambda = 0.01 note (check_widgets.mjs + CONTENT_GUIDE) | done | hand-written: opencode (deepseek-v4.1-flash-free and glm-5.3-flash-free) both returned "Rate limit exceeded" |
| 1 | m2 first-robots line-follow PD | done | `lineFollow.ts` + `LineFollowWidget`; whole `m2-line_sim.txt` byte-matched (15 checks); hand-written (opencode rate-limited) |
| 2 | m2 sensors-fusion alpha | done | `complementary.ts` + `ComplementaryWidget`; analytic approximation (script uses seeded random noise), checked to 1 decimal place against `offset_flat` (4 checks); page says so in zh/en; hand-written |
| 3 | m3 fdm snap-fit | done | `snapFit.ts` + `SnapFitWidget`; whole `fdm-snap_fit.txt` byte-matched (6 checks); hand-written |
| 4 | m3 transmissions planetary/backlash | done | `gears.ts` + `GearWidget`; whole `tr-gear_calc.txt` byte-matched (20 checks); hand-written |
| 5 | m3 so101 STS packet | done | `stsPacket.ts` + `StsPacketWidget`; whole `arm-sts_packet.txt` byte-matched (7 checks); hand-written |
| 6 | m3 gripper force | done | `gripForce.ts` + `GripForceWidget`; whole `grip-force.txt` byte-matched (5 checks); hand-written |
| 7 | m4 urdf-tf pan/tilt | done | `panTilt.ts` + `PanTiltWidget`; no Python script exists, so the model is the URDF joint chain composed like TF and printed like tf2_echo; `ros-tf_pan30.txt` lines 2-10 byte-matched, time stamp masked as in check.sh (11 checks); `WidgetShell` got an optional `sourceLabel`; hand-written |
| 8 | m4 ros2-control diff drive | skipped (needs a decision) | No Python script and no expected-output file with wheel speeds: the formula lives in the C++ `diff_drive_controller`, and the only numbers in the lesson are quiz q2 (0.3 m/s → 6.0 rad/s) and the qualitative q3 (90° → ~75°). A widget could only be checked against quiz answers, not byte-compared with a script output, so per the rules it is not built. Options: add a tiny `diff_drive.py` + expected file to the lesson first, or accept a quiz-value check. |
| 9 | m5 control-modelling Bode | done | `jointFreq.ts` (CPython complex arithmetic: Smith division, hypot, atan2) + `BodeWidget`; whole `m5-joint_freq.txt` byte-matched (31 checks); hand-written |
| 10 | m5 state-space LQR | done | `lqr.ts` + `LqrWidget`; part 1 (cart-pole: discretise, Riccati LQR, nonlinear balance, recovery-angle search) of `m5-lqr_sim.txt` byte-matched (18 checks); MPC part 2 not ported; hand-written |
| 11 | m6 vla-models action tokens | done | `actionTokens.ts` + `pyRandom.ts` (MT19937 replay of `random.Random`) + `ActionTokenWidget`; lines 1-8 of `action_tokens.txt` byte-matched (8 checks); DCT half not ported (not in the widget); relies on Python ≥ 3.12 compensated `sum()`; hand-written |
| 12 | m6 policy-evaluation Wilson | done | `wilson.ts` + `WilsonWidget`; Wilson interval only (no trials-needed); section 1 of `eval_report.txt` byte-matched (8 checks); hand-written |

## opencode vs hand log

- Item 0: opencode attempted twice (both models rate-limited, no output); written by hand.
- Item 1: opencode tried with both models (rate-limited before any edit); model, widget, shared `Chart.tsx`, `pyfmt.ts` and wiring hand-written.
- Item 2: hand-written (opencode still rate-limited).
- Item 3: hand-written (opencode rate-limited; a 90 s probe got no reply).
- Item 4: hand-written (opencode rate-limited).
- Item 5: hand-written (opencode rate-limited).
- Item 6: hand-written (opencode rate-limited).
- Item 7: hand-written (opencode rate-limited).
- Item 12: hand-written (opencode rate-limited).
- Item 11: hand-written (opencode rate-limited).
- Item 9: hand-written (opencode rate-limited).
- Item 10: hand-written (opencode rate-limited). `pySum` (Python 3.12+ compensated float sum) lives in `pyfmt.ts`, shared with item 11.
