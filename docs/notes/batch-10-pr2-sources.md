# Batch-10 PR2 source, scope and validation audit

Base: `59aa6df` (#141 merged; site **26160**). Proposal §9 PR2 locks: H3 1.2 components ESD/TVS +150, H6 11.1 power-battery-emc shared-return ground loop +210. No arithmetic mismatch: curriculum.ts on base gives M1 1020 / M11 3210 / site 26160; after this PR M1 **1170**, M11 **3420**, site **26520**; 71 lessons. All prior expected files remain byte-identical except the two added/updated here. Minutes unchanged from the first #142 land; NEEDS_FIX rework is numerical/topology/prose only.

## Opened sources (curl -L + pdftotext body, 2026-11-09, Asia/Shanghai UTC+8)

- `ti-ssya010` / SSYA010A: https://www.ti.com/lit/an/ssya010/ssya010.pdf, HTTP 200, PDF body verified. HBM = **100 pF + 1500 Ω** component-level stress; clamps discharge ESD current to ground; series resistor isolates a secondary clamp that protects a gate oxide. Numbers 以原文为准.
- `ti-slvae37` / SLVAE37: https://www.ti.com/lit/an/slvae37/slvae37.pdf, HTTP 200, PDF body verified (`pdftotext`). Defines `VRWM`, `VBR` (typically 1 mA), `VCLAMP`, `RDYN`, `IPP`. Explicit formula: **`VCLAMP = VBR + ISURGE × RDYN`**. Also: **`VBR will always be higher than VRWM`**, so with surge current `VRWM < VBR < VCLAMP`. Pick `VRWM` above the nominal rail; do not trust `VBR` alone for leakage. Numbers 以原文为准.
- `ti-slyt512` / SLYT512: https://www.ti.com/lit/an/slyt512/slyt512.pdf, HTTP 200, PDF body verified. Large return loops across splits; joining planes only at the supply makes a bigger loop; single-point star ground at the mixed-signal device; careless multi-point joins create ground loops. Numbers 以原文为准.

Cached under `/workspace/b10p2-sources/` in the worktree host (not committed).

## Toy design (after NEEDS_FIX)

- `esd_tvs_clamp_toy.py` (1.2): shared HBM 100 pF / 1500 Ω, nominal 2 kV ±8 % charge jitter, five seeds.
  - Integration: **backward Euler**, `DT = 1 ps` (clamp τ = RDYN·C_pin = 7.5 ps), `T_END = 1 µs ≥ 5·τ_HBM`. DT-invariance checked (1 ps vs 0.5 ps peak Δ ≪ 1 mV).
  - Short-circuit peak ≈ V/1500 Ω ≈ **1.33 A at 2 kV**.
  - Clamp model: synthetic `VBR = 8 V`, `RDYN = 1.5 Ω` → `VCLAMP ≈ VBR + I·RDYN` (SLVAE37).
  - Arms: A unprotected (pin C only); B TVS at connector (= IC pin); C **TVS at connector → series 33 Ω → IC pin + internal clamp**.
  - Metrics: connector peak, IC-pin peak, peak TVS current, peak IC-clamp current, TVS / IC / R_HBM energies (µJ). Stored ½CV² = 200 µJ; clamp ~1.7 µJ; most energy in the 1500 Ω.
  - Arm C claims only measured IC-pin peak and IC-clamp current (lower than connector / TVS); no “softens the edge” without a rise-time / dV/dt metric.
  - Out of scope (one line in prose): TVS capacitance vs signal speed, and trace inductance.
- `ground_loop_return_ir_toy.py` (11.1): shared motor pulse (8 A ±10 %), shared R map, five seeds.
  - Arms: A shared return; B star; C star + kelvin.
  - Kelvin residual = physical **`I_ADC_BIAS × R_SENSE_LEAD`** (no `0.001·i·R` fudge).
  - **`R_MOTOR_FEED` used**: peak feed drop reported and **not** added to sense bounce (feed IR ≠ return IR into ADC).
  - A vs B is literacy **V = I·R** on the chosen return R, not a chassis measurement.
  - `L·di/dt` is not modelled (one line in prose).

Independent tests: `tools/test_b10_esd_groundloop_toys.py` (DT invariance, ≥5τ, energy split, arm-C topology, Kelvin physics, feed IR).

## Models / reproducibility

opencode free models were tried briefly on the first land; NEEDS_FIX rework implemented locally in `/workspace/hl-b10p2` (node_modules hardlinked via `cp -al`).

## Local validation

`tools/test_b10_esd_groundloop_toys.py`, month-1 / month-11 `check.sh`, `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build. No workflow edits. Minutes unchanged.
