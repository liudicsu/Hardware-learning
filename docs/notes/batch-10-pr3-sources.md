# Batch-10 PR3 source, scope and validation audit

Base: `e814307` (#142 merged; site **26520**). Proposal §9 PR3 locks: H4 10.4 multi-view-extrinsics SpatialVLA +210, H5 9.9 world-models-overview MemoryVLA +210. No arithmetic mismatch: curriculum.ts on base gives M10 2280 / M9 3480 / site 26520; after this PR M10 **2490**, M9 **3690**, site **26940**; 71 lessons. All prior expected files remain byte-identical; two are added. README site copy updated 26 520 → 26 940.

## Opened sources (curl -L, 2026-11-09, Asia/Shanghai UTC+8)

- `spatialvla-paper` / Qu et al.: https://arxiv.org/abs/2501.15830 and https://arxiv.org/html/2501.15830, HTTP 200. Ego3D Position Encoding in the egocentric camera frame eliminates robot–camera extrinsic calibration; Adaptive Action Grids use CDF/PPF discretization (vs linear 256-bin); 1.1 Million real episodes. Benchmark % 以论文为准. Same work: RSS 2025 (doi 10.15607/RSS.2025.XXI.011). Not an AX=ZB rewrite.
- `memoryvla-paper` / Shi et al.: https://arxiv.org/abs/2508.19236 and https://arxiv.org/html/2508.19236, HTTP 200. Working memory + Perceptual-Cognitive Memory Bank (retrieve / consolidate / fuse) + memory-conditioned diffusion action expert. Reported 71.9% / 72.7% / 96.5% / 41.2% and real-robot 84.0% / long-horizon +26 以论文为准.
- Neighbour same-line work (reading only, not a toy): MemoryVLA++ https://arxiv.org/abs/2606.09827 (curl 200) — imagination / world-model futures; not implemented this PR.

Cached under `/workspace/b10p3-sources/` on the worktree host (not committed).

## Toy design

- `spatialvla_ego3d_grid_toy.py` (10.4): shared camera-frame points + translation actions; arms A 2D-only+uniform, B Ego3D+uniform, C Ego3D+empirical CDF/PPF bins; k-NN BC; action MAE + pick-success proxy; five seeds; no robot-base pose leak; ≠ AX=ZB host section.
- `memoryvla_bank_retrieve_toy.py` (9.9): shared delayed-cue POMDP; arms Markov / fixed window / memory-bank retrieve; equal move budget; no future leak; five seeds; ≠ MTC stage memory; ≠ DreamGen IDM.

Independent tests: `tools/test_b10_spatialvla_memoryvla_toys.py`.

## Models / reproducibility

opencode free models tried first (DeepSeek flash-free returned empty within 40 s); toys implemented locally in `/workspace/hl-b10p3` (`npm ci` for node_modules; prior hardlink donors lacked `next`).

## Local validation

`tools/test_b10_spatialvla_memoryvla_toys.py`, month-9 / month-10 `check.sh`, `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build. No workflow edits.
