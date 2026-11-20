# Batch-28 PR2 sources

Unit: H2 SimpleFOC current-mode d/q cross-coupling / lag feedforward (`foc-actuator-lab`, +180 → 660). Site **45720** = 45540+180; M11 **4530**; still 71 lessons. Branch `feat/foc-dq-decoupling` from `fd382df872d123ee4ba78332f91cb8773e46a058`. **After this PR, M11 ties M8 at 4530 as joint-heaviest: 60 min above M9 / M10 = 4470, 150 min above M6 = 4380.** This is a disclosed natural-host choice, not a dump onto M9 / M10 or an avoided host, and is recorded here and in the month-11 plan only, not as a student-facing process lecture. Parent accepted the 2-unit batch; this PR is H2 only. H1 / `ros2-hardware-interface` was not reopened.

## Pins actually opened (re-fetched live at writing)

These are official documentation pages (and one Wikipedia oldid opened as a cross-check), not arXiv records: no Comments header and no journal-ref field were present, and none was invented.

- Official current-mode page *FOC Current Mode | Arduino-FOC*, https://docs.simplefoc.com/foc_current_torque_mode — curl **200**; fetched-HTML sha256 `3c8950f3ffd5b106e26880ade44b4ae8719113fe1696dc66b7592180d92cf9ed`; `Last-Modified: Thu, 19 Nov 2026 10:24:56 GMT` = 2026-11-19 18:24:56 Asia/Shanghai. Identical hash and Last-Modified to the parent re-check; no hash drift. This page was **not** already in the reading map or in `src/lib/resources.ts`; it is added here as a new Resource / reading-map line and is the primary formula body. Current-mode laws when the d-axis target is 0: \(u_q=\mathrm{PI}_q(i_q-\hat{i}_q)\), \(u_d=\mathrm{PI}_d(-\hat{i}_d)\). If \(L_d,L_q\) are provided, \(u_q=\mathrm{PI}_q(i_q-\hat{i}_q)+L_d i_d v_e\), \(u_d=\mathrm{PI}_d(-\hat{i}_d)-L_q i_q v_e\), with \(v_e=n_{pp}\cdot v\). The same page states that in steady state, when the PI loops stabilise, cross-coupling and inductive lag “will be compensated even without the feed-forward terms. However, at highly dynamic conditions and at high speeds, the PI controllers alone may not be able to keep up…” Library performance remarks stay 以文档为准 and are not toy outputs.
- Official voltage / torque-methods page *Torque Control Methods in FOC | Arduino-FOC*, https://docs.simplefoc.com/voltage_torque_control — curl **200**; fetched-HTML sha256 `e8a36f869d17a0ffc545ae89295f97e8e87f69eef5739a08664a0595656043b3`; `Last-Modified: Thu, 19 Nov 2026 10:24:56 GMT` = 2026-11-19 18:24:56 Asia/Shanghai. Identical hash and Last-Modified to the parent re-check; no hash drift. This page was already linked and is kept as the plant / named voltage-mode contrast. Plant model \(u_d=R i_d+L_d di_d/dt-v_e L_q i_q\), \(u_q=R i_q+L_q di_q/dt+v_e L_d i_d+U_{\mathrm{bemf}}\). First back-EMF law \(U_{\mathrm{bemf}}=K_e\cdot v\). Voltage-mode lag term \(u_d=-v_e L_q i_q\) is a named, not-adopted contrast, not a substitute for adding `foc_current_torque_mode`.
- Official theory page *Coordinate Transformations in FOC | Arduino-FOC*, https://docs.simplefoc.com/foc_theory — curl **200**; fetched-HTML sha256 `a083b7f5879f2f810d255921e156525eaa51110dfeff8ae6685aec73e4e63705`; same Last-Modified. Opened as a consistency check only; already the Clarke–Park body; not re-taught.
- Already-linked pages re-fetched as consistency checks, not re-taught: https://docs.simplefoc.com/foc_implementation — curl **200**; sha256 `e53e774a33205741dfa4fc69571ca5a9f7b983fe3244ee9502338d7732905967`; same Last-Modified. https://docs.simplefoc.com/alignment_procedure — curl **200**; sha256 `eea98bdeaaaec442f49a5ef95ecf104c5163f712f81204c6fd58a2bfc4a827c4`; same Last-Modified.
- Wikipedia *Field-oriented control* oldid **1354069032**, https://en.wikipedia.org/w/index.php?title=Field-oriented_control&oldid=1354069032 — curl **200**; raw sha256 `6fa0f8acb2e107493968f2813484d6642bad05340fa3231319f24272bb4ecaec`. Qualitative cross-check only (“A decoupling term is sometimes added…”). Induction-machine equations are a different model and are not the formula body. 以 SimpleFOC 文档为准.

Lesson-chosen toy parameters (`R = 0.8000`, `L_d = 0.0020`, `L_q = 0.0024`, `n_pp = 7`, `K_e = 0.0400`, `dt = 1.000e-4`, PI gains, `V_LIM = 24.0000`, `noise_i = 0.0200`, and the two regime speeds / currents) were named on the page before the official first run. Official SimpleFOC flash 本页未运行.

## Official first run

`foc_dq_decoupling_toy.py`, 2026-11-20 17:01:41 Asia/Shanghai, byte-identical on rerun. Expected sha256 `27221a07f3f0f4f08fc3cad3468ffea41046811293ebac453033c4d5d7e52d44`. Official `expected/` was not retuned.

## Pre-declared cells

All held and are disclosed in the en/zh results.

- low_speed_settled: B-A `id_rmse -1.355e-7+-3.902e-7`, **near-tie** (|m| <= sd), 1 of 5 seeds has the opposite sign; B-A `iq_rmse -1.002e-8+-1.002e-7`, **near-tie**, 3 of 5 seeds have the opposite sign. Declared may near-tie; held; kept.
- high_speed_iq_step: B-A `id_rmse -0.2667+-0.0008`, **clear**, same sign on all 5 seeds; B-A `iq_rmse -0.0621+-1.596e-4`, **clear**, same sign on all 5 seeds (B consistently better; held, kept). Wrong-sign C-B `id_rmse 0.5639+-0.0009`, **clear**, same sign on all 5 seeds; C-B `iq_rmse 0.1384+-2.698e-4`, **clear**, same sign on all 5 seeds (lose kept).
- Named alternative `ALT_VOLTAGE_MODE_LAG` was printed on the same streams and not adopted (on the settled cell a perfect-model inversion can look tight, ALT `id_rmse 8.147e-8+-0.0000`; on the dynamic cell ALT-B `id_rmse 0.2197+-0.0009`, **clear**, same sign on all 5 seeds).

## Post-first-run disclosures

There was no official toy or `expected/` change after the first run. Lesson prose (including the SimOutput embedding and the results / work-plan wording), hooks, curriculum, plans, sources, README typography and tip locks were written after those figures were frozen. A later MDX compile required wrapping `|m| <= sd` in backticks in the en/zh lesson prose so the less-than sign would not be parsed as a tag; official expected/ was not retuned. No lock relaxed. Existing `foc_current_loop_toy.py` and `clarke_park_toy.py` were not retuned. `kinematics.py`, `grip_sweep.py`, `package.json` / lockfile, and `.github/workflows` are untouched.

## Mismatch with §9

None.

## Lock changes

New batch-28 PR2 block in `tools/check_diagrams.mjs` (toy, expected, CRN, label order, required current-mode page addition and official-feedforward contrast, sources, plans, README, declared regimes) plus `tools/test_b28p2_foc_dq_decoupling_toy.py`. Tipped site-total, host-minute, month-total and Current-header locks only (45540→45720, M11 4350→4530, foc-actuator-lab 480→660, README `45 540`→`45 720`). Historical strings inside already-written plan/sources files were not edited, including `Current / 当前：**M11 4350 min**, Batch-24 PR3`, `Current / 当前：**M8 4530 min**, Batch-28 PR1`, and `Current / 当前：**M8 4350 min**, Batch-25 PR2`. M8 stays 4530. No lock relaxed.

- README `/45 540/` and `约 45 540 分钟` → `/45 720/` and `约 45 720 分钟`.
- Curriculum sum checks `45540` → `45720`; live M11 sum checks 4350→4530; live host-minute check 480→660 on foc-actuator-lab.
- Current-curriculum month table: M11 4350→4530; M8 stays 4530.
