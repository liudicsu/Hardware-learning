# Batch-8 PR3 source, scope and validation audit

Base: 1d2717b1f5d0a71e18da4c4b048ab60da7ac2f4d (#134 merged). Proposal §9 PR3 locks: H5 6.1 VQ-BeT +210, H6 6.3 dual-system VLA +210. No arithmetic mismatch: curriculum.ts on 1d2717b gives M6 1560 (behaviour-cloning 240, vla-models 360) and site 24240; after this PR M6 1560+210+210=1980 and site 24240+420=24660 (batch-8 final, matching proposal §4–5); 71 lessons. All 197 prior expected files remain byte-identical; two are added. README site copy (still 23 610 after PR1/PR2) updated to 24 660, as proposal §4–5 asks for the batch end.

## Opened sources (curl -L, 2026-11-09, Asia/Shanghai UTC+8)

- `vqbet-paper` — https://arxiv.org/abs/2403.03181 — HTTP 200; also read https://arxiv.org/html/2403.03181 (HTTP 200): BeT k-means limits, residual VQ with primary/secondary codes, N_q = 2, offset head, 5× sim / 25× real speed-up over diffusion (cited only as 以论文为准).
- `vqbet-project` — https://sjlee.cc/vq-bet/ — HTTP 200.
- `bet-paper` — https://arxiv.org/abs/2206.11251 — HTTP 200 (title/abstract page); BeT mechanism described via VQ-BeT §2.2.
- `openhelix-paper` — https://arxiv.org/abs/2505.03912 — HTTP 200; also read https://arxiv.org/html/2505.03912 (HTTP 200): System 1/2 definition, real-time perception criterion excluding π0 / GR00T N1, family table (LCB, DP-VLA, HiRT, RoboDual), §3.1 LLaVA + linear projector + 3D Diffuser Actor, prompt-tuned <ACT>, projector/MLLM joint-training collapse, CALVIN-D (numbers not quoted; 以论文为准).
- `openhelix-project` — https://openhelix-robot.github.io/ — HTTP 200; finding that action tokens mostly reflect instruction semantics.

Not cited: proposal's https://huggingface.co/docs/lerobot/policy_vqbet returns HTTP 200 with only a "doesn't exist in v0.7.0" notice, and the suggested main-version URL https://huggingface.co/docs/lerobot/main/en/policy_vqbet returned 404. No LeRobot VQ-BeT doc is cited.

## Toy design

- `vqbet_residual_vq_toy.py`: synthetic two-mode obstacle demos (60 train + 60 held-out per seed), five seeds, 100 rollouts each on a shared rollout stream; same observation bins and count-based heads. MSE per-observation mean vs k-means K=8 + offsets vs residual VQ 4+4 + offsets; equal stored codebook vectors (8) and Lloyd iterations (12); unequal code combinations (8 vs 16) and head/offset table sizes printed and labelled. Result: MSE 66 % collisions; k-means and rvq both keep both modes with no collisions; reconstruction close. No winner between discrete arms.
- `dual_system_vla_cadence_toy.py`: synthetic moving targets with a mid-episode red→blue instruction switch, eight switch-time seeds, equal 1.0 compute unit per tick, declared per-arm information: slow single, fast single (instruction parsed once, uncharged — labelled), dual with real-time System 1 perception, dual without it. A static/no-switch scenario shows single-rate arms lose nothing. No winner declared. π0 never called dual-system; TwinVLA (6.2) untouched.

Independent tests: tools/test_b8_vqbet_dualsystem_toys.py.

## Models / reproducibility

Tried opencode/deepseek-v4.1-flash-free and mimo-v2.6-flash-free (no content within 40 s) and glm-5.3-flash-free (returned only a two-stage residual-VQ encode function, equivalent to the local one); LongCat and MiniMax free IDs were absent from `opencode models`. Implemented locally. Worktree /workspace/hl-b8p3, node_modules hardlinked via `cp -al`.

## Local validation

check_diagrams, check_widgets, check_wokwi, check_quotes, month 1–11 check.sh, lint, next typegen, tsc --noEmit, production build, independent tests. No workflow edits.
