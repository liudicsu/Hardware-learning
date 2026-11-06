# Batch-5 PR3 — source, protocol and limitation audit

2026-11-06 (Asia/Shanghai, UTC+8). Base `3beda7dba69a38c21fd48af87c4034e68a53cb86` (merged #122). New worktree `/workspace/hl-b5p3`, branch `feat/cal-conrft-mtc`; dependencies hardlinked with `cp -al`, not a symlink. Read proposal H1/H7 and §9 LOCKED before implementation.

## Actually opened and curl-verified

| Source | HTTP | Use |
|---|---|---|
| https://arxiv.org/html/2502.05450 | 200 | ConRFT original: offline Cal-ConRFT critic + consistency BC/Q head; online HIL-ConRFT interactions/interventions; experimental/analysis caveats. |
| https://arxiv.org/abs/2502.05450 | 200 | Existing resource metadata/link, reverified. |
| https://arxiv.org/html/2303.05479 | 200 | Cal-QL original: calibration definition, conservative push-down mask, function-approximation caveat, dataset dependence and appendix implementation/theory. |
| https://arxiv.org/abs/2303.05479 | 200 | New primary resource link. |
| https://moveit.picknik.ai/main/doc/tutorials/pick_and_place_with_moveit_task_constructor/pick_and_place_with_moveit_task_constructor.html | 200 | Primary MTC tutorial: result flow, containers, CurrentState/planning scene, plan versus execute, failure introspection. Does not promise our cache algorithm. |

Full readable pages opened this turn, not just HTTP checks. Paper figures such as96.3 % are 以论文为准. No paper benchmarks claimed as site-measured.

## H1: what is actually learned

- Four-state, three-action offline MDP; reward1 only at goal, wrong-key0, abort0.2 is not success; stochastic advance0.9, gamma0.95.48 behavior episodes per seed,1071–1075; batches include failures, and all declared states have data. Train never queries transition dynamics or evaluation rollouts.
- Same immutable batch, state weights, zero actor initialization and1000 full-batch actor updates for BC-only/CQL+BC/Cal-QL+BC. Actor beta=1, eta=0/2/2; critic TD weight1, conservative alpha1, LSE temperature0.1; learning rates0.03/0.06. Two RL critics each1000 updates; BC has no critic and Q=NA. Equal outer/actor updates, not equal FLOPs or total optimizer work.
- Discrete temperature-logsumexp CQL variant with unchanged data-action compensation and TD targets. Cal-QL applies max(Q,V_MC) **inside the conservative penalty**, with zero push-down derivative below reference. V_MC is per-state behavior return-to-go from the same batch, stop-gradient. No evaluation/optimal-value reference, no post-hoc output clamp or Bellman-target clamp.
- Default critic is deliberately restricted Q(s,a)=w_s*(1,1.2,1.4)[a]. This selected diagnostic fixture is **not an unbiased leaderboard**. It exposes coupled conservative-gradient/representation error; it cannot fit all true action rankings. Both competing RL arms share the restriction. An executable `--tabular` control uses the same MDP/data/updates/losses with a full table, with a second expected output and check hook.
- Restricted CQL mean policy Q0.135372 versus MC reference0.439094; Cal-QL0.419844. Raw state-average gaps remain negative (e.g.-0.092253 at seed1072), explicitly printed: the **penalty argument** is lower-bounded, not every raw learned Q. This follows the paper's finite-optimizer/function-approximation caveat, rather than inventing a hard certificate.
- Success mean±population-SD: BC0.2142±0.0494, CQL0.1958±0.0400, Cal-QL0.1628±0.0305. Retain this unfavorable Cal-QL result. In full-tabular control CQL/Cal-QL Q0.457688/0.604030 versus same reference; success0.2786/0.2748. Large CQL under-scaling is not universal. All15 rows per representation, min/max, returns and lengths retained.
- Shared1000 evaluation action/transition uniform streams per seed; stochastic extraction for all arms. Q/reference means uniformly weight four dataset states and are not start-state evaluation returns or same-policy prediction errors.
- Regression checks execute both representations, compare exact expected outputs, test data/reference parity, finite-difference the mask derivative and confirm CQL/Cal-QL training becomes identical when alpha=0. No online phase, consistency head, Octo/Franka/GPU or real robot; online-dip mitigation is reading only. Existing advantage-filter and10.6 outputs unchanged.

## H7: memory, failure and accounting

- Same eight deterministic planning requests, candidate order, root context and current-world predicate for full replanning / cached prefix / bounded8. No per-arm world changes, future cache or executed-motion/reset trick. Only the current request reaches Search.
- Actual depth-first candidate search, not an assigned cost table. A cached first-three-stage prefix came from past accepted results. Every cached edge is revalidated at one expansion unit per predicate check, including rejected nodes. Invalidating an edge drops all dependents. Failed suffix search additionally pays exhaustive root fallback; no free global infeasibility label.
- Stable repeat costs8(full) vs2+3=5(cache). Blocked place costs18(full) vs20+3=23(cache), including fallback. World change makes cached route0 actually fail validation:1 check+10 root search=11 vs full10; final task recovers on route1. This is a **cached-candidate validation failure**, not unsafe execution or an intentionally hidden whole-task failure. Both routes blocked causes a second stale failure.
- Full6/8,73 expansions; cache6/8,56 search+14 revalidation=70,2 stale-prefix failures; bounded2/8,58 expansions,5 budget exhaustions. Exhaustion is unknown, not proof of infeasibility. No universal winner or seconds/speedup claim. New counts do not reinterpret legacy stage_graph_toy mock seconds.
- Runtime regression checks solution validity, total=search+revalidation, cap compliance, stale rejection/fallback costs and prefix invariance when the future stream is removed. Cache is a site-defined strategy sketch, not an MTC automatic-caching API. Real MoveIt/Panda/SO-101 本页未运行.

## Minutes and placement

20700+210+180=**21090**,71 lessons. M10=1650+210=**1860**; M9=2550+180=**2730**. Independent full sum: M1–M11 =870/1650/1470/1620/1800/1350/2070/2670/2730/1860/3000. No mismatch. These are final batch totals applied only in PR3.

Both target lessons already had whole-lesson Summary blocks. Preserved their full prior content and added one symmetric sentence per language; all new sections/code/stdout/exercises precede the sole final Summary. Reachable regression locks before the sole final exit preserve old locks and update current minute totals. No pre-existing expected file modified.

## Tools and validation

opencode DeepSeek and GLM free models returned planning-only review comments, no edits; MiMo timed out20s (exit124). Fresh catalog lacks LongCat/MiniMax free models. Reviewed suggestions against primary equations: in particular, max belongs in the conservative regularizer, **not Bellman targets**, despite ambiguous model-review wording. Implementation local in the requested worktree.

PASS: diagrams **11141 checks/0failed**; widgets680/0; Wokwi8 diagrams/16cards/0problems; quotes334 blocks/274 simulated outputs/0problems; full M9/M10 check.sh including all new outputs; lint; next typegen; tsc --noEmit; production build/postbuild including178 pages' markdown/percentage/base-path checks; git diff --check. PR CI status is verified after push, not invented in this note.
