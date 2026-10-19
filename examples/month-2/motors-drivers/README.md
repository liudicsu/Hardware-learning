# Lesson 4: Motors, drivers & your first encoder loop / 电机、驱动器与编码器闭环

Board / 开发板: Arduino Uno + TB6612FNG breakout + gearmotor with quadrature encoder (e.g. Pololu Romi 120:1, 12 CPR → 1440 counts per wheel turn)

`one_rev/`: turn the wheel exactly one revolution. / 让车轮精确转一圈。

| TB6612FNG | Uno |
| --- | --- |
| PWMA | D5 |
| AIN1 / AIN2 | D7 / D8 |
| STBY | D9 |
| VCC | 5 V |
| VM | motor battery + / 电机电池正极 |
| GND | common ground (battery, driver, Uno) / 电池、驱动、Uno 共地 |
| AO1 / AO2 | motor leads / 电机两根线 |

Encoder / 编码器: A → D2, B → D3, VCC → 5 V, GND → GND.

```bash
arduino-cli compile -b arduino:avr:uno examples/month-2/motors-drivers/one_rev
```

Serial at 115200 baud. The counts in the lesson come from simavr connected to a toy motor + encoder model (**simulated output / 仿真输出**); on a real wheel tune `MIN_PWM` and `KP` and expect different numbers. The Python model is [`tools/sim/models/one_rev_sim.py`](../../../tools/sim/models/one_rev_sim.py).
