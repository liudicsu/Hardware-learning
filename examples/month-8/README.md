# Month 8 examples

CPU-reproducible scripts for Month 8 (site supplement). Run `./check.sh` from this folder.

| lesson | script | needs |
|--------|--------|-------|
| dataset-engineering | `dataset-engineering/dataset_audit.py` | stdlib (+ synthetic fixture) |
| vla-finetune | `vla-finetune/compute_budget.py` | stdlib |
| async-deployment | `async-deployment/chunk_latency_sim.py` | stdlib |
| ros2-hardware-interface | `ros2-hardware-interface/servo_bus_sim.py` | stdlib (+ `so101_hw/` skeleton, not built here) |
| safety-reliability | `safety-reliability/watchdog_sim.py`, `safety-reliability/actuator_fault_monitor_toy.py` | stdlib |
| robot-devops | `robot-devops/bag_stats.py` | stdlib (+ synthetic MCAP timeline) |
| capstone | `capstone/capstone_gate.py` | stdlib (+ Month 6 `portfolio_check.py`) |
| sim-benchmarks | `sim-benchmarks/suite_score_table.py`, `sim-benchmarks/imagine_rank_toy.py` | stdlib |

8 lessons complete / 8 课已齐 (8.1–8.8 Track B).

Batch-4 PR2: `safety-reliability/safety_pl_assign_toy.py` (stdlib CPU), reproduced by `check.sh`; output in `expected/safety_pl_assign_toy.txt`. Supply `safety-reliability/plr_inputs.json` explicitly; its S/F/P values are illustrative inputs, not selected by the program.
