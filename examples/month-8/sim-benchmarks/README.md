# 8.8 sim-benchmarks

- `suite_score_table.py` — five fake LIBERO-style suites, per-suite mean and Wilson 95 % intervals (seed 88).
- `imagine_rank_toy.py` — the Ctrl-World idea (arXiv 2510.10125) as a stdlib toy: five synthetic policies ranked in an oracle environment and in biased "world models" on the same tasks and initial conditions; Kendall τ and flipped pairs. 五个合成策略在有偏世界模型与 oracle 环境中排名，共享任务与初始条件；输出 Kendall τ 与翻转对。

```bash
python3 suite_score_table.py   # ../expected/suite_score_table.txt
python3 imagine_rank_toy.py    # ../expected/imagine_rank_toy.txt
```

No video world model, DROID data, π0 / π0.5 checkpoint or GPU is run here (本页未运行). Paper numbers are per the paper / 以论文为准.
