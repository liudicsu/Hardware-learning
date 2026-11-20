# Batch-26 PR1 sources

Base `783242044cfd250be2d3747a5b31633f650b1369` (batch-25 PR3 #203 squash-merged; 71 lessons, site **43380**). This PR: **M3 3690→3870**, **M4 3750→3930**, site **43380→43740** (43740=43380+180+180), still 71 lessons. Hosts: `gripper-fingers` 570→**750**, `ros2-control` 420→**600**.

## Opened sources

- Brown, Rodenberg, Amend, Mozeika, Steltz, Zakin, Lipson, Jaeger, Universal Robotic Gripper based on the Jamming of Granular Material, arXiv **1009.4444** v2, https://arxiv.org/abs/1009.4444, curl **200**. Title / 8 authors in abs order: Eric Brown, Nicholas Rodenberg, John Amend, Annan Mozeika, Erik Steltz, Mitchell R. Zakin, Hod Lipson, Heinrich M. Jaeger. Submitted 2010-09-22, this version 2010-11-05. The abs Comments field is "10 pages, 7 figures". The abs Journal reference is Proceedings of the National Academy of Sciences 107, (44) 18809-18814 (2010) (Related DOI 10.1073/pnas.1003250107). That journal pagination was not opened as a second body; the opened body remains arXiv 1009.4444 v2. No equal-contribution or corresponding-author typography on the v2 title page.
- https://arxiv.org/html/1009.4444 — curl **200**; v2 body read (Eqs. 1-2, `theta_c` slip condition, membrane-seal suction, interlocking for `theta > pi/2`).
- https://arxiv.org/pdf/1009.4444 — curl **200**; sha256 `ffe128e4c94d5d01919f0bf1460565eb6219064e64e65ac0d8f325a84ef521bc`. v2 title page (no contribution marks) + Eqs. 1-2 + Fig. 3 + the `theta_c` slip condition. Volume changes of less than 0.5 %; fitted `mu = 1.04 +- 0.06`, `sigma_star = 50 +- 4 kPa`, `d = 1.07 +- 0.07 mm`; spheres that form a seal held with a force about 10 times that of porous spheres. Suction is a membrane seal that holds a gap vacuum while the object is lifted after jamming has pinched the bag; no pressure drop is detected when the gripper merely contracts. Independent inclined-plane `mu = 1.10 +- 0.03` in Methods.
- Wikipedia, Jamming (physics), oldid **1371811728**, https://en.wikipedia.org/w/index.php?title=Jamming_(physics)&oldid=1371811728 `action=raw`, curl **200**. Mentions the Cornell granular-jamming gripper video; **no** holding-force equations — literacy only, not a substitute for Eqs. 1-2. The lesson cites the paper equations, not this page, so the oldid is recorded here rather than as a toy output.
- ros2_control Controller Chaining / Cascade Control, https://github.com/ros-controls/ros2_control/blob/b558c3ab693fbf9aa472392cafc0c0f14f9fc549/controller_manager/doc/controller_chaining.rst, git commit **`b558c3ab693fbf9aa472392cafc0c0f14f9fc549`** (2026-11-17 21:59:51 UTC = 2026-11-18 05:59:51 Asia/Shanghai), blob **`0b91260a4064e51fce45e0de1e09101c5147fd02`**; curl **200**; sha256 of the fetched RST `6e3d172ae313e316e1dc07044e932e9d69bf9bd59e1478be4815b686cd2808fd`. Activation / deactivation order, chained mode, reference-interface availability, `switch_controllers` list, spawner `--activate-as-group`. Cascade control is a specific type of controller chaining. The controller manager updates preceding controllers before their following controllers.
- https://control.ros.org/jazzy/doc/ros2_control/controller_manager/doc/controller_chaining.html — curl **200**; same Jazzy HTML rendering, used as a cross-check, not a second conflicting body.
- ros2_control_demos example 16, https://github.com/ros-controls/ros2_control_demos/blob/b34cc5917f216b36ff3bda1ca0cc0736ecc00235/example_16/doc/userdoc.rst, git commit **`b34cc5917f216b36ff3bda1ca0cc0736ecc00235`** (2025-07-10 07:15:16 UTC = 2025-07-10 15:15:16 Asia/Shanghai), blob **`331f9881206b6a71a60b6c5b0463161c2039e99b`**; curl **200**; sha256 `377ce01c5a44cf4565ce8850fdbcbdc191441261a790f5a62462f63310fda553`. DiffBot: `diff_drive_controller` precedes two PID controllers; `[claimed]` / `[unclaimed]` literacy.

Real jamming bag / vacuum pump / Instron / `controller_manager` / DiffBot / hardware: 本页未运行. Paper figures 以论文为准; ros2_control figures 以文档为准.

## Declared headers and first-run results

Official first run: 2026-11-20 04:07:30 Asia/Shanghai. Official expected sha256:

- `examples/month-3/expected/jamming_gripper_holding_force_toy.txt` `2e771d7f9469a3cabfb35db6e21f6d3f485f6f304195effe4e647649f8e9f518`
- `examples/month-4/expected/controller_chaining_cascade_toy.txt` `c905ed8f67ecc77cad344d5cd2cf4d8fd072d70ae80affcb0a1992a785546b72`

Both files were rerun twice and `cmp` was byte-identical.

Common random numbers: the jamming toy shares the contact angle across arms at each regime and seed (five seeds). The chaining toy shares the measurement-noise sequence and inner-disturbance step across arms at each regime and seed (five seeds); the outer reference is shared.

Jamming declared stand-in: `R=0.0125` m, `MU=1.0400`, `SIGMA_STAR=50000.0000` Pa, `D=0.00107` m, `SMALL_FRAC=0.2000`. Hand calc (printed): `theta_c=0.7658` rad, `pi/4=0.7854`, `pi/2=1.5708`, `D=1.0700` mm, `50.0000` kPa, `0.2000`. below_theta_c: all `F_h` `0.0000+-0.0000`, tie: identical on every seed — held (declared lose). modest_seal: C-B `11.8387+-8.5333`, clear, 5/5 — held; C `13.9682+-9.9559` N, B `2.1295+-1.4229` N. good_theta_unjammed: B-A `3.0794+-0.9884` and C-A `20.6079+-7.1491`, clear, 5/5 — held. thin_disk: all `0.0000+-0.0000`, lose held.

Chaining declared stand-in: `DT=0.0020` s, `T_SIM=8.0000` s, `T_WARM=1.0000` s, `TAU_INNER=0.0250` s, `TAU_OUTER=0.6000` s, `T_REF=2.5000` s, `KP_SINGLE=1.8500`, `KP_OUTER=2.0000`, `KP_INNER=12.0000`, `SIG_Y=0.0100`, `DIST_AMP=0.3500`, `DIST_START=2.0000` s, `U_BROKEN=0.0000`. Hand calc (printed): inner ZOH `0.9231` / `0.0769`, outer ZOH `0.9967` / `0.0033`, ratio `24.0000`, window `3500`, `0.2000`. slow_no_dist: B-A outer `1.234e-7+-1.824e-6`, near-tie (2 of 5 opposite) — held as a may-near-tie; A/B outer `0.2899+-4.051e-5` / `0.2899+-4.160e-5`. inner_disturbance: B-A outer `-0.9775+-9.508e-5` and inner `-4.0858+-1.412e-5`, clear, 5/5 — held. broken_chain: C-B outer `0.5038+-5.723e-5`, clear, 5/5 — held; C outer `0.7938+-0.0000`.

## Declared expectations that did not hold

None. Every pre-declared official cell held (below-threshold and thin-disk losses; modest seal-side consistent gain; unjammed loss; quiet A/B near-tie; inner-disturbance cascade win; broken-chain loss). Kept, not retuned.

## Post-hoc choices

None of the official parameters were changed after the first official run. Named alternatives on the same seeds, not adopted:

- Jamming toy: `MU=1.1000` (paper independent inclined-plane `1.10 +- 0.03` 以论文为准; `hand_calc theta_c at MU_ALT = 0.7378` rad). below_theta_c and thin_disk stay `0.0000`; modest_seal C-B remains a clear gap `12.8686+-8.9134` (C `15.1888+-10.3904` N, B `2.3202+-1.4772` N). Not adopted to chase a paper-like "10 times" ratio.
- Chaining toy: `KP_SINGLE=1.5000` (`hand_calc` official `1.8500` vs alternative `1.5000`). On slow_no_dist this turns B-A outer into a small consistent gap `-0.0398+-6.176e-6` (A `0.3297+-3.573e-5`); not adopted, because it would manufacture a cascade win on the quiet cell. inner_disturbance remains a clear B win (`-1.1343+-9.207e-5` outer).

## Typography notes

Official expected/ uses ASCII minus and `+-` in printed toy numbers, generated with ROUND_HALF_UP. Lesson prose quotes those official strings with the same ASCII minus / `+-` typography. House percentages use a space (`0.5 %`, `20 %`). The `20 %` cutoff is labelled 手算 in the pages and printed as `0.2000`. No typography or layout rewrite of official numbers after the first run. SimOutput fences were in the first official draft (`source="model"`).

## Code changes after the first run

No official toy or expected/ change after the first run. The official expected/ files were frozen at 2026-11-20 04:07:30 Asia/Shanghai and remained byte-identical on rerun. Official numbers were not rewritten. After that freeze, lesson typography and command-block layout were adjusted (expected/ not retuned):

- All four run-the-toy bash snippets gained a leading `cd ~/Hardware-learning/examples/month-3/gripper-fingers` or `cd ~/Hardware-learning/examples/month-4/ros2-control`, so each block is self-contained for the cad-cd check.
- Chinese new-section bold markers that sat next to a full-width colon or a full-width period were loosened (`成立：`, `本页未运行`, and similar).
- A missed live current-curriculum lock in the deepen3 block of `tools/check_diagrams.mjs` was tipped M3 3690→3870 and M4 3750→3930. An unused `lang` binding in the new lock loop was removed so eslint stays warning-free.
- The Month 3 `examples/month-3/check.sh` hook for `jamming_gripper_holding_force_toy` had been written after `exit $fail`. With `set -euo pipefail`, that line never ran. The same `check` command was moved above `exit $fail`, next to the other enrichment hooks. The check command itself, Month 4, expected/, and the toy sources were not changed. `tools/test_m3_optional_cad.py` records the live check.sh hooks; `jamming_gripper_holding_force_toy.txt` was added to that list so the control-flow spy matches the hook that now actually runs.
- The Fair setup sentences in the gripper-fingers en/zh lessons labelled the declared theta sampling bounds `0.0500`, `0.9000`, `0.0200`, and `0.1000` as `hand_calc` / 手算, because those four numbers are not printed in expected/. The toy and expected/ were not changed to print them.
- These typography, wording, hook-position, and lock edits, plus the en/zh disclosure sentences that describe them, are the post-freeze page and harness changes. expected/ was not retuned.

## Mismatch with §9

None. Pre-declared cells held and are disclosed in the en/zh results. Alternatives were named, run on the same seeds, and not adopted. Paper / docs figures stay 以论文为准 / 以文档为准. Real hardware 本页未运行.

## Lock changes

New batch-26 PR1 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, Eqs. 1-2 clamp, activation contract / chained mode, sources, plans, README, declared regimes) plus `tools/test_b26p1_jamming_chaining_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (43380→43740, M3 3690→3870, M4 3750→3930, gripper-fingers 570→750, ros2-control 420→600). Historical strings inside already-written plan/sources files were not edited. No lock relaxed. `kinematics.py`, `grip_sweep.py`, `package.json` / lockfile, and `.github/workflows` are untouched.

- README `/43 380/` and `约 43 380 分钟` → `/43 740/` and `约 43 740 分钟`.
- Curriculum sum checks `43380` → `43740`; live M3/M4 sum checks 3690→3870 and 3750→3930; live host-minute checks 570→750 on gripper-fingers and 420→600 on ros2-control.
