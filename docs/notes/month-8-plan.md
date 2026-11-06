# Month 8 plan

Batch 1–2 delivered 8.1–8.7 (dataset → capstone). **Track B (promote electives):** append **8.8 `sim-benchmarks`** after capstone — does **not** replace 8.7.

| slug | minutes | CPU toy | notes |
|------|---------|---------|-------|
| dataset-engineering | 180 | `dataset_audit.py` | batch 1 |
| vla-finetune | 420 | `compute_budget.py`, `rpd_teacher_rl_toy.py` | batch 2 |
| async-deployment | 300 | `chunk_latency_sim.py`, `stream_sync_eval_toy.py` | batch 1 + deepen PR3: arrival-causal alignment |
| ros2-hardware-interface | 600 | `servo_bus_sim.py`, `lifecycle_sm_toy.py`, `can_fault_confinement_toy.py` (+ `so101_hw/` skeleton 本页未运行) | batch 2 + follow-up PR1 F2: managed-node SM ≠ HardwareComponent |
| safety-reliability | 540 | `watchdog_sim.py`, `actuator_fault_monitor_toy.py` | batch 1 + follow-up PR2 F3: device/bus fault latch + operator ack |
| robot-devops | 360 | `bag_stats.py`, `bag_qos_accept_toy.py` | batch 1 + follow-up PR1 F1: bag/QoS acceptance |
| capstone | 300 | `capstone_gate.py --demo` | batch 2; LIBERO section → pointer to 8.8 |
| **sim-benchmarks** | **330** | **`suite_score_table.py`**, **`imagine_rank_toy.py`** | **Track B 8.8 + G6**; GPU `lerobot-eval` 本页未运行 |

Site “~1500 min” habit is intentionally broken by Track B (+180). Still labelled 本站补充. Remaining electives on month page: HIL-SERL / Isaac Lab / legged playground (not formal lessons).

Deepen PR3 (+120): 8 lessons / **1 800 min**. Three synthetic streams share packets/noise; correct known clock offsets and interpolate only arrived brackets at now−0.14 s. RMSE and catch proxy are scored at a common lagged query, not live success; no RTC mask re-teach. Site was then 71 lessons / 16 050 min.

Follow-up PR1 (+360): F1 `robot-devops` 180→360 (bag/QoS acceptance; Jazzy README QoS keys; no binary MCAP in CI); F2 `ros2-hardware-interface` 240→420 (managed-node lifecycle toy + HardwareComponent contrast; illegal activate recoverable). **8 lessons / 2 160 min**. Site: 71 lessons / **16 410 min**.

Follow-up PR2 (+180 here): F3 `safety-reliability` 180→360 (command-path watchdog ≠ device/bus fault; fault latches safe, a cleared bit never auto re-enables, re-enable needs operator_ack + bit clear + frames recovered; CiA 402 standard bits 0–7, 9–11 from the public ros2_canopen StatusWord table, bits 8 / 12–13 / 14–15 masked and not asserted; bus-off / soft reset ≠ e-stop; diagnostic OK/WARN/ERROR + Example 17 pointer). **8 lessons / 2 340 min**. Site with F4: 71 lessons / **16 800 min**.

Follow-up PR3 (F5–F7 on M5/M6, +510 site): does not change Month 8 minutes (**2 340**). Site after PR3: 71 lessons / **17 310 min**.

Batch-after-obs PR3 (G6, +150): 8.8 `sim-benchmarks` 180→330 — Ctrl-World (arXiv 2510.10125) read per the paper; `imagine_rank_toy.py` ranks five synthetic policies on shared tasks / ICs in an oracle env vs biased world models with Kendall τ (uniform_drop preserves order under this seed; a policy-independent bias of this kind often preserves order; tight_tol / no_slide / no_retry flip pairs). **8 lessons / 2 490 min**. Site with G5/G7: 71 lessons / **18 570 min**.

## Batch-4 PR2 (locked H1/H6)

H6 8.5 360→540 (+180): user-supplied S/F/P base graph → required PLr only; missing fields insufficient_data; achieved PL requires category/MTTFd/DCavg/CCF and is out of scope. ISO 13849-1:2023 Edition 4 metadata verified; 10218:2025 summaries explicitly secondary; toy ≠ certification. Month 8 **2 670 min** (2 490 + 180).

Site: **71 lessons / 19 440 min** (19 050 + 390). See `batch-4-pr2-sources.md` for source checks and the M7 arithmetic correction.

## Batch-6 PR2 / 本月 H2 (+180)

Latest task overrides proposal §9's old host/threshold: **8.4 ros2-hardware-interface 420→600**, not 8.5; **TEC>255 (≥256)**, not 255. M8 **2670→2850**, eight lessons. / 最新任务明确宿主与正确边界；不改 8.5 既有锁存或 PLr 内容。

Opened Bosch CAN 2.0 Part A pp.24–26 and NXP BCANPSV2.0 Rev.3 §5.2: ordinary TEC +8 / success −1; REC +1/−1 plus qualified +8; passive >127; bus-off TEC>255; 128×11 recessive recovery. Deterministic shared 43 slots, RX exceptions, 255/256 and 1407/1408 boundaries; controller policy simplified. Not CiA402/EtherCAT/e-stop; real CAN/SocketCAN 本页未运行. / 原始规则、成功回退、被动与离线、例外和恢复完整序列均回归锁定。

Allocation 45+45+30+45+15=180 min. With M9 +210 separately: **21570+180+210=21960**, **M8=2850**, **M9=2940**, **71 lessons**; M1/M2 remain 1020/1980, no PR3 minutes. / 仅计本 PR，外月宿主不列在本月标题下。

## Batch-6 PR3 / 本月 H7 (+180)

8.2:240→420; M8 **2850→3030**, still 8 lessons. Site **21960→22350** with M10 **1860→2070** (+210). Count only PR3:180+210=390. Deliberately suboptimal teacher; BC-only / scratch RL / teacher-MSE RL all use7680 env ticks/80 updates, with paired768/8 early checkpoints. Five seeds, shared random tape and separate256-episode evaluation; mean±population sd and range retain early BC wins. Discrete REINFORCE surrogate, not PPO, Cal-ConRFT or HIL-SERL. Real GPU/VLA/ManiSkill 本页未运行; figures 以论文为准. Source audit: batch-6-pr3-sources.md.
