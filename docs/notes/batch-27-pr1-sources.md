# Batch-27 PR1 sources

Units: H1 first- vs third-angle projection (`cad-parametric`, +180 → 630) and H2 official Jazzy executor / callback-group contract (`ros2-graph`, +180 → 750). Site **44820** = 44460+360; M3 **4050**, M4 **4110**; still 71 lessons. Branch `feat/first-third-angle-ros2-executors` from `0fcb28a514ee381b0f3281e3eb42ab3539910ac4`.

## Pins actually opened

- Wikipedia “Multiview orthographic projection” `action=raw` oldid **1385532381**; lastrevid **1385532381** (2026-11-13T20:08:47Z = 2026-11-14 04:08:47 Asia/Shanghai); revision sha1 `09d8d8eadae7856a2a5772f05c8dbc54ea057b5e`; fetched wikitext sha256 `7affee62a66d8b9ceab172f65e0e40c5bbb548077e8f35fa0dd6602761d0f664`. Sections used: Quadrants in descriptive geometry, First-angle projection, Third-angle projection, Additional information, Symbol, Territorial use. Standalone “First-angle projection” and “Third-angle projection” titles are redirects to those sections. Additional information and Territorial use were paraphrased separately; no merged geography sentence was invented. ISO 5456-2 / ASME Y14.3 / BS 8888 / JIS B 0001 / AS 1100 are named only as Wikipedia names, 以原文为准; paid PDFs were not opened. Real CAD was 本页未运行.
- Wikipedia “Engineering drawing” oldid **1367578425** (2026-08-03T23:15:53Z = 2026-08-04 07:15:53 Asia/Shanghai); fetched wikitext sha256 `d0bb88e617e13f834065e41ea83a71c65c4db4eaff850d1b1a059150228c6466`. Secondary / literacy only.
- ros2_documentation commit **`bb5ba426fe4de413362f605c27074385c83ff9e3`** (2026-11-19T08:49:59Z = 2026-11-19 16:49:59 Asia/Shanghai, jazzy tip at survey):
  - About-Executors.rst blob **`2a4e909434eb0f5e60f92ab72237e8cd89da3a6b`**, sha256 `655625207ddfa66b3cf40796c8ae96289166aa115bc84377c47f9b9dcbb3059b`. Three executor types only; Outlook names WaitSet and rclc, not EventsExecutor; composition containers use a Single-Threaded Executor.
  - Using-callback-groups.rst blob **`829b66d96d7e0de22d5ee29bcdd24196fdcea54f`**, sha256 `7d4e34db972907d768f9f7fa73e112914e8f040cc36ad65f4678c9d381800914`. Default group is Mutually Exclusive; a Multi-Threaded node with everything in that group “essentially acts as if it was handled by a Single-Threaded Executor”; a synchronous call that shares a Mutually Exclusive group with the server “will always cause a deadlock”. Official wording is 以文档为准. Real rclpy / rclcpp was 本页未运行.

## Official first runs

Both toys, 2026-11-20 11:46:03 Asia/Shanghai, byte-identical on rerun.

- `first_third_angle_projection_toy.py` expected sha256 `28cc915f82a3ea33ddf243c48e4a59e3ba35171c65ad7782386b4006422f590a`.
- `executor_callback_group_toy.py` expected sha256 `57a1f7eaeb307c91ac83e9ef87375cb3920ea438c8524fd43dd1b475f0a2c016`.

## Pre-declared cells

All held and are disclosed in the en/zh results.

- H1 same-convention: A and B exact tie on slot_match, boss_ok and notch_ok (`0.0000+-0.0000`, identical on every seed).
- H1 cross-convention: C loses, left/right and top/bottom swap (paired C-A `-1.0000+-0.0000`, 5/5).
- H1 symbol-ignored: D loses on left/right (paired D-A boss_ok `-1.0000+-0.0000`, 5/5); notch_ok stays a tie.
- H2 no_sync_no_overlap: A_single, A_mt_default and B_two_groups exact-tie on timer_done and sub_done (`0.0000+-0.0000`).
- H2 overlap_sync: B consistent better subscription service / lower starved ticks (paired B-A_single sub_done `20.0000+-0.0000`, starved_ticks `-39.0000+-0.0000`, 5/5); C loses (deadlock, handler_progress `0.0000+-0.0000`, ties A_mt_default). A_single and A_mt_default also deadlock in this regime, as the official default-group contract says.

Named alternatives (invert-symbol; Reentrant group) were printed on the same objects / schedule and not adopted.

## Post-first-run disclosures

There was no official toy or `expected/` change after the first run. Lesson prose, hooks, curriculum, plans, sources, README typography and tip locks were written after those figures were frozen. After the first `check_diagrams.mjs` run, this sources note was completed so that 本页未运行 and 以文档为准 appear here as well as in the lessons and toys. The en/zh Results paragraphs were then completed to say that, after the figures were frozen, Chinese bold typography was adjusted and the pages were written to the frozen official output; official expected/ was not retuned. No lock relaxed. Existing service/action deadlock snippets on `ros2-graph` were not rewritten; the `ros2-control` MultiThreaded + Reentrant usage note was contrasted, not edited. `kinematics.py`, `grip_sweep.py`, `package.json` / lockfile, and `.github/workflows` are untouched.

## Mismatch with §9

None.

## Lock changes

New batch-27 PR1 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, layout / deadlock contract, sources, plans, README, declared regimes) plus `tools/test_b27p1_projection_executor_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (44460→44820, M3 3870→4050, M4 3930→4110, cad-parametric 450→630, ros2-graph 570→750). Historical strings inside already-written plan/sources files were not edited. No lock relaxed.

- README `/44 460/` and `约 44 460 分钟` → `/44 820/` and `约 44 820 分钟`.
- Curriculum sum checks `44460` → `44820`; live M3/M4 sum checks 3870→4050 and 3930→4110; live host-minute checks 450→630 on cad-parametric and 570→750 on ros2-graph.
