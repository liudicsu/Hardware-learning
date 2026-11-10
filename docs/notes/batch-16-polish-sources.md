# Batch-16 polish sources / 来源记录

Base `25fb8f23382c7f59f5cf1e93a940dbae06d0f89f` (main after #167; site **33600**). Minutes unchanged (**33600**); no lesson added or removed.

## 1. Bridge rectifier topology diagram (1.2 components)

- New circuit diagram `bridge-rectifier-paths` (`src/lib/diagrams/specs/bridgeRectifier.ts`), shown with `<Diagram id="bridge-rectifier-paths" />` in the "Bridge rectifier and ripple" section of `src/content/m1/components/en.mdx` and `zh.mdx`, after the opened-sources list and before "Ripple from charge balance".
- The page had no diode numbering before. A short paragraph (en + zh) now defines it: D1 upper-left, D2 upper-right, D3 lower-right, D4 lower-left, every anode below its cathode (top rail +, bottom rail −). Positive half-cycle (terminal a above b): D1 + D3 conduct; negative half-cycle: D2 + D4. The load RL is crossed from the + rail to the − rail in both half-cycles; each path holds two diodes, matching the toy's `abs(src) - 2.0 * vf`.
- Two states with conventional-current paths: positive a → D1 → + rail → RL (top to bottom) → − rail → D3 → b; negative b → D2 → + rail → RL (top to bottom) → − rail → D4 → a. The smoothing capacitor (C in parallel with RL in the toy) is left out and the caption says so.
- Numbers computed in the spec and compared with the lesson's worked example: 12 V rms × √2 = 16.97 V; minus two 0.7 V drops ≈ 15.6 V.
- The circuit renderer gained two part types (`diode`, `ac`). `tools/check_diagrams.mjs` (generic circuit checks, extended): a diode carries current only when listed in the state's `closed` set, and only anode → cathode along the path; a blocking diode must not lie on the path; an `ac` source is never crossed, and a path that starts at one of its terminals must end at the other. Existing rules (supply → ground, loopReason, closed switches on path) are unchanged.

## 2. MAP-VLA authors in prose (10.5 intervention-logging)

- Fetched https://arxiv.org/abs/2511.09516 with curl on 2026-11-10 (Asia/Shanghai): HTTP **200**. `citation_title` "MAP-VLA: Memory-Augmented Prompting for Vision-Language-Action Model in Robotic Manipulation"; eight `citation_author` entries in order: Li, Runhao; Guo, Wenkai; Wu, Zhenyu; Wang, Changyuan; Deng, Haoyuan; Weng, Zhenyu; Tan, Yap-Peng; Wang, Ziwei; citation_date 2025/11/12 (v1).
- This matches `mapvla-html` / `mapvla-pdf` in `src/lib/resources.ts` ("Runhao Li, Wenkai Guo, Zhenyu Wu, Changyuan Wang, Haoyuan Deng, Zhenyu Weng, Yap-Peng Tan, Ziwei Wang").
- The sources line of the MAP-VLA section (en + zh) now lists all 8 names in that order; the substrings locked by batch-13/15 polish ("Runhao Li et al.", "8 authors with the full list on the resource card", "Runhao Li 等 8 位作者") are kept.

## Lock changes

- New `b16pol` block in `tools/check_diagrams.mjs`: diagram registered and placed in both language pages of the bridge section (before "Ripple from charge balance"); D1/D3 and D2/D4 as the conducting pairs; both flows cross RL top to bottom; positive path leaves terminal a; prose numbering in en/zh; all 8 MAP-VLA authors in order in en/zh prose and resources; this note; README minutes 33 600.
- Generic circuit checks extended for diodes and ac sources (see above). No lock relaxed; `.github/workflows` untouched.

## Models

- opencode free models were tried first for the diagram spec: deepseek-v4.1-flash-free exited without a file (it tried to read files outside its directory and was auto-rejected); glm-5.3-flash-free wrote a standalone `bridgeRectifier.ts` with its own invented types (not the repo's `CircuitSpec`), so it was not used; the run was stopped there. The spec, renderer and checks were written locally.

## Local validation

See the PR description (check_diagrams, check_widgets, check_wokwi, check_quotes, tools/test_*.py, month check.sh, lint, typegen, tsc, build + postbuild, CI=1 build).
