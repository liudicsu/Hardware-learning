# Month 8 plan

Batch 1–2 delivered 8.1–8.7 (dataset → capstone). **Track B (promote electives):** append **8.8 `sim-benchmarks`** after capstone — does **not** replace 8.7.

| slug | minutes | CPU toy | notes |
|------|---------|---------|-------|
| dataset-engineering | 180 | `dataset_audit.py` | batch 1 |
| vla-finetune | 240 | `compute_budget.py` | batch 2 |
| async-deployment | 300 | `chunk_latency_sim.py`, `stream_sync_eval_toy.py` | batch 1 + deepen PR3: arrival-causal alignment |
| ros2-hardware-interface | 420 | `servo_bus_sim.py`, `lifecycle_sm_toy.py` (+ `so101_hw/` skeleton 本页未运行) | batch 2 + follow-up PR1 F2: managed-node SM ≠ HardwareComponent |
| safety-reliability | 360 | `watchdog_sim.py`, `actuator_fault_monitor_toy.py` | batch 1 + follow-up PR2 F3: device/bus fault latch + operator ack |
| robot-devops | 360 | `bag_stats.py`, `bag_qos_accept_toy.py` | batch 1 + follow-up PR1 F1: bag/QoS acceptance |
| capstone | 300 | `capstone_gate.py --demo` | batch 2; LIBERO section → pointer to 8.8 |
| **sim-benchmarks** | **180** | **`suite_score_table.py`** | **Track B 8.8**; GPU `lerobot-eval` 本页未运行 |

Site “~1500 min” habit is intentionally broken by Track B (+180). Still labelled 本站补充. Remaining electives on month page: HIL-SERL / Isaac Lab / legged playground (not formal lessons).

Deepen PR3 (+120): 8 lessons / **1 800 min**. Three synthetic streams share packets/noise; correct known clock offsets and interpolate only arrived brackets at now−0.14 s. RMSE and catch proxy are scored at a common lagged query, not live success; no RTC mask re-teach. Site was then 71 lessons / 16 050 min.

Follow-up PR1 (+360): F1 `robot-devops` 180→360 (bag/QoS acceptance; Jazzy README QoS keys; no binary MCAP in CI); F2 `ros2-hardware-interface` 240→420 (managed-node lifecycle toy + HardwareComponent contrast; illegal activate recoverable). **8 lessons / 2 160 min**. Site: 71 lessons / **16 410 min**.

Follow-up PR2 (+180 here): F3 `safety-reliability` 180→360 (command-path watchdog ≠ device/bus fault; fault latches safe, a cleared bit never auto re-enables, re-enable needs operator_ack + bit clear + frames recovered; CiA 402 standard bits 0–7, 9–11 from the public ros2_canopen StatusWord table, bits 8 / 12–13 / 14–15 masked and not asserted; bus-off / soft reset ≠ e-stop; diagnostic OK/WARN/ERROR + Example 17 pointer). **8 lessons / 2 340 min**. Site with F4: 71 lessons / **16 800 min**.

Follow-up PR3 (F5–F7 on M5/M6, +510 site): does not change Month 8 minutes (**2 340**). Site after PR3: 71 lessons / **17 310 min**.

Batch-after-obs PR3 (G6, +150): 8.8 `sim-benchmarks` 180→330 — Ctrl-World (arXiv 2510.10125) read per the paper; `imagine_rank_toy.py` ranks five synthetic policies on shared tasks / ICs in an oracle env vs biased world models with Kendall τ (uniform_drop keeps the order, tight_tol / no_slide / no_retry flip pairs). **8 lessons / 2 490 min**. Site with G5/G7: 71 lessons / **18 570 min**.
