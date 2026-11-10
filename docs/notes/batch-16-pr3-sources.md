# Batch-16 PR3 sources / 来源记录

Base `b162a86` (main after #166; site **33180**). This PR: M6 vla-models 990→1200 (+210), M6 behaviour-cloning 450→660 (+210); site **33180→33600**; M6 2820→3240; still 71 lessons.

## Opened sources

All fetched with curl on 2026-11-10 (Asia/Shanghai), HTTP 200, then read as text (PDF via `pdftotext -layout`).

| Resource id | URL | Version | Body read | What is used |
|---|---|---|---|---|
| `molmoact-paper` | https://arxiv.org/abs/2508.07917 | abs page: citation_title "MolmoAct: Action Reasoning Models that can Reason in Space", authors Lee, Jason; Duan, Jiafei; Fang, Haoquan; … Fox, Dieter; Krishna, Ranjay (19 authors), citation_date 2025/08/11; PDF v4 (18 Sep 2025); HTML version also fetched | abstract, §2.2–2.4, §5.2, §5.6, Appendix G | depth perception tokens (eqs. 1–2, N = 128 codebook, M = 100 tokens), visual reasoning trace of 1 ≤ L ≤ 5 points (eq. 3), factorisation p(d, τ, a ∣ I, T) (eq. 4), steering by trace editing (eq. 5); Table 2 LIBERO MolmoAct 87.0/95.4/87.6/77.2 (avg 86.6) vs π0-FAST 96.4/96.8/88.6/60.2 (85.5); steerability 0.75 over 15 trials, trace steering beats language steering by 33 %; limitation: the 2-D trace lacks an explicit notion of depth |
| `hamster-paper` | https://arxiv.org/abs/2502.05485 | abs page: citation_title "HAMSTER: Hierarchical Action Models For Open-World Robot Manipulation", authors Li, Yi; Deng, Yuquan; Zhang, Jesse; … Gupta, Abhishek; Goyal, Ankit (12 authors), citation_date 2025/02/08; PDF v4 (10 May 2025); HTML version also fetched | abstract, §1, §4.1, §4.2, §5, Tables 1/2/3/4/7, Appendix E | VLM (VILA-1.5-13B) fine-tuned on 770k RoboPoint / 320k RLBench / 110k Bridge+DROID samples draws a 2-D path p = [(x_t, y_t, gripper_open_t)]; low-level 3-D policy πθ(a ∣ s, o, z, p) (RVT-2 / 3DDA); Table 3 avg 0.46±0.04 vs 0.35±0.04, cam pos 0.39±0.06 vs 0.35±0.11; Table 1 0.36±0.04 vs 0.18±0.10; Table 4 SQA-I 78.0 vs 80.1; Appendix E failure split (trajectory adherence 72 % of RVT failures, 10 % for 3DDA) |

Paper numbers are marked 以论文为准 on the site. No 7B model, VLM, LIBERO, real robot or GPU run (本页未运行). The arXiv abs page does not state a venue; the page makes no venue claim.

## Toy design

- `examples/month-6/vla-models/molmoact_reasoning_trace_toy.py`: kinematic 2-D gripper in a unit square plus a lift height, speed V 0.05, wall (thickness 0.06, height 0.45) checked at 10 sub-points per step with `assert V / SUB < WALL_T` (no integration step). Arms A_direct (kNN from observation to action), B_trace (16-bin depth tokens → ≤ 5-point 2-D trace → kNN step relative to the next waypoint), C_wrong (mirrored trace; in steer regimes the frozen trace to the other bin). Regimes multi_stage_few (5 demos, wall), multi_stage_many (200 demos, wall), single_step (5 demos, no wall), steer_in_plane, steer_depth; 40 test episodes per seed; seeds 0–4; Common random numbers across arms.
- `examples/month-6/behaviour-cloning/hamster_hierarchical_path_toy.py`: kinematic pick-to-target task with a distractor; demos see a background appearance vector (4-D). Arms A_mono (kNN on state + appearance), B_hier (noisy 2-D path from a high level that sees the true goal, low-level kNN on 4-D path-relative features), C_wrong (path to the distractor). Regimes visual_shift (background shift 0.5, 20 demos), matched_easy (in-domain, 200 demos), coarse_path (path sd 0.06), no_appearance (no background features; added after the first run). Seeds 0–4, CRN; per-regime random streams fixed by `STREAM`.
- Labels as in batch-15/16 (tie → numerically zero below 1e-9 → near-tie |m| ≤ sd → consistent, small under 20 % of the smaller arm mean else clear, with sign count).

## Results (k/N = seeds with the reported sign)

MolmoAct (success %, paired):
- multi_stage_few: A 20.5, B 92.5, C 0.0. B−A succ 72.0000±8.5513 clear 5/5; final error −166.6343±67.9518 clear 5/5; C−B −92.5000±3.5355 clear 5/5.
- multi_stage_many (tie/lose regime): A 97.0, B 92.5. B−A succ **−4.5000±4.8088 near-tie** (1/5 opposite); error −2.8577±2.3265 clear 5/5.
- single_step: A 37.0; B−A 58.0000±17.1756 clear 5/5.
- steer_in_plane: A 11.0, B 93.0, C 16.5. B−A 82.0000±8.9093 clear 5/5; C−B −76.5000±4.5415 clear 5/5.
- steer_depth: A 17.0, B 48.0, C 47.5. B−A 31.0000±10.6946 clear 5/5; edited vs frozen trace C−B **−0.5000±1.1180 near-tie** (no seed opposite, 4/5 equal); error −0.0576±0.0686 near-tie.

HAMSTER (success %, paired):
- visual_shift: A 2.0, B 78.5, C 0.5. B−A 76.5000±7.4162 clear 5/5; error −167.4022±29.2251; C−B −78.0000±6.2249 clear 5/5. Path ADE B 2.9518 vs C 7.9150.
- matched_easy: A 33.5, B 96.0. B−A 62.5000±5.3033 clear 5/5; C−B −96.0000±2.8504 clear 5/5.
- coarse_path: A 37.0, B 54.5. B−A 17.5000±15.0000 clear (1/5 opposite); B ADE 7.4559; C−B −54.5000±5.4199 clear 5/5.
- no_appearance (tie/lose regime): A 98.5, B 96.0. B−A **−2.5000±4.3301 near-tie** (no seed opposite, 3/5 equal); error 2.8710±4.3003 near-tie (same sign 5/5); C−B −95.5000±4.1079 clear 5/5.

## Post-hoc choices

- MolmoAct toy: the first run crashed (C_wrong looked up a mirrored bin that only exists in steer regimes); fixed so C uses the mirrored trace outside steer regimes. The kNN was rewritten as an exact early-exit `nearest()`; output checked byte-identical with `cmp` before and after (runtime 57 s → 22 s). Regimes and constants unchanged. Both stated on the pages, with the alternatives not taken (keeping the slower `heapq` search; renaming `single_step`).
- HAMSTER toy: the declared three regimes gave no regime where B ties or loses, so `no_appearance` was added after the first run (marked in the source, stated in en/zh with the alternatives not taken: lowering the background sd in every regime, which would have changed the declared regimes, or keeping only the three declared regimes, which would leave no tie/lose regime). The `STREAM` table keeps the three declared regimes on their first-run random streams, so their numbers did not move. The same exact kNN rewrite was applied (byte-identical, 118 s → 43 s).

## Mismatch with §9

- MolmoAct single_step: §9 expected a near-tie; it is a clear B win 5/5 (with 5 demos the direct kNN generalises poorly even without a wall). Reported as is.
- MolmoAct tie/lose regime: multi_stage_many (success near-tie, B nominally lower); steer_depth adds a second near-tie (editing the 2-D trace cannot choose along depth, matching the paper's stated limitation).
- HAMSTER matched_easy: §9 expected a near-tie; it is a clear B win 5/5 (A's background features are nuisance dimensions even in domain).
- HAMSTER coarse_path: §9 expected a B loss; B stays ahead (17.5±15.0, 1/5 opposite). The tie regime is the post-hoc no_appearance.

## Lock changes

- New `b16p3` block in `tools/check_diagrams.mjs` (exact source/stdout in sections, label rules, regime lines, markers, en/zh symmetry, Summary sentences, resources, plan header, sources note, README, post-hoc no_appearance marked in source and STREAM table present).
- Tips moved: site total 33180→33600; month table M6 2820→3240; README `33 180`→`33 600` (en + zh); host-minute tips vla-models 990→1200 (wm2, b13 dual-system, b14 RDT2, b14p3 CoT-VLA cases) and behaviour-cloning 450→660 (VQ-BeT case). The old b14p3 month-6 plan check no longer requires the "Current" header line (it moved to Batch-16 PR3, locked in the new block); it still requires its `## Batch-14 PR3` section.
- No lock relaxed; `.github/workflows` untouched.

## Models / reproducibility

- opencode free models were tried first with one prompt asking for both toys: deepseek-v4.1-flash-free, glm-5.3-flash-free, mimo-v2.6-flash-free and longcat-2.5-free timed out (exit 124, no files); minimax-m2.5-free exited 1 ("Unexpected server error"). Both toys were written locally.
- Reproduce: `python3 examples/month-6/vla-models/molmoact_reasoning_trace_toy.py`, `python3 examples/month-6/behaviour-cloning/hamster_hierarchical_path_toy.py`, `python3 tools/test_b16p3_molmoact_hamster_toys.py`, `bash examples/month-6/check.sh`.

## Local validation

See the PR description for the command list and results (check_diagrams, check_widgets, check_wokwi, check_quotes, month check.sh, unit tests, lint, typegen, tsc, build + postbuild, CI=1 build).
