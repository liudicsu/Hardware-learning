# Batch-21 PR2 sources — parallel-axis URDF inertia, Madgwick vs complementary

Base: `33a4a703eced7372f71e0decc6b733655ee1cbb4` (batch-21 PR1 #185 merged; site **38340**, M4 **3210**, M2 **3390**).
This PR: site **38340→38700** (38700=38340+180+180), M4 **3210→3390**, M2 **3390→3570**, catalogue still **71**. Hosts: `urdf-tf` 420→600, `first-robots` 240→420. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All fetched this run (2026-11-12 UTC+8).

| id | URL | rev / version | What was used |
|---|---|---|---|
| wiki-parallel-axis | https://en.wikipedia.org/wiki/Parallel_axis_theorem | rev 1337841361 (HTTP 200) | Huygens–Steiner theorem; I = I_cm + m d² for a parallel axis a perpendicular distance d away; derivation (cross term vanishes because the centre of mass is at the origin); tensor form J = I + m[(R·R)E₃ − R⊗R]; diagonal elements count only displacement perpendicular to the axis. 以原文为准. |
| madgwick-2010-report | https://web.archive.org/web/20190715000000/https://x-io.co.uk/res/doc/madgwick_internal_report.pdf | Wayback copy, HTTP 200, `application/pdf`, 1 536 828 bytes, `%PDF-1.4`; read with pdftotext | Title *An efficient orientation filter for inertial and inertial/magnetic sensor arrays*; author **Sebastian O.H. Madgwick** (single author, as printed on the title page); dated April 30, 2010. Sections read: abstract, 3.1–3.3 (quaternion rate from the gyro, accelerometer objective and Jacobian, gradient-descent step, fusion eqs 42–44 with β as the gyro-error divergence rate), 3.6 (β = √(3/4) ω̃β), 4.4 (β = 0.033 IMU, 0.041 MARG; initial 2.5 for 10 s), 5.2–5.3 (Table 1; β swept 0–0.5), 6 (accelerations due to motion corrupt the gravity direction; choose β low enough). Abstract figures < 0.6° static and < 0.8° dynamic RMS, 109 / 277 operations. 以报告为准. |

Not cited:
- `https://wiki.ros.org/urdf/XML/link`: bot wall in the proposal round; not opened as a body this run and not cited. The URDF convention used (the `<inertial><origin>` is the centre of mass and the matrix is about it) is the one the lesson's own `inertial_macros.xacro` already uses.
- `https://x-io.co.uk/downloads/madgwick_internal_report.pdf` (live x-io): captcha / HTTP 202 in the proposal round; **not** cited as a body that was read. Only the Wayback PDF is cited.
- No MPU-6050 datasheet and no Gazebo documentation were opened, so every noise level, bias range, tolerance and torque in the toys is a **declared toy parameter**, printed.

## Toys

- `examples/month-4/urdf-tf/urdf_parallel_axis_inertia_toy.py` → `examples/month-4/expected/urdf_parallel_axis_inertia_toy.txt`
- `examples/month-2/first-robots/madgwick_vs_complementary_balancer_toy.py` → `examples/month-2/expected/madgwick_vs_complementary_balancer_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only, half-up rounding on the shortest decimal repr, byte-identical output on rerun. The parallel-axis toy has no integration step (closed form). The Madgwick toy integrates only the filters, at dt = 1/200 s, forward Euler on the quaternion with normalisation (the report's eq 42); the truth is closed form. Every number in the new lesson prose, the new Summary sentences, the curriculum objectives, the month-2 / month-4 plans and this note that carries an m±sd form is printed by the toys into `expected/`; hand calculations are labelled and printed; report figures carry 以报告为准.

## Regime results

### H3 parallel axis (`urdf_parallel_axis_inertia_toy.txt`; first accepted run = first run)

- Declared toy parameters: chassis 2.0 kg, 0.30 × 0.24 × 0.08 m (the lesson's worked example 1), mass ±3 %, sizes ±2 %, TAU 0.05 N·m.
- Hand calc (printed): Izz_cm 0.0246 kg·m², radius of gyration 0.1109 m; d = 0.15 m → m d² 0.0450, I 0.0696, typo/true 0.3534; d = 0.01 m → 2.000e-4 (0.8130 % of Izz_cm); r = (0.10, 0.08, 0) → J_xy -0.0160.
- zero: every pair **tie** (identical on every seed) — matches §9 / the declaration.
- small: paired B−A J_zz -2.009e-4±2.789e-6, **small but consistent**, 5/5; B−A alpha_z 0.0164±0.0007, small, 5/5. The declared "may near-tie" did **not** occur (the tolerance draws move A and B together). Printed, not retuned.
- large: paired B−A J_zz -0.0448±4.431e-4, clear, 5/5; B−A alpha_z 1.3520±0.0164, clear, 5/5 (typo loses — held); C−A J_zz and C−A alpha_z **tie** (held); C−A tau_g -2.9280±0.0290, clear, 5/5 (declared C loss on gravity torque held, kept).
- along_axis: B−A J_zz **tie** (held); B−A J_xx -0.0032±6.824e-5, clear, 5/5.
- diagonal: B−A J_xy 0.0160±1.924e-4, clear, 5/5; C−A J_xy **tie**; C−A tau_g -1.9610±0.0236, clear, 5/5.
- Alternatives (same seeds, written before the first run, not adopted): d = 0.10 m (B−A J_zz -0.0199±1.969e-4, clear), d = 0.20 m (-0.0796±0.0008, clear), d = 0.005 m (-5.023e-5±6.972e-7, small but consistent).

### H4 Madgwick (`madgwick_vs_complementary_balancer_toy.txt`; first accepted run = first run)

- Declared toy parameters: 200 Hz, τ 0.5 s (the lesson's), β_low 0.033 (the report's IMU value), β_high 0.5 (top of the report's sweep), initial pitch ±3°, gyro bias ±1 °/s, gyro noise 0.1 °/s, accelerometer noise 0.04 g per axis, A_LIN 2.0 m/s², lean lag 0.3 s, warm-up 2 s, end window 5 s.
- Hand calc (printed): lean atan(2.0/9.81) 11.5232°, accelerometer angle 0.0000° in the steady lean; a = 0.9901; bias error b·τ 0.5000° at 1 °/s; gyro-only drift 60.0000° in 60 s; β 0.033 ↔ ω̃β 2.1833 °/s.
- static: paired A−B end_err 35.5376±23.4941, clear, 5/5 (gyro-only loses — held). Declared "B vs C may near-tie" did **not** hold: C−B rmse 0.2661±0.2218 and C−B end_err 0.2938±0.2460, clear, 5/5 (Madgwick at β 0.033 loses). D−B rmse 0.1542±0.1725, near-tie (1 of 5 opposite).
- slow_tilt: A−B rmse 8.4331±7.2937, clear, 5/5 (held); C−B rmse 0.2049±0.2241, **near-tie** (2 of 5 opposite) — held; D−B rmse 0.1923±0.1807, consistent with 1 of 5 opposite.
- accelerate: D−B rmse 0.7386±0.0326, **small but consistent**, 5/5 — declared large-β loss held, kept; D−B end_err 0.2065±0.0374, small. C−B rmse -2.9664±0.3624, clear, 5/5 (not pre-declared; C wins). A−B rmse 1.0716±2.8608, near-tie; A−B end_err 7.6907±4.8046, clear, 5/5.
- Alternatives (same seeds, written before the first run, not adopted): accelerate τ = 0.25 s (D−B rmse 0.2814±0.0276, small), τ = 1.0 s (1.7716±0.0575, clear), β_high = 0.1 (0.0526±0.0354, small, 1 of 5 opposite), β_high = 0.2 (0.4900±0.0352, small); static β_low = 0.1 (C−B rmse -0.0458±0.0919, near-tie).

## Post-hoc choices

None for parameters or regimes in either toy: offsets, tolerances, TAU, τ, both β, noise levels, bias range, acceleration profile and every printed alternative were written before the first run.

Code changes after the first run: **none** in either toy. Both first-run outputs are byte-identical to the committed `expected/` files.

## Mismatch with §9

- H3: §9 says small d "may near-tie — keep". Under the page's label rule it is a **small but consistent** gap (5/5), because paired differences of m d² share the tolerance draw and have almost no spread. Reported plainly. d = 0 tie, large-d typo loss and (A)(C) tie on the shared-axis metric match §9. Extra arms of the same toy: C loses on gravity torque (it moves the COM to the joint), and the along-axis / diagonal regimes show the tensor form's perpendicular-distance and product-of-inertia terms.
- H4: §9 says static "may near-tie (B)(C)". In `static` Madgwick at the report's β = 0.033 **loses** with a clear gap; in `slow_tilt` the near-tie holds. The large-β loss under linear acceleration matches §9 (small but consistent, 5/5, kept). Gyro-only drift loses at rest as §9 says. C beating B under acceleration was not pre-declared.

No other mismatch: CRN, ≥5 seeds, integration step stated, no unprinted side-run numbers, en/zh synced, difference directions in prose / Summary / curriculum / plans / this note match the printed `paired` lines (locked).

Gazebo / a real inertia measurement, a real MPU-6050 / optical reference / the report's Kalman comparison: 本页未运行.

## opencode

Tried free models in order DeepSeek (`opencode/deepseek-v4.1-flash-free`), GLM (`opencode/glm-5.3-flash-free`), MiMo (`opencode/mimo-v2.6-flash-free`), LongCat (`opencode/longcat-2.5-free`), MiniMax (`opencode/minimax-m3.1-flash-free`), 300 s each, on the parallel-axis toy. @@OPENCODE@@ Both toys, the pages and the locks were written locally.

## Lock changes

@@LOCKS@@
