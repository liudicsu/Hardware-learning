# Batch-16 PR1 sources / 来源记录

Base `c60dee9` (main after #164; site **32490**). This PR: M1 components 600→750 (+150), M3 pid-control 540→720 (+180); site **32490→32820**; M1 1950→2100, M3 2490→2670; still 71 lessons. Proposal: `batch-16-proposal.md` PR1 (H1 at §2, H2) and §9 locks.

## Opened sources

All fetched with curl on 2026-11-10 (Asia/Shanghai), HTTP 200, article body present (`mw-parser-output`), then read as text.

| Resource id | URL | Revision | Lines read (text extract) | What is used |
|---|---|---|---|---|
| `wiki-diode-bridge` | https://en.wikipedia.org/wiki/Diode_bridge | 1373727385 | 13, 20, 22, 27 | four-diode full-wave from two-wire AC; only 2 diodes forward-biased at a time; output at twice the input frequency, normally followed by a capacitor / filter; Pollak 1895 / Graetz 1897 |
| `wiki-rectifier` | https://en.wikipedia.org/wiki/Rectifier | 1367200865 | 151, 159, 164, 168 | half-wave Vpeak/π, full-wave 2Vpeak/π; ≈0.7 V per silicon drop (0.3 V Schottky), half-wave one drop, bridge two; ripple at f (half) / 2f (full), quoted peak-to-peak; r = (Vp − Vmin)/Vp; capacitor vs ripple current trade-off, peak current limited by winding resistance |
| `wiki-ripple` | https://en.wikipedia.org/wiki/Ripple_(electrical) | 1381025481 | 67–68, 76 | linear discharge Q = C·Vpp = I·t, t = 1/(2f) full-wave, **Vpp = I/(2fC)**; γ = 1/(4√3 fCR) |
| `wiki-pid-controller` | https://en.wikipedia.org/wiki/PID_controller (redirect to "Proportional–integral–derivative controller"; the card uses this short URL because the encoded title trips the percent-spacing check) | 1383929606 | 269–271 | derivative of PV is "a simple case of setpoint weighting"; weights (usually 0–1) on the setpoint in P and D; I must use the true error; the two parameters "do not affect the response to load disturbances and measurement noise" |

Numbers from these pages are marked 以原文为准 on the site. No hardware, mains, transformer or servo was run (本页未运行).

## Toy design

- `examples/month-1/components/bridge_rectifier_ripple_toy.py`: ideal 50 Hz sine (12 V rms) behind RS = 0.5 Ω; ideal diode + series VF; arms A_half (one drop) / B_bridge (two drops) / C_noC (bridge, no capacitor); forward Euler DT = 5 µs on the capacitor node, stable for DT ≤ 2/(1/(RS C) + 1/(R C)) (printed per regime, asserted DT under 5 % of it; tests at 0.98× / 1.02× and DT vs DT/2). Law check: simulated ripple / (I/(k f C)) within 25 % when ripple is small; ripple over 10 % of vdc labelled "not DC". Common random numbers: line amplitude, C tolerance, load and VF drawn once per seed (5 seeds) for every arm and regime. Regimes small_C_heavy, medium, large_C_light, tiny_C_heavy.
- `examples/month-3/pid-control/pid_setpoint_weighting_2dof_toy.py`: rigid joint 1/(s(TM s + 1)), TM = 0.05 s; ISA PID u = Kc((b r − y) + (1/TI)∫(r − y) + TD d(c r − y)/dt), trapezoid I, Tustin-filtered D, TS = 1 ms; Kc for |L(j20)| = 1; arms A_1dof (b = c = 1) / B_2dof (b = 0.5, c = 0) / C_aggr (b = 1, c = 0); RK4 H = TS/4 with |R(Hλ)| ≤ 1 asserted (h_max 139.26 ms; tests at 0.98× / 1.02× and H vs H/2); margins printed (PM 60.6°, GM 42.37 dB; TI × 4: PM 67.9°, GM 42.77 dB). Common random numbers: start target, setpoint steps, load steps and noise drawn once per seed (5 seeds). Regimes setpoint_large, load_step, mixed_noise, tiny_b (b = 0.1, TI × 4; pre-declared possible loss). Pass rule: B's load ISE within 5 % of A's.
- Labels as in batch-15 (tie → numerically zero below 1e-9 → near-tie |m| ≤ sd → consistent, small under 20 % of the smaller arm mean else clear, with sign count).

## Results (k/N = seeds with the reported sign)

Bridge (paired B−A unless noted):
- small_C_heavy: ripple −5.2981±0.2119 V clear 5/5 (B wins); vdc +2.8946±0.2236 clear 5/5; ipk −0.3169±0.0960 small 5/5; both not DC.
- medium: ripple −2.3476±0.2445 clear 5/5; ipk −0.8996±0.0907 clear 5/5; vdc +0.5862±0.1365 small 5/5; law within 25 % (A 0.83–0.85, B 0.76–0.78); both not DC (A 40.5 %, B 18.4 %).
- large_C_light: vdc −0.4146±0.0308 small but consistent 5/5 (**B loses**, second diode drop); ripple −0.1619±0.0207 clear 5/5; ipk −0.5103±0.0339 clear 5/5; both DC; law within 25 %.
- tiny_C_heavy: ripple −4.1851±0.4101 clear 5/5; ipk −0.0446±0.0022 small 5/5; all not DC.
- C_noC: not DC everywhere (ripple ≈165 % of vdc); C−B ripple clear loss in all four regimes 5/5; C−B ipk negative, clear, in all four (B loses on diode stress to C).

2DOF:
- setpoint_large: B−A overshoot −19.2551±0.0001 % clear 5/5 (B wins); rise +132 ms and ise_sp +118.9698±21.0614 clear 5/5 (B loses); C−A overshoot +6.0945±0.0001 clear 5/5.
- load_step: B−A ise_load −2.359e-17±3.854e-16 numerically zero; C−A tie (identical on every seed); band 0.0000 %.
- mixed_noise: B−A overshoot −19.2653±0.0104 clear 5/5; ise_load 0.0034±0.0044 near-tie (1 of 5 opposite); **load band 14.2940 % fails the 5 % pass rule**.
- tiny_b: B−A rise 926.6000±0.1491 ms clear 5/5, ise_sp 1065.3485±264.8766 clear 5/5 (B loses, as pre-declared).

## Post-hoc choices

- No parameter, regime, tolerance or weight of either toy was changed after the first full run. All regimes that were run are printed, including the ones unfavourable to the bridge (large_C_light vdc, ipk vs C_noC) and to 2DOF (tiny_b, mixed_noise load band).
- After the first run, `simulate` in the 2DOF toy gained a `sub` argument (default = SUB) so a test can halve the RK4 step; the printed output is byte-identical.
- One independent bridge test was rewritten after its first run: it used a 47 mF capacitor, which does not reach steady state in 20 cycles; it now checks that the law ratio rises towards 1 from `medium` to `large_C_light` and stays within 25 %.
- Diagnostic only (not in the toy, not on the page): rerunning mixed_noise without noise gives the same B-above-A load ISE pattern (A 0.0211/0.0248/0.0414/0.0131/0.0188, B 0.0195/0.0260/0.0428/0.0212/0.0266), supporting the explanation that B's slower setpoint tail overlaps the load windows. The page states the explanation as an interpretation and leaves the check as exercise 4.
- Interpretation of the proposal's arm C for H2 ("aggressive b = 1 with the same gains"): C uses b = 1, c = 0 (full proportional kick, derivative on the measurement), so it differs from A. Alternative not run: a re-tuned higher-gain 1DOF arm.

## Mismatch with §9

- H1 lock "large-C **near-tie**": measured mean Vdc in large_C_light is a **small but consistent** gap (B−A −0.4146±0.0308 V, 5/5) because the bridge's second diode drop is deterministic and the seed spread is small. Not tuned away; reported as is. "Small-C **consistent** bridge ripple win" matches (clear, 5/5). Ripple-vs-I/(fC) check present (25 %). ≠ Wheatstone / TVS matches.
- H2 lock "setpoint step **consistent** less overshoot" matches (clear, 5/5). "Load step **near-tie**/zero vs 1DOF" matches in load_step (numerically zero); in mixed_noise the label is near-tie but the stated 5 % load band fails (14.2940 %), disclosed on the page. ≠ notch / lead / Smith matches.

## Lock changes

- New `b16p1` block in `tools/check_diagrams.mjs` (exact source/stdout in sections, label rules, regime lines, markers, en/zh symmetry, plan headers, sources note, README) and `tools/test_b16p1_bridge_2dof_toys.py` (labels, CRN, Euler bound at 0.98×/1.02×, no-C quadrature, law approached from below, RK4 bound at 0.98×/1.02×, weights out of the loop, preset steady state, step halving, outputs).
- Extended: `tools/test_m3_optional_cad.py` FULL list gains `pid_setpoint_weighting_2dof_toy.txt` (the month-3 harness grew by one check).
- Tips moved: site total 32490→32820; month table M1 1950→2100, M3 2490→2670; README `32 490`→`32 820` (en + zh); host-minute tips components 600→750 (b6p1, b10p2, b11p1 cases) and pid-control 540→720 (b13p1, b15p1 cases); b15p1 plan-header locks repointed from the "Current" line to their `## Batch-15 PR1` headings (all other strings kept).
- No lock relaxed; `.github/workflows` untouched.

## Models / reproducibility

- opencode free models were tried first with one prompt asking for both toys (150 s timeout each): deepseek-v4.1-flash-free, glm-5.3-flash-free, mimo-v2.6-flash-free, longcat-2.5-free timed out (exit 124, no files); minimax-m2.5-free returned "Unexpected server error" (exit 1). Both toys, the tests and the page text were written locally.
- Reproduce: `python3 examples/month-1/components/bridge_rectifier_ripple_toy.py`, `python3 examples/month-3/pid-control/pid_setpoint_weighting_2dof_toy.py`, `python3 tools/test_b16p1_bridge_2dof_toys.py`, `bash examples/month-1/check.sh`, `bash examples/month-3/check.sh`, `node tools/check_diagrams.mjs`. Common random numbers, seeds 0–4, stdlib only.

## Local validation

See the PR description for the command list and results (check_diagrams, check_widgets, check_wokwi, check_quotes, month check.sh, unit tests, lint, typegen, tsc, build + postbuild, CI=1 build).
