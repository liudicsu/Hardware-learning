# 11.5 cross-embodiment-datasets

`oxe_imbalance_toy.py` — synthetic embodiment counts → top-4 share + clipped inverse-frequency weights (stdlib).
Counts are **synthetic**, not real OXE cardinality. Paper constants (1M+, 22, >85 %, 4.4M, 24–45 %) are printed separately.
Downloading OXE / training is not run on this page.

## In-place deepen toy

Synthetic 4×10 A.5-style milestone scores: mean/sample-SE vs binary full placement on identical trials. Stage constants document mask fusion/inpaint/base tuning/replay; no GPU pipeline implemented. 24–45 % paper lift denominator is uncertain, not assumed percentage points or relative gain. No OXE download/training run here (本页未运行), no real dataset cardinality in CI.

```bash
python3 examples/month-11/cross-embodiment-datasets/oxe_auge_score_toy.py
bash examples/month-11/check.sh
```

Expected output: `examples/month-11/expected/oxe_auge_score_toy.txt` (captured from real stdout).
