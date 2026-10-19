# Lesson 4: PID & control, windup and cascade loops / 第 4 课：PID 与控制，积分饱和与串级回路

**`balancer_cascade/`**: Month 2's balancer (inner PD on pitch at 200 Hz) plus an outer PI loop on wheel speed at 25 Hz that moves the inner loop's setpoint, with anti-windup and a ±3° limit.
在第 2 个月平衡车（200 Hz 俯仰角 PD 内环）的基础上，加一个 25 Hz 的轮速 PI 外环来调整内环设定值，带抗积分饱和和 ±3° 限幅。

Board / 开发板: Arduino Uno + TB6612FNG + two gearmotors with encoders + MPU-6050, wired as in Month 2 Lesson 6, plus:
接法同第 2 个月第 6 课，另加：

| Encoder / 编码器 | Uno |
| --- | --- |
| left A / 左 A | D2 (interrupt / 中断) |
| left B / 左 B | D10 |
| right A / 右 A | D3 (interrupt / 中断) |
| right B / 右 B | D11 |
| VCC / GND | 5 V / GND |

```bash
arduino-cli compile -b arduino:avr:uno examples/month-3/pid-control/balancer_cascade
```

Get the inner loop balancing first and copy your Month 2 `KP`/`KD` into the sketch. `METERS_PER_COUNT` assumes a 12 CPR encoder, a 30:1 gearbox and 65 mm wheels, counting rising edges of A only: change it for your motors. The outer gains (3 and 3) are a cautious start; the lesson's model liked 12 and 12.
先让内环能站稳，再把第 2 个月调好的 `KP`/`KD` 填进来。`METERS_PER_COUNT` 假设 12 CPR 编码器、30:1 减速箱、65 mm 车轮、只数 A 相上升沿，请按你的电机修改。外环增益（3 和 3）是保守的起点，课程里的模型用的是 12 和 12。

The lesson's output for this sketch comes from simavr with the simulated MPU-6050 and injected encoder pulses; no motors or robot physics are simulated (**simulated output / 仿真输出**). The models are [`pid_sim.py`](../../../tools/sim/models/pid_sim.py) and [`cascade_sim.py`](../../../tools/sim/models/cascade_sim.py). Not run on a real robot by the site editor.
课程中这个程序的输出来自 simavr、模拟的 MPU-6050 和注入的编码器脉冲，没有模拟电机和车身物理。本站编者没有在真车上运行过。
