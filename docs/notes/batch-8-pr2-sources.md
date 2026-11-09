# Batch-8 PR2 source, scope and validation audit

Base: 166392f7653ea59c306a5c3d1dbb0e8d912b5ffe (#133 merged). Proposal §9 PR2 locks: H3 9.8 IBVS +180, H4 9.5 escalation +150. No arithmetic mismatch: curriculum.ts on 166392f gives M9 2940 (visual-servoing 240, failure-recovery 180) and site 23910; after this PR M9 2940+180+150=3270 and site 23910+330=24240; 71 lessons. All 195 prior expected files under examples/*/expected remain byte-identical; two new expected files are added.

## Opened sources (curl -L, 2026-11-09, Asia/Shanghai UTC+8)

- `visp-ibvs-tutorial` — https://visp-doc.inria.fr/doxygen/visp-daily/tutorial-ibvs.html — HTTP 200. Read: e = s − s*, ṡ = L_x v_c, the 2×6 point interaction matrix, v_c = −λ L_x⁺ e, and per-iteration Z update from the estimated pose. Primary formula source for the lesson and toy.
- `wiki-visual-servoing` — https://en.wikipedia.org/wiki/Visual_servoing — HTTP 200. Secondary overview: IBVS/PBVS/hybrid taxonomy, camera retreat under large rotations, local minima and Jacobian singularity/condition-number checks.
- `btcpp-fallback` — https://www.behaviortree.dev/docs/nodes-library/FallbackNode — HTTP 200. Fallback ticks the next child after FAILURE; returns FAILURE when the last child fails.
- `btcpp-decorators` — https://www.behaviortree.dev/docs/nodes-library/DecoratorNode — HTTP 200. RetryUntilSuccessful num_attempts; -1 means infinite retries.
- Existing `inner-monologue-paper` (https://arxiv.org/abs/2207.05608, HTTP 200) kept as the lesson's existing pointer.

Not cited: proposal's LAAS course notes (https://homepages.laas.fr/afranchi/robotics/teaching/2018-2019/visual_servoing.pdf) return HTTP 200 but only an Anubis proof-of-work bot-check HTML page to curl, not the PDF; Inria HAL (inria-00350283) likewise served an Anubis page; IEEE Xplore 4015997 returned HTTP 202 with an empty body. None of these was read, so none is cited. BehaviorTree.dev lower-case paths (/decoratornodes/, /fallbacknode/) returned 404; the capitalised paths above are the working ones.

## Toy design

- `ibvs_interaction_matrix_toy.py`: synthetic free-flying camera, four coplanar points. PBVS and IBVS share the same noisy normalized points (σ=0.002), the same assumed model scale k, therefore the same homography pose and depth estimate (no true-depth oracle), λ=0.5, dt=0.1 s, 300-step cap, FOV ±0.4; five noise seeds with mean±sd. Scenarios: nominal, wrong_Z_k1.5, near_edge, roll_170, plus a two-point rank-deficient stack. The near_edge start was chosen from a random sweep of starts (0.28–0.38 initial FOV use) where the arms differed; in that sweep PBVS lost points in 19/150 starts and IBVS in 0/150 — a property of this toy, not a general claim. roll_170 shows IBVS camera retreat; wrong_Z shows PBVS converging to a wrong pose. No winner declared.
- `recovery_escalate_budget_toy.py`: synthetic 40-task stream × five seeds, hidden case mix, pre-drawn outcomes (common random numbers) and the same detect signal for all arms. A infinite retry (per-task bookkeeping deadline), B Retry(2)+Fallback, C capped ladder with operator budget 6; sweep 0/6/20. Explicit rung costs. Handoff fields escalate_reason, last_obs_summary, attempted_skills[]. Budget 0 reproduces B; autonomous successes of C equal B's. No winner declared.

Independent tests (tools/test_b8_ibvs_escalate_toys.py): finite-difference check of every interaction-matrix column, noise-free pose recovery and k-scaled translation, least-squares normal equations, noise-free wrong-scale PBVS final depth, two-point null-space count, common random numbers, budget-0 equivalence, autonomy share and handoff schema, livelock only where the primary cannot succeed.

## Models / reproducibility

Tried opencode/deepseek-v4.1-flash-free (no content within 40 s), glm-5.3-flash-free and mimo-v2.6-flash-free (both returned only the 2×6 interaction-matrix function, matching ViSP). LongCat and MiniMax free IDs were absent from `opencode models`. Everything else was implemented locally. Worktree /workspace/hl-b8p2 with node_modules hardlinked via `cp -al` (real directory, not a symlink).

## Local validation

check_diagrams, check_widgets, check_wokwi, check_quotes, month 1–11 check.sh, lint, next typegen, tsc --noEmit, production build and the independent test suite. Existing optional guards (OpenSCAD, ROS Jazzy, MuJoCo) unchanged; new stdlib comparisons are unguarded. No workflow edits.
