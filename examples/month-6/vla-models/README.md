# Lesson 3: VLA models, action tokens / 第 3 课：VLA 模型与动作词元

`action_tokens.py` uses only the Python standard library and fixed seeds. It builds a dataset shaped like SO-101
teleoperation (50 episodes of 6 joint targets in degrees at 30 Hz, synthetic) and tokenises a 1 s chunk from a new
episode two ways: OpenVLA-style 256 bins per dimension between the 1st and 99th percentile, and a DCT of each
joint over the chunk, scaled and rounded (the idea behind FAST; FAST's byte-pair encoding step is left out and the
nonzero coefficients are counted instead).
`action_tokens.py` 只用 Python 标准库并固定随机种子。它生成一个形状类似 SO-101 遥操作的合成数据集（50 个回合，6 个关节
目标，单位度，30 Hz），用两种方法给一个新回合里 1 秒的动作块分词：OpenVLA 式在第 1 与第 99 百分位数之间每维 256
个区间，以及对每个关节做 DCT 再缩放取整（FAST 的思路；省略了 FAST 的字节对编码，改为统计非零系数个数）。

```bash
python3 action_tokens.py
```

No hardware needed. Output quoted in the lesson as **simulated output / 仿真输出**; checked by
`examples/month-6/check.sh` against `examples/month-6/expected/action_tokens.txt`.
不需要硬件。课程中以“仿真输出”引用；由 `examples/month-6/check.sh` 与 `examples/month-6/expected/action_tokens.txt` 比对。

## Enrichment / 深化

`vla_async_chunk_toy.py`: sync vs async action-chunk inference in the style of SmolVLA's RobotClient (arXiv 2506.01844, §3.3): request the next chunk when the remaining queue fraction falls below g. All arms share the chunk predictor, n = 50, the latency draws and the target path; it reports idle_s, infer_calls, underruns, action staleness and overlapping-chunk switches. Fixed seed; checked by `examples/month-6/check.sh`. SmolVLA weights, a GPU server and a real arm are not run here; paper numbers are per the paper. Not RTC (10.2), not timestamp sync (8.3).
仿 SmolVLA RobotClient 的同步/异步动作块推理玩具：队列剩余比例低于 g 时请求下一块。所有臂共享预测器、n = 50、延迟抽样和目标轨迹；输出空闲时间、推理次数、欠载、动作陈旧度与重叠块切换。固定种子；由 `examples/month-6/check.sh` 核对。SmolVLA 权重、GPU 服务器与真机本页未运行；论文数字以论文为准。不是 RTC（10.2），也不是时间戳同步（8.3）。

```bash
python3 vla_async_chunk_toy.py
```

## cot_vla_subgoal_toy.py

CoT-VLA-style visual chain of thought (arXiv 2503.22020, Eq. 2–3): count-table policies on a 1-D track compare a direct chunk policy, a subgoal refreshed every chunk and a stale subgoal; four regimes (multi-stage with and without videos, action-rich, single reach), five seeds, common random numbers; tokens are counted at the paper's sizes (7 per action, 256 per subgoal image). No time-step integration. Checked by `examples/month-6/check.sh`. CoT-VLA weights and a GPU are not run here; paper numbers are per the paper. Not DreamGen, TraceVLA or MAP-VLA.
CoT-VLA 式视觉思维链（arXiv 2503.22020 式 2–3）：在一维轨道上用计数表比较直接动作块策略、每块刷新的子目标和过时的子目标；四种情形（有 / 无视频的多阶段、动作示范充足、单次到达），5 个种子，共用随机数；词元按论文尺寸计数（每个动作 7 个、每张子目标图像 256 个）。没有时间步积分。由 `examples/month-6/check.sh` 核对。CoT-VLA 权重与 GPU 本页未运行；论文数字以论文为准。不是 DreamGen、TraceVLA 或 MAP-VLA。

```bash
python3 cot_vla_subgoal_toy.py
```

## molmoact_reasoning_trace_toy.py

MolmoAct-style action reasoning (arXiv 2508.07917, Eq. 3–5): depth perception tokens, then an editable 2-D visual reasoning trace of at most 5 points, then a trajectory-conditioned action, compared with a direct k-nearest-neighbour policy and a mirrored (wrong) trace; five regimes (wall with 5 / 200 demos, no wall, in-plane steering edit, depth steering edit), five seeds, common random numbers. No integration step (kinematic steps; the wall check asserts V / SUB < WALL_T). Checked by `examples/month-6/check.sh`. MolmoAct weights and a GPU are not run here; paper numbers are per the paper. Not ThinkAct, CoT-VLA or TraceVLA.
MolmoAct 式动作推理（arXiv 2508.07917 式 3–5）：深度感知词元 → 最多 5 个点、可编辑的二维视觉推理轨迹 → 以轨迹为条件的动作，与直接 k 近邻策略和左右镜像（错误）的轨迹比较；五种情形（有墙且 5 / 200 条示范、无墙、像平面内转向编辑、沿深度的转向编辑），5 个种子，共用随机数。没有积分步长（运动学步进；墙检查断言 V / SUB < WALL_T）。由 `examples/month-6/check.sh` 核对。MolmoAct 权重与 GPU 本页未运行；论文数字以论文为准。不是 ThinkAct、CoT-VLA 或 TraceVLA。

```bash
python3 molmoact_reasoning_trace_toy.py
```

`internvla_m1_spatial_prompt_toy.py` — InternVLA-M1-style "where, then how" (arXiv 2510.13778): a grounding stage trained on a toy grounding corpus picks the named object, then the same reach stage acts; compared with a direct head that learns grounding only from demonstrations and with a shuffled spatial prompt. Four regimes (cluttered, single object, many demonstrations, a grounding corpus that swaps two colour words), 5 seeds, common random numbers; no integration step. Checked by `examples/month-6/check.sh`. InternVLA-M1 weights, SimplerEnv, LIBERO and GPU: 本页未运行; paper numbers 以论文为准. Not SpatialVLA, Magma, HAMSTER or MolmoAct. / InternVLA-M1 式「先定位、再动作」：玩具定位语料训练的定位阶段先选出被点名的物体，再用同一个到达阶段执行；与只从示范学定位的直接动作头、以及打乱的空间提示比较。四种情形，5 个种子，共用随机数。

```bash
python3 internvla_m1_spatial_prompt_toy.py
```
