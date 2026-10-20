# Lesson 2: imitation learning II, multimodal demos, ACT and diffusion / 第 2 课：模仿学习（二），多模态示范、ACT 与扩散策略

`multimodal.py` uses only the Python standard library and fixed seeds. A point gripper must pass a 0.3 m block; the
expert goes round it on the left or the right, 50/50, after a straight lead-in to a fork at (0, 0.2). Every policy
looks at the 10 recorded frames nearest the current position and differs only in what it does with them: average
their actions (what a squared-error network learns), sample one, play an action chunk of 4, 8 or 16 steps from one,
or run 20-step DDPM sampling with the exact denoiser of those frames (what a diffusion policy's network approximates).
`multimodal.py` 只用 Python 标准库并固定随机种子。点状夹爪要绕过一个 0.3 m 的方块；专家先直行到 (0, 0.2) 的岔口，再以
50/50 的概率从左或从右绕过。每个策略都看离当前位置最近的 10 个录制帧，只在“怎么用它们”上不同：取动作均值（平方误差网络
学到的东西）、随机采一个、从其中一个播放 4、8 或 16 步的动作块，或者用这些帧的精确去噪器做 20 步 DDPM 采样（扩散策略的
网络所逼近的东西）。

```bash
python3 multimodal.py
```

No hardware needed. Output quoted in the lesson as **simulated output / 仿真输出**; checked by
`examples/month-6/check.sh` against `examples/month-6/expected/multimodal.txt`.
不需要硬件。课程中以“仿真输出”引用；由 `examples/month-6/check.sh` 与 `examples/month-6/expected/multimodal.txt` 比对。
