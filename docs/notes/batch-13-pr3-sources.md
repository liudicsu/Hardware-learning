# Batch-13 PR3 source, scope and validation audit

Base: `e0c9ccf` (batch-13 PR2 #154 merged; site **29850**). Proposal `batch-13-proposal.md` §9 PR3 locks: H5 10.5 intervention-logging MAP-VLA stage memory prompts +210, H6 10.1 flow-matching-policies Diffusion Forcing +210. No arithmetic mismatch: curriculum.ts on base gives M10 2490 / site 29850 / 71 lessons; after this PR **M10 2910**, site **30270** (= 29850 + 420), still 71 lessons.

## Opened sources (curl -L + body read, 2026-11-10, Asia/Shanghai UTC+8)

- `mapvla-html` / MAP-VLA, arXiv 2511.09516 HTML: https://arxiv.org/html/2511.09516, HTTP 200, LaTeXML body read (not a JavaScript shell). §III-A stage segmentation with RDP key poses and DTW alignment; §III-B `P_k = P_base + V_k` (Eq. 2) tuned with the flow-matching loss on a frozen π0 (Eq. 3); §III-C sliding-window L2 retrieval restricted to `|k − k_cur| ≤ 1` (Eq. 4–5) and the α softmax ensemble (Eq. 6–7). 以论文为准.
- `mapvla-pdf` / MAP-VLA PDF: https://arxiv.org/pdf/2511.09516, HTTP 200, 9 pages, body read via pdftotext. LIBERO-Long 83.4 vs 76.4 (+7.0); real robot 48.3 vs 23.3 (+25.0); stage-prompt ablation 81.4; retrieval 21.6 ms with 37.8 demos per task; Galaxea A1, RTX 4090. Numbers 以论文为准; π0 / GPU 本页未运行.
- `dforcing-html` / Diffusion Forcing, arXiv 2407.01392 HTML: https://arxiv.org/html/2407.01392, HTTP 200, LaTeXML body read. §3.1 noise as partial masking; §3.2 independent per-token `k_t` (Algorithm 1), causal RNN, loss Eq. 3.1, Theorem 3.1 reweighted ELBO; scheduling matrix `K`; §3.3 stabilization with `k_small`, zig-zag schedule; §3.4 Monte Carlo Guidance. 以论文为准.
- `dforcing-pdf` / Diffusion Forcing PDF: https://arxiv.org/pdf/2407.01392, HTTP 200, 35 pages, body read via pdftotext (abstract through §4.5, App. B.2 i.i.d. uniform noise levels, App. B.4 stabilization). §4.1 teacher forcing and causal full-sequence baselines diverge past the training horizon, DF stable (e.g. 1000 frames); §4.2 Maze2D beats Diffuser (which needs a PD controller); §4.4 Franka 80 % where diffusion policy fails, 76 % vs 48 % under occlusion. Numbers 以论文为准; video models, Franka and GPU 本页未运行.
- `forge-tree-pdf` / FORGE-Tree, arXiv 2510.21744 PDF: https://arxiv.org/pdf/2510.21744, HTTP 200, 8 pages; abstract and introduction read via pdftotext. Stage-aligned DF head on a frozen VLA encoder + Monte Carlo Tree Diffusion; LIBERO +13.4 to +17.2 pp over native VLA baselines (OpenVLA, Octo-Base). Reading only, no toy; 以论文为准.

Derived in the lessons, not quoted: the α ensemble worked example (0.690 / 0.182); the feedback gain `ρ(G)` criterion and `1.023^120 ≈ 15`, `0.95^120 ≈ 0.002`; `ᾱ_1 = cos²(π/20) = 0.976`.

Cached under `/workspace/b13p3-sources/` on the worktree host (not committed): `mapvla-abs.html`, `mapvla.html`, `mapvla.pdf/.txt`, `df-abs.html`, `df.html`, `df.pdf/.txt`, `forge-abs.html`, `forge.pdf/.txt`.

## Toy design

- `map_vla_memory_prompt_toy.py` (10.5): a 2D point visits K goals (STEP 0.25, TOL 0.15, budget 14 per stage); the observation is `[state, look, 1]`; a frozen least-squares linear base W (ridge 1e-6) stands in for a frozen VLA; a stage prompt is the mean residual of W per stage (the least-squares optimum of an additive prompt); retrieval = sliding-window (WIN 4) L2 over demo segments of stages `|k − k_cur| ≤ 1`, α = 1/(1+exp(d_mem − d_base)). Arms: A memoryless / B MAP retrieval / C wrong-stage memory (prompt and reference from the neighbouring stage). Regimes ambiguous_long (looks 0,1,0,1), distinct_long (0,1,2,3), single_stage (C not run), noisy_retrieval (state sd 0.12). Common random numbers, 5 seeds × 20 episodes, 8 demos.
- `diffusion_forcing_token_noise_toy.py` (10.1): 2D Hopf-like limit-cycle map (θ 0.3, γ 0.15, σ 0.02); 2000 training sequences of 8 tokens; linear least-squares denoiser per noise-level pair, K = 10 cosine levels, deterministic DDIM; arms A teacher forcing (k_prev = 0), B Diffusion Forcing (independent levels, context re-noised to k_small = 1), C causal full-sequence (k_prev = k_cur). Exact `ρ(G)` via two unit differences (the sampler is affine in the previous token). Regimes in_horizon, past_horizon (128 tokens), guided_s8 / guided_s32 (best-of-S selection stand-in, not gradient guidance or MCG). k_small sweep 0 / 1 / 2. Common random numbers, 5 seeds × 20 episodes.

Label helpers follow #154 (`num`, `sign_note`, `fmt_pair`, `verdict`, `NUM_ZERO = 1e-9` checked before the sd test).

## §9 lock vs measured numbers (numbers followed)

- H5: ambiguous MAP consistent win — met (B−A stage 0.3500±0.1075, 5/5). single-stage near-tie allowed — measured **tie: identical on every seed** on stage and full, near-tie on steps. wrong-stage C consistent loss — met in ambiguous_long and noisy_retrieval; in distinct_long only small but consistent on stage (1 of 5 opposite), near-tie on full / steps.
- H6: past-horizon DF stable — met (B−A div −1.0000±0.0000, 5/5). in-horizon A/B "may near-tie" — **mismatch**: with k_small = 1 DF loses clearly (mse 0.3378±0.0455, 5/5); only k_small = 0 near-ties (0.0011±0.0062), and then diverges like teacher forcing. guided regime where full-sequence "may tie or beat" DF — **mismatch**: causal full-sequence loses clearly at S = 8 (0.2966±0.0505) and S = 32 (0.2248±0.0468); the lose/tie regime for DF is instead in_horizon and guided_s8 (teacher forcing beats DF, 0.0451±0.0242, 5/5). Disclosed in the prose; a non-causal Diffuser-style planner is not modelled.

Independent tests: `tools/test_b13p3_mapvla_dforcing_toys.py` (17 tests; also executed by the batch-13 PR3 block in `tools/check_diagrams.mjs`).

## Lock changes (totals only)

Existing locks updated only for totals / current-tip markers: site total 29850→30270 (two curriculum locks), month table M10 2490→2910, README `29 850`→`30 270`, `b6p3 flow-matching-policies` host minutes 450→660, `b10p3` month-10 plan header lock moved from the "Current" line to its `## Batch-10 PR3` section. No other lock relaxed.

## Models / reproducibility

opencode free models were tried first with a toy brief (`/workspace/b13p3-opencode/`): `deepseek-v4.1-flash-free`, `glm-5.3-flash-free`, `mimo-v2.6-flash-free`, `longcat-2.5-free` all timed out (exit 124) with no file output; no MiniMax free model is listed by `opencode models`. Toys, tests and prose were written locally.

## Local validation

`tools/test_b13p3_mapvla_dforcing_toys.py`, month-10 `check.sh`, `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build. No workflow edits. Minutes **71 / 30270**.
