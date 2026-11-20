# Batch-26 PR3 sources

Base `600d5898535a0d81ea8c7c81e72897ea0ea7e060` (batch-26 PR2 #205 squash-merged; 71 lessons, site **44100**). This PR: **M10 4110→4290**, **M6 4200→4380**, site **44100→44460** (44460=44100+180+180), still 71 lessons. Hosts: `multi-view-extrinsics` 450→**630**, `vla-models` 1410→**1590**. Final month totals: M1 2910, M2 4110, M3 3870, M4 3930, M5 4110, M6 **4380**, M7 3870, M8 4350, M9 4290, M10 **4290**, M11 4350 (checksum 44460). M6 becoming the uniquely heaviest month at 4380 is an already accepted and already disclosed choice.

The H4 HG-DAgger clarification already on main was not reverted. Historical strings inside already-written plan/sources files were left in place, including PR1 **43740** / M3 **3870** / M4 **3930** and PR2 **44100** / M5 **4110** / M6 **4200**, and previous Current headers.

## Opened sources

- Pan, Wang, Pang, Zhou, Yang, Zhang, Di, CoRe-VLA: Preserving Cross-View Coordination in VLAs under Camera Shifts, arXiv **2609.37150** v1, https://arxiv.org/abs/2609.37150, curl **200**. Title / 7 authors in abs order: Tianhang Pan, Xuanhao Wang, Yiwen Pang, Bo Zhou, Jun Yang, Min-Ling Zhang, Shimin Di. Jun Yang carries affiliations 1 and 2. Submitted 2026-09-29. The live and cached abs pages have no Comments field and no journal-ref field (subjects: cs.RO). The abs typo “exsit-ing” was not copied into the lesson.
- https://arxiv.org/html/2609.37150 — curl **200**; v1 HTML body read as a cross-check (R2C Restoration, ETCA, camera-shift failure mode), not a second conflicting body.
- https://arxiv.org/pdf/2609.37150 — curl **200**; sha256 `f2a39ba43d97ea5e352dac577cc8c97c4456e6ed47e6488ac800d81aa98366e5`. PDF title page prints `{tianhang.pan,shimin.di}@seu.edu.cn`. **No** corresponding-author dagger and **no** equal-contribution star are visible on the title page; the email line is not a corresponding-author mark, and the HTML was not used to invent one. The typographic PDF title is the same paper as the abs title. Paper figures 13.3 % / 83.3 % / 1.6 m 以论文为准.

- Arora, Agarwal, Agrawal, CoBoVLA: Decoupling Language from Action with Discrete Codes for Robust and Interpretable Robot Manipulation, arXiv **2611.22395** v1, https://arxiv.org/abs/2611.22395, curl **200**. Title / 3 authors in abs order: Mehul Arora, Dhruv Agarwal, Ambuj Agrawal. Submitted 2026-11-17. The live and cached abs pages have no Comments field and no journal-ref field (subjects: cs.CV + cs.RO).
- https://arxiv.org/html/2611.22395 — curl **200**; v1 HTML body read as a cross-check (three stages, paraphrase protocol, failure localization, discrete-versus-continuous step codes), not a second conflicting body.
- https://arxiv.org/pdf/2611.22395 — curl **200**; sha256 `d436d26f72d26b5027f19f425be25d93d01fcb196a81ceeafa9eecda5e87bf53`. PDF title page: Mehul Arora¹ and Dhruv Agarwal¹ (UC San Diego), Ambuj Agrawal² (Carnegie Mellon University). **No** equal-contribution or corresponding typography is visible. The prose “contributions are as follows” is a bullet list, not a footnote mark. Paper figures 91 % / 27.2 % / 91.4 % / 82.8 % / 81.1 % / 36.5 % / 17 ms / 4,092 paraphrases 以论文为准.

AnyCamVLA (arXiv 2603.05868) was opened in the proposal and **not adopted**. It was not added to the multi-view-extrinsics host.

Real RGB-D / point-cloud renderer / VLA weights / LIBERO / LIBERO-Para / GPU: 本页未运行. Paper figures 以论文为准.

## Declared headers and first-run results

Official first run: 2026-11-20 09:36:09 Asia/Shanghai. Official expected sha256:

- `examples/month-10/expected/corevla_training_view_restore_toy.txt` `df5aae53eed9cd26b214fa79589d57159ee0228c65afd7cb3fad5030a3f43720`
- `examples/month-6/expected/cobovla_paraphrase_codes_toy.txt` `eb520245d06bb21f726ecc2ba9efb5b1cfb2861ecf10c0cee5a661adc43441ca`

Both files were rerun twice and `cmp` was byte-identical.

Common random numbers: the training-view toy shares markers, training extrinsics, shifted extrinsics and render-noise draws across arms at each regime and seed (five seeds). The paraphrase-code toy shares tasks, canonical instructions, official paraphrases and scene order across arms at each regime and seed (five seeds).

CoRe-VLA declared stand-in: `SHIFT_OFFICIAL=0.2000` m along +x with fixed training orientation, `SHIFT_NONE=0.0000` m, `RENDER_SIGMA=0.5000` px, `FX=FY=400.0000`, `CX=CY=160.0000`, `TRAIN_EYE=(0.0000, -0.8000, 0.6000)` m, `SMALL_FRAC=0.2000`. Hand calc (printed): noiseless training cup/bowl uv, principal-point distances `24.8691` / `86.8298` px, closer=cup; noiseless official-shift RMSE `78.5675` px, closer=bowl; `0.2000`. no_shift: B-A `rmse_px -4.863e-15+-1.254e-14`, numerically zero (effective tie); B-A `order_acc 0.0000+-0.0000`, tie: identical on every seed — declared may-near-tie held (stricter). large_shift: B-A `rmse_px -77.9351+-0.2948`, clear, 5/5; B-A `order_acc 1.0000+-0.0000`, clear, 5/5 — held. C matches A on large_shift and loses to B — lose held.

CoBoVLA declared stand-in: `NGRAM=2`, six official unseen paraphrases, `SMALL_FRAC=0.2000`, foreign-code derangement for official C. Hand calc (printed): 2-gram cosines for every official paraphrase and the coupled choice (all six choose the wrong task). canonical: B-A success `0.0000+-0.0000`, tie: identical on every seed (declared may-near-tie held, stronger); C success `0.0000+-0.0000` lose held. paraphrase: B-A success `1.0000+-0.0000`, clear, 5/5 — held; C success `0.0000+-0.0000` lose held.

## Declared expectations that did not hold

None. Every pre-declared official cell held (no-shift may-near-tie, held as a numerically-zero effective tie plus an identical-seed tie; large-shift restore win; leaked-identity lose; canonical may-near-tie, held as an exact identical-seed tie; paraphrase decoupled win; foreign-code lose). Kept, not retuned.

## Post-hoc choices

None of the official parameters were changed after the first official run. Named alternatives on the same seeds, not adopted:

- Training-view toy: `SHIFT=0.4000` m (`hand_calc` official `0.2000` m vs alternative `0.4000` m). On this larger translation B-A `rmse_px` is `-156.4236+-0.2585`, clear, 5/5, with more points leaving the image. Not adopted, because the official `0.2000` m cell already holds the declared large-shift win and is not the paper's 1.6 m figure.
- Paraphrase-code toy: a continuous pre-quantization vector (wording-sensitive 2-gram scores, then nearest-task quantization) in place of official C's foreign discrete codes. On canonical wording this alternative makes C succeed (`1.0000+-0.0000`) and would drop the official lose cell; on paraphrases it still loses to B (`1.0000+-0.0000`, clear, 5/5), like A. Not adopted, because official C is the foreign-code lose cell.

## Typography notes

Official expected/ uses ASCII minus and `+-` in printed toy numbers, generated with ROUND_HALF_UP. Lesson prose quotes those official strings with the same ASCII minus / `+-` typography. House percentages use a space (`13.3 %`, `83.3 %`, `91 %`, `27.2 %`, `20 %`). The `20 %` cutoff is labelled 手算 in the pages and printed as `0.2000`. The numerically-zero threshold is labelled 手算: 1e-9. No typography or layout rewrite of official numbers after the first run. SimOutput fences (`source="model"`) and a leading `cd` were already in the first official draft; after that run, only the required blank lines around those fences were added (disclosed in en/zh). Chinese bold markers were kept off full-width colons in the first official draft.

## Code changes after the first run

After the first official run, the only page change was to add the blank lines that `check_quotes.py` requires around each new SimOutput fence (one blank line after the opening tag and one before the closing tag). This is disclosed in the en/zh results. Official expected/ was not rewritten and remained byte-identical on rerun after the 2026-11-20 09:36:09 Asia/Shanghai freeze. Official numbers were not rewritten. The leading `cd` in the run-the-toy bash snippets was already in the first official draft. expected/ was not retuned.

## Mismatch with reviewer locks

None. Pre-declared cells held and are disclosed in the en/zh results. Alternatives were named, run on the same seeds, and not adopted. Paper figures stay 以论文为准. Real RGB-D / LIBERO / VLA hardware 本页未运行. Both abs pages have no Comments / journal-ref, matching the proposal note.

## Lock changes

New batch-26 PR3 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, CoRe-VLA / CoBoVLA contracts, sources, plans, README, declared regimes) plus `tools/test_b26p3_corevla_cobovla_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (44100→44460, M10 4110→4290, M6 4200→4380, multi-view-extrinsics 450→630, vla-models 1410→1590). Historical strings inside already-written plan/sources files were not edited, including the batch-26 PR2 live-at-the-time site **44100** strings and the previous Current headers (`M10 4110`, `M6 4200`). The b19p3 vla-models “last before Summary” lock was tipped (not relaxed) to also accept the later CoBoVLA heading, following the existing b19p2 Steinhart–Hart pattern. No lock relaxed. `kinematics.py`, `grip_sweep.py`, `package.json` / lockfile, and `.github/workflows` are untouched.

- README `/44 100/` and `约 44 100 分钟` → `/44 460/` and `约 44 460 分钟`.
- Curriculum sum checks `44100` → `44460`; live M10/M6 sum checks 4110→4290 and 4200→4380; live host-minute checks 450→630 on multi-view-extrinsics and 1410→1590 on vla-models.
