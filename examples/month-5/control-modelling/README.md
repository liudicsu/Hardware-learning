# Lesson 1: control theory, model the plant, then read the loop / 第 1 课：控制理论，先建模再看回路

This lesson's program is a toy model, so it lives with the other models in [`tools/sim/models/joint_freq.py`](../../../tools/sim/models/joint_freq.py). It uses only the Python standard library.
本课的程序是一个玩具模型，所以和其他模型一起放在 [`tools/sim/models/joint_freq.py`](../../../tools/sim/models/joint_freq.py)，只用 Python 标准库。

```bash
python3 tools/sim/models/joint_freq.py
```

What it does / 它做什么:
1. Open-loop step on Month 3's arm joint (J = 0.004 kg·m², B = 0.05 N·m per rad/s, gravity cancelled by feedforward), then B and J back from the final speed and the 63 % time.
   对第 3 个月的机械臂关节做开环阶跃（重力由前馈抵消），再从终值速度和 63 % 时间反推出 B 和 J。
2. The loop gain of a PD controller at 200 Hz with a zero-order hold and one sample of delay, as a Bode table, with the gain and phase margins.
   200 Hz、零阶保持加一个采样周期延迟的 PD 回路增益：伯德表、增益裕度与相位裕度。
3. A P-only gain sweep in the time domain that checks the margins' predictions (overshoot, the kp where it goes unstable, the ringing frequency).
   在时域里扫描纯 P 增益，验证裕度的预测（超调、失稳的 kp、振荡频率）。

Its output is quoted in the lesson as **simulated output / 仿真输出** and checked by `tools/sim/reproduce.sh` against `tools/sim/expected/m5-joint_freq.txt`. To try it on hardware, log speed (from an encoder) while you hold a constant PWM on a motor, and apply step 1 to your own log. Not run on a real motor by the site editor.
课程中以“仿真输出”引用它的输出，由 `tools/sim/reproduce.sh` 与 `tools/sim/expected/m5-joint_freq.txt` 比对。想在硬件上试，就给电机一个恒定 PWM 并用编码器记录速度，再对你自己的记录做第 1 步。本站编者没有在真实电机上运行过。

## Enrichment: PE vs step (`sysid_pe_compare_toy.py`) / 深化：持续激励对照阶跃

```bash
python3 examples/month-5/control-modelling/sysid_pe_compare_toy.py
# or: bash examples/month-5/check.sh
```

Fair energy, shared noise, reports `cond(ΦᵀΦ)` and `‖θ̂−θ‖`. Equation-error OLS bias caveat. Real motor sysid 本页未运行.
公平能量、共享噪声，报告条件数与参数误差；方程误差 OLS 偏差风险已标明。真实电机辨识本页未运行。

## smith_predictor_delay_toy.py — Smith predictor / Smith 预估器

```bash
python3 examples/month-5/control-modelling/smith_predictor_delay_toy.py
```

First-order plant with a pure input delay, explicit Euler at 1 ms (asserts `H < 2τ`); a PI that ignores the delay vs the same PI in a Smith predictor with the true model vs one with a wrong delay / gain model; five seeds, common random numbers. Real delayed plant 本页未运行.
带纯输入延迟的一阶对象，1 ms 显式 Euler（断言 `H < 2τ`）；比较忽略延迟的 PI、放进真实模型 Smith 预估器的同一个 PI、以及延迟/增益模型错误的 Smith 预估器；5 个种子，共用随机数。真实带延迟对象本页未运行。

## computed_torque_inverse_dynamics_toy.py — computed torque / 计算力矩

```bash
python3 examples/month-5/control-modelling/computed_torque_inverse_dynamics_toy.py
```

Planar 2R arm with point masses, unmodelled friction and held measurement noise, semi-implicit Euler at 1 ms (stable step H* = 41.4214 ms for the matched error dynamics, checked at 0.98× / 1.02× and at half step); PD + gravity vs computed torque with the true model vs computed torque with the payload left out; five seeds, common random numbers. Real arm 本页未运行.
带点质量、未建模摩擦和保持测量噪声的平面 2R 机械臂，1 ms 半隐式 Euler（模型准确时误差动态的稳定步长 H* = 41.4214 ms，在 0.98× / 1.02× 和半步长下检查）；比较 PD + 重力、模型准确的计算力矩和漏掉负载的计算力矩；5 个种子，共用随机数。真实机械臂本页未运行。
