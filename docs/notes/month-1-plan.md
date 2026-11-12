# Month 1 plan / 第 1 个月计划

Current / 当前：**M1 2910 min**, Batch-22 PR1. Earlier entries below retain their historical totals.

## Batch-22 PR1 / 本月 H1 (+180)

Base `5c0a2058860b3776983f1a4e19ef0ecf5cf51f0a` (batch-21 polish #188 merged; site **39060**). PR1 on M1 host: **M1 2730→2910 (+180)**; M3 moves in the same PR on its own plan. Site **39060→39420** (39420=39060+180+180), still 71 lessons.

- **H1 / 1.4 soldering: 270→450 (+180).** Crimp vs solder and strain relief (`crimp_vs_solder_strain_relief_toy.py`; common random numbers, 5 seeds; 19 strand fatigue factors and one contact factor per regime and seed, shared by all four arms). Wikipedia Crimp (joining) body read (rev 1380146082; 以原文为准): solderless, correctly sized barrel, gas-tight, no solder wicking, "mechanically stronger" (the article's claim, not a toy output). Declared toy parameters: 19 × 0.16 mm strands, ε = d/(2ρ), N = 2000·(0.02/ε)^2·z, SIGMA_LIFE=0.3, bend radius A 3.0 / B 6.0 / C 6.0 / D 12.0 mm, R_C0=0.50 milliohm, UNDER_X=3.0, FRET_PER_KCYCLE=0.5, OX_PER_KHOUR=0.5. Hand calc (printed): ε 0.0267 / 0.0133 / 0.0067, median life 1125.0000 / 4500.0000 / 18000.0000 cycles, 19/3=6.3333. flex (1500 cycles): B−A intact `16.2000±1.6432`, **clear**, 5/5; B−A life_half `3211.9624±284.6963`, clear, 5/5; C−D contact_mohm `2.1192±0.0670`, **clear**, 5/5 (under-crimp loses to the relieved solder joint, **kept**); C−D intact **tie**. light_flex (300 cycles): B−A intact **tie** (declared "may near-tie"). static (2000 h, no flex): B−A intact and contact **tie**; C−D contact_mohm `2.4243±0.1546`, clear, 5/5. Every pre-declared regime held. Alternatives (declared, same seeds): K_FAT=3.0 → B−A intact `18.6000±0.5477`; A ρ=4.0 mm → `3.4000±0.5477`; OX_PER_KHOUR=0.1 → C−D contact `1.2607±0.0804`; none adopted. No code change after the first run. ≠ thermal-window toy. Real crimp tool / IPC-A-610 本页未运行. / 压接与焊接、应力释放，不宣布压接钳实验。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

## Batch-21 PR1 / 本月 H1 (+180)

Base `b918527ab417d2fec73c736169bae90d1a773ae5` (batch-20 polish #184 merged; site **37980**). PR1 on M1 host: **M1 2550→2730 (+180)**; M3 moves in the same PR on its own plan. Site **37980→38340** (38340=37980+180+180), still 71 lessons.

- **H1 / 1.2 components: 900→1080 (+180).** Peukert rate-capacity vs the nameplate clock (`peukert_rate_capacity_toy.py`; common random numbers, 5 seeds; one shared k_true per regime and seed feeds a declared synthetic generator). Wikipedia Peukert's law body read (rev 1345423657; 以原文为准): t = H(C/(IH))^k, k = 1 means capacity independent of current, lead–acid k typically 1.1–1.3, limits (temperature not in the equation, k grows with age, self-discharge at low current, less capacity than fixed-k at very high current). Declared toy parameters: generator k_true U[1.15, 1.25] (lead–acid) and U[1.00, 1.03] (k≈1 pack), I_KNEE=50 A, GAMMA=0.25, D_DERATE=0.80, I_SD=0.05 A; rating 100 Ah / 20 h and K_DECL=1.2 from Wikipedia's worked example. Hand calc (printed): 100 Ah, 20 h, k=1.2, 10 A → 8.7055 h, 87.0551 Ah; rated 5 A → t=H=20.0000 h for any k. rated: A−B t and abs_err **tie** (identical on every seed), as declared. high: paired A−B abs_err `1.0280±0.2552`, **clear**, 5/5 (nameplate loses). very_high: B over-predicts on 5/5 (B err `0.0714±0.0417`); the pre-declared "B can lose to D" came out a **near-tie**, paired D−B abs_err `-0.0277±0.0757` (2 of 5 opposite sign), printed, not retuned. low: B predicts 158.4893 Ah from 100 Ah and over-predicts on 5/5; A−B abs_err `38.3430±39.5659` near-tie (not pre-declared). misapplied: paired A−B abs_err `-1.0787±0.1315`, **clear**, 5/5 — lead–acid k on a k≈1 pack loses, **kept**. Two code changes after the first run (identical-value sd shortcut; over/under-predict count lines), no label changed, disclosed on the page. ≠ C-rate quiz; ≠ power-battery-emc SoC derate. Real pack 本页未运行. / Peukert 放电率–容量与铭牌时钟。

**Allocation / 安排:** 30+30+50+40+30=180 minutes.

## Batch-19 PR1 / 本月 H1+H2 (+300)

Base `13471fe8c009af353b0f30abc99b6068154447aa` (batch-18 closed incl. polish #176; site **35820**). PR1 only on M1 hosts: **M1 2250→2550 (+300)**. Site **35820→36120**, still 71 lessons.

- **H1 / 1.3 bench-multimeter: 390→540 (+150).** True-RMS vs sine-calibrated average-responding vs peak/√2 sine assumption (`true_rms_vs_average_responding_toy.py`). Shared sampled waveforms (common random numbers, 5 seeds, phase; sine is clean, other waves have 1 mV rms noise). No integration step (finite sum over samples). sine: B−A **near-tie** `-6.112e-06±1.805e-05` (2 of 5 opposite sign) — §9 asked for tie / numerically-zero; the first accepted run is a near-tie because discrete mean(|sin|) is not exactly 2/π, reported honestly, not retuned. square: B−A `0.1107±8.278e-07`, **small but consistent**, 5/5 (hand-calc over-read `0.1107207345 V` / `11.0721 %`). triangle: B−A `-0.0220±2.386e-05`, **small but consistent**, 5/5. pwm_high_crest (D=0.0625, CF=4 > CF_CAP=3): B−A `-0.1793±0.0024`, **clear**, 5/5; C−A `0.4603±0.0053`, **clear**, 5/5; clipped true-RMS vs A `-0.0629±0.0027`, **clear**, 5/5. Alternatives CF_CAP=2.0 / 4.0 printed on the same seeds; no post-hoc retune. ≠ Kelvin; ≠ Thévenin. Real DMM 本页未运行. / 真有效值与平均值响应，不宣布万用表实验。

- **H2 / 1.2 components: 750→900 (+150).** Zener shunt vs LDO headroom (`zener_shunt_ldo_headroom_toy.py`). Shared Vin and load (common random numbers, 5 seeds). Declared toy parameters `HEADROOM=0.40 V` (not a datasheet dropout) and `P_THERMAL=0.50 W` with strict `P < P_THERMAL`. No integration step (DC solve). in_regulation: A−B Vout **near-tie** `-0.0233±0.0516 V` (2 of 5 opposite sign). below_headroom: A and B in_reg vs 1 is `-1.0000±0.0000`, **clear**, 5/5, **kept**. thermal_small_R (R=22 Ω sized for 200 mA): Zener thermal_ok vs 1 is `-1.0000±0.0000`, **clear**, 5/5, **kept**; light-load companion on the same R is `1.5368±0.0231 W`, also a clear miss. Uncapped shunt dissipation C−A `702.6763±8.8323 W`, **clear**, 5/5, **kept**. Hand calc `IR=0.0700000000 A`, `IZ=0.0500000000 A`, `PZ=0.2500000000 W`. Alternatives HEADROOM=0.20 V and P_THERMAL=0.80 W printed on the same seeds; no post-hoc retune. ≠ TVS; ≠ rectifier; ≠ Wheatstone. Real regulator bench 本页未运行. / 齐纳并联与 LDO 压差，不宣布稳压实验台。

**Allocation / 安排:** 30+30+40+30+20=150 minutes per host (300 total).

**Site accounting / 全站核算:** **36120=35820+300**; **M1=2550**, **71 lessons**.


## Batch-18 PR1 / 本月 H1 (+150)

Base `8462424` (batch-17 closed incl. polish #172; site **34710**). PR1 on M1 host: **M1 2100→2250 (+150)**; M3 moves in the same PR on its own plan. Site **34710→35040**, still 71 lessons.

- **H1 / 1.1 ohms-law: 240→390 (+150).** Superposition theorem vs a joint nodal solve vs a nonlinear element (`superposition_linear_circuit_toy.py`). Shared two-source linear net (`Vs1 = 5 V`, `R1 = 1000 Ω`, `Vs2 = 3 V`, `R2 = 2000 Ω`, `R3 = 4000 Ω`); arms A joint KCL / B sum of single-source responses / residual on a series diode + `Rf = 2000 Ω`. Common random numbers, 5 seeds (32 boards in the meter-noise regime). No integration step (DC nodal equation). linear_noiseless: A and B **tie** at `3.7142857143 V` (`26/7 V` by hand), identical on every seed; linear_meter (`σ = 0.001 V`): A−B **near-tie** `-0.0001±0.0003 V` (1 of 5 opposite sign); nonlinear_diode: residual vs 0 is `0.1750±0.0000 V`, **clear**, same sign on all 5 seeds. ≠ Thévenin; ≠ Wheatstone; ≠ rectifier. Real breadboard 本页未运行. / 叠加定理与非线性失效，不宣布面包板实验。

**Allocation / 安排:** 30+30+40+30+20=150 minutes.

**Site accounting / 全站核算:** **35040=34710+330** with M3 +180 on month-3-plan.md; **M1=2250**, **71 lessons**.


## Batch-16 PR1 / 本月 H1 (+150)

Base `c60dee9` (batch-15 closed incl. polish #164; site **32490**). PR1 only on M1 host: **M1 1950→2100 (+150)**; M3 moves in the same PR on its own plan. Site **32490→32820**, still 71 lessons.

- **H1 / 1.2 components: 600→750 (+150).** Bridge rectifier and ripple. Toy `bridge_rectifier_ripple_toy.py`: ideal 50 Hz source behind RS = 0.5 Ω, ideal diodes + series VF, forward Euler DT = 5 µs with DT ≤ 2/(1/(RS C) + 1/(R C)) asserted (tests at 0.98× / 1.02×); arms A half-wave + C / B bridge + C / C bridge without C; shared line amplitude, C, R and VF (common random numbers, 5 seeds). small_C_heavy: B−A ripple −5.2981±0.2119 V, clear, 5/5; medium: B−A ripple −2.3476±0.2445 V, clear, 5/5, law I/(2fC) within 25 % (0.76–0.78); large_C_light: B−A vdc −0.4146±0.0308 V, **small but consistent** (proposal expected near-tie; disclosed), ripple clear, both DC; tiny_C_heavy: all not DC; C_noC not DC everywhere and lowest peak diode current. ≠ Wheatstone (batch-11); ≠ TVS (batch-10). Real mains / PSU bench 本页未运行.

**Allocation / 安排:** 25+30+35+30+30=150 minutes.

**Site accounting / 全站核算:** **32820=32490+330** with M3 +180 on month-3-plan.md; **M1=2100**, **71 lessons**.

## Batch-15 PR1 / 本月 H1 (+150)

Base `df3c1d8` (batch-14 closed incl. polish #160; site **31380**). PR1 only on M1 host: **M1 1800→1950 (+150)**; M3 moves in the same PR on its own plan. Site **31380→31710**, still 71 lessons.

- **H1 / 1.5 python-terminal: 180→330 (+150).** Nyquist rate and aliasing. Toy `nyquist_aliasing_toy.py`: ideal impulse sampling + plain DFT over a 1 s record (closed-form samples, no time step); arms A 50 Hz / B 200 Hz with a 4th-order Butterworth prefilter (FC = 0.25 fs) / C 200 Hz raw; shared tones, phases and ADC noise (common random numbers, 5 seeds × 8 trials). single_tone: A−B freq 29.8500±0.3791 Hz, clear, 5/5, and C−B amp −8.1064±0.5337 (B loses amplitude to passband droop, clear, 5/5); interferer: C−B false peaks 0.9750±0.0559, clear, 5/5; near_edge: C−B amp −84.4824±1.3352 (B loses, clear, 5/5); slow_tone (added after the first run, disclosed): A−B freq and false peaks **tie** (identical on every seed). Real scope / ADC 本页未运行.

**Allocation / 安排:** 25+30+40+30+25=150 minutes.

**Site accounting / 全站核算:** **31710=31380+330** with M3 +180 on month-3-plan.md; **M1=1950**, **71 lessons**.

## Batch-14 PR1 / 本月 H1 (+150)

Base `db28b03` (batch-13 closed incl. polish #156; site **30270**). PR1 only on M1 host: **M1 1650→1800 (+150)**; M3 moves in the same PR on its own plan. Site **30270→30600**, still 71 lessons.

- **H1 / 1.3 bench-multimeter: 240→390 (+150).** Kelvin four-terminal sensing vs two-wire lead and contact resistance. Toy `kelvin_four_wire_sense_toy.py`: DC steady state (no time step), arms A two-wire / B Kelvin / C two-wire after a shorted-tip null; shared part, leads, contacts, lead warming, gain error, thermal EMF and noise (common random numbers, 5 seeds × 20 parts). shunt_small_dut: A−B abs 763.9274±61.6410 %, clear, 5/5; large_dut: A−B abs near-tie (2 of 5 opposite sign), bias 8 ppm clear; zero_lead: A and B **tie** (identical on every seed), C beats B by cancelling the thermal EMF (disclosed). ≠ Wheatstone (batch-11); ≠ Thévenin (batch-12); extends the GUM section that omits lead R. Real 4-wire bench 本页未运行.

**Allocation / 安排:** 25+30+40+30+25=150 minutes.

**Site accounting / 全站核算:** **30600=30270+330** with M3 +180 on month-3-plan.md; **M1=1800**, **71 lessons**.

## Batch-13 PR1 / 本月 H1 (+150)

Base `bc1e7ce` (batch-12 closed incl. polish #152; site **29160**). PR1 only on M1 host: **M1 1500→1650 (+150)**; M3 moves in the same PR on its own plan. Site **29160→29490**, still 71 lessons.

- **H1 / 1.4 soldering: 120→270 (+150).** Tip / pad thermal window: two-node lumped RC (tip regulated by a proportional heater, joint with contact conductance G_c cut by tip oxide, loss G_loss to the board), explicit Euler with DT = 1 ms < 2/λ_max = 0.458 s. Toy `soldering_thermal_window_toy.py`: arms differ only in dwell (1 s / 3 s / 8 s); shared pad heat capacity, pad loss, oxide, wetting time and adhesion budget (common random numbers, 5 seeds × 40 joints). heavy_pad_underheat: A−B cold-joint rate 0.7700±0.0737, clear, 5/5; small_pad_overheat: C−B pad lift 0.9750±0.0177, clear, 5/5; matched_clean: A and B **tie** on cold-joint and pad-lift rates (identical on every seed), dose differs. Reflow-profile reading (ramp / soak / TAL / peak; Wikipedia windows 以原文为准). ≠ cold-joint quiz prose; ≠ Wheatstone / Thévenin. Real iron / oven 本页未运行. / 焊点热窗口与回流曲线识读，不宣布实验台实验。

**Allocation / 安排:** 30+30+40+30+20=150 minutes.

**Site accounting / 全站核算:** **29490=29160+330** with M3 +180 on month-3-plan.md; **M1=1650**, **71 lessons**.

## Batch-12 PR1 / 本月 H1 (+150)

Base `a4b3b93` (batch-11 closed incl. polish #148; site **28050**). PR1 only on M1 host: **M1 1350→1500 (+150)**; M4 moves in the same PR on its own plan. Site **28050→28380**, still 71 lessons.

- **H1 / 1.1 ohms-law: 90→240 (+150).** Thévenin / Norton equivalent of the lesson's loaded divider (`Vth = 1.5986 V`, `Rth ≈ 3197 Ω`, `In = 0.5 mA`); shared parts and meter-noise draws (common random numbers, 5 seeds × 32 boards); arms Voc-only / Thévenin two-reading / Norton short-circuit with ammeter burden; heavy and lesson load Voc-only loses; light load (RL = 10 MΩ): B vs C **near-tie / small gap** (paired C−B 0.0004±0.0015 mV, within seed noise); A−B a **small but consistent gap, not a tie** (paired 0.1153±0.0588 mV). ≠ Wheatstone; ≠ multimeter open-circuit tip alone. Real bench lab 本页未运行. / 戴维南与诺顿等效，不宣布实验台实验。

**Allocation / 安排:** 30+30+40+30+20=150 minutes.

**Site accounting / 全站核算:** **28380=28050+330** with M4 +180 on month-4-plan.md; **M1=1500**, **71 lessons**.

## Batch-11 PR1 / 本月 H1 (+180)

Base `262adda` (batch-10 closed; site **26940**). PR1 only on M1 host: **M1 1170→1350 (+180)**; M3 moves in the same PR on its own plan. Site **26940→27270**, still 71 lessons.

- **H1 / 1.2 components: 420→600 (+180).** Wheatstone bridge + INA sense: shared ΔR/excitation; single-ended vs ideal bridge vs bridge+offset; small-δ noisy-CM bridge SNR win; large-δ quiet-CM single-ended tie; ≥5 seeds; ≠ ESD/ENOB. Real bridge 本页未运行. / 电桥与仪表放，不宣布应变片实验。

**Allocation / 安排:** 30+45+45+45+15=180 minutes.

**Site accounting / 全站核算:** **27270=26940+330** with M3 +150 on month-3-plan.md; **M1=1350**, **71 lessons**.

## Batch-10 PR2 / 本月 H3 (+150)

Base `59aa6df` (batch-10 PR1 merged; site **26160**). PR2 only on M1 host: **M1 1020→1170 (+150)**; M11 moves in the same PR on its own plan. Site **26160→26520**, still 71 lessons.

- **H3 / 1.2 components: 270→420 (+150).** ESD/TVS: shared HBM-style pulse (SSYA010A 100 pF/1500 Ω, I_sc≈V/1500 Ω); BE 1 ps / ≥5τ; unprotected vs connector-TVS vs series+IC-clamp; VRWM<VBR<VCLAMP (SLVAE37); ≥5 seeds; no IEC claim. ESD gun 本页未运行. / 钳位取舍，不宣布 IEC 合格。

**Allocation / 安排:** 30+30+45+30+15=150 minutes.

**Site accounting / 全站核算:** **26520=26160+360** with M11 +210 on month-11-plan.md; **M1=1170**, **71 lessons**.

Batch-6 PR1 only, base `073da37`: **M1 870→1020 min (+150)**, six lessons. / 本页只列第 1 月的宿主，保留六课。

## M1 host / 本月宿主

- **1.2 components: 120→270 (+150), H6.** Equal **10 µF** total capacitance in far-bulk / local-single / local-split / long-trace banks; series ESL+ESR+C plus shared placement L. Show mounted-path SRF, inductive high-frequency impedance and transient rail dip under the same pulse train. Local-split vs long-trace changes only placement; single vs split keeps total C and placement fixed. / 等总电容比较容量与放置；共享环路 L 不能除以电容数量，既有频域 SRF 也有时域放电 / 回充，不声称 FCC/CE 或熔断器认证。
- **150 min allocation:** 30 source/layout +30 impedance/SRF +30 shared-pulse simulation +45 equal-C controls/refinement +15 review. / 来源、推导、仿真、对照与复盘。

## Site accounting, not additional M1 lessons / 全站核算，不列为本月课程

M2 separately gains +330 (see month-2-plan.md); **21570=21090+150+330**, **M1=1020**, **M2=1980**, **71 lessons**. Other months unchanged; no PR2/PR3 minutes included. / 第 2 月新增另见其计划，不把外月宿主列在第 1 月标题下；无算术差异。

Both languages keep all new source/output/exercises before the final Summary. SN74HC14 PDF opened/curl200 for local-bypass advice; all RLC model inputs synthetic. Hardware/scope 本页未运行. / 双语同步，旧示例保留，真实测量未运行。
