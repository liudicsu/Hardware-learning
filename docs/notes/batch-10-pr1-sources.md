# Batch-10 PR1 source, scope and validation audit

Base: `73add87` (pre-PR1 tip; site **25800**). Proposal §9 PR1 locks: H1 2.1 arduino-io ADC ENOB +180, H2 2.3 sensors-fusion mag hard/soft-iron +180. No arithmetic mismatch: after this PR M2 **3030**, site **26160**; 71 lessons. All prior expected files remain byte-identical except the two added here. Minutes for the later polish PR stay **71 / 26940** (no minute edits).

## Opened sources (curl -L + body read, 2026-11-09, Asia/Shanghai UTC+8)

- `wiki-enob` / Wikipedia — Effective number of bits: https://en.wikipedia.org/wiki/Effective_number_of_bits, HTTP 200, HTML body verified. Formula **`ENOB = (SINAD − 1.76) / 6.02`**; ENOB may be fractional (e.g. a 12-code-bit converter can report ~9.5 effective bits). Numbers 以原文为准.
- `ti-slaa013` / SLAA013 — *Understanding Data Converters*: https://www.ti.com/lit/an/slaa013/slaa013.pdf, HTTP 200, PDF body verified (`pdftotext`). Ideal quantization error ±½ LSB / ±q/2; mean-square quantization noise **`N² = q²/12`**; for a full-scale sine the ideal SNR is **`6.02n + 1.76 dB`** (~**61.96 dB** at n = 10). Numbers 以原文为准.
- `arduino-analog-input` / Arduino analog-input page: https://docs.arduino.cc/learn/microcontrollers/analog-input, HTTP 200. The fetched body is a **JS-rendered Gatsby shell** (`___gatsby` empty wrapper); this page did **not** verify `analogRead`, `1023`, or “10-bit” text from that body. **Marked not verified.** Nominal 10-bit / `5.0/1023` facts in the lesson come from the earlier Analog section plus Wikipedia+TI, not from that curl.
- `vn-hsi-calibration` / VectorNav — Magnetometer Hard & Soft Iron Calibration: https://www.vectornav.com/resources/inertial-navigation-primer/specifications--and--error-budgets/specs-hsicalibration, HTTP 200, HTML body verified. Hard-iron = permanent centre bias (200 / 100 mGauss example); soft-iron stretches the sphere/circle into an ellipsoid/ellipse; compensation `m_c = S_I (m̃ − b_HI)` with a full **3×3** `S_I` (off-diagonals included) and 2D yaw or 3D motion. Numbers 以原文为准.
- `wiki-magnetometer` / Wikipedia — Magnetometer: https://en.wikipedia.org/wiki/Magnetometer, HTTP 200, HTML body verified. Absolute magnetometers need internal calibration or known constants; relative devices measure against an uncalibrated baseline. Numbers 以原文为准.

Cached under `/workspace/b10p1-sources/` on the worktree host (not committed).

## Toy design

- `adc_enob_noise_toy.py` (2.1): shared coherent tone (bin 17 / 1024) + shared mid-riser n=10 quantizer; arms A ideal / B front-end Gaussian noise / C same noise + mild odd cubic; SNR/SINAD from coherent DFT then ENOB from SINAD; five seeds; not a SAR datasheet claim.
- `mag_hard_soft_iron_toy.py` (2.3): shared horizontal field + shared 72-yaw path + shared diagonal soft stretch + shared hard bias; arms A raw / B hard-only / C hard+diagonal-soft; heading |err| and radius residual RMS; five seeds; diagonal soft only (full 3×3 ellipsoid fit is further reading); not an AHRS certification.

Independent tests: `tools/test_b10_enob_magcal_toys.py`.

## Models / reproducibility

opencode free models were tried first on the original land; toys lived in `/workspace/hl-b10p1` at merge. This polish note is written from `/workspace/hl-b10pol` on `fix/batch10-polish` (base `fede4e6`).

## Local validation

`tools/test_b10_enob_magcal_toys.py`, month-2 `check.sh`, `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build. No workflow edits. Minutes unchanged (71 / 26940).
