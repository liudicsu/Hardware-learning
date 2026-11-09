# 10.5 intervention-logging

- `intervention_log_toy.py` — seeded human-in-the-loop log with an `intervention` column: segments, intervention rate, RaC-style recovery / correction split, what "end after intervention" keeps, and a toy merge that refuses mismatched features until `intervention` is removed. The rollout follows the LeRobot DAgger flow (control goes back to the policy after each correction); it does not simulate RaC's "end the episode after an intervention" rule, it only counts what that rule would keep. / 玩具模拟 LeRobot DAgger 流程（纠正后交回策略），不模拟 RaC「介入后结束本回合」。

```bash
python3 intervention_log_toy.py    # ../expected/intervention_log_toy.txt
```

Not run here / 本页未运行 (needs an SO-101 leader + follower and a trained policy; LeRobot v0.6.x, options may change): follow the LeRobot "Human-In-the-Loop Data Collection" page for `lerobot-rollout --strategy.type=dagger` and `lerobot-edit-dataset --operation.type remove_feature` / `merge`. The merge error text in the toy is the toy's own, not LeRobot's.

- `map_vla_memory_prompt_toy.py` — standard-library MAP-VLA stand-in: a frozen linear "VLA", stage soft prompts tuned on logged demos / corrections, sliding-window trajectory retrieval and prompt ensembling, against a memoryless base and a wrong-stage memory on shared episodes (5 seeds). Output in `../expected/map_vla_memory_prompt_toy.txt`, checked by `../check.sh`. π0 weights / LIBERO / real robot 本页未运行; paper numbers 以论文为准. / 标准库 MAP-VLA 替身：冻结线性「VLA」、在记录的演示/纠正上调的阶段 soft prompt、滑窗轨迹检索与 prompt 集成，与无记忆基线和错阶段记忆在共享回合上比较（5 个种子）；不是 π0。
