# Batch-20 PR3 sources — InternVLA-A1 foresight, GraspVLA synthetic pre-training

Base: `38f5083ba5eaf0de84cc822c6eb698b277596d73` (batch-20 PR2 #182 merged; site **37560**, M7 **3120**, M9 **3900**).
This PR: site **37560→37980** (37980=37560+210+210), M9 **3900→4110**, M7 **3120→3330**, catalogue still **71**. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All returned HTTP **200** (this run, 2026-11-12 UTC+8). PDFs were read with `pdftotext -layout`.

| id | URL | version | What was used |
|---|---|---|---|
| internvla-a1-pdf (abs) | https://arxiv.org/abs/2601.02456 | v2 (v1 submitted 5 Jan 2026) | Title **InternVLA-A1: Unifying Understanding, Generation and Action for Robotic Manipulation**; **42 authors** in arXiv order (checked against the `citation_author` meta and the author line; the PDF byline reads InternVLA-A1 Team): Junhao Cai, Zetao Cai, Jiafei Cao, Yilun Chen, Zeyu He, Lei Jiang, Hang Li, Hengjie Li, Yang Li, Yufei Liu, Yanan Lu, Qi Lv, Haoxiang Ma, Jiangmiao Pang, Yu Qiao, Zherui Qiu, Yanqing Shen, Xu Shi, Yang Tian, Bolun Wang, Hanqing Wang, Jiaheng Wang, Tai Wang, Xueyuan Wei, Chao Wu, Yiman Xie, Boyang Xing, Yuqiang Yang, Yuyin Yang, Qiaojun Yu, Feng Yuan, Jia Zeng, Jingjing Zhang, Shenghan Zhang, Shi Zhang, Zhuoma Zhaxi, Bowen Zhou, Yuanzhen Zhou, Yunsong Zhou, Hongrui Zhu, Yangkun Zhu, Yuchen Zhu. |
| internvla-a1-pdf | https://arxiv.org/pdf/2601.02456.pdf | v2, 13 Feb 2026 | Abstract and §1: MLLM-based VLAs lack physical dynamics; video-prediction world models lack semantic grounding and are brittle to prediction errors. §3.1–3.2: Mixture-of-Transformers with three experts (understanding, generation, action); generation expert takes current and historical (t−15) frames from three views, COSMOS CI8×8 VAE latents compressed to 16 tokens per image, one parallel decode of the t+15 frame; blockwise mask understanding → generation → action. §3.3: generation loss on the future latent, flow-matching action loss, λ = 0.01. §3.4 / Table 1: 2B (InternVL3) and 3B (Qwen3-VL), about 13 Hz on one RTX 4090. §4: pre-training mixture over 692M frames (InternData-A1, RoboTwin, AgiBot-World, RoboMind, EgoDex). §5: +4.4 % static, +2.6 % RoboTwin 2.0, +26.7 % dynamic vs π0.5; without the generation expert the average falls from 77.0 % to 57.6 %. §6: limitations (understanding expert not co-trained on VQA; low-fidelity foresight frames). All 以论文为准, not reproduced. |
| graspvla-pdf (abs) | https://arxiv.org/abs/2505.03233 | v3 (v1 submitted 6 May 2025) | Title **GraspVLA: a Grasping Foundation Model Pre-trained on Billion-scale Synthetic Action Data**; **13 authors** in arXiv order (checked against `citation_author` and the PDF author line): Shengliang Deng, Mi Yan, Songlin Wei, Haixin Ma, Yuxin Yang, Jiayi Chen, Zhiqi Zhang, Taoyu Yang, Xuheng Zhang, Wenhao Zhang, Heming Cui, Zhizheng Zhang, He Wang. |
| graspvla-pdf | https://arxiv.org/pdf/2505.03233.pdf | v3, 27 Aug 2025 | Abstract and §1: VLA pre-trained entirely on synthetic action data; SynGrasp-1B billion-frame set with photorealistic rendering and extensive domain randomisation; Progressive Action Generation (PAG) as a chain of thought. §3: Objaverse LVIS subset, 240 categories, 10,680 meshes; antipodal grasp synthesis, CuRobo planning, MuJoCo validation; Isaac Sim ray-traced rendering with randomised lighting, backgrounds and cameras. §4: InternLM2 1.8B VLM, DINO-v2 + SigLIP encoder, flow-matching action expert; PAG predicts 2-D boxes for Internet (GRIT) and synthetic data, then grasp pose and action chunk for synthetic data only. §5: zero-shot real-world and LIBERO tables, AnyGrasp comparison, scaling, few-shot post-training, PAG ablation. §7: grasp labels from force closure, no deformables; about 200 ms latency. All 以论文为准, not reproduced. |

In-repo `src/content/m9/world-models-overview` (DreamGen, MemoryVLA bank, WorldVLA mask) and `src/content/m7/perception-to-grasp` (hand-eye, mask pipe, antipodal force closure / ε) were re-read on the base; no existing section was changed. The InternVLA-M1 section in `src/content/m6/vla-models` was re-read to keep A1 distinct from it.

No robot, gripper or camera datasheet was opened, so no hardware figure is quoted. Every toy length, speed, noise level, probability, appearance gain / offset, count and tolerance is a **declared toy parameter**, printed.

## Toys

- `examples/month-9/world-models-overview/internvla_a1_mot_foresight_toy.py` → `examples/month-9/expected/internvla_a1_mot_foresight_toy.txt`
- `examples/month-7/perception-to-grasp/graspvla_syngrasp_pretrain_toy.py` → `examples/month-7/expected/graspvla_syngrasp_pretrain_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only, byte-identical output on rerun. No integration step (closed-form positions in H5; no dynamics in H6). Printed numbers use half-up rounding on the shortest decimal repr (`decimal.ROUND_HALF_UP`). Every number in the new lesson prose, the new Summary sentences, the curriculum objectives and tasks, the month-7 / month-9 plans and this note that carries an m±sd form is printed by the toys into `expected/`; hand calculations are labelled as such and printed.

## Regime results

### H5 InternVLA-A1 (`internvla_a1_mot_foresight_toy.txt`; first accepted run = first run)

- Declared toy parameters: 50 scenes per (regime, seed), H=0.5 s, V=10.0–30.0 cm/s (random sign), SIGMA_LO=0.3 cm, SIGMA_HI=1.2 cm, P_CORRUPT=0.3, CORRUPT_CM=6.0 cm, TOL=2.0 cm (strict).
- Hand calc (printed): travel during H 5.0000–15.0000 cm, never below TOL; extrapolation noise sd √5·σ = 0.6708 cm / 2.6833 cm.
- static: paired B−A success -0.0040±0.0089, near-tie (4 of 5 equal) — pre-declared near-tie held; paired B−A aim_err 0.2848±0.0321, clear, 5/5 (foresight costs precision); paired C−B success -0.3400±0.0949, clear, 5/5, **kept**.
- dynamic: paired B−A aim_err -9.0519±0.3205 and paired B−A success 0.9920±0.0110, clear, 5/5 — pre-declared foresight win held; paired C−B success -0.3120±0.0576, clear, 5/5, **kept**; paired C−A success 0.6800±0.0490, clear, 5/5.
- static_noisy: paired B−A success -0.3720±0.0729 and paired B−A aim_err 1.3198±0.1251, clear, 5/5 — pre-declared possible loss happened, **kept**; paired C−B success -0.1080±0.0522, clear, 5/5.
- Alternatives (same seeds, written before the first run, not adopted): TOL=3.0 cm — dynamic paired B−A success@alt 1.0000±0.0000; static_noisy paired B−A success@alt -0.2960±0.0410, clear; P_CORRUPT=0.1 on dynamic — paired C−B success@alt -0.1080±0.0642, small but consistent, 5/5.

### H6 GraspVLA (`graspvla_syngrasp_pretrain_toy.txt`; first run kept for every number, one printed sentence changed)

- Declared toy parameters: DIM=8, S_CAT=6 synthetic + W_CAT=4 web categories, N_PER=30, N_OBJ=3, N_SCENES=60, INST_SIGMA=0.15, PIX_SIGMA=0.05, DR gain 0.4–1.6 / offset −0.5–0.5, web gain 0.5–1.5 / offset −0.4–0.4, real gain 0.60 / offset 0.35, ORI_SIGMA=5.0 deg, ORI_TOL=10.0 deg (strict). Domain check printed: real domain inside the wide DR range True; canonical False; narrow range False.
- Hand calc (printed): chance pick 1/3 = 0.3333 (1/5 = 0.2000); grasp ceiling erf(10.0/(5.0·√2)) = 0.9545.
- in_family: paired B−A success 0.5400±0.1217 and paired B−A pick_ok 0.5700±0.1083, clear, 5/5 — pre-declared win held; paired D−B success -0.6467±0.1114, clear, 5/5, **kept**; paired C−B success 0.0233±0.0630, near-tie — **the canonical no-DR arm did not lose; the expected DR benefit did not appear**, printed as it came out, not retuned.
- web_category: paired B−A success 0.5667±0.1074, clear, 5/5; paired C−B success tie on every seed (pre-declared possible); paired D−B success -0.5200±0.1114, clear, 5/5.
- single_object: every paired line tie, identical on every seed (pre-declared near-tie or tie); all arms 0.9467±0.0398.
- Alternatives (same seeds, written before the first run, not adopted): narrow DR (gain 0.9–1.1, offset −0.1–0.1) — B@alt 0.9067±0.0585 against 0.8700±0.0853, paired Bwide−Bnarrow success -0.0367±0.0492, near-tie; paired Bnarrow−C success 0.0133±0.0247, near-tie. N_OBJ=5 — paired B−A success@alt 0.6333±0.1054, clear; paired D−B success@alt -0.7800±0.1293; paired C−B success@alt 0.0033±0.0861, near-tie.

## Post-hoc choices

None for parameters, regimes or alternatives in either toy: every value and both alternatives per toy were written before the first run.

**Code changes after the first run:** H5 none (the first run is the `expected/` file). H6 one, to a printed sentence only: the closing `No winner declared` line first read "... needs DR on the synthetic side, and is useless with shuffled labels"; after the first run showed C near-tying (in_family) and tying (web_category) B, it was changed to "... is useless with shuffled labels; here the canonical no-DR arm did not lose". No parameter, regime or number changed; the change is recorded in the toy docstring and disclosed on both lesson pages (en/zh).

## Mismatch with §9

- H5: matches §9 (dynamic consistent foresight win; static near-tie on success; corrupted foresight consistent lose, kept). Added a pre-declared static_noisy regime where B loses (kept); static aim error is a clear B loss even where success near-ties, reported plainly.
- H6: in-family consistent semantic win and single-object tie match §9; shuffled labels lose (kept). **No-DR did not lose** (§9 allowed "no-DR / shuffle kept if they lose"; no-DR did not, which the lesson states plainly with an untested likely reason). Paper % only as 以论文为准.

No other mismatch: CRN, ≥5 seeds, no integration step stated, no unprinted side-run numbers, en/zh synced, full author names in arXiv order on both lesson pages and in `resources.ts`, difference directions in prose / Summary / curriculum / plans / this note match the printed `paired` lines (locked).

GPU training, weights, RoboTwin, SynGrasp-1B, Isaac Sim, LIBERO, real robots and grasp cells: 本页未运行.

## opencode

Tried free models in order DeepSeek (`opencode/deepseek-v4.1-flash-free`), GLM (`opencode/glm-5.3-flash-free`), MiMo (`opencode/mimo-v2.6-flash-free`), LongCat (`opencode/longcat-2.5-free`), MiniMax (`opencode/minimax-m3.1-flash-free`), 90 s each, in the background while the toys were drafted locally. All five timed out (exit 124) with no file written. Implementation is local.

## Lock changes

Tipped site-total, host-minute and Current-header locks only; no lock relaxed. New batch-20 PR3 block added (toys, expected, CRN, label order, strict TOL, half-up rounding, domain check, author lists, difference directions, sources, plans, README) plus `tools/test_b20p3_internvla_graspvla_toys.py`.

No lock relaxed.
