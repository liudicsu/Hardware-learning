# Month 8 plan

Batch 1–2 delivered 8.1–8.7 (dataset → capstone). **Track B (promote electives):** append **8.8 `sim-benchmarks`** after capstone — does **not** replace 8.7.

| slug | minutes | CPU toy | notes |
|------|---------|---------|-------|
| dataset-engineering | 180 | `dataset_audit.py` | batch 1 |
| vla-finetune | 240 | `compute_budget.py` | batch 2 |
| async-deployment | 300 | `chunk_latency_sim.py`, `stream_sync_eval_toy.py` | batch 1 + deepen PR3: arrival-causal alignment |
| ros2-hardware-interface | 240 | `servo_bus_sim.py` (+ `so101_hw/` skeleton 本页未运行) | batch 2 |
| safety-reliability | 180 | `watchdog_sim.py` | batch 1 |
| robot-devops | 180 | `bag_stats.py` | batch 1 |
| capstone | 300 | `capstone_gate.py --demo` | batch 2; LIBERO section → pointer to 8.8 |
| **sim-benchmarks** | **180** | **`suite_score_table.py`** | **Track B 8.8**; GPU `lerobot-eval` 本页未运行 |

Site “~1500 min” habit is intentionally broken by Track B (+180). Still labelled 本站补充. Remaining electives on month page: HIL-SERL / Isaac Lab / legged playground (not formal lessons).

Deepen PR3 (+120): 8 lessons / **1 800 min**. Three synthetic streams share packets/noise; correct known clock offsets and interpolate only arrived brackets at now−0.14 s. RMSE and catch proxy are scored at a common lagged query, not live success; no RTC mask re-teach. Site: 71 lessons / 16 050 min.
