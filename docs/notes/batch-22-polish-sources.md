# Batch-22 polish sources — EgoVLA pre-fix comparison, PointVLA author order, toy label sweep

Base: `bd88324f324ce9c082f5799a715bf8eacf997e27` (batch-22 PR3 #191 merged; site **40140**, catalogue **71**).
This PR: site stays **40140**, catalogue stays **71**; no minute count changed.

## Sources

| id | URL | What was used |
|---|---|---|
| pointvla-paper | https://arxiv.org/abs/2503.07511 | Abstract page author order: Chengmeng Li, Junjie Wen, Yan Peng, Yaxin Peng, Feifei Feng, Yichen Zhu. PDF / HTML byline (v1): Chengmeng Li∗, Yichen Zhu∗†, Junjie Wen, Yan Peng, Yaxin Peng†, Feifei Feng; † is defined as corresponding author, ∗ is not spelled out in the body read and is described on the page as the usual co-first-author mark. |

## Item by item

1. **umi-style-collection (m11) EgoVLA toy and en/zh section.** The toy gains `ridge_fit_prefix`, the pre-fix solver with the symmetric intercept row left unfilled, labelled in the output "erroneous version, kept only for comparison / 漏填对称截距行的错误版本，仅作对照" and "not an official verdict". On the same seeds it prints pre-fix half-data B minus full-data B long_sr 0.0400±0.1012 (near-tie, 1 of 5 seeds opposite), and a solver check on the noise-free demonstrations of seed 0, task 0: pre-fix max |θ error| 0.0736, |b error| 0.1240; corrected 4.253e-8 and 7.161e-8. Official verdicts still use the corrected solver (`prefix=False` by default). The page sentences "more than 0.5" / "about 1e-7" (from different, unprinted data) are replaced by these printed numbers, and the pages say the comparison is newly added. The PR3 sources note is corrected the same way. Every earlier printed line is byte-identical: `diff` of the old and new `expected/` shows only three added lines, and a SHA-256 of the output with those three lines removed equals the old file.
2. **PointVLA author order.** Lesson en/zh and the resource card now say the arXiv abstract page order is Li, Wen, Yan Peng, Yaxin Peng, Feng, Zhu; the PDF/HTML byline is Li, Zhu (both asterisked), Wen, Yan Peng, Yaxin Peng, Feng; the page and card use the abstract-page order. "arXiv order" became "arXiv abstract-page order".
3. **PointVLA C−B ties.** A sentence in en/zh says the C−B height_err_mm and false_grasp lines print 0.0000±0.0000 because B and C share the same height-correction path and presence check: equal by construction, not a finding.
4. **Process labels inside four toys**, their outputs and the embedded copies on m4/slam-nav, m5/camera-calibration, m7/mujoco-so101 and m8/async-deployment (en/zh):
   - `eight_point_essential_toy.py` comment: "same label rules as the batch-13 lead-lag toy" → "same label rules as the lead-lag toy".
   - `nora_fastplus_small_vla_toy.py` docstring: the trailing revision and drafting note removed.
   - `octomap_tsdf_volume_toy.py` docstring: "returned HTTP 500 this round" → "returned HTTP 500 when fetched".
   - `mujoco_integrator_energy_toy.py`: comment "(polish addition)" → "(added after the original regimes)"; printed heading "(added in polish; not a pre-declared regime)" → "(added after the original regimes; not a pre-declared regime)".
   - Each toy was rerun and `expected/` regenerated. eight-point, NORA and OctoMap outputs are byte-identical; the MuJoCo output differs in that one heading line only. A numbers-only comparison (every printed number in order) is identical for all four: 226, 134, 272 and 389 numbers.
5. **check_diagrams console tips** for the batch-22 PR1 / PR2 blocks now print site 40140 (and M11 3990 for PR2).

Not changed: the esp32 "not datasheet values" wording and the UM10204 mirror remain deferred.

## Lock changes

- New block: EgoVLA rerun equals `expected/`; SHA-256 of the output without the three comparison lines pinned to the old file; the three new lines pinned; the pre-fix solver differs from the official one only by the missing row; official verdicts default to the corrected solver; page and note sentences carry the printed numbers and the old unprinted figures are gone; PointVLA author-order sentences and card text; C−B construction-tie sentences; byte-identical output hashes for the eight-point, NORA and OctoMap toys and a numbers-only hash for the MuJoCo toy; a site-wide process-label check over every toy source and every `expected/` output (narrow pattern: batch only with a number, so training "batch" sizes pass); the four lesson pages free of the removed labels. Plus `tools/test_b22pol_ego_prefix_and_labels.py`.
- The batch-17 MuJoCo lock string for the damped-criterion heading was updated to the new wording (same check, new text).

No lock relaxed.
