# Month 10 plan: Modern policy heads, deployment & real-world improvement

Current / 当前 Batch-7 PR3: M10 **2280 min**; older sections retain historical totals.

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Lessons open with "This lesson is a site supplement — Months 7–11 are not part of the original six-month course." / 「本课是本站补充内容——第 7–11 个月不属于原六个月课程。」

**PR1–PR3:** full MDX + examples for **10.1–10.7** (PR1: 10.1–10.3, PR2: 10.4–10.5, PR3: 10.6–10.7). `multi-view-extrinsics`, `intervention-logging` and `edge-deploy-checklist` were Month 9 electives and are now formal lessons. Month 10 does not replace the 8.7 capstone and does not open a new track.

Constraints: no new hardware; not required this month: Isaac, an F/T sensor or a real robot. Runnable toys are stdlib CPU with fixed seeds, outputs pinned in `examples/month-10/expected/` and checked by `examples/month-10/check.sh` (7 of 7). GPU training, weight downloads, real SO-101 runs and LeRobot CLI commands are marked「本页未运行」; commands carry「以当期文档为准」against LeRobot v0.6.x.

| # | slug | minutes | runnable | verified against |
|---|------|---------|----------|------------------|
| 1 | `flow-matching-policies` | 450 | `flow_match_toy.py`, `policy_distill_onestep_toy.py` | Flow Matching / π0 / rectified flow / SmolVLA papers; LeRobot π0.5 docs |
| 2 | `real-time-chunking` | 180 | `rtc_blend_toy.py` | RTC paper; LeRobot RTC + async docs |
| 3 | `edge-deploy-checklist` | 330 | `latency_budget.py`, `int8_quant_toy.py`, `vla_edge_budget_toy.py` | ONNX Runtime quantization; LeRobot hardware / accelerator docs |
| 4 | `multi-view-extrinsics` | 240 | `extrinsics_chain_toy.py` | OpenCV calibrateRobotWorldHandEye / ArUco / solvePnP docs |
| 5 | `intervention-logging` | 180 | `intervention_log_toy.py` | LeRobot HIL data collection + v0.6.0 blog; DAgger / HG-DAgger / RaC |
| 6 | `real-world-rl` | 240 | `rlpd_chain_toy.py` | RLPD arXiv 2302.02948; HIL-SERL arXiv 2410.21845; LeRobot HIL-SERL docs |
| 7 | `vla-rl-finetune` | 450 | `advantage_filter_toy.py` (optional), `cal_conrft_offline_toy.py` | SimpleVLA-RL 2509.09674; OpenVLA-OFT 2502.19645; π*0.6 blog; ResiP 2407.16677; Policy Decorator 2412.13630; LeRobot SARM docs; ConRFT2502.05450 / Cal-QL2303.05479 (opened) |

Current total **2 070 minutes** (Batch-6 PR3); historical total1 650 after G7. Pointers: 8.3 → 10.2 (async seam), 8.7 capstone → Month 10 (optional, not a replacement), M8 topics → "HIL-SERL 见 10.6".

Widgets deferred. No prices anywhere.

Verification: `examples/month-8/check.sh`, `examples/month-9/check.sh`, `examples/month-10/check.sh`, check_quotes, check_diagrams, check_widgets, lint, check_wokwi, tsc, CI build.

Batch-after-obs PR3 (G7, +150): 10.3 `edge-deploy-checklist` 180→330 — `vla_edge_budget_toy.py`: weights-only memory (params × bytes; activations / KV cache / vision buffers excluded and labelled) for SmolVLA 0.45B, π0-class 3.3B, OpenVLA-class 7B (counts from the papers); chunk / Hz / sync idle linked to 6.3's g ≥ (E[ℓ_S] / Δt) / n. No device measurements; Jetson / Pi 本页未运行. Month 10 **7 lessons / 1 650 min**; site **71 lessons / 18 570 min**.

## Batch-5 PR3 (+210 here)

10.7:240→450; M10 **1650→1860**,7 lessons. Site **20700→21090** with M9+180 (2730). Same-data/equal-update offline BC/CQL/Cal-QL, MC reference inside conservative push-down, five seeds and restricted/tabular representation control. Online dip, consistency head and robot/GPU reading only / 本页未运行; paper以论文为准. Existing advantage filter and10.6 unchanged.

## Batch-6 PR3 / 本月 H1 (+210)

10.1:240→450; M10 **1860→2070**, still 7 lessons. Site **21960→22350** with M8 **2850→3030** (+180). Count only PR3:210+180=390. Shared64 demos / disjoint64 eval starts, 5 seeds, action MSE / actual NFE / independent nonlinear-plant success. Eight-call analytic teacher, one-call full/underfit regressors; unequal fit updates disclosed, no convergence claim. OneDP reverse KL and real Consistency Policy reading only; GPU 本页未运行, figures 以论文为准. Existing Consistency Policy paragraph and expected outputs retained. Sources: batch-6-pr3-sources.md.

## Batch-7 PR3 / 本月 H5 (+210)

10.6 real-world-rl240→450. M6 **1350→1560**, M10 **2070→2280**. This PR only:23190+210+210=**23610**,71 lessons; no arithmetic mismatch, no earlier PR minutes counted twice.

Allocation:45+45+45+45+30=210 min (model/loss or information declaration / implementation / shared-seed experiment / limits and reading / exercises).
Three core arms DPO / RM+RL / preferred-only BC plus BC-all/success-filter to retain the proposal literacy baselines. Success-filter's extra binary training supervision is explicit. Same64 pairs,240 total gradient slots (RM120 reward +120 policy), disjoint256 eval contexts, five seeds and25 % preference flips; no truth reward in optimization or evaluation-label tuning. Existing HIL-SERL chain and SARM pointers preserved.
New symmetric en/zh code/stdout/exercises before final Summary, stdlib expected+harness, independent regression locks, opened-source audit in batch-7-pr3-sources.md. No workflows changed.
