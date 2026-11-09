# Month 6 plan: Robot learning, specialisation & getting hired

Current / 当前：**M6 2820 min**, Batch-14 PR3. Earlier entries below retain their historical totals.

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

## Batch-14 PR3 / 本月 H5 + H6 (+420)

Base `386f359` (batch-14 PR2 merged as #158; site **30960**). PR3 only: **M6 2400→2820 (+420)**; site **30960→31380**, still 71 lessons; no arithmetic mismatch with proposal §9 or curriculum.ts. Batch 14 content is complete at 31380.

- **H5 / 6.2 act-diffusion: 660→**870** (+210).** HybridVLA (Jiaming Liu et al., arXiv 2503.10631, HTML + PDF opened; numbers 以论文为准): diffusion and AR actions from one LLM, collaborative action ensemble at θ = 0.96. Toy `hybridvla_action_ensemble_toy.py`: two head error models (no training, no time step), arms A AR only / B diffusion only / C confidence-gated average; shared episodes, evidence and noise (common random numbers, 5 seeds). precision: C−A 21.8500±1.3647, C−B 7.0500±2.0797, both 5/5; semantic: C−B success **tie** (identical on every seed), C−A −26.8500±2.5593 (C loses to the AR specialist, 5/5); mixed: C−A −2.9000±1.5268 (C loses to the best single head, 5/5); easy_precision: success **tie**. ≠ ACT vs DP, ≠ CogACT AAE, ≠ OneDP, ≠ Diffusion Forcing. GPU 本页未运行.
- **H6 / 6.3 vla-models: 780→**990** (+210).** CoT-VLA (Qingqing Zhao et al., arXiv 2503.22020, HTML + PDF opened; numbers 以论文为准): subgoal image first, then an action chunk. Toy `cot_vla_subgoal_toy.py`: count tables on a 1-D track (no time-step integration), arms A direct / B subgoal every chunk / C subgoal every 2nd chunk; shared task, demos, videos and starts (common random numbers, 5 seeds). multi_stage_video: B−A success 62.0000±44.8400 (5/5); multi_stage_no_video, multi_stage_action_rich, single_reach: B−A success **near-tie**, B loses on tokens (clear, 5/5); C loses to B on multi-stage success (clear). New section after Common mistakes, before the Summary; RDT2 section unchanged. ≠ DreamGen / TraceVLA / MAP-VLA / WorldVLA. GPU 本页未运行.

**Allocation / 安排:** each host 40+30+50+50+40=210 minutes. Sources: batch-14-pr3-sources.md.

**Site accounting / 全站核算:** **31380=30960+420**; **M6=2820**, **71 lessons**.
