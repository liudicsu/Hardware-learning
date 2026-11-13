# Batch-22 PR3 sources — PointVLA, EgoVLA

Base: `0193f7837fcf135a369a678d1abac948651bda88` (batch-22 PR2 #190 merged; site **39780**, M7 **3330**, M11 **3810**).
This PR: site **39780→40140** (40140=39780+180+180), M7 **3330→3510**, M11 **3810→3990**, catalogue still **71**. Hosts: `depth-pointcloud` 630→810, `umi-style-collection` 420→600. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All returned HTTP **200** (2026-11-13 UTC+8): abstract page, HTML and PDF for each paper.

| id | URL | version | What was used |
|---|---|---|---|
| pointvla-paper | https://arxiv.org/abs/2503.07511 | v1 (CC BY 4.0) | *PointVLA: Injecting the 3D World into Vision-Language-Action Models*; 6 authors in abs-page order: Chengmeng Li, Junjie Wen, Yan Peng, Yaxin Peng, Feifei Feng, Yichen Zhu. Builds on DexVLA (Qwen2-VL 2B plus a 1B ScaleDP action expert with 32 blocks); the vanilla action expert is frozen and point-cloud features enter through a small adapter per selected block and are added, not mixed into the language model; a skip-block analysis on shirt folding finds the first 11 blocks critical and later blocks skippable, and five later blocks receive the injection; a 3 mm training foam versus 52 mm at test where the 2D baselines grasp at the trained height; a photo of an object on a screen where 2D baselines keep trying to grasp; RealSense L515 for the cloud (以论文为准). |
| egovla-paper | https://arxiv.org/abs/2507.12440 | v3 (CC BY 4.0) | *EgoVLA: Learning Vision-Language-Action Models from Egocentric Human Videos*; 15 authors in arXiv order: Ruihan Yang, Qinxi Yu, Yecheng Wu, Rui Yan, Borui Li, An-Chieh Cheng, Xueyan Zou, Yunhao Fang, Xuxin Cheng, Ri-Zhao Qiu, Hongxu Yin, Sifei Liu, Song Han, Yao Lu, Xiaolong Wang. NVILA-2B base; about 500,000 image-action pairs from HOI4D, HOT3D, HoloAssist and TACO; action space wrist pose plus 15 MANO PCA components; IK for the arm and an MLP retarget for the hand; Isaac Lab humanoid benchmark (Unitree H1 with Inspire hands, 12 tasks); zero-shot without robot post-training 0 % on all tasks; about 20 % higher long-horizon success than NoPretrain; 50 % of robot data drops long-horizon success from 45.93 % to 7.41 % (以论文为准). |

Not cited: no DexVLA, ScaleDP, NVILA, MANO, Isaac Lab or RealSense documentation was opened, so every block importance, noise level, height, threshold, offset, prior error and regularisation weight in the toys is a **declared toy parameter**, printed or stated as declared. The PointVLA skip-block profile used in the toy is a declared stand-in, not the paper's measurement.

## Toys

- `examples/month-7/depth-pointcloud/pointvla_frozen_injector_toy.py` → `examples/month-7/expected/pointvla_frozen_injector_toy.txt`
- `examples/month-11/umi-style-collection/egovla_human_pretrain_retarget_toy.py` → `examples/month-11/expected/egovla_human_pretrain_retarget_toy.txt`

Common random numbers, five seeds, stdlib CPU only, half-up rounding on the shortest decimal repr, byte-identical output on rerun. No integration step in either toy. Every number in the new lesson prose, the new Summary sentences, the month-7 / month-11 plans and this note that carries an m±sd form is printed by the toys into `expected/`; hand calculations are printed by the toys.

## Regime results

### H5 PointVLA (`pointvla_frozen_injector_toy.txt`)

- Declared toy parameters: W_BLOCK 0.30 → 0.06 over 8 blocks, ETA 0.5, SIG_GRIP 0.04, GRIP_THR 0.90, late block 6, early block 0, table 3 mm (train) / 52 mm (shift), RGB_CUE 0.1, 32 cloud points with 4 mm noise, presence 20 mm, tolerance 10 mm, 40 scenes, 30 % outliers.
- Hand calc (printed): 0.0441 m height error, 0.0007 m cloud-mean sd, closing probability 0.9938 / 0.9599 / 0.1056.
- train_height: B−A success -0.0300±0.0326, near-tie; B−A height_err_mm -1.8022±0.4029, clear; C−B success -0.7900±0.0783, clear, 5/5, **kept**.
- height_shift: A success 0.0000±0.0000; B−A success 0.9750±0.0177, clear, 5/5; C−B success -0.8650±0.0548, clear.
- real_vs_photo: B−A success 0.4000±0.1000, clear; B−A false_grasp -1.0000±0.0000 (A cannot refuse by construction); C−A success -0.0800±0.1605, near-tie.
- corrupted_cloud: B−A success -0.3050±0.0925, clear, 5/5 — B loses (declared possible), **kept**.
- Alternatives (same seeds, written before the first run, not adopted): block 3 → X−B success -0.0250±0.0177, small; median cloud → B_median−A success -0.0300±0.0326, near-tie; TOL 20 mm → B−A success -0.0300±0.0326; RGB_CUE 0.3 → B−A success 0.9750±0.0177.

### H6 EgoVLA (`egovla_human_pretrain_retarget_toy.txt`)

- Declared toy parameters: D 16, P 17, B_ROBOT 1.0, OFFSET_MISMATCH 1.5, SIG_DEMO 0.5, 32 / 16 demos, TOL 0.5, LAM 0.25 (A) / 25 (B), 4 tasks, 25 short and 25 long rollouts, long = 4 subtasks, prior error 0.1 / 0.5.
- Hand calc (printed): 0.5510, 0.4000, 0.6358 / 0.1635, 0.7887 / 0.3869, offset 3.0000× tolerance, posterior sd 0.0880 / 0.0662 / 0.0781.
- in_domain_full: C−A short_sr -0.6320±0.0746, clear, 5/5; C−B long_sr -0.6660±0.0773, clear; B−A long_sr 0.4300±0.1430, clear, 5/5; B−A short_sr 0.2220±0.0968, clear.
- half_data: B−A long_sr 0.4900±0.0775, clear; B−A short_sr 0.5640±0.0590, clear; half-data B minus full-data B long_sr -0.1620±0.0841, clear, 5/5; short_sr -0.0600±0.0742, near-tie.
- large_mismatch: B−A short_sr -0.3100±0.1286 and B−A long_sr -0.2180±0.0955, clear, 5/5, **kept**; C−B long_sr -0.0160±0.0219, near-tie.
- Alternatives (same seeds, written before the first run, not adopted): LAM_B 5 → B−A long_sr -0.1180±0.1085; TOL 0.7 → B−A long_sr 0.4140±0.1724; OFFSET_MISMATCH 0.5 → C short_sr 0.4600±0.0394, C−A long_sr -0.1860±0.0713.

## Post-hoc choices

PointVLA: none; every parameter, regime and printed alternative was written before the first run. EgoVLA: none beyond the solver correctness fix below; no parameter, regime, arm or rule changed.

## Code changes after the first run

- PointVLA: the first run printed the hand-calculation lines and stopped with a data-structure error before any regime result; per-arm results were changed from tuples to named fields. No parameter changed. The corrected output is byte-identical to `expected/`.
- EgoVLA: (1) the first run stopped at a syntax error before printing anything; f-strings were split into plain variables. (2) The second run printed every regime; a check afterwards found that the ridge solver filled the intercept column of the normal equations but not its symmetric row, so the fit did not solve the declared objective (noise-free data missed θ and b by more than 0.5; after the fix, about 1e-7). The row was added. This changed results: in the buggy run the half-data drop of B on long_sr was a near-tie (the declaration did not hold there) and the B−A gaps were smaller. The corrected output is the one kept and is byte-identical to `expected/`. (3) One docstring paragraph was rewrapped, with no output change. All three are disclosed on the lesson pages.

## Mismatch with §9

- No declared regime failed in the kept outputs. EgoVLA in_domain_full short_sr came out as the consistent-win branch of the declaration (B−A short_sr 0.2220±0.0968), not the near-tie branch.
- EgoVLA half_data: the declaration held only after the solver fix above; in the buggy run it was a near-tie.
- Not pre-declared and reported on the page: PointVLA C−A success on height_shift 0.1100±0.0548 (early injection still beats the 2D head there); real_vs_photo C−A success -0.0800±0.1605, near-tie.

DexVLA / GPU / RealSense / robot, EgoVLA model / MANO / Isaac Lab / humanoid: 本页未运行.

## Lock changes

Tipped site-total, host-minute and Current-header locks only. New lock block added (toys, expected, CRN, label order, difference directions, cited paper decimals, sources, plans, README, no process labels in the new toys and outputs, rejecting polish and 来源笔记) plus `tools/test_b22p3_pointvla_egovla_toys.py`.

- README `/39 780/` and `约 39 780 分钟` → `/40 140/` and `约 40 140 分钟`.
- Curriculum sum checks `39780` → `40140`; month-total lists M7 3330→3510, M11 3810→3990.
- Host-minute locks for `depth-pointcloud` (630→810) and `umi-style-collection` (420→600) in earlier cases.
- month-7 / month-11 plan Current header locks → Batch-22 PR3 (**M7 3510**, **M11 3990**); historical section markers kept.
- Labels of moved tip locks now name the live total.

No lock relaxed.
