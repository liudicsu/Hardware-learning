# Batch-24 PR2 sources

Base `e4a8c2236cd5a2e37144408108b8d0f12f23f320` (batch-24 PR1 #197 merged; 71 lessons, site **41580**). This PR: **M2 3930→4110**, **M8 3990→4170**, site **41580→41940** (41940=41580+180+180), still 71 lessons. Hosts: `motors-drivers` 720→**900**, `dataset-engineering` 330→**510**.

## Opened sources

- Wikipedia, Incremental encoder, oldid 1357373609, https://en.wikipedia.org/w/index.php?title=Incremental_encoder&oldid=1357373609 action=raw, HTTP 200. Last modified 2026-06-02 07:12:06 UTC = 2026-06-02 15:12 Asia/Shanghai. Speed is a derivative of a quantized position; by frequency, speed = (C_1 − C_0)/(T_1 − T_0), resolution grows with encoder resolution and with the window, and low speed is limited by position quantization; by period, measurements are triggered at positions rather than at clock instants, avoiding position quantization but inheriting time-reference quantization and becoming more sensitive to phase / symmetry errors. The page's 4096 counts-per-revolution, once-per-second RPM example is 以原文为准 and is not a toy output. Craig / Petrella / NASA primer PDFs linked from that page were not opened and are not cited as bodies.
- arXiv 2504.16054 v1 only, abs https://arxiv.org/abs/2504.16054, HTTP 200. Title: π0.5: a Vision-Language-Action Model with Open-World Generalization. Submitted 2025-04-22 17:31:29 UTC = 2025-04-23 01:31 Asia/Shanghai. No `journal-ref` on the abs at this writing. The abs lists Physical Intelligence first, then 35 named authors in this order: Kevin Black, Noah Brown, James Darpinian, Karan Dhabalia, Danny Driess, Adnan Esmail, Michael Equi, Chelsea Finn, Niccolo Fusai, Manuel Y. Galliker, Dibya Ghosh, Lachy Groom, Karol Hausman, Brian Ichter, Szymon Jakubczak, Tim Jones, Liyiming Ke, Devin LeBlanc, Sergey Levine, Adrian Li-Bell, Mohith Mothukuri, Suraj Nair, Karl Pertsch, Allen Z. Ren, Lucy Xiaoyang Shi, Laura Smith, Jost Tobias Springenberg, Kyle Stachowicz, James Tanner, Quan Vuong, Homer Walke, Anna Walling, Haohuan Wang, Lili Yu, Ury Zhilinsky.
- https://arxiv.org/html/2504.16054 — HTTP 200; v1 HTML body (abstract, heterogeneous co-training, first-phase 97.6 % non-target data, subtask-then-action inference). Those paper figures are 以论文为准 and are not toy outputs.
- https://arxiv.org/pdf/2504.16054 — HTTP 200; v1 PDF, 22 Apr 2025. The PDF places “Physical Intelligence” as an organization line above the same 35 names; the 35-name order matches the abs.

Resource cards: wiki-incremental-encoder, pi05-paper. A real encoder, timer capture, GPU, π0.5 weights, or real homes: 本页未运行.

## Declared headers and first-run results

Common random numbers: the encoder toy shares the shaft motion, A-channel edge train and jitter draws across arms at each regime and seed (five seeds). The co-training toy shares the scene / instruction / eval feature draws across arms at each regime and seed (five seeds, 25.0000 scenes).

Encoder declared lesson stand-in (not a vendor fact): motor_cpr = 12.0000, gear = 120.0000, shaft_cpr = 1440.0000, pulses_per_rev = 360.0000, frequency edges per rev = 720.0000, timer_tick = 1.0000000000e-06 s, jitter_frac = 0.0200, symmetry = 0.3000, assumed_duty_C = 0.5000, n_periods_B = 4.0000. low_speed: 10.0000 RPM, window 0.0200 s, expected A-edges 2.4000; paired B−A abs_rpm_err −2.6062±1.8042, clear, 5/5 — held. high_speed_long_window: 300.0000 RPM, window 0.1000 s, expected A-edges 360.0000; paired B−A 2.0576±1.2790, clear, 5/5 — the pre-declared near-tie did not hold; kept. C loses on both regimes: C−B 7.4955±1.4420 and 198.2811±49.3165, clear, 5/5 — held.

π0.5 declared mixture: w_target = 0.4000, w_web = 0.2000, w_subtask = 0.2500, w_other = 0.1500, sum 1.0000; w_target_C = 0.0000, C used-weight sum 0.6000; bias = 0.0500, sig = 0.0800, n_scenes = 25.0000. in_domain mus all 0.7500; paired B−A success −0.0131±0.0062, small but consistent, 5/5 — the pre-declared near-tie did not hold; kept. ood_new_home mus 0.3500 / 0.6000 / 0.6000 / 0.5500; paired B−A 0.1504±0.0199, clear, 5/5 — held. C loses on both regimes: C−B −0.3032±0.0038 and −0.1370±0.0121, clear, 5/5 — held.

## Declared expectations that did not hold

Encoder high_speed_long_window: declared A and B may near-tie on abs_rpm_err; first run gave paired B−A 2.0576±1.2790, a clear gap (same sign on all 5 seeds), with A lower error than B. Kept, not retuned.

π0.5 in_domain: declared A and B may near-tie on success; first run gave paired B−A −0.0131±0.0062, a small but consistent gap (same sign on all 5 seeds), with A slightly higher than B. Kept, not retuned.

## Post-hoc choices

None. No constant, arm, metric or regime was changed after the first run. Alternatives on the same seeds (encoder jitter_frac = 0.0100 and window_scale = 2.0000; co-training sig = 0.1200 and B weights 0.5000/0.2000/0.2000/0.1000) were printed and not adopted.

## Code changes after the first run

None.

## Mismatch with §9

The two “may near-tie” cells above did not hold; both are printed and kept, and the lesson prose was written to match the first-run labels. No retune.

## Lock changes

New batch-24 PR2 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, difference directions, sources, plans, README, declared regimes, and the two near-tie cells that did not hold) plus `tools/test_b24p2_encoder_pi05_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (41580→41940, M2 3930→4110, M8 3990→4170, motors-drivers 720→900, dataset-engineering 330→510). No lock relaxed. Historical PR1 strings such as 41220→41580 and 41580=41220+180+180 stay in the PR1 plan sections.

- README `/41 580/` and `约 41 580 分钟` → `/41 940/` and `约 41 940 分钟`.
- Curriculum sum checks `41580` → `41940`; the current month-total table and the live M2/M8 sum checks 3930→4110 and 3990→4170; live host-minute checks 720→900 on motors-drivers and 330→510 on dataset-engineering.
