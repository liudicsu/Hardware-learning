# Month 2 plan / 第 2 个月计划

Batch-6 PR1 only, base `073da37`: six lessons retained, **1650→1980 min**. / 仅计本 PR，保留六课，不提前加入 PR2 / PR3。

- **H3 / 2.4 motors-drivers: 360→540 (+180)** — winding copper loss + lesson-defined Rθ/Cθ, same current request, ignore / monitor / derate-and-trip; report physical peak, copper energy, trips. Ideal winding T is disclosed; derate actually trips. Not harness I²R or driver-package θJA. / 绕组铜耗和热 RC；共享请求电流，忽略 / 监测 / 降额并跳闸，理想绕组温度信息明示，不混同线束或驱动封装。
- **H4 / 2.1 arduino-io: 150→300 (+150)** — shared bytes, synthetic Rp/Cbus, 30 %–70 % rise vs bit/high budgets and sink current. Real TMP102 + TI pull-up PDFs opened; retain button quiz. / 共享字节与合成 Rp/Cbus；真实数据手册时序，预算标志不是丢包，保留按键小测。
- **H6 / 1.2 components: 120→270 (+150)** — shared current pulses, far bulk / local ceramic-short / long trace; L·di/dt ONLY, min rail and dip. SN74HC14 local-bypass source opened; L/current values synthetic. / 共享电流脉冲，远端 bulk / 本地陶瓷短回路 / 长走线；只算电感边沿，不模拟电荷网络或声称 FCC/CE。

**Arithmetic / 算术：** 21090+180+150+150=**21570**; M1=870+150=**1020**; M2=1650+180+150=**1980**. No mismatch; catalogue **71** lessons. All other months unchanged (M8 2670, M9 2730, M10 1860); do not substitute batch-final totals. / 无差异，其余月份不变。

**Work allocation / 课时安排：** H3 45+45+45+30+15=180; H4 30+30+30+45+15=150; H6 30+30+30+45+15=150 minutes. Source reading, derivation, execution and sensitivity are explicitly included, not just script runtime. / 包含阅读、推导、运行、敏感性分析与复盘，不把脚本耗时当课时。

All additions, full toy source, stdout and exercises precede final en/zh Summary; add one summary sentence per lesson. Stdlib only; new expected outputs plus harness hooks; old expected outputs untouched. Real hardware/scope **本页未运行**. / 双语同步，新增内容在最终 Summary 前，旧输出不变。

Sources curl200 and opened: TI SLVA505, SLVA689, TMP102 SBOS397I, SN74HC14 SCLS085L. NXP UM10204 remains unresolved/not used. / 本 PR 不冒认未打开的来源。
