# Batch-22 PR2 sources — LQG separation, NTC inrush limiting

Base: `833aac3e5ab0a197f7f1dcb155ad3c4f7c956b15` (batch-22 PR1 #189 merged; site **39420**, M5 **3390**, M11 **3630**).
This PR: site **39420→39780** (39780=39420+180+180), M5 **3390→3570**, M11 **3630→3810**, catalogue still **71**. Hosts: `state-space-lqr` 600→780, `power-battery-emc` 690→870. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All returned HTTP **200** (2026-11-13 UTC+8).

| id | URL | rev / version | What was used |
|---|---|---|---|
| wiki-lqg | https://en.wikipedia.org/wiki/Linear–quadratic–Gaussian_control | rev 1337444202 | LQG concerns linear systems driven by additive white Gaussian noise; the optimal output-feedback controller is unique and is a Kalman filter (linear–quadratic estimator) together with an LQR; separation principle (estimator and state feedback designed independently); discrete-time predictive estimator whose gain comes from the process and measurement noise covariances; "LQG optimality does not automatically ensure good robustness" (以原文为准). |
| wiki-inrush | https://en.wikipedia.org/wiki/Inrush_current | rev 1326751079 | A discharged capacitor initially looks like a short circuit, limited only by the source internal resistance and the ESR; a series resistor drops voltage and dissipates power in normal operation; an NTC thermistor self-heats so its resistance falls; just after switch-off a hot NTC cannot limit the inrush current unless it cools for more than 1 minute; not short-circuit-proof (以原文为准). |
| wiki-inrush-limiter | https://en.wikipedia.org/wiki/Inrush_current_limiter | rev 1312732367 | High cold resistance; self-heating lowers the resistance; it is inherently impossible for 100 % of the supply voltage to appear on the protected circuit; a fixed resistor's resistance never falls; the limiter can be switched out by a relay or MOSFET (以原文为准). |

Not cited: no NTC thermistor, capacitor, fuse or PSU datasheet, no control textbook and no MATLAB documentation was opened, so every resistance, beta, thermal resistance and capacity, capacitance, fuse budget, noise level, weight and pole set in the toys is a **declared toy parameter**, printed. The hot-restart statement is cited only from the Inrush current page (the limiter page does not state it); the toy's hot_restart regime (no cooling time) is a declared model assumption, not a reproduction of that page. The mass-damper plant and the page observer poles 0.85 / 0.80 are the state-space-lqr lesson's existing observer-toy values.

## Toys

- `examples/month-5/state-space-lqr/lqg_kalman_lqr_separation_toy.py` → `examples/month-5/expected/lqg_kalman_lqr_separation_toy.txt`
- `examples/month-11/power-battery-emc/ntc_inrush_limiter_toy.py` → `examples/month-11/expected/ntc_inrush_limiter_toy.txt`

Common random numbers, five seeds, stdlib CPU only, half-up rounding on the shortest decimal repr, byte-identical output on rerun. Integration: LQG uses the forward-Euler plant at DT 0.02 s with both Riccati maps iterated until the largest change is below 1e-12; the NTC toy uses forward Euler at DT 2e-6 s over a 0.05 s window. Every number in the new lesson prose, the new Summary sentences, the month-5 / month-11 plans and this note that carries an m±sd form is printed by the toys into `expected/`; hand calculations are labelled as such and printed, except the NTC thermal-balance check used to choose R_TH, which is labelled 手算 on the page.

## Regime results

### H3 LQG (`lqg_kalman_lqr_separation_toy.txt`)

- Declared toy parameters: DT 0.02 s, M 1.0 kg, damping 0.40 N·s/m, SIG_W 0.04 (velocity only), Q diag(1.0, 0.1), R 0.01, 500 steps, P0 diag(0.25, 0.01); sensor noise 0.05 / 0.25 / 0.005 m; arms A_oracle (privileged), B_lqg, C_luen_page (0.85, 0.80), D_luen_fast (0.20, 0.20), E_kf_misspec (V×0.01, W×100), all with the same K.
- Hand calc (printed): K = [9.5023, 5.0042]; L matched [0.1576, 0.6712], noisy [0.0700, 0.1263], quiet [0.4303, 5.8664]; Lp page [0.3420, 1.3632], fast [1.5920, 31.3632]; L1 = [0.9901, 0.0000].
- matched: A cost 0.0270±0.0202, B 0.0553±0.0401, C 0.0602±0.0421, D 1.4436±0.2831, E 0.1409±0.0452; paired B−A cost 0.0284±0.0202, clear, 5/5; B−C cost -0.0049±0.0026, small, 5/5; B−D cost -1.3883±0.2447, clear; E−C cost 0.0807±0.0444, clear, 5/5, **kept**.
- noisy_sensor: B 0.0352±0.0106, C 0.1437±0.0110; B−C cost -0.1084±0.0036, clear, 5/5; B−D cost -27.7882±1.4261, clear; E−C cost 0.4013±0.2864, clear.
- quiet_sensor: B−C cost 0.0127±0.0235, near-tie (1 of 5 opposite); B−D cost -0.0716±0.0946, near-tie; B−C est_rms -0.0031±0.0010, small, 5/5; B−C u_rms 0.5113±0.4373, clear; E−C cost 0.0127±0.0147, near-tie (1 of 5 opposite); B−A cost 0.0253±0.0355, near-tie.
- Alternatives (same seeds, written before the first run, not adopted): V×100 / W×0.01 → E−C cost 1.1922±0.2001; page poles 0.90 / 0.85 → B−C cost 0.0058±0.0064; 1000 steps noisy → B−C cost -0.1120±0.0068.

### H4 NTC inrush limiter (`ntc_inrush_limiter_toy.txt`)

- Declared toy parameters: 24 V source, R_SRC 0.05 ohm, 2200 µF, 12 ohm load (6 ohm heavy), R25 5 ohm, BETA 3500 K, R_TH 60 K/W, C_TH 0.5 J/K, 0.05 s window, I²t budget 1.0 A²s; arms A_none, B_ntc, C_fixed, D_bypass.
- Hand calc (printed): 480.0000 A, 4.7525 A, 12.6720 A²s, 0.1255 A²s, 0.6336 J, 1.9917 A.
- cold_start: A peak 488.1174±63.0625 A; A−B peak_a 483.8672±62.9814, clear, 5/5; A−B fuse_ok -1.0000±0.0000; B peak 4.2502±0.2690 A; C−B peak_a 0.3278±0.0755, small, 5/5; B v_drop_ss 0.7479±0.0153 V; C−B p_ss 8.6198±0.2385, clear, **kept**; B−D peak **tie**.
- hot_restart (declared model assumption, no cooling time): B peak 56.1052±0.8280 A; B i2t 1.7419±0.1192 A²s, fails the budget on every seed; B−D fuse_ok -1.0000±0.0000; A−B fuse_ok **tie** (both fail).
- heavy_load: C−B p_ss 21.3877±0.1482, clear; C−B peak_a -0.1153±0.3361, near-tie.
- Alternatives (same seeds, written before the first run, not adopted): R25=10 → C−B p_ss 10.0913±0.0408; R_TH=30 → hot A−B peak_a 510.6694±38.8185; budget 0.25 → A−B fuse_ok -1.0000±0.0000.

## Post-hoc choices

LQG: none; every parameter, regime and printed alternative was written before the first run. NTC: R_TH 60 K/W was chosen from a standalone thermal-balance hand check (手算 on the page) done before the toy was written and run; no parameter or regime was changed after the first run.

Code changes after the first run: none in either toy. Both first-run outputs are byte-identical to the `expected/` files.

## Mismatch with §9

- NTC cold_start: declared "C vs B peak may near-tie"; result C−B peak_a 0.3278±0.0755 is **small but consistent**, not a near-tie. Kept as printed.
- LQG quiet_sensor: declared "E loses to C, keep"; result E−C cost 0.0127±0.0147 is a **near-tie** (1 of 5 opposite), not a consistent loss. Kept as printed.
- Not pre-declared and reported on the page: LQG quiet_sensor B−A cost 0.0253±0.0355 is a near-tie (the oracle bound is not consistent there), and B−C cost has B worse on 4 of 5 seeds within a near-tie.

Real plant / IMU / MATLAB toolbox, real PSU / NTC disc / fuse: 本页未运行.

## Lock changes

Tipped site-total, host-minute and Current-header locks only; no lock relaxed. New lock block added (toys, expected, CRN, label order, difference directions, sources, plans, README, no process labels in the new toys and outputs, now also rejecting the words polish and 来源笔记) plus `tools/test_b22p2_lqg_ntc_toys.py`.

- README `/39 420/` and `约 39 420 分钟` → `/39 780/` and `约 39 780 分钟`.
- Curriculum sum checks `39420` → `39780`; month-total lists M5 3390→3570, M11 3630→3810.
- Host-minute locks for `state-space-lqr` (600→780) and `power-battery-emc` (690→870) in earlier cases.
- month-5 / month-11 plan Current header locks → Batch-22 PR2 (**M5 3570**, **M11 3810**); historical section markers kept.
- Labels of moved tip locks now name the live total.

No lock relaxed.
