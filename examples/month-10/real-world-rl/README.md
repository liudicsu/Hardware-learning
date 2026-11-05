# 10.6 real-world-rl

- `rlpd_chain_toy.py` — a 10-state "combination lock" chain (wrong action → back to the start, reward only at the goal). Tabular Q-learning over 20 seeds: online replay only, 3 demos dumped into the same buffer, and 3 demos in their own buffer with RLPD-style 50/50 symmetric sampling. Prints how many seeds ever reach the goal, the first successful episode, resets per run, greedy success at the end, and the demo share of the last episode's samples.

```bash
python3 rlpd_chain_toy.py    # ../expected/rlpd_chain_toy.txt
```

Not run here / 本页未运行 (needs an NVIDIA GPU, a real arm with a gamepad / leader arm, and a URDF; LeRobot docs, options may change): the LeRobot HIL-SERL guide (`lerobot-find-joint-limits`, `python -m lerobot.rl.gym_manipulator`, reward-classifier training with `lerobot-train`, `python -m lerobot.rl.learner` + `python -m lerobot.rl.actor`). 以当期文档为准.
