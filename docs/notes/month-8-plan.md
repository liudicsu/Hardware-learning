# Month 8 plan

Current / 当前：**M8 4710 min**, Batch-33 PR1. Earlier entries below retain their historical totals. After this leftover only, M8 is uniquely heaviest at 4710 (180 above M11=4530). Site typography after this PR is `46 800`. M1=3450 stays lightest.

## Batch-33 PR1 / 本月 H1 (+180)

Base `1257ad6dc71118c2c6b7a7ad7af9a302a05300ff` (batch-31 PR1 #216 squash-merged; site **46620**). PR1 on M8 host: **M8 4530→4710 (+180)**. Host `robot-devops` 360→540. Site **46620→46800** (README typography `46 800`). Still 71 lessons. M11 stays 4530; M1=3450 remains lightest. The 4710 tip is for this leftover only, not a general 4560/4650/4710 relaxation. These load facts are recorded here and in the sources note only, not as a student-facing process lecture.

- **H1 / 8.6 robot-devops: 360→540 (+180).** Official rosbag2 simulation-time clock contract (`rosbag2_sim_time_clock_toy.py`; five seeds; CRN late-`/clock` arrivals; stdlib only). Official bodies re-fetched at writing (live pins recorded in `docs/notes/batch-33-pr1-sources.md`; 以原文为准) at commit `12b5e8ba4eb5665501a16f0d9e050552a1149f56` (Jazzy tip, `ahead_by` 0): README simulation-time definition, `--use-sim-time` wait-for-`/clock` and the 0-then-N “essentially unplayable” jump, the `--use-sim-time` / `--no-discovery` incompatibility, and play `--clock` argparse `const=40` / `default=0` plus session / pause / exclude wiring. Declared toy parameters: `N_DATA=12`, `DATA_PERIOD_MS=50`, `CLOCK_FIRST_MS=150`, `CLOCK_FIRST_ALT_MS=250`, `CLOCK_PERIOD_MS=50`, `N_CLOCK=10`, `SIM_T0_MS=1000`, `clear_frac=0.2000`, `CLOCK_HZ_BARE=40`, `SESSION_ACTIVE_MS=250`, 手算 `1000/40=25` and `250/25=10`. Official first run 2026-11-26 20:04:37 Asia/Shanghai; expected sha256 `3a7d4e1bdc2e9688bb6cc0dfd537646e1fba0357918ea5320156ebb2cbf9ddd5`; later rerun byte-identical; official expected/ not retuned. Official arm: written `9.0000+-0.0000`, dropped `4.2000+-0.4472`, `zero_then_n_jump` `0.0000+-0.0000`. C loses: paired C-A `zero_then_n_jump` `1.0000+-0.0000`, **clear**, 5/5; `jump_from_zero_ms` `1000.0000+-0.0000`, **clear**, 5/5; kept and disclosed. Alternative `clock_first_ms=250` printed, not adopted. Existing `bag_stats.py`, `bag_qos_accept_toy.py` and their expected/ / fixtures / already-taught mcap / bag-stats / bag-QoS wording were not retuned or edited. Live ros2 bag / real simulator / Foxglove / Rerun / hardware clock 本页未运行. / 官方 rosbag2 仿真时间时钟契约，对照等待首条 `/clock` 与先写 0 再写 N 的失败臂，不宣布现场录包或真实仿真器实验。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

Current / 当前：**M8 4530 min**, Batch-28 PR1. Earlier entries below retain their historical totals.

## Batch-28 PR1 / 本月 H1 (+180)

Base `06f937610f42489334ac3652197205e190d0c456` (batch-27 PR3 #209 merged; site **45360**). PR1 on M8 host: **M8 4350→4530 (+180)**. Site **45360→45540** (README typography `45 540`). After this PR, M8 is the new sole heaviest month: **60 min** above M9 / M10 = 4470, **150 min** above M6 = 4380. M11 stays 4350 in this PR. Still 71 lessons.

- **H1 / 8.4 ros2-hardware-interface: 600→780 (+180).** JointLimiter enable-scope and coupled saturation (`joint_saturation_limiter_toy.py`; common random numbers, 5 seeds; limits-disabled passthrough vs a naive independent box clamp vs a labeled JointSaturationLimiter contract stand-in of the opened doxygen / userdoc wording). Official plugin / `ros2_control_node` 本页未运行. Official concept-page *Configuration of Limits* and *Description of the Limiter Algorithms* remain `tba` and are not invented. After this PR M8 is the sole heaviest month as disclosed above, not a dump onto M9 / M10 or an avoided host.

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

Current / 当前：**M8 4350 min**, Batch-25 PR2. Earlier entries below retain their historical totals.

## Batch-25 PR2 / 本月 H4 (+180)

Base `55c7e5033b8600d33584e2ccece0fff29c8e3aab` (batch-25 PR1 #201 merged; site **42660**). PR2 on M8 host: **M8 4170→4350 (+180)**; M7 moves in the same PR on its own plan. Site **42660→43020** (43020=42660+180+180), still 71 lessons.

- **H4 / 8.8 sim-benchmarks: 330→510 (+180).** LIBERO-X hierarchical robustness (`libero_x_robustness_ladder_toy.py`; common random numbers, 5 seeds; shared scenes, slots, instructions and policy stand-in). arXiv 2602.06556 v1 abs / HTML / PDF bodies read (submitted 2026-02-06; 以论文为准): seven authors in abs order Guodong Wang, Chenkai Zhang, Qingjie Liu, Jinjin Zhang, Jiancheng Cai, Junjie Liu, Xinmin Liu; PDF title-page marks (not the garbled HTML) Wang/Zhang equal contribution, Junjie Liu corresponding, Xinmin Liu project leader, affiliations Meituan and Beihang University; Comments “19 pages, 14 figures and 8 tables”, no venue. Paper figures 2,520 / 600 / 100 and the 9.8 % L1→L2 drop in average success rate (Figure 5) 以论文为准 (a drop, not a suite mean, and not the L1-to-L5 decline, not toy outputs). Levels L1–L5 as in the Evaluation Framework. Declared parameters: `P_BASE=0.8000`, `N_EP=40`, `N_SCENES=8`, `N_SLOTS=4`, penalties `0.0200, 0.1200, 0.1800, 0.1600, 0.1400`, `SMALL_FRAC=0.2000`, seeds 0–4. Hand calc (printed): cumulative penalties `0.0200, 0.1400, 0.3200, 0.4800, 0.6200`. Official first run 2026-11-19 22:49:29 Asia/Shanghai; expected sha256 `5d22ca3589545cc2b91bcd3661fad06cca9cc0becd6562ad7a819b03333d76c7`. l1_jitter: B−A L1 success `-0.0150+-0.0224`, **near-tie** (held, kept). cumulative_shift: B−A L3 `-0.3900+-0.1009`, L4 `-0.5000+-0.0530`, L5 `-0.6250+-0.0250`, **clear**, 5/5 (held, kept). leak_misreport: C−B leaked_L5_minus_true_L5 `0.6300+-0.0671`, **clear**, 5/5 (held, kept). Alternative same seeds `HARSH_PENALTY=0.7000` unstructured success `0.0750+-0.0177` (not adopted; too harsh). No code change after the first official run. ≠ five-suite LIBERO table / SimplerEnv / imagination ranking / LIBERO-Plus. GPU `lerobot-eval` / real LIBERO-X 本页未运行. / L1 可接近打平；累积 L3–L5 露出一致下降；把 L1 当成 L5 会误报。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

Current / 当前：**M8 4170 min**, Batch-24 PR2. Earlier entries below retain their historical totals.

## Batch-24 PR2 — π0.5 heterogeneous co-training on dataset-engineering (+180)

Base `e4a8c2236cd5a2e37144408108b8d0f12f23f320` (batch-24 PR1 #197 merged; site **41580**). PR2 on M8 host: **M8 3990→4170 (+180)**; M2 moves in the same PR on its own plan. Site **41580→41940** (41940=41580+180+180), still 71 lessons.

- **H4 / dataset-engineering: 330→510 (+180).** π0.5 heterogeneous co-training, not packed flow-matching-policies (`pi05_heterogeneous_cotrain_toy.py`; common random numbers, 5 seeds; linear / lookup stand-in). arXiv 2504.16054 v1 abs + HTML + PDF bodies read. Authorship follows the abs: Physical Intelligence first, then the 35 named authors in abs order; the PDF places “Physical Intelligence” as an org line above the same 35 names (order matches; disclosed). 97.6 % and house-clean figures 以论文为准, not toy outputs. in_domain: paired B−A success −0.0131±0.0062, **small but consistent**, 5/5 — the pre-declared near-tie **did not hold**, kept, not retuned. ood_new_home: paired B−A 0.1504±0.0199, **clear**, 5/5 (declared co-train win held). C loses on both regimes: C−B −0.3032±0.0038 and −0.1370±0.0121, **clear**, 5/5 (held). Alternatives sig = 0.1200 and B weights 0.5000/0.2000/0.2000/0.1000 printed, not adopted. Choices after seeing results: none. GPU / π0.5 weights / real homes: 本页未运行. / π0.5 异构共训练，预先声明的域内接近打平未成立并保留。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.


## Batch-21 PR3 / 本月 H6 (+180)

Base `122d224c91dfa02e5e7c867354dc246b02d7737e` (batch-21 PR2 #186 merged; site **38700**). PR3 touches M6 and M8: **M8 3810→3990 (+180)**; M6 moves in the same PR on its own plan. Site **38700→39060** (39060=38700+180+180), still 71 lessons.

- **H6 / 8.2 vla-finetune: 840→1020 (+180).** OpenVLA-OFT (arXiv 2502.19645, Moo Jin Kim, Chelsea Finn, Percy Liang checked on the abs page in arXiv order; abs, HTML and PDF v2 body read) as a per-cell lookup stdlib stand-in (`openvla_oft_parallel_l1_toy.py`; common random numbers, 5 seeds; shared demonstrations). Arms A 256-bin tokens (K·D passes) / B parallel continuous L1 (1 pass) / C 10-step diffusion head / D instruction-conditioned L1 (OFT+ / FiLM idea). unimodal: B−A abs_err `-0.0015±1.281e-4`, **clear**, 5/5; B−A passes `-15.0000±0.0000`; C−B success **tie** (declared may near-tie); C−B passes `9.0000±0.0000`; C−B abs_err `-8.507e-5±2.293e-5` small (not pre-declared). bimodal: the declared B loss did **not** hold as a consistent gap — C−B success `0.2000±0.2592` **near-tie**, and B−A success `0.5000±0.3062` is clear in B's favour. language: D−B follow_err `-0.4000±0.0713`, **clear**, 5/5 (declared loss held, kept). k1: B−A passes `-1.0000±0.0000` (held). Alternatives tolerance 0.002 / 0.005, noise 0.01, bimodal 11 demos printed; none replaced the defaults. Code change after the first run: integer-count formatting only, no value changed. ≠ ChatVLA / SimpleVLA-RL. 76.5→97.1 % / 26× / 43× 以论文为准; 7B / LIBERO / ALOHA / GPU 本页未运行. / OpenVLA-OFT 并行解码 + 连续 L1，论文数字以论文为准。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

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
