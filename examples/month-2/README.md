# Month 2 examples / 第 2 个月示例

One folder per lesson. Each folder's README lists the hardware, the wiring and how to build.
每课一个目录，目录里的 README 写明所需硬件、接线和编译方法。

| Lesson / 课程 | Folder / 目录 | Board / 开发板 | Checked by / 验证方式 |
| --- | --- | --- | --- |
| 1 Arduino IO, PWM & serial / Arduino 入门 | [`arduino-io/`](arduino-io/) | Uno | compiled; `pot_pwm` run in simavr / 编译；`pot_pwm` 在 simavr 中运行 |
| 2 Timing, interrupts & debouncing / 非阻塞计时与中断 | [`timing-interrupts/`](timing-interrupts/) | Uno (+ your computer for `overflow.c`) | simavr; `overflow.c` run natively / simavr；`overflow.c` 在电脑上直接运行 |
| 3 ESP32 | [`esp32/`](esp32/) | ESP32 / ESP32-S3 | compiled only / 只编译 |
| 4 Motors, drivers & encoder loop / 电机与编码器 | [`motors-drivers/`](motors-drivers/) | Uno + TB6612FNG | simavr + motor/encoder model / simavr + 电机编码器模型 |
| 5 Sensors, I2C & complementary filter / 传感器与互补滤波 | [`sensors-fusion/`](sensors-fusion/) | Uno + MPU-6050 | simavr + simulated MPU-6050 / simavr + 模拟 MPU-6050 |
| 6 First two robots / 前两台机器人 | [`first-robots/`](first-robots/) | Uno + TB6612FNG | line follower compiled only; balancer in simavr / 循线只编译；平衡车在 simavr 中运行 |

**Build any sketch / 编译任意程序** (needs [arduino-cli](https://arduino.github.io/arduino-cli/) and the `arduino:avr` core):

```bash
arduino-cli core install arduino:avr
arduino-cli compile -b arduino:avr:uno examples/month-2/arduino-io/pot_pwm
arduino-cli upload  -b arduino:avr:uno -p /dev/ttyACM0 examples/month-2/arduino-io/pot_pwm   # your port / 你的串口
```

The Python toy models used in these lessons are in [`tools/sim/models/`](../../tools/sim/models/); to re-create every simulated output, run `tools/sim/reproduce.sh` (see [`tools/sim/README.md`](../../tools/sim/README.md)).
课程中的 Python 玩具模型在 `tools/sim/models/`；运行 `tools/sim/reproduce.sh` 可重新生成全部仿真输出。

> Simulated outputs are not hardware measurements: on a real board your numbers will differ.
> 仿真输出不是硬件实测，真实开发板上的数值会有所不同。
