# Batch-20 PR1 sources — leadscrew efficiency and self-locking, lidar realism vs ideal rays

Base: `73b59b39de82a388c0a89514269680b5c04048f9` (batch-19 polish #180 merged; site **36900**, M3 **3000**, M4 **3030**).
This PR: site **36900→37230** (37230=36900+150+180), M3 **3000→3150**, M4 **3030→3210**, catalogue still **71**. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All returned HTTP **200** (this run, 2026-11-12 UTC+8).

| id | URL | rev | What was used |
|---|---|---|---|
| wiki-leadscrew | https://en.wikipedia.org/wiki/Leadscrew | 1372857424 | Mechanics: unwrap one square-thread revolution; T_raise = (F·d_m/2)·tan(φ+λ), T_lower = (F·d_m/2)·tan(φ−λ); self-locking when μ > tan λ, equivalently φ > λ; "this self-locking property is not absolute": under vibration or shock the effective coefficient of friction may drop to dynamic levels and the screw can back-drive unexpectedly; safety-critical uses add a holding brake. Efficiency: η = tan λ / tan(φ+λ). Non-zero thread angle: μ·sec α (α = half thread angle). Thread-friction table: dry steel-on-bronze row starts at 0.15 (以原文为准). |
| sdf-lidar-spec | https://raw.githubusercontent.com/gazebosim/sdformat/sdf14/sdf/1.11/lidar.sdf and .../noise.sdf | `sdf14` branch, read 2026-11-12 | lidar.sdf: range min / max "for each lidar ray", range resolution; noise type "gaussian" drawn independently for each beam (mean, stddev); visibility_mask vs visibility_flags. noise.sdf: generic bias_mean, dynamic bias, gaussian_quantized precision (以文档为准). |
| gz-sensors-lidar-src | https://raw.githubusercontent.com/gazebosim/gz-sensors/gz-sensors8/src/Lidar.cc | `gz-sensors8` branch, read 2026-11-12 | "The lidar sensor only supports Gaussian noise"; ApplyNoise adds noise per ray then calls Clamp; Clamp: NaN → RangeMax, finite → std::clamp(range, RangeMin, RangeMax), infinities unchanged (以文档为准). |

Also read, not cited as a resource card: the Gazebo Harmonic sensors tutorial source (raw.githubusercontent.com/gazebosim/docs/master/harmonic/sensors.md, HTTP **200**): gpu_lidar example with range min / max / resolution and the LaserScan message fields. The rendered SDFormat spec page `sdformat.org/spec?ver=1.11&elem=sensor` returned HTTP **500** this round and was **not** cited (as the proposal also notes); the spec text was read from the repository source instead. In-repo `src/content/m4/gazebo-sim/en.mdx` "Sensors: simulation versus the datasheet" and `examples/month-4/gazebo-sim/m4_gazebo/urdf/sensors.gazebo.xacro` (min 0.20 m, max 8.0 m, stddev 0.01 m) were re-read on the base.

No lidar datasheet and no leadscrew vendor catalogue was opened, so no vendor accuracy band, blind-zone distance, drop-out rate or dynamic friction factor is quoted. Every such number in the toys is a **declared toy parameter**, printed (以原文为准 / 以文档为准 only for the documented statements above).

## Toys

- `examples/month-3/transmissions/leadscrew_self_locking_toy.py` → `examples/month-3/expected/leadscrew_self_locking_toy.txt`
- `examples/month-4/gazebo-sim/gazebo_lidar_realism_toy.py` → `examples/month-4/expected/gazebo_lidar_realism_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only, byte-identical output on rerun. No integration step (closed-form statics / one static scan). Every number in the new lesson prose, the new Summary sentences, the curriculum objectives, the month-3 / month-4 plans and this note that carries an m±sd form is printed by the toys into `expected/`; hand calculations are labelled as such and printed.

## Regime results

### H1 leadscrew (`leadscrew_self_locking_toy.txt`; first accepted run = first run)

- Declared toy parameters: F=500.0 N ±10 %, d_m=10.0 mm, MU_NOM=0.15 ±0.03, VIB_FACTOR=0.30; leads 10.0 mm (A) and 2.0 mm (B, C); borderline lead 4.7124 mm (tan λ = MU_NOM).
- Hand calc (printed): λ=3.6426°, φ=8.5308°, T_raise 0.5393 N·m, T_lower 0.2138 N·m, η 0.2951; steep λ=17.6568°, T_lower -0.4016 N·m, η 0.6472; vibrated μ 0.0450 < tan λ 0.0637 → T_lower -0.0465 N·m. Boundary strict: μ = tan λ gives T_lower 0.0000 and holds=0; μ+1e-6 holds=1.
- nominal: paired B−A T_lower 0.5823±0.0264, clear, 5/5; paired B−A holds 1.0000±0.0000; paired B−A η -0.3505±0.0034 (trade); paired C−B T_lower -0.2535±0.0395, clear, 5/5; paired C−B holds -1.0000±0.0000 — vibration unlock **kept**.
- borderline: B holds on 3/5; B T_lower 0.0050±0.0478; paired B−A holds 0.6000±0.5477 — label **clear gap** (|m| just above sd, 2 of 5 equal), so the pre-declared possible near-tie did **not** occur; printed as it came out, not retuned. Paired C−B holds -0.6000±0.5477.
- Alternatives (same seeds, written before the first run, not adopted): VIB_FACTOR=0.60 keeps the lock 5/5 (paired C−B holds tie; T_lower -0.1444±0.0225); MU_NOM=0.10 (paired C−B T_lower -0.1721±0.0363); trapezoidal α=15.0° on borderline (B holds 4/5; paired B−A holds 0.8000±0.4472).

### H2 lidar realism (`gazebo_lidar_realism_toy.txt`)

- MIN=0.20 m, MAX=8.0 m, SIGMA=0.01 m from the lesson xacro; C_BIAS=0.015 m, P_DROP_C=0.50, R_BIAS=0.020 m, R_SIGMA=0.012 m, P_DROP_R=0.60, TOL=0.10 m declared toy parameters. R (real-unit stand-in) uses its own random stream; arms share one stream (CRN).
- Hand calc (printed): 1.80 − 0.12 = 1.68 m; edge beam 1.68 / cos 30° = 1.9399 m. Boundary: 0.1200 m → A 0.1200, B 0.2000 (gz-sensors clamp), C none; 0.2000 m → all 0.2000 (blind zone strict).
- clear_wall: paired B−A mean_err 0.0011±0.0013, **near-tie** as declared; paired C−A mean_err 0.0161±0.0013, clear, 5/5 (C worse vs geometry, as declared, kept); R mean_err 0.0195±0.0017.
- glossy: paired A−C ret_err 0.2689±0.0563, clear, 5/5, kept; paired A−C mismatch 3.6000±2.7928, small but consistent, 5/5 (not declared a C win; reported as it came out).
- min_range: paired A−C mismatch 19.0000±0.0000, clear, 5/5; paired A−C near_err 1.5834±0.0089; paired B−C near_err 1.5034±0.0089 — kept.
- visual_only: paired A−C mismatch 27.0000±0.0000, clear, 5/5; paired A−C near_err 0.0720±0.0193; paired B−C near_err 0.0797±0.0194 — kept.
- Alternatives (same seeds, written before the first run, not adopted): TOL=0.05 m (min_range / visual_only unchanged; clear_wall paired A−C mismatch 0.4000±0.5477, near-tie); P_DROP_C=0.90 (glossy paired A−C ret_err 0.2492±0.1052, clear); C_BIAS=0.000 (clear_wall paired C−A mean_err 0.0011±0.0013, near-tie).

## Post-hoc choices

None for parameters or regimes in either toy: loads, μ, VIB_FACTOR, leads, scene positions, realism parameters, TOL and every printed alternative were written before the first run.

Code changes after the first run (H2 only), no number changed: (1) the TOL-alternative header said "on min_range and visual_only" while the loop also printed clear_wall — text corrected, and an unused helper (`kw_tol`) removed; (2) a `scene:` line per regime was added so every scene position quoted in the lesson is printed by the toy. All other lines of the first run are byte-identical (first-run output kept outside the repo and diffed). H1 had no code change after its first run.

## Mismatch with §9

- H1: §9 says the borderline cell *may* near-tie. Under the page's label rule the hold flag came out as a clear gap (0.6000±0.5477, 3/5 differ, 2/5 equal). Reported plainly; not retuned. The static hold, the η trade and the vibration unlock match §9.
- H2: matches §9 (clear-wall near-tie A vs B; glossy / min-range / visual-only consistent ideal loss, kept). Extra: on the geometric metric C is worse than A on the clear wall (pre-declared, kept), and on glossy the beam-level gap is only small-but-consistent.

No other mismatch: CRN, ≥5 seeds, no integration step stated, no unprinted side-run numbers, en/zh synced, difference directions in prose / Summary / curriculum / plans / this note match the printed `paired` lines (locked).

Real leadscrew / jack / printer axis, real lidar and Gazebo: 本页未运行.

## Folded #180 review nits

- m2/esp32 Sleep Modes intro (en/zh): "not a datasheet value" narrowed to "not a board measurement and not ESP32-S3 values"; it now says I_LIGHT / I_DEEP equal classic-ESP32 datasheet typicals and explains that the printed phrase `not datasheet values` means only that narrower claim. Toy and `expected/` unchanged; no lock changed for it.
- m2/sensors-fusion (en/zh): the lesson body now says the UM10204 body was read from Pololu's hosted mirror (pololu.com/file/0J435/UM10204.pdf) because nxp.com refused the curl fetch; the card still links NXP. Toy and `expected/` unchanged.

## opencode

Tried free models in order DeepSeek (`opencode/deepseek-v4.1-flash-free`), GLM (`opencode/glm-5.3-flash-free`), MiMo (`opencode/mimo-v2.6-flash-free`), LongCat (`opencode/longcat-2.5-free`), MiniMax (`opencode/minimax-m3.1-flash-free`), 90 s each. All five timed out (exit 124) with no file written. Implementation is local.

## Lock changes

Tipped site-total, host-minute and Current-header locks only; no lock relaxed. New batch-20 PR1 block added (toys, expected, CRN, label order, strict boundaries, difference directions, sources, plans, README) plus `tools/test_b20p1_leadscrew_lidar_toys.py`.

- README `/36 900/` and `约 36 900 分钟` → `/37 230/` and `约 37 230 分钟` (including earlier "unchanged" tips).
- Curriculum sum checks `36900` → `37230`; `current curriculum` month totals M3 3000→3150, M4 3030→3210.
- Host-minute locks for `transmissions` (510→660) and `gazebo-sim` (450→630) in earlier cases.
- month-3 / month-4 plan Current header locks → Batch-20 PR1 (**M3 3150**, **M4 3210**); historical section markers kept.
- `tools/test_m3_optional_cad.py` call list gains `leadscrew_self_locking_toy.txt` (the month-3 harness gained one check).

No lock relaxed.
