# Batch-14 PR1 source, scope and validation audit

Base: `db28b03` (batch-13 closed incl. polish #156; site **30270**). Proposal `batch-14-proposal.md` §9 PR1 locks: H1 1.3 bench-multimeter Kelvin four-wire +150, H2 3.2 fdm-printing pressure advance +180. No arithmetic mismatch: curriculum.ts on base gives M1 1650 / M3 2130 / site 30270 (bench-multimeter 240, fdm-printing 180); after this PR M1 **1800**, M3 **2310**, site **30600**; 71 lessons. No new slugs, no Month 12, no M9 / M11 edits. All prior expected files remain byte-identical; two expected files are added.

## Opened sources (curl -L + body read, 2026-11-10, Asia/Shanghai UTC+8)

- `wiki-four-terminal` / Wikipedia — Four-terminal sensing: https://en.wikipedia.org/wiki/Four-terminal_sensing, HTTP 200, HTML body verified (mw-parser-output; oldid 1361618432). Separate force (current) and sense (voltage) pairs; separation eliminates lead and contact resistance, an advantage for low resistance (cites a Racal-Dana LCR bridge manual: four-terminal below 100 Ω); sense connections adjacent to the impedance, almost no current to the instrument so the sense-lead drop is negligible; sense inside, force outside, exchanging them lets more lead resistance in; force wires need adequate gauge; three-wire RTD variant less accurate than four-wire. 以原文为准.
- `marlin-lin-advance` / Marlin — Linear Advance: https://marlinfw.org/docs/features/lin_advance.html, HTTP 200, HTML body read (Jekyll page, server-rendered text). Extruder not a linear system → extra material at the end of each move, bleeding corners; LIN_ADVANCE decouples extrusion; v1.5 K unit mm of filament compression per 1 mm/s extrusion speed, K around 0.1–2.0 (v1: 30–130); past the extruder jerk limit the print acceleration is reduced; too low K: starved line on acceleration, too much material on deceleration; too high K reverses that; disable slicer "coast at end" / pressure options; Bowden needs higher K. 以原文为准.
- `klipper-pressure-advance` / Klipper — Pressure advance: https://www.klipper3d.org/Pressure_Advance.html, HTTP 200, HTML body read. TUNING_TOWER FACTOR=.005 (direct drive) / .020 (long Bowden); value = start + height × factor; below ideal: corner blobs; above ideal: rounded corners and poor extrusion leading up to the corner; typical 0.050–1.000; depends on extruder, nozzle, filament, temperature and extrusion rate; test at high flow (e.g. 100 mm/s); high values (over 0.200) with high acceleration may make the extruder skip. 以原文为准.
- Klipper — Kinematics (§ Pressure advance): https://www.klipper3d.org/Kinematics.html, HTTP 200, HTML body read. Hooke's-law pressure, Poiseuille flow, `pa_position = nominal_position + pressure_advance_coefficient * nominal_velocity`; extruder retracts during deceleration; smoothing via `pressure_advance_smooth_time`. Cited in the lesson prose together with the Pressure advance page (one resource card, `klipper-pressure-advance`).
- Marlin — M900 page (https://marlinfw.org/docs/gcode/M900.html, HTTP 200) was fetched but not cited; the lesson already mentions M900.
- Existing `fdm-printing` "Flow, pressure advance and retraction" prose and the `bench-multimeter` GUM section ("lead resistance … not simulated"): read in-repo and extended in place.

Derived in the lesson, not quoted: the two-wire sum `R + 2 r_lead + 2 r_contact`, the Kelvin divider `R × R_IN / (R_IN + r_sense)`, the melt ODE and the explicit-Euler bound `DT < 2/λ` with `λ = dq/ds = q/(n s)`; each is verified numerically in the toys and in `tools/test_b14p1_kelvin_pa_toys.py`.

Not used: no real DMM datasheet was opened, so gain error ±100 ppm, thermal EMF ±2 µV, noise 0.5 µV and R_IN 10 GΩ are labelled toy choices; the copper tempco 0.00393 1/K is a toy constant. No Marlin ISR or Klipper source code was read; the planner is a trapezoid stand-in. No login / 403 pages were needed for this PR.

Cached under `/workspace/b14p1-sources/` on the worktree host (not committed): `wiki-kelvin.html/.txt`, `marlin-la.html/.txt`, `marlin-m900.html/.txt`, `klipper-pa.html/.txt`, `klipper-kin.html/.txt`.

## Toy design

- `kelvin_four_wire_sense_toy.py` (1.3): DC steady state, no time step (so no integration-step criterion applies; the tests check the script has none). Arms A two-wire, B Kelvin (sense pair with `r_sense` in series with `R_IN`), C two-wire after a shorted-tip null (new contacts at the part, leads warmed 0–5 K). **Common random numbers** per (regime, seed, part): part value, four lead resistances, contacts at the part and at the shorted tips, lead warming, gain error, thermal EMF, two noise draws — shared by all arms. 5 seeds × 20 parts. Key numbers: shunt_small_dut A−B abs 763.9274±61.6410 (clear, 5/5), C−B abs 40.2171±8.2949 (clear, 5/5), C−B bias 3.0990±11.7689 near-tie; large_dut A−B abs −5.365e-05±1.445e-04 near-tie (2 of 5 opposite sign), A−B bias 0.0008±6.426e-05 clear (5/5, about 8 ppm); zero_lead A−B **tie: identical on every seed** on both metrics, and C−B abs −0.0325±0.0135 (clear, 5/5): **Kelvin loses** to the null there because the null cancels the shared thermal EMF and the toy's Kelvin arm has no offset compensation (disclosed in the lesson).
- `pressure_advance_corner_toy.py` (3.2): melt `ds/dt = feed − q(s)`, `q = q_ref (s/s_ref)^(1/n)`, `q(s ≤ 0) = 0`; advance feed `k_e v DT + K k_e Δv`. Arms K = 0 / tower-tuned K (local slope `n K_true` at 100 mm/s × (1 + reading error, sd 15 %), rounded to 0.005 s) / 3 × tuned K. **Common random numbers** per (regime, seed): `K_true` 0.04–0.08 s, `n` 0.75–1.0, reading error, filament-diameter sequence. Explicit Euler `DT = 0.1 ms`; largest recorded λ 25.84 1/s → limit 77.41 ms, asserted on every run. Key numbers: sharp_corner A−B bulge 165.9007±18.7792 (clear, 5/5), A−B starve 19.2602±12.3244 (clear, 1 of 5 opposite sign: seed 4 tower read 0.090 s against a 0.0781 s slope), A−B rms 23.9144±1.8771 (clear, 5/5), C−B starve 89.2661±10.3383 (clear, 5/5), C−B bulge 1.0286±19.6914 near-tie; slow_corner A−B bulge 49.8740±8.5664 (clear, 5/5), C−B starve 49.7598±13.7362 (clear, 5/5); steady_straight every A−B and C−B line **tie: identical on every seed** (structural: `K × Δv = 0`). No extruder torque / jerk limit is modelled.

No line in either expected file triggers the numerically-zero rule; the rule (|m| and sd < 1e-9, checked after the exact-tie test and before the sd test, no sign count) is implemented, unit-tested on hand-made data and defined in the en/zh prose.

Independent tests: `tools/test_b14p1_kelvin_pa_toys.py` (also executed by the batch-14 PR1 block in `tools/check_diagrams.mjs`).

## §9 lock check

- H1: small-DUT consistent Kelvin win ✔; large-DUT near-tie ✔ (absolute error; the signed bias is a clear 8 ppm gap, disclosed); zero-lead tie ✔. Not in the lock but measured and reported: in zero_lead the nulled two-wire beats Kelvin.
- H2: corner consistent tuned win ✔; constant-speed near-tie / zero: measured an exact **tie** (identical on every seed), which is the "zero" end of the lock; over-tuned consistent lose ✔ (starve and RMS; on bulge C−B is a near-tie, disclosed). slow_corner is an extra regime: tuned K still wins clearly there.
- No mismatch requiring a lock change.

## Lock changes

Totals only: site 30270→30600 and M1 1650→1800, M3 2130→2310 in the existing curriculum / README locks; the b5p1 bench-multimeter host-minutes lock 240→390 (host total, same as other per-host minute locks moved by earlier batches). The b13p1 month-1 / month-3 plan-header locks that matched `Current / 当前：**M1 1650 min**, Batch-13 PR1` / `**M3 2130 min**` now match the `## Batch-13 PR1` headings (same entries, still required), as #154 / #155 did. No lock relaxed.

## Models / reproducibility

opencode free models were tried first with a toy brief (`/workspace/b14p1-opencode/`): `deepseek-v4.1-flash-free`, `glm-5.3-flash-free`, `mimo-v2.6-flash-free`, `longcat-2.5-free` (90 s each) all timed out (exit 124) with no file output; `minimax-m2.5-free` is not listed by `opencode models` and returned an UnknownError (exit 1). Toys, tests and lesson text implemented locally in `/workspace/hl-b14p1`.

## Local validation

`tools/test_b14p1_kelvin_pa_toys.py`, month-1 / month-3 `check.sh`, `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build with postbuild. No workflow edits. Minutes **71 / 30600**.
