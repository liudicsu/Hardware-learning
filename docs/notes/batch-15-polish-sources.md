# Batch-15 polish source audit

Base: `8ad7892` (batch-15 PR3 merged as #163; site **32490**, 71 lessons). Minutes unchanged: **71 / 32490**. No new sections that add minutes, no new slugs, no workflow edits, no lock relaxed. J-STD-020 stays shelved (not cited).

## 1. m4 slam-nav — RPP min reading has an implementation basis

Fetched with `curl -sL` on 2026-11-10 (Asia/Shanghai UTC+8) and read:

- https://raw.githubusercontent.com/ros-navigation/navigation2/main/nav2_regulated_pure_pursuit_controller/src/regulated_pure_pursuit_controller.cpp — HTTP **200**, 439 lines (branch head `f9c8761`, committed 2026-11-10 04:39 UTC+8). `applyConstraints()` starts at **line 372**; curvature limit at lines 378–382 (`heuristics::curvatureConstraint`), proximity limit at lines 384–387 (`heuristics::costConstraint`); **line 389** comment `// Use the lowest of the 2 constraints, but above the minimum translational speed`; **line 390** `linear_vel = std::min(cost_vel, curvature_vel);`; **line 391** `linear_vel = std::max(linear_vel, params_->regulated_linear_scaling_min_speed);`; then the approach constraint (line 394) and a clamp to `max_linear_vel` (line 399).
- https://raw.githubusercontent.com/ros-navigation/navigation2/jazzy/nav2_regulated_pure_pursuit_controller/src/regulated_pure_pursuit_controller.cpp — HTTP **200**, 570 lines (branch head `94d1c2a`, committed 2026-11-04 05:11 UTC+8). `applyConstraints()` at **line 455**; comment at **line 472**; **line 473** `linear_vel = std::min(cost_vel, curvature_vel);`; **line 474** `std::max(linear_vel, params_->regulated_linear_scaling_min_speed)`; clamp to `desired_linear_vel` (line 482).
- https://raw.githubusercontent.com/ros-navigation/navigation2/main/nav2_regulated_pure_pursuit_controller/include/nav2_regulated_pure_pursuit_controller/regulation_functions.hpp — HTTP **200**, 139 lines (jazzy 140 lines, HTTP 200): `curvatureConstraint` (lines 41–49), `costConstraint`, and `approachVelocityConstraint` ending in `std::min(constrained_linear_vel, approach_vel)` (main line 132).
- `.../src/regulation_functions.cpp` on main and jazzy: HTTP **404** (the heuristics live in the header); not cited.

So the source does show `std::min(cost_vel, curvature_vel)`, the same conservative reading the toy uses, while the RPP paper's text (arXiv 2305.20026) says maximum. The en/zh sentence states this and marks it 以原文为准.

## 2. m10 intervention-logging — MAP-VLA authors

https://arxiv.org/abs/2511.09516 — HTTP **200**, `citation_author` meta tags read: Runhao Li, Wenkai Guo, Zhenyu Wu, Changyuan Wang, Haoyuan Deng, Zhenyu Weng, Yap-Peng Tan, Ziwei Wang (**8 authors**), title "MAP-VLA: Memory-Augmented Prompting for Vision-Language-Action Model in Robotic Manipulation", submitted 12 Nov 2025. This matches the two `resources.ts` cards (full list already there). Prose now reads "Runhao Li et al., 8 authors with the full list on the resource card" / "Runhao Li et al.，即 Runhao Li 等 8 位作者，完整名单见资源卡片"; the existing `Runhao Li et al.` lock text is kept.

## 3. m1 python-terminal — why about two samples per period

One intuitive sentence in en and zh after the Nyquist worked example: the samples must catch the sinusoid going both up and down, so more than two per period (at least one per half-cycle), otherwise a slower sinusoid passes through the same sample points. Derived; consistent with the Nyquist–Shannon page already cited there (rate above 2B).

## Lock changes

New `batch-15 polish` block in `tools/check_diagrams.mjs` (extends only): the std::min sentence and source path in slam-nav en/zh, the 8-author wording in intervention-logging en/zh, the two-samples sentence in python-terminal en/zh, this note's URLs / statuses / line numbers, and site 32490. No lock relaxed.

## Models / reproducibility

opencode free models were asked first (`/workspace/b15pol-opencode/`) how the controller combines the two speeds: `deepseek-v4.1-flash-free`, `glm-5.3-flash-free` and `mimo-v2.6-flash-free` answered `std::min(cost_vel, curvature_vel)` followed by `std::max(..., regulated_linear_scaling_min_speed)` (DeepSeek cited line 390); `longcat-2.5-free` gave no answer. Their answers were only a cross-check; the cited lines come from the raw files fetched above. Edits made locally in `/workspace/hl-b15pol`.
