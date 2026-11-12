# async-deployment


`stream_sync_eval_toy.py` — stdlib CPU deepen toy; run `python3 stream_sync_eval_toy.py` in this directory.
No hardware, wiring or packages required. Expected stdout: `../expected/stream_sync_eval_toy.txt`; run `bash examples/month-8/check.sh` from the repo root.
Arrival-ordered shared packets; interpolate only arrived brackets at a buffered query. Known clock offsets are synthetic inputs, not estimated. Catch metric is a lagged retrospective proxy, not real success.

`nora_fastplus_small_vla_toy.py` — NORA-style small VLA (arXiv 2504.19854): a 3.0 B-parameter stand-in with FAST-style DCT tokens (rounded coefficients, BPE not modelled) against a 7.0 B-parameter stand-in with one 256-bin token per joint per step, plus the small model read through a shuffled codebook. Two regimes (short in-distribution chunks, long-horizon chunks where the small backbone is declared to fit worse), 5 seeds, common random numbers; success is chunk RMSE strictly below TOL; cost proxy is parameters × tokens. Expected stdout: `../expected/nora_fastplus_small_vla_toy.txt`, checked by `examples/month-8/check.sh`. NORA checkpoint, LIBERO, WidowX and GPU: 本页未运行; paper numbers 以论文为准. Not VLA-Adapter, SmolVLA or the π0-FAST catalogue. / NORA 式小模型 + FAST 式动作词元，对比大模型逐步分箱词元与打乱码本；两种情形，5 个种子，共用随机数。
