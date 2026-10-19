# Lesson 2: Non-blocking timing, interrupts & debouncing / 非阻塞计时、中断与按键消抖

Board / 开发板: Arduino Uno

| File / 文件 | Hardware / 硬件 | Wiring / 接线 |
| --- | --- | --- |
| `two_blinks/` | 2 LEDs + 2 × 220 Ω / 两只 LED 与两只 220 Ω 电阻 | D8 → 220 Ω → LED A → GND; D9 → 220 Ω → LED B → GND |
| `reaction_timer/` | push button / 按键 | button between D2 (INT0) and GND; uses the on-board LED (D13) / 按键接 D2（INT0）与 GND，使用板载 LED（D13） |
| `overflow.c` | none: runs on your computer / 无，在电脑上运行 | — |

```bash
arduino-cli compile -b arduino:avr:uno examples/month-2/timing-interrupts/reaction_timer
cc -o overflow examples/month-2/timing-interrupts/overflow.c && ./overflow
```

The debounce toy model is [`tools/sim/models/debounce_sim.py`](../../../tools/sim/models/debounce_sim.py).
The `two_blinks` and `reaction_timer` outputs in the lesson come from simavr with scripted button presses (**simulated output / 仿真输出**); `overflow.c` is a real run on a computer.
