# Batch-21 PR1 sources — Peukert rate-capacity, FDM build-orientation anisotropy

Base: `b918527ab417d2fec73c736169bae90d1a773ae5` (batch-20 polish #184 merged; site **37980**, M1 **2550**, M3 **3150**).
This PR: site **37980→38340** (38340=37980+180+180), M1 **2550→2730**, M3 **3150→3330**, catalogue still **71**. Hosts: `components` 900→1080, `fdm-printing` 360→540. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All returned HTTP **200** (this run, 2026-11-12 UTC+8).

| id | URL | rev / version | What was used |
|---|---|---|---|
| wiki-peukert | https://en.wikipedia.org/wiki/Peukert%27s_law | rev 1345423657 | Lead–acid approximate law (Wilhelm Peukert, 1897); C_p = I^k t; t = H (C / (I H))^k; k = 1 → delivered capacity independent of current; lead–acid k typically 1.1–1.3, with separate AGM / gel / flooded ranges; worked example 100 Ah at the 20-hour rate, k = 1.2, 10 A → about 8.7 h and 87 Ah; It = C (C / (IH))^(k−1); Limitations: temperature not included, k grows with age, self-discharge at low rates, practical batteries give less capacity than a fixed exponent at very high currents; high-current internal-resistance note; constant-current / constant-temperature caveat (以原文为准). |
| rajkumar-fdm-orientation | https://arxiv.org/abs/2202.05692 and https://arxiv.org/pdf/2202.05692 | v1 abs (submitted 2022-01-18 per `citation_date`); PDF via pdftotext | Title verified: *Effect of infill pattern and build orientation on mechanical properties of FDM printed parts: An experimental modal analysis approach*. Authors: the abs page lists **one** author, **Santosh Rajkumar** (`citation_author` "Rajkumar, Santosh"); the PDF byline reads **Santosh Mohan Rajkumar** (Graduate Student, Miami University). There is no "et al.". Body: PLA beams 100 × 15 × 5 mm, Dremel 3D45, 100 % infill, 0.2 mm layers, six infills × flatwise / edgewise / upright, five specimens each, three-point bending per ASTM D7264 (σ = 3PL/(2wt²), ε = 6dt/L², E = ΔL³/(4wt³), d = PL³/(48EI)); cubic + edgewise highest maximum flexural stress 107.95 MPa, triangles + upright lowest 62.32 MPa; flatwise highest median maximum flexural stress, upright "much lower"; flatwise higher modulus, upright lower; triangles + flatwise highest modulus 3.36 GPa, zigzag + edgewise lowest 2.185 GPa; edgewise higher maximum flexural strain; modal analysis: natural frequency tracks modulus (以论文为准). Table 2 is an image in the PDF and was not read as numbers; no span L value was found in the text, so the toy span is a declared toy parameter. |

Not cited: the 2006 Doerffel & Sharkh review that Wikipedia cites (paywalled, body not read). No battery datasheet, no filament datasheet and no Instron report was opened, so every capacity exponent spread, high-current loss, self-discharge current, strength and modulus in the toys is a **declared toy parameter**, printed. Paper MPa / GPa values appear only in the citation prose and the resource card, never as toy outputs.

## Toys

- `examples/month-1/components/peukert_rate_capacity_toy.py` → `examples/month-1/expected/peukert_rate_capacity_toy.txt`
- `examples/month-3/fdm-printing/fdm_build_orientation_anisotropy_toy.py` → `examples/month-3/expected/fdm_build_orientation_anisotropy_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only, half-up rounding on the shortest decimal repr, byte-identical output on rerun. No integration step (closed form). Every number in the new lesson prose, the new Summary sentences, the curriculum objectives, the month-1 / month-3 plans and this note that carries an m±sd form is printed by the toys into `expected/`; hand calculations are labelled as such and printed. The only unprinted decimals in prose are the cited paper / Wikipedia values (107.95 MPa, 62.32 MPa, 3.36 GPa, 2.185 GPa; about 8.7 h / 87 Ah), each marked 以论文为准 / 以原文为准.

## Regime results

### H1 Peukert (`peukert_rate_capacity_toy.txt`)

- Declared toy parameters: generator k_true U[1.15, 1.25] (lead–acid) and U[1.00, 1.03] (k≈1 pack, not a LiPo datasheet), I_KNEE=50 A (strict I > I_KNEE), GAMMA=0.25, D_DERATE=0.80, I_SD=0.05 A (`low` cell only). Rating 100 Ah / 20 h and K_DECL=1.2 are Wikipedia's worked-example values.
- Hand calc (printed): 100 Ah, 20 h, k=1.2, 10 A → t=8.7055 h, 87.0551 Ah (Wikipedia: about 8.7 h, 87 Ah); rated 5.0000 A → t=H=20.0000 h for any k. Boundary: D/B=1.0000 at I=I_KNEE, 0.8000 just above.
- rated: paired A−B t and A−B abs_err **tie** (identical on every seed) — matches §9.
- high: paired A−B abs_err 1.0280±0.2552, clear, 5/5 (nameplate loses; A over-predicts 5/5, A err 1.1636±0.1692); B err -0.0471±0.1692 (over 3/5, under 2/5). C−A t tie in every regime.
- very_high: B over-predicts 5/5 (B err 0.0714±0.0417); paired D−B abs_err -0.0277±0.0757, **near-tie** (2 of 5 opposite sign) — the pre-declared "B can lose to D" did **not** occur as a consistent loss; printed, not retuned.
- low: B predicts 158.4893 Ah from 100 Ah; over-predicts 5/5 (B err 39.3178±19.7830); A err -77.6608±19.7830; paired A−B abs_err 38.3430±39.5659, near-tie (not pre-declared).
- misapplied: paired A−B abs_err -1.0787±0.1315, clear, 5/5 — lead–acid k on a k≈1 pack loses, **kept**; B err -1.1447±0.0658, A err 0.0660±0.0658.
- Alternatives (same seeds, written before the first run, not adopted): K_DECL=1.1 / 1.3 on high (A−B abs_err 0.6472±0.0000 / 0.6260±0.3383, clear); K_DECL=1.3 on misapplied (A−B abs_err -1.5692±0.1315); D_DERATE=0.90 on very_high (D−B abs_err -0.0393±0.0251, consistent, 1 of 5 opposite); GAMMA=0.10 (D−B abs_err 0.0550±0.0743, near-tie; B−A err -0.4507±0.0000); I_SD=0 on low (B err 5.8889±23.1640; A−B abs_err 91.0895±15.4044).

### H2 FDM orientation (`fdm_build_orientation_anisotropy_toy.txt`; first accepted run = first run)

- Declared toy parameters: span 80 mm, 15 × 5 mm section (paper geometry), load ±5 %, strength quality ±8 %, modulus quality ±5 % (shared); default strengths 90/85/55 MPa and moduli 3.2/3.0/2.7 GPa (flat/edge/up); zigzag-like 80/78/50 MPa and 3.0/2.2/2.5 GPa. Ordered after the paper's qualitative statements; not paper values.
- Hand calc (printed): 220 N → σ=70.4000 MPa, util 0.7822 (flat) / 1.2800 (up); I=156.2500 mm⁴; 100 N at 3.2 GPa → 2.1333 mm. Boundary strict: snap at σ = S, survive when S is 1e-6 MPa higher.
- light: paired B−A snap **tie** (identical on every seed), as declared; paired B−A util 0.2330±0.0133, clear, 5/5; paired D−A defl 0.1436±0.0054, small, 5/5.
- mid: paired B−A snap 1.0000±0.0000, clear, 5/5; paired B−C snap 1.0000±0.0000 (isotropic guess misses the snap); paired B−A util 0.4878±0.0278; paired D−A defl 0.3140±0.0125, small.
- modulus: paired D−A defl 0.8295±0.0478, clear, 5/5 — side-on rule loses on stiffness, **kept**.
- Paired A−B sigma is a tie in every regime (shared geometry and load).
- Alternatives (same seeds, written before the first run, not adopted): SPAN=60 mm (B snaps 1/5; B−A snap 0.2000±0.4472, near-tie); S_UP=65 MPa (5/5; B−A snap 1.0000±0.0000); load ×0.80 (2/5; B−A snap 0.4000±0.5477, near-tie).

## Post-hoc choices

None for parameters or regimes in either toy: currents, generator ranges, K_DECL, I_KNEE, GAMMA, D_DERATE, I_SD, span, loads, strengths, moduli and every printed alternative were written before the first run.

Code changes after the first run (H1 only), disclosed on the components page in en and zh: (1) `mean_sd` returns sd 0 when all five values are identical — the first run printed floating residue such as `3.7893+-4.965e-16` (B and D `t` in `high` / `misapplied`), `0.4394+-6.206e-17` (D `t` in `very_high`) and `paired A-B t: 0.4507+-6.206e-17` (label unchanged: clear); (2) one "over-predicts (err > 0) on k/5 seeds, under-predicts on k/5" line per arm A, B, D was added so the pre-declared over-prediction claims are printed. Every other first-run line is byte-identical (first-run output kept outside the repo and diffed); no label changed. H2 had no code change after its first run.

## Mismatch with §9

- H1: §9 says very-high-current fixed-k "can lose" to the practical cap. Under the page's label rule D−B abs_err came out a **near-tie** (-0.0277±0.0757), because the declared 0.80 cap under-predicts on 4/5 seeds. Reported plainly; not retuned. The rated tie, the high-current nameplate loss and the mis-applied-k loss match §9; B does over-predict on 5/5 at very high current. §9 lists arm (C) as "k=1 or a high-current cap or a mis-applied k"; this toy runs all three as separate pieces (arm C = k=1, arm D = cap, regime `misapplied`) rather than choosing one.
- H2: matches §9 (light-load tie on survival kept; mid-load consistent upright snap; modulus cell where edgewise does not win kept). Extra: at default parameters the edgewise stiffness gap is only small-but-consistent.
- The task brief called the FDM source "Rajkumar et al."; the arXiv abs page lists a single author, so the lesson names Santosh Rajkumar (abs) / Santosh Mohan Rajkumar (PDF byline) and writes no "et al.".

No other mismatch: CRN, ≥5 seeds, no integration step stated, no unprinted side-run numbers, en/zh synced, difference directions in prose / Summary / curriculum / plans / this note match the printed `paired` lines (locked).

Real pack / BMS / calorimeter, real printer / Instron / modal hammer: 本页未运行.

## opencode

Tried free models in order DeepSeek (`opencode/deepseek-v4.1-flash-free`), GLM (`opencode/glm-5.3-flash-free`), MiMo (`opencode/mimo-v2.6-flash-free`), LongCat (`opencode/longcat-2.5-free`), MiniMax (`opencode/minimax-m3.1-flash-free`), 90 s each, on the Peukert toy. DeepSeek, LongCat and MiniMax timed out (exit 124) with no file; MiMo timed out after writing a partial file; GLM returned a short skeleton with its own label rule (near-tie if |mean| ≤ 1 % of 20 h) and no regimes, generator, sign counts or numerically-zero rule. Neither file was used. Implementation is local.

## Lock changes

Tipped site-total, host-minute and Current-header locks only; no lock relaxed. New batch-21 PR1 block added (toys, expected, CRN, label order, strict boundaries, difference directions, sources, plans, README) plus `tools/test_b21p1_peukert_fdm_toys.py`.

- README `/37 980/` and `约 37 980 分钟` → `/38 340/` and `约 38 340 分钟` (including earlier "unchanged" tips).
- Curriculum sum checks `37980` → `38340`; month-total lists M1 2550→2730, M3 3150→3330.
- Host-minute locks for `components` (900→1080) and `fdm-printing` (360→540) in earlier cases.
- month-1 / month-3 plan Current header locks → Batch-21 PR1 (**M1 2730**, **M3 3330**); historical section markers kept.
- Labels of moved tip locks now name the live total ("tip after batch-21 PR1"), and the b18pol label-reference check follows them.
- b20p1 month-3 month-total list `[3,3150]` → `[3,3330]`.
- The month-3 plan's batch-21 line words the isotropic comparison without a `B−C` difference, because the b20p1 difference-direction scan of the whole month-3 plan pairs `1.0000±0.0000` with B−A only; the b20p1 lock itself is unchanged.
- Inside the new block, the curriculum m±sd check scans only the batch-21 objective and task lines (Peukert, `σ = 3PL`, `b21p1-`), and the prose-decimal check skips the mantissa of a number in e-notation (the disclosed first-run residue `4.965e-16`, which is not in `expected/`).
- `tools/test_m3_optional_cad.py` call list gains `fdm_build_orientation_anisotropy_toy.txt` (the month-3 harness gained one check).

No lock relaxed.
