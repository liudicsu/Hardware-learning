# 10.2 real-time-chunking

`rtc_blend_toy.py` — naive chunk switch vs the RTC soft mask (Eq. 5 of arXiv 2506.07339) applied as a **linear blend**. Real RTC uses the mask inside a guidance term during denoising; this toy is a simplified linear stand-in.

```bash
python3 rtc_blend_toy.py   # compare with ../expected/rtc_blend_toy.txt
```

`forge_tree_mctd_toy.py` — a synthetic FORGE-Tree-style stand-in (arXiv 2510.21744; stdlib, five seeds,
common random numbers): one-shot decoding vs depth-1 segment search with a frozen prefix vs random segment
picks, five regimes plus a budget sweep, prefix violations counted (0 in every arm).

```bash
python3 forge_tree_mctd_toy.py   # compare with ../expected/forge_tree_mctd_toy.txt
```

OpenVLA / Octo / LIBERO 本页未运行; paper numbers 以论文为准.

Optional, not run here / 本页未运行 (needs a GPU and a robot or dataset; follow the LeRobot v0.6.x RTC docs, flags may change):

```bash
lerobot-rollout --strategy.type=base --policy.path=<your/policy> \
  --inference.type=rtc --inference.rtc.execution_horizon=10 \
  --inference.rtc.max_guidance_weight=10.0 ...
```
