# Batch-20 PR2 sources — rolling versus global shutter, Tobin-style visual domain randomisation

Base: `bf2716c4ad5d843f4e1c5a8cf4e62b0bd357d81c` (batch-20 PR1 #181 merged; site **37230**, M5 **3210**, M7 **2970**).
This PR: site **37230→37560** (37560=37230+180+150), M5 **3210→3390**, M7 **2970→3120**, catalogue still **71**. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All returned HTTP **200** (this run, 2026-11-12 UTC+8).

| id | URL | rev / version | What was used |
|---|---|---|---|
| wiki-rolling-shutter | https://en.wikipedia.org/wiki/Rolling_shutter (wikitext via `action=raw`, and the rendered page) | 1381766604 | A rolling shutter captures a frame "not by taking a snapshot of the entire scene at a single instant in time but rather by scanning across the scene rapidly, vertically, horizontally or rotationally"; not all parts are recorded at the same instant although playback shows one instant; "predictable distortions of fast-moving objects or rapid flashes of light"; a global shutter captures the entire frame at the same instant. Electronic rolling shutter found on many CMOS cameras, the majority in the consumer market; CCD cameras often use global shutters. Effects: wobble (jello), skew, spatial aliasing (propeller), temporal aliasing / partial exposure. "Final results depend on the readout speed of the sensor"; rectification / compensation is "an active area of research" (以原文为准). |
| tobin-dr (abs) | https://arxiv.org/abs/1703.06907 | v1, 20 Mar 2017 | Title **Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World**; **6 authors** in order: Josh Tobin, Rachel Fong, Alex Ray, Jonas Schneider, Wojciech Zaremba, Pieter Abbeel (checked against `citation_author` meta and the author line). |
| tobin-dr (PDF) | https://arxiv.org/pdf/1703.06907 (pdftotext) | v1 | Abstract: randomise rendering in the simulator so the real world may appear as just another variation; detector accurate to 1.5 cm using only simulated data with non-realistic random textures. §III-A: randomise distractors, object positions and textures, table / floor / skybox / robot textures, camera position / orientation / field of view, number and properties of lights, image noise; textures are a random RGB value, a gradient or a checker between random RGB values; the detector has no access to the object colour; MuJoCo renderer not photo-realistic. §IV-B: within 1.5 cm on average in the real world; overfits sim (0.3 cm to 0.5 cm). §IV-C: sensitive to all factors except random noise; performance degrades significantly with fewer than 1,000 textures. §IV-D: Fetch picked the target in 38 of 40 trials. All 以论文为准, not reproduced. |

In-repo `src/content/m5/camera-calibration` (pinhole, stereo-σ, eight-point, `solvePnP` paragraph) and `src/content/m7/sim-to-real` (opening Tobin / Peng citation, contact-DR toy, *Common mistakes* line "Tobin-style visual DR does not fix a wrong τ") were re-read on the base; neither existing section was changed.

No camera datasheet and no sensor vendor document was opened, so no readout time, row time or frame rate of any real sensor is quoted. H, DT_ROW, SLOW, SIGMA_PX, the speeds and every visual-DR size, colour, gain, U and τ are **declared toy parameter** values, printed.

## Toys

- `examples/month-5/camera-calibration/rolling_vs_global_shutter_toy.py` → `examples/month-5/expected/rolling_vs_global_shutter_toy.txt`
- `examples/month-7/sim-to-real/tobin_visual_domain_randomization_toy.py` → `examples/month-7/expected/tobin_visual_domain_randomization_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only, byte-identical output on rerun. No integration step (closed-form positions). Every number in the new lesson prose, the new Summary sentences, the curriculum objectives, the month-5 / month-7 plans and this note that carries an m±sd form is printed by the toys into `expected/`; hand calculations are labelled as such and printed (except 600 / 200 = 3, labelled 手算 in the lesson).

## Regime results

### H3 rolling shutter (`rolling_vs_global_shutter_toy.txt`; first accepted run = first run)

- Declared toy parameters: H=480 rows, DT_ROW=30.0 µs, SLOW=4, SIGMA_PX=0.3 px, speed jitter ±10 %, speeds 0 / 300.0 / 1500.0 px/s. Row r stamped t0 + r·DT_ROW (printed: r=479 → 14.3700 ms).
- Hand calc (printed): readout 14.3700 ms; skew 4.3110 px and naive bias 2.1555 px at 300.0 px/s; 21.5550 px / 10.7775 px at 1500.0 px/s; slow readout 17.2440 px at 300.0 px/s.
- static: every paired line **tie: identical on every seed** — the pre-declared tie held exactly.
- moderate: paired B−A pos_err 2.1073±0.0837, paired B−A skew 4.2034±0.1754, clear, 5/5; paired C−B pos_err 6.3269±0.2589, paired C−B skew 12.6538±0.5177, clear, 5/5 — slow readout loss **kept**.
- fast: paired B−A pos_err 10.5261±0.5669, paired B−A skew 21.0389±1.1377, paired C−B pos_err 31.5960±1.7118, paired C−B skew 63.1920±3.4236, clear, 5/5.
- Alternatives (same seeds, written before the first run, not adopted): DT_ROW=15.0 µs on moderate (paired B−A pos_err 1.0528±0.0406, paired B−A skew 2.0945±0.0907, clear); RS-aware line-fit intercept estimator on fast (paired B−A and C−B pos_err `-1.137e-14±4.756e-14`, numerically zero).

### H4 visual DR (`tobin_visual_domain_randomization_toy.txt`; first accepted run = first run)

- Declared toy parameters: W=24 px, OBJ_W=4.0 px, N_TRAIN=600, N_TEST=40, K_NN=3, PIX_SIGMA=0.02, PALETTE=200, gain 0.6–1.4, U_MOVE=30.0 px/s, TAU_REAL=0.10 s, TAU_SIM=0.05 s, TOL=1.0 px (strict). Peek check printed False: no held-out or canonical texture in B's palette on any seed.
- Hand calc (printed): wrong-τ aim error 30.0 × (0.10 − 0.05) = 1.5000 px, not below TOL even with a perfect detector; object travel 3.0000 px.
- heldout: paired B−A loc_err -3.4207±0.8743, paired B−A success 0.1950±0.0758, clear, 5/5 — pre-declared DR win held; paired C−B tie on every metric (static).
- canonical: paired B−A loc_err 0.1828±0.0448, clear, 5/5 — B loses on A's own texture (pre-declared possible), **kept**; paired B−A success -0.0050±0.0112, near-tie (4 of 5 equal).
- moving: paired C−B loc_err tie; paired C−B grasp_err 0.3734±0.2150, small but consistent, 5/5; paired C−B success -0.3300±0.1110, clear, 5/5 — wrong τ loss **kept**. Paired B−A loc_err -3.4064±0.8660, clear, 5/5; paired B−A success 0.2100±0.1616, clear, 1 of 5 opposite.
- Alternatives (same seeds, written before the first run, not adopted): PALETTE=10 on heldout — B@alt loc_err 1.5310±0.8132 against 2.2700±0.6663; paired B200−B10 loc_err 0.7390±0.3862, clear, 5/5, i.e. **fewer textures did better here, the opposite direction from the paper's ablation**; printed as it came out, not retuned; paired B−A loc_err@alt -4.1596±0.9999. TOL=2.0 px on moving — paired C−B success@alt -0.0450±0.0818, near-tie (a loose threshold hides the τ error).

## Post-hoc choices

None for parameters, regimes or alternatives in either toy: every value and both alternatives per toy were written before the first run. No code change after the first run in either toy (the first run is the `expected/` file).

## Mismatch with §9

- H3: matches §9 (static tie / zero; motion consistent RS warp; slow readout consistent lose, kept). The static tie came out as an exact tie, not only numerically zero.
- H4: matches §9 on the three regimes (held-out consistent DR win; canonical texture: B loses, one of the two pre-declared outcomes, kept; wrong τ consistent lose, kept). Not in §9 but reported plainly: the palette-size alternative (§H4 correctness criterion asks for one) went the **opposite** way from Tobin's ablation; the lesson says so and gives an untested likely reason (3 rows per texture for k-NN). Tobin's 1.5 cm is quoted only as 以论文为准, never as a toy result.

No other mismatch: CRN, ≥5 seeds, no integration step stated, no unprinted side-run numbers, en/zh synced, difference directions in prose / Summary / curriculum / plans / this note match the printed `paired` lines (locked).

Real camera, rolling-shutter lab, GPU training and robot: 本页未运行.

## opencode

Tried free models in order DeepSeek (`opencode/deepseek-v4.1-flash-free`), GLM (`opencode/glm-5.3-flash-free`), MiMo (`opencode/mimo-v2.6-flash-free`), LongCat (`opencode/longcat-2.5-free`), MiniMax (`opencode/minimax-m3.1-flash-free`), 90 s each, in the background while the toys were drafted locally. All five timed out (exit 124) with no file written. Implementation is local.

## Lock changes

Tipped site-total, host-minute and Current-header locks only; no lock relaxed. New batch-20 PR2 block added (toys, expected, CRN, label order, strict TOL, peek check, difference directions, sources, plans, README) plus `tools/test_b20p2_shutter_visual_dr_toys.py`.

No lock relaxed.
