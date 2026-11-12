# Batch-19 PR1 sources — true-RMS vs average-responding, Zener shunt / LDO headroom

Base: `13471fe8c009af353b0f30abc99b6068154447aa` (batch-18 closed, including polish #176; site **35820**, M1 **2250**).
This PR: site **35820→36120**, M1 **2250→2550**, catalogue still **71**. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All four returned HTTP **200** (curl, this run, User-Agent identified as curriculum research).

| id | URL | rev | What was used |
|---|---|---|---|
| wiki-multimeter | https://en.wikipedia.org/wiki/Multimeter | 1384382275 | Average-responding unless stated true-RMS; AC accuracy only on pure sinusoids; true-RMS up to a specified crest factor; the meter manual may also state the crest-factor and frequency (bandwidth) limits for which the calibration is valid. No AC vs AC+DC coupling claim is taken from this page. |
| wiki-rms | https://en.wikipedia.org/wiki/Root_mean_square | 1381647998 | RMS is the square root of the mean of the square; for a zero-mean sine, peak-to-peak = 2√2 × RMS ≈ 2.8 × RMS; other waveforms do not share that ratio. |
| wiki-zener | https://en.wikipedia.org/wiki/Zener_diode | 1373728185 | Shunt regulator: reverse-biased in parallel, holds near breakdown; series R must satisfy the strict inequality I_D V_B < P_max. |
| wiki-ldo | https://en.wikipedia.org/wiki/Low-dropout_regulator | 1378921240 | Regulates when Vin is already very close to Vout; pass element can be driven into saturation; P_LOSS = (V_IN − V_OUT) I_OUT + V_IN I_Q. No dropout millivolt is quoted in the body we read, and none is invented. |

Fluke / Keysight pages were not opened (the proposal already flagged a listing redirect / 403). No TI or NXP LDO datasheet was opened. Wikipedia statements 以原文为准.

## Toys

- `examples/month-1/bench-multimeter/true_rms_vs_average_responding_toy.py` → `examples/month-1/expected/true_rms_vs_average_responding_toy.txt`
- `examples/month-1/components/zener_shunt_ldo_headroom_toy.py` → `examples/month-1/expected/zener_shunt_ldo_headroom_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only. No integration step (finite sum / DC solve). Every number in the new lesson prose, the new Summary bullets and this note that carries an m±sd form is printed by the toys into `expected/`. Hand calculations are labelled as such and also printed.

## Regime results (first accepted run = first run)

### H1 true-RMS (`true_rms_vs_average_responding_toy.txt`)

- Hand calc (also printed): 1 V-peak sine RMS = 0.7071067812 V (0.7071 V); pp/RMS = 2.8284271247 (~2.8); form factor = 1.1107207345. ±1 V square average-responding error = 0.1107207345 V (11.0721 %). Crest factors: sine 1.4142135624, square 1.0000000000, triangle 1.7320508076, pwm duty 0.0625 → 4.0000000000.
- sine, paired B−A reading: near-tie -6.112e-06±1.805e-05 (2 of 5 opposite sign). Not a numerical-zero / identical tie.
- square, paired B−A reading: 0.1107±8.278e-07, small but consistent, same sign on all 5 seeds; C−A -0.2902±2.475e-04, clear, 5/5.
- triangle, paired B−A reading: -0.0220±2.386e-05, small but consistent, 5/5; C−A 0.1271±0.0015, clear, 5/5.
- pwm_high_crest, paired B−A reading: -0.1793±0.0024, clear, 5/5; C−A 0.4603±0.0053, clear, 5/5; clipped true-RMS vs A -0.0629±0.0027, clear, 5/5.

### H2 Zener / LDO (`zener_shunt_ldo_headroom_toy.txt`)

- Declared toy parameters, not datasheet mV: HEADROOM = 0.40 V, P_THERMAL = 0.50 W. Headroom rule: in regulation iff Vin − Vset ≥ HEADROOM (equality allowed). Boundary printed: Vin=5.4000000000 V in_reg=1; Vin=5.3990000000 V in_reg=0. below_headroom spare printed: Vin − Vset = 0.1500000000 V (5.15 − 5.0), below HEADROOM 0.40 V. In the r_z = 0 model the Zener is in regulation iff I_Z > 0; that flag is not a datasheet knee current I_Z,min (printed). Thermal test is the strict inequality P < P_THERMAL, matching I_D V_B < P_max.
- Hand calc (also printed): IR=0.0700000000 A, IZ=0.0500000000 A, PZ=0.2500000000 W. Thermal heavy: PZ=0.5909090909 W, thermal_ok=0. Light on the same R: PZ=1.5409090909 W, thermal_ok=0.
- in_regulation, paired A−B vout: near-tie -0.0233±0.0516 (2 of 5 opposite sign). The |err| line in the same regime is a clear gap -0.0120±0.0110 (5/5); both are printed. Uncapped dissipation C−A 702.6763±8.8323, clear, 5/5, kept.
- below_headroom, B in_reg vs 1 and A in_reg vs 1: -1.0000±0.0000, clear, 5/5, kept.
- thermal_small_R, A thermal_ok vs 1: -1.0000±0.0000, clear, 5/5, kept. Light-load companion 1.5368±0.0231 W, thermal_ok vs 1 also -1.0000±0.0000, clear, 5/5, kept.

## Post-hoc choices

None. CF_CAP = 3.0, PWM duty 0.0625, HEADROOM = 0.40 V, P_THERMAL = 0.50 W and the 22 Ω / 200 mA sizing were written before the first run. Alternatives were printed on the same seeds as a pre-planned sensitivity and were not adopted: CF_CAP=2.0 (clipped vs A -0.1249±5.952e-06, clear, 5/5) and CF_CAP=4.0 (-0.0030±0.0027, small but consistent, 2 of 5 equal); HEADROOM=0.20 V (below-headroom in_reg 0.4000±0.5477); P_THERMAL=0.80 W (would have made every thermal_small_R seed pass). The looser thermal cap was not used to delete the loss.

## Mismatch with §9

- H1 sine was pre-declared as a **tie** / **numerically zero** cell. The first accepted run is a **near-tie** (-6.112e-06±1.805e-05, 2 of 5 opposite sign), because the discrete mean of |sin| on 8000 samples is not exactly 2/π. Reported honestly; the sampling grid was not retuned. The continuous-time hand calc still shows exact agreement and is printed.
- H1 square / triangle average-responding losses are **consistent** as required; the 20 % wording rule labels the 0.1107 V (11.0721 %) square over-read and the -0.0220 V triangle gap **small but consistent** rather than **clear**. The official labels are the printed ones.
- H2 matches §9: in-regulation Vout near-tie; below-headroom and thermal-cap (and uncapped shunt) consistent losses, all kept. No invented dropout mV.

No other mismatch: CRN, ≥5 seeds, no integration step stated and tested, no unprinted side-run numbers, en/zh synced, locks only tip totals / Current headers / host minutes (bench-multimeter 390→540, components 750→900, site 35820→36120).

## Review fix on #177

- The sine near-tie is printed as paired B−A -6.112e-06±1.805e-05. The first-run body already used B−A; the Summary, curriculum objectives and the month-1 plan Current line had written A−B with the same signed value. Those labels are now B−A, matching expected/. The in-regulation Vout near-tie stays A−B -0.0233±0.0516. A lock now checks difference-direction labels against the printed `paired` lines.
- The below-headroom spare 0.1500000000 V (5.15 − 5.0) is now printed by the toy into expected/ (it had appeared in en/zh prose without a print or a hand-calc label). A rescan of the two new sections and their new Summary bullets found no other unprinted, unlabelled result number; 40 periods / 10 kHz sampling are labelled as derived from the already-printed F = 50 Hz, FS = 10000 Hz, N = 8000.

Real DMM / regulator bench: 本页未运行.

## opencode

Tried free models in order DeepSeek (`opencode/deepseek-v4.1-flash-free`), GLM (`opencode/glm-5.3-flash-free`), MiMo (`opencode/mimo-v2.6-flash-free`), LongCat (`opencode/longcat-2.5-free`), MiniMax (`opencode/minimax-m3.1-flash-free`, the free MiniMax id available in this environment). None produced toy files (timeout or empty). Implementation is local.

## Lock changes

Tipped site-total and host-minute locks only; no lock relaxed. Tightened on the #177 review: difference-direction labels must match expected/, and the printed 0.1500000000 V spare is locked.

- README `/35 820/` and `约 35 820 分钟` → `/36 120/` and `约 36 120 分钟` (including earlier “unchanged” tips).
- Curriculum sum checks `35820` → `36120`.
- `bench-multimeter` host minutes in earlier cases `390` → `540`.
- `components` host minutes in earlier cases `750` → `900`.
- month-1 plan Current header lock (was Batch-18 PR1, **M1 2250**) → Batch-19 PR1, **M1 2550**; historical `## Batch-18 PR1` and earlier markers kept.
- `current curriculum` month totals: M1 2250→2550 (other months unchanged).

No lock relaxed.
