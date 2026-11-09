# Batch-9 PR3 source, scope and validation audit

Base: 64579b58cf71713daae5792ec49a00692e97533e (#138 merged). Proposal §9 PR3 locks: H5 6.3 vla-models RDT2 three-stage +210, H6 11.5 cross-embodiment-datasets UniVLA latent actions +210. No arithmetic mismatch: curriculum.ts on 64579b5 gives M6 1980 (vla-models 570), M11 3000 (cross-embodiment-datasets 330) and site 25380; after this PR M6 2190, M11 3210 and site 25800; 71 lessons. All 203 prior expected files remain byte-identical; two are added. README site copy updated 25 380 → 25 800.

## Opened sources (curl -L, 2026-11-09, Asia/Shanghai UTC+8)

- `rdt2-paper`: https://arxiv.org/abs/2602.03310, HTTP 200, and the HTML full text https://arxiv.org/html/2602.03310, HTTP 200 (Liu et al., RDT2). 7B Qwen2.5-VL; over 10,000 hours of UMI data from more than 100 households; Stage 1 RVQ tokenizer + cross-entropy with 1024 reserved vocabulary entries (128K iterations); Stage 2 frozen VLM, a 400M RDT-1B-variant action expert with GQA and per-layer cross-attention, flow-matching loss, five forward passes per chunk (66K iterations); Stage 3 distillation into a single-step generator G(A⁰) = A⁰ + v_θ′(0, A⁰, ·) initialised from the expert; RVQ saves up to about two-thirds of tokens vs FAST at the same error, uniform binning has the lowest error with far more tokens. Task scores 以论文为准; nothing reproduced.
- `univla-paper`: https://arxiv.org/abs/2505.06111, HTTP 200, and the HTML full text https://arxiv.org/html/2505.06111, HTTP 200 (Bu et al., UniVLA, RSS 2025). VQ-VAE latent actions on DINOv2 features of frame pairs; Stage 1 with T5 instruction embeddings absorbs task-irrelevant dynamics, Stage 2 learns task-centric latents; Prismatic-7B policy with |C| extra tokens, N = 4 per step (16⁴ vs OpenVLA's 256⁷); 10.8M per-embodiment decoder heads; 960 vs 21,500 A100-hours; LIBERO +18.5 %, navigation +29.6 %, real robot +36.7 % over OpenVLA; task-irrelevant latents give near-zero LIBERO-Long success. Numbers 以论文为准; nothing reproduced.

## Toy design

- `rdt2_rvq_fm_distill_toy.py` (6.3): 4-number action chunks from four heading modes; five seeds; shared chunks and noise draws.
  - Part 1, equal 8-bit budget: bins_4x4, single_vq_256, rvq_2x16, rvq_4x4; held-out MSE, tokens, entries, unused entries.
  - Part 2: the expert is the exact flow-matching field of smoothed training chunks (not trained, not conditioned); fm_1 / fm_2 / fm_5 Euler vs two lookup students (nearest pair, average of 3) that cost 2000 offline expert NFE; precision, recall, off-manifold share, distinct outputs. No winner is declared.
  - New section after the OpenHelix dual-system section (unchanged); ≠ VQ-BeT 6.1, ≠ OneDP 10.1.
- `univla_latent_action_toy.py` (11.5): 2-D reach around an obstacle, two embodiments (B: axes swapped, one flipped, different gains), a task-irrelevant wanderer; five seeds; shared video, wanderer paths and evaluation starts.
  - Arms: A raw BC from A only, B latent with the actor split + per-embodiment linear decoder, C latent over the whole frame change, D raw BC on the decoder's 20 labels. Equal codebook (12), Lloyd iterations, grid and decoder labels; decoder input 2 vs 4 numbers (labelled). Language is a known actor mask (UniVLA's two-stage split not modelled).
  - Scenarios wanderer and still_scene. No winner is declared. ≠ OXE-AugE toys on this lesson; ≠ 9.9 LAPA / IDM curve.

Independent tests: tools/test_b9_rdt2_univla_toys.py.

## Heading clean-up

All lesson headings that carried a minute count were cleaned in en and zh (58 "(+N min)" / "（+N min）" / "（+N 分钟）" suffixes, plus 4 zh "（本课 N min 中新增 M min）"), including the 9.8 TraceVLA heading. A check_diagrams lock now rejects minute counts in any lesson heading. Two heading pairs still start with a pipeline label ("Batch-6 H2" in 8.4 ros2-hardware-interface, "Batch-6 H5" in 9.3 effort-admittance); they carry no minutes and were left unchanged.

## Models / reproducibility

opencode free models were tried briefly (timeout 40 s) on the flow-matching field, and the work was implemented locally: deepseek-v4.1-flash-free, glm-5.3-flash-free and mimo-v2.6-flash-free all returned no content within 40 s.

Worktree /workspace/hl-b9p3; node_modules hardlinked via `cp -al`.

## Local validation

check_diagrams, check_widgets, check_wokwi, check_quotes, month 1–11 check.sh, lint, next typegen, tsc --noEmit, production build, independent tests. No workflow edits.
