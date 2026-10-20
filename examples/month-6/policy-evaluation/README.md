# Lesson 4: evaluating a policy / 第 4 课：评估一个策略

`eval_report.py` uses only the Python standard library and imports the corridor task, expert and nearest-neighbour
policies from `../behaviour-cloning/bc_reach.py`. It prints Wilson 95 % intervals for lesson 1's success counts,
ten 10-trial sessions of the same policy, a paired comparison of two policies over the same 100 per-trial seeds
with McNemar's exact test, the trials needed to tell two success rates apart, and a failure table.
`eval_report.py` 只用 Python 标准库，并从 `../behaviour-cloning/bc_reach.py` 导入走廊任务、专家和最近邻策略。它输出第 1 课
成功次数的 Wilson 95 % 区间、同一策略的十组 10 次试验、两个策略在同样 100 个逐次种子上的配对比较（McNemar 精确检验）、
区分两个成功率所需的试验次数，以及失败分类表。

```bash
python3 eval_report.py
```

No hardware needed. Output quoted in the lesson as **simulated output / 仿真输出**; checked by
`examples/month-6/check.sh` against `examples/month-6/expected/eval_report.txt`.
不需要硬件。课程中以“仿真输出”引用；由 `examples/month-6/check.sh` 与 `examples/month-6/expected/eval_report.txt` 比对。
