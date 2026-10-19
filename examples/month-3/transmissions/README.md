# Lesson 3: Transmissions & backlash / 第 3 课：传动与回差

**`gear_calc.py`**: planetary-stage tooth counts that actually assemble, cycloidal ratios, torque and speed through a gearbox, what backdriving feels like at different ratios, and how joint backlash becomes tip error.
能真正装配的行星级齿数、摆线减速比、经过减速箱后的扭矩与转速、不同减速比下反向拖动的手感，以及关节回差如何变成末端误差。

```bash
python3 gear_calc.py
```

Ordinary arithmetic run on a computer (not a simulation). The 90 % efficiency per printed stage is a guess: measure your own.
在电脑上运行的普通计算（不是仿真）。每级 90 % 的效率只是估计值，请自己测量。

The backlash toy model used in the lesson is [`tools/sim/models/backlash_sim.py`](../../../tools/sim/models/backlash_sim.py) (**simulated output / 仿真输出**).
课程中的回差玩具模型见 `tools/sim/models/backlash_sim.py`。
