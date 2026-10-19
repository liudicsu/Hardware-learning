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
