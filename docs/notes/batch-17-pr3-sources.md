# Batch-17 PR3 sources / 来源记录

Base `5825c942f213b60014c1f9de9435fda17f8ca163` (`5825c94`, main after #170; site **34290**). This PR: M6 policy-evaluation 330→540 (+210), M8 vla-finetune 630→840 (+210); site **34290→34710**; M6 3240→3450, M8 3390→3600; still 71 lessons.

## Opened sources

All six URLs were fetched with curl on 2026-11-12 (Asia/Shanghai), returned HTTP **200**, and were read as text (PDF via pdftotext).

| Resource id | URLs | Version | What is used |
|---|---|---|---|
| `magma-paper` (new) | https://arxiv.org/abs/2502.13130, https://arxiv.org/html/2502.13130, https://arxiv.org/pdf/2502.13130.pdf | v1, submitted 18 Feb 2025 | Title "Magma: A Foundation Model for Multimodal AI Agents"; 13 authors (Jianwei Yang, Reuben Tan, Qianhui Wu, Ruijie Zheng, Baolin Peng, Yongyuan Liang, Yu Gu, Mu Cai, Seonghyeon Ye, Joel Jang, Yuquan Deng, Lars Liden, Jianfeng Gao), matching the proposal. Section 3.2 body read: Set-of-Mark (candidate regions from proposal networks such as segmentation / detection; numeric marks; the model "faces much less difficulties to predict the numeric marks"), coordinates "quantized into 256 bins" (Figure 3 caption), Trace-of-Mark (future traces; "look ahead of time"; "predicting traces uses much fewer tokens"; traces from CoTracker). |
| `chatvla-paper` (new) | https://arxiv.org/abs/2502.14420, https://arxiv.org/html/2502.14420, https://arxiv.org/pdf/2502.14420.pdf | v1, submitted 20 Feb 2025 | Title "ChatVLA: Unified Multimodal Understanding and Robot Control with Vision-Language-Action Model"; 11 authors (Zhongyi Zhou, Yichen Zhu, Minjie Zhu, Junjie Wen, Ning Liu, Zhiyuan Xu, Weibin Meng, Ran Cheng, Yaxin Peng, Chaomin Shen, Feifei Feng), matching the proposal. Body read: robot-only training "yields a performance of 0 across all benchmarks" and "only murmuring"; spurious forgetting as misalignment, a fixed reasoning template seems to "reactivate" it; task interference; 3:1 robot : visual-text co-training following RT-2; Phased Alignment ("first masters embodied control before incrementally integrating multimodal data"); MoE with shared self-attention and control / understanding experts, "in stage 1 training, only the control expert is activated"; system prompts "Answer based on question" / "Predict robot action"; 25 real-world tasks. |

Paper numbers are marked 以论文为准 on the site. The toys are labelled stand-ins and take no benchmark number from either paper. No GPU, UI agent or robot was used (本页未运行).

## Toy design

- `examples/month-6/policy-evaluation/magma_som_tom_toy.py`
  - Scenes: K candidates uniform in [0.05, 0.95]², object 0 the target, constant velocity (regime speed, random direction). Shared scores: target SIGNAL 3.0 + N(0, SIG_B 1.0), distractors N(0, 1.0).
  - Arms: A direct (softmax-weighted point + N(0, SIG_REG 0.01); no trace); B Set-of-Mark + Trace-of-Mark (argmax mark, 256-bin quantisation, trace with velocity + N(0, SIG_TRK)); C shuffled marks (uniform permutation of the labels).
  - Metrics: grounding % (within RADIUS 0.05 now), trace ADE × 100 over L 8, success % (planned point at step L within RADIUS of the target then). SCENES 400 per seed.
  - Common random numbers: every scene's positions, velocities, scores, noises and permutation drawn once per (regime, seed), seeds 0–4.
  - No integration step: positions are closed-form per step.
- `examples/month-8/vla-finetune/chatvla_phased_alignment_toy.py`
  - Linear stand-in: z = A x (shared), f = P z (M=2 features), control â = c · f, VQA logits = V f (NQ=3); labels are the frozen model's own answers (baseline 100.0000 %).
  - Arms: A robot-only SFT through one P; B MoE (P_ctrl / P_vqa), stage 1 = first R − R2 robot batches (only the control path and A), stage 2 = last R2 (100) robot batches interleaved with Q VQA batches; C naive joint through one P, robot : VQA = 3:1 from step 0. R=300, BATCH=8, LR=0.05, TOL=0.25, TEST=400.
  - Common random numbers: init perturbation, every robot batch, every VQA batch and the test set drawn once per (regime, seed), seeds 0–4.
  - No integration step: discrete SGD updates, no plant.
- Labels as in batch-15/16/17: tie → numerically zero below 1e-9 → near-tie |m| ≤ sd → consistent ("small" under 20 % of the smaller arm mean, else "clear"), always with a sign count.

## Results (k/N = seeds with the reported sign)

Magma (paired):
- cluttered (K 8): B−A grounding +70.6000±1.9653, success +82.1000±0.6982, ADE −9.9207±0.7258, all clear 5/5. C−B grounding −78.7500±1.2119, success −78.1000±1.4427, ADE +36.8265±1.1706, clear 5/5.
- single_target (K 1, declared tie): **B−A grounding and success: tie, identical on every seed (both 100.0000 %).** B−A ADE −1.1249±0.0282, clear 5/5. C−B tie on all three (identity permutation).
- static_jitter (K 2, declared tie/lose): **B−A success −62.1500±1.2324, clear 5/5 (B loses).** B−A ADE +2.8806±0.1251 clear 5/5; B−A grounding +24.1000±0.8023 clear 5/5. C−B grounding −48.2500±1.1592, success −5.7500±0.3953, clear 5/5.

ChatVLA (paired):
- conflict: B−A VQA +40.9500±2.0721 clear 5/5; B−A control tie (identical). C−B VQA −29.6500±3.7442 clear 5/5; C−B control −4.6500±4.1026 small consistent 5/5. B stage-1 VQA 72.4500 %.
- aligned (declared near-tie on everything): control ties; **B−A VQA +3.0500±1.0954 and C−B VQA −0.4500±0.3260, small consistent 5/5 — the declared near-tie did not hold.**
- few_vqa: B−A VQA +27.7000±3.0177 clear 5/5; C−B VQA −27.5500±2.8140 clear 5/5; control ties.

Every number quoted in the page prose and Summary sentences is printed by the toy and appears in `examples/month-*/expected/`; the new lock checks every `m±sd` and every four-decimal number in the new sections and Summary sentences against the expected output. No side run was made or quoted.

## Post-hoc choices

- Magma: none. No constant, arm, metric or regime was changed after the first run; the expected output is the first run.
- ChatVLA: none. No constant, arm, metric or regime was changed after the first run; the aligned regime's failed near-tie is printed and stated on the page.
- Alternatives named on the page but not run (so no numbers quoted): a larger RADIUS or a velocity estimate for A (Magma); a wider bottleneck or another robot : VQA ratio for C (ChatVLA).

## Mismatch with §9

- §9 names the base as `25fb8f23` / 33600. The actual PR3 base is `5825c94` / 34290. Totals match §9: 34710, M6 3450, M8 3600, catalogue 71.
- H5 "clutter → consistent SoM win": met. "single obvious target → near-tie": the toy declared and got a **tie** (identical) on grounding and success; B's trace ADE is still clearly lower. "shuffled marks consistent lose": met wherever K > 1; with K 1 the shuffle is the identity, so C ties B there by construction. The extra static_jitter regime (declared before the run) shows B clearly losing on success.
- H6 "robot-only consistent VQA collapse vs phased": met in conflict and few_vqa (aligned only a small consistent gap). "A/B near-tie on control": control is an exact tie in every regime. "naive joint may tie or beat B on one metric": did not happen — C never beats B; it ties on control in aligned and few_vqa, loses slightly on control in conflict and loses on VQA everywhere. The aligned near-tie expectation did not hold.
- policy-evaluation had no `<Summary>`. The new section goes before "## Common mistakes" and a whole-lesson `<Summary>` (one recap paragraph plus the one Magma sentence) is added at the end, as batch-14 PR2 did for control-modelling. vla-finetune appends its sentence to the existing `<Summary>`.

## Lock changes

- New `b17p3` block in `tools/check_diagrams.mjs`. It locks:
  - exact source and stdout in the sections, label rules, regime lines, markers, en/zh symmetry and Summary sentences;
  - **every `m±sd` and four-decimal number in the new prose and Summary sentences must be printed by the toy**;
  - resources, both plan headers, this note and README;
  - the declared tie / lose regimes (single_target, static_jitter) and the failed aligned near-tie expectation kept in the toy sources;
  - "no integration step" stated by both toys.
- Tips moved:
  - site total 34290→34710 (two places);
  - month table M6 3240→3450, M8 3390→3600;
  - README `34 290`→`34 710` (en + zh);
  - host tips policy-evaluation 330→540 (obs3 check), vla-finetune 630→840 (b6p3 RPD case and b11p3 continual-ER case).
- The b11p3 month-8 and b16p3 month-6 plan checks no longer require their old "Current" lines; those moved to Batch-17 PR3 and are locked in the new block. Both checks still require their own sections.
- No lock relaxed; `.github/workflows` untouched.

## Models / reproducibility

- opencode free models were tried first, with one prompt asking for both toys (150 s timeout each). deepseek-v4.1-flash-free, glm-5.3-flash-free, mimo-v2.6-flash-free and longcat-2.5-free timed out (exit 124, no files). minimax-m2.5-free exited 1 (server error) with no files. The toys were written locally.
- Reproduce:
  - `python3 examples/month-6/policy-evaluation/magma_som_tom_toy.py`
  - `python3 examples/month-8/vla-finetune/chatvla_phased_alignment_toy.py`
  - `python3 tools/test_b17p3_magma_chatvla_toys.py`
  - `bash examples/month-6/check.sh` and `bash examples/month-8/check.sh`

## Local validation

See the PR description: check_diagrams, check_widgets, check_wokwi, check_quotes, month check.sh, unit tests, lint, typegen, tsc, build + postbuild, and the CI=1 build.
