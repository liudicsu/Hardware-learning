# Batch-4 PR2 source and scope audit

Checked 2026-11-06 (Asia/Shanghai, UTC+8). No standard full text purchased/read.

| Source | curl -L result | What was actually checked |
|---|---|---|
| https://arxiv.org/html/2403.02751v1 | 200 | Theorem 1: disjoint iff EXISTS s in (0,1), K(s)>1. Corollary 1: finite samples conservative. Direct diagonal formula uses obstacle Sa/(1-s), sphere Sb/s. Ignore nearby ambiguous “negativeness” prose. |
| https://www.iso.org/standard/73481.html | 403 | Public WebFetch succeeded: ISO 13849-1:2023, Edition 4, publication 2023-04, status Published, stage 60.60. 2015 shown withdrawn. The catalogue does not assign PLr to particular applications. This is metadata, not access to the paid standard. |
| https://www.tuv.com/landingpage/en/robotics/main/standard-update-alert/ | 200 | SECONDARY: 10218-1/-2:2025 scope distinction, Class I/II, collaborative-operation/15066 incorporation into Part 2. No thresholds or clause text taken. |
| https://www.ibf-solutions.com/en/seminars-and-news/news/new-standards-for-industrial-robots-en-iso-10218-1-and-2 | 200 | SECONDARY cross-check of 2025 industrial-robot standards update. |
| https://www.pilz.com/en-GB/support/law-standards-norms/functional-safety/en-iso-13849-1 | 403 | Public WebFetch succeeded: SECONDARY S/F/P risk graph and achieved-PL evidence categories; 2023 P-selection discussion. Used for literacy, not normative clauses. |
| https://www.pilz.com/download/open/Pos_Functional_safety_1003920-EN-06.pdf | 200 | SECONDARY poster, downloaded and pdftotext checked. It labels 13849-1 “probably 2023”, so NOT used to establish the current edition; ISO catalogue is the edition evidence. |

The curl 403s are reported honestly, not silently treated as successful curl verification. Public readable fetch was the fallback for those pages. No credentials involved.

## Numerical and scope limits

- K(s)>1 certifies separation; finite-s can only miss separation witnesses in exact arithmetic. Floating-point tolerance biases collision but is not interval certification.
- Truth is an independent exact-distance formulation with a 100-bisection numerical solve; not sampled K(s), not a physical-world ground truth. Gaussian opacity>=0.5 and 2-sigma truncation define the same scene for all arms. Boundary/tangency tests included.
- Query cost is deterministic axis-kernel evaluations, not wallclock; different kernels have different operations. 5/20 Hz are paper claims, 以论文为准.
- PLr toy requires explicit user JSON; fixture values are illustrative, not inferred from application names. Base eight-branch graph only, no probability adjustment or Type-C override. Missing fields insufficient_data; invalid values invalid_input. Achieved PL/category/MTTFd/DCavg/CCF and full certification remain out of scope.
- ISO 10218:2025 changes are labelled secondary, never transplanted onto SO-101 as force limits or certification. No clause numbers or 15066 force/pressure tables supplied.

## Arithmetic correction to implementer brief

Base main 2b6b9c2: M7=1650, M8=2490, site=19050. H1 adds210 and H6 adds180: **M7=1860**, M8=2670, site=19440,71 lessons. Requested M7=2070 belongs to the full-batch target after PR3 H2 adds another210; forcing2070 in PR2 would make site19650 or require unrelated reductions. PR2 preserves the locked lesson deltas and reports this discrepancy rather than falsifying totals.

## CLI fallback

Tried free DeepSeek, then GLM, then MiMo through opencode; each produced only its startup banner with no edits/tool activity (bounded waits, stopped own stalled jobs). LongCat and MiniMax free models were not in the CLI model catalogue. Implemented locally; no CloudAgent used.

## Local verification

- `check_diagrams`: 23 diagrams / 10691 checks / 0 failed, with the PR2 block before the sole final process.exit.
- `check_widgets`: 680 checks / 0 failed; `check_wokwi`: 8 diagrams,16 cards / 0 problems; `check_quotes`: 316 code blocks,268 simulated outputs / 0 problems.
- eslint, next typegen, tsc --noEmit and production build passed. node_modules is a hardlinked copy, not a symlink.
- Month7/8 check.sh outputs match, including both new toys. Existing optional Month7 grip_sweep skipped because default python lacks mujoco; existing handeye NumPy case ran. No new dependency was needed.
- Additional independent scratch fuzz (seed751,8 random scenes,500 queries each): 4000 queries,0 false-safe for AABB/15-s/1-s tests; 1-s ellipsoid sampling produced66 false alarms, demonstrating finite-s conservatism. This is additional evidence, not certification or an all-scenes proof.
