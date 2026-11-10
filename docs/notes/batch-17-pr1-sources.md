# Batch-17 PR1 sources / 来源记录

Base `2df760493759f8946e561fc817b4f28412fa1ace` (`2df7604`, main after #168; site **33600**). This PR: M3 cad-parametric 300→450 (+150), M4 ros2-graph 390→570 (+180); site **33600→33930**; M3 2670→2820, M4 2670→2850; still 71 lessons.

## Opened sources

All fetched with curl on 2026-11-10 (Asia/Shanghai), HTTP **200**, then read as text.

| Resource id | URL | Version | What is used |
|---|---|---|---|
| `wiki-interference-fit` (new) | https://en.wikipedia.org/wiki/Interference_fit | rev 1382725373 (oldid in the fetched HTML) | definition (press / friction fit, held by friction after the parts are pushed together); tightness of fit = allowance, from tables; 10 mm stainless shaft 3–10 µm; rule of thumb 0.1–0.25 % of the diameter (0.15 % average), falling with diameter; assembly by force (press, chamfers) or thermal expansion / contraction (shrink fitting) |
| `ros2-qos` (existing card, summary extended) | https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Quality-of-Service-Settings.html | Jazzy docs page | Deadline and Lifespan definitions (quoted), Liveliness / lease duration, "default" durations usually infinite, deadline and lease-duration compatibility tables (requested may not be shorter than offered; default offer vs set request: no), QoS events (offered / requested deadline missed) |

Statements are marked 以原文为准 on the site. The pressure / hoop-stress / friction formulas of the press-fit toy are **not** from the Wikipedia page (it gives none); the page says so and calls them a textbook-style stand-in. No press, oven, torque test or ROS 2 run (本页未运行).

## Toy design

- `examples/month-3/cad-parametric/interference_press_fit_toy.py`: steel shaft 20 mm in a steel hub 40 mm, 15 mm engaged, μ 0.15, yield value 250 MPa, α 12e-6 1/K, each diameter uniform within ±0.005 mm. p = E δ / (2d) (1 − (d/D)²), hoop = p (D² + d²)/(D² − d²), F = μ p π d L, T = F d / 2; yield caps the kept pressure. Arms A_clear (−0.020 mm + set screw N(40, 8) N m) / B_fit (+0.025 mm, shrink fit with the regime's oven ΔT) / C_heavy (+0.070 mm, same oven). Press force from the interference left while hot, δ − α ΔT d. 20 parts × 200 load cycles per seed; Common random numbers (tolerance positions, set-screw torques, loads) shared by all arms; seeds 0–4. No integration step (closed form; tested).
- `examples/month-4/ros2-graph/qos_deadline_lifespan_toy.py`: discrete-event stand-in in integer microseconds (no integration step; tested). Period 10 ms ± 1 ms, delay 1–3 ms, controller ticks every 10 ms with a per-seed phase, stale bound 25 ms at use. Arms A_rel (default deadline / lifespan) / B_dl (deadline 20 ms, lifespan 10 ms) / C_tight (deadline 5 ms offered and requested, lifespan 10 ms). Miss count per gap g between accepted receptions = ⌈g / deadline⌉ − 1; lifespan drop iff t_recv − t_stamp > lifespan. Common random numbers (publications, stalls, delays, losses, phase); seeds 0–4. Prints the deadline compatibility table cases.
- Labels as in batch-15/16 (tie → numerically zero below 1e-9 → near-tie |m| ≤ sd → consistent, small under 20 % of the smaller arm mean else clear, with sign count).

## Results (k/N = seeds with the reported sign)

Interference fit (paired):
- loaded_vibration: B−A slip −25.4300±4.5789 points clear 5/5; B−A press **tie** (oven opens the bore past the largest shaft); B−A stress +0.6212±0.0112 clear 5/5; C−B press +17.9435±0.2383 kN clear 5/5; C−B stress +1.1250 clear 5/5; C−B slip tie.
- no_load (tie regime): B−A slip **tie** and press **tie** (identical on every seed); B−A stress +0.6208±0.0202 clear 5/5.
- press_no_oven (lose regime): **B−A press +13.2461±0.3928 kN clear 5/5 (B loses)**; B−A slip −32.3100±2.3000 clear 5/5; C−B press +23.8565 kN, C−B stress +1.1250 clear 5/5; every C part yields in every regime.

QoS (paired):
- late_sensor: B−A stale −6.6633±1.6806 points clear 5/5; B−A hold +6.9535±1.8594 clear 5/5; B−A age −3.6816±0.9901 ms clear 5/5.
- on_time (tie regime): B−A stale, hold and age **tie** (identical on every seed).
- lossy_reliable (tie/lose regime): **B−A hold +2.7814±0.3652 clear 5/5 (B loses)**; B−A stale −1.0705±0.1824 clear 5/5; B−A age −0.4466±0.0695 small but consistent 5/5; about 299 lifespan drops per seed.
- C_tight: C−B hold +44.2821 to +52.9765 points clear 5/5 in every regime; about 3000 requested-deadline misses per 20 s.

## Post-hoc choices

- Interference fit: none. Regimes, allowances, tolerance band, oven temperatures and yield value were written before the first run; every regime is printed.
- QoS: no parameter changed. After the first run one docstring sentence about common random numbers was added (output byte-identical, checked with cmp). Alternatives not taken and printed on the page: raising the stale bound to 30 ms or more (would make the declared lossy_reliable stale tie true); dropping lossy_reliable.
- The independent test file had one wrong hand count on the first run (2 misses in a 50 ms gap, not 4); the test was fixed, the toy was not changed.

## Mismatch with §9

- §9 names the base as `25fb8f23` / 33600; this PR is based on `2df7604` (main after #168), also 33600. Totals as in §9: 33930, M3 2820, M4 2850; catalogue 71.
- H1: matches (load → consistent B slip win 5/5; no load → A/B tie on slip and press force, here exact; heavy press C → consistent loss on stress and press force). The tie is exact ("tie: identical on every seed"), not a near-tie.
- H2: late stream → consistent B freshness win 5/5 (matches); on-time → exact tie (matches "near-tie / numerically zero" in the stronger form); C → consistent miss by construction (matches). The toy's own pre-declared expectation for lossy_reliable ("B ties A on stale uses") did **not** hold: B−A stale is a clear B win (−1.0705±0.1824, 5/5); the declared loss on hold % held. Printed as is.
- The proposal's source table names the ids `wiki-interference` and `ros2-qos-jazzy`. The new card is `wiki-interference-fit` (clearer next to the existing CAD interference-check text); the repo already had `ros2-qos` with the same Jazzy URL, so that card was extended instead of adding a duplicate.

## Lock changes

- New `b17p1` block in `tools/check_diagrams.mjs` (exact source/stdout in sections, label rules, regime lines, markers, en/zh symmetry, Summary sentences, resources, plan headers, sources note, README, declared tie/lose regimes kept, shrink-fit and deadline/lifespan correctness lines in the toy source).
- Tips moved: site total 33600→33930 (two places); month table M3 2670→2820, M4 2670→2850; README `33 600`→`33 930` (en + zh); host-minute tips cad-parametric 300→450 (b11 GD&T case) and ros2-graph 390→570 (b8 composition case). The b15p2 month-4 and b16p1 month-3 plan checks no longer require their old "Current" line (moved to Batch-17 PR1 and locked in the new block); they still require their own sections.
- No lock relaxed; `.github/workflows` untouched.

## Models / reproducibility

- opencode free models were tried first with one prompt asking for both toys; see the PR description for the per-model result. The toys were written locally.
- Reproduce: `python3 examples/month-3/cad-parametric/interference_press_fit_toy.py`, `python3 examples/month-4/ros2-graph/qos_deadline_lifespan_toy.py`, `python3 tools/test_b17p1_pressfit_qos_toys.py`, `bash examples/month-3/check.sh`, `bash examples/month-4/check.sh`.

## Local validation

See the PR description (check_diagrams, check_widgets, check_wokwi, check_quotes, month check.sh, unit tests, lint, typegen, tsc, build + postbuild, CI=1 build).
