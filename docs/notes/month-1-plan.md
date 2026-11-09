# Month 1 plan / 第 1 个月计划

Current / 当前：**M1 1350 min**, Batch-11 PR1. Earlier entries below retain their historical totals.

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
