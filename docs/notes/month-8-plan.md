# Month 8 plan

Current / 当前：**M8 3810 min**, Batch-19 PR3. Earlier entries below retain their historical totals.

## Batch-19 PR3 / 本月 H6 (+210)

Base `61bb8f769f2d87901bfe1d504ffc25b4fe4d947e` (batch-19 PR2 #178 merged; site **36480**). PR3 touches M6 and M8: M6 3450→3660 (+210), **M8 3600→3810 (+210)**. Site **36480→36900**, still 71 lessons.

- **H6 / 8.3 async-deployment: 300→510 (+210).** NORA (arXiv 2504.19854, 8 authors checked on the abs page; PDF body read, HTML fetched), a 3B VLA on Qwen-2.5-VL-3B with FAST+ action tokens: a 7.0 B-parameter stand-in with one 256-bin token per joint per step (A) vs a 3.0 B-parameter stand-in with FAST-style DCT tokens (B, BPE not modelled) vs B through a shuffled codebook (C) (`nora_fastplus_small_vla_toy.py`; common random numbers, 5 seeds, 200 chunks per seed). short_in_dist: paired B−A success_pct **tie: identical on every seed**; paired B−A cost `-399.2110±0.6314`, **clear**, 5/5. long_horizon (SIG_SMALL=0.055 > SIG_LARGE=0.040, declared): paired B−A success_pct `-72.9000±1.7819`, **clear**, 5/5 — the small model **loses**, **kept**; paired B−A cost `-1184.3520±2.1307`. Shuffled codebook: paired C−B success_pct `-100.0000±0.0000` (short), **clear**, 5/5. Alternative GAMMA=20.0 printed on the same seeds (long_horizon paired B−A success_pct@alt `-10.2000±2.1966`, small but consistent, 5/5); no post-hoc retune. ≠ VLA-Adapter / SmolVLA / π0-FAST catalogue. Paper numbers 以论文为准; checkpoint / LIBERO / GPU 本页未运行. / NORA 小模型 + FAST 式词元，论文数字以论文为准。

**Allocation / 安排:** 40+30+60+40+40 = 210 minutes.

**Site accounting / 全站核算:** **36900=36480+420**; **M6=3660**, **M8=3810**, **71 lessons**.

## Batch-17 PR3 — ChatVLA phased alignment + MoE on vla-finetune (+210)

Base `5825c94` (batch-17 PR2 merged as #170; site **34290**). PR3 touches M6 and M8: M6 3240→3450 (+210), **M8 3390→3600 (+210)**. Site **34290→34710**, still 71 lessons.

- **H6 / vla-finetune: 630→**840** (+210).** Phased alignment + MoE vs robot-only SFT vs naive 3:1 joint training. Toy `chatvla_phased_alignment_toy.py`: D=6, M=2 shared-bottleneck linear stand-in, NQ=3 answer classes labelled by the frozen model (baseline 100.0000 %); R=300 robot batches per arm, B stage 2 = last 100 with Q VQA batches, C 3:1 from step 0; 5 seeds, common random numbers; no integration step. conflict: B−A VQA +40.9500±2.0721, clear, 5/5; B−A control tie; C−B VQA −29.6500±3.7442 and control −4.6500±4.1026 (small, consistent). aligned (declared near-tie): did not hold — B−A VQA +3.0500±1.0954, C−B −0.4500±0.3260, small consistent. few_vqa: B−A VQA +27.7000±3.0177. Naive joint never wins a metric here. ≠ DPO / OpenHelix / CoT-VLA / Magma. ChatVLA numbers 以论文为准; GPU / 25-task real robot 本页未运行.

**Allocation / 安排:** 30+30+40+40+40+30 = 210 minutes.

Batch 1–2 delivered 8.1–8.7 (dataset → capstone). **Track B (promote electives):** append **8.8 `sim-benchmarks`** after capstone — does **not** replace 8.7.

| slug | minutes | CPU toy | notes |
|------|---------|---------|-------|
| dataset-engineering | 330 | `dataset_audit.py`, `dataset_crc_integrity_toy.py` | batch1 + Batch-7 PR1 |
| vla-finetune | 630 | `compute_budget.py`, `rpd_teacher_rl_toy.py` | batch 2 |
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

## Batch-7 PR1 / 本月 H7 (+150)

8.1 dataset-engineering180→330; **M8 3030→3180**, eight lessons. Site **22350→22830**, counting only PR1 +480 with **M2 1980→2310** (+330). Still71 lessons; no arithmetic mismatch. Allocation:30+30+45+30+15=150 min (polynomial/check value/shared corpus/burst limits+authentication/exercises). Deterministic4 payloads; no-check/sum8/CRC32 receive the same corrupted bytes and tags. Existing dataset audit remains. No claim that LeRobot formats store this toy CRC. New sections before Summary, en/zh symmetric. Sources: batch-7-pr1-sources.md.

## Batch-11 PR3 / 本月 H6 (+210)

Base `777543d` (batch-11 PR2 #146 merged; site **27630**). PR3 only: **M8 3180→3390 (+210)** and M6 **2190→2400 (+210**, own host in month-6-plan.md); site **27630→28050**, still 71 lessons; no arithmetic mismatch with proposal §9 or curriculum.ts.

- **H6 / 8.2 vla-finetune: 420→**630** (+210).** Continual VLA finetune + Experience Replay (Huihan Liu et al. arXiv:2603.03818, abs+HTML+PDF opened; LIBERO/NBT 以论文为准). Toy `vla_continual_er_toy.py`: shared task order/steps/noise; A sequential (cap=0), B ER cap=8 replay=2, C ER cap=48 replay=4 with protected prior-task prefix; compute = samples touched; no_shift near-tie / small gap (max |Δavg|=0.0167; ER buys nothing); task_shift ER reduces NBT forget at explicit buffer/compute cost; five seeds, common random numbers. ≠ MemoryVLA / SARM / compute_budget redo. GPU 本页未运行. Sources: batch-11-pr3-sources.md.

**Site accounting / 全站核算:** **28050=27630+420** with M6 +210 on month-6-plan.md; **M8=3390**, **71 lessons**.
