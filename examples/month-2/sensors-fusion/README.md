# Lesson 5: Sensors, I2C & the complementary filter / 传感器、I2C 与互补滤波

Board / 开发板: Arduino Uno + MPU-6050 breakout (GY-521)

| MPU-6050 (GY-521) | Uno |
| --- | --- |
| VCC | 5 V (the GY-521 has a regulator; bare 3.3 V modules → 3.3 V) / 5 V（GY-521 自带稳压；裸 3.3 V 模块接 3.3 V） |
| GND | GND |
| SDA | A4 |
| SCL | A5 |
| AD0 | unconnected → address 0x68 / 悬空 → 地址 0x68 |

| Sketch / 程序 | What it does / 作用 |
| --- | --- |
| `i2c_scanner/` | lists every address that answers / 列出所有应答的地址 |
| `imu_pitch/` | pitch from gyro only, accelerometer only and the complementary filter / 分别用陀螺仪、加速度计和互补滤波计算俯仰角 |

```bash
arduino-cli compile -b arduino:avr:uno examples/month-2/sensors-fusion/imu_pitch
```

Serial at 115200 baud. The outputs in the lesson come from simavr with a simulated MPU-6050 (scripted tilt, +1.5 °/s gyro bias; **simulated output / 仿真输出**). The Python model is [`tools/sim/models/filter_sim.py`](../../../tools/sim/models/filter_sim.py).

Wokwi: `i2c_scanner/` and `imu_pitch/` each also have a `diagram.json` for the online simulator at [wokwi.com](https://wokwi.com); create a new Uno project there, paste the sketch's `.ino` into the editor's `sketch.ino` tab and this `diagram.json` into the `diagram.json` tab, then start the simulation. Note that Wokwi's MPU-6050 is an ideal sensor: no gyro bias, no noise and therefore no drift, so the gyro-only angle will not wander like the simulated output in the lesson (which adds a +1.5 °/s bias). / Wokwi：`i2c_scanner/` 和 `imu_pitch/` 每个程序目录里另有供在线模拟器 [wokwi.com](https://wokwi.com) 使用的 `diagram.json`；在网站上新建一个 Uno 项目，把程序的 `.ino` 内容粘进编辑器的 `sketch.ino` 标签页，把这里的 `diagram.json` 粘进 `diagram.json` 标签页，再点运行。注意 Wokwi 的 MPU-6050 是理想传感器：没有陀螺零偏、没有噪声，因此也没有漂移，纯陀螺积分的角度不会像课里的仿真输出（加了 +1.5 °/s 零偏）那样慢慢跑偏。
