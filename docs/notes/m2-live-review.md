# Month 2 live review (2026-10-22)

Scope: the 6 Month 2 lessons plus the Month 2 overview, zh and en, on the deployed site
(https://liudicsu.github.io/Hardware-learning/, deploy of main 560908b), each at 390 px and 1280 px:
12 lesson pages × 2 widths = 24 lesson page views, plus 4 overview views. Already confirmed earlier and not redone:
first-robots (new paragraphs, Summary), the esp32 divider ratios and margins, and the timing-interrupts SREG order
and 16K CK ≈ 1.0 ms wake-up. The verified key facts in issue #48 were taken as given.

## Method

- Browser: headless Chrome (playwright-core) against the live site. For every page view: HTTP status of the page,
  every response ≥ 400, console errors and uncaught page errors, horizontal overflow
  (`documentElement.scrollWidth > innerWidth`), and the smallest rendered text (HTML computed font size; SVG `<text>`
  font size × screen scale, the same rule as tools/check_text_size.mjs).
- Glossary: at 1280 px every inline term (`<Term>`) was clicked open and the links in its popover collected. Every
  in-site link on the pages and in the popovers was then requested on the live site.
- firstExplained: a script walked the curriculum in order and, for every term used in Month 2, compared the
  glossary's `lesson` with the first lesson that wraps the term, and checked whether that lesson actually explains it.
- Content: every sentence with a number and unit in the six en lessons was checked against the datasheet or by
  recomputing it; zh and en were compared number by number (outside code blocks).

## Results: technical checks

| Page | zh 390 | zh 1280 | en 390 | en 1280 | Terms (per locale) |
|---|---|---|---|---|---|
| month-2 overview | OK | OK | OK | OK | 0 |
| arduino-io | OK | OK | OK | OK | 8 |
| timing-interrupts | OK | OK | OK | OK | 6 |
| esp32 | OK | OK | OK | OK | 5 |
| motors-drivers | OK | OK | OK | OK | 7 |
| sensors-fusion | OK | OK | OK | OK | 7 |
| first-robots | OK | OK | OK | OK | 4 |

OK means all of these held: HTTP 200, no response ≥ 400, 0 console errors, no horizontal overflow, smallest text
12.0 px. Links: 46 unique in-site targets from the pages and their 37 + 37 term popovers. All carry
`/Hardware-learning` and all return 200 (this confirms the #49 fix on the live site). Every popover has its
lesson link and glossary link.

Embedded simulators: Wokwi appears only as link cards (no iframe). The first pass did not scroll through each page,
and the Falstad iframes are mounted only when they scroll near the viewport, so their console errors were not
counted then. A second pass (live site, deploy of 23ea9f0, 1280 px) scrolled every Month 2 lesson from top to bottom,
zh and en, and waited 2.5 s: the four lessons with Falstad circuits (arduino-io, esp32, motors-drivers,
sensors-fusion) loaded all their iframes, with 0 console errors, 0 page errors and 0 responses ≥ 400.

## Results: glossary and firstExplained

All 35 terms used in Month 2 point to the first lesson that wraps them, and zh and en wrap the same terms in
every lesson. Problems found, all fixed in this PR:

- `adc` pointed to Month 1 ohms-law, which only names the ADC ("an ADC that accepts only 5 V"). The ADC is
  explained in arduino-io ("Analog input: the ADC": 10 bits, 0–1023, 104 µs per conversion). Now
  `lesson: "arduino-io", firstExplained: true`.
- `pwm` pointed to Month 1 components, which only mentions it ("ramp PWM from zero"). arduino-io's section "PWM:
  analogWrite is not analog" explains it. Now `lesson: "arduino-io", firstExplained: true`.
- `pull-up-pull-down`: components explains both pull-up and pull-down (10 kΩ, active low), so the entry is now
  marked `firstExplained: true`.
- `low-high-pass-filter`: a beginner first meets "low-pass filter" in arduino-io (the RC filter that averages
  PWM), but the term was only wrapped in sensors-fusion. arduino-io now wraps that first use (zh and en). The
  glossary's related lesson stays sensors-fusion, which explains both filter types in the complementary filter.
- Left as is: `bit-byte-hex` is assigned to arduino-io but no lesson wraps it. Hexadecimal is worked through on
  the math reference page (`/math#hex`, linked from sensors-fusion). The term only appears on /glossary. Wrapping
  it is a content decision for the Month 1/2 polish and is not needed for correctness.
  TODO: wrap the first use of bit-byte-hex in lesson text (zh and en) and mark it firstExplained.

## Results: content and facts

arduino-io:
- Checked: ATmega328P internal pull-up 20–50 kΩ; ADC 13 ADC clocks per conversion (25 for the first) at
  16 MHz / 128 = 125 kHz → 104 µs; PWM about 490 Hz on pins 3, 9, 10, 11 and about 980 Hz on 5, 6
  (250 kHz / 510 and / 256); 20 mA recommended and 40 mA absolute maximum per pin; 3.3 V pin 50 mA (Uno Rev3
  spec); 0.5 KB bootloader; 64-byte serial TX buffer; 10 bits / 115200 baud = 86.8 µs per character; 220 Ω red
  LED 13.6 mA; quiz arithmetic.
- Fixed: the 1023 vs 1024 paragraph said the divisor is 1023 "because the Arduino convention maps the maximum
  code 1023 exactly to the full-scale voltage", as if this were the converter's definition. The datasheet's ADC
  Conversion Result section defines ADC = V_IN × 1024 / V_REF (code 0x3FF is V_REF minus one LSB). The paragraph
  now states the datasheet formula, says the course follows Arduino's 1023 convention so the top code reads 5.00 V,
  and gives the 0.1 % difference (zh and en).

timing-interrupts (SREG and 16K CK already confirmed):
- Checked: Timer0 prescaler 64 → 1.024 ms overflow, first correction on the 42nd overflow (42 × 24 µs ≥ 1 ms) at
  43.008 ms, about 23.4 corrections per second, `micros()` 4 µs; 2^32 ms = 49.71 days; wrap example
  296 + 200 = 496 ms; interrupt latency 4 + 3 + 30 + 9 = 46 cycles ≈ 2.9 µs (issue #48: 2.875 µs).

esp32 (divider already confirmed):
- Checked against the ESP32-S3 datasheet v2.2 and module datasheet: 512 KB SRAM (C3 400 KB, classic 520 KB),
  240 MHz (15× the Uno, 256× its RAM), VIH = 0.75 × 3.3 V = 2.475 V, absolute maximum about 3.6 V; strapping
  GPIO 0, 3, 45, 46; USB 19/20; UART0 43/44; flash/PSRAM 26–32 and 35–37 with octal PSRAM; JTAG 39–42; ADC1 GPIO
  1–10, ADC2 11–20. Classic ESP32: flash GPIO 6–11, input-only 34–39, strapping 0, 2, 5, 12, 15, ADC1 GPIO
  32–39. LEDC: 1.0/1.25/1.5/1.75/2.0 ms at 50 Hz and 14 bits → 819, 1024, 1228, 1433, 1638.
  Correction (fix PR after 23ea9f0): this line first said 1023 and was marked Checked, but the lesson's formula
  used 2^bits − 1. ESP-IDF's LEDC driver uses duty / 2^bits with duty from 0 to 2^bits
  (components/esp_driver_ledc/include/driver/ledc.h, e.g. ledc_set_duty: "the range of duty setting is [0,
  (2**duty_resolution)]", checked at espressif/esp-idf caaa5e1, and docs/en/api-reference/peripherals/ledc.rst. The
  same LEDC docs warn that on the ESP32-S3, whose timers are at most 14 bits (soc_caps.h SOC_LEDC_TIMER_BIT_WIDTH),
  a timer at its maximum resolution cannot take duty 2^bits; Arduino-ESP32's ledcWrite() in esp32-hal-ledc.c,
  checked at 8667595, rewrites duty >= 2^bits − 1 to 2^bits, so 16383 hits this too), so 1.25 ms is
  0.0625 × 16384 = 1024. The lesson, curriculum, glossary and web_servo.ino now use 2^bits.

motors-drivers:
- Checked: Romi 120:1 (Pololu #1520) 130 mA free run and 1.25 A stall at 4.5 V (R = 3.6 Ω, as in #48);
  12 CPR × 120 = 1440 counts per wheel turn, 0.25° per count; 8.4 / 7.4 = 1.135 (about 14 % faster); TB6612FNG
  1.0 A per channel, 1.2 A absolute maximum, 2 A for 20 ms pulses, VM up to 13.5 V (as in #48); A4988
  I_max = Vref / (8 × R_CS) with 0.068 Ω (since 2017) or 0.050 Ω; stepper 1.8° → 200 steps.
- Changed (fix PR after 23ea9f0): "the DRV8833 also gives about 1.2 A per channel" now says that 1.2 A is Pololu's
  continuous rating for its carrier (#2130); TI's datasheet (SLVSAR1E) rates 1.5 A RMS (2 A peak) per H-bridge
  only for the PWP and RTY packages, at VM = 5 V and 25 °C (its recommended-operating table lists 1.5 A for RTY at
  VM = 5 V), and 500 mA RMS (2 A peak) for the PW package. Pololu measured that 1.2–1.3 A is what the chip
  sustains without thermal shutdown. "About 1.2 A" is the realistic number for a beginner, and the lesson still
  tells readers to check their own breakout.

sensors-fusion:
- Checked against the MPU-6000/6050 register map and product specification: address 0x68 (0x69 with AD0 high),
  PWR_MGMT_1 = 0x6B resets to 0x40 (sleep bit 6), ACCEL_XOUT_H = 0x3B, 14-byte burst, ±2 g → 16384 LSB/g,
  ±250 °/s → 131 LSB/(°/s); I2C 100/400 kHz and 4.7–10 kΩ pull-ups; ultrasonic 0.0343 cm/µs; drift
  1.5 °/s × 60 s = 90°; complementary filter τ = α·dt/(1−α) = 0.49 s and dt/(−ln α) = 0.495 s, steady offset
  bias × τ = 0.735° (issue #48).

first-robots: already confirmed (issue #48), not redone.

zh/en parity: outside code blocks every number in each en lesson also appears in the zh lesson. The only
differences are numbers written out as words in en ("five thousand", "42nd", "eight or sixteen").

## Also fixed in this PR (reviewer follow-up on #46)

- m6 act-diffusion quiz q1: the explanation derived the mean from the fork's 4.16 cm step (−1.66 cm) and called it
  "the −0.017 m the averaging policy actually takes". multimodal.py does not print that value: its table only counts
  the averaging policy's 200 moves at (0, 0.23), all in the −3 to −1 cm bin. The explanation now gives each value
  with the place it is taken. At the fork itself, (0, 0.2), each step is 4.16 cm sideways, so 7 left and 3 right
  average to −1.66 cm. Just past the fork, at (0, 0.23), the recorded steps are 4.3 to 4.4 cm and the policy's
  actual move is −1.74 cm. That figure was recomputed from the 10 nearest frames of the 40 Random(5) demos: mean
  (−1.738, +2.461) cm. This matches the wording of the sentence above the fork table. A stray leading space in
  en.mdx was removed.
- curriculum.ts, act-diffusion "run" task: "check it against the −0.017 m it prints" now has the reader work out
  −1.66 cm at the fork by hand, then run a one-line command that prints the averaging policy's move at (0, 0.23)
  and confirm it is −1.74 cm, the value in the Quiz q1 explanation (zh and en). tools/check_diagrams.mjs binds both
  quotes and Quiz q1 to act-fork.json's mean.

## Retest after 23ea9f0 (2026-10-22)

tools/check_text_size.mjs was re-run against the deployed site (deploy of main 23ea9f0, CI-built export) at 390 px
and 1280 px: 156 pages, 0 problems (no text under 12 px, no horizontal overflow).

## Review follow-up after 6be12b3

- esp32 ADC range: ESP-IDF's ADC docs give no S3 range of their own (they point to the datasheet; the 2800 mV limit
  in adc_calibration.rst is for the ESP32-C2 only). The 0–3100 mV figure for ADC_11db on the ESP32-S3 is from the
  Arduino-ESP32 ADC documentation (docs/en/api/adc.rst, checked at 0b70aff), so the lesson now cites that.
  The lesson names the setting as 12 dB (ADC_ATTEN_DB_12 in ESP-IDF 5.x, ADC_11db in Arduino), cites the
  datasheet's 2.9 V calibrated limit and says readings above 2.9 V are unreliable.
- esp32 LEDC: the lesson, glossary and web_servo.ino no longer say 16384 is fully high at 14 bits. Duty is
  generally 0 to 2^bits, but the ESP32-S3 (14-bit timers) cannot take 2^bits at its maximum resolution (ESP-IDF
  LEDC docs warning), and Arduino's ledcWrite() maps 16383 to 16384, so a 100 % output needs 13 bits or fewer. The
  servo uses 5–10 % duty and is unaffected. The angle -> duty table and its steps are now bound to angleToDuty()
  in tools/check_diagrams.mjs (mutation-tested: 1024 -> 1023 in the table fails).
- next.config.ts: CI="false" no longer switches on the Pages export; only CI=1 or CI=true does.
