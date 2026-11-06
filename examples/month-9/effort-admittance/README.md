# effort-admittance


`impedance_vs_admittance_toy.py` — stdlib CPU deepen toy; run `python3 impedance_vs_admittance_toy.py` in this directory.
No hardware, wiring or packages required. Expected stdout: `../expected/impedance_vs_admittance_toy.txt`; run `bash examples/month-9/check.sh` from the repo root.
Same mass/damper/spring/wall and noise for effort-out impedance vs motion-out admittance plus an explicit inner tracking servo. Comparative metrics, not a safety ranking; real controller and F/T runs 本页未运行.

## Batch-6 PR2: synthetic F/T calibration / 合成 F/T 标定

`python3 ft_bias_gravity_toy.py`: six sensor-frame orientations ×16 free-space rows, LS mass/COM/force+torque offsets; same twelve held-out poses and contact/noise for raw, one-pose tare, bias-only LS and full gravity compensation. Five seeds with mean/std/min/max, vector force/torque RMSE, contact F1 and free-space false triggers. / 六姿态估计，留出验证；单姿态仅用前16条已披露，不偷看真实参数。

Expected: `../expected/ft_bias_gravity_toy.txt`, compared by `../check.sh`. Frame/polarity/origin and static-model exclusions are in the bilingual lesson. Present Load path unchanged; real F/T hardware 本页未运行, no purchase or certification claim.
