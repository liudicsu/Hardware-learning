# Batch-24 PR1 sources

Base `80c9b9d3b5d706eba950636c5916b473ef934d70` (batch-23 polish #196 merged; 71 lessons, site **41220**). This PR: **M2 3750→3930**, **M5 3570→3750**, site **41220→41580** (41580=41220+180+180), still 71 lessons. Hosts: `sensors-fusion` 900→**1080**, `control-modelling` 780→**960**.

## Opened sources

- Wikipedia, Steinhart–Hart equation, oldid 1291894974, https://en.wikipedia.org/w/index.php?title=Steinhart%E2%80%93Hart_equation&oldid=1291894974 action=raw, HTTP 200. Last modified 2025-05-24 01:30:53 UTC = 2025-05-24 09:30 Asia/Shanghai. Forward map 1/T = A + B ln R + C (ln R)^3; three-point coefficient solve; inverse R = exp(cbrt(y − x/2) − cbrt(y + x/2)) with x = (1/C)(A − 1/T) and y = sqrt((B/(3C))^3 + x^2/4). This inverse is the only R(T) used in the toy and the lesson.
- Wikipedia, Thermistor, oldid 1380549254, https://en.wikipedia.org/w/index.php?title=Thermistor&oldid=1380549254 action=raw, HTTP 200. Last modified 2026-10-16 12:03:39 UTC = 2026-10-16 20:03 Asia/Shanghai. Same-family forward map with a, b, c; B-parameter reduction; linear ΔR = k ΔT only over a limited range; example a = 1.40e-3, b = 2.37e-4, c = 9.90e-8 for a typical 3 kΩ-at-25 °C part; “error generally less than 0.02 °C over a 200 °C range”. Those example coefficients and the 0.02 °C claim are 以原文为准 and are not toy outputs. The Thermistor page's rearranged inverse was not mixed in.
- Wikipedia, Nyquist stability criterion, oldid 1376383390, https://en.wikipedia.org/w/index.php?title=Nyquist_stability_criterion&oldid=1376383390 action=raw, HTTP 200. Last modified 2026-09-23 21:20:30 UTC = 2026-09-24 05:20 Asia/Shanghai. N = Z − P; clockwise encirclements of −1; Z = N + P; closed-loop stable iff Z = 0; an open-loop-unstable plant needs one counter-clockwise encirclement per open-loop right-half-plane pole; Bode is less general. The title “Nyquist plot” is only a redirect, not a second body, and is not cited as one.

Resource cards: wiki-steinhart-hart, wiki-thermistor, wiki-nyquist-stability. A real thermistor, calibration bath, MPU-6050 TEMP_OUT reading, real plant or analyser: 本页未运行.

## Declared headers and first-run results

Common random numbers: the Steinhart–Hart toy shares the resistance-noise draw across arms at each regime and seed (five seeds). The Nyquist toy is a deterministic contour; every seed sees the same plants and the same omega grid (five seeds still printed).

Steinhart–Hart declared stand-in points (not the Wikipedia 3 kΩ example): (25000.0000 Ω, 0.0000 °C), (10000.0000 Ω, 25.0000 °C), (1500.0000 Ω, 80.0000 °C). Solved A, B, C = 1.7038685512e-03, 1.1164361508e-04, 7.9592857047e-07 (declared toy parameter). mid_range: paired B−A rmse_C −0.0064±0.0142, near-tie, 3 of 5 opposite — held. wide_span: paired B−A −4.1852±0.4341, clear, 5/5 — held. out_of_range: paired C−B 11.6515±0.2455, clear, 5/5 — held. Arm C is raw ADC counts treated as temperature; a narrow-range Steinhart–Hart solve on the same three-parameter curve recovers the same A, B, C and is printed only as an alternative.

Nyquist declared plants: ol_stable_joint num=(72.0,), den=(1.0, 6.0, 36.0), P=0, first PM = 49.3542°, Z = 0, paired B−A call 0.0000±0.0000, tie identical on every seed — held (declared as agree / may near-tie). ol_unstable num=(8.0, 1.6), den=(1.0, 3.0, −4.0), P=1, first PM = 90.1206°, Z = 1, paired B−A miss -1.0000±0.0000, clear, 5/5 — held. nmp_encircle num=(−5.0, 1.0), den=(1.0, 3.0, 2.0), P=0, first PM = 84.9799°, Z = 2, paired C−B miss 1.0000±0.0000, clear, 5/5 — held. Step-stability bound: |y| clipped at 20.0000; ISE to t_end = 20.0000 with Euler dt = 0.0010.

## Declared expectations that did not hold

None.

## Post-hoc choices

None. No constant, arm, metric or regime was changed after the first run. Alternatives on the same seeds (local linear ΔR = k ΔT; narrow-range Steinhart–Hart coefficients; a 20-point-per-decade omega grid) were printed and not adopted.

## Code changes after the first run

The first-line Wikipedia disclaimer in the Steinhart–Hart toy and expected/ header was reworded after the first run so the 0.02 °C figure is not printed as a toy output; result blocks were left byte-identical (proved by diff from “Regimes and parameters” onward). Pages and this note disclose that print-only header change. After local checks, the English disclosure of that header change was placed in the Steinhart–Hart section (it had been inserted into the previous I²C clock-stretching paragraph by mistake, and that paragraph was restored); the Chinese disclosure sentence was adjusted so the full stop sits outside the bold span. No retune.

## Mismatch with §9

None on the pre-declared cells. The ol_stable_joint “may near-tie” cell came back as an identical tie; it is kept, not retuned.

## Lock changes

New batch-24 PR1 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, difference directions, sources, plans, README, declared regimes, post-first-run none) plus `tools/test_b24p1_steinhart_nyquist_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (41220→41580, M2 3750→3930, M5 3570→3750, sensors-fusion 900→1080, control-modelling 780→960). The cited 0.02 check uses the same digit-boundary as the prose matcher so a later digit in an expected/ figure such as 0.0224 is not treated as the Wikipedia 0.02 °C claim. An accidental ASCII hyphen on the existing Diffusion Forcing curriculum “div −1.0000±0.0000” line was restored to the unicode minus so an earlier difference-direction lock does not see a new token. No lock relaxed. The unused laterSum deletion is left in place; laterOft and laterHi stay.

- README `/41 220/` and `约 41 220 分钟` → `/41 580/` and `约 41 580 分钟`.
- Curriculum sum checks `41220` → `41580`; the current month-total table and the live M2/M5 sum checks 3750→3930 and 3570→3750; live host-minute checks 900→1080 on sensors-fusion and 780→960 on control-modelling.
