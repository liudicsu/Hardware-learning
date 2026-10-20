# Lesson 5: choosing a specialisation, the portfolio and getting hired / 第 5 课：选择方向、作品集与求职

`portfolio_check.py` (Python standard library only) reads a project's `README.md` and reports which of eight parts a
reviewer looks for are present: a video, a results table, the number of trials, a failure analysis, how to
reproduce it, the hardware, what you built yourself, and limitations or next steps. It checks by simple text rules,
so it can tell you a part is missing but not whether it is good.
`portfolio_check.py`（只用 Python 标准库）读取项目的 `README.md`，报告评审关注的八个部分是否齐全：视频、结果表、
试验次数、失败分析、复现方法、硬件、你自己做了什么、局限或下一步。它按简单的文本规则检查，只能告诉你缺了什么，
不能判断写得好不好。

```bash
python3 portfolio_check.py samples/arm-pick-place samples/line-follower
python3 portfolio_check.py ~/my-project          # your own project
```

`samples/arm-pick-place/` is an example of the format; its numbers are illustrative, not a real result.
`samples/arm-pick-place/` 只是格式示例，其中的数字是示意，不是真实结果。
This is an ordinary program, not a simulation; checked by `examples/month-6/check.sh` against
`examples/month-6/expected/portfolio_check.txt`. 这是普通程序，不是仿真；由 `examples/month-6/check.sh` 比对。
