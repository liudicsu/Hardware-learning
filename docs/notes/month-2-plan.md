# Month 2 plan / 第 2 个月计划

Current / 当前：**M2 3570 min**, Batch-21 PR2. Earlier entries below retain their historical totals.

## Batch-21 PR2 / 本月 H4 (+180)

Base `33a4a703eced7372f71e0decc6b733655ee1cbb4` (batch-21 PR1 #185 merged; site **38340**). PR2 on M2 host: **M2 3390→3570 (+180)**; M4 moves in the same PR on its own plan. Site **38340→38700** (38700=38340+180+180), still 71 lessons.

- **H4 / 2.6 first-robots: 240→420 (+180).** Madgwick vs the lesson's complementary filter on the balancer pitch (`madgwick_vs_complementary_balancer_toy.py`; common random numbers, 5 seeds; shared initial pitch, gyro bias and every noise sample). Madgwick 2010 internal report body read from the Wayback PDF (以报告为准); the captcha-gated live x-io link is not cited. Arms A gyro only / B complementary τ = 0.5 s / C Madgwick β = 0.033 (the report's IMU value) / D Madgwick β = 0.5. static: A−B end_err `35.5376±23.4941`, **clear**, 5/5; the declared B vs C near-tie did **not** hold — C−B rmse `0.2661±0.2218`, **clear**, 5/5 (C loses); D−B rmse `0.1542±0.1725` **near-tie**. slow_tilt: A−B rmse `8.4331±7.2937` clear; C−B rmse `0.2049±0.2241` **near-tie** (held). accelerate: D−B rmse `0.7386±0.0326`, **small but consistent**, 5/5 (declared loss held, kept); C−B rmse `-2.9664±0.3624`, **clear**, 5/5 (not pre-declared); A−B rmse `1.0716±2.8608` near-tie, A−B end_err `7.6907±4.8046` clear. Alternatives τ = 0.25 / 1.0 s, β_high = 0.1 / 0.2, β_low = 0.1 printed; none replaced the defaults. No code change after the first run. Real MPU-6050 本页未运行.

**Allocation / 安排:** 30+30+50+40+30=180 minutes.

## Batch-19 PR2 / 本月 H3+H4 (+360)

Base `37181b1f9c6c64acdea478415ea7febdefc6e92d` (batch-19 PR1 #177 merged; site **36120**). PR2 only on M2 hosts: **M2 3030→3390 (+360)**. Site **36120→36480**, still 71 lessons.

- **H3 / 2.3 esp32: 360→540 (+180).** Always-on vs Light-sleep vs Deep-sleep on a shared event timeline (`esp32_light_deep_sleep_toy.py`; common random numbers, 5 seeds). Declared toy currents I_ACTIVE=40.0 mA, I_LIGHT=0.80 mA, I_DEEP=0.01 mA, I_BOOT=50.0 mA and wake costs T_WAKE_LIGHT=0.001 s, T_BOOT_DEEP=0.300 s — not datasheet values; the ESP-IDF Sleep Modes body gives no current table or wake latency. Hand calc (printed): C<A iff g>0.4250 s, C<B iff g>18.9839 s (strict). long_idle: paired C−A `-39.7086±0.0026`, **clear**, 5/5; paired C−B `-0.5417±0.0023`, **clear**, 5/5. high_wake_rate (mean gap 0.25 s): paired C−B `21.1306±0.2356`, **clear**, 5/5 — Deep-sleep loses to Light-sleep, **kept**; the pre-declared possible loss vs A did not occur: paired C−A `-9.9044±0.2135`, **clear**, 5/5, printed as it came out, not retuned. missed_wake_source (digital-only GPIO): paired C−B missed `122.0000±10.3199`, **clear**, 5/5, **kept**. Alternatives I_BOOT=40.0 mA (C−A `-14.2824±0.1689`) and T_BOOT_DEEP=0.100 s (C−A `-20.2624±0.0965`) printed on the same seeds; no post-hoc retune. ≠ ADC section; ≠ FreeRTOS toy. Real ESP32 本页未运行. / 休眠能耗账，玩具电流不是数据手册数值。

- **H4 / 2.5 sensors-fusion: 720→900 (+180).** I²C clock stretching (`i2c_clock_stretch_toy.py`; common random numbers, 5 seeds, 20×16 bytes per seed). Controller ignores SCL vs waits for SCL high vs waits with TIMEOUT_US=200.0 us (toy, strict `stretch > TIMEOUT_US` aborts). no_stretch: every paired line **tie: identical on every seed**. moderate_stretch: paired A−B bad_rate `0.8681±0.0111`, **clear**, 5/5; paired B−A bus_ms `12.0501±0.1307`, **clear**, 5/5; C−B tie. overtime_stretch: paired C−B bad_rate `0.9375±0.0000`, **clear**, 5/5, **kept**; paired B−A bus_ms `135.1400±0.7771`. Alternatives TIMEOUT_US=1000.0 (C−B tie on overtime) and 50.0 (C−B `0.7800±0.0216` on moderate) printed on the same seeds; no post-hoc retune. Ideal edges; ≠ I²C rise-time SI (arduino-io); ≠ scanner; ≠ RS-485. Real bus / analyser 本页未运行. / 时钟拉伸流控，不是上升时间。

**Allocation / 安排:** 30+30+50+40+30=180 minutes per host (360 total).

**Site accounting / 全站核算:** **36480=36120+360**; **M2=3390**, **71 lessons**.


## Batch-10 PR1 / 本月 H1 + H2 (+360)

Base `73add87` (batch 9 closed incl. polish #140; site **25800**). PR1 only: **M2 2670→3030 (+360)**, site **25800→26160**, still 71 lessons; no arithmetic mismatch with proposal §0.5/§9 or curriculum.ts. M1/M11 move only in PR2, M10/M9 only in PR3.

- **H1 / 2.1 arduino-io: 480→660 (+180).** ADC ENOB from SINAD: ENOB=(SINAD−1.76)/6.02; shared tone/aperture; ideal quantizer vs +noise vs +distortion; ≥5 seeds; ≠ DMM GUM; ≠ ideal 10-bit formula alone. Real ADC lab 本页未运行. / 有效位账，不宣布芯片手册 ENOB。
- **H2 / 2.5 sensors-fusion: 540→720 (+180).** Mag hard-iron bias + soft-iron stretch; shared field/path; raw vs hard-only vs hard+soft; heading / residual metrics; ≥5 seeds; ≠ KF/complementary. Mag hardware 本页未运行. / 硬铁圆心、软铁拉伸，不是 AHRS 认证。

**Allocation / 安排:** H1 30+45+45+45+15=180; H2 30+45+45+45+15=180 minutes.

**Site accounting / 全站核算:** **26160=25800+360**, **M2=3030**, **71 lessons**. Other months unchanged this PR.



Batch-6 PR1 only, base `073da37`: **M2 1650→1980 min (+330)**, six lessons. / 本页只列第 2 月宿主，保留六课。

- **H3 / 2.4 motors-drivers: 360→540 (+180).** R(T)=R20[1+0.00393(T−20)] with α at 20 °C; explicit I²R(T) positive feedback at fixed current. Steady ΔT=P·Rθ vs short t≪τ rise P·t/Cθ. Shared demand; ignore/monitor/derate-and-trip; real derate trips, no insulation or package-rating claim. / 温度参考一致，区分稳态与短时热响应，理想绕组温度信息明示。
- **H4 / 2.1 arduino-io: 150→300 (+150).** Same bytes/Rp/C model; TI SLVA689A Table 2-1 gives Sm/Fm/Fm+ t_r maxima **1000/300/120 ns**, all three screened. Generic rise-only tests are separate from the Fm 400 kHz trace and TMP102 device limits. Original button quiz remains. / 三种上升限制均检查，不把上升筛查当整条链路合规或实测丢包。

**Allocation / 安排:** H3 45+45+45+30+15=180; H4 30+30+30+45+15=150 minutes.

**Site accounting / 全站核算:** M1 separately gains +150 (month-1-plan.md); **21570=21090+180+150+150**, **M1=1020**, **M2=1980**, **71 lessons**. Other months unchanged; no PR2/PR3 minutes. / 仅计本 PR，无算术差异。

New en/zh material and expected outputs precede final Summary; stdlib only; hardware/scope 本页未运行. TI SLVA505, SLVA689A and TMP102 were opened/curl200; no unopened NXP attribution. / 不冒认未打开来源或实测。

## Batch-7 PR1 / 本月 H1 + H2 (+330)

2.5 sensors-fusion360→540 (+180), 2.2 timing-interrupts180→330 (+150). **M2 1980→2310**, six lessons. Site **22350→22830**, counting only PR1 +480; M8 **3030→3180** (+150, own host in month-8-plan.md). No arithmetic mismatch; still71 lessons.

H1:45+45+45+30+15=180 min for modes/edge traces/bit order+CS/toy/exercises. H2:30+30+45+30+15=150 min for opened registers/independent counter/progress vsISR/generic window/exercises. Shared deterministic input cases; no stochastic seeds needed. New full code/stdout/exercises before final Summary, bilingual added summary sentence. Existing KF, I2C timing and software command watchdog unchanged. Sources: batch-7-pr1-sources.md.

## Batch-9 PR1 / 本月 H1 + H2 (+360)

Base `80ee63a` (batch 8 closed; the polish PR #136 changed no minutes, so the proposal's `7deb758` baseline still holds). PR1 only: **M2 2310→2670 (+360)**, site **24660→25020**, still 71 lessons; no arithmetic mismatch with proposal §0.5/§9 or curriculum.ts. M3/M9 move only in PR2, M6/M11 only in PR3.

- **H1 / 2.4 motors-drivers: 540→720 (+180).** PWM dead time: ΔV ≈ −sign(i)·t_d/T_s·V_dc (0.480 V at 1 µs/20 kHz/24 V); shared reference/V_dc/load/carrier/jitter; A ideal, B dead time, C sign(i) feed-forward (no extra V_dc). Normal vs light load; compensator over-corrects at light load; no winner. ≠ FOC (11.2), ≠ winding thermal, ≠ shoot-through prose only. Real bridge 本页未运行. / 死区伏秒账，轻载过补偿，不宣布赢家。
- **H2 / 2.1 arduino-io: 300→480 (+180).** RS-485 differential pair: Γ, 120 Ω at both trunk ends, SLLA272 stub rule, single-ended common-mode failure, DE/RE turnaround (reading only). Shared 17 bytes, baud, driver, trunk and five noise seeds; 1 Mbps vs 125 kbps; termination costs idle drive. ≠ UART baud garbage, ≠ CAN TEC/REC, ≠ CRC, ≠ Modbus. TDR/transceiver 本页未运行. / 端接与支线取舍，不宣布赢家。

**Allocation / 安排:** H1 45+45+45+30+15=180; H2 30+45+45+45+15=180 minutes.
