# 11.3 tactile-sensing

`tactile_marker_toy.py` — synthetic marker-grid deformation → contact estimate (stdlib).
DIGIT / GelSight Mini / AnySkin hardware is optional reading; real capture is **not run here**.
No purchase required.

## In-place deepen toy

Shared-noise synthetic axis/sign, rest debias, independent gain recalibration and low-load first-contact data gate. Synthetic skin coordinates + dimensionless load, NOT measured Newtons. No hardware purchase; real capture/calibration not run here (本页未运行). Policy integration stays in 11.7.

```bash
python3 examples/month-11/tactile-sensing/tactile_debias_recal_toy.py
bash examples/month-11/check.sh
```

Expected output: `examples/month-11/expected/tactile_debias_recal_toy.txt` (captured from real stdout).
