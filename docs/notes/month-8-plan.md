# Month 8 plan: Foundation-model fine-tuning, deployment & robot systems engineering

Site supplement beyond @DeRonin_'s 6-month roadmap. Proposal: `/workspace/proposals/m7-m8-proposal.md` §3 / §5 / §6.
Batch 1 (this PR): scaffold all seven lessons; full MDX + examples for **8.1, 8.3, 8.5, 8.6**.
Later batch: full MDX + examples for **8.2, 8.4, 8.7**.
Electives E8-a/b/c/d stay on the month page topics only (not formal lessons, not in minutes).

Constraints: private env; runnable toys prefer stdlib CPU with fixed seeds. GPU / true PolicyServer / real SO-101 / binary MCAP readers marked「本页未运行」. Hard facts re-fetched from primary sources (2026-11-04 UTC+8), not copied from the proposal. Isaac Lab stays out of core. ISO 10218-1: name/principles only (iso.org 403). docs.ros.org anti-bot → prefer `ros2/ros2_documentation` jazzy RST when scraping.

| # | slug | minutes | this batch | runnable | verified against |
|---|------|---------|------------|----------|------------------|
| 1 | `dataset-engineering` | 180 | **full** | `dataset_audit.py` + synthetic fixture (stdlib) | HF LeRobot dataset-v3; SmolVLA ~50 eps / 5×10; arXiv 2310.08864 |
| 2 | `vla-finetune` | 240 | outline | (later) | HF SmolVLA; openpi; lerobot pi05/groot |
| 3 | `async-deployment` | 180 | **full** | `chunk_latency_sim.py` (stdlib) | HF LeRobot async (PolicyServer/RobotClient; actions_per_chunk; chunk_size_threshold) |
| 4 | `ros2-hardware-interface` | 240 | outline | (later) | control.ros.org Jazzy writing-hw-component / joint limiting |
| 5 | `safety-reliability` | 180 | **full** | `watchdog_sim.py` (stdlib) | ISO/TS 15066 catalogue scope; HIL-SERL; no STS3215 overload numbers; ISO 10218-1 name only |
| 6 | `robot-devops` | 180 | **full** | `bag_stats.py` (stdlib) | rosbag2 jazzy `default_storage_id.cpp` → `"mcap"`; Iron release notes; docker-vscode RST; action-ros-ci |
| 7 | `capstone` | 300 | outline | (later) | portfolio_check 8 parts; Month 6 eval protocol |

Rechecks from proposal §6 (batch 1):
- **Jazzy rosbag2 default mcap** — confirmed: `ros2/rosbag2` branch `jazzy`, `rosbag2_storage/src/rosbag2_storage/default_storage_id.cpp` returns `"mcap"`; README agrees. Iron first switched the default writer to MCAP.
- ISO 10218-1 still Cloudflare/403 — name and general principles only; no clause numbers.
- ISO/TS 15066 catalogue: industrial collaborative systems; **does not apply** to non-industrial robots — stated in lesson.
- micro.ros.org hardware page: elective only; not dug into this batch.
- Isaac Lab: not in core (Month 7 elective wording already).

Widgets: `ChunkTimelineWidget` / `WatchdogWidget` deferred (must be measurable via check_widgets; not in this batch). Lessons note the deferral.

Verification: `examples/month-8/check.sh` (hooked into `tools/sim/reproduce.sh`), check_diagrams bindings + mutations, check_widgets, check_quotes, lint, check_wokwi, tsc, CI build, check_text_size.
