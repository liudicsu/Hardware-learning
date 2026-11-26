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

## Batch-5 PR1 / 第5批 PR1

`sensors-fusion/imu_kf_vs_complementary_toy.py`: standard-library synthetic simulation, no hardware; expected output in `expected/imu_kf_vs_complementary_toy.txt`, included in `check.sh`. / 标准库合成仿真，不是硬件测量，输出由 `check.sh` 核对。

## Batch-19 PR2 / 第19批 PR2

`esp32/esp32_light_deep_sleep_toy.py`: standard-library synthetic charge-bookkeeping model of always-on, Light-sleep and Deep-sleep over a shared event timeline, with declared toy currents and wake costs (not datasheet values); no board; expected output in `expected/esp32_light_deep_sleep_toy.txt`, included in `check.sh`. / 标准库合成电荷账模型，在共享事件时间线上比较常开、Light-sleep 与 Deep-sleep；电流与唤醒代价是声明的玩具参数，不是数据手册数值；不是真板测量，输出由 `check.sh` 核对。

`sensors-fusion/i2c_clock_stretch_toy.py`: standard-library synthetic bit-timing model of I²C clock stretching: a controller that ignores SCL, one that waits for SCL high and one with a timeout, on a shared byte schedule; ideal edges (not the rise-time toy); expected output in `expected/i2c_clock_stretch_toy.txt`, included in `check.sh`. / 标准库合成位时序模型，在共享字节时间表上比较不读 SCL、等待 SCL 变高和带超时的控制器；理想边沿（不是上升时间玩具）；输出由 `check.sh` 核对。

## Batch-21 PR2 / 第21批 PR2

`first-robots/madgwick_vs_complementary_balancer_toy.py`: standard-library synthetic balancer pitch IMU stream (gyro only, the lesson's 0.5 s complementary filter, and the Madgwick 2010 IMU gradient-descent update at two beta values), shared noise draws, no hardware; expected output in `expected/madgwick_vs_complementary_balancer_toy.txt`, included in `check.sh`. Real MPU-6050 本页未运行. / 标准库合成的平衡车俯仰 IMU 数据（纯陀螺积分、课程的 0.5 s 互补滤波、两种 beta 的 Madgwick 2010 IMU 梯度下降更新），共用噪声抽样，不是硬件测量，输出由 `check.sh` 核对。

## arduino-io/ — Optocoupler isolation, CTR and LED current / 光耦隔离、CTR 与 LED 电流

`arduino-io/optocoupler_ctr_isolation_toy.py`: standard-library synthetic 24 V field input reaching a 3.3 V pin directly through a shared-ground divider, through a well-driven optocoupler (10 mA) or through the same coupler under-driven (1 mA), on shared bits, pin noise and common-mode surges (three regimes); CTR, thresholds and surge shares are declared toy parameters, not datasheet values; expected output in `expected/optocoupler_ctr_isolation_toy.txt`, included in `check.sh`. Real coupler / isolation tester 本页未运行. / 标准库合成的 24 V 现场输入：经共地分压直连 3.3 V 引脚、经驱动充足的光耦（10 mA）或同一光耦驱动不足（1 mA），在共用位、引脚噪声和共模浪涌下比较（三种情形）；CTR、阈值和浪涌份额是声明的玩具参数，不是手册值；输出由 `check.sh` 核对。

`sensors-fusion/steinhart_hart_ntc_sense_toy.py`: standard-library synthetic Steinhart–Hart NTC temperature-sensing model (local B-parameter fit near 25 °C, three-point Steinhart–Hart solve, raw ADC counts as temperature) on a shared temperature list, divider/ADC and resistance-noise draw; Wikipedia example coefficients and the 0.02 °C claim 以原文为准 and are not toy outputs; expected output in `expected/steinhart_hart_ntc_sense_toy.txt`, included in `check.sh`. Real thermistor / bath / IMU temperature register 本页未运行. / 标准库合成的 Steinhart–Hart NTC 测温模型，在共享温度列表、分压器/ADC 和电阻噪声下比较局部 B 参数拟合、三点 Steinhart–Hart 求解和把原始 ADC 计数当成温度；Wikipedia 示例系数与 0.02 °C 说法以原文为准，不是玩具输出；输出由 `check.sh` 核对。

`motors-drivers/encoder_speed_frequency_period_toy.py`: standard-library synthetic incremental-encoder edge train (frequency / fixed-window counts, period / time-between-edges, and a single high-pulse with declared symmetry 0.3000 and no averaging) on a shared shaft motion and jitter draw; the 12.0000 × 120.0000 = 1440.0000 count figure is a lesson stand-in, not a vendor fact; the cited Wikipedia frequency-to-RPM worked example 以原文为准 and is not a toy output; expected output in `expected/encoder_speed_frequency_period_toy.txt`, included in `check.sh`. Real encoder / timer capture 本页未运行. / 标准库合成的增量编码器边沿序列，在共享轴运动和抖动下比较频率（固定窗口计数）、周期（边沿间隔）以及不做平均、按声明对称性 0.3000 测量单次高电平脉宽的臂；12.0000 × 120.0000 = 1440.0000 是课程替身，不是厂商事实；Wikipedia 频率到 RPM 算例以原文为准，不是玩具输出；输出由 `check.sh` 核对。

## Batch-29 PR2 / 第29批 PR2

`esp32/rmt_symbol_vs_bitbang_toy.py`: standard-library labeled stand-in of the opened ESP-IDF v5.3.2 RMT symbol / encoder contract versus a bit-banged delay loop that stretches under a declared ISR load, plus hardware `loop_count` versus software re-issue and kept wrong-resolution, `bit0`/`bit1`-swap and swapped-level arms; official driver / flash 本页未运行; expected output in `expected/rmt_symbol_vs_bitbang_toy.txt`, included in `check.sh`. / 标准库、带标签的替身，对照已打开的 ESP-IDF v5.3.2 RMT 符号 / 编码器契约与声明 ISR 负荷下被拉长的 bit-bang 延时，并比较硬件 `loop_count` 与软件重发，以及保留的错误分辨率、`bit0`/`bit1` 对调和电平对调臂；官方驱动 / 烧录本页未运行，输出由 `check.sh` 核对。

## Batch-30 PR2 / 第30批 PR2

`timing-interrupts/timer1_input_capture_vs_poll_toy.py`: standard-library labeled stand-in of the opened ATmega328P 7810D §15.6 Input Capture Unit contract versus software edge polling at a declared loop period, plus official ICR overwrite and a kept wrong-ICES arm; official AVR flash / logic analyzer 本页未运行; expected output in `expected/timer1_input_capture_vs_poll_toy.txt`, included in `check.sh`. / 标准库、带标签的替身，对照已打开的 ATmega328P 7810D §15.6 输入捕获单元契约与声明循环周期下的软件边沿轮询，并比较官方 ICR 覆盖与保留的错误 ICES 臂；官方 AVR 烧录 / 逻辑分析仪本页未运行，输出由 `check.sh` 核对。
