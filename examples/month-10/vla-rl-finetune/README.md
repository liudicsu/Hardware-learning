# 10.7 vla-rl-finetune

- `advantage_filter_toy.py` — the 10.6 lock chain again, but offline: a mediocre behaviour policy logs 40 episodes, a value V(s) ("minus steps to finish") is averaged from the log, and three counted policies are compared: plain BC, success-only BC, and BC on steps with advantage A > 0. A second log with no successes shows the filter has nothing to rank.

```bash
python3 advantage_filter_toy.py    # ../expected/advantage_filter_toy.txt
```

Not run here / 本页未运行 (GPU clusters, VLA weights, real robots): SimpleVLA-RL (veRL + GRPO), π*0.6 / RECAP, ResiP, Policy Decorator, LeRobot SARM + RA-BC (`python -m lerobot.rewards.sarm.compute_rabc_weights`). Reading map only; 以当期文档为准.

## Batch-5 offline critic/actor experiment

`cal_conrft_offline_toy.py`: BC-only / CQL+BC / Cal-QL+BC on shared48-demo batches and1000 actor updates; critic extra work disclosed. MC reference masks only conservative push-down, not Bellman targets or final outputs. Five held-out evaluation seeds' success spread and raw calibration gaps retained. The restricted critic is a selected diagnostic, not a leaderboard; `--tabular` is a same-data representation control.

```bash
python3 cal_conrft_offline_toy.py
python3 cal_conrft_offline_toy.py --tabular
```

同数据等更新，保留负面结果与欠校准；一致性头、在线阶段及真机本页未运行。在线下跌缓解只读原文，数字以论文为准。
