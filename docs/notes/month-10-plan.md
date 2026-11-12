# Month 10 plan / 第 10 个月计划

Current / 当前：**M10 3750 min**, Batch-18 PR3. Earlier entries below retain their historical totals.

## Batch-18 PR3 / 本月 H5+H6 (+420)

Base `e055b90690d7655f9810d49fff920c193f1e7338` (batch-18 PR2 merged as #174; site **35400**). PR3 only on M10 hosts: **M10 3330→3750 (+420)**. Site **35400→35820**, still 71 lessons.

- **H5 / flow-matching-policies: 660→870 (+210).** Knowledge Insulation (arXiv 2505.23705, HTML + PDF body read; 11 authors verified). Toy `knowledge_insulation_flow_toy.py`: linear VLM-stand-in + flow-matching expert + frozen semantic probe; arms A naive FM grads into the backbone / B discrete-action CE with stopped expert grads / C frozen backbone. Common random numbers, 5 seeds. No plant integration step. conflict: B−A probe 33.9000±6.9991 **clear**, 5/5 (A consistent semantic drop); B−A control 0.8500±4.2815 **near-tie**; C−B probe **tie: identical on every seed**, C−B control −10.1500±6.3161 **clear**, 5/5 (frozen probe-win / control-lose kept). A is *faster* on `fit_mid` (B−A 2.1921±0.6843 clear, 5/5) — §9's "and/or slower residual drop" for A did not hold; kept and printed. After the first run the discrete head was restricted to action-slot units `h[SEM:]`; the first-run full-`h` head is still printed (B−A probe −12.7500±12.1861, B worse). ≠ ChatVLA / OneDP. Paper numbers 以论文为准; GPU / π0 / LIBERO 本页未运行.

- **H6 / edge-deploy-checklist: 330→540 (+210).** VLA-Adapter Bridge Attention (arXiv 2509.09372, HTML + PDF body read; 16 authors verified). Toy `vla_adapter_bridge_attention_toy.py`: shared demos; arms A larger two-layer 48-wide plain head / B tiny + Bridge Attention / C same tiny policy with shuffled VL conditions. short_id: B−A success 5.6000±7.9009 **near-tie**; B consistent-wins params −2393.0000±0.0000 and flops −2036.0000±0.0000, **clear**, 5/5. need_vl: C−B success −41.9000±12.6461 **clear**, 5/5 (shuffled lose). precise: B−A success −20.2000±14.4075 **clear** (tiny+bridge loses to the large head; kept). After the first run: learned AQ MLP, proprio/AQ residual, larger A backbone, STEPS=300 / LR=0.10; first-run short_id is replayed by `_vla_adapter_firstrun.py` (B params 381 > A 266; B success 11.3000±9.9411). ≠ SmolVLA / weights-only budget / OpenVLA-OFT. Paper 0.5B / 8 h 以论文为准; GPU 本页未运行.

**Allocation / 安排:** 45+30+45+50+40=210 minutes per host.

**Site accounting / 全站核算:** **35820=35400+420**; **M10=3750**, **71 lessons**.


Current / 当前：**M10 3330 min**, Batch-15 PR3. Older sections retain historical totals.

## Batch-15 PR3 / 本月 H5+H6 (+420)

Base `2e88830` (batch-15 PR2 merged as #162; site **32070**). PR3 only on M10 hosts: **M10 2910→3330 (+420)**. Site **32070→32490**, still 71 lessons.

- **H5 / 10.2 real-time-chunking: 180→390 (+210).** FORGE-Tree (arXiv 2510.21744 v1, PDF body read): stage-aligned Diffusion Forcing head on a frozen VLA, partial denoising of one segment with the complement frozen, stage-aware MCTD with P-UCT, fast heuristic and scene-graph return, executed prefix preserved. Toy `forge_tree_mctd_toy.py`: displacement tokens, depth-1 segment search (uniform prior, `c_puct = 1.0`), accept-if-better on a noisy geometry return; arms one-shot / tree / random segments; common random numbers, 5 seeds × 40 trials; no integration step, prefix violations 0 in every arm. long_tight: B−A final 0.1400±0.0548 clear 5/5; low_budget: B−A final **near-tie**, random picks ahead on stage (C−B 0.0363±0.0284, 5/5); noisy_graph: B−A final **tie**; single_stage: B−A clear (§9-adjacent mismatch with the proposal's single-stage near-tie, disclosed); budget sweep B−A final tie at N = 1, near-tie at 2 and 4, clear from 8. No parameter changed after the first run. LIBERO % 以论文为准, 本页未运行.
- **H6 / 10.6 real-world-rl: 450→660 (+210).** ThinkAct (arXiv 2507.16815 v2, PDF body read): reasoning MLLM writes a visual plan latent, GRPO on goal + DTW trajectory + format rewards, DiT action model conditioned through a Q-Former, asynchronous N actions per latent. Toy `thinkact_visual_latent_toy.py`: grid stages with revisits, stage indicator hidden with q_hide; arms direct / plan latent / rotated (scrambled) latent; shared demos, slips and hides; 5 seeds × 40 trials; no integration step. single_step: **tie**; multi_stage (per-step hide): **near-tie** (§9 mismatch, disclosed); ambiguous / multi_stage_block / ambiguous_block: small but consistent B wins; noisy_plan: B loses; drop_dense: small B win, drop_sparse: near-tie; scrambled C−B clear in multi_stage, near-tie in ambiguous_block. Post-hoc (disclosed, alternatives printed): shared fallback, rotated C, `_block` regimes. Paper % 以论文为准, 本页未运行.

**Allocation / 安排:** H5 45+30+45+50+40=210; H6 45+30+45+50+40=210 minutes.

**Site accounting / 全站核算:** **32490=32070+420**; **M10=3330**, **71 lessons**.

## Batch-13 PR3 / 本月 H5+H6 (+420)

（历史）Batch-13 PR3 header: M10 2910 min.

Base `e0c9ccf` (batch-13 PR2 merged; site **29850**). PR3 only on M10 host: **M10 2490→2910 (+420)**. Site **29850→30270**, still 71 lessons.

- **H5 / intervention-logging: 180→390 (+210).** MAP-VLA (arXiv 2511.09516, HTML + PDF body read) stage memory prompts: `P_k = P_base + V_k`, sliding-window L2 retrieval limited to `|k − k_cur| ≤ 1`, α soft ensemble. Toy `map_vla_memory_prompt_toy.py`: frozen least-squares base, prompt = mean residual per stage; arms memoryless / MAP retrieval / wrong-stage memory; common random numbers, 5 seeds × 20 episodes. ambiguous_long: B−A stage 0.3500±0.1075 clear 5/5; distinct_long: B−A near-tie; single_stage: B−A stage and full **tie: identical on every seed**; wrong-stage C−B stage −0.6625±0.0395 clear 5/5 (distinct_long only small but consistent). ≠ π0 fine-tuning; π0 / real robot 本页未运行.
- **H6 / flow-matching-policies: 450→660 (+210).** Diffusion Forcing (arXiv 2407.01392, HTML + PDF body read): independent per-token noise level, `k_small` re-noising; FORGE-Tree 2510.21744 reading only. Toy `diffusion_forcing_token_noise_toy.py`: linear pair-tabular denoiser, K=10 cosine schedule, exact `ρ(G)` criterion; arms teacher forcing / Diffusion Forcing / causal full-sequence. in_horizon: DF **loses** (B−A mse 0.3378±0.0455 clear 5/5; near-tie with k_small = 0); past_horizon: B−A div −1.0000±0.0000 clear 5/5; guided_s8: teacher forcing beats DF, guided_s32: DF beats teacher forcing; causal full-sequence never ties or beats DF (§9 mismatch, disclosed). Video / Maze2D / Franka 以论文为准, 本页未运行.

**Allocation / 安排:** H5 40+30+40+50+50=210; H6 45+30+45+50+40=210 minutes.

**Site accounting / 全站核算:** **30270=29850+420**; **M10=2910**, **71 lessons**.

## Batch-10 PR3 / 本月 H4 (+210)

（历史）Batch-10 PR3 header: M10 2490 min.

Base `e814307`. PR3 only on M10 host: **M10 2280→2490 (+210)**; M9 +210 on month-9-plan.md. Site **26520→26940**, still 71 lessons.

- **H4 / 10.4 multi-view-extrinsics: 240→450 (+210).** SpatialVLA Ego3D + adaptive action grids: shared camera-frame points; 2D-only vs Ego3D vs CDF/PPF grids; ≥5 seeds; ≠ AX=ZB rewrite. GPU 本页未运行. / Ego3D 与自适应网格，不宣布 SpatialVLA 基准。

**Allocation / 安排:** 45+45+45+45+30=210 minutes.

**Site accounting / 全站核算:** **26940=26520+420** with M9 +210; **M10=2490**, **71 lessons**.

<!-- historical -->

Current / 当前（历史） Batch-7 PR3: M10 **2280 min**; older sections retain historical totals.

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Lessons open with "This lesson is a site supplement — Months 7–11 are not part of the original six-month course." / 「本课是本站补充内容——第 7–11 个月不属于原六个月课程。」

**PR1–PR3:** full MDX + examples for **10.1–10.7** (PR1: 10.1–10.3, PR2: 10.4–10.5, PR3: 10.6–10.7). `multi-view-extrinsics`, `intervention-logging` and `edge-deploy-checklist` were Month 9 electives and are now formal lessons. Month 10 does not replace the 8.7 capstone and does not open a new track.

Constraints: no new hardware; not required this month: Isaac, an F/T sensor or a real robot. Runnable toys are stdlib CPU with fixed seeds, outputs pinned in `examples/month-10/expected/` and checked by `examples/month-10/check.sh` (7 of 7). GPU training, weight downloads, real SO-101 runs and LeRobot CLI commands are marked「本页未运行」; commands carry「以当期文档为准」against LeRobot v0.6.x.

| # | slug | minutes | runnable | verified against |
|---|------|---------|----------|------------------|
| 1 | `flow-matching-policies` | 450 | `flow_match_toy.py`, `policy_distill_onestep_toy.py` | Flow Matching / π0 / rectified flow / SmolVLA papers; LeRobot π0.5 docs |
| 2 | `real-time-chunking` | 180 | `rtc_blend_toy.py` | RTC paper; LeRobot RTC + async docs |
| 3 | `edge-deploy-checklist` | 330 | `latency_budget.py`, `int8_quant_toy.py`, `vla_edge_budget_toy.py` | ONNX Runtime quantization; LeRobot hardware / accelerator docs |
| 4 | `multi-view-extrinsics` | 450 | `extrinsics_chain_toy.py`, `spatialvla_ego3d_grid_toy.py` | OpenCV calibrateRobotWorldHandEye / ArUco / solvePnP docs; SpatialVLA 2501.15830 |
| 5 | `intervention-logging` | 180 | `intervention_log_toy.py` | LeRobot HIL data collection + v0.6.0 blog; DAgger / HG-DAgger / RaC |
| 6 | `real-world-rl` | 240 | `rlpd_chain_toy.py` | RLPD arXiv 2302.02948; HIL-SERL arXiv 2410.21845; LeRobot HIL-SERL docs |
| 7 | `vla-rl-finetune` | 450 | `advantage_filter_toy.py` (optional), `cal_conrft_offline_toy.py` | SimpleVLA-RL 2509.09674; OpenVLA-OFT 2502.19645; π*0.6 blog; ResiP 2407.16677; Policy Decorator 2412.13630; LeRobot SARM docs; ConRFT2502.05450 / Cal-QL2303.05479 (opened) |

Current total **2 070 minutes** (Batch-6 PR3); historical total1 650 after G7. Pointers: 8.3 → 10.2 (async seam), 8.7 capstone → Month 10 (optional, not a replacement), M8 topics → "HIL-SERL 见 10.6".

Widgets deferred. No prices anywhere.

Verification: `examples/month-8/check.sh`, `examples/month-9/check.sh`, `examples/month-10/check.sh`, check_quotes, check_diagrams, check_widgets, lint, check_wokwi, tsc, CI build.

Batch-after-obs PR3 (G7, +150): 10.3 `edge-deploy-checklist` 180→330 — `vla_edge_budget_toy.py`: weights-only memory (params × bytes; activations / KV cache / vision buffers excluded and labelled) for SmolVLA 0.45B, π0-class 3.3B, OpenVLA-class 7B (counts from the papers); chunk / Hz / sync idle linked to 6.3's g ≥ (E[ℓ_S] / Δt) / n. No device measurements; Jetson / Pi 本页未运行. Month 10 **7 lessons / 1 650 min**; site **71 lessons / 18 570 min**.

## Batch-5 PR3 (+210 here)

10.7:240→450; M10 **1650→1860**,7 lessons. Site **20700→21090** with M9+180 (2730). Same-data/equal-update offline BC/CQL/Cal-QL, MC reference inside conservative push-down, five seeds and restricted/tabular representation control. Online dip, consistency head and robot/GPU reading only / 本页未运行; paper以论文为准. Existing advantage filter and10.6 unchanged.

## Batch-6 PR3 / 本月 H1 (+210)

10.1:240→450; M10 **1860→2070**, still 7 lessons. Site **21960→22350** with M8 **2850→3030** (+180). Count only PR3:210+180=390. Shared64 demos / disjoint64 eval starts, 5 seeds, action MSE / actual NFE / independent nonlinear-plant success. Eight-call analytic teacher, one-call full/underfit regressors; unequal fit updates disclosed, no convergence claim. OneDP reverse KL and real Consistency Policy reading only; GPU 本页未运行, figures 以论文为准. Existing Consistency Policy paragraph and expected outputs retained. Sources: batch-6-pr3-sources.md.

## Batch-7 PR3 / 本月 H5 (+210)

10.6 real-world-rl240→450. M6 **1350→1560**, M10 **2070→2280**. This PR only:23190+210+210=**23610**,71 lessons; no arithmetic mismatch, no earlier PR minutes counted twice.

Allocation:45+45+45+45+30=210 min (model/loss or information declaration / implementation / shared-seed experiment / limits and reading / exercises).
Three core arms DPO / RM+RL / preferred-only BC plus BC-all/success-filter to retain the proposal literacy baselines. Success-filter's extra binary training supervision is explicit. Same64 pairs,240 total gradient slots (RM120 reward +120 policy), disjoint256 eval contexts, five seeds and25 % preference flips; no truth reward in optimization or evaluation-label tuning. Existing HIL-SERL chain and SARM pointers preserved.
New symmetric en/zh code/stdout/exercises before final Summary, stdlib expected+harness, independent regression locks, opened-source audit in batch-7-pr3-sources.md. No workflows changed.
