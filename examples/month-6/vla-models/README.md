# Lesson 3: VLA models, action tokens / 第 3 课：VLA 模型与动作词元

`action_tokens.py` uses only the Python standard library and fixed seeds. It builds a dataset shaped like SO-101
teleoperation (50 episodes of 6 joint targets in degrees at 30 Hz, synthetic) and tokenises a 1 s chunk from a new
episode two ways: OpenVLA-style 256 bins per dimension between the 1st and 99th percentile, and a DCT of each
joint over the chunk, scaled and rounded (the idea behind FAST; FAST's byte-pair encoding step is left out and the
nonzero coefficients are counted instead).
`action_tokens.py` 只用 Python 标准库并固定随机种子。它生成一个形状类似 SO-101 遥操作的合成数据集（50 个回合，6 个关节
目标，单位度，30 Hz），用两种方法给一个新回合里 1 秒的动作块分词：RT-2/OpenVLA 式在第 1 与第 99 百分位数之间每维 256
个区间，以及对每个关节做 DCT 再缩放取整（FAST 的思路；省略了 FAST 的字节对编码，改为统计非零系数个数）。

```bash
python3 action_tokens.py
```

No hardware needed. Output quoted in the lesson as **simulated output / 仿真输出**; checked by
`examples/month-6/check.sh` against `examples/month-6/expected/action_tokens.txt`.
不需要硬件。课程中以“仿真输出”引用；由 `examples/month-6/check.sh` 与 `examples/month-6/expected/action_tokens.txt` 比对。
