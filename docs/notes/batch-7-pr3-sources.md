# Batch-7 PR3: source, scope and budget audit

Base `e5bd1fa1fb5276f5b8686907be9954991a022b1f` (`e5bd1fa`); branch feat/dpo-bimanual; separate /workspace/hl-b7p3 worktree, node_modules hardlinked using cp -al (not symlink). No workflows changed.

Opened and curl200 verified 2026-11-06 11:48 Asia/Shanghai (UTC+8); actual paper text read.

| Source | HTTP | Saved HTML SHA256 |
|---|---:|---|
| https://arxiv.org/abs/2305.18290 |200| `a4191d70e363cfbf66a090a42c0b19475263f051d48dd39a8d415a0671920880` |
| https://arxiv.org/html/2305.18290 |200| `46515bc6001158063f3da04695b1412099bc40b90c53f54bf1834581aefa15d1` |
| https://arxiv.org/abs/2511.05275 |200| `a96c548891f340feb1c498b419574a7d8aaa9f46de4a0ba707ac1dcd03cfc2b5` |
| https://arxiv.org/html/2511.05275 |200| `d15f80290e5e6083df72fe937856372a7d598b97191249000684b2b16d299cc3` |

## Scope / conflicting baseline lists

Latest request asks DPO vs reward-model+RL vs preferred-only BC. Proposal §9/H5 additionally specifies BC-all / binary-success-filter / preference. Include all five, not silently replace either set. Core three use only shared preferences; success-filter consumes extra binary TRAINING supervision (present in common records but ignored by core methods), explicitly not a pure-preference information-matched winner claim.

Equal budget is240 TOTAL gradient updates to one four-parameter block: RM+RL120 reward-fit then120 policy updates; others240 policy updates. Same64 pairs/full context batch each slot, fixed0.12 learning rate, beta=tau0.5. NOT equal FLOPs, parameter count or240 policy updates for RM+RL. Exact finite-action learned-reward-minus-KL gradient; no PPO or online env steps. Five seeds, disjoint256 eval contexts, clean/Bernoulli0.25 flip probability cases with common candidates/eval starts. Independent finite-difference DPO, reward-fit, preferred-BC and RL objectives, poisoned truth helpers and label invariance guard leakage. No SARM content removed/rewritten.

TwinVLA architecture statements come from actual section4 of opened arXiv HTML v2 (23 February2026): duplicate VLM, share vision encoder+DiT, per-arm proprioception encoders, joint QKV attention and shared-token MoE FFN routing. Bimanual fine-tuning still required, not zero-shot from duplication. No parameter/Hz/success figures copied as toy output. All paper numbers 以论文为准; real robots/weights/GPU/VLA/online RL 本页未运行.

Toy bimanual modes are analytic controls on a compliant shared-strap kinematic proxy, NOT TwinVLA architecture reproduction, rigid-body/force simulation or fleet navigation. Both arms/all modes receive full noisy state/goal schema, but independent deliberately factorizes the law. Same starts/gains/noise/horizon/caps, no latent gains/clean-state/future-noise oracle. Run all400 ticks even after arrival; success/collision episodes/span metrics/censoring explicit. All5 standard cases succeed with zero collisions; do not manufacture a failure or claim universal ranking. Separate impossible-goal unit test checks timeout accounting only.

## CLI attempts and placement

Free opencode order: DeepSeek/GLM/MiMo each timed out after35s without a completed audit; LongCat/MiniMax free IDs absent. Local implementation. MiMo only made read-only lookups in the prior worktree; no source changes from those attempts. No CloudAgent tool available.

All new symmetric en/zh code/stdout/exercises before sole final Summary.10.6 existing whole-lesson Summary retained plus one preference sentence;6.2 lacked Summary in both languages, so add a full whole-lesson one plus bimanual sentence. Correct month6/month10 plan headers.

## Arithmetic and preservation

No arithmetic mismatch:23190+210+210=**23610**,71 lessons; M6 **1350→1560**, M10 **2070→2280**. Both host lessons240→450. PR3 only, M4/M5 remain1830/1950.
All191 prior tracked expected files byte-for-byte preserved; add two new outputs only. No workflow edits.

## Local validation

Passed check_diagrams (23 diagrams /11905 checks, including independent derivatives/leakage/budgets/controllers), check_widgets (680), check_wokwi (8 diagrams /16 cards), check_quotes (362 code blocks /302 outputs), all eleven month harnesses, lint, next typegen, tsc --noEmit, production build and postbuild (178 pages, no leaked emphasis/percent/basepath issues), diff whitespace checks. Rendered RM+RL table checked for three columns in both locales.

Existing local optional environment skips unchanged: Month3 OpenSCAD CAD and SDK comparison; Month4 ROS2 Jazzy/colcon (both Python-only checks still ran); Month7 MuJoCo grip sweep. Both new stdlib toys always execute.
