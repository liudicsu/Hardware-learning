# Batch-6 PR1 source audit / 来源核对

Opened PDF bodies with `curl -fL` + `pdftotext -layout`; source GET status rechecked at 2026-11-06 09:54 Asia/Shanghai (UTC+8). / 已下载 PDF 正文并转文字阅读，再 GET 核对状态。

| Source | URL | GET | SHA-256 of opened PDF |
|---|---|---|---|
| SLVA505 | [https://www.ti.com/lit/an/slva505/slva505.pdf](https://www.ti.com/lit/an/slva505/slva505.pdf) | 200 | `5c1991a3228d27021ca665466a10f5bfd582014379a50cd9457b7d71b70fe53c` |
| SLVA689 | [https://www.ti.com/lit/an/slva689/slva689.pdf](https://www.ti.com/lit/an/slva689/slva689.pdf) | 200 | `84da7d3745364e881a72914ca609e93132c356dcc0a0461de483fa27a8669e7b` |
| TMP102 SBOS397I | [https://www.ti.com/lit/ds/symlink/tmp102.pdf](https://www.ti.com/lit/ds/symlink/tmp102.pdf) | 200 | `c9da6620ef95f75ce94372f670a84d168e05922dd32cebfaa6517083f15ebfaf` |
| SN74HC14 SCLS085L | [https://www.ti.com/lit/ds/symlink/sn74hc14.pdf](https://www.ti.com/lit/ds/symlink/sn74hc14.pdf) | 200 | `24911ae018ad9bf6f8f069158b8689d0d941e3cde9f48924e2421276ae10e397` |

- **SLVA505:** package / PCB thermal-rating context only, not a winding Rθ/Cθ identification. All winding plant/control values are lesson-defined synthetic inputs. / 仅封装散热阅读，不把 θJA 当绕组热阻。
- **SLVA689A:** reopened and curl-verified HTTP 200 for the NEEDS_FIX: Table 2-1 explicitly gives Sm 1000 ns / Fm 300 ns / Fm+ 120 ns maximum t_r. RC waveform and 30 %–70 % rise factor 0.8473; Rp minimum from `(VCC−VOLmax)/IOL`, maximum from rise-time / bus C. / 上升沿与电阻范围公式。
- **TMP102 SBOS397I:** opened Timing Requirements: Fast-mode max SCL 0.4 MHz, clock rise max 300 ns, low min 1300 ns, high min 600 ns; electrical output low 0.4 V max at 3 mA with V+ above 2 V. The toy explicitly ASSUMES every other transmitter/master supports this sink budget. It is not a TMP102 transaction. / 真手册时序；其他参与者能力仍须另外核对。
- **SN74HC14 SCLS085L:** opened Power Supply Recommendations: 0.1 µF bypass per VCC, as close to supply pin as possible, mentions parallel 1 µF. Does not supply the toy's loop L, pulse slew or rail result. / 真手册去耦建议；模型 L / 电流 / 电压均合成。

No hardware measurements; 本页未运行. No NXP UM10204 claim: that PDF remains unresolved/not used. No insulation/FCC/CE/fuse certification. / 不冒认未打开的资料或实测 / 认证。

## Reviewed model corrections / 复审模型修正

- Winding resistance uses **R20 at 20 °C** with **α20=0.00393/K**, and explicitly teaches I²R(T) positive feedback, steady ΔT=P·Rθ and short-pulse P·t/Cθ. / 温度参考一致。
- The decoupling toy is now a **series ESL+ESR+C circuit** with shared source impedance and a separate placement loop L; all banks have 10 µF total, and intrinsic and mounted SRFs, frequency impedance and pulse voltage are evaluated. All part/parasitic/source values are synthetic. / 旧 L-only 模型已替换，不冒认器件实测值。
- The three generic I2C rise-limit screens do not establish frequency, high-time, sink or device-mode compliance. No TMP102 Fm+ claim. / 只作上升时间筛查，不声称整机链路符合所有模式。

## Batch-6 polish follow-up

- 2026-11-06 11:02:08 Asia/Shanghai (UTC+8): TI SLVA689 URL above reopened, curl HTTP200; SLVA689A Table2-1 still states1000/300/120 ns. Download SHA256 `84da7d3745364e881a72914ca609e93132c356dcc0a0461de483fa27a8669e7b`. UM10204 remained unresolved during the original batch source check, so the lessons/resource metadata explicitly identify TI SLVA689A as the substitute. No claim that UM10204 is nonexistent.
- Constant-current algebra verified with ΔT=T−Ta and R(Ta)=R20[1+α(Ta−20)]: Cθ·dΔT/dt=I²R(Ta)−(1/Rθ−I²αR20)ΔT. The supplied stable-rise formula needs no correction. At/above threshold there is no finite **physical** steady state reached by heating from ambient (R(Ta)>0); an above-threshold negative-R formal root is not a physical equilibrium. I_crit=7.975790 A for the synthetic values; not a motor rating. Regression tests cover below/equal/above threshold and preserve the existing thermal arm results.
- Polish only: site22350 minutes unchanged; no workflow edits. Paper Hz/success-rate figures are explicitly reading comparisons only in both languages.
