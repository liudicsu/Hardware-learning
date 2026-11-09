# Month 3 plan / 第 3 个月计划

Current / 当前：**M3 1620 min**, Batch-9 PR2. Earlier entries below retain their historical totals.

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
