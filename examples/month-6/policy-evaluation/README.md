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

## Enrichment: eval seed layers (`eval_seed_layers_toy.py`) / 深化：评估种子分层

```bash
python3 examples/month-6/policy-evaluation/eval_seed_layers_toy.py
# also hooked in examples/month-6/check.sh
```

`synthetic_policy_draw_k` are scripted policies, not real training. `shared_IC` and `independent_IC` in separate tables; Wilson/Beta count intervals ≠ across-draw dispersion; best-seed vs median. Checklist → arXiv 2409.09491v2 §4. Real training 本页未运行.
`synthetic_policy_draw_k` 是脚本化策略，不是真训练。`shared_IC` 与 `independent_IC` 分表；Wilson/Beta 计数区间 ≠ 跨 draw 离散；best-seed 对 median。清单 → arXiv 2409.09491v2 §4。真训练本页未运行。
