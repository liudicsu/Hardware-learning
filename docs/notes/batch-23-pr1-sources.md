# Batch-23 PR1 sources — optocoupler isolation, Ziegler–Nichols

Base: `38a8c8d453368df23057812729b96cba251672c3` (batch-22 polish #192 merged; site **40140**, M2 **3570**, M3 **3510**).
This PR: site **40140→40500** (40500=40140+180+180), M2 **3570→3750**, M3 **3510→3690**, catalogue still **71**. Hosts: `arduino-io` 660→840, `pid-control` 720→900. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

Both returned HTTP **200** (2026-11-13 UTC+8); the HTML body of the pinned revision was read.

| id | URL | revision | What was used |
|---|---|---|---|
| wiki-opto | https://en.wikipedia.org/w/index.php?title=Opto-isolator&oldid=1381742785 | 1381742785 | Transfers electrical signals between two isolated circuits by using light; prevents high voltages from affecting the receiving system; commercial parts withstand up to 10 kV input-to-output and voltage transients with speeds up to 25 kV/μs; the main function is to block such high voltages and transients; breaks ground loops; unidirectional (exceptions noted) and cannot transmit power, only modulating energy already on the output side; CTR table: photodiode 0.1–0.2 %, phototransistor 2–120 %, Darlington 100–600 %; generous allowances for parameter fluctuations, datasheets list worst-case values; Bob Pease: 4N28 CTR in one production lot from 15 % to more than 100 % against a 10 % datasheet minimum. |
| wiki-zn | https://en.wikipedia.org/w/index.php?title=Ziegler%E2%80%93Nichols_method&oldid=1340563087 | 1340563087 | Heuristic by John G. Ziegler and Nathaniel B. Nichols; I and D set to zero, P raised to the ultimate gain Ku with stable, consistent oscillations of period Tu; table rows used: P 0.5 Ku; classic PID 0.6 Ku / 0.5 Tu / 0.125 Tu; no overshoot 0.20 Ku / 0.50 Tu / 0.33̄ Tu; some overshoot 0.33̄ Ku / 0.50 Tu / 0.33̄ Tu (printed alternative only); classic aims at quarter-wave decay and best disturbance rejection, is aggressive with overshoot; the no-overshoot row is for applications that must avoid overshoot. |

Not cited: no vendor datasheet (4N25/4N28/4N35 or any other), no IEC 60747-5-2 / UL 1577 text, no Microstar Laboratories page and not the 1942 Trans. ASME paper were opened. Every CTR, threshold, pull-up, surge share, LED current, plant constant and noise level in the toys is a **declared toy parameter**, printed or stated as declared, never a datasheet value.

## Toys

- `examples/month-2/arduino-io/optocoupler_ctr_isolation_toy.py` → `examples/month-2/expected/optocoupler_ctr_isolation_toy.txt`
- `examples/month-3/pid-control/ziegler_nichols_ultimate_gain_toy.py` → `examples/month-3/expected/ziegler_nichols_ultimate_gain_toy.txt`

Common random numbers, five seeds, stdlib CPU only, half-up rounding on the shortest decimal repr, byte-identical output on rerun (also under Python 3.12). Optocoupler: no integration step (static operating point per bit). Ziegler–Nichols: exact zero-order-hold discretisation, stable for any step because 0 < A < 1 (printed). Every m±sd in the new lesson prose, the new Summary sentences, the month-2 / month-3 plans and this note is printed in `expected/`.

## Regime results

### H1 optocoupler (`optocoupler_ctr_isolation_toy.txt`)

- Declared toy parameters: VCC 3.3 V, RL 4700 ohm, VCE_SAT 0.2 V, V_IL / V_IH 0.3 / 0.7 VCC, ABS_MAX 3.6 V, divider 3.0/24, K_CM 0.1, K_ISO 1e-4, CTR_NOM 0.5 with exp(0.3 g) spread, pin noise 0.05 V, 200 bits, surge probability 0.2, 20–200 V, AGE 0.25, I_F 10 mA (B) / 1 mA (C).
- Hand calc (printed): 0.6596 mA, 1.3191 mA, 0.9500 V against 0.9900 V, 20.0000 V against 3.6000 V, aged C 0.1250 mA → 2.7125 V.
- quiet_legal: B−A logic_err tie (identical on every seed); C−B logic_err 0.1930±0.2643, near-tie, 3 of 5 equal.
- surge: B−A overvolt -0.1790±0.0444 and logic_err -0.1050±0.0158, clear, 5/5; C−A overvolt -0.1790±0.0444; C−B logic_err 0.3510±0.1996, C−A logic_err 0.2460±0.2007 (1 of 5 opposite).
- low_ctr: C−B and C−A logic_err 0.5260±0.0475, clear, 5/5, **kept**.
- Alternatives (same seeds, written before the first run, not adopted): RL 10 kΩ → C−B 0.5260±0.0475; K_CM 0.02 → B−A overvolt -0.0980±0.0323; C at 2 mA → C−B 0.5260±0.0475.

### H2 Ziegler–Nichols (`ziegler_nichols_ultimate_gain_toy.txt`)

- Declared toy parameters: K 1, TAU 1 s, DT 0.005 s, L 0.1 / 0.5 s, noise sd 0.002 / 0 / 0.02, load step 0.2–0.4 at 10 s, derivative filter Td/10, no actuator limit, 20 s runs; identification by P-only bisection over [0.1, 100], 40 steps, 60 s runs.
- Hand calc (printed): Ku 16.3506 / Tu 0.3850 s (L 0.1 s), Ku 3.8069 / Tu 1.7106 s (L 0.5 s); identified 15.9619 / 0.3943 s and 3.7913 / 1.7179 s.
- lag: B−A iae 0.3162±0.0080, clear, 5/5; B overshoot 43.6254±0.0581 %; C−A iae 1.7036±0.0972, clear, **kept**.
- delay_quiet: B−A overshoot -30.9996±0.0000, clear, 5/5; B−A iae 0.8479±0.0533.
- delay_noisy: B−A overshoot -31.0408±0.2830, clear; B−A iae 0.7306±0.0300, clear, 5/5 (A lower).
- Alternatives (same seeds, written before the first run, not adopted): some-overshoot row X−A overshoot -21.8736±0.4418, iae 0.4278±0.0131; Tf = Td/5 X−A iae 0.0023±0.0033, near-tie; analytic Ku/Tu on lag X−A iae 1.549e-4±1.278e-4.

## Post-hoc choices

None for either toy; every parameter, regime and printed alternative was written before the first run and run on the same seeds.

## Code changes after the first run

None. Both toys ran once as written; each first output is byte-identical to its `expected/` file.

## Mismatch with §9

- Ziegler–Nichols lag: the declared A/B near-tie on iae did not hold (B−A 0.3162±0.0080, clear, A better). Kept on the page as declared.
- Ziegler–Nichols delay_noisy: the overshoot half held; the "classic ZN has poorer IAE than B" half did not (B−A iae 0.7306±0.0300, clear, A better). Kept on the page as declared.
- The "no overshoot" row overshoots 43.6254±0.0581 % on lag (short Ti relative to the lag); reported, not pre-declared.
- Optocoupler: every declared regime held. Not pre-declared and reported: C's quiet_legal near-tie with two bad seeds; in surge C misreads more bits than the direct pin (C−A 0.2460±0.2007) while still keeping the surge off the pin.
- Plan wording: the proposal's "210-min plan" is read as the +180 delta per host (30+25+50+40+35).

## PointVLA byline wording

The depth-pointcloud page and the `pointvla-paper` card now say the asterisk on Li and Zhu is **usually read as equal contribution** (the paper defines only †, corresponding author), and that the asterisks are visible only in the PDF: the arXiv HTML conversion dropped them, while its author order is the same as the PDF's. The batch-22 polish note's wording ("PDF / HTML byline … ∗") is historical and left unchanged.

## Lock changes

Tipped site-total, host-minute and Current-header locks only; tightened the PointVLA byline lock to the new wording. New lock block added (toys, expected, CRN, label order, difference directions, the cited 0.125 table value with 以原文为准, opened-source cards with oldid and rev, plans, README, sources, no process labels in the new toys and outputs) plus `tools/test_b23p1_opto_zn_toys.py`.

- README `/40 140/` and `约 40 140 分钟` → `/40 500/` and `约 40 500 分钟`.
- Curriculum sum checks `40140` → `40500`; month-total lists M2 3570→3750, M3 3510→3690.
- Host-minute locks for `arduino-io` (660→840) and `pid-control` (720→900) in earlier cases.
- month-2 / month-3 plan Current header locks → Batch-23 PR1 (**M2 3750**, **M3 3690**); historical section markers kept.
- Labels of moved tip locks now name the live total.
- PointVLA card and page lock: same strings checked with the new wording, plus "usually read as equal contribution", the PDF-only asterisk sentence, and no "co-first-author" / 共同第一作者.

No lock relaxed.

Real coupler / isolation tester / vendor CTR curve, real plant / hardware autotune: 本页未运行. Wikipedia figures 以原文为准.
