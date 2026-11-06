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
