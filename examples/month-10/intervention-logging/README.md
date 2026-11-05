# 10.5 intervention-logging

- `intervention_log_toy.py` — seeded human-in-the-loop log with an `intervention` column: segments, intervention rate, RaC-style recovery / correction split, what "end after intervention" keeps, and a toy merge that refuses mismatched features until `intervention` is removed.

```bash
python3 intervention_log_toy.py    # ../expected/intervention_log_toy.txt
```

Not run here / 本页未运行 (needs an SO-101 leader + follower and a trained policy; LeRobot v0.6.x, options may change): follow the LeRobot "Human-In-the-Loop Data Collection" page for `lerobot-rollout --strategy.type=dagger` and `lerobot-edit-dataset --operation.type remove_feature` / `merge`. The merge error text in the toy is the toy's own, not LeRobot's.
