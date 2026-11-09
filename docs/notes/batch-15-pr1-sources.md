# Batch-15 PR1 source, scope and validation audit

Base: `df3c1d8` (batch-14 closed incl. polish #160; site **31380**). Proposal `batch-15-proposal.md` §9 PR1 locks: H1 1.5 python-terminal Nyquist / aliasing +150, H2 3.4 pid-control notch filter +180. No arithmetic mismatch: curriculum.ts on base gives M1 1800 / M3 2310 / site 31380 (python-terminal 180, pid-control 360, as the proposal states); after this PR M1 **1950**, M3 **2490**, site **31710**; 71 lessons. No new slugs, no Month 12. All prior expected files remain byte-identical; two expected files are added.

## Opened sources (curl -L + body read, 2026-11-10, Asia/Shanghai UTC+8)

- `wiki-nyquist-shannon` / Wikipedia — Nyquist–Shannon sampling theorem: https://en.wikipedia.org/wiki/Nyquist–Shannon_sampling_theorem, HTTP 200, HTML body verified (mw-parser-output; revision 1380977741). Shannon's statement (no frequencies above B hertz → determined by samples spaced less than 1/(2B) s apart); sufficient rate anything above 2B; equivalently B < fs/2; 2B = Nyquist rate (attribute of the input), fs/2 = Nyquist frequency (attribute of the sampling equipment); too high a bandlimit → aliasing. 以原文为准.
- `wiki-aliasing` / Wikipedia — Aliasing: https://en.wikipedia.org/wiki/Aliasing, HTTP 200, HTML body verified (mw-parser-output; revision 1372423745). Reconstructed signal gains low-frequency components absent from the original when components exceed fs/2; real-sinusoid aliases |f + N·fs|; folding frequency fs/2; Nyquist condition fs/2 > |f|; anti-aliasing low-pass filters before sampling, attenuated components still alias at low amplitude. 以原文为准.
- `wiki-band-stop` / Wikipedia — Band-stop filter: https://en.wikipedia.org/wiki/Band-stop_filter, HTTP 200, HTML body verified (mw-parser-output; revision 1380964572). Band-stop passes most frequencies and attenuates one range; notch = band-stop with a narrow stopband (high Q); standard notch H(s) = (s² + ω0²)/(s² + ωc s + ω0²) with ω0 the central rejected frequency and ωc > 0 the rejected bandwidth; 59–61 Hz anti-hum example; PA / instrument-amplifier feedback notches. 以原文为准.
- Also fetched (HTTP 200, body read, not carded): Wikipedia — Nyquist frequency (https://en.wikipedia.org/wiki/Nyquist_frequency); the two cited pages already cover everything the lesson states.
- Existing `pid-control` lead–lag section (resonant_light divergence, "the notch filter is outside this section") and `python-terminal` lesson body: read in-repo and extended in place.

Derived in the lesson, not quoted: the folding formula `min(f mod fs, fs − (f mod fs))`, the Butterworth magnitude `1 / √(1 + (f/FC)^8)`, the notch phase at crossover (−18.4° at 20 rad/s for ω0 = 40, ωc = 20 rad/s), and the RK4 bound `|R(H·λ)| ≤ 1`; each is verified numerically in the toys and in `tools/test_b15p1_aliasing_notch_toys.py`. No ADC datasheet, oscilloscope manual or servo modal-test source was opened; sample rates, filter order, noise and plant constants are toy choices, and the lesson says so.

Not cited: no source was blocked. Every source named in the proposal for PR1 was readable without login.

Cached under `/workspace/b15p1-sources/` on the worktree host (not committed): `nyquist.html/.txt`, `aliasing.html/.txt`, `bandstop.html/.txt`, `nyqfreq.html/.txt`.

## Toy design

- `nyquist_aliasing_toy.py` (1.5): ideal impulse sampling of integer-Hz tones over a 1 s record, plain DFT (1 Hz bins). Closed-form samples: **no time step**, so no integration-step criterion applies (the tests check the script has none, and check the Nyquist boundary at 0.98× / 1.02× of fs/2: 49 Hz → 49 Hz, 51 Hz → 49 Hz at fs = 100 Hz). Arms A_low 50 Hz / B_aaf 200 Hz + 4th-order Butterworth magnitude prefilter (FC = 0.25 fs, steady-state amplitude only) / C_raw 200 Hz. **Common random numbers** per (regime, seed, trial): wanted tone frequency, amplitude, phase, interferer frequency and phase, ADC noise record (the 50 Hz arm uses its first 50 samples). 5 seeds × 8 trials. Key numbers: slow_tone A−B freq / false **tie: identical on every seed**, A−B amp 0.1110±0.0533 clear 5/5 (fewer samples), C−B amp −1.322e-06±2.423e-06 near-tie; single_tone A−B freq 29.8500±0.3791 clear 5/5, A−B false 1.0000±0.0000 clear 5/5, C−B freq / false tie, C−B amp −8.1064±0.5337 clear 5/5 (**B loses** amplitude to passband droop); interferer C−B false 0.9750±0.0559 clear 5/5, C−B amp −0.1308±0.1390 near-tie (same sign on all 5, but |m| ≤ sd), A−B amp 3.0909±4.6715 near-tie (1 of 5 opposite); near_edge C−B amp −84.4824±1.3352 clear 5/5 (**B loses**: corner at 50 Hz eats a 70–90 Hz tone although B counts as safe 40/40).
- `notch_vs_lead_resonant_toy.py` (3.4): the lead–lag toy's LTI joint. Arms A PID / B PID + notch (ω0 = 40 rad/s, ωc = 0.5 ω0) / C PID + lead–lag (reproduces the lead–lag toy's B_leadlag to 1e-9, tested) / D notch at 0.7 ω0. One recipe, |L(j WC)| = 1 at 20 rad/s for every arm. **Common random numbers** per seed: three reference steps, three load steps, noise sequence. RK4 H = 0.25 ms; largest stable step 139.3 / 70.9 / 73.5 / 72.7 ms, asserted every run; tests: decay at 0.98× and growth at 1.02× of h_max on the zr = 0.05 mode, H vs H/2 agree to 1e-6, discrete notch matches the continuous one to 1e-3. Loop-stability criterion: GM > 0 dB, PM > 0° on the Bode proxy and no divergence on ≥ 4 of 5 seeds. Key numbers: well_damped B−A ise 5.5960±1.4179, over 10.9526±0.0092 (**B loses**, clear, 5/5); resonant (zr 0.3) B−A ise 27.4063±6.9473, over 24.4897±0.0409 (**B loses**, clear, 5/5), C−A ise −2.8025±0.6749 (lead–lag small but consistent win, as in the lead–lag section); resonant_light (zr 0.2) B GM 0.80→2.35 dB but B−A ise 7.5146±3.5371 small but consistent loss, over 14.8871±3.5792 clear loss, du 0.0008±0.0009 near-tie; C diverges 5/5, D loses all three; resonant_sharp (zr 0.05) A, C, D diverge 5/5, B stable (PM 38.3°, GM 2.03 dB).

No line in either expected file triggers the numerically-zero rule; the rule (|m| and sd < 1e-9, checked after the exact-tie test and before the sd test, no sign count) is implemented, unit-tested on hand-made data and defined in the en/zh prose.

Independent tests: `tools/test_b15p1_aliasing_notch_toys.py` (also executed by the batch-15 PR1 block in `tools/check_diagrams.mjs`).

## Post-hoc choices (stated in the en/zh prose; alternatives printed)

1. **slow_tone** (Nyquist toy): added after the first run, to show a case where 50 Hz is enough. The first run's three regimes and every parameter (FC = 0.25 fs, order 4, threshold 0.05, noise 0.01, 8 trials) are unchanged, so the three-regime alternative is the same three printed blocks.
2. **A_under → A_low** (Nyquist toy): renamed after adding slow_tone, because the 50 Hz arm is not under-sampled there. Name only; no number changes.
3. **Summary print wording** (Nyquist toy): the first run's line said the prefilter costs "a little passband droop" in single_tone; it measured 8.2 %, so the line now says "costs passband droop at 35..45 Hz". Wording only.
4. **resonant_sharp zr = 0.05** (notch toy): picked after a margins-only prototype that also tried zr = 0.1. The toy prints the zr = 0.1 margins (A −66.8°, B 34.5° / 2.19 dB, C −58.3°, D −42.7°): same pattern.
5. Not post-hoc, but printed so the choice is visible: notch width ωc/ω0 = 0.5 and mistune 0.7 were fixed before the first run; B's margins at ωc/ω0 = 0.25 and 1.0 are printed for every regime (0.25 fails on resonant_sharp, PM −42.8°).
6. Bug fix, not a parameter: the first notch-toy draft realised first-order Tustin sections as biquads with a cancelled pole at z = −1 and passed the notch coefficients in the wrong order; both were fixed before any number in the lesson was recorded. `test_lead_arm_reproduces_lead_lag_toy` and `test_discrete_notch_matches_continuous` guard them.

## Mismatch with §9

- H1: "under **consistent** alias" ✔ (single_tone A−B freq clear 5/5); "multi-tone without prefilter → (C) consistent false peaks" ✔ (interferer C−B false 0.9750±0.0559, clear 5/5). "B ≪ fs/2 → (A)(B) near-tie / numerically-zero": measured an exact **tie** on frequency and false peaks in slow_tone, but A's amplitude error is a **clear** loss (0.1110±0.0533, 5/5, fewer samples); no numerically-zero line occurs. Extra, not in §9: the prefilter arm B loses amplitude clearly in single_tone and near_edge.
- H2: "well-damped **near-tie**" ✗ — measured: the notch **loses with a clear gap** on the rigid joint (ISE 5.5960±1.4179, overshoot 10.9526±0.0092, 5/5) and also on the zr = 0.3 joint (ISE 27.4063±6.9473). "resonant **consistent** notch stabilize" holds only on resonant_sharp (zr = 0.05: A, C, D diverge 5/5, B stable); on resonant_light the notch improves GM (0.80→2.35 dB) but tracks worse. "mistuned → (C) consistent lose" ✔ (as arm D; the lead arm is kept as C). The numbers were followed, not §9; the lesson reports them as measured.

## Lock changes

Totals only: site 31380→31710 and M1 1800→1950, M3 2310→2490 in the existing curriculum / README locks (all `31 380` README tips → `31 710`, labels renamed b14p3→b15p1); the b13p1 pid-control host-minutes lock 360→540 (host total, as earlier per-host minute locks were moved). The b14p1 month-1 / month-3 plan-header locks that matched `Current / 当前：**M1 1800 min**, Batch-14 PR1` / `**M3 2310 min**` now match the `## Batch-14 PR1` headings (same entries, still required), as #154–#159 did. New b15p1 block added. No lock relaxed.

## Models / reproducibility

opencode free models were tried first with a toy brief (`/workspace/b15p1-opencode/`): `deepseek-v4.1-flash-free`, `glm-5.3-flash-free`, `mimo-v2.6-flash-free`, `longcat-2.5-free` (90 s each) all timed out (exit 124) with no file output; `minimax-m2.5-free` returned an UnknownError (exit 1). Toys, tests and lesson text implemented locally in `/workspace/hl-b15p1`.

## Local validation

`tools/test_b15p1_aliasing_notch_toys.py`, month-1 / month-3 `check.sh`, `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build with postbuild. No workflow edits. Minutes **71 / 31710**.
