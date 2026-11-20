# Batch-26 PR2 sources

Base `4f9d0bb73f9804f264bfa6eaf3e88e6d47a460f3` (batch-26 PR1 #204 squash-merged; 71 lessons, site **43740**). This PR: **M5 3930→4110**, **M6 4020→4200**, site **43740→44100** (44100=43740+180+180), still 71 lessons. Hosts: `moveit-pick-place` 480→**660**, `behaviour-cloning` 660→**840**.

## Opened sources

- moveit2_tutorials, The Pilz Industrial Motion Planner, **main** how-to `doc/how_to_guides/pilz_industrial_motion_planner/pilz_industrial_motion_planner.rst`, git commit **`cdee39bbc5746a98630a4d631ab7d0184de2f1e1`** (2024-12-31 20:05:15 UTC = 2025-01-01 04:05:15 Asia/Shanghai), blob **`54f4ee6cc3379f2198ac5d4a9a26349a1428ade0`**; curl **200**; RST sha256 `dff95cb2091f121defb32a7ad90c4a9b34786aa3ce73b283699c19436e71a591`. PTP: synchronized joint-space path; the lead axis sets the time law only. LIN: Cartesian straight-line position plus quaternion slerp. CIRC is named in the how-to and in the lesson, and has no toy arm. Definitions 以文档为准. The same how-to path on the Jazzy branch of `moveit2_tutorials` returned **404** and is not a body. docs.ros.org served a challenge page and is not a body. The pinned main RST was not replaced by a newer unpinned main.
- Picknik / MoveIt 2 documentation HTML rendering of the same how-to on main (`pilz-picknik-main.html`, sha256 `dbb69a59161fd919ccf14d77158649ca2c88c9fcd7f5117bf7e2e2fdacd0cdbf`) was used as a cross-check, not a second conflicting body.
- Li, Korkmaz, Bıyık, Reward-DAgger: Adaptive Human Intervention with Reward-Informed Progress, arXiv **2610.04054** v1, https://arxiv.org/abs/2610.04054, curl **200**. Title / 3 authors in abs order: Ryan Li, Yigit Korkmaz, Erdem Bıyık (dotted ı in Bıyık retained). Submitted 2026-10-02. The abs has no Comments field and no journal-ref field.
- https://arxiv.org/html/2610.04054 — curl **200**; v1 HTML body read (Eqs. 1-4 two-timescale Spearman progress gate; robot-gated takeover; paper success / ROHE Eq. 7).
- https://arxiv.org/pdf/2610.04054 — curl **200**; sha256 `ace2df056a4b2afc0a233c955aa5eb9e92295528784552b212088b7403284778`. PDF title page: Li∗ and Korkmaz∗, footnote “⋆ Equal Contribution”; no corresponding-author typography. Gating equations and paper figures 以论文为准.

Real MoveIt / Panda / `computeCartesianPath` / VLA / GPU reward model / human-in-the-loop arm: 本页未运行. Pilz definitions 以文档为准; paper success / ROHE and the paper gate `(75, −0.9, 0.05, 225, 0.0)` 以论文为准.

## Declared headers and first-run results

Official first run: 2026-11-20 08:25:24 Asia/Shanghai. Official expected sha256:

- `examples/month-5/expected/pilz_lin_vs_ptp_path_toy.txt` `112673bc6c03da8b9b35859d479bd1497b6ba4272378af007653750feb3bb39c`
- `examples/month-6/expected/reward_dagger_progress_gate_toy.txt` `4f01f183b07e17b70c299f354cd875e3fe54c5855566a4da2dd65d812fe352f1`

Both files were rerun twice and `cmp` was byte-identical.

Common random numbers: the path toy shares start and goal poses, the arm, the obstacle and the measurement-noise sequence across arms at each regime and seed (five seeds). The Reward-DAgger toy shares the synthetic progress traces across arms at each regime and seed (five seeds).

Pilz declared stand-in: `L1=0.3000` m, `L2=0.2500` m, `N_PATH=41`, `SIG_MEAS=4.000e-4` m (`hand_calc SIG_MEAS = 0.0004` m), `SMALL_FRAC=0.2000`. Hand calc (printed): reach `0.5500` m, fold `0.0500` m, `0.2000`, `N_PATH` 41, short joints, long reconfig and blocked poses, obstacle box. short_straight: B-A bow `-1.230e-5+-4.839e-5`, near-tie (2 of 5 opposite) — held as a may-near-tie. long_reconfig: B-A bow `-0.1659+-2.886e-4`, clear, 5/5 — held. lin_blocked: `line_hit` `1.0000`, C `n_collide` `9.0000+-0.0000` — lose held. A's `n_collide` `0.0000` on that box is an accidental joint-space bow off the box, not planning — disclosed, not claimed as a planner.

Reward-DAgger declared stand-in: `T=80`, `N_EPS=8`, `L_S=8`, `L_L=24`, `TAU_S=-0.5000`, `TAU_L=0.2000`, `DELTA_MIN=0.0800`, `SIG_PHI=0.0150`, `DROP_T=32`, `RISE_TO=0.7000`, `DROP_TO=0.2500`, `SMALL_FRAC=0.2000`. uneventful: B-A success `0.0000+-0.0000`, tie: identical on every seed (declared may-near-tie held, stronger); B-A calls `-80.0000+-0.0000`, clear, 5/5 effort advantage. drop_stall: B-C effort_return `0.6380+-0.0005` and success `1.0000+-0.0000`, clear, 5/5 — held; B-A calls `-34.6000+-0.1046`, clear, 5/5 more selective; C success `0.0000+-0.0000` lose held.

## Declared expectations that did not hold

None. Every pre-declared official cell held (short-straight may-near-tie; long-reconfig LIN bow win; lin-blocked lose; uneventful may-near-tie on success, held as an exact identical-seed tie, with a clear effort advantage; drop-stall selective-gate win; never-fire lose). Kept, not retuned.

## Post-hoc choices

None of the official parameters were changed after the first official run. Named alternatives on the same seeds, not adopted:

- Path toy: `SIG_MEAS=0.0000` m (`hand_calc` official `4.000e-4` m vs alternative `0.0000` m). On short_straight this turns B-A bow into a clear gap `-6.181e-5+-0.0000` (A `6.181e-5+-0.0000` m, B `7.376e-17+-0.0000` m). Not adopted, because it would manufacture a clear LIN win on the quiet cell.
- Reward-DAgger toy: `TAU_L=1.0000` (`hand_calc` official `0.2000` vs alternative `1.0000`). On uneventful this leaves B-A success a tie but raises B's calls to `57.0000+-0.0000` (`effort_return` `0.5839+-0.0000`) by firing as soon as the long window is full. A first short-only `delta_min=0` alternative produced identical official B behaviour and was replaced with `TAU_L=1.0000` before the official freeze. Not adopted.

## Typography notes

Official expected/ uses ASCII minus and `+-` in printed toy numbers, generated with ROUND_HALF_UP. Lesson prose quotes those official strings with the same ASCII minus / `+-` typography. House percentages use a space (`20 %`). The `20 %` cutoff is labelled 手算 in the pages and printed as `0.2000`. No typography or layout rewrite of official numbers after the first run. SimOutput fences were in the first official draft (`source="model"`). The PDF footnote is “⋆ Equal Contribution” in the lesson (以论文为准); expected/ prints the ASCII phrase `PDF footnote star Equal Contribution`.

## Code changes after the first run

No official toy or expected/ change after the first run. The official expected/ files were frozen at 2026-11-20 08:25:24 Asia/Shanghai and remained byte-identical on rerun. Official numbers were not rewritten. After that freeze, lesson typography was adjusted (expected/ not retuned):

- Chinese new-section bold markers that sat next to a full-width colon were loosened so the MDX build stays clean.
- The leading `cd` in the run-the-toy bash snippets and the `SimOutput` fences (`source="model"`) were already in the first official draft.
- A trailing blank line inside each new `SimOutput` fence was removed so `tools/check_quotes.py` accepts the quoted block as a whole-line match of expected/. Official numbers were not rewritten.
- These typography edits, plus the en/zh disclosure sentences that describe them, are the post-freeze page changes. expected/ was not retuned.

## Mismatch with §9

None. Pre-declared cells held and are disclosed in the en/zh results. Alternatives were named, run on the same seeds, and not adopted. Paper / docs figures stay 以论文为准 / 以文档为准. Real MoveIt / VLA hardware 本页未运行. The Reward-DAgger abs has no Comments / journal-ref, matching the proposal note.

## Lock changes

New batch-26 PR2 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, Pilz path-shape / Reward-DAgger gate contracts, sources, plans, README, declared regimes) plus `tools/test_b26p2_pilz_reward_dagger_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (43740→44100, M5 3930→4110, M6 4020→4200, moveit-pick-place 480→660, behaviour-cloning 660→840). Historical strings inside already-written plan/sources files were not edited, including the batch-26 PR1 live-at-the-time site **43740** strings and the previous Current headers (`M5 3930`, `M6 4020`). No lock relaxed. `kinematics.py`, `grip_sweep.py`, `package.json` / lockfile, and `.github/workflows` are untouched.

- README `/43 740/` and `约 43 740 分钟` → `/44 100/` and `约 44 100 分钟`.
- Curriculum sum checks `43740` → `44100`; live M5/M6 sum checks 3930→4110 and 4020→4200; live host-minute checks 480→660 on moveit-pick-place and 660→840 on behaviour-cloning.
