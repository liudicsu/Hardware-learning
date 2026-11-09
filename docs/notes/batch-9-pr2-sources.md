# Batch-9 PR2 source, scope and validation audit

Base: 159f6ffac67f95916bd00cc5fc83ddc61220b63e (#137 merged). Proposal §9 PR2 locks: H3 3.5 so101-arm absolute vs incremental encoders +150, H4 9.8 visual-servoing TraceVLA visual trace prompting +210. No arithmetic mismatch: curriculum.ts on 159f6ff gives M3 1470 (so101-arm 240), M9 3270 (visual-servoing 420) and site 25020; after this PR M3 1620, M9 3480 and site 25380; 71 lessons. All 201 prior expected files remain byte-identical; two are added. README site copy updated 25 020 → 25 380.

## Opened sources (curl -L, 2026-11-09, Asia/Shanghai UTC+8)

- `wiki-rotary-encoder`: https://en.wikipedia.org/wiki/Rotary_encoder, HTTP 200. Absolute encoders keep position through power loss; incremental encoders need a reference; multi-turn types are battery-powered, geared, or self-powered (Wiegand).
- `dxl-xl330-emanual`: https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/, HTTP 200. Contactless absolute encoder (12-bit, 360°, 4096 pulse/rev); Position Control Mode 0–4,095; Extended Position Control Mode multi-turn ±256 rev; in Extended Position Control Mode, power-off resets Present Position to the single-turn absolute value. Numbers 以原文为准. The XL330 is not in the SO-101 BOM; it is used only as a documented example of a turn count lost at power-off. No claim is made about STS3215 multi-turn modes.
- `tracevla-paper`: https://arxiv.org/abs/2412.10345, HTTP 200, and the HTML full text https://arxiv.org/html/2412.10345, HTTP 200 (Zheng et al., TraceVLA). Co-Tracker on a K×K grid, active points, M sampled traces overlaid on the current frame; both original and overlaid image fed with a separator token; trace dropout α; K=40, M=5, N=6; 150K trajectories; OpenVLA 7B and a 4B Phi-3-Vision variant; about 10 % over OpenVLA on 137 SimplerEnv configurations and 3.5x on 4 real WidowX tasks; naive history-frame concatenation distracts the model. Paper numbers 以论文为准; nothing reproduced.

## Toy design

- `abs_vs_incr_power_on_toy.py` (3.5): 4096 counts per turn, ±1 count read noise, 20 glitches × five seeds; true angle, unpowered drift and read-noise streams shared by all arms.
  - Arms: A single-turn absolute (mapped to the turn nearest the range middle), B incremental trusted at the calibration zero, C incremental + homing (time cost only: hard stop + one full turn at 90 °/s + 0.5 s), D multi-turn with battery-backed count (flat battery alarms and homes).
  - Scenarios: single-turn joint (−150…150°), three-turn shaft (0…1080°), three-turn shaft with flat battery. No winner is declared.
  - The 2.4 `encoder_index_cal_toy.py` Z-index calibration is referenced, not re-implemented.
- `visual_trace_prompt_toy.py` (9.8): 7×7 grid, fixed blob-coordinate encoder, k-NN behaviour cloning (k=3), 20 demos, 30 eval episodes, five seeds; demos, eval starts and the jitter stream are shared.
  - Arms: A raw frame, B raw + trace of the last 3 frames, C raw + trace lagged 2 frames with 20 % jitter. The trace is drawn only from past frames; no arm sees the hidden sweep direction.
  - Tasks: wipe (history hidden from the frame) and reach (Markov). The trace helps wipe and costs reach; no winner is declared. Section is separate from, and placed after, IBVS.

Independent tests: tools/test_b9_absenc_trace_toys.py.

## Models / reproducibility

opencode free models were tried briefly (timeout 40 s) on the single-turn mapping, and the work was implemented locally:
- deepseek-v4.1-flash-free and glm-5.3-flash-free returned no content within 40 s.
- mimo-v2.6-flash-free returned a single_turn_map equivalent to the local one (nearest-to-middle turn).

Worktree /workspace/hl-b9p2; node_modules hardlinked via `cp -al`.

## Local validation

check_diagrams, check_widgets, check_wokwi, check_quotes, month 1–11 check.sh, lint, next typegen, tsc --noEmit, production build, independent tests. No workflow edits.
