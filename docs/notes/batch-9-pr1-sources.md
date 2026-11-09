# Batch-9 PR1 source, scope and validation audit

Base: 80ee63a61bf1dd7ea591862074db2b3064cbb92a (#136 polish merged; it changed no minutes, so the proposal's 7deb758 baseline of 24660 still holds). Proposal §9 PR1 locks: H1 2.4 PWM dead-time +180, H2 2.1 RS-485 termination +180. No arithmetic mismatch: curriculum.ts on 80ee63a gives M2 2310 (motors-drivers 540, arduino-io 300) and site 24660; after this PR M2 2310+180+180=2670 and site 24660+360=25020; 71 lessons. All 199 prior expected files remain byte-identical; two are added. README site copy updated 24 660 → 25 020.

## Opened sources (curl -L, 2026-11-09, Asia/Shanghai UTC+8)

- `esp-idf-mcpwm-deadtime`: https://docs.espressif.com/projects/esp-idf/en/v5.2/esp32/api-reference/peripherals/mcpwm.html, HTTP 200. Covers why dead time is needed (a MOSFET needs a small window to turn off), posedge/negedge_delay_ticks, and that zero bypasses the module.
- `wiki-h-bridge`: https://en.wikipedia.org/wiki/H-bridge, HTTP 200. Gives the shoot-through definition.
- `daido-deadtime-ieej`: https://www.jstage.jst.go.jp/article/ieejjia/8/1/8_41/_pdf, HTTP 200 PDF (IEEJ JIA 8(1) 41–50, DOI 10.1541/ieejjia.8.41). Covers the polarity-dependent output-voltage error, conventional feed-forward compensation, and parasitic-capacitance effects near zero current. Numbers are 以原文为准; parasitic capacitance is not modelled.
- `ti-slla272`: https://www.ti.com/lit/an/slla272/slla272.pdf, HTTP 200 PDF (Rev. D). Gives −7…+12 V common mode, 32 UL, 1.5 V / 54 Ω and 200 mV, 120 Ω at each end, the stub rule (Table 6-1: 7 ft at 100 ns), DE/RE contention and failsafe.
- `wiki-rs485`: https://en.wikipedia.org/wiki/RS-485, HTTP 200. Gives ±200 mV levels, line rather than star topology, and that unterminated reflections corrupt data.
- `arduino-uart-guide`: https://docs.arduino.cc/learn/communication/uart/, HTTP 200. The content was read from the site's page-data JSON (https://docs.arduino.cc/page-data/learn/communication/uart/page-data.json, HTTP 200): asynchronous, no shared clock, start/data/parity/stop frame.

The proposal's H1 list did not include a source for the volt-second formula, so the Daido & Hayashi paper was added after opening it. Tried for the same purpose but not cited:
- NXP AN4863 and AN1728 PDFs: HTTP 404 "Page not available" from the fetcher.
- Infineon AN205406: HTTP 200, but not needed.

## Toy design

- `pwm_deadtime_distortion_toy.py`: one synthetic half-bridge leg with an exact R-L solution per interval and a diode clamp, including the current stopping at zero during dead time.
  - Shared: 50 Hz reference, 24 V bus, 2 Ω / 2 mH load, 20 kHz centre-aligned carrier, and a ±10 % dead-time jitter stream over five seeds.
  - Arms: A ideal; B with 1 µs dead time; C with sign(i) feed-forward from a noisy current sample (σ 0.05 A), using nominal t_d and no extra V_dc.
  - Normal and light scenarios: C over-corrects at light load, and no winner is declared.
- `rs485_termination_toy.py`: a synthetic bounce lattice with a comparator and a UART 8N1 decoder.
  - Shared: 17 bytes, baud rate, ±5 V / 20 Ω / 100 ns driver, 120 m Z0 120 Ω trunk, and five common-mode/differential noise seeds.
  - Arms: terminated, unterminated, 15 m stub (deliberately breaks the SLLA272 rule), and single-ended on the same terminated trunk.
  - Rates are 1 Mbps and 125 kbps; termination costs idle drive current, and no winner is declared.
  - The DE/RE turnaround is covered in prose only.

Independent tests: tools/test_b9_deadtime_rs485_toys.py.

## Models / reproducibility

opencode free models were tried and then the work was implemented locally:
- deepseek-v4.1-flash-free and mimo-v2.6-flash-free returned no content within 40 s.
- glm-5.3-flash-free returned only an exact R-L step function, equivalent to the local one.
- LongCat/MiniMax free IDs were absent from `opencode models`.

Worktree /workspace/hl-b9p1; node_modules hardlinked via `cp -al`.

## Local validation

check_diagrams, check_widgets, check_wokwi, check_quotes, month 1–11 check.sh, lint, next typegen, tsc --noEmit, production build, independent tests. No workflow edits.
