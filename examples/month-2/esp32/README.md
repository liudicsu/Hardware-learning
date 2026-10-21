# Lesson 3: ESP32 / ESP32：Wi-Fi、3.3 V 逻辑与框架选择

Board / 开发板: ESP32 DevKit (classic) or ESP32-S3 DevKitC. Arduino core `esp32:esp32` (tested with 3.3.12).

| Sketch / 程序 | Hardware / 硬件 | Wiring / 接线 |
| --- | --- | --- |
| `chip_info/` | none: on-board LED (set `LED_PIN` for your board) / 无，板载 LED（按你的板子设置 `LED_PIN`） | — |
| `web_servo/` | hobby servo, 10 kΩ potentiometer, separate 5 V supply for the servo / 舵机、10 kΩ 电位器、舵机独立 5 V 电源 | servo signal → GPIO 18; servo + → external 5 V; servo − → GND shared with the ESP32; pot ends → 3.3 V and GND; wiper → GPIO 34 (classic) or GPIO 4 (S3) / 舵机信号 → GPIO 18，舵机 + → 外部 5 V，舵机 − 与 ESP32 共地；电位器两端接 3.3 V 与 GND，滑动端接 GPIO 34（经典款）或 GPIO 4（S3） |

```bash
arduino-cli core install esp32:esp32
arduino-cli compile -b esp32:esp32:esp32s3 examples/month-2/esp32/web_servo    # or esp32:esp32:esp32
```

Before flashing `web_servo`, replace `your-network` / `your-password`, and **do not commit your real Wi-Fi password**.
烧录 `web_servo` 前替换 Wi-Fi 名称和密码，**不要把真实密码提交到 Git**。
These sketches were compiled, not run; the lesson quotes no output for them. / 这些程序只做了编译，课程里没有引用它们的输出。

Wokwi: `chip_info/` also has a `diagram.json` for the online simulator at [wokwi.com](https://wokwi.com); create a new ESP32-S3 project there, paste the sketch's `.ino` into the editor's `sketch.ino` tab and this `diagram.json` into the `diagram.json` tab, then start the simulation. `web_servo/` has no Wokwi diagram because reaching the ESP32's web server from a browser needs Wokwi's paid Private IoT Gateway. / Wokwi：`chip_info/` 目录里另有供在线模拟器 [wokwi.com](https://wokwi.com) 使用的 `diagram.json`；在网站上新建一个 ESP32-S3 项目，把程序的 `.ino` 内容粘进编辑器的 `sketch.ino` 标签页，把这里的 `diagram.json` 粘进 `diagram.json` 标签页，再点运行。`web_servo/` 没有 Wokwi 图，因为要从浏览器访问 ESP32 的网页服务器需要 Wokwi 付费的 Private IoT Gateway。
