# Month 3 plan / 第 3 个月计划

Current / 当前：**M3 2490 min**, Batch-15 PR1. Earlier entries below retain their historical totals.

## Batch-15 PR1 — notch filter on pid-control (+180)

Base `df3c1d8` (batch-14 closed incl. polish #160; site **31380**). PR1 on M3 host: **M3 2310→2490 (+180)**; M1 moves in the same PR on its own plan. Site **31380→31710**, still 71 lessons.

**H2 / 3.4 pid-control:** `pid-control` 360→**540**. Toy `notch_vs_lead_resonant_toy.py`: the lead–lag toy's LTI joint, arms A PID / B PID + notch (ω0 = 40 rad/s, ωc = 0.5 ω0) / C PID + lead–lag / D notch at 0.7 ω0; one recipe, shared 20 rad/s crossover, shared steps, loads and noise (common random numbers, 5 seeds); RK4 H = 0.25 ms with |R(Hλ)| ≤ 1 asserted (h_max 72.7 ms on the zr = 0.05 mode). well_damped: B−A ise 5.5960±1.4179 (B loses, clear, 5/5); resonant (zr 0.3): B−A ise 27.4063±6.9473 (B loses, clear, 5/5); resonant_light (zr 0.2): B GM 0.80→2.35 dB but B−A ise 7.5146±3.5371 (small but consistent loss, 5/5); resonant_sharp (zr 0.05, picked after a margins-only prototype; zr 0.1 margins also printed): A, C, D diverge 5/5, B stable (PM 38.3°, GM 2.03 dB). ≠ lead–lag redo; ≠ Smith; ≠ discrete LQR. Real servo / modal test 本页未运行.

**Allocation / 安排:** 30+40+40+40+30=180 minutes.

**Site accounting / 全站核算:** **31710=31380+330** with M1 +150 on month-1-plan.md; **M3=2490**, **71 lessons**.

## Batch-14 PR1 — pressure advance corner toy on fdm-printing (+180)

Base `db28b03` (batch-13 closed incl. polish #156; site **30270**). PR1 on M3 host: **M3 2130→2310 (+180)**; M1 moves in the same PR on its own plan. Site **30270→30600**, still 71 lessons.

**H2 / 3.2 fdm-printing:** `fdm-printing` 180→**360**. Toy `pressure_advance_corner_toy.py`: 1-D compressible-melt stand-in ds/dt = feed − q(s), q ∝ s^(1/n); arms K = 0 / tower-tuned K / 3 × tuned K; shared K_true, n, tower reading error and filament-diameter sequence (common random numbers, 5 seeds); explicit Euler DT = 0.1 ms with DT × λ_max < 2 asserted (λ_max 25.84 1/s → 77.41 ms). sharp_corner: A−B bulge 165.9007±18.7792, clear, 5/5; C−B starve 89.2661±10.3383, clear, 5/5; steady_straight: all arms **tie** (identical on every seed). ≠ snap_fit; not Marlin / Klipper planner. Real printer 本页未运行.

**Allocation / 安排:** 30+30+40+40+40=180 minutes.

**Site accounting / 全站核算:** **30600=30270+330** with M1 +150 on month-1-plan.md; **M3=2310**, **71 lessons**.

## Batch-13 PR1 — lead–lag compensation on pid-control (+180)

Base `bc1e7ce` (batch-12 closed; site **29160**). PR1 on M3 host: **M3 1950→2130 (+180)**; M1 moves in the same PR on its own plan. Site **29160→29490**, still 71 lessons.

**H2 / 3.4 pid-control:** `pid-control` 180→**360**. Toy `lead_lag_vs_pid_toy.py`: joint 1/(s(TM s+1)) with an optional compliant mode; PID / PID + lead–lag (φ = 30° at WC = 20 rad/s, lag z2 = 2, p2 = 0.667 rad/s) / swapped lead pole–zero; one recipe, Kc set for |L(j·WC)| = 1 on every arm; shared steps, load torques and sensor noise (common random numbers, 5 seeds); RK4 H = 0.25 ms with |R(Hλ)| ≤ 1 checked. resonant (wr = 40, zr = 0.3): B−A ISE −2.8025±0.6749, small but consistent, 5/5, but GM 3.00→2.01 dB; well_damped: B−A ISE +0.7150±0.1951, small but consistent loss, 5/5; resonant_light (zr = 0.2): B diverges 5/5 (PM −16.3°). ≠ Smith; ≠ notch; ≠ discrete LQR. Real motor bench 本页未运行.

**Allocation / 安排:** 30+40+40+40+30=180 minutes.

**Site accounting / 全站核算:** **29490=29160+330** with M1 +150 on month-1-plan.md; **M3=2130**, **71 lessons**.

## Batch-11 PR2 — load-dependent gear η on transmissions (+180)

Base `014a8ba` (batch-11 PR1 merged; site **27270**). PR2 on M3 host: **M3 1770→1950 (+180)**; M5 moves in the same PR on its own plan. Site **27270→27630**, still 71 lessons.

**Host / 宿主:** `transmissions` 330→**510**. Toy `gear_efficiency_load_toy.py`: shared τ–ω / ratio / friction CRN; constant η vs Coulomb+viscous vs heavy-fit η; heavy-load near-tie; light-load gap; ≠ backlash-in-loop.

**Allocation / 安排:** 30+30+45+45+30=180 minutes.

**Site accounting / 全站核算:** **27630=27270+360** with M5 +180 on month-5-plan.md; **M3=1950**, **71 lessons**.


## Batch-11 PR1 / 本月 H2 (+150)

Base `262adda` (batch-10 closed; site **26940**). PR1 only on M3 host: **M3 1620→1770 (+150)**; M1 moves in the same PR on its own plan. Site **26940→27270**, still 71 lessons.

- **H2 / 3.1 cad-parametric: 150→300 (+150).** GD&T bilateral / stack-up: shared chain; worst-case vs RSS vs datum re-root; short-chain exact tie; skewed MC shows RSS unsafe; ≥5 seeds; no ASME certification. CMM 本页未运行. / 公差累积，不宣布 ASME 认证。

**Allocation / 安排:** 30+30+45+30+15=150 minutes.

**Site accounting / 全站核算:** **27270=26940+330** with M1 +180 on month-1-plan.md; **M3=1770**, **71 lessons**.

Batch-5 PR1, base39215d6: six lessons retained, **1290→1470 min (+180)**. Only `transmissions` deepened; other lesson minutes unchanged. / 保留六课，只深化 `transmissions`，其余课时不变。

- M1 bench-multimeter:90→240; synthetic specs, rectangular limit/√3, sensitivity-weighted RSS vs linear limits. / 合成规格、矩形限值除 √3、带灵敏度系数的 RSS 与线性限值。
- M2 sensors-fusion:210→360; declared Q/R,9-candidate equal budgets,separate tuning/held-out seeds,no bias oracle. / 声明 Q/R、等9候选预算、调参 / 留出分离、不提供真零偏。
- M3 transmissions:150→330; physical friction+I ablation,sensor-information disclosure,deadband residual/mis-set bands. / 物理摩擦加积分消融、传感器信息披露、死区残差及设错误差带。

This PR only: **19830+180+150+150=20310**,71 lessons; M1=870,M2=1650,M3=1470. Do not substitute batch-final M5/M9/M10 totals. / 本 PR 仅更新前三月，不提前计入本批后续 PR。

All new prose/code/stdout/exercises precede final bilingual Summary. Existing examples/expected retained; hardware 本页未运行. / 新增内容置于最终双语 Summary 前，旧示例输出不变。

## Batch-9 PR2 / 本月 H3 (+150)

Base `159f6ff` (Batch-9 PR1 merged). PR2 only: **M3 1470→1620 (+150)** and M9 **3270→3480 (+210**, own host in month-9-plan.md); site **25020→25380**, still 71 lessons; no arithmetic mismatch with proposal §9 or curriculum.ts. M6/M11 move only in PR3.

- **H3 / 3.5 so101-arm: 240→390 (+150).** Absolute vs incremental encoders at power-on: shared true angle, glitches, unpowered drift and read noise over five seeds; A single-turn absolute, B incremental trusted, C incremental + homing (time cost only), D multi-turn with battery-backed count (flat battery alarms and homes). Single-turn joint vs three-turn shaft vs flat battery; single-turn ambiguity across turns; no winner. Z-index homing stays in 2.4 `encoder_index_cal_toy.py` (referenced, not re-implemented). XL330 e-Manual numbers 以原文为准; real servos 本页未运行. / 掉电后绝对式与增量式、多圈回绕，不宣布赢家。

**Allocation / 安排:** 30+30+45+30+15=150 minutes. Sources: batch-9-pr2-sources.md.
