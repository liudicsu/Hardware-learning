# Batch-29 PR1 sources

Unit: H1 Y-Δ / Δ-Y reduction of two-terminal networks (`ohms-law`, 390→570). Site **45900** = 45720+180; M1 **3090** (still lightest); still 71 lessons. Branch `feat/ydelta-network-reduction` from `5dec4b5b09ba627d44f4702cc589793d7e6bac0f`. After this PR alone, site typography is `45 900` (the full-batch target 46 080 is after PR2). M2 stays 4110; M8=M11 stay jointly heaviest at 4530. These load facts are recorded here and in the month-1 plan Current header only, not as a student-facing process lecture. Parent accepted the 2-unit batch; this PR is H1 only. H2 / `esp32` was not started.

## Pins actually opened (re-fetched live at writing)

This is a Wikipedia page, not an arXiv record: no Comments header and no journal-ref field were present, and none was invented.

- English Wikipedia *Y-Δ transform*, raw oldid **1369326226**, https://en.wikipedia.org/w/index.php?title=Y-%CE%94_transform&action=raw&oldid=1369326226 — curl **200**; raw sha256 `40643fc21df5c477d02bd580ce6871fef849ef5efeeba200e221a7b41b27c28c`. Revision timestamp 2026-08-14 08:11:14 GMT = 2026-08-14 16:11:14 Asia/Shanghai. Identical raw hash to the parent re-check and to the cached body at `/tmp/b29p1-parent-recheck/ydelta.raw`; no raw-hash drift. The HTML wrapper Last-Modified can move without a revision change and is not the formula-body pin. Canonical article URL in `resources.ts`: https://en.wikipedia.org/wiki/Y-%CE%94_transform. This page was **not** already in `src/lib/resources.ts`, `src/lib/curriculum.ts`, or the host MDX; it is added here as a new Resource / reading-map / curriculum entry `wiki-ydelta` and is the formula body. 以原文为准: names (wye-delta, star-delta, T-Π, Kennelly 1899), the three-resistor special case of star-mesh, equivalence of three-terminal networks, the opened Δ↔Y formulae with labels R1, R2, R3 / Ra, Rb, Rc (including the rewritten Y→Δ forms), and the *Simplification of networks* statement that series and parallel transforms “do not suffice” for a bridge, while Y-Δ can eliminate a node (or Δ-Y can add a node) so the net can be reduced further.

Lesson-chosen toy parameters (ladder `RS1=1000`, `RP1=2000`, `RS2=3000`, `RP2=4000`, `RS3=5000` ohm; bridge `RPL=100`, `RPR=10000`, `RQL=10000`, `RQR=100`, `RX_LARGE=1000000`, `RX_MODERATE=100` ohm; `VTEST=1.0 V`; `clear_frac=0.2000`; work plan `30+25+50+40+35=180`) were named in the toy header / `hand_calc` lines before the official first run. Real breadboard / DMM 本页未运行. No Falstad claim that the toy was clicked on this page. No invented datasheet values.

## Official first run

`ydelta_network_reduction_toy.py`, 2026-11-20 18:49:31 Asia/Shanghai, byte-identical on rerun. Expected sha256 `8bd78d13521c96a254c1de450e9e5aacf2ce50f0095ad30bb336ef357ca74610`. Official `expected/` was not retuned.

## Pre-declared cells

All held and are disclosed in the en/zh results.

- series_parallel_ladder: paired A-B Req `0.0000+-0.0000: tie: identical on every seed`. Declared exact tie; held; kept.
- large_cross_bridge: paired A-B Req `24.3794+-0.0000 ohm`, **small but consistent gap, not a tie** (`|m| > sd`; same sign on all 5 seeds). This is the allowed “or small” form of the pre-declared near-tie-or-small claim (not `|m|<=sd`; there is no seed noise). Held; kept. The paired residual of A-B versus 0 is labelled a clear gap because 20 % of the smaller residual mean is 0; the scoring label is the paired A-B Req label.
- moderate_bridge: paired A-B Req `4757.7670+-0.0000 ohm`, **clear**, same sign on all 5 seeds (B clearly better than A; held, kept). Paired C-B Req `-258.9083+-0.0000 ohm`, **clear**, same sign on all 5 seeds (C loses; kept).
- Named alternative `RX=10000000 ohm` was printed on the same bridge arms and not adopted (paired A-B Req `2.4490+-0.0000 ohm`, still small but consistent).

## Post-first-run disclosures

There was no official toy or `expected/` change after the first run. Lesson prose (including the SimOutput embedding and the results / work-plan wording), hooks, curriculum, plans, sources, README typography and tip locks were written after those figures were frozen. `|m| <= sd` was wrapped in backticks in the first official en/zh draft so the less-than sign would not be parsed as a tag; official expected/ was not retuned. No lock relaxed. Existing `thevenin_loaded_divider_toy.py` and `superposition_linear_circuit_toy.py` and their `expected/` were not retuned or edited. The Wheatstone-disambiguation sentences on this page were left byte-untouched. Avoided hosts including `components` and `wiki-wheatstone` were not reopened. `package.json` / lockfile, `.github/workflows`, `kinematics.py`, `grip_sweep.py`, `servo_loop_sim.py`, and python-terminal `ohm.py` / `resistors.py` / `log.py` are untouched. The authoritative proposal file was not edited.

## Mismatch with §9

None. (The large-cross cell is the disclosed “or small” form, not a failed claim.)

## Lock changes

New batch-29 PR1 block in `tools/check_diagrams.mjs` (toy, expected, CRN, label order, required `wiki-ydelta` addition, official Δ↔Y vs series-parallel-only contrast, sources, plans, README, declared regimes) plus `tools/test_b29p1_ydelta_network_reduction_toy.py`. Tipped site-total, host-minute, month-total and Current-header locks only (45720→45900, M1 2910→3090, ohms-law 390→570, README `45 720`→`45 900`). Historical strings inside already-written plan/sources files were not edited, including `Current / 当前：**M1 2910 min**, Batch-22 PR1`. No lock was jumped to 46080 / `46 080`. M2 stays 4110; M8=M11 stay 4530. No lock relaxed.

- README `/45 720/` and `约 45 720 分钟` → `/45 900/` and `约 45 900 分钟`.
- Curriculum sum checks `45720` → `45900`; live M1 sum checks 2910→3090; live host-minute checks 390→570 on ohms-law.
- Current-curriculum month table: M1 2910→3090; other months unchanged.
