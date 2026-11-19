# Month 9 examples

CPU-reproducible scripts for Month 9 (site supplement). Run `./check.sh` from this folder.

| lesson | script | this batch | needs |
|--------|--------|------------|-------|
| mtc-long-horizon | `mtc-long-horizon/stage_graph_toy.py` | **full** | stdlib |
| moveit-servo | `moveit-servo/servo_loop_sim.py` | **full** | stdlib |
| effort-admittance | `effort-admittance/load_contact_sim.py`, `admittance_1d.py` | **full** | stdlib |
| llm-skill-planning | `llm-skill-planning/saycan_score_toy.py`, `llm-skill-planning/chatvla2_reasoning_following_toy.py` | **full** (fake LLM only) | stdlib |
| failure-recovery | `failure-recovery/recovery_bt_toy.py` + `failure_table.md` | **full** | stdlib |
| nav-arm-compose | `nav-arm-compose/nav_pick_bt.py` | **full** | stdlib |
| multi-skill-demo | `multi-skill-demo/demo_gate.py` (`--all` for CI) | **full** | stdlib |
| visual-servoing | `visual-servoing/tag_error_jog.py` | **Track B** | stdlib |
| world-models-overview | `world-models-overview/latent_predict_toy.py`, `world-models-overview/neural_traj_idm_toy.py` | **Track B** | stdlib |

9 lessons complete / 9 课已齐 (9.1–9.9 Track B). Absolute paths in lessons: `~/Hardware-learning/examples/month-9/...`.

## Batch-5 PR2 / 第5批 PR2

`nav-arm-compose/multi_robot_corridor_toy.py`: standard-library synthetic model; all expected output in `expected/multi_robot_corridor_toy.txt`, checked by `check.sh`. No new dependency or hardware result. / 标准库合成模型，输出由 `check.sh` 对照；无新增依赖，不是硬件结果。

## Batch-5 PR3

`mtc_stage_memory_toy.py`: same eight requests, full/cached/bounded search, stale-prefix failures, charged revalidation and global fallback; node-expansion counts only, not timing. / 共享八请求，完整 / 缓存 / 有界搜索，陈旧失败、重验证与回退记账，只计展开不测时间。

## Batch-20 PR3 / 第20批 PR3

`world-models-overview/internvla_a1_mot_foresight_toy.py`: standard-library synthetic 1-D conveyor scenes (action only vs understanding + foresight + action vs corrupted foresight), no GPU, no weights; expected output in `expected/internvla_a1_mot_foresight_toy.txt`, included in `check.sh`. InternVLA-A1 numbers 以论文为准; real robot 本页未运行. / 标准库合成的一维传送带场景（只做动作、先前瞻再动作、前瞻出错），不是 GPU 训练或真机结果，输出由 `check.sh` 核对。

## ChatVLA-2 reasoning-following (`chatvla2_reasoning_following_toy.py`)

```bash
python3 examples/month-9/llm-skill-planning/chatvla2_reasoning_following_toy.py
```

Stdlib only. A ChatVLA-2-style stand-in on shared board-and-card scenes: a naive overwrite of the reasoner vs a two-stage freeze-reasoner follow vs stage-2-only against an un-co-trained reasoner; pick accuracy and reason-then-pick over five seeds with common random numbers. Paper math-matching scores 以论文为准; GPU / whiteboard 本页未运行.
只用标准库。共享棋盘与数字卡片上的 ChatVLA-2 风格替身：比较覆盖推理器的稠密微调、两阶段冻结推理器再跟随、以及只做第二阶段对着未经共训练的推理器；5 个种子、共用随机数，报告选牌准确率和推理再跟随。论文数学配对分数以论文为准；GPU / 白板本页未运行。
