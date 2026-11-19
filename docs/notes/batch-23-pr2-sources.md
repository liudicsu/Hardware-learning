# Batch-23 PR2 sources — AMCL, generalized advantage estimation

Base: `5930053b6e4298a41f13906160965fd453365707` (batch-23 PR1 #193 merged; site **40500**, M4 **3390**, M7 **3510**).
This PR: site **40500→40860** (40860=40500+180+180), M4 **3390→3570**, M7 **3510→3690**, catalogue still **71**. Hosts: `slam-nav` 810→990, `rl-foundations` 630→810. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All returned HTTP **200** (2026-11-13 UTC+8); the bodies below were read.

| id | URL | revision / version | What was used |
|---|---|---|---|
| wiki-mcl | https://en.wikipedia.org/w/index.php?oldid=1279828307 (Monte Carlo localization) | 1279828307 | Also known as particle filter localization; estimates position and orientation on a given map with a particle filter, each particle a hypothesis; uniform start; motion update with noise; sensor update by weighting and resampling; multimodal belief (one peak per similar door); particle deprivation: converged on a wrong state or kidnapped after convergence, the algorithm cannot recover, more likely with few particles (M ≤ 50), randomly added particles as a remedy; KLD sampling adapts the particle count. |
| ros-amcl-archive | https://web.archive.org/web/20241226202453/https://wiki.ros.org/amcl | Wayback snapshot 2024-12-26 | amcl: probabilistic 2D localization implementing adaptive (KLD-sampling) Monte Carlo localization against a known map; `min_particles` 100, `max_particles` 5000, `kld_err` 0.01; `recovery_alpha_slow` / `recovery_alpha_fast` default 0.0 (disabled), 0.001 / 0.1 suggested, for adding random poses; `laser_model_type` default `likelihood_field`. |
| gae-paper | https://arxiv.org/abs/1506.02438 and https://arxiv.org/pdf/1506.02438 | v6 (20 Oct 2018) | Title *High-Dimensional Continuous Control Using Generalized Advantage Estimation*; abstract-page authors in order: John Schulman, Philipp Moritz, Sergey Levine, Michael Jordan, Pieter Abbeel; the PDF byline writes Michael I. Jordan (the same person, same order, not a reordering). GAE(γ, λ) as the exponentially-weighted average of k-step estimators, a discounted sum of TD residuals (Eq. 16); λ = 0 the one-step residual (Eq. 17), λ = 1 the discounted return minus V (Eq. 18); γ-just / bias / variance statements; cart-pole fastest improvement for intermediate λ in 0.92–0.98; the one-step return (λ = 0) gave excessive bias and poor performance. |

Not cited: the live `wiki.ros.org/amcl` page (bot wall, no readable body) and the Nav2 `configuring-amcl` URL (page moved); the Wikipedia Particle filter article was not used. Every particle count, recovery rate, noise level, map size and value error in the toys is a **declared toy parameter**, printed or stated as declared; ROS defaults are quoted 以原文为准 and are not what the toy uses.

## Toys

- `examples/month-4/slam-nav/amcl_particle_filter_localization_toy.py` → `examples/month-4/expected/amcl_particle_filter_localization_toy.txt`
- `examples/month-7/rl-foundations/gae_lambda_advantage_toy.py` → `examples/month-7/expected/gae_lambda_advantage_toy.txt`

Common random numbers, five seeds, stdlib CPU only, half-up rounding on the shortest decimal repr, byte-identical output on rerun (also under Python 3.12). Neither toy has a continuous-time integration step. Every m±sd in the new lesson prose, the new Summary sentences, the month-4 / month-7 plans and this note is printed in `expected/`.

## Regime results

### H3 AMCL (`amcl_particle_filter_localization_toy.txt`)

- Declared toy parameters: 10×6 m room with three boxes, 12×2 m corridor; heading known; 4 axis beams, SIG_Z 0.1 m, R_MAX 8 m; step 0.3 m, scale noise 0.05, additive 0.02 m; SIG_L 0.2, Z_HIT / Z_RAND 0.9 / 0.1; EPS 0.05, Z_Q 2.326, 0.5 m bins; B 100–600 particles, recovery A_SLOW 0.05 / A_FAST 0.5; C 30 particles, recovery off; particles move by the command without added noise; success when the mean error of the last 5 steps is under 0.5 m.
- Hand calc (printed): KLD 65.8404 → 100, 216.9395, 749.3302 → 600; likelihood floor 0.0125; drift 0.1250 m per axis after 25 steps.
- distinctive_unknown: B−A err -2.9468±1.1879 and success 1.0000±0.0000, clear, 5/5; C−B err 3.1153±2.1111 (1 of 5 opposite), C−A err 0.1685±3.2395 near-tie.
- known_short: B−A err -0.0157±0.0066, clear, 5/5 (declared near-tie did not hold); C−B err -0.0021±0.0053 near-tie; success ties.
- kidnapped: C−B err 4.4777±1.9964 and success -1.0000±0.0000, clear, 5/5, **kept**; B−A err -4.4787±2.0026; C−A err -0.0010±0.0486 near-tie.
- corridor_multimodal: B−A err -2.3561±1.0515, clear, 5/5; C−B err 2.0126±3.1586 near-tie; C−A success 0.6000±0.5477.
- Alternatives (same seeds, written before the first run, not adopted): B recovery off in kidnapped X−B err 4.4964±1.9985; N_MAX 300 X−B err -0.0115±0.0566 near-tie; C with recovery in kidnapped X−C err -2.7986±1.3081.

### H4 GAE (`gae_lambda_advantage_toy.txt`)

- Declared toy parameters: GAMMA 0.99, P1 0.5, C_R 1, SIG_R 1, N_EP 16, M_DRAW 40, SIG_V 0.3, λ 1 / 0.95 / 0; H 50 / 1 / 30.
- Hand calc (printed): g_true 9.8748 / 0.2500 / 5.6038; effective horizon 16.8067 (λ = 0.95) and 100.0000 (λ = 1); the H = 1 identity.
- long_noisy: B−A grad_var -6.7764±0.6108, clear, 5/5; C−B grad_var -4.1182±1.5598 and grad_mse -4.0223±1.5024, clear (not declared).
- one_step: every pair a tie, identical on every seed, on both metrics.
- delayed_coarse: C−B grad_mse 18.1442±3.3853 and C−A 18.2344±4.5531, clear, 5/5, **kept**; B−A grad_mse 0.0902±3.7467 near-tie; B−A grad_var -7.6030±2.3450 clear.
- Alternatives (same seeds, written before the first run, not adopted): λ 0.9 X−A grad_var -8.4984±1.0608; λ 0.98 X−A grad_var -4.2012±0.4197; C with the step-indexed true value plus errors X−C grad_mse 0.2929±0.5736 near-tie.

## Post-hoc choices

None for either toy; every parameter, regime and printed alternative was written before the first run and run on the same seeds.

## Code changes after the first run

Print-only, after the first run, no retune: both declared-parameter lines were extended so the lesson-prose values are printed into `expected/`. AMCL now also prints `bin_size=0.5000 n_steps=25 n_steps_short=6 kidnap_after=10 tail_steps=5 room=10.0000x6.0000 corridor=12.0000x2.0000`; GAE now also prints `long_noisy_H=50 delayed_coarse_H=30`. Result blocks are byte-identical to the first run; no model, metric or parameter was changed.

## Mismatch with §9

- AMCL known_short: the declared A/B near-tie on err did not hold (B−A -0.0157±0.0066, clear, B better). Kept on the page as declared.
- AMCL corridor_multimodal: the declared possible failure of B did not occur; in this toy the 12 m corridor keeps an end wall within the 8 m beam range from every point (hand calculation, labelled 手算 on the page).
- GAE: every declared regime held. Not pre-declared and reported: λ = 0 wins on long_noisy, and λ = 0.95 does not beat λ = 1 on grad_mse in delayed_coarse.
- The GAE paper's "以论文为准" wording in §9 appears on the pages as 以原文为准 next to every paper figure; the toy output prints 以论文为准.
- Plan wording: +180 per host as 30+25+50+40+35.

## Lock changes

Tipped site-total, host-minute and Current-header locks only. New lock block added (toys, expected, CRN, label order, difference directions, the cited 0.92 paper value with 以原文为准, opened-source cards with oldid / Wayback URL / full author names, plans, README, sources, no process labels in the new toys and outputs, the OctoMap wording untouched) plus `tools/test_b23p2_amcl_gae_toys.py`.

- README `/40 500/` and `约 40 500 分钟` → `/40 860/` and `约 40 860 分钟`.
- Curriculum sum checks `40500` → `40860`; month-total lists M4 3390→3570, M7 3510→3690.
- Host-minute locks for `slam-nav` (810→990) and `rl-foundations` (630→810) in earlier cases.
- month-4 / month-7 plan Current header locks → Batch-23 PR2 (**M4 3570**, **M7 3690**); historical section markers kept.

No lock relaxed.

Real robot / Nav2 AMCL / live ROS wiki, paper locomotion / GPU / SB3: 本页未运行. Wikipedia, archived ROS wiki and paper figures 以原文为准.
