# 10.1 flow-matching-policies

`flow_match_toy.py` — 1-D flow matching with a closed-form marginal velocity (no network). Euler-integrates noise to a bimodal target with 1/2/3/5/10/50 steps.

```bash
python3 flow_match_toy.py   # compare with ../expected/flow_match_toy.txt
```

Optional, not run here / 本页未运行: read `num_steps` in the LeRobot SmolVLA / π0 policy configs (follow the LeRobot v0.6.x docs; options may change between versions).

## Batch-6 PR3: `policy_distill_onestep_toy.py`

Stdlib CPU literacy surrogate; run `python3 examples/month-10/flow-matching-policies/policy_distill_onestep_toy.py` from repo root, then `bash examples/month-10/check.sh`. Full bilingual model, code and five-seed output are in lesson 10.1. GPU / original policy / robot 本页未运行; paper 以论文为准.

## Batch-13 PR3: `diffusion_forcing_token_noise_toy.py`

Standard-library Diffusion Forcing stand-in: one causal linear denoiser class trained three ways on shared tokens and noise (teacher forcing / independent per-token levels / one shared level), sampled with DDIM, compared in-horizon, past the training horizon and under a best-of-S guidance stand-in (5 seeds). Output in `../expected/diffusion_forcing_token_noise_toy.txt`, checked by `../check.sh`. Video / Franka / GPU 本页未运行; paper numbers 以论文为准. / 标准库 Diffusion Forcing 替身：同一类因果线性去噪器在共享 token 与噪声上按三种噪声模式训练，DDIM 采样，比较训练长度内、超出训练长度与 best-of-S 引导替身；不是视频模型。

## Batch-18 PR3: `knowledge_insulation_flow_toy.py`

Standard-library Knowledge Insulation stand-in: a linear VLM-backbone + flow-matching expert + frozen semantic probe, trained three ways on shared batches and noise (naive expert grads into the backbone / discrete-action CE with stopped expert grads / frozen backbone), five seeds. Output in `../expected/knowledge_insulation_flow_toy.txt`, checked by `../check.sh`. GPU / π0 / LIBERO 本页未运行; paper numbers 以论文为准. Not ChatVLA, not OneDP. / 标准库 Knowledge Insulation 替身：共享批次与噪声上比较朴素专家反传到主干、离散动作 CE + 截断专家梯度、冻结主干；五种子。
