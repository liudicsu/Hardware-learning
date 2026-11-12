# Batch-19 PR3 sources — InternVLA-M1 where-then-how, NORA small VLA with FAST+

Base: `61bb8f769f2d87901bfe1d504ffc25b4fe4d947e` (batch-19 PR2 #178 merged; site **36480**, M6 **3450**, M8 **3600**).
This PR: site **36480→36900**, M6 **3450→3660**, M8 **3600→3810**, catalogue still **71**. vla-models 1200→1410 (M6, 6.3), async-deployment 300→510 (M8, 8.3). Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All six returned HTTP **200** (this run, 2026-11-12 UTC+8).

| id | URL | What was checked / used |
|---|---|---|
| internvla-m1 abs | https://arxiv.org/abs/2510.13778 | `citation_title` "InternVLA-M1: A Spatially Guided Vision-Language-Action Framework for Generalist Robot Policy"; **29 authors** (counted `citation_author` tags): Xinyi Chen, Yilun Chen, Yanwei Fu, Ning Gao, Jiaya Jia, Weiyang Jin, Hao Li, Yao Mu, Jiangmiao Pang, Yu Qiao, Yang Tian, Bin Wang, Bolun Wang, Fangjing Wang, Hanqing Wang, Tai Wang, Ziqin Wang, Xueyuan Wei, Chao Wu, Shuai Yang, Jinhui Ye, Junqiu Yu, Jia Zeng, Jingjing Zhang, Jinyu Zhang, Shi Zhang, Feng Zheng, Bowen Zhou, Yangkun Zhu. v1, submitted 15 Oct 2025. |
| internvla-m1-html | https://arxiv.org/html/2510.13778 | HTML body fetched (2.3M, two-stage recipe present). |
| internvla-m1-pdf | https://arxiv.org/pdf/2510.13778.pdf | v1 PDF body read via pdftotext: abstract; §1 (over 3M multimodal items incl. 2.3M spatial grounding); §2.1 dual system (Qwen2.5-VL-3B-instruct System 2, diffusion-policy action expert on DINOv2, about 4.1B params, querying transformer, gradient decay e.g. 0.5); §2.2 Stage 1 spatial grounding pre-training (VLM only; box / point / trajectory QA) and Stage 2 spatially guided action post-training (spatial prompting: a cue prepended to the instruction, the VLM does not explicitly answer it; co-training with grounding data); §3.1; §4.1.1 setup (action chunk 16); Fig. 5 / Table 3 ablation captions; §6. |
| nora abs | https://arxiv.org/abs/2504.19854 | `citation_title` "NORA: A Small Open-Sourced Generalist Vision Language Action Model for Embodied Tasks"; **8 authors**: Chia-Yu Hung, Qi Sun, Pengfei Hong, Amir Zadeh, Chuan Li, U-Xuan Tan, Navonil Majumder, Soujanya Poria. v1, submitted 28 Apr 2025. |
| nora-html | https://arxiv.org/html/2504.19854 | HTML body fetched (FAST+ present). |
| nora-pdf | https://arxiv.org/pdf/2504.19854.pdf | v1 PDF body read via pdftotext: abstract (3B, Qwen-2.5-VL-3B, 970k real-world demonstrations, FAST+); §2.3 action tokenization (DCT then BPE as the paper words it; about 8.3GB GPU memory at inference); §3 / §3.1 (eqs. 1–2, 2048 added FAST+ tokens, single frame, chunk size 1); §3.2 pre-training (OXE, about three weeks on one 8×H100 node); §3.3 NORA-Long (chunk 5); §4.1–4.4 (WidowX tasks, Table 2 LIBERO, distractors, chunking crashes on WidowX). |

Paper numbers quoted on the pages are 以论文为准: InternVLA-M1 +14.6 % / +17 % / +4.3 % vs its no-spatial-guidance variant, 6.2 %, +7.3 %, +20.6 %, 2.3M, over 3M, 4.1B; NORA 3B, 970k, 2048, 8.3GB, LIBERO averages 87.9 / 73.9 / 76.5 and LIBERO-Long 45 / 53.7. None of them is a toy output. NORA's §2.3 words its DCT as running across the action dimensions at each timestep; the toy uses the time-axis DCT of the existing FAST section in vla-models (a stand-in, stated on the page). No InternVLA-M1 or NORA weights, no SimplerEnv / LIBERO / WidowX, no GPU.

## Toys

- `examples/month-6/vla-models/internvla_m1_spatial_prompt_toy.py` → `examples/month-6/expected/internvla_m1_spatial_prompt_toy.txt`
- `examples/month-8/async-deployment/nora_fastplus_small_vla_toy.py` → `examples/month-8/expected/nora_fastplus_small_vla_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only, byte-identical output on rerun. No integration step (one reach per episode / chunks scored, not simulated). Every number in the new lesson prose, the new Summary sentences, the curriculum objectives and tasks, the month-6 / month-8 plans and this note that carries an m±sd form or two or more decimals is printed by the toys into `expected/`; hand calculations are labelled and printed.

## Regime results (first accepted run = first run)

### H5 InternVLA-M1 (`internvla_m1_spatial_prompt_toy.txt`)

- Hand calc (printed): TOL / SIGMA_EXEC = 2.5000; P(reach inside TOL) = 95.6063 %; chance among 8 objects 12.5000 %; success strict (0.0500 fails, 0.0499 succeeds).
- cluttered (K=8, N_DEMO=40): paired B−A success_pct 14.6000±7.3263, small but consistent, 5/5; paired B−A where_pct 15.8000±8.4009; paired C−B success_pct -94.2000±1.7176, clear, 5/5. The 14.6000 equals the paper's +14.6 % by coincidence; it is not a reproduction.
- single_object (K=1): paired B−A success_pct tie: identical on every seed; paired C−B success_pct -94.9000±2.0433, clear, 5/5.
- many_demos (N_DEMO=400): paired B−A success_pct tie: identical on every seed (pre-declared "may near-tie"); paired C−B success_pct -94.5000±2.0000, clear, 5/5.
- camera_shift (colour words 0 and 1 swapped in the grounding corpus): paired B−A success_pct -23.8000±4.4385, clear, 5/5 — B **loses**, kept; paired B−A where_pct -24.8000±4.4244; paired C−B success_pct -70.4000±3.9592, clear, 5/5.

### H6 NORA (`nora_fastplus_small_vla_toy.txt`)

- Hand calc (printed): per-step tokens 7*10 = 70 and 7*30 = 210; bin width 0.007812, half a bin 0.003906; rounding RMS 0.028868; P_SMALL / P_LARGE = 0.4286; success strict (0.0600 fails, 0.0599 succeeds).
- short_in_dist (H=10, SIG 0.030 both): paired B−A success_pct tie: identical on every seed (pre-declared "may near-tie"); paired B−A tokens -39.7370±0.2105, clear, 5/5; paired B−A cost -399.2110±0.6314, clear, 5/5; paired C−B success_pct -100.0000±0.0000, clear, 5/5.
- long_horizon (H=30, SIG_LARGE 0.040, SIG_SMALL 0.055): paired B−A success_pct -72.9000±1.7819, clear, 5/5 — the small model **loses**, kept; paired B−A tokens -114.7840±0.7102; paired B−A cost -1184.3520±2.1307; paired C−B success_pct -27.1000±1.7819, clear, 5/5.

## Post-hoc choices

None for parameters or regimes: the four InternVLA regimes, G_ITEMS = 600, TOL, SIGMA_EXEC, the colour swap, the two NORA regimes, all SIG values, GAMMA = 10.0, TOL, P_LARGE / P_SMALL, and both alternatives were written before the first run. Alternatives printed on the same seeds as a pre-planned sensitivity and not adopted: G_ITEMS = 60 (paired B−A success_pct@alt 12.1000±7.0480 on cluttered, -21.1000±3.6125 on camera_shift; B knows 28.8000±1.3038 pairs on cluttered) and GAMMA = 20.0 (short_in_dist success tie, paired B−A cost@alt -353.5390±0.7962, tokens 45.4870±0.2654; long_horizon B success 89.8000±2.1966 %, paired B−A success_pct@alt -10.2000±2.1966, small but consistent, 5/5, tokens 147.0000±0.5566, paired B−A cost@alt -1029.0000±1.6697).

Code changes after the first run, none of which changed a number: (1) the NORA toy caches its DCT cosine table and its per-(regime, GAMMA) result tables to cut runtime from about 12 s to about 4 s, with **byte-identical output** (checked with `cmp`); (2) the first printed line of each toy now names its arXiv id (2510.13778 / 2504.19854) so the id quoted on the page is printed; every other line of `expected/` is unchanged (checked line by line).

## Mismatch with §9

- H5: §9 asks for a consistent spatial win in clutter — it came out as a **small but consistent** gap (5/5), because |m| is under 20 % of A's mean; the shuffled prompt loses consistently in every regime. The near-tie cells (single object, many demonstrations) came out as exact ties and are printed as ties. The extra camera_shift regime (B loses) was pre-declared in the toy docstring and kept.
- H6: §9 asks for a consistent small-model win on size / latency (cost proxy: clear, 5/5 in both regimes), a consistent shuffled-codebook loss (clear, 5/5 in both regimes) and to keep a success loss against the large head — it happened in long_horizon (paired B−A success_pct -72.9000±1.7819) and is kept. Success on short_in_dist is a tie rather than a near-tie.

No other mismatch: CRN, ≥5 seeds, no integration step stated, no unprinted side-run numbers, en/zh synced, difference directions in prose / Summary / curriculum / plans / this note match the printed `paired` lines (locked).

InternVLA-M1 / NORA weights, SimplerEnv, LIBERO, WidowX, real robots and GPU: 本页未运行.

## opencode

Tried free models in order DeepSeek (`opencode/deepseek-v4.1-flash-free`), GLM (`opencode/glm-5.3-flash-free`), MiMo (`opencode/mimo-v2.6-flash-free`), LongCat (`opencode/longcat-2.5-free`), MiniMax (`opencode/minimax-m3.1-flash-free`), each with a 90 s timeout. All five timed out (exit 124) with no file written. Implementation is local.

## Lock changes

Tipped site-total, month-total, host-minute and Current-header locks only; no lock relaxed. New batch-19 PR3 block added (toys, expected, CRN, label order, strict boundaries, printed numbers, difference directions, sources, plans, README).

- README `/36 480/` and `约 36 480 分钟` → `/36 900/` and `约 36 900 分钟` (including earlier “unchanged” tips).
- Curriculum sum checks `36480` → `36900`; `current curriculum` month totals M6 3450→3660 and M8 3600→3810; tip-lock comments renamed “(tip after batch-19 PR3)”.
- `vla-models` host minutes in earlier cases `1200` → `1410`; `async-deployment` host minutes `300` → `510`.
- month-6 and month-8 plan Current header locks (were Batch-17 PR3, **M6 3450** / **M8 3600**) → Batch-19 PR3, **M6 3660** / **M8 3810**; historical `## Batch-17 PR3` markers kept.

No lock relaxed.
