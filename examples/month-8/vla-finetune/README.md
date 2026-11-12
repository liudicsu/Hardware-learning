# vla-finetune

## Batch-6 PR3: `rpd_teacher_rl_toy.py`

Stdlib CPU literacy surrogate; run `python3 examples/month-8/vla-finetune/rpd_teacher_rl_toy.py` from repo root, then `bash examples/month-8/check.sh`. Full bilingual model, code and five-seed output are in lesson 8.2. GPU / original policy / robot 本页未运行; paper 以论文为准.

## chatvla_phased_alignment_toy.py — phased alignment + MoE / 分阶段对齐与混合专家

```bash
python3 examples/month-8/vla-finetune/chatvla_phased_alignment_toy.py
```

Stdlib only. A linear ChatVLA-style stand-in (shared layer, expert projections, action head, answer head): robot-only SFT vs phased alignment with two experts vs naive 3:1 joint training, equal robot batches; control success, VQA accuracy and the forgetting gap against the frozen model over five seeds with common random numbers; no integration step. ChatVLA numbers 以论文为准; GPU / real robot 本页未运行.
只用标准库。ChatVLA 风格的线性替身（共享层、专家投影、动作头、回答头）：比较纯机器人 SFT、带两个专家的分阶段对齐和朴素 3:1 联合训练，机器人批次数相同；5 个种子、共用随机数，报告控制成功率、VQA 准确率和相对冻结模型的遗忘差距；没有积分步。ChatVLA 数字以论文为准；GPU / 真机本页未运行。
