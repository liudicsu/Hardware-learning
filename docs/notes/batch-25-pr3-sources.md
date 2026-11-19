# Batch-25 PR3 sources

Base `44bc06ba51af58cc6663d022f4ff4bbd1f2600de` (batch-25 PR2 #202 merged; 71 lessons, site **43020**). This PR: **M10 3750→4110**, site **43020→43380** (43380=43020+180+180), still 71 lessons. Hosts: `edge-deploy-checklist` 540→**720**, `real-time-chunking` 390→**570**.

## Opened sources

- TacitVLA abs, https://arxiv.org/abs/2610.17540, HTTP 200 on 2026-11-20. Title: “TacitVLA: Reasoning Vision-Language-Action Models Without Reasoning Latency.” Eleven authors in abs / citation order: Jack Lu, Yurong You, Boyi Li, Yulong Cao, Thomas Tian, Chaowei Xiao, Xiangyu Chen, Wenjie Luo, Boris Ivanovic, Marco Pavone, Yan Wang. v1 only; dateline “[Submitted on 13 Oct 2026]”; citation_date 2026/10/13. Comments: “Project page: this https URL” (https://tacitvla.github.io); no venue. Saved under `/workspace/b25p3-sources/2610.17540.abs.html`, sha256 `73935e5f7e745f622a6998c060d469ac0054243ad17f47eaa205637a3515f1b2`.
- TacitVLA HTML, https://arxiv.org/html/2610.17540, HTTP 200 on 2026-11-20. v1 body read (masking reasoning from the action expert, deferred text generation, explicit vs tacit vs no-reasoning, memory ledger). The HTML conversion attaches the internship footnote poorly; marks were **not** transcribed from the HTML. Saved under `/workspace/b25p3-sources/2610.17540.html`, sha256 `6f750c2130f8744606a72b0dbaa6b72db30a4306f833b97ed0595ace1221e861`.
- TacitVLA PDF, https://arxiv.org/pdf/2610.17540, HTTP 200 on 2026-11-20, 26 pages, arXiv:2610.17540v1 [cs.AI] 13 Oct 2026. PDF opened with pdftotext and the title page was rendered. Title-page marks: “Jack Lu^{1,2,†} … Marco Pavone^{1,5,*} and Yan Wang^{1,*}”; “1 NVIDIA, 2 New York University, 3 University of California, Berkeley, 4 Johns Hopkins University, 5 Stanford University, † Work done during an internship at NVIDIA, * Equal advising.” The dagger is an internship mark, **not** corresponding and **not** equal first author; the stars are equal advising, **not** corresponding; no corresponding-author mark was invented. The PDF header also prints **2026-10-14**, disclosed as a compiled / header date, not a second version. Paper figures (up to 3.4× lower latency than explicit reasoning, up to +17.1 % success at a no-reasoning architecture’s latency, RoboMME Counting 82.7 % vs 66.8 %, RMBench 77.5 % vs 56.5 %, LIBERO-Plus 72.9 %, PhysicalAI-AV public-split scene score 52.5 %) 以论文为准, not toy outputs. Saved under `/workspace/b25p3-sources/2610.17540.pdf`, sha256 `072b52ae2c70a9e4223ebc9776009569334863a909aee8850c93b302a8275ea9`.
- Vela abs, https://arxiv.org/abs/2610.05230, HTTP 200 on 2026-11-20. Title: “Vela: Scaling Vision-Language-Action Models with Adaptive Action Curve Parametrization” (spelling **Parametrization**, not Parameterization). Seven authors in abs / citation order: Yifan Li, Jiaxu Wang, Dongming Wu, Yicheng Jiang, Ryan Ji, Xiangyu Yue, Yanwei Fu. v1 only; dateline “[Submitted on 4 Oct 2026]”; citation_date 2026/10/04. No Comments field; no venue. Saved under `/workspace/b25p3-sources/2610.05230.abs.html`, sha256 `37004d260644292ce392466dea2a7d811c584c3b3a403f278fc2aeb7a3f1a57f`.
- Vela HTML, https://arxiv.org/html/2610.05230, HTTP 200 on 2026-11-20. v1 body read (fixed-rate chunks vs compact spline / motion-dependent temporal support, §3.3 horizon adaptation). Saved under `/workspace/b25p3-sources/2610.05230.html`, sha256 `db666abb5349170d96c78e489990ab5667b930479b188d8a91f4acf387d4dc9f`.
- Vela PDF, https://arxiv.org/pdf/2610.05230, HTTP 200 on 2026-11-20, 18 pages, arXiv:2610.05230v1 [cs.RO] 4 Oct 2026. PDF opened with pdftotext and the title page was rendered. Title-page marks: “Yifan Li^{1,2*} Jiaxu Wang^{3*} … Xiangyu Yue^{3†} Yanwei Fu^{1,2†}”; “1 Fudan University 2 Shanghai Innovation Institute 3 The Chinese University of Hong Kong 4 NovaXBot”; “* Equal Contribution. † Corresponding Authors.” Both corresponding-author marks are kept. Paper LIBERO-X / EBench / real egg-cake cooking and potato-shredding scores 以论文为准, not toy outputs. Saved under `/workspace/b25p3-sources/2610.05230.pdf`, sha256 `e21c25e7bfe8e91b48ac2283de4cdad276e9e05894d9188c3d3079bcfaf882a1`.

Resource cards: `tacitvla-paper`, `vela-paper`. GPU / RoboMME / PhysicalAI-AV / real cooking / EBench: 本页未运行. Paper figures 以论文为准.

## Declared headers and first-run results

Official first run: 2026-11-20 00:18:32 Asia/Shanghai. Official expected sha256:

- `examples/month-10/expected/tacitvla_reasoning_latency_toy.txt` `b5ff59f999c2957fe47c8786a339a299f1a78d15b156489b8e8af441a16bd634`
- `examples/month-10/expected/vela_spline_action_toy.txt` `7421b0ee26c31845b6ff4799f1af074e93256bc5a9e07c0ebeb819a2b2c3fd37`

Both files were rerun twice and `cmp` was byte-identical.

Common random numbers: the TacitVLA toy shares tasks, uniforms, targets and stale draws across arms at each regime and seed (five seeds). The Vela toy shares the continuous reference motions, the output-budget K and the query grid across arms at each regime and seed (five seeds).

TacitVLA declared stand-in: `T_ACTION=8.0000`, `T_REASON=12.0000`, `WINDOW=20.0000`, `N_EP=40`, `N_STEPS=6`, `P_SHORT=0.8500`, `P_SHORT_NOSUP=0.7000`, `C_FIXED_PRESSES=4`, targets 2, 3, 4, 5, `SMALL_FRAC=0.2000`, seeds 0–4. Hand calc (printed): `T_ACTION + T_REASON = 20.0000`, `WINDOW - T_REASON = 8.0000`, `explicit_over_tacit_latency = 2.5000`. That 2.5000 is a toy ratio, not the paper’s 3.4×. short_reactive: B-A success `0.0000+-0.0000`, tie: identical on every seed; B-A latency `-12.0000+-0.0000`, clear, 5/5 — held (declared may near-tie on success with consistent lower tacit latency; held as an exact tie on success), kept. memory_ledger: B-C success `0.7500+-0.0000`, clear, 5/5; B-C latency `0.0000+-0.0000`, tie: identical on every seed (comparable) — held, kept. stale_memory: C-B success `-1.0000+-0.0000`, clear, 5/5 — held, kept. B-A success is a tie on every official regime; tacit was not retuned to beat explicit on success.

Vela declared stand-in: `K=8`, `N_QUERY=121`, `T_SHORT=1.0000`, `T_LONG=4.0000`, `T_PRECISE=1.0000`, `T_MIXED=5.0000`, `BUMP_AMP=1.0000`, `BUMP_WIDTH=0.1600`, `C_STRETCH=2.0000`, `SMALL_FRAC=0.2000`, seeds 0–4. Hand calc (printed): `T_LONG + T_PRECISE = 5.0000`, query spacing short `0.0083`, mixed `0.0417`. The stretched horizon `10.0000` is a 手算 from printed `T_MIXED=5.0000` and `C_STRETCH=2.0000` (not a separate official print line). short_smooth: B-A RMSE `6.208e-17+-0.0000`, numerically zero (floating-point residue), effectively a tie — held, kept. mixed_motion: A `0.1661+-0.0000`, B `0.0183+-0.0000`, B-A `-0.1478+-0.0000`, clear, 5/5 — held, kept. coarse_horizon: C `0.1875+-0.0000`, C-B `0.1692+-0.0000`, clear, 5/5 — held, kept.

## Declared expectations that did not hold

None. Every pre-declared official regime held (short-horizon success exact tie with tacit lower latency; memory-cell B-over-C success at comparable latency; stale-reasoning lose; short-smooth numerically-zero effective tie; mixed-motion consistent spline lower error; coarse-horizon C lose).

## Post-hoc choices

None of the official parameters were changed after the first official run. The lesson pages were written from the frozen official output. After that official run, Vela lesson prose marks the stretched horizon `10.0000` as a 手算 from the printed `T_MIXED=5.0000` and `C_STRETCH=2.0000`; official expected output was not retuned. Named alternatives on the same seeds, not adopted:

- TacitVLA: `ALT_T_REASON=25.0000` on the memory_ledger bank (hand_calc overflow `5.0000`) makes B’s latency `13.0000+-0.0000`, no longer tied with C’s `8.0000+-0.0000`. Official `T_REASON=12.0000` still fits in `WINDOW=20.0000`.
- Vela: a dropped-knot support on the mixed_motion bank yields C RMSE `0.0212+-0.0000` and C-B `0.0030+-0.0000`, a small but consistent gap, 5/5. Official C stays the stretched long horizon, where the lose is clear.

Existing int8 / VLA-Adapter / RTC / FORGE-Tree / π0 body, batch-20–24 hosts, #201 / #202 wording, `package.json`, and `.github/workflows` were not edited.

## Lock changes

No lock relaxed. Live site-total locks were tipped 43020 → 43380 and live README `/43 020/` → `/43 380/`. Live M10 curriculum sum and live host-minute locks for `edge-deploy-checklist` (540→720) and `real-time-chunking` (390→570) were tipped where they test the live curriculum. Historical strings inside already-written plan and sources files (including previous Current lines and the batch-25 PR1 / PR2 sources notes, and “42660→43020” in the month-7 / month-8 plan locks) were left unchanged. New PR3 locks were added for the two toys, expected output, CRN, label order, TacitVLA / Vela authorship and PDF marks / no venue, header date 2026-10-14, title spelling Parametrization, live totals 43380, and host / month minutes. Independent tests: `tools/test_b25p3_tacit_vela_toys.py`.

## Mismatch with §9

None.

## Post-first-run typography and live lock tips

After the official freeze (2026-11-20 00:18:32 Asia/Shanghai), official parameters and expected/ were not retuned.

- Chinese lesson typography: the 20 % small/clear cutoff in the new TacitVLA and Vela sections was written with a space before the percent sign (house style). Disclosed in en/zh “Choices made after seeing results.”
- Live lock tips only (not historical plan/sources strings): README `/43 020/` → `/43 380/`; live curriculum site total 43020→43380; live host minutes `edge-deploy-checklist` 540→720 and `real-time-chunking` 390→570; live current-curriculum M10 month sum 3750→4110 (the M4 3750 entry in the same table was left unchanged).
- The stretched horizon `10.0000` remains a 手算 / hand calc from printed `T_MIXED = 5.0000` and `C_STRETCH = 2.0000`; official expected has no separate print line for that product.
