# Batch-11 PR1 source, scope and validation audit

Base: `262adda` (batch-10 closed; site **26940**). Proposal §9 PR1 locks: H1 1.2 components Wheatstone/INA +180, H2 3.1 cad-parametric GD&T stack +150. No arithmetic mismatch: curriculum.ts on base gives M1 1170 / M3 1620 / site 26940; after this PR M1 **1350**, M3 **1770**, site **27270**; 71 lessons. All prior expected files remain byte-identical except the two added here.

## Opened sources (curl -L + body read, 2026-11-09, Asia/Shanghai UTC+8)

- `ti-sloa034` / SLOA034 — *Signal Conditioning Wheatstone Resistive Bridge Sensors*: https://www.ti.com/lit/an/sloa034/sloa034.pdf, HTTP 200, PDF body verified (`pdftotext`). Bridge sensors produce differential `Vsig` on a common-mode near `½ Vexc`; full-scale outputs typically **10–100 mV**; need differential / instrumentation amps that reject common mode. Numbers 以原文为准.
- `ina126-ds` / INAx126 datasheet: https://www.ti.com/lit/ds/symlink/ina126.pdf, HTTP 200, PDF body verified (`pdftotext`). Gain equation **`G = 5 + (80 kΩ / RG)`** (5…10000 V/V); low input offset (250 µV max class); **CMRR min 80 dB** (typ 94 dB, `RS = 0 Ω`) — used as the toy’s finite CMRR. Numbers 以原文为准.
- `wiki-wheatstone` / Wikipedia — Wheatstone bridge: https://en.wikipedia.org/wiki/Wheatstone_bridge, HTTP 200, HTML body verified (mw-parser-output present). Two divider legs; `V_G` is the mid-point difference; balance when ratios equal. Numbers 以原文为准.
- `wiki-gdt` / Wikipedia — Geometric dimensioning and tolerancing: https://en.wikipedia.org/wiki/Geometric_dimensioning_and_tolerancing, HTTP 200, HTML body verified. Feature control frames; equal/unequal bilateral tolerances; datums / datum references; MMC/LMC appear in the article. Numbers 以原文为准.
- `wiki-tol-analysis` / Wikipedia — Tolerance analysis: https://en.wikipedia.org/wiki/Tolerance_analysis, HTTP 200, HTML body verified. Worst-case vs statistical stack-up; RSS and Monte Carlo named. Numbers 以原文为准.

Cached under `/workspace/b11p1-sources/` on the worktree host (not committed).

## Toy design

- `wheatstone_bridge_sense_toy.py` (1.2): shared `Vexc`/`R0`/`G` and per-regime `(δ, CM σ)`; **common random numbers** for CM across A/B/C; CM added to both bridge legs then differential + residual `cm/10^(CMRR/20)` with **CMRR = 80 dB** (INA126 min); multi-sample SNR (`N=64`); regimes small-δ noisy-CM (bridge wins) and large-δ quiet-CM (near-tie / small gap ~2.6 dB from finite CMRR residual + DIFF_NOISE; multi-sample SNR cannot see static Vos); five seeds; ≠ ESD/ENOB.
- `gdt_tolerance_stack_toy.py` (3.1): shared bilateral half-widths per regime; arms A worst-case / B RSS / C datum re-root; short_chain (1 dim, worst==RSS tie); long_normal (`σ = t/3`); long_skew (violates RSS iid/centered/normal assumptions — unsafe); five seeds; no ASME certification claim.

Independent tests: `tools/test_b11_bridge_gdt_toys.py`.

## Models / reproducibility

opencode free model `deepseek-v4.1-flash-free` was tried first (45 s); returned empty. Toys implemented locally in `/workspace/hl-b11p1` (`cp -al` node_modules from hl-b10pol).

## Local validation

`tools/test_b11_bridge_gdt_toys.py`, month-1 / month-3 `check.sh`, `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build. No workflow edits. Minutes **71 / 27270**.

## NEEDS_FIX follow-up (same PR)

- Wheatstone: shared CM draws across arms; CM on both bridge legs; finite CMRR 80 dB (INA126 min); multi-sample SNR; δ=GF·ε literacy; comments/prose/expected synced.
- GD&T prose: RSS needs independent/centered/approx-normal parts; `long_skew` unsafe because it violates them; 3σ convention `±t ≈ ±3σ` ⇒ `σ = t/3`.
- Minutes unchanged (27270 / M1 1350 / M3 1770).

## NEEDS_FIX follow-up 2 (same PR)

- Relabel `large_delta_quiet_cm` as **near-tie / small gap** (接近打平 / 差距很小), not a true tie; remaining ~2.6 dB from finite-CMRR residual + private `DIFF_NOISE`.
- Explicit prose: multi-sample SNR cannot see static `Vos` (cancels in Δmean); C’s slightly higher SNR does not mean C wins — cost is offset / absolute accuracy.
