# Lesson 1: Arduino IO, PWM & serial / Arduino 入门：数字/模拟 IO、PWM 与串口

Board / 开发板: Arduino Uno (or any ATmega328P board / 任意 ATmega328P 板)

| Sketch / 程序 | Hardware / 硬件 | Wiring / 接线 |
| --- | --- | --- |
| `blink_custom/` | none: on-board LED / 无，用板载 LED | — |
| `button_pullup/` | push button / 按键 | button between D2 and GND (internal pull-up) / 按键接 D2 与 GND（内部上拉） |
| `pot_pwm/` | 10 kΩ potentiometer, LED + 220 Ω resistor / 10 kΩ 电位器、LED + 220 Ω 电阻 | pot ends → 5 V and GND, wiper → A0; D9 → 220 Ω → LED anode, LED cathode → GND / 电位器两端接 5 V 和 GND，滑动端接 A0；D9 → 220 Ω → LED 正极，LED 负极接 GND |

```bash
arduino-cli compile -b arduino:avr:uno examples/month-2/arduino-io/pot_pwm
```

Serial monitor at 115200 baud. / 串口监视器波特率 115200。
The `pot_pwm` output in the lesson was produced in simavr with fixed voltages on A0 (**simulated output / 仿真输出**); reproduce it with `tools/sim/reproduce.sh`.

Wokwi: `blink_custom/`, `button_pullup/` and `pot_pwm/` each also have a `diagram.json` for the online simulator at [wokwi.com](https://wokwi.com); create a new Uno project there, paste the sketch's `.ino` into the editor's `sketch.ino` tab and this `diagram.json` into the `diagram.json` tab, then start the simulation. / Wokwi：`blink_custom/`、`button_pullup/` 和 `pot_pwm/` 每个程序目录里另有供在线模拟器 [wokwi.com](https://wokwi.com) 使用的 `diagram.json`；在网站上新建一个 Uno 项目，把程序的 `.ino` 内容粘进编辑器的 `sketch.ino` 标签页，把这里的 `diagram.json` 粘进 `diagram.json` 标签页，再点运行。
