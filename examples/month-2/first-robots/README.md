# Lesson 6: Your first two robots / 你的前两台机器人：循线小车与自平衡车

Board / 开发板: Arduino Uno + TB6612FNG (both channels) + two gearmotors. Both sketches use the same motor pins.
两个程序使用相同的电机引脚。

| TB6612FNG | Uno |
| --- | --- |
| PWMA / AIN1 / AIN2 (left / 左) | D5 / D7 / D8 |
| PWMB / BIN1 / BIN2 (right / 右) | D6 / D4 / D12 |
| STBY | D9 |
| VCC / VM / GND | 5 V / motor battery + / common ground / 5 V / 电机电池正极 / 共地 |

**`line_follower/`**: Pololu QTR-8RC array, library `QTRSensors` (tested 4.0.0). / 需要 `QTRSensors` 库。
Sensors 1–8 → A0, A1, A2, A3, A4, A5, D10, D11; array VCC → 5 V, GND → GND; mount about 3 mm above the floor. / 传感器 1–8 依次接 A0–A5、D10、D11；距地面约 3 mm。

```bash
arduino-cli lib install QTRSensors
arduino-cli compile -b arduino:avr:uno examples/month-2/first-robots/line_follower
```

Compiled only, never run on a robot. / 只编译，没有在小车上运行过。

**`balancer/`**: MPU-6050 wired as in Lesson 5 (SDA → A4, SCL → A5, 0x68). / MPU-6050 接法同第 5 课。
Keep the 40° cut-off and test with the wheels off the ground first. / 保留 40° 断电保护，先架空车轮测试。

```bash
arduino-cli compile -b arduino:avr:uno examples/month-2/first-robots/balancer
```

The balancer output in the lesson comes from simavr with a simulated MPU-6050 and no motors or physics (**simulated output / 仿真输出**). The toy models are [`line_sim.py`](../../../tools/sim/models/line_sim.py) and [`balance_sim.py`](../../../tools/sim/models/balance_sim.py).

**`madgwick_vs_complementary_balancer_toy.py`**: standard-library synthetic IMU stream for the balancer's pitch (gyro only, the lesson's 0.5 s complementary filter, and the Madgwick 2010 IMU update at beta 0.033 and 0.5); five seeds, common random numbers; expected output in `../expected/madgwick_vs_complementary_balancer_toy.txt`, compared by `../check.sh`. Not an MPU-6050; a real IMU 本页未运行. / 标准库合成的平衡车俯仰 IMU 数据，比较纯陀螺积分、课程的 0.5 s 互补滤波与 beta 为 0.033 和 0.5 的 Madgwick 2010 IMU 更新；5 个种子，共用随机数；不是 MPU-6050，真实 IMU 本页未运行。

```bash
python3 madgwick_vs_complementary_balancer_toy.py
```
