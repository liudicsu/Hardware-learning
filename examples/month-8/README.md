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

`dataset-engineering/pi05_heterogeneous_cotrain_toy.py`: standard-library linear / lookup stand-in for heterogeneous co-training (target-robot features only, a declared target-plus-web-subtask-other-robot mixture, and a mixture with no target-robot actions) on shared scenes / instructions / eval; paper first-phase non-target-data percentage and house-clean figures 以论文为准 and are not toy outputs; expected output in `expected/pi05_heterogeneous_cotrain_toy.txt`, included in `check.sh`. GPU / pi0.5 weights / real homes 本页未运行. / 标准库线性查找替身，在共享场景、指令和评估下比较仅目标机器人特征、声明的共训练混合、以及不含目标机器人动作的混合；论文第一阶段非目标数据比例与住宅清洁数字以论文为准，不是玩具输出；输出由 `check.sh` 核对。
