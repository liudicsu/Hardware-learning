# Month 6 examples: robot learning, specialisation & getting hired / 第 6 个月示例

Standard-library Python: toy models with fixed seeds (lessons 1-4) and a README checker (lesson 5); no packages and no hardware needed.
只用 Python 标准库：固定随机种子的玩具模型（第 1–4 课）和一个 README 检查器（第 5 课）；不需要安装包，也不需要硬件。

```bash
examples/month-6/check.sh            # re-run every example and compare with expected/
UPDATE=1 examples/month-6/check.sh   # rewrite expected/ after an intentional change
```

| lesson | folder | program |
|---|---|---|
| 1. Imitation learning I: behaviour cloning and DAgger | `behaviour-cloning/` | `bc_reach.py` |
| 2. Imitation learning II: multimodal demos, ACT and diffusion policy | `act-diffusion/` | `multimodal.py` |
| 3. VLA models: action tokens and open weights | `vla-models/` | `action_tokens.py`, `vla_async_chunk_toy.py` |
| 4. Evaluating a policy: intervals, paired trials, failure analysis | `policy-evaluation/` | `eval_report.py`, `hi_robot_hierarchical_feedback_toy.py` |
| 5. Choosing a specialisation, the portfolio and getting hired | `specialisation-portfolio/` | `portfolio_check.py` |

Plan: `docs/notes/month-6-plan.md`.

## Hi Robot hierarchical feedback (`hi_robot_hierarchical_feedback_toy.py`)

```bash
python3 examples/month-6/policy-evaluation/hi_robot_hierarchical_feedback_toy.py
```

Stdlib only. A Hi Robot-style hierarchical stand-in on shared table scenes: a flat policy vs a hierarchy that consumes mid-task feedback vs a hierarchy that ignores it; instruction accuracy and task progress over five seeds with common random numbers. Paper IA/TP figures 以论文为准; real robots / GPT-4o 本页未运行.
只用标准库。共享桌面场景上的 Hi Robot 风格分层替身：比较扁平策略、吸收中途反馈的分层、以及忽略反馈的分层；5 个种子、共用随机数，报告指令准确率和任务进度。论文 IA/TP 数字以论文为准；真机 / GPT-4o 本页未运行。
