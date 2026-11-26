# Batch-29 PR2 sources

Unit: H2 ESP-IDF RMT symbol / encoder contract versus a bit-bang stretch (`esp32`, 540→720). Site **46080** = 45900+180; M2 **4290** (still 180 below M9/M10=4470 and 240 below jointly-heaviest M8=M11=4530); still 71 lessons. Branch `feat/esp32-rmt-symbols` from `6c79742822f4554b13715cc6d077891d2aac0fca`. Site typography after this PR is `46 080`. M1 stays 3090 (still lightest). M8=M11 stay jointly heaviest at 4530. These load facts are recorded here and in the month-2 plan Current header only, not as a student-facing process lecture. Parent accepted the 2-unit batch; this PR is H2 only. H1 / `ohms-law` was already squash-merged and is not retouched.

## Pins actually opened (re-fetched live at writing)

This is an Espressif docs page, not an arXiv record: no Comments header and no journal-ref field were present, and none was invented. The lesson is pinned to v5.3.2, not to `stable`.

- ESP-IDF Programming Guide **v5.3.2**, ESP32-S3, *Remote Control Transceiver (RMT)*, https://docs.espressif.com/projects/esp-idf/en/v5.3.2/esp32s3/api-reference/peripherals/rmt.html — curl **200**; sha256 `5c37adca533d49aef945039bfb46ca6195475f7596ed507a7fabd6f6b71470ab`. Last-Modified Fri, 06 Dec 2024 01:16:25 GMT = 2024-12-06 09:16:25 Asia/Shanghai. Live re-fetch at writing 2026-11-26 09:38:34 Asia/Shanghai (response Date Thu, 26 Nov 2026 01:38:34 GMT): HTTP 200, sha256 and Last-Modified both match the parent pin and the cached body at `/tmp/b29p2-docs/rmt.html`. This page was **not** already in `src/lib/resources.ts`, `src/lib/curriculum.ts`, or the host MDX; it is added here as a new Resource / reading-map / curriculum entry `esp-idf-s3-rmt` and is the formula body. 以文档为准: infrared-transceiver origin and general-purpose extension; `rmt_symbol_word_t` as two pairs of a 15-bit duration in RMT ticks and a 1-bit level; cannot transmit raw byte streams like SPI or I2C; `rmt_new_bytes_encoder` with `bit0` / `bit1` / `msb_first`; `resolution_hz` and the official example `.resolution_hz = 1 * 1000 * 1000` (“1 MHz tick resolution, i.e., 1 tick = 1 µs”, an example, not a chip-universal default); `loop_count` hardware-controlled periodic sequences, `-1` until `rmt_disable()` with no trans-done, a positive finite count, and the documented memory-block size limitation for non-zero `loop_count`. Official example comments mention NEC shortest duration 560 µs and longest 9000 µs; 以文档为准, and they are not toy outputs. No numeric channel count was invented. Official RMT driver / flash, including `led_strip`, `ir_nec_transceiver`, `dshot_esc` and `onewire`, 本页未运行.

- ESP-IDF Programming Guide v5.3.2, ESP32-S3, *LED Control (LEDC)*, https://docs.espressif.com/projects/esp-idf/en/v5.3.2/esp32s3/api-reference/peripherals/ledc.html — curl **200**; sha256 `a5e3fadff9827a5322672fb668988fd37e82bb000a09312bd80e98e90b820aae`. Last-Modified Fri, 06 Dec 2024 01:15:55 GMT. Live re-fetch at writing matched. Cross-check only, not the formula body. The article body does not discuss RMT or `rmt_symbol_word_t`; one sidebar toctree link is nav chrome. This unit is not a second LEDC PWM lecture; the existing LEDC duty table and 14-bit overflow warning were not rewritten.

Lesson-chosen toy parameters (`resolution_hz = 1000000`, `wrong_resolution_hz = 2000000`, short-pulse `duration0=8` / `duration1=4` / `N_SHORT=8`, periodic `duration0=20` / `duration1=30`, `loop_count=4`, `reissue_gap_us=8.0000`, bytes-encoder payload `0xA5` / `msb_first` / `bit0` 4+12 and `bit1` 12+4, `lambda_per_us=0.1500`, `isr_cost_us=5.0000`, `lambda_alt=0.0500`, `clear_frac=0.2000`, work plan `30+25+50+40+35=180`) were named in the toy header / `hand_calc` lines before the official first run. Official RMT driver / flash 本页未运行. No Falstad / Wokwi claim that the toy was clicked on this page. No invented datasheet currents, WS2812 timings, or channel counts.

## Official first run

`rmt_symbol_vs_bitbang_toy.py`, 2026-11-26 09:44:10 Asia/Shanghai, byte-identical on rerun. Expected sha256 `4b931fc03c0ffd64d2c27c03e52c9defa8508fdae6d80c7b9a76a732c6c876e4`. Official `expected/` was not retuned.

## Pre-declared cells

All held and are disclosed in the en/zh results.

- idle: paired A-B `total_us` and paired A-B `wrong_level_us` are both `0.0000+-0.0000: tie: identical on every seed` (`96.0000 us`). Declared exact tie; held; kept.
- isr_loaded_short: paired A-B `total_us` `72.0000+-14.4049`, **clear**, same sign on all 5 seeds (B clearly better; bit-bang stretches). B `total_us` versus the declared `96.0000 us` is a **tie**. Held; kept.
- hw_loop_periodic: B stays at declared `200.0000 us` (tie). Paired A-B `total_us` `197.0000+-28.4165`, **clear**, same sign on all 5 seeds (software re-issue stretches). Held; kept.
- wrong_resolution: paired C-B `total_us` `-48.0000+-0.0000`, **clear**, same sign on all 5 seeds (C loses; kept).
- bytes_bit_swap: paired D-B `total_us` is a **tie** (`128.0000 us`; `bit0` and `bit1` have the same declared period). The lose is on the waveform and the decode: paired D-B `wrong_level_us` `64.0000+-0.0000`, **clear**, same sign on all 5 seeds; decoded `0x5A` instead of `0xA5`. Held; kept, including the duration tie.
- swapped_levels: paired E-B `total_us` is a **tie** (`96.0000 us`); paired E-B `wrong_level_us` `96.0000+-0.0000`, **clear**, same sign on all 5 seeds (E loses; kept).
- Named alternative `lambda_per_us=0.0500` was printed on `isr_loaded_short` with the same seeds and not adopted (paired A-B `total_us@alt` `24.0000+-4.1833`, still clear).

## Post-first-run disclosures

There was no official toy or `expected/` change after the first run. Lesson prose (including the SimOutput embedding and the results / work-plan wording), hooks, curriculum, plans, sources, README typography and tip locks were written after those figures were frozen. `|m| <= sd` was wrapped in backticks in the first official en/zh draft so the less-than sign would not be parsed as a tag; official expected/ was not retuned. No lock relaxed. Existing `freertos_priority_toy.py`, `esp32_light_deep_sleep_toy.py`, and `web_servo.ino` / `angleToDuty()` and their `expected/` were not retuned or edited. The existing LEDC duty table, 14-bit overflow warning, sleep wording and FreeRTOS wording were left byte-untouched except the allowed one new Summary sentence and the new section immediately before `<Summary>`. Avoided hosts including `motors-drivers` and `arduino-io` were not reopened. `package.json` / lockfile, `.github/workflows`, and the authoritative proposal file were not edited.

## Mismatch with §9

None.

## Lock changes

New batch-29 PR2 block in `tools/check_diagrams.mjs` (toy, expected, CRN, label order, required `esp-idf-s3-rmt` addition, official symbol / encoder contract vs bit-bang stretch, sources, plans, README, declared regimes) plus `tools/test_b29p2_rmt_symbol_vs_bitbang_toy.py`. Tipped site-total, host-minute, month-total and Current-header locks only (45900→46080, M2 4110→4290, esp32 540→720, README `45 900`→`46 080`). Historical strings inside already-written plan/sources files were not edited, including `Current / 当前：**M2 4110 min**, Batch-24 PR2`. The b19p2 “last section before Summary” check for `esp32` was extended to allow the later RMT heading, in the same way the sensors-fusion check already allows the later Steinhart–Hart heading. The b29p1 live “did not jump to 46080” assertion against README / curriculum was moved onto the H1 sources note, which still records that fact. No lock relaxed.

- README `/45 900/` and `约 45 900 分钟` → `/46 080/` and `约 46 080 分钟`.
- Curriculum sum checks `45900` → `46080`; live M2 sum checks 4110→4290; live host-minute checks 540→720 on esp32.
- Current-curriculum month table: M2 4110→4290; other months unchanged.
