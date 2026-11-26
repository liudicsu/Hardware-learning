# Batch-31 PR1 sources

Unit: H1 official NIST Type A standard uncertainty of the mean (`bench-multimeter`, 540→720). Site **46620** = 46440+180; M1 **3450** (still lightest); still 71 lessons. Branch `feat/nist-type-a-uncertainty` from `223e6cdf2b125048dc8c35b85cab7f4adcebf879`. Site typography after this PR is `46 620`. M2 stays 4470; M8=M11 stay jointly heaviest at 4530. These load facts are recorded here and in the month-1 plan Current header only, not as a student-facing process lecture. Parent accepted the one-unit batch; this PR is the only unit. No PR2 was started.

## Pins actually opened (re-fetched live at writing)

Official NIST Type A HTML and equation GIFs were re-fetched immediately before the sources note was written, at **2026-11-26 14:41:43 Asia/Shanghai** (response Date Thu, 26 Nov 2026 06:41:43 GMT). GIFs were opened visually. 以原文为准.

- `https://physics.nist.gov/cuu/Uncertainty/typea.html` — HTTP **200**, `Content-Type: text/html`, **9023** bytes, Last-Modified Thu, 09 May 2024 16:14:20 GMT = **2024-05-10 00:14:20 Asia/Shanghai**. Title: “Evaluating uncertainty components: Type A”. Full-page sha256 `c2c9b4eb391ee0c861ff6ff5698cc94f2bbddb3b55bdc23be347d6ea8c40cb62`. This full-page hash moved relative to the parent's re-fetch `a4f8f7d78ea9cadea385536be79243729c703f62f6f613b4f4716eced096e813` and the writer's pin `420dbe2b41a77010839c2f3ad857ea1bea9fe7b06f9aba9bb920014740dfbb70` because of a trailing Cloudflare `__CF$cv$params` script (1130-byte tail that also includes `</BODY>\n</HTML>\n`). Length, Last-Modified, CF-stripped body, and GIF pins rematched, so the moved full-page hash is not treated as a scientific revision.
- CF-stripped Type A body (bytes before the trailing `<script>` that contains `__CF$cv$params`): sha256 `4eda5d64cda840936c444b6e324e8b121ca0835327dfc85fb355f7acd1fd5e43` (**7893 B**). Rematched.
- Official eq (4) GIF `https://physics.nist.gov/cuu/Uncertainty/equations/eqa4.gif` — HTTP **200**, `image/gif`, **703** B, same Last-Modified, sha256 `426a2ce072666a6fba172c86e81897458d6521ee2097de469715485e6b54247a`. Rematched. Opened visually: \(x_i=\bar X_i=\frac{1}{n}\sum_{k=1}^{n} X_{i,k}\).
- Official eq (5) GIF `https://physics.nist.gov/cuu/Uncertainty/equations/eqa5.gif` — HTTP **200**, `image/gif`, **1575** B, same Last-Modified, sha256 `4445412921d019ea75601cfd0f81939ca3ade00a514626ef67358bbc16a8cdb7`. Rematched. Opened visually: \(u(x_i)=s(\bar X_i)=\bigl(\frac{1}{n(n-1)}\sum_{k=1}^{n}(X_{i,k}-\bar X_i)^2\bigr)^{1/2}\).
- Official Type A HTML has **0** hits for `sqrt` / `s/√n` / `s/sqrt`. The official display is eq (5). An algebraic check that eq (5) equals \(s/\sqrt{n}\) is labelled 手算 and is printed by the toy; it is not invented as a second official displayed equation.

This Type A URL was **not** already in `src/lib/resources.ts`, `src/lib/curriculum.ts`, or the host MDX; it is added here as a new Resource / reading-map / curriculum entry `nist-uncertainty-typea` and is the formula body. The existing `nist-uncertainty-typeb` resource is `https://physics.nist.gov/cuu/Uncertainty/typeb.html` and does not already cover Type A eqs (4)–(5). The existing `nist-uncertainty-propagation` resource is handbook `mpc55.htm` and is not rewritten.

Claims used from the opened Type A page, 以原文为准: “A Type A evaluation of standard uncertainty may be based on any valid statistical method for treating data…” (including the named least-squares and ANOVA examples, which are not this unit's cut); the sample-mean sentence leading to official eq (4); “the standard uncertainty \(u(x_i)\) to be associated with \(x_i\) is the estimated **standard deviation of the mean**” leading to official eq (5). Supporting Type A / Type B definitions from the already-opened basic page, and the already-cited Type-B “manufacturer's specifications” contrast, are used only as supporting definitions / contrast. No coverage factor \(k\), 95 % expanded uncertainty, or Welch–Satterthwaite degrees of freedom were invented as if they were eq (5). Official Type A examples were not claimed as real DMM measurements on this page.

Lesson-chosen toy parameters (`MU=5.0000` V, `SIGMA=0.0200` V, `N=16`, `N_LARGE=64`, `N_ALT=256`, `L=0.0500` V, `uB=L/sqrt(3)=0.0288675135` V, `clear_frac=0.2000`, work plan `30+25+50+40+35=180`) were named in the toy header / `hand_calc` lines before the official first run. Observations are synthetic; Arm B is the already-taught \(L/\sqrt{3}\) conversion and is not computed from this series. Arm C's single pre-declared lose mode (treat the observation sample standard deviation \(s\) as if it were \(s(\bar X)\)) was declared before the first official run. Real DMM / calibration laboratory / repeated physical observations 本页未运行.

## Official first run

`type_a_mean_uncertainty_toy.py`, 2026-11-26 14:52:20 Asia/Shanghai, byte-identical on an immediate rerun. Expected sha256 `2905a8b2d685dcdb3249efae3f26c5ad4b0df8f1beb21eab0f2eb43692bee5d9`. Official `expected/` was not retuned.

## Pre-declared cells

All held and are disclosed in the en/zh results.

- official identity / 手算 check: paired A-hand_s_over_sqrt_n `0.0000+-0.0000: tie: identical on every seed` at n=16 and at n=64 (and on the unused alternative n=256). The 手算 `C/A` versus `√n` is the same exact tie (`4.0000000000` at n=16, `8.0000000000` at n=64). Held as an exact tie; kept.
- larger n (same seed family, CRN): paired A(n=64)-A(n=16) `-0.0020+-0.0006`, **clear**, same sign on all 5 seeds (Arm A shrinks consistently with the official \(1/(n(n-1))\) formula, from `0.0046+-0.0007` V to `0.0025+-0.0003` V). Paired B(n=64)-B(n=16) `0.0000+-0.0000: tie: identical on every seed` (Arm B stays put at `0.0289+-0.0000` V = 手算 `0.0288675135` V). Held; kept.
- C loses: paired C-A at n=16 is `0.0137+-0.0022`, **clear**, same sign on all 5 seeds; at n=64, `0.0177+-0.0022`, **clear**, 5/5. The lose mode is only the \(s\) vs \(s(\bar X)\) confusion. Held; kept.
- Named alternative `n=256` was printed on the same seed family (CRN) and not adopted (A shrinks further to `0.0012+-4.206e-05` V; paired A(n=256)-A(n=64) `-0.0013+-0.0003`, still clear, 5/5; B stays put).

## Post-first-run disclosures

There was no official toy or `expected/` change after the first run. After the first `check_diagrams.mjs` run, the new sources-note lock looked for the substring `s vs`, which did not appear because this note writes the lose mode as `s` versus `s(\bar X)` with TeX delimiters; the lock was pointed at the existing `s(\bar X)` wording already in this note. Official expected/ was not retuned. After the first `CI=1 npm run build`, MDX treated `{i,k}` and other bare `{…}` in the official-eq prose as JavaScript (`ReferenceError: i is not defined` while prerendering `/en/month/month-1/bench-multimeter` and the zh page). The official eqs were moved into house `<Formula>` string children, and inline math that used braces was rewritten with backticks and Unicode, following the lesson's existing Type-B / Kelvin / true-RMS style. Official expected/ was not retuned. No lock relaxed. Lesson prose (including the SimOutput embedding and the results / work-plan wording), hooks, curriculum, plans, sources, README typography and tip locks were written after those figures were frozen. `|m| <= sd` was wrapped in backticks in the first official en/zh draft so the less-than sign would not be parsed as a tag; official expected/ was not retuned. No lock relaxed. Existing `dmm_uncertainty_toy.py`, `kelvin_four_wire_sense_toy.py`, `true_rms_vs_average_responding_toy.py` and their `expected/`, and the existing Type-B / Kelvin / true-RMS / CAT / input-impedance / current-shunt / common-mistakes wording, were not retuned or edited. The existing Summary bullets were left byte-untouched except the allowed one new Summary sentence and the new section immediately before `<Summary>`. Avoided hosts were not reopened. `package.json` / lockfile, `.github/workflows`, and the authoritative proposal file were not edited. `tools/test_b30p1_monotonic_vs_wallclock_timeout_toy.py` is a hook-order spy that previously required the monotonic hook to be last immediately before `exit $fail`; it was updated in this change so the new `type_a_mean_uncertainty_toy` hook is last immediately before exit, with the monotonic hook still after `ydelta_network_reduction_toy`. The rest of that test file was not rewritten.

## Mismatch with §9

None.

## Lock changes

New batch-31 PR1 block in `tools/check_diagrams.mjs` (toy, expected, CRN, label order, required `nist-uncertainty-typea` addition, official Type A vs Type-B contrast, sources, plans, README, declared regimes) plus `tools/test_b31p1_type_a_mean_uncertainty_toy.py`. Tipped site-total, host-minute, month-total and Current-header locks only (46440→46620, M1 3270→3450, bench-multimeter 540→720, README `46 440`→`46 620`). Historical strings inside already-written plan/sources files were not edited, including `Current / 当前：**M1 3270 min**, Batch-30 PR1`, `Current / 当前：**M1 3090 min**, Batch-29 PR1` and `Current / 当前：**M1 2910 min**, Batch-22 PR1`. M2 stays 4470; M8=M11 stay 4530. No lock relaxed.

- README `/46 440/` and `约 46 440 分钟` → `/46 620/` and `约 46 620 分钟`.
- Curriculum sum checks `46440` → `46620`; live M1 sum checks 3270→3450; live host-minute checks 540→720 on bench-multimeter.
- Current-curriculum month table: M1 3270→3450; other months unchanged.
