# Wokwi diagrams: parts and pins check (PR demos-pr1)

Checked 2026-10-21 (UTC+8) by fetching each page below with `curl` (all HTTP 200
unless noted) and reading the pin tables; the pin sets are copied into
`tools/check_wokwi.py`, which validates every `examples/**/diagram.json`
(JSON parses, `version` 1, unique part ids, known part types, every connection
end is `id:pin` with a declared id and a documented pin, exactly one board,
no `bounce` override on push buttons, a sketch `.ino` in the same folder).
It runs in CI and in `tools/sim/reproduce.sh`.

No Wokwi account or project was created. The `.ino` files are the existing repo
files, unchanged; readers paste them into a new wokwi.com project themselves.

| Source | What it confirms |
|---|---|
| https://docs.wokwi.com/diagram-format | file layout (`version`, `author`, `editor`, `parts` with `type`/`id`/`top`/`left`/`attrs`, `connections` as `[from, to, color, route]`); `wokwi-arduino-uno` and `board-esp32-s3-devkitc-1` are supported microcontroller types |
| https://docs.wokwi.com/parts/wokwi-arduino-uno | pins `0`–`13`, `A0`–`A5`, `GND.1` `GND.2` `GND.3`, `VIN`, `5V` (3.3V/IOREF/AREF/RESET not simulated, so not allowed); `L` LED on pin 13; A4 = SDA, A5 = SCL; Serial Monitor attaches automatically |
| https://docs.wokwi.com/parts/wokwi-pushbutton | pins `1.l` `1.r` `2.l` `2.r`; bouncing is simulated by default, `bounce: "0"` disables it (we keep the default) |
| https://docs.wokwi.com/parts/wokwi-potentiometer | pins `GND` `SIG` `VCC`; attr `value` 0–1023 |
| https://docs.wokwi.com/parts/wokwi-led | pins `A` (anode) `C` (cathode); attr `color` |
| https://docs.wokwi.com/parts/wokwi-resistor | pins `1` `2`; attr `value` in ohms |
| https://docs.wokwi.com/parts/wokwi-mpu6050 | pins `VCC` `GND` `SCL` `SDA` `XDA` `XCL` `AD0` `INT`; address 0x68 (AD0 unconnected); Uno: SDA → A4, SCL → A5; initial accel/gyro attrs; ideal sensor (no bias/noise attributes) |
| https://docs.wokwi.com/parts/wokwi-logic-analyzer | pins `D0`–`D7`, `GND` |
| https://docs.wokwi.com/parts/board-esp32-s3-devkitc-1 | **404** — no part page exists for this board |
| https://docs.wokwi.com/guides/esp32 | ESP32-S3-DevKitC-1 is a supported board; USB-CDC option (not used: we keep UART0 on `TX`/`RX`) |
| https://github.com/wokwi/wokwi-boards/blob/main/boards/esp32-s3-devkitc-1/board.json | the board's pin names: `0`–`21`, `35`–`42`, `45`–`48`, `3V3.1` `3V3.2` `5V` `GND.1`–`GND.4` `RST` `RX` `TX` |
| https://docs.wokwi.com/guides/serial-monitor | `$serialMonitor:TX` goes to the board's RX, `$serialMonitor:RX` to its TX |

## Diagrams

| Sketch | Parts | Connections |
|---|---|---|
| `arduino-io/blink_custom` | Uno | none (on-board `L` LED, pin 13) |
| `arduino-io/button_pullup` | Uno, push button | `btn1:1.l`–`uno:2`, `btn1:2.l`–`uno:GND.1` |
| `arduino-io/pot_pwm` | Uno, potentiometer, 220 Ω, LED, logic analyzer | pot VCC/GND/SIG → 5V/GND.2/A0; `uno:9` → 220 Ω → LED → GND.1; analyzer D0 ← pin 9 |
| `timing-interrupts/two_blinks` | Uno, 2 × (220 Ω + LED) | pins 8 and 9 → resistor → LED → GND.1 |
| `timing-interrupts/reaction_timer` | Uno, push button (default bounce), 220 Ω, LED | button pin 2 ↔ GND.1; pin 13 → 220 Ω → LED → GND.2 |
| `sensors-fusion/i2c_scanner`, `sensors-fusion/imu_pitch` | Uno, MPU6050 | VCC → 5V, GND → GND.2, SDA → A4, SCL → A5 |
| `esp32/chip_info` | ESP32-S3-DevKitC-1, 220 Ω, LED | GPIO 2 → 220 Ω → LED → GND.1; TX/RX ↔ Serial Monitor |

Not done: `esp32/web_servo` (reaching the simulated ESP32's HTTP server from a
browser needs Wokwi's Private IoT Gateway, documented as paid-only), and the
diagrams were not run on wokwi.com in this PR (format and pins were checked
against the docs only).
