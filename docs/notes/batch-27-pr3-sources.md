# Batch-27 PR3 sources

Unit: H5 SeRA set-valued relabeling of autonomous rollouts (`intervention-logging`, +180 → 570). Site **45360** = 45180+180; M10 **4470**; still 71 lessons. Branch `feat/sera-autonomous-relabel` from `d398b3533e5b3f3fc44534085b5946c576fa9f4e`. **M10 = 4470 stands equal with M9 = 4470, 90 min above current heaviest M6 = 4380**; disclosed, not a dump onto M8 / M11. Parent accepted H5; this unit was not dropped to avoid the 4470 disclosure, and SeRA was not moved onto an avoided host or onto M9.

## Pins actually opened

- Li, Della Santina, Kober, “Old Experience, New Lessons: Relabeling Autonomous Robot Rollouts in Interactive Imitation Learning,” arXiv **2611.24273** v1.
  - https://arxiv.org/abs/2611.24273 and https://arxiv.org/abs/2611.24273v1 — curl **200** at 2026-11-20 14:04:57 Asia/Shanghai. Official title as above. Abs-order authors **Zhaoting Li, Cosimo Della Santina, Jens Kober**. Dateline: Submitted on 18 Nov 2026. Subjects: Robotics (cs.RO). Submission history: From: Zhaoting Li; [v1] Wed, 18 Nov 2026 11:51:08 UTC (2,309 KB). no Comments header in the abs metafield tags; no “Journal-ref” / “journal-ref” text on that page. The line “arXiv-issued DOI via DataCite (pending registration)” is **not** a journal-ref and was not filed as one.
  - Live Atom / API: `https://export.arxiv.org/api/query?id_list=2611.24273` returned HTTP **200** at 2026-11-20 14:13:24 Asia/Shanghai after earlier HTTP 429s (including on `id_list=2611.24273v1`). The entry id is `http://arxiv.org/abs/2611.24273v1`. Title and authors match the abs. `<published>2026-11-18T11:51:08Z</published>` (= 2026-11-18 19:51:08 Asia/Shanghai). The entry has no `arxiv:comment` element and no `arxiv:journal_ref` element. Live Atom bytes 3053, sha256 `cdf97b880d26c9e20f9b2c6b4c8fbe27d27cef14a49204b95263af0069f7a933` (identical to the earlier-today cached snapshot).
  - https://arxiv.org/html/2611.24273 and `…/2611.24273v1` — sha256 `fe1a52cc667cafe29407b2b948c412675dfb9f66a60686a8fdd73a02473f9771` (identical bytes for the two URLs).
  - https://arxiv.org/pdf/2611.24273 — 9 pages; sha256 `d7109a869d27a87f7d3cae8384de2d9861d60c897820973c7b366ce00e77d083`. Title page + §IV method (cross-round relabel, agreement / consistency mask, set-valued targets with radius `r_N ∥ã − a_r∥`, step-masked loss) + the discussion that exact-target pseudo-labelling can underperform were body-read. PDF title page matches the abs-order authors, with “and” before Kober. Title-page footnotes: Li and Della Santina at Delft University of Technology, the Netherlands; Kober at the University of Stuttgart, Germany. no corresponding-author mark was seen on the opened title page; none was invented. Paper Tables I–II and the abs tomato-picking 80 % vs 40 % stay 以论文为准 and are not toy outputs. Real robot / diffusion policy / SDP training / LIBERO / PushT 本页未运行.

## Official first run

`sera_autonomous_relabel_toy.py`, 2026-11-20 14:13:07 Asia/Shanghai, byte-identical on rerun. Expected sha256 `f86f5694016e75deec905c877a87b5c80e253939da9df3f74c06cb8607ab8fc8`.

## Pre-declared cells

All held and are disclosed in the en/zh results.

- already_good: C-B `task_mse 0.0000+-0.0000`, **tie: identical on every seed**. Declared may near-tie each other; held as an exact tie; kept. A remains at human-only `task_mse 0.2917+-0.0000`.
- wrong_auton_agree: C-B `task_mse -6.0000+-0.0000`, **clear**, 5/5; C `robot_mse 4.0000+-0.0000` versus B `0.0000+-0.0000` (lower imitation of the bad historical action). Kept. C exact-ties A on both metrics.
- checkpoints_disagree: C exact-ties A (`task_mse 0.2917+-0.0000`). D-C `task_mse 0.4583+-0.0000`, **clear**, 5/5 (exact-imitate-relabel loses). B also loses (`task_mse 6.2917+-0.0000`). Prefix rejection: `rejected_prefix=16`; step 1 `abs_diff=3.0000`, step 2 would have agreed individually (`0.0000`). Kept.
- exact_target_lose: D-C `task_mse 1.4400+-0.0000`, **clear**, 5/5. Radius `2.2000`, set `[-2.0000, 2.4000]`, which contains `a_star(1)=1.2500` and the human-only base `1.0000`. Kept.

Named alternative `ALT_RADIUS_RATIO=0.0000` (exact target after the agreement filter) was printed on the same streams and not adopted (on `exact_target_lose` it matches D and is clearly worse than official C).

## Post-first-run disclosures

There was no official toy or `expected/` change after the first run. Lesson prose, hooks, curriculum, plans, sources, README typography and tip locks were written after those figures were frozen. Official expected/ was not retuned. No lock relaxed. Existing `intervention_log_toy.py` and `map_vla_memory_prompt_toy.py` were not retuned. `kinematics.py`, `grip_sweep.py`, `servo_loop_sim.py`, `package.json` / lockfile, and `.github/workflows` are untouched.

## Mismatch with §9

None.

## Lock changes

New batch-27 PR3 block in `tools/check_diagrams.mjs` (toy, expected, CRN, label order, required three-way IIL contrast, sources, plans, README, declared regimes) plus `tools/test_b27p3_sera_relabel_toy.py`. Tipped site-total, host-minute, month-total and Current-header locks only (45180→45360, M10 4290→4470, intervention-logging 390→570, README `45 180`→`45 360`). Historical strings inside already-written plan/sources files were not edited, including `Current / 当前：**M10 4290 min**, Batch-26 PR3` and `Current / 当前：**M9 4290 min**, Batch-23 PR3`. No lock relaxed.

- README `/45 180/` and `约 45 180 分钟` → `/45 360/` and `约 45 360 分钟`.
- Curriculum sum checks `45180` → `45360`; live M10 sum checks 4290→4470; live host-minute check 390→570 on intervention-logging (MAP-VLA deepen row).
