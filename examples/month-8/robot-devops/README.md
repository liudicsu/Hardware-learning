# robot-devops (8.6)

CPU toys (stdlib; no binary MCAP in CI):

- `bag_stats.py` — rates / gaps on `sample_bag/timeline.json` (Jazzy default `storage_id=mcap`).
- `bag_qos_accept_toy.py` — acceptance gate on `accept_fixtures/` (missing topic `n==0`, gaps, message budget; QoS keys from rosbag2 jazzy README). Live bag / Foxglove / Rerun / wandb = 本页未运行.

```bash
python3 bag_stats.py
python3 bag_qos_accept_toy.py
```
