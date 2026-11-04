# Failure table template / 失败表模板

Fill one row per failure mode you care about for a long-horizon skill sequence.
长时程技能序列里，每种你在意的失败模式填一行。

| Failure mode / 失败模式 | Detect signal / 检测信号 | Recover action / 恢复动作 | Notes / 备注 |
| --- | --- | --- | --- |
| Grasp closed on empty air / 闭合抓空 | Gripper width ≈ open after close; vision “object missing” / 闭合后开口仍≈张开；视觉“物体不见了” | Retry grasp ≤2, then backup grasp pose / 重试抓取≤2，再换备用抓取位 | Semantic skill failure — not a command timeout / 语义技能失败，不是指令超时 |
| Object slipped in lift / 抬起时滑落 | Sudden Present Load drop; wrist camera empty / Present Load 骤降；腕相机空 | Abort lift, re-detect, re-grasp / 中止抬起，重检测再抓 | Pair with Month 8 soft limits / 配合第 8 个月软限位 |
| Nav goal blocked / 导航目标被挡 | Nav2 BT recovery exhausted / Nav2 行为树恢复用尽 | Replan via Fallback skill; ask for human help / Fallback 换技能；或请求人工 | Cross-link Month 4 slam-nav recoveries / 交叉链接第 4 个月 slam-nav |
| LLM proposed unknown skill / LLM 提议未知技能 | Skill name ∉ skill table / 技能名不在技能表 | Reject; re-prompt with table constraint / 拒绝；用技能表约束重提示 | Month 9.4 SayCan-style filter / 第 9.4 课 SayCan 式过滤 |
| Contact load spike / 接触负载尖峰 | Present Load ≥ threshold (duty-cycle %, not N) / Present Load ≥ 阈值（占空比%，非牛顿） | Admittance retreat / hold; do not raise position gain / 导纳回退/保持；勿加大位置增益 | Month 9.3; no invented overload trip numbers / 第 9.3 课；不编造过载切断数 |

Watchdog (Month 8) covers **command timeout / illegal command**. This table covers **skill-semantic** failures after a command was accepted.
看门狗（第 8 个月）管**指令超时/非法指令**；本表管指令已被接受后的**技能语义**失败。
