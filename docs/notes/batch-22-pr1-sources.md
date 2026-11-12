# Batch-22 PR1 sources — crimp vs solder strain relief, SO-101 shared-rail sag

Base: `5c0a2058860b3776983f1a4e19ef0ecf5cf51f0a` (batch-21 polish #188 merged; site **39060**, M1 **2730**, M3 **3330**).
This PR: site **39060→39420** (39420=39060+180+180), M1 **2730→2910**, M3 **3330→3510**, catalogue still **71**. Hosts: `soldering` 270→450, `so101-arm` 390→570. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All returned HTTP **200** (2026-11-13 UTC+8).

| id | URL | rev / version | What was used |
|---|---|---|---|
| wiki-crimp | https://en.wikipedia.org/wiki/Crimp_(joining) | rev 1380146082 | An electrical crimp is a solderless connection: stripped stranded wire is inserted into a correctly sized opening of a connector and a crimper squeezes the opening tightly against the wire; benefits over soldering include a well-executed crimp being gas-tight (oxygen and moisture kept off the metals, so no corrosion), no alloy and so "lack of solder wicking", "potentially superior mechanical characteristics due to strain relief", and the article's "mechanically stronger" claim (以原文为准). |
| wiki-voltage-drop | https://en.wikipedia.org/wiki/Voltage_drop | rev 1384299568 | DC voltage drop V = I R; drops in the internal resistance of the source, across conductors, contacts and connectors; voltage drop exists in both the supply and return wires; conductor resistance depends on length, cross-sectional area, material and temperature; the simplest way to reduce the drop is to increase the conductor diameter (以原文为准). |

Not cited: no crimp-terminal datasheet, no wire datasheet, no IPC/WHMA-A-620 or IPC-A-610 text and no PSU datasheet was opened, so every strand count, strand diameter, bend radius, fatigue constant, contact resistance, growth rate and wiring resistance in the toys is a **declared toy parameter**, printed. The SO-101 per-servo currents (C001 rated 0.5 A, stall 2.0 A at 6 V), the 4 V floor and the 4 A supply nameplate are the so101-arm lesson's existing figures and citations (以该课已引用规格为准); the Feetech documents were not re-fetched and are not newly cited.

## Toys

- `examples/month-1/soldering/crimp_vs_solder_strain_relief_toy.py` → `examples/month-1/expected/crimp_vs_solder_strain_relief_toy.txt`
- `examples/month-3/so101-arm/so101_shared_rail_sag_toy.py` → `examples/month-3/expected/so101_shared_rail_sag_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only, half-up rounding on the shortest decimal repr, byte-identical output on rerun. No integration step (closed form / DC solve). Every number in the new lesson prose, the new Summary sentences, the month-1 / month-3 plans and this note that carries an m±sd form is printed by the toys into `expected/`; hand calculations are labelled as such and printed, except the 手算 one-stall total 4.5 A, which is labelled on the page.

## Regime results

### H1 crimp vs solder (`crimp_vs_solder_strain_relief_toy.txt`)

- Declared toy parameters: 19 strands × 0.16 mm, ε = d/(2ρ), N = 2000·(0.02/ε)^2·z with K_FAT=2.0 and lognormal SIGMA_LIFE=0.3; bend radius A 3.0 / B 6.0 / C 6.0 / D 12.0 mm; R_C0=0.50 milliohm, UNDER_X=3.0, FRET_PER_KCYCLE=0.5, OX_PER_KHOUR=0.5. The arm ordering follows from the declared radii and contact growth.
- Hand calc (printed): ε 0.0267 / 0.0133 / 0.0067; median life 1125.0000 / 4500.0000 / 18000.0000 cycles; 19/3 = 6.3333.
- flex (1500 cycles): A intact 2.8000±1.6432; paired B−A intact 16.2000±1.6432, clear, 5/5; B−A life_half 3211.9624±284.6963, clear, 5/5; C−D contact_mohm 2.1192±0.0670, clear, 5/5, **kept**; C−D gas_tight -1.0000±0.0000; C−D intact **tie** (not pre-declared: C loses on contact only). D life_half 17130.4662±1518.3801.
- light_flex (300 cycles): B−A intact **tie** (declared "may near-tie"); C−D contact_mohm 1.2351±0.0886, clear, 5/5.
- static (2000 h, no flex): B−A intact and contact **tie**; C−D contact_mohm 2.4243±0.1546, clear, 5/5.
- Alternatives (same seeds, written before the first run, not adopted): K_FAT=3.0 → B−A intact 18.6000±0.5477; A ρ=4.0 mm → 3.4000±0.5477; OX_PER_KHOUR=0.1 → C−D contact_mohm 1.2607±0.0804.

### H2 SO-101 shared-rail sag (`so101_shared_rail_sag_toy.txt`)

- Declared toy parameters: ideal 5.0 V source; B_wired R_LEAD 0.10 ohm, R_SEG 0.05 ohm; C_thick 0.03 ohm, 0.025 ohm; resistance jitter ±20 %, current jitter ±10 %; constant-current servo loads; chain order shoulder_pan → … → gripper.
- Hand calc (printed): 3.0000 A, 12.0000 A, 1.2000 V, nominal B all_stall 2.3000 V, nominal B rated 4.3250 V.
- rated: B v_min 4.3346±0.0455 V; paired B−A v_min -0.6654±0.0455, small, 5/5; B−A v_ok **tie**; i_sum 2.9554±0.0504 A.
- one_stall (gripper): B v_min 3.8588±0.0415 V; paired B−A v_ok -1.0000±0.0000, clear, 5/5; C 4.5120±0.0160 V; i_sum 4.3757±0.0804 A, above 4 A on every seed (not pre-declared).
- multi_stall (shoulder_lift, elbow_flex, gripper): B 3.2611±0.0548 V (B−A v_min -1.7389±0.0548, clear, 5/5); C 4.2776±0.0237 V (C−B v_min 1.0165±0.0336, clear, 5/5); i_sum 7.5232±0.3085 A.
- all_stall: i_sum 11.9266±0.1133 A; B 2.3751±0.1700 V; C 3.9067±0.0644 V; C−B v_min 1.5317±0.1076, clear; C−B v_ok **tie** (both below 4 V on every seed).
- Alternatives (same seeds, written before the first run, not adopted): R_SEG=0.03 on multi_stall (B still fails on every seed); R_LEAD=0.20 on rated (B−A v_ok -0.4000±0.5477, near-tie); C R_LEAD=0.05 on multi_stall (C still passes on every seed).

## Post-hoc choices

None for parameters or regimes in either toy: every radius, fatigue and contact constant, wiring resistance, current figure, jitter, schedule, regime and printed alternative was written before the first run.

Code changes after the first run: none in either toy. Both first-run outputs are byte-identical to the `expected/` files.

## Mismatch with §9

None. Every pre-declared regime held in both toys. Not pre-declared and reported on the pages: the crimp C−D intact tie in flex; the sag one_stall total current already above 4 A.

Real crimp tool / IPC-A-610 inspection / pull test, real SO-101 arm / PSU / stall test: 本页未运行.

## Lock changes

Tipped site-total, host-minute and Current-header locks only; no lock relaxed. New lock block added (toys, expected, CRN, label order, difference directions, sources, plans, README, no process labels in the new toys and outputs) plus `tools/test_b22p1_crimp_so101_sag_toys.py`.

- README `/39 060/` and `约 39 060 分钟` → `/39 420/` and `约 39 420 分钟`.
- Curriculum sum checks `39060` → `39420`; month-total lists M1 2730→2910, M3 3330→3510.
- Host-minute locks for `soldering` (270→450) and `so101-arm` (390→570) in earlier cases.
- month-1 / month-3 plan Current header locks → Batch-22 PR1 (**M1 2910**, **M3 3510**); historical section markers kept.
- Labels of moved tip locks now name the live total.

No lock relaxed.
