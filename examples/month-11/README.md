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

## umi-style-collection/ — EgoVLA: human-video prior, retargeting and robot post-training / EgoVLA：人类视频先验、重定向与机器人后训练

`umi-style-collection/egovla_human_pretrain_retarget_toy.py`: standard-library synthetic linear action model with a prior-mean ridge fit (robot-only vs human prior plus post-training vs zero-shot retargeting; full data, half data, far-off prior) on shared skill, prior, demonstration and rollout draws; no GPU, no weights; expected output in `expected/egovla_human_pretrain_retarget_toy.txt`, included in `check.sh`. EgoVLA numbers 以论文为准; MANO / Isaac Lab / humanoid 本页未运行. / 标准库合成线性动作模型与带先验均值的岭回归（只用机器人数据、人类先验加后训练、零样本重定向；全量数据、数据减半、先验偏差大），不是 GPU 训练或真机结果，输出由 `check.sh` 核对。

`humanoid-wbc-overview/navila_midlevel_locomotion_toy.py`: standard-library 2-D kinematic / reactive lane stand-in (flat low-level vs mid-level plus visual locomotion vs ignored mid-level / blind heading; open corridor and cluttered / transparent-obstacle regimes) on shared instruction, occupancy and mid-level vocabulary; no Isaac, no real Unitree or Booster; expected output in `expected/navila_midlevel_locomotion_toy.txt`, included in `check.sh`. Paper VLN figures 以论文为准; IsaacLab / real Unitree or Booster / GPU 本页未运行. / 标准库二维运动学 / 反应式车道替身（平坦底层、中层加视觉运动、忽略中层 / 盲目航向；开放走廊与杂乱 / 透明障碍情形），不是 Isaac 或真机结果，输出由 `check.sh` 核对。

`contact-rich-policies/fdvla_force_distill_toy.py`: standard-library linear lookup force-token stand-in (vision-only vs distilled token without the true force channel at test time vs biased / drop-out raw-sensor injection; easy observed and occluded / subtle contact) on shared scenes, features and true latent force; unofficial oracle printed, not a retuning target; no GPU, no F/T hardware; expected output in `expected/fdvla_force_distill_toy.txt`, included in `check.sh`. Paper success rates 以论文为准; GPU / F/T 本页未运行. / 标准库线性查找力 token 替身（仅视觉、蒸馏 token、带偏置 / 丢弃的原始传感器；容易观察与遮挡 / 细微接触），不是权重或真机结果，输出由 `check.sh` 核对。
