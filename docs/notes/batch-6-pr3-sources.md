# Batch-6 PR3 source/model audit

Verified 2026-11-06 10:50:07 Asia/Shanghai (UTC+8). Base `1fe1eac573c9fa4bfa1dc38367459071b94faee1` (PR2,21960). Proposal §9 read first, then H1/H7. Only this PR adds210+180=390: site22350 /71 lessons; M10 1860→2070, M8 2850→3030. No arithmetic mismatch.

All six pages were fetched, opened/read (full HTML converted to text), and curl-verified. Hashes identify the opened copies, not a promise of immutable unversioned URLs.

| source | final HTTP | opened HTML SHA256 |
|---|---|---|
| https://arxiv.org/abs/2410.21257 | 200 | `b7052d4414adaf6a17d9d6a26242abcb9da7269ef30ac50ac63038fe3a7de6d2` |
| https://arxiv.org/html/2410.21257 | 200 | `6565f35721b3b1bedb74ed27f9131510674767a3a255706f208f834d1acd62d5` |
| https://arxiv.org/abs/2405.07503 | 200 | `aab0b9d683c45d51d05be608bf32e1f3b0ac3480db74f61821ca98cf16ea6159` |
| https://arxiv.org/html/2405.07503 | 200 | `6d19d710f8fda667f9c078b976fcc8d2939f2fccc91ca59734a57d31e44dd71f` |
| https://arxiv.org/abs/2503.05833 | 200 | `e058d8b604f7d0c815ee1fb0fb16db8a47affec187b88e4872725cba22b6de12` |
| https://arxiv.org/html/2503.05833 | 200 | `94acf11964fb71722d2841081a320d294d1146106e5384e0f689c0ca9895b990` |

## Original-paper interpretation and limits

- **OneDP, Wang et al.** Reverse KL between diffused action distributions along the chain, with score-difference gradient; OneDP-S auxiliary score network / OneDP-D analytic case. Extra2%–10% pretraining cost and1.5→62Hz are 以论文为准, not measured. An eight-call analytic nonlinear-inverse teacher and polynomial MSE student are a **regression surrogate**, not that distribution/score objective. Student fit never receives eval starts/labels. Shared64 demos per seed / shared64 disjoint eval starts. Unequal240-vs2 updates is intentional underfit control, not convergence/sample-efficiency evidence. Independent plant success and actual call-count NFE; no wall-clock claim.
- **Consistency Policy, Prasad et al.** Self-consistency along a diffusion teacher's learned probability-flow trajectories, CTM plus denoising score matching; single/few-step preset chaining. Existing complete paragraph is preserved verbatim and extended, not replaced. Actual Consistency Policy is reading only; reduced NFE is not equivalent to reduced end-to-end latency.
- **Refined Policy Distillation, Jülg/Burgard/Walter.** PPO reward objective plus action-mean teacher MSE; fixed-variance Gaussian motivation belongs to the paper, not our Bernoulli surrogate. Our tabular REINFORCE uses terminal reward and supervised teacher-MSE gradients on visited states, not PPO, critic, clipped objective, VLA weights or ManiSkill. Teacher is deliberately imperfect and provably beatable by independent finite-horizon DP; BC is online mean-MSE imitation, not offline/categorical-MLE BC. Equal7680 ticks/80 updates/teacher queries; active visits differ and are reported. Common random tape, identical init, independent256-episode eval, fixed8/80 checkpoints; five seeds report mean/population sd/ranges, including early BC wins. No guaranteed method winner; teacher bias can hinder learning.

## Execution/setup deviations

- New branch/worktree `feat/onedp-rpd`, `/workspace/hl-b6p3`; node_modules hardlinked via cp -al (react/package.json shares inode622102 with hl-b6p2), not symlink.
- opencode free-model attempts in requested order: DeepSeek, GLM, MiMo each timed out after70s with no usable response. LongCat/MiniMax free model IDs absent from current catalog. Implemented locally; no CloudAgent used.
- No GPU, real policy, ManiSkill, server, robot, original KL objective or PPO executed: 本页未运行. No Cal-ConRFT/advantage-filter/HIL-SERL/RTC rewrite. No workflow edits.
- Optional existing local dependency skips: OpenSCAD CAD, month-3 SDK comparison and month-7 MuJoCo checks depend on installed packages; actual full-suite result is recorded in the PR body. Existing expected outputs must remain byte-identical to base.
