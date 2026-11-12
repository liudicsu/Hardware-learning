# vla-finetune

## Batch-6 PR3: `rpd_teacher_rl_toy.py`

Stdlib CPU literacy surrogate; run `python3 examples/month-8/vla-finetune/rpd_teacher_rl_toy.py` from repo root, then `bash examples/month-8/check.sh`. Full bilingual model, code and five-seed output are in lesson 8.2. GPU / original policy / robot 本页未运行; paper 以论文为准.

## chatvla_phased_alignment_toy.py — phased alignment + MoE / 分阶段对齐与混合专家

```bash
python3 examples/month-8/vla-finetune/chatvla_phased_alignment_toy.py
```

Stdlib only. A linear ChatVLA-style stand-in (shared layer, expert projections, action head, answer head): robot-only SFT vs phased alignment with two experts vs naive 3:1 joint training, equal robot batches; control success, VQA accuracy and the forgetting gap against the frozen model over five seeds with common random numbers; no integration step. ChatVLA numbers 以论文为准; GPU / real robot 本页未运行.
只用标准库。ChatVLA 风格的线性替身（共享层、专家投影、动作头、回答头）：比较纯机器人 SFT、带两个专家的分阶段对齐和朴素 3:1 联合训练，机器人批次数相同；5 个种子、共用随机数，报告控制成功率、VQA 准确率和相对冻结模型的遗忘差距；没有积分步。ChatVLA 数字以论文为准；GPU / 真机本页未运行。

## openvla_oft_parallel_l1_toy.py — parallel decoding + continuous L1 / 并行解码与连续 L1

```bash
python3 examples/month-8/vla-finetune/openvla_oft_parallel_l1_toy.py
```

Stdlib only. An OpenVLA-OFT-style per-cell lookup stand-in (arXiv 2502.19645): 256-bin autoregressive tokens (K·D passes) vs a parallel continuous L1 chunk (1 pass) vs a 10-step kernel-score diffusion head vs an instruction-conditioned L1 lookup (the OFT+ / FiLM idea); unimodal, bimodal, language and K = 1 regimes, five seeds, common random numbers; no integration step. Not ChatVLA, not SimpleVLA-RL. OpenVLA-OFT numbers 以论文为准; 7B model / LIBERO / ALOHA / GPU 本页未运行.
只用标准库。OpenVLA-OFT 风格的按格子查表替身（arXiv 2502.19645）：256 分箱自回归 token（K·D 次前向）vs 并行连续 L1 动作块（1 次）vs 10 步核分数扩散头 vs 按指令查表的 L1（OFT+ / FiLM 思路）；unimodal、bimodal、language 与 K = 1 四种情形，5 个种子、共用随机数；没有积分步。不是 ChatVLA，也不是 SimpleVLA-RL。OpenVLA-OFT 数字以论文为准；7B 模型 / LIBERO / ALOHA / GPU 本页未运行。
