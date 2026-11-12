# Month 11 examples

CPU / standard-library toys for Month 11 (actuator hardware, tactile contact & cross-embodiment collection).

All 7 of 7 lessons: 11.1 power-battery-emc, 11.2 foc-actuator-lab, 11.3 tactile-sensing,
11.4 umi-style-collection, 11.5 cross-embodiment-datasets, 11.6 humanoid-wbc-overview,
11.7 contact-rich-policies.

```bash
bash examples/month-11/check.sh
UPDATE=1 bash examples/month-11/check.sh   # regenerate expected/
```

Set `M11_PYTHON` to override the interpreter (default `python3`).

11.3 also includes `tactile_debias_recal_toy.py` (shared-noise calibration, dimensionless load); 11.5 includes `oxe_auge_score_toy.py` (synthetic partial scores vs binary completion). Both are included in check.sh.

- `power-battery-emc/soc_coulomb_thermal_toy.py` — coulomb SoC drift + thermal derate (batch-4).

Batch-4 PR3: `umi-style-collection/teleop_rtt_budget_toy.py` (stdlib CPU); `check.sh` compares `expected/teleop_rtt_budget_toy.txt`. Unilateral positions, control/video RTT, explicit display+reaction model; one_way_only_estimate is accounting, not physical performance.

## power-battery-emc/ — Inrush current and an NTC limiter / 浪涌电流与 NTC 限流

`power-battery-emc/ntc_inrush_limiter_toy.py`: standard-library synthetic capacitor-charging circuit with a one-node NTC thermal model (no limiter vs NTC vs fixed resistor vs relay bypass; cold start, hot restart, heavy load) on shared capacitor, source, tolerance and ambient draws; no hardware; expected output in `expected/ntc_inrush_limiter_toy.txt`, included in `check.sh`. Real PSU / NTC disc / fuse 本页未运行. / 标准库合成的电容充电电路与单节点 NTC 热模型（无限流、NTC、固定电阻、旁路继电器；冷启动、热重启、重载），不是实测，输出由 `check.sh` 核对。
