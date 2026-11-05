# 10.2 real-time-chunking

`rtc_blend_toy.py` — naive chunk switch vs the RTC soft mask (Eq. 5 of arXiv 2506.07339) applied as a **linear blend**. Real RTC uses the mask inside a guidance term during denoising; this toy is a simplified linear stand-in.

```bash
python3 rtc_blend_toy.py   # compare with ../expected/rtc_blend_toy.txt
```

Optional, not run here / 本页未运行 (needs a GPU and a robot or dataset; follow the LeRobot v0.6.x RTC docs, flags may change):

```bash
lerobot-rollout --strategy.type=base --policy.path=<your/policy> \
  --inference.type=rtc --inference.rtc.execution_horizon=10 \
  --inference.rtc.max_guidance_weight=10.0 ...
```
