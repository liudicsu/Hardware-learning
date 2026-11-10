# Batch-16 PR2 sources / 来源记录

Base `208706f` (main after #165; site **32820**). This PR: M5 kinematics-ik 570→750 (+180), M7 rl-foundations 450→630 (+180); site **32820→33180**; M5 2670→2850, M7 2610→2790; still 71 lessons. Proposal: `batch-16-proposal.md` PR2 and §9 locks.

## Opened sources

All fetched with curl on 2026-11-10 (Asia/Shanghai), HTTP 200, then read as text.

| Resource id | URL | Version | Lines read (text extract) | What is used |
|---|---|---|---|---|
| `wiki-poe` | https://en.wikipedia.org/wiki/Product_of_exponentials_formula | rev 1356253030, article body present (`mw-parser-output`) | 717, 719, 735–758, 763, 766 | PoE as an alternative to DH; advantages "uniform treatment of prismatic and revolute joints, definition of only two reference frames, and an easy geometric interpretation from the use of screw axes"; twist ξ = (ω, −ω × q) (prismatic (0, v)); Rodrigues e^(ω̂θ); translation (I − e^(ω̂θ))(ω × v) + ωωᵀvθ; gd = e^(ξ̂1θ1)⋯e^(ξ̂nθn) gst(0); DH needs careful frame selection and has several conventions, PoE twists ignore adjacent joints; no one-to-one mapping between the two. The text says "introduced by Roger W. Brockett in 1984" while its cited reference is dated 1983; the page says 以原文为准. |
| `td3-paper` | https://arxiv.org/abs/1802.09477 | abs page: citation_title "Addressing Function Approximation Error in Actor-Critic Methods", authors Fujimoto, Scott; van Hoof, Herke; Meger, David, date 2018/02/26; PDF body arXiv:1802.09477v3 [cs.AI] 22 Oct 2018 (pdftotext, xref warning, text reconstructed) | abstract 1–30; eq. (10) 239; Algorithm 1 372–399; eq. (15) 422; Table 1 483ff; Table 2 536–552; 506–508; hyper-parameter table 834–841 | overestimation persists in actor-critic; clipped double Q (min of two critics); delayed policy updates d = 2; target smoothing ε ~ clip(N(0, 0.2), −0.5, 0.5); τ = 0.005, exploration N(0, 0.1), batch 100, 10 seeds, 1 M steps. Table 1 (以论文为准): HalfCheetah TD3 9636.95 ± 859.065 vs DDPG 3305.60; InvertedPendulum all 1000.00 (tie); InvertedDoublePendulum DDPG 9355.52 > TD3 9337.47. Table 2: TD3 − DP 9590.65 > TD3 9532.99 (HCheetah), 4695.50 > 4565.24 (Walker2d); TD3 − CDQ 9792.80 > TD3 on HCheetah. Line 506: training the actor for too few iterations "would cripple learning". |

Paper numbers are marked 以论文为准 and Wikipedia statements 以原文为准 on the site. No real arm, MuJoCo, Gym, SB3 or GPU run (本页未运行).

## Toy design

- `examples/month-5/kinematics-ik/poe_vs_dh_fk_toy.py`: the lesson's three-joint SO-101 model (H 0.1166, L1 0.1160, L2 0.1350 m). Arms A_dh (standard DH rows (q0, H, 0, +90°), (q1, 0, L1, 0), (q2, 0, L2, 0) plus a fixed Rx(−90°) tool rotation) / B_poe (space-frame PoE, twists ξ = (ω, −ω × q), home pose M) / C_poe_tilt (B with the elbow axis tilted 2° about x). Truth: the lesson's closed form. Common random numbers: 200 configurations and the encoder noise per (regime, seed), shared by every arm, seeds 0–4. Regimes matched, near_singular (q2 within ±1°), encoder_noise (0.2° sd). No integration step; correctness criterion max ||T_DH − T_PoE||_F and ||RᵀR − I||_F below 1e-12 asserted on noise-free regimes.
- `examples/month-7/rl-foundations/td3_clipped_double_q_toy.py`: plant s′ = clip(s + 0.5a, −2, 2), reward −s′² − 0.1a² + noise, reset every 10 steps (not terminal). Critics linear in (1, s, a, s², a², s·a); actor a = clip(k·s + b, −1, 1). Arms A_ddpg / B_td3 (two critics, min, smoothing, d = 2) / C_cdq_nodelay (B with d = 1). Common random numbers: separate streams for start states, exploration, reward noise, minibatches, smoothing noise and initial weights, shared by every arm, seeds 0–4. Regimes noisy_reward (σ_r 1.0, γ 0.8), easy (0, 0.8), bandit_no_bootstrap (0, 0; pre-declared tie-or-lose regime). No integration step; critic SGD stability LR·|φ|² < 2 asserted (max |φ|² 27.0, LR·max 0.2700, limit LR 0.0741; tests at 0.98× / 1.02×); divergence flag at ±1e4 never fired.
- Labels as in batch-15/16 (tie → numerically zero below 1e-9 → near-tie |m| ≤ sd → consistent, small under 20 % of the smaller arm mean else clear, with sign count).

## Results (k/N = seeds with the reported sign)

PoE (paired):
- matched: B−A pose −2.712e-18±3.790e-18 and tip 1.506e-14±1.371e-15 mm **numerically zero**; C−B pose 0.0507±0.0025 and tip 3.3504±0.1425 mm clear 5/5 (wrong twist loses).
- near_singular: B−A numerically zero (pose 8.369e-18±4.354e-18); C−B tip 0.0397±0.0020 mm clear 5/5 (tiny but consistent).
- encoder_noise: A and B both 0.8681±0.0357 mm from truth; B−A numerically zero (−1.776e-16±1.363e-15 mm); C−B tip 2.6701±0.0984 mm clear 5/5.

TD3 (paired):
- noisy_reward: B−A bias −0.3451±0.0468 clear 5/5; absbias −0.0965±0.2627 near-tie (1/5 opposite); ret −0.0002±0.0488 near-tie (1/5 opposite). C−B bias 0.2726±0.0443 clear 5/5. C−A bias −0.0725±0.0064 clear 5/5, absbias −0.0519±0.0484 clear (1 of 5 opposite), ret near-tie.
- easy: B−A bias −0.3765±0.0563 clear 5/5, absbias −0.2847±0.1360 clear 5/5, ret 0.0198±0.0554 near-tie (3/5 opposite). C−B bias 0.3022±0.0489 clear 5/5. C−A bias −0.0743±0.0090 clear 5/5, ret near-tie.
- bandit_no_bootstrap: **B−A ret −0.2140±0.0683 clear 5/5 (TD3 loses)**; absbias +0.0064±0.0024 clear 5/5 (TD3 loses); C−A **tie, identical on every seed** on all three metrics.

## Post-hoc choices

- PoE toy: none. The 2° tilt, ranges, noise and the 1e-12 bound were fixed before the first run; all regimes printed.
- TD3 toy: after the first full run, the C−A comparison line was added to the printed pairs (marked `# C-A added after the first run` in the source, stated on both language pages). Reason: the first run showed C's numbers equal to A's in bandit_no_bootstrap. No parameter, regime or seed changed; all other lines are byte-identical. Alternative not taken: leaving C−A unprinted and only stating the equality in prose.
- The toy hyper-parameters (τ = 0.01, linear critics, 3000 steps) are the toy's own, not the paper's (τ = 0.005, 400-300 networks, 1 M steps); stated on the page.

## Mismatch with §9

- TD3, "overestimation regime consistent TD3 win": matches for the signed bias (clear, 5/5) in noisy_reward, but absbias and return there are **near-ties**, not wins. Reported as is.
- TD3, "easy near-tie": return is a near-tie as locked, but bias and absbias are **clear** TD3 wins in easy (the overestimate comes from the critic chasing the actor, not from reward noise). Reported as is.
- TD3 tie-or-lose regime: present (bandit_no_bootstrap, TD3 loses return clearly 5/5; C ties A exactly). Consistent with the paper's own Table 2, where removing the delay scores higher on two tasks.
- PoE: matches §9 (DH vs PoE numerically zero, never labelled clear; wrong twist a consistent loss). Note: it is "numerically zero", not "tie", because the two products round differently.

## Lock changes

- New `b16p2` block in `tools/check_diagrams.mjs` (exact source/stdout in sections, label rules, regime lines, markers, en/zh symmetry, Summary sentences, resources, plan headers, sources note, README; DH vs PoE never labelled clear / 明显) and `tools/test_b16p2_poe_td3_toys.py` (14 tests: labels, lesson config, DH = PoE to 1e-12, independent twist exponential, wrong twist and its zero at q2 = 0, CRN, no-integration-step statements, SGD bound at 0.98× / 1.02×, clipped min ≤ both critics, independent MC return, A = C without bootstrapping, outputs).
- Tips moved: site total 32820→33180; month table M5 2670→2850, M7 2610→2790; README `32 820`→`33 180` (en + zh); host-minute tips kinematics-ik 570→750 (b7p2, b12p2 cases) and rl-foundations 450→630 (b4p3 case); b14p2 month-5 and b15p2 month-7 plan-header locks repointed from the "Current" line to their `## Batch-14 PR2` / `## Batch-15 PR2` headings (all other strings kept).
- The opened-source regex in the new block accepts 以原文为准 or 以论文为准 (the paper card uses the latter); the older blocks are unchanged.
- No lock relaxed; `.github/workflows` untouched.

## Models / reproducibility

- opencode free models were tried first with one prompt asking for both toys (150 s timeout each): deepseek-v4.1-flash-free, glm-5.3-flash-free, mimo-v2.6-flash-free and longcat-2.5-free timed out (exit 124, no files); minimax-m2.5-free returned "Unexpected server error" (exit 1, no files). Both toys, the tests and the page text were written locally.

- Reproduce: `python3 examples/month-5/kinematics-ik/poe_vs_dh_fk_toy.py`, `python3 examples/month-7/rl-foundations/td3_clipped_double_q_toy.py`, `python3 tools/test_b16p2_poe_td3_toys.py`, `bash examples/month-5/check.sh`, `bash examples/month-7/check.sh`, `node tools/check_diagrams.mjs`. Common random numbers, seeds 0–4, stdlib only.

## Local validation

See the PR description for the command list and results (check_diagrams, check_widgets, check_wokwi, check_quotes, month check.sh, unit tests, lint, typegen, tsc, build + postbuild, CI=1 build).
