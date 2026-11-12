# Month 6 plan: Robot learning, specialisation & getting hired

Current / 当前：**M6 3660 min**, Batch-19 PR3. Earlier entries below retain their historical totals.

## Batch-19 PR3 / 本月 H5 (+210)

Base `61bb8f769f2d87901bfe1d504ffc25b4fe4d947e` (batch-19 PR2 #178 merged; site **36480**). PR3 touches M6 and M8: **M6 3450→3660 (+210)**, M8 3600→3810 (+210). Site **36480→36900**, still 71 lessons.

- **H5 / 6.3 vla-models: 1200→1410 (+210).** InternVLA-M1 (arXiv 2510.13778, 29 authors checked on the abs page; PDF body read, HTML fetched) spatially guided where-then-how: a direct head without grounding (A) vs a grounding stage trained on a toy grounding corpus, then the same reach (B) vs a shuffled spatial prompt (C) (`internvla_m1_spatial_prompt_toy.py`; common random numbers, 5 seeds, 200 test scenes per seed; G_ITEMS=600 is a toy count, not the paper's 2.3M). cluttered: paired B−A success_pct `14.6000±7.3263`, **small but consistent**, 5/5 (equal to the paper's +14.6 % by coincidence, not a reproduction). single_object and many_demos: paired B−A success_pct **tie: identical on every seed** (many_demos was pre-declared "may near-tie"). camera_shift: paired B−A success_pct `-23.8000±4.4385`, **clear**, 5/5 — B **loses**, **kept**. Shuffled prompt: paired C−B success_pct `-94.2000±1.7176` (cluttered), **clear**, 5/5. Alternative G_ITEMS=60 printed on the same seeds (paired B−A success_pct@alt `12.1000±7.0480` cluttered, `-21.1000±3.6125` camera_shift); no post-hoc retune. ≠ SpatialVLA / Magma / HAMSTER / MolmoAct. Paper numbers 以论文为准; weights / SimplerEnv / GPU 本页未运行. / InternVLA-M1 先定位再动作，论文数字以论文为准。

**Allocation / 安排:** 40+30+60+40+40 = 210 minutes.

**Site accounting / 全站核算:** **36900=36480+420**; **M6=3660**, **M8=3810**, **71 lessons**.

## Batch-17 PR3 — Magma Set-of-Mark / Trace-of-Mark on policy-evaluation (+210)

Base `5825c94` (batch-17 PR2 merged as #170; site **34290**). PR3 touches M6 and M8: **M6 3240→3450 (+210)**, M8 3390→3600 (+210). Site **34290→34710**, still 71 lessons.

- **H5 / policy-evaluation: 330→**540** (+210).** Set-of-Mark + Trace-of-Mark vs a direct point vs shuffled marks. Toy `magma_som_tom_toy.py`: K candidates in [0, 1]², shared scores (target SIGNAL 3.0 + N(0, 1)), A softmax-weighted point + SIG_REG 0.01, B argmax mark quantised to 256 bins + trace with tracked velocity, C permuted labels; 400 scenes × 5 seeds, common random numbers; no integration step. cluttered: B−A grounding +70.6000±1.9653 and success +82.1000±0.6982, clear, 5/5; C−B grounding −78.7500±1.2119. single_target: B−A grounding and success tie (identical on every seed); C = B (identity permutation). static_jitter (declared tie/lose): B−A success −62.1500±1.2324, clear, 5/5. ≠ HAMSTER / MolmoAct / TraceVLA / ThinkAct. Magma numbers 以论文为准; GPU / UI / robot 本页未运行.

**Allocation / 安排:** 30+30+40+40+40+30 = 210 minutes.

Course source: @DeRonin_'s 6-month roadmap (`COURSE_SOURCE` in src/lib/curriculum.ts). Month 6 topics there:
imitation learning (behaviour cloning, ACT, diffusion policy), VLA models and which have open weights,
choosing a specialisation, portfolio and job applications. Milestones are already in curriculum.ts.

Constraints that shape the design: no GPU and no PyTorch on the build box, and every quoted output must be
reproducible from a clean checkout. So each lesson's runnable example is a **standard-library Python toy model**
(fixed seeds, `random.Random`) that shows the real algorithmic effect, quoted as `<SimOutput source="model">`.
The real-hardware path (LeRobot on an SO-101, `lerobot-record` / `lerobot-train`) is given as commands to run on
the learner's own machine, clearly marked as not run here. All code lives in `examples/month-6/<slug>/`, outputs in
`examples/month-6/expected/`, and `examples/month-6/check.sh` re-runs everything and diffs (also hooked into
`tools/sim/reproduce.sh`). `tools/check_quotes.py` checks CodeSource and SimOutput blocks.

| # | slug | lesson | runnable example | how it is verified |
|---|------|--------|------------------|--------------------|
| 1 | `behaviour-cloning` | Imitation learning I: demonstrations, behaviour cloning, covariate shift, DAgger | `bc_reach.py`: a point gripper in a narrow corridor; a scripted expert records episodes in a LeRobot-style table (episode_index, frame_index, observation.state, action); a nearest-neighbour BC policy is trained on 5 / 20 / 80 demos and evaluated over 100 seeded rollouts with actuator noise; then 3 DAgger rounds | success rate, mean off-path distance and failure count per policy compared with `expected/bc_reach.txt` |
| 2 | `act-diffusion` | Imitation learning II: multimodal demos, action chunking (ACT) and diffusion policy | `multimodal.py`: an obstacle the expert passes on the left or the right (50/50). Compares an MSE-style averaging policy (drives into the obstacle), single-step sampling (mode switching, dithering), action chunks with temporal ensembling (ACT idea), and DDPM sampling with the exact denoiser of the demo set (what a diffusion policy's network learns to approximate) | success / collision / timeout counts over seeded rollouts, `expected/multimodal.txt` |
| 3 | `vla-models` | VLA models: what they are, how actions become tokens, which have open weights | `action_tokens.py`: RT-2/OpenVLA-style 256-bin per-dimension tokenisation (1st–99th percentile range) vs. a DCT-based chunk compression in the spirit of FAST; token counts and reconstruction error on a recorded trajectory | `expected/action_tokens.txt`; open-weight facts (OpenVLA, Octo, π0/π0.5 via openpi, SmolVLA, GR00T N1.x, RDT) checked against each official page with "check the official page" note |
| 4 | `policy-evaluation` | Evaluating a policy: success rate, confidence intervals, failure analysis | `eval_report.py`: reads the episode logs written by lessons 1–2, prints success with Wilson 95 % intervals, how many trials are needed to tell two policies apart, and a failure taxonomy table | `expected/eval_report.txt` |
| 5 | `specialisation-portfolio` | Choosing a specialisation, the portfolio and getting hired | `portfolio_check.py`: checks a project folder's README for the parts a reviewer looks for (demo video link, metrics table, failure analysis, reproduce commands, hardware list) and prints what is missing; run on a good and a bad sample project in the repo | `expected/portfolio_check.txt` (pass + fail case) |

Per lesson: zh.mdx + en.mdx in `src/content/m6/<slug>/` (same structure, quiz ids, numbers), README.md in the
example folder, lesson entry with tasks in `month6Lessons` in curriculum.ts, resources in resources.ts
(official pages only, external links). Month 6 `status` stays `"outline"` until all five lessons exist, then `"ready"`.
Verification per lesson: `npx tsc --noEmit`, `npx eslint .`, `npm run build`, `examples/month-6/check.sh`,
`python3 tools/check_quotes.py`; commit and push after each lesson.

## Status (2026-10-20, UTC+8)

All five lessons built and pushed on `opencode/month-6`; Month 6 `status` is now `"ready"`. PR not opened yet.

| lesson | commit |
|---|---|
| 1 `behaviour-cloning` | 75e94c0 (wording fix on seeds: e52530e) |
| 2 `act-diffusion` | ed41329 (wording fix on seeds: e52530e) |
| 3 `vla-models` | ef30048 |
| 4 `policy-evaluation` | 537ee3a |
| 5 `specialisation-portfolio` | 24fd29d |

Changes from the plan above:
- Lesson 2: the nearest-neighbour toy shows the averaging failure (67/100 vs 99/100 for sampling) and the open-loop
  cost of long chunks (chunk 16: 80/100), but not chunking's benefits (the position already tells the policy which
  side it is on; variants with smaller steps and with a pause at the fork did not show it either). The lesson says so
  and explains the benefits (fewer decisions, consistency, pauses, temporal ensembling) in prose only.
- Lessons 1-2 evaluate every policy from one shared seed, which does not give identical per-trial conditions once
  policies take different numbers of steps; the text now says this, and lesson 4 uses per-trial seeds.
- Lesson 4 imports lesson 1's model (no separate episode-log file); lesson 5's sample READMEs live in
  `examples/month-6/specialisation-portfolio/samples/`, and its output is a real run (unlabelled), checked by
  check.sh against expected/ and against the text quoted in both MDX files.
- VLA licence facts were checked on 2026-10-20 against the Hugging Face model cards/API (OpenVLA MIT, Octo MIT,
  SmolVLA Apache-2.0, lerobot/pi05_base Gemma, GR00T N1.6 NVIDIA research licence, GR00T N1.7 NVIDIA Open Model
  License) and the openpi README (code Apache-2.0).

## Follow-up PR3 (+150 here)

F7 `policy-evaluation` 180→330 — `eval_seed_layers_toy.py`: `synthetic_policy_draw_k` (not real training); `shared_IC` / `independent_IC` separate tables; Wilson/Beta count intervals separate from across-draw dispersion; best-seed cherry-pick vs median; checklist fields from arXiv 2409.09491v2 §4. Month 6 then **1 170 min**. With F5+F6: site then **71 lessons / 17 310 min**.

## Batch-after-obs PR2 (G4, +180 here)

G4 `vla-models` 180→360 — `vla_async_chunk_toy.py`: SmolVLA read per the paper; sync vs async (queue remaining fraction &lt; g triggers next request); same chunk prediction / same ℓ_S; idle_s, infer_calls, underruns, action staleness and overlapping chunk switches; async ≠ 10.2 RTC soft-mask ≠ 8.3 timestamp sync. Month 6 **5 lessons / 1 350 min**. With G3: site then **71 lessons / 18 120 min**; after G5–G7: site **71 lessons / 18 570 min** (from `src/lib/curriculum.ts`).

## Batch-7 PR3 / 本月 H6 (+210)

6.2 act-diffusion240→450. M6 **1350→1560**, M10 **2070→2280**. This PR only:23190+210+210=**23610**,71 lessons; no arithmetic mismatch, no earlier PR minutes counted twice.

Allocation:45+45+45+45+30=210 min (model/loss or information declaration / implementation / shared-seed experiment / limits and reading / exercises).
Shared compliant-object kinematic task, all arms/modes receive full noisy snapshot and goals, independent deliberately factorizes it; no local-only versus oracle information advantage. All400 ticks, same noise/gains/caps, arrival/collision/censoring rules explicit; five-seed full-horizon metrics. TwinVLA architecture only from opened original section4; no robots/weights. Add full whole-lesson final Summary because both languages lacked one.
New symmetric en/zh code/stdout/exercises before final Summary, stdlib expected+harness, independent regression locks, opened-source audit in batch-7-pr3-sources.md. No workflows changed.

## Batch-8 PR3 / 本月 H5 + H6 (+420)

Base 1d2717b, after #134. H5 6.1 behaviour-cloning 240→450 (+210), H6 6.3 vla-models 360→570 (+210).
M6 **1560→1980**; site **24240→24660** (+420), still 71 lessons. No arithmetic mismatch with proposal §9 or curriculum.ts on 1d2717b. Batch-8 final total 24660; README site copy updated from the stale 23 610 to 24 660.

- H5: 45 min multimodal BC and the mean failure +45 min BeT k-means bins / VQ-BeT residual VQ + offsets (opened papers) +45 min shared demos, observation bins, heads, rollout stream; equal codebook vectors (8) and Lloyd iterations (12), unequal combinations (8 vs 16) printed +45 min five-seed results (MSE 66 % collisions; k-means and rvq tie on modes) +30 min exercises =210. 5× speed-up 以论文为准; GPU 本页未运行. Not FAST/DCT (6.3), diffusion (6.2) or DAgger.
- H6: 45 min single trunk vs dual system and OpenHelix's real-time perception criterion (π0 not dual-system) +45 min OpenHelix architecture/findings per the paper +45 min equal-compute cadence toy, declared information per arm, eight switch-time seeds +45 min moving-switch vs static scenarios, no winner +30 min exercises =210. Separate from TwinVLA (6.2) and async chunking. Weights/GPU/CALVIN 本页未运行.
- Neither host had a Summary: each now ends with a full whole-lesson Summary in en and zh whose last sentence covers the new section. New code/stdout/exercises precede it.

## Batch-9 PR3 / 本月 H5 (+210)

Base `64579b5` (Batch-9 PR2 merged). PR3 only: **M6 1980→2190 (+210)** and M11 **3000→3210 (+210**, own host in month-11-plan.md); site **25380→25800**, still 71 lessons; no arithmetic mismatch with proposal §9 or curriculum.ts. Batch 9 is complete at 25800.

- **H5 / 6.3 vla-models: 570→780 (+210).** RDT2 three-stage recipe (arXiv 2602.03310, opened; numbers 以论文为准): Stage 1 RVQ tokens + cross-entropy, Stage 2 frozen VLM + flow-matching expert, Stage 3 one-step distillation. Toy: equal 8-bit budget (bins 4×4, single VQ 256, RVQ 2×16, RVQ 4×4) and shared noise draws for FM 1/2/5 NFE vs two lookup students (offline expert NFE reported), five seeds; no winner. New section after the OpenHelix dual-system section, which is unchanged; ≠ VQ-BeT (6.1), ≠ OneDP (10.1). 7B training / GPU 本页未运行. / RDT2 三阶段，不宣布赢家。

**Allocation / 安排:** 40+30+50+60+30=210 minutes. Sources: batch-9-pr3-sources.md.

## Batch-11 PR3 / 本月 H5 (+210)

Base `777543d` (batch-11 PR2 #146 merged; site **27630**). PR3 only: **M6 2190→2400 (+210)** and M8 **3180→3390 (+210**, own host in month-8-plan.md); site **27630→28050**, still 71 lessons; no arithmetic mismatch with proposal §9 or curriculum.ts.

- **H5 / 6.2 act-diffusion: 450→**660** (+210).** CogACT componentized VLM→specialized action module (Qixiu Li et al. arXiv:2411.19650, abs+HTML+PDF opened; numbers 以论文为准). Toy `cogact_dit_action_toy.py`: shared demos/noise/budget; A ridge-linear MLP-head stand-in, B pairwise-expanded+iterative DiT-style expressivity stand-in (not a real transformer), C quantized tokens; unimodal_short exact tie (|ΔMSE|≈0), multimodal_long DiT-style edge; five seeds, common random numbers. ≠ OpenHelix / VQ-BeT / RDT2. GPU/weights 本页未运行. Sources: batch-11-pr3-sources.md.

**Site accounting / 全站核算:** **28050=27630+420** with M8 +210 on month-8-plan.md; **M6=2400**, **71 lessons**.

## Batch-16 PR3 / 本月 H5 + H6 (+420)

Base `b162a86` (batch-16 PR2 merged as #166; site **33180**). PR3 only: **M6 2820→3240 (+420)**; site **33180→33600**, still 71 lessons. Batch 16 content is complete at 33600.

- **H5 / 6.3 vla-models: 990→**1200** (+210).** MolmoAct (Jason Lee et al., arXiv 2508.07917; abs + PDF body read, HTML fetched; numbers 以论文为准): depth perception tokens → 2-D visual reasoning trace (1–5 points) → action tokens; steering by editing the trace. Toy `molmoact_reasoning_trace_toy.py`: kinematic gripper, wall check V/SUB < WALL_T asserted (no integration step); arms A direct kNN / B depth-token + trace / C mirrored or frozen wrong trace; 5 regimes, 5 seeds, CRN. multi_stage_few B−A success +72.0000±8.5513 clear 5/5; multi_stage_many near-tie (−4.5000±4.8088); single_step clear B win (expected near-tie, disclosed); steer_in_plane B beats A and C clearly; steer_depth edited vs frozen near-tie (2-D edit cannot choose along depth). ≠ ThinkAct / CoT-VLA / TraceVLA. 7B / LIBERO / GPU 本页未运行.
- **H6 / 6.1 behaviour-cloning: 450→**660** (+210).** HAMSTER (Yi Li et al., arXiv 2502.05485; abs + PDF body read, HTML fetched; numbers 以论文为准): high-level VLM draws a coarse 2-D path with gripper states, low-level 3-D policy follows it. Toy `hamster_hierarchical_path_toy.py`: arms A monolithic kNN (sees background appearance) / B path + path-relative kNN low level / C off-task path; 4 regimes, 5 seeds, CRN. visual_shift B−A +76.5000±7.4162 clear 5/5; matched_easy clear B win (expected near-tie, disclosed); coarse_path B still ahead (expected loss, disclosed); no_appearance (added after the first run, disclosed) near-tie −2.5000±4.3301. ≠ ACT / DP head; ≠ MolmoAct traces. VLM / real robot 本页未运行.

**Allocation / 安排:** each host 40+30+50+50+40=210 minutes. Sources: batch-16-pr3-sources.md.

**Site accounting / 全站核算:** **33600=33180+420**; **M6=3240**, **71 lessons**.

## Batch-14 PR3 / 本月 H5 + H6 (+420)

Base `386f359` (batch-14 PR2 merged as #158; site **30960**). PR3 only: **M6 2400→2820 (+420)**; site **30960→31380**, still 71 lessons; no arithmetic mismatch with proposal §9 or curriculum.ts. Batch 14 content is complete at 31380.

- **H5 / 6.2 act-diffusion: 660→**870** (+210).** HybridVLA (Jiaming Liu et al., arXiv 2503.10631, HTML + PDF opened; numbers 以论文为准): diffusion and AR actions from one LLM, collaborative action ensemble at θ = 0.96. Toy `hybridvla_action_ensemble_toy.py`: two head error models (no training, no time step), arms A AR only / B diffusion only / C confidence-gated average; shared episodes, evidence and noise (common random numbers, 5 seeds). precision: C−A 21.8500±1.3647, C−B 7.0500±2.0797, both 5/5; semantic: C−B success **tie** (identical on every seed), C−A −26.8500±2.5593 (C loses to the AR specialist, 5/5); mixed: C−A −2.9000±1.5268 (C loses to the best single head, 5/5); easy_precision: success **tie**. ≠ ACT vs DP, ≠ CogACT AAE, ≠ OneDP, ≠ Diffusion Forcing. GPU 本页未运行.
- **H6 / 6.3 vla-models: 780→**990** (+210).** CoT-VLA (Qingqing Zhao et al., arXiv 2503.22020, HTML + PDF opened; numbers 以论文为准): subgoal image first, then an action chunk. Toy `cot_vla_subgoal_toy.py`: count tables on a 1-D track (no time-step integration), arms A direct / B subgoal every chunk / C subgoal every 2nd chunk; shared task, demos, videos and starts (common random numbers, 5 seeds). multi_stage_video: B−A success 62.0000±44.8400 (5/5); multi_stage_no_video, multi_stage_action_rich, single_reach: B−A success **near-tie**, B loses on tokens (clear, 5/5); C loses to B on multi-stage success (clear). New section after Common mistakes, before the Summary; RDT2 section unchanged. ≠ DreamGen / TraceVLA / MAP-VLA / WorldVLA. GPU 本页未运行.

**Allocation / 安排:** each host 40+30+50+50+40=210 minutes. Sources: batch-14-pr3-sources.md.

**Site accounting / 全站核算:** **31380=30960+420**; **M6=2820**, **71 lessons**.
