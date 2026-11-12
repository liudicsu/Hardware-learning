# Batch-18 PR2 sources / 来源记录

Base `26d4664edc52abc3a0c35b8c960ddc29d35b5057` (`26d4664`, main after #173; site **35040**). This PR: M4 slam-nav 630→810 (+180), M7 mujoco-so101 240→420 (+180); site **35040→35400**; M4 2850→3030, M7 2790→2970; still 71 lessons.

## Opened sources

All fetched with curl on 2026-11-12 (Asia/Shanghai), then read as text (HTML; Curless PDF via `pdftotext`).

| Resource id | URL | Version | What is used |
|---|---|---|---|
| `octomap-site` (new) | https://octomap.github.io/ | HTTP **200**, fetched 2026-11-12 | occupied and free space, unknown encoded implicitly, probabilistic updates, multi-resolution compact octree; library developed by Kai M. Wurm and Armin Hornung |
| `curless-volrange` (new) | https://graphics.stanford.edu/papers/volrange/volrange.pdf | HTTP **200**, SIGGRAPH 1996; authors **Brian Curless, Marc Levoy** | cumulative weighted signed distance function; incremental Di+1 = (Wi Di + wi+1 di+1)/(Wi+wi+1), Wi+1 = Wi+wi+1; truncate near the surface; isosurface |
| `open3d-tsdf` (new) | https://www.open3d.org/docs/latest/tutorial/pipelines/rgbd_integration.html | HTTP **200**, Open3D 0.20.0 docs | ScalableTSDFVolume, `sdf_trunc` as the truncation value; “TSDF volume works like a weighted average filter in 3D space. If more frames are integrated, the volume produces a smoother and nicer mesh.” |
| `mujoco-computation` (new) | https://mujoco.readthedocs.io/en/stable/computation/index.html | HTTP **200**, stable docs, fetched 2026-11-12 | Integrators: explicit Euler pedagogical but not implemented; semi-implicit Euler (velocity first, position with the new velocity) strictly better; implicit / implicitfast implicit-in-velocity only (Taylor expansion in velocity); integrating some gyroscopic terms explicitly “can lead to energy gain and divergence of fast-spinning free bodies”; existing `grip_sweep` text contrasted, not replaced |
| `hornung-auro` (not cited) | http://ais.informatik.uni-freiburg.de/publications/papers/hornung13auro.pdf | HTTP **500**, empty body | **not cited** |

Statements from the opened sources are marked 以原文为准 / 以论文为准 on the site. No real lidar, Open3D, `octomap_server`, MuJoCo binary or Menagerie run (本页未运行). Hornung AURO PDF is not cited.

## Toy design

- `examples/month-4/slam-nav/octomap_tsdf_volume_toy.py`: shared 4 m cube, 0.25 m voxels, floor slab plus a hanging box (72 overhang voxels, 328 occupied). Arms A_grid2d (project hits to the floor) / B_octree (log-odds hit at the endpoint, miss along the ray, unknown otherwise) / C_tsdf (Curless incremental D, W update) / S_single (first-frame hit occupancy, same walk as B's hits) / C_bad (TSDF with the first camera shifted 0.5 m). Common random numbers; seeds 0–4; per-seed range noise reused by every arm. C surface MAE is mean |D - sdf_true| on updated voxels with |sdf_true| ≤ sdf_trunc; raw surface MAE is mean |range_meas - range_gt|. Unknown means neither a hit nor a clearing ray (printed count 0.0000±0.0000). Not the PGM / DWA / costmap path, not the depth-pointcloud voxel pass.
- `examples/month-7/mujoco-so101/mujoco_integrator_energy_toy.py`: shared stdlib pendulum (light damping) and a tumbling asymmetric spinner (no quaternion). Arms A_explicit / B_semimpl / C_implvel / C_bad (sign-flipped D). Common random numbers; seeds 0–4; per-seed initial-condition jitter reused by every arm. Stable-step: the criterion is the strict inequality h < h* = 2/ω0 = 0.6385508568 s (at h = h* the trace is −2, a repeated eigenvalue −1 in a Jordan block, solution grows linearly: hand/analytic, not a printed toy number); default h = 0.1500 s is below it; tests at 0.50× / 0.98× / 1.02× h* and a half default step. Not `mujoco.step`, not a redo of `grip_sweep`.
- Labels as in batch-15/16/17/18 PR1 (tie → numerically zero below 1e-9 → near-tie `|m| ≤ sd` → consistent, small under 20 % of the smaller arm mean else clear, with sign count).

## Results (k/N = seeds with the reported sign)

OctoMap / TSDF (printed):

- overhang_multiview: A overhang recall 0.0000±0.0000; B 0.9861 on every seed; C 0.9833±0.0062. Paired B-A and C-A overhang recall **clear**, same sign on all 5 seeds. A's occupied IoU 0.6555±0.0048 vs B 0.5780±0.0067 is printed and kept (the declared 3-D win is overhang recall). B nodes 1677.8000±0.4472 / dense 4096.
- single_frame_clean: paired B-S occupied IoU 0.0316±0.0000, **small but consistent**, 5/5. The declared near-tie did not hold (kept).
- noisy_multiview: C surface MAE 0.0631±0.0018 m vs raw 0.0953±0.0015 m, paired C-raw -0.0322±0.0024, **clear**, 5/5.
- bad_pose: C 0.0440±0.0006 m, C_bad 0.0466±0.0007 m, paired C_bad-C 0.0026±0.0004, **small but consistent**, 5/5 (kept).

Integrator energy (printed):

- Stable-step: criterion is strictly h < h* (not h ≤ h*). 0.98× h* energy_bounded=1, spectral radius 1.000000; 1.02× grows, spectral radius 1.490835; half default step bounded; assert_below_hstar=1. The linear growth at exactly h* is hand/analytic and is not printed.
- moderate_h: A |dE| 63.3880±2.9999 (blow 2/5); B 0.4783±0.0811; C 0.4451±0.0762. Paired A-B 62.9097±3.0587 **clear** 5/5.
- tiny_h: declared near-tie on |dE| did not hold. A |dE| 0.0346±0.0091 looks smaller than B 0.4880±0.0941 because energy gain cancels damping; |E-Eref| A 0.4553±0.0855 vs B 0.0019±0.0005, paired A-B 0.4534±0.0850 **clear** 5/5 (kept).
- large_h_spin: pendulum A blows 5/5, |dE| 92.5926±16.7441; spinner A and B **tie** at 52.8938±16.4901 (identical velocity update); C |dE| 13.3682±0.2701; A-C 39.5256±16.3407 **clear** 5/5.
- inconsistent_D: C_bad |dE| 12527.3906±6611.5011, blow 5/5; C_bad-C 12514.0224±6611.4795 **clear** 5/5 (kept).

Every number in the lesson prose, Summary and this note is printed by the toys into `expected/` (paper/docs wording is marked 以原文为准 / 以论文为准 and is not a toy measurement).

## Post-hoc choices

- `sdf_trunc=0.25` m was chosen after the first run. The first run used 0.50 m; at that truncation, C did not beat the raw range MAE on noisy_multiview (paired C-raw 0.0131±0.0034, small but consistent, against TSDF). That cell is printed as the alternative and kept. The surface-MAE definition itself was also switched after a first, buggy zero-crossing extractor (to |D - sdf_true| in the truncation band, labelled in the stdout).
- |E-Eref| was added as a printed companion metric after the first integrator run showed that |dE| from E0 can be misleading under damping. The declared tiny_h near-tie is still reported as not holding.
- No layout or plant was claimed as written before the first run if it was not. The hanging-box geometry, default h, h* formula, inertias and the flipped-D fail arm were written before the first run.

## Mismatch with §9

- H3 single-frame occupied-IoU **near-tie** did not hold: B-S is 0.0316±0.0000, small but consistent, 5/5. Printed and kept.
- H3 noisy-view TSDF win holds at the accepted `sdf_trunc=0.25` m, not at the first-run 0.50 m (that unfavourable alternative is kept).
- H4 tiny_h **near-tie** on |dE| did not hold. Printed and kept; the companion |E-Eref| shows A clearly worse, not better.
- No other mismatch: CRN, ≥5 seeds, stable-step at 0.98× / 1.02× / half step, pre-declared lose cells kept, every prose number printed by the toy, en/zh synced, Hornung PDF not cited, ≠ PGM / DWA / grip_sweep.

## opencode

Free-model attempts (DeepSeek, GLM, MiMo, LongCat, MiniMax flash-free) were run first via `opencode run` with a 40 s timeout each, as in batch-18 PR1. They produced no usable toy files; the toys and pages were implemented locally against the opened sources and the locked regimes.

## Lock changes

- Tip / totals only, plus an additive lock for this PR: slam-nav minutes 630→810, mujoco-so101 240→420, M4 2850→3030, M7 2790→2970, site 35040→35400 / README 35 040→35 400, and the month-totals array in the deepen-3 / current-curriculum check. Existing DWA / ICP / grip_sweep bindings are not relaxed.
- No lock relaxed.

