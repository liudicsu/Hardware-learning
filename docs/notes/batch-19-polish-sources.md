# Batch-19 polish sources — authors, ESP32 vs ESP32-S3, UM10204 / ESP-IDF I²C, PSRR, Zener slope, ac+dc true-RMS

Base: `0f3b2541f10579cf8d0e05dcb94208ea86c33c77` (batch-19 PR3 #179 merged; site **36900**, catalogue **71**).
This PR: site stays **36900**, catalogue stays **71**; **no minute count changed** (curriculum, month plans and README untouched for minutes).
Head of this branch is recorded at open time in the PR; locks check this note, not a later SHA.

## Sources opened and read (bodies)

All fetched with curl on 2026-11-12 (UTC+8) and read in full where quoted (PDFs via `pdftotext -layout`).

| id | URL | rev | HTTP | What was used |
|---|---|---|---|---|
| arXiv 2510.13778 (abs + export API) | https://arxiv.org/abs/2510.13778 | v1 listing | 200 | Title "InternVLA-M1: A Spatially Guided Vision-Language-Action Framework for Generalist Robot Policy"; **29** authors in this order: Xinyi Chen, Yilun Chen, Yanwei Fu, Ning Gao, Jiaya Jia, Weiyang Jin, Hao Li, Yao Mu, Jiangmiao Pang, Yu Qiao, Yang Tian, Bin Wang, Bolun Wang, Fangjing Wang, Hanqing Wang, Tai Wang, Ziqin Wang, Xueyuan Wei, Chao Wu, Shuai Yang, Jinhui Ye, Junqiu Yu, Jia Zeng, Jingjing Zhang, Jinyu Zhang, Shi Zhang, Feng Zheng, Bowen Zhou, Yangkun Zhu. The abs page `citation_author` tags and the export API agree, and match the reviewer's list exactly. |
| arXiv 2504.19854 (abs + export API) | https://arxiv.org/abs/2504.19854 | v1 listing | 200 | Title "NORA: A Small Open-Sourced Generalist Vision Language Action Model for Embodied Tasks"; **8** authors: Chia-Yu Hung, Qi Sun, Pengfei Hong, Amir Zadeh, Chuan Li, U-Xuan Tan, Navonil Majumder, Soujanya Poria (matches the reviewer's list). |
| esp32-s3-datasheet | https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf | Datasheet v2.2 | 200 | §4 power modes: four modes, Active, Modem-sleep, Light-sleep, Deep-sleep (the word "Hibernation" does not occur in the document). Table 5-10 typ: Light-sleep **240 µA** (VDD_SPI and Wi-Fi powered down, all GPIOs high-impedance; PSRAM extra); ULP-FSM 170 µA, ULP-RISC-V 190 µA; Deep-sleep ULP sensor-monitored 18 µA, RTC memory + RTC peripherals powered up **8 µA**, RTC memory only **7 µA**; power off 1 µA. |
| esp32-datasheet | https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf | Datasheet v5.3 | 200 | Table 4-2: Light-sleep **0.8 mA**; Deep-sleep ULP powered up 150 µA, ULP sensor-monitored 100 µA at 1 % duty, RTC timer + RTC memory **10 µA**; **Hibernation** (RTC timer only) **5 µA**; power off 1 µA. The PR2 toy's I_LIGHT = 0.80 mA and I_DEEP = 0.01 mA equal the classic Light-sleep and RTC-timer+memory Deep-sleep typicals. |
| idf-sleep-modes (stable) | https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/sleep_modes.html | stable docs | 200 | Second half of the Wi-Fi passage: "If Wi-Fi/Bluetooth connections need to be maintained, enable Wi-Fi/Bluetooth Modem-sleep mode and automatic Light-sleep feature (see Power Management APIs). This allows the system to wake up from sleep automatically when required by the Wi-Fi/Bluetooth driver, thereby maintaining the connection." Still no sleep-current table. |
| idf-i2c | https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/i2c.html (also the `esp32s3` path) | stable docs | 200 | `i2c_device_config_t::scl_wait_us`: SCL await time in µs, should not be very small because slave stretch can be long ("possible even stretch for 12 ms"), 0 = default register value; example `.scl_wait_us = 20000`. `xfer_timeout_ms` on `i2c_master_transmit` / `receive` / `transmit_receive` / `probe`: -1 waits forever, `ESP_ERR_TIMEOUT` when exceeded. ESP32 page: "The ESP32 I2C controller does not support clock stretching when operating as a slave." The ESP32-S3 page has no such sentence and documents `i2c_slave_stretch_callback_t`. |
| nxp-um10204 | https://www.nxp.com/docs/en/user-guide/UM10204.pdf | Rev. 7.0, 1 October 2021 | nxp.com: Access Denied (HTML); body read from https://www.pololu.com/file/0J435/UM10204.pdf (200, same PDF, Rev. 7.0) | §3.1.9 Clock stretching: pauses a transaction by holding SCL LOW until released HIGH; optional, most targets have no SCL driver and cannot stretch; byte level (hold SCL LOW after receiving and acknowledging a byte, controller waits) and bit level (extend each clock LOW period); Hs-mode byte level only. Table 3 note [2]: if no target can stretch, the controller need not handle it. Table 11 Standard-mode: t_LOW ≥ 4.7 µs, t_HIGH ≥ 4.0 µs. Replaces Wikipedia as the primary I²C source; Wikipedia kept as secondary. |
| wiki-ldo (re-read) | https://en.wikipedia.org/wiki/Low-dropout_regulator | 1378921240 | 200 | Filtering section: error amplifier limited at high frequencies; most LDOs have relatively high PSRR at lower frequencies (10 Hz – 1 kHz); PSRR fluctuates over frequency, temperature, current, output voltage and voltage differential. |
| ti-slaa414 | https://www.ti.com/lit/an/slaa414a/slaa414a.pdf | SLAA414A, rev. August 2017 | 200 | PSRR = 20 log(ripple input / ripple output), over a wide frequency range (10 Hz to 1 MHz is common); "Historically LDOs have poor high frequency PSRR performance". |
| onsemi-hbd854 | https://www.onsemi.com/pub/Collateral/HBD854-D.PDF | HBD854/D Rev. 1 | 200 | Zener impedance Z_Z = incremental ΔV/ΔI on the breakdown plateau, specified for most zeners; shunt-regulator eq. (10): ΔV_O = ΔV_I / (1 + R_S/R_Z + R_S/R_L) − (R_S R_Z / (R_S + R_Z)) ΔI_L + TC ΔT V_Z — the load term is a slope. |
| fluke-truerms-facts | https://www.fluke.com/en-gb/learn/blog/digital-multimeters/facts-about-true-rms-measurement | page as served 2026-11-12 | 200 | Most DMMs measure ac-coupled true-RMS and reject DC; a few (Fluke 189) offer ac+dc; ac+dc = √(ac² + dc²) from two readings. |
| keysight-ac-errors | https://keysight.zinfi.net/concierge/OEMs/keysight/wwwcontent/Attachments/pdf/5988-5513.pdf | app note 5988-5513 | 200 | AC functions measure ac-coupled true RMS (DC rejected); sine / triangle / square: ac-coupled = ac+dc (no DC offset); pulse trains contain DC. |

Not used: TI / ADI true-RMS converter datasheets (AD737 / AD8436 fetch timed out), Nexperia BZX79 datasheet (HTML block page), the Fluke "What is true-RMS" blog (no ac/ac+dc statement in its body), Wikipedia Zener diode and True RMS converter (no dynamic-resistance / coupling statement). No board, analyser or meter was run: 本页未运行.

## Item by item

1. **InternVLA-M1 authors** (m6/vla-models en/zh): the surname-only list is replaced by all 29 full names in arXiv order; `resources.ts` already carried the full list (unchanged). "appended" → "prepended or appended" in the lesson intro (en/zh), both resource summaries (en/zh), the curriculum objective (en/zh) and the toy docstring (output unchanged, `cmp`).
2. **NORA authors** (m8/async-deployment en/zh): all 8 full names in arXiv order; resources already full (unchanged).
3. **PSRR** (m1/components en/zh): headroom is not filtering; PSRR falls with frequency (Wikipedia LDO 以原文为准; TI SLAA414A 以文档为准). The DC toy does not model PSRR.
4. **ESP32 vs ESP32-S3** (m2/esp32 en/zh): classic values (0.8 mA, 10 µA, Hibernation 5 µA) vs S3 values (240 µA, 8 / 7 µA, no separate Hibernation), 以文档为准. Toy numbers **not** changed; I_LIGHT / I_DEEP now labelled toy parameters modelled on classic ESP32 (prose, Summary, curriculum objective). Reviewer's "about 240 µA light, 7–8 µA deep, no separate Hibernation" is confirmed by the S3 datasheet v2.2.
5. **Modem-sleep + automatic Light-sleep** keeps the connection (m2/esp32 en/zh, curriculum objective), 以文档为准; not modelled.
6. **UM10204 primary, ESP-IDF I²C** (m2/sensors-fusion en/zh): UM10204 §3.1.9 / Table 3 / Table 11; `scl_wait_us`, `xfer_timeout_ms`, classic ESP32 slave cannot stretch, 以文档为准. Wikipedia kept as secondary. TIMEOUT_US = 200.0 us stays a declared toy parameter (not an ESP-IDF default).
7. **Optional, both done**: ac-coupled vs ac+dc true-RMS (m1/bench-multimeter en/zh; Fluke + Keysight) — the toy's arm A is the ac+dc value; its unipolar pwm_high_crest has DC, so an ac-coupled meter would read lower there (direction only, no new number); Zener dynamic impedance makes load regulation a slope (m1/components en/zh; onsemi HBD854).

Reviewer nits:

- NORA toy: `fmt6()` (decimal ROUND_HALF_UP) for the bin-width line, so 2/256 = 0.0078125 (hand calculation, exact) prints **0.007813** (was round-half-even 0.007812); half a bin stays 0.003906. Only that line of `examples/month-8/expected/nora_fastplus_small_vla_toy.txt` changed; reruns byte-identical. Hand-calc text updated in en/zh worked example, the embedded stdout and code blocks, and `batch-19-pr3-sources.md`.
- Curriculum InternVLA objective: "prepended or appended" (en) / "在指令前或后附加" (zh).
- Lesson pages now disclose the post-first-run code changes (en/zh): InternVLA toy — arXiv id on the first line (and the polish docstring edit); NORA toy — cosine-table / result-table cache (`cmp`-identical) and arXiv id on the first line, plus the polish rounding change. The similar existing disclosure for the batch-19 PR2 ESP32 toy (`simulate()` latency 0.0 when no event is served, `cmp`-identical) is also now on the esp32 page.

## Toys

No new toy, no regime or parameter change. Only `nora_fastplus_small_vla_toy.py` output changed (one line). Every number added to prose is either a document value marked 以文档为准 / 以原文为准, or already printed in `expected/`. No difference direction changed.

## opencode

Tried free models in order with a 90 s timeout, on a narrow sub-task (the half-up `fmt6` helper): DeepSeek (`opencode/deepseek-v4.1-flash-free`) exit 0, wrote `fmt6.py` (correct, printed 0.007813) — **used**, adapted into the NORA toy; GLM (`opencode/glm-5.3-flash-free`) exit 0; MiMo (`opencode/mimo-v2.6-flash-free`) exit 0; LongCat (`opencode/longcat-2.5-free`) exit 124 (timeout); MiniMax (`opencode/minimax-m3.1-flash-free`) exit 0. All prose, resources and locks were written locally.

## Lock changes

New batch-19 polish block only (tightening): full author lists in en/zh, "prepended or appended", 0.007813 printed and on the pages (0.007812 gone), code-change disclosures on the pages, ESP32 vs S3 values and labels, Modem-sleep passage, UM10204 / ESP-IDF I²C statements and resources, PSRR / Zener slope / ac+dc notes, this note, totals 71 / 36900 unchanged. No lock relaxed; no existing lock edited.
