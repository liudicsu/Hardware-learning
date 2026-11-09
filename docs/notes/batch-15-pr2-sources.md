# Batch-15 PR2 source, scope and validation audit

Base: `d0da082` (batch-15 PR1 merged as #161; site **31710**). Proposal `batch-15-proposal.md` §9 PR2 locks: H3 4.6 slam-nav DWA vs RPP-like +180, H4 7.3 rl-manipulation-sim HER +180. No arithmetic mismatch: curriculum.ts on base gives M4 2490 / M7 2430 / site 31710 (slam-nav 450, rl-manipulation-sim 240, as the proposal states); after this PR M4 **2670**, M7 **2610**, site **32070**; 71 lessons. No new slugs, no Month 12. All prior expected files remain byte-identical; two expected files are added.

## Opened sources (curl -L + body read, 2026-11-10, Asia/Shanghai UTC+8)

- `fox-dwa-1997` / Fox, Burgard, Thrun, "The Dynamic Window Approach to Collision Avoidance": https://www.ri.cmu.edu/pub_files/pub1/fox_dieter_1997_1/fox_dieter_1997_1.pdf, HTTP 200, PDF body read via pdftotext. Circular-arc search space (v, ω); eq. 14 admissible velocities v ≤ √(2·dist(v, ω)·v̇_b) ∧ ω ≤ √(2·dist(v, ω)·ω̇_b); eq. 15 dynamic window; objective G = σ(α·heading + β·dist + γ·vel), terms normalised to [0, 1], α = 2.0, β = γ = 0.2 (Fig. 10 text); smoothing increases side clearance; interval 0.25 s; example accelerations 50 cm/s² and 60 deg/s². 以原文为准.
- `macenski-rpp-2023` / Macenski, Singh, Martín, Ginés, "Regulated Pure Pursuit for Robot Path Tracking": https://arxiv.org/pdf/2305.20026 (v1), HTTP 200, PDF body read via pdftotext (abstract page https://arxiv.org/abs/2305.20026 also HTTP 200). κ = 2y / L²; curvature heuristic and proximity heuristic applied to linear velocity, "and we take the maximum of the two" (§3). The toy takes the **smaller** (conservative); the en/zh prose says so.
- `nav2-rpp-readme` / Nav2 `nav2_regulated_pure_pursuit_controller` README: https://raw.githubusercontent.com/ros-navigation/navigation2/main/nav2_regulated_pure_pursuit_controller/README.md, HTTP 200, body read. Active collision detection projects the command for `max_allowed_time_to_collision_up_to_carrot`, "limited to maximum distance of lookahead distance selected"; `regulated_linear_scaling_min_radius`, `regulated_linear_scaling_min_speed`, approach slowdown, velocity-scaled lookahead. 以原文为准.
- `her-andrychowicz-2017` / Andrychowicz et al., "Hindsight Experience Replay": https://arxiv.org/pdf/1707.01495 (v3), HTTP 200, PDF body read via pdftotext (abstract page also HTTP 200). Sparse binary rewards, any off-policy algorithm, implicit curriculum; goal influences actions not dynamics (§3.3); strategies final / future / episode / random, future with k = 4 or 8 best, k above 8 degrades (§4.5); bit-flipping DQN without HER n ≤ 13, with HER up to 50; §4.4 shaped rewards fail for DDPG and DDPG+HER; reward −[f_g(s) = 0]. 以论文为准.
- Wikipedia — Dynamic window approach: https://en.wikipedia.org/wiki/Dynamic_window_approach, HTTP 200, HTML body verified (mw-parser-output; revision 1364437479). A stub; named in the prose as a secondary pointer only, not carded.
- Existing `slam-nav` Nav2 / RPP controller prose and `examples/month-4/slam-nav/m4_nav/config/nav2.yaml`, and `rl-manipulation-sim` `reward_shaping.py` (sparse 0.000 / dense 1.000 at seed 7): read in-repo and extended in place.

Not cited: the Nav2 docs RPP configuration page (https://docs.nav2.org/configuration/packages/configuring-regulated-pp.html) returned a "Page moved" 404 page; nothing from it is used.

Derived in the lesson, not quoted: the control-period admissibility v ≤ √(2·v̇_b·(dist − v·Δt)) (0.8828 m/s at 1.0 m), the dynamic-window worked example, κ = 0.741 1/m for a 0.9 m / 0.3 m carrot, and the HER worked example; each is verified in the toys or in `tools/test_b15p2_dwa_her_toys.py`.

Cached under `/workspace/b15p2-sources/` on the worktree host (not committed): `fox.pdf/.txt`, `rpp.pdf/.txt`, `rpp-abs.html`, `rpp-readme.md`, `her.pdf/.txt`, `her-abs.html`, `dwa-wiki.html`.

## Toy design

- `dwa_vs_pure_pursuit_toy.py` (4.6): circular unicycle (r 0.2 m), accel limits 0.5 m/s² and 1.5 rad/s², |ω| ≤ 1.5; exact circular-arc steps H = 0.05 s inside a 0.25 s control period (no step-size stability limit; H vs H/2 printed: open loop 3.467e-03 m, closed-loop branching on D clutter_fast seed 0 trial 0 disclosed). Arms A_rpp (RPP-style: κ = 2y/L², curvature and proximity regulation, the smaller kept, floor 0.25 m/s, 1.0 s collision arc capped at the carrot, commands ignore accel limits) / B_dwa (7 × 15 window, Fox eq. 14 translational part, G = 2.0 heading + 0.2 dist + 0.2 vel, no σ) / C_window (no admissibility) / D_dwa_dt (eq. 14 with one held period). **Common random numbers** per (regime, seed, trial): obstacle field, global path and slip record (per-period v and ω slip factors). 5 seeds × 6 trials. Safety criterion checked at 0.98× / 1.02× (1.0 m: 0.9604 m before / 1.0404 m hits). Analytic arc–circle hit validated against a 1 mm brute-force walk in the tests.
- `her_sparse_grasp_toy.py` (7.3): `reward_shaping.py`'s grid made goal-conditioned; Q table keyed by goal-relative offset; replay-only Q-learning (64 updates per episode, α 0.35, γ 0.95, ε 0.5→0.05, 30 steps); arms A_sparse / B_her (future, k = 4, relabel share 0.80, only goals achieved with grip = 1) / C_dense (reward_shaping.py's dense reward). **Common random numbers** per (regime, seed): episode starts, goals, both exploration draws per (episode, step). 5 seeds. **No integration step** (discrete grid); the tests check the script has none.

No line in either expected file triggers the numerically-zero rule; the rule (|m| and sd < 1e-9, after the exact-tie test, before the sd test, no sign count) is implemented, unit-tested and defined in the prose.

Key numbers (DWA, pad 0.05): empty / open_slow all **tie**; clutter_slow RPP success 0 (blocked), B−A success 0.9000±0.0913 clear 5/5, B−A clearance −0.1321±0.0122 (RPP keeps more room); clutter_fast A collision 0.8000±0.1394, B−A −0.6667±0.2041 clear 5/5, D−A −0.8000±0.1394 clear 5/5, C−B 0.1333±0.1394 near-tie, D−B −0.1333±0.1394 near-tie; narrow_gap B−A time −1.0333±0.1896 small but consistent 5/5, clearance near-tie; winding A success 1.0 / 25.3333 s, B and C collide 30/30, D success 0.5000±0.2041 with 0 collisions (D−A −0.5000±0.2041 clear 5/5).
Key numbers (HER): near_goal final tie, auc near-tie (B−A 0.0021±0.0031, B−C 0.0014±0.0040); fixed_goal B−A 1.0000±0.0000 clear 5/5, B−C tie; far_goals B−A auc 0.5846±0.4715 clear 5/5, final 0.5967±0.5523 clear but 1 of 5 opposite and 1 of 5 equal, B−C near-tie (final −0.0067±0.0091, auc −0.0096±0.0146); big_grid A = B = 0 tie, B−C −0.4321±0.2232 clear 5/5 (HER loses).

Independent tests: `tools/test_b15p2_dwa_her_toys.py` (also executed by the batch-15 PR2 block in `tools/check_diagrams.mjs`).

## Post-hoc choices (stated in the en/zh prose; alternatives printed)

1. **PAD = 0.05 m** (DWA toy): the first run used no planning margin; DWA grazed obstacles under slip. ALT_PADS 0.0 and 0.1 are printed (pad 0: clutter_slow B 0.8000/0.2000, clutter_fast A 0/0.8333, B 0.4000/0.4667, D 0.4333/0.3667, winding D 0.1667/0.7333; pad 0.1: clutter_fast D 0.5667/0.0000, winding B 0/0.7333, D 0.2333/0).
2. **D_dwa_dt** arm: added after the first run showed B colliding although every chosen command passed eq. 14.
3. **winding** regime: added after the first run so RPP has a regime built for it; first geometry y = sin(2πx/5), walls ±0.6 m stopped all four arms without a collision (0/0 each, printed); final geometry y = 0.5(1 − cos(2πx/5)), walls ±0.7 m.
4. Brake fallback: a keep-curvature variant was tried during development and reverted; the first version (brake and straighten) is used.
5. **Goal-relative Q table** (HER toy): the first run used a (goal, cell, grip) table; HER barely helped there (near_goal 0.9333 vs sparse 0.7556; fixed_goal 0/0/1; far_goals 0.0267/0.0733/0.3967; big_grid all 0). Both tables are printed.
6. **wall** regime dropped (HER toy): the first run had five wall cells (final A 0.0000, B 0.0000, C 0.0250); dropped because a goal-relative table cannot see walls; disclosed in prose.
7. **big_grid** 10 × 10 (HER toy): added after the first run; the 8 × 8 version (x + y ≥ 9) tried first is printed (A 0.0000, B 0.4643, C 0.9571).
8. Explored, not adopted: with the first table, UPDATES 256 and 1000 episodes (far_goals A 0.067, B 0.333, C 1.000); a few smaller budgets (100 / 150) with the relative table. None is used on the page.

## Mismatch with §9

- H3: "clutter → (B) **consistent** fewer collisions than (A)" ✔ (clutter_fast B−A −0.6667±0.2041, clear 5/5). "than (C)" ✗ — measured C−B 0.1333±0.1394, a **near-tie** (no seed of the opposite sign, 2 of 5 equal). "open slow → (A)(B) **near-tie**": measured an exact **tie: identical on every seed** (stronger). "empty map → tie" ✔. "admissibility = can-stop-before-hit" ✔, checked at 0.98× / 1.02×. Extra, not in §9: RPP wins the winding corridor (B and C collide 30/30); Fox's literal test needs the control period (arm D) to stay collision-free; RPP keeps more clearance in clutter_slow; RPP is slower through narrow_gap (small but consistent).
- H4: "HER **consistent** > sparse" ✔ in fixed_goal (5/5) and far_goals (auc 5/5; final clear with 1 of 5 opposite); ✗ in near_goal (final tie, auc near-tie) and big_grid (both 0, tie). "HER tie/lose vs dense allowed" ✔: tie in fixed_goal, near-tie in far_goals, clear loss in big_grid. "trivial goal → (A)(B) near-tie" ✔ (near_goal). "sparse (A) consistent lose" holds against dense in fixed_goal, far_goals and big_grid, not in near_goal (tie). The numbers were followed, not §9.

## Lock changes

Totals only: site 31710→32070 and M4 2490→2670, M7 2430→2610 in the existing curriculum / README locks (all `31 710` README tips → `32 070`, labels renamed b15p1→b15p2); the b7p2 slam-nav host-minutes lock 450→630 (host total, as earlier per-host minute locks were moved). The b14p2 month-4 and b13p2 month-7 plan-header locks that matched `Current / 当前：**M4 2490 min**, Batch-14 PR2` / `**M7 2430 min**, Batch-13 PR2` now match the `## Batch-14 PR2` / `## Batch-13 PR2` headings (same entries, still required), as #154–#161 did. New b15p2 block added. No lock relaxed.

## Models / reproducibility

opencode free models were tried first with a toy brief (`/workspace/b15p2-opencode/`): `deepseek-v4.1-flash-free`, `glm-5.3-flash-free`, `mimo-v2.6-flash-free`, `longcat-2.5-free` all timed out (exit 124) with no file output; `minimax-m2.5-free` returned an UnknownError "Unexpected server error" (exit 1). Toys, tests and lesson text implemented locally in `/workspace/hl-b15p2`.

## Local validation

`tools/test_b15p2_dwa_her_toys.py`, month-4 / month-7 `check.sh` (toy lines), `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build with postbuild. No workflow edits. Minutes **71 / 32070**.
