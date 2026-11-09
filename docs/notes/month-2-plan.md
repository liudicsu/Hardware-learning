# Month 2 plan / 第 2 个月计划

Current / 当前：**M2 3030 min**, Batch-10 PR1. Earlier entries below retain their historical totals.

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
