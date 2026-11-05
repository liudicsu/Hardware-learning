# Month 10 plan: Modern policy heads, deployment & real-world improvement

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Lessons open with "This lesson is a site supplement — Months 7–11 are not part of the original six-month course." / 「本课是本站补充内容——第 7–11 个月不属于原六个月课程。」

**PR1–PR3:** full MDX + examples for **10.1–10.7** (PR1: 10.1–10.3, PR2: 10.4–10.5, PR3: 10.6–10.7). `multi-view-extrinsics`, `intervention-logging` and `edge-deploy-checklist` were Month 9 electives and are now formal lessons. Month 10 does not replace the 8.7 capstone and does not open a new track.

Constraints: no new hardware; not required this month: Isaac, an F/T sensor or a real robot. Runnable toys are stdlib CPU with fixed seeds, outputs pinned in `examples/month-10/expected/` and checked by `examples/month-10/check.sh` (7 of 7). GPU training, weight downloads, real SO-101 runs and LeRobot CLI commands are marked「本页未运行」; commands carry「以当期文档为准」against LeRobot v0.6.x.

| # | slug | minutes | runnable | verified against |
|---|------|---------|----------|------------------|
| 1 | `flow-matching-policies` | 240 | `flow_match_toy.py` | Flow Matching / π0 / rectified flow / SmolVLA papers; LeRobot π0.5 docs |
| 2 | `real-time-chunking` | 180 | `rtc_blend_toy.py` | RTC paper; LeRobot RTC + async docs |
| 3 | `edge-deploy-checklist` | 180 | `latency_budget.py`, `int8_quant_toy.py` | ONNX Runtime quantization; LeRobot hardware / accelerator docs |
| 4 | `multi-view-extrinsics` | 240 | `extrinsics_chain_toy.py` | OpenCV calibrateRobotWorldHandEye / ArUco / solvePnP docs |
| 5 | `intervention-logging` | 180 | `intervention_log_toy.py` | LeRobot HIL data collection + v0.6.0 blog; DAgger / HG-DAgger / RaC |
| 6 | `real-world-rl` | 240 | `rlpd_chain_toy.py` | RLPD arXiv 2302.02948; HIL-SERL arXiv 2410.21845; LeRobot HIL-SERL docs |
| 7 | `vla-rl-finetune` | 240 | `advantage_filter_toy.py` (optional) | SimpleVLA-RL 2509.09674; OpenVLA-OFT 2502.19645; π*0.6 blog; ResiP 2407.16677; Policy Decorator 2412.13630; LeRobot SARM docs |

Total 1 500 minutes. Pointers: 8.3 → 10.2 (async seam), 8.7 capstone → Month 10 (optional, not a replacement), M8 topics → "HIL-SERL 见 10.6".

Widgets deferred. No prices anywhere.

Verification: `examples/month-8/check.sh`, `examples/month-9/check.sh`, `examples/month-10/check.sh`, check_quotes, check_diagrams, check_widgets, lint, check_wokwi, tsc, CI build.

Batch-after-obs PR3 (G7, +150): 10.3 `edge-deploy-checklist` 180→330 — `vla_edge_budget_toy.py`: weights-only memory (params × bytes; activations / KV cache / vision buffers excluded and labelled) for SmolVLA 0.45B, π0-class 3.3B, OpenVLA-class 7B (counts from the papers); chunk / Hz / sync idle linked to 6.3's g ≥ (E[ℓ_S] / Δt) / n. No device measurements; Jetson / Pi 本页未运行. Month 10 **7 lessons / 1 650 min**; site **71 lessons / 18 570 min**.
