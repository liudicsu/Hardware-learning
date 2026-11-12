# Batch-19 PR2 sources — ESP32 Light-sleep / Deep-sleep energy, I²C clock stretching

Base: `37181b1f9c6c64acdea478415ea7febdefc6e92d` (batch-19 PR1 #177 merged; site **36120**, M2 **3030**).
This PR: site **36120→36480**, M2 **3030→3390**, catalogue still **71**. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

Both returned HTTP **200** (this run, 2026-11-12 UTC+8).

| id | URL | rev | What was used |
|---|---|---|---|
| idf-sleep-modes | https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/sleep_modes.html | `latest` docs, read 2026-11-12 | Two major modes. Light-sleep: digital peripherals, most RAM and CPUs clock-gated with reduced supply; internal state preserved on exit. Deep-sleep: CPUs, most RAM and APB-clocked digital peripherals powered off; RTC controller, ULP coprocessor, RTC FAST and RTC SLOW memory remain. Wakeup sources can be combined: timer, touchpad, ext0 / ext1 (RTC IOs), ULP, GPIO wakeup from Light-sleep (any IO), GPIO wakeup from Deep-sleep (VDD3P3_RTC-domain pins only). Wi-Fi / Bluetooth connections are not maintained in Deep-sleep or Light-sleep. A Deep-sleep wake runs the wake stub, then loads the application. `RTC_DATA_ATTR` variables live in RTC SLOW memory. |
| wiki-i2c | https://en.wikipedia.org/wiki/I²C (fetched as `I%C2%B2C`) | 1384185777 | Clock stretching is target flow control; a target may hold SCL low after a byte; open-drain, so SCL stays low; the controller must wait until it observes SCL actually high, then a minimal time (4 μs for standard 100 kbit/s); usually around the ACK; some controllers do not support it (two-wire interface); pure I²C sets no stretch limit, SMBus does. The bit-transfer paragraph also says the wait includes the finite RC rise time — that part is the existing arduino-io rise-time toy and is **not** modelled here (ideal edges). |

The ESP-IDF body we read gives **no sleep-current table and no wake-latency figure**; the only current it mentions (SPI flash standby) is not used. Every current and wake cost in the ESP32 toy is a **declared toy parameter**, printed, not a datasheet value (以文档为准 for the documented behaviour). UM10204 (the NXP I²C-bus specification) was **not** opened, so no tLOW / tHIGH / timing-table value from it is quoted; the only timing figure used is Wikipedia's 4 μs (以原文为准). No ESP32 datasheet, no power-analyser capture, no logic-analyser capture.

## Toys

- `examples/month-2/esp32/esp32_light_deep_sleep_toy.py` → `examples/month-2/expected/esp32_light_deep_sleep_toy.txt`
- `examples/month-2/sensors-fusion/i2c_clock_stretch_toy.py` → `examples/month-2/expected/i2c_clock_stretch_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only. No integration step (event-driven I × t sum / summed event times). Every number in the new lesson prose, the new Summary sentences, the curriculum objectives, the month-2 plan and this note that carries an m±sd form is printed by the toys into `expected/`. Hand calculations are labelled as such and printed, except the 15 / 16 = 0.9375 lost-byte fraction, which is labelled 手算 in the page and equals the printed overtime bad_rate.

## Regime results (first accepted run = first run)

### H3 ESP32 sleep (`esp32_light_deep_sleep_toy.txt`)

- Declared toy parameters, not datasheet values: I_ACTIVE=40.0 mA, I_LIGHT=0.80 mA, I_DEEP=0.01 mA, I_BOOT=50.0 mA, T_WAKE_LIGHT=0.001 s, T_BOOT_DEEP=0.300 s, WORK=0.050 s.
- Hand calc (printed): per cycle A=40.0*g, B=1.9992+0.80*g, C=16.9965+0.01*g mA·s (C valid for g ≥ 0.350 s). Break-even C<A iff g>0.4250 s, C<B iff g>18.9839 s — strict, equality is a tie (tested at equality and ±1 ms).
- long_idle: paired C−A avg_mA -39.7086±0.0026, clear, 5/5; paired C−B -0.5417±0.0023, clear, 5/5; latency C 300.0000 ms vs B 1.0000 ms.
- high_wake_rate (mean gap 0.25 s): paired C−B avg_mA 21.1306±0.2356, clear, 5/5 — Deep-sleep **loses** to Light-sleep, kept. Paired C−A -9.9044±0.2135, clear, 5/5 in C's favour: the pre-declared *possible* loss against A did **not** happen with these parameters; printed as it came out, not retuned.
- missed_wake_source: paired C−B missed 122.0000±10.3199, clear, 5/5, kept; C still lowest current (paired C−A -39.7101±0.0022).
- State check True on every regime: B RAM counter == served; C RTC SLOW counter == served and RAM counter < served.

### H4 I²C clock stretching (`i2c_clock_stretch_toy.txt`)

- Hand calc (printed): T_BIT=10.0 us → 100.0 kHz; T_HIGH=5.0 us ≥ 4 us; unstretched transaction 16*9*10.0 us = 1440.0 us. Early-sample rule strict: stretch 2.5000 us → 0 early bits, 2.5001 us → 1. Timeout strict: 200.0000 us accepted, 200.0010 us aborts.
- no_stretch: every paired line tie: identical on every seed (bus 28.8000 ms for all arms).
- moderate_stretch: paired A−B bad_rate 0.8681±0.0111, clear, 5/5; paired B−A bus_ms 12.0501±0.1307, clear, 5/5; paired C−B bad_rate tie.
- overtime_stretch: paired C−B bad_rate 0.9375±0.0000, clear, 5/5, kept; paired C−B aborts 20.0000±0.0000; paired B−A bus_ms 135.1400±0.7771; paired A−B bad_rate 0.9338±0.0041.

## Post-hoc choices

None for parameters or regimes: the currents, wake costs, windows, the 0.25 s gap (chosen before the first run to sit below the hand-calculated 0.4250 s break-even), the stretch ranges and TIMEOUT_US = 200.0 us were written before the first run. Alternatives were printed on the same seeds as a pre-planned sensitivity and were not adopted: I_BOOT=40.0 mA (paired C−A -14.2824±0.1689, break-even g>0.3500 s), T_BOOT_DEEP=0.100 s (paired C−A -20.2624±0.0965, break-even g>0.1750 s), TIMEOUT_US=1000.0 on overtime (C−B tie) and TIMEOUT_US=50.0 on moderate (paired C−B 0.7800±0.0216).

One code change after the first run, with **byte-identical output**: `simulate()` in the ESP32 toy now returns latency 0.0 when an arm serves no event (the independent test with a single missed event hit a division by zero). No regime serves zero events, so `expected/` did not change (checked with `cmp`).

## Mismatch with §9

- H3: §9 pre-declares that a high wake rate *may* lose. The kept loss is Deep-sleep vs Light-sleep (paired C−B 21.1306±0.2356, clear); against always-on, Deep-sleep still wins (paired C−A -9.9044±0.2135). Reported as is; parameters were not changed to manufacture a loss vs A.
- H4 matches §9: no-stretch tie; moderate stretch consistent wait win; overtime consistent fail, kept.

No other mismatch: CRN, ≥5 seeds, no integration step stated and tested, no unprinted side-run numbers, en/zh synced, difference directions in prose / Summary / curriculum / plan / this note match the printed `paired` lines (locked).

Real ESP32 / real I²C bus or analyser: 本页未运行.

## opencode

Tried free models in order DeepSeek (`opencode/deepseek-v4.1-flash-free`), GLM (`opencode/glm-5.3-flash-free`), MiMo (`opencode/mimo-v2.6-flash-free`), LongCat (`opencode/longcat-2.5-free`), MiniMax (`opencode/minimax-m3.1-flash-free`). All five timed out (exit 124) with no file written. Implementation is local.

## Lock changes

Tipped site-total, host-minute and Current-header locks only; no lock relaxed. New batch-19 PR2 block added (toys, expected, CRN, label order, strict boundaries, difference directions, sources, plan, README).

- README `/36 120/` and `约 36 120 分钟` → `/36 480/` and `约 36 480 分钟` (including earlier “unchanged” tips).
- Curriculum sum checks `36120` → `36480`; `current curriculum` month totals M2 3030→3390.
- `esp32` host minutes in the rtos1 case `360` → `540`.
- `sensors-fusion` host minutes in earlier cases `720` → `900`.
- month-2 plan Current header lock (was Batch-10 PR1, **M2 3030**) → Batch-19 PR2, **M2 3390**; historical `## Batch-10 PR1` and earlier markers kept.

No lock relaxed.
