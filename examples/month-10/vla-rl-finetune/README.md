# 10.7 vla-rl-finetune

- `advantage_filter_toy.py` — the 10.6 lock chain again, but offline: a mediocre behaviour policy logs 40 episodes, a value V(s) ("minus steps to finish") is averaged from the log, and three counted policies are compared: plain BC, success-only BC, and BC on steps with advantage A > 0. A second log with no successes shows the filter has nothing to rank.

```bash
python3 advantage_filter_toy.py    # ../expected/advantage_filter_toy.txt
```

Not run here / 本页未运行 (GPU clusters, VLA weights, real robots): SimpleVLA-RL (veRL + GRPO), π*0.6 / RECAP, ResiP, Policy Decorator, LeRobot SARM + RA-BC (`python -m lerobot.rewards.sarm.compute_rabc_weights`). Reading map only; 以当期文档为准.
