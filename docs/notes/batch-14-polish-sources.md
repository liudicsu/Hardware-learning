# Batch-14 polish: Smith wrong_delay_big pure-mismatch subset; MAP-VLA authors; J-STD-020 recheck

Base: `89ca3ea` (batch-14 PR1–PR3 merged: #157, #158, #159; site **31380**, 71 lessons). Polish after the batch-14 查漏补缺 pass. Minutes unchanged: **71 / 31380** (M1 1800, M3 2310, M4 2490, M5 2670, M6 2820). No new sections that add minutes, no new slugs, no workflow edits, no lock relaxed.

## 1. control-modelling — wrong_delay_big pure-mismatch subset (must)

- Seeds 0–1 of `wrong_delay_big` round the wrong delay model to `k̂ = 0`, so arm C behaves exactly like A (delay-ignoring PI) with ~87 % overshoot. That collapse inflates both the 5-seed C−B mean and the sd.
- The toy now also prints a **pure-mismatch subset on seeds 2–4 only**, with the same label rules and same-sign counts written as k/3.
- Printed lines (byte-identical on rerun):
  - 5-seed C−B overshoot: `43.0091+-40.3948: clear gap, not a tie (|m| > sd); same sign on all 5 seeds`
  - subset C−B overshoot: `13.5172+-1.3548: clear gap, not a tie (|m| > sd); same sign on all 3 seeds`
  - subset C−B ISE: `0.1096+-0.0054: clear gap, not a tie (|m| > sd); same sign on all 3 seeds`
  - subset C−B settle: `2.7367+-0.0058: clear gap, not a tie (|m| > sd); same sign on all 3 seeds`
- en/zh prose at the wrong_delay_big bullet state both the 5-seed figures (≈ 43.0±40.4 overshoot) and the subset figures (≈ 13.5±1.4), and explain why they differ.
- `examples/month-5/expected/smith_predictor_delay_toy.txt` regenerated; independent tests in `tools/test_b14p2_tf_smith_toys.py` extended; b14p2 locks in `tools/check_diagrams.mjs` extended to cover the subset block (sign-count regex now accepts 3 or 5 seeds — an extension, not a relaxation).

## 2. Optional — MAP-VLA full author list

- Rechecked https://arxiv.org/abs/2511.09516 (2026-11-10, Asia/Shanghai UTC+8): `citation_author` meta tags are Runhao Li; Wenkai Guo; Zhenyu Wu; Changyuan Wang; Haoyuan Deng; Zhenyu Weng; Yap-Peng Tan; Ziwei Wang.
- `src/lib/resources.ts` cards `mapvla-html` / `mapvla-pdf` already list the full author string: `Runhao Li, Wenkai Guo, Zhenyu Wu, Changyuan Wang, Haoyuan Deng, Zhenyu Weng, Yap-Peng Tan, Ziwei Wang`. Matches the abstract page. No change needed.
- Prose keeps **Runhao Li et al.** (list is long), as allowed.

## 3. Optional — J-STD-020 recheck — **not cited**

Tried again (2026-11-10, Asia/Shanghai UTC+8):
- `https://www.jedec.org/standards-documents/docs/j-std-020e` → HTTP **403** (Cloudflare challenge / login wall).
- `https://www.jedec.org/sites/default/files/docs/j-std-020e.pdf` → HTTP **500**.
- `https://www.jedec.org/system/files/docs/JESD22-A113H.pdf` → HTTP **500**.
- No body text was opened, so the soldering reflow section is unchanged (Wikipedia / SparkFun only). Same conclusion as batch-13 polish.

## Lock changes

- **No lock relaxed.** Extended the existing b14p2 Smith locks (markers, outLines, langMarkers, sign-count regex for k/3) and added a batch-14 polish block in `tools/check_diagrams.mjs` that requires the subset header/lines, the en/zh prose contrast, this sources note, and the MAP-VLA full author string in `resources.ts`. Site total stays **31380**.

## Models / reproducibility

Implemented locally in `/workspace/hl-b14pol` (node_modules symlink to hl-b14p3). No opencode run for this polish.

## Local validation

`check_diagrams`, `check_widgets`, `check_wokwi`, `check_quotes`, eslint 0 warnings, typegen, `tsc --noEmit`, full `npm run build` including postbuild. No workflow edits. Minutes **71 / 31380**.
