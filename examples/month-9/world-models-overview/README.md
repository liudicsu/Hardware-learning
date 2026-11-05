# 9.9 World models overview / 世界模型概览

`latent_predict_toy.py`: discrete latent × action dict rollout for H steps (stdlib, fixed seed).
`neural_traj_idm_toy.py`: DreamGen-style four stages (arXiv 2505.12705) on synthetic 2-D frames — fit a world-model step map on real trajectories, generate frames, pseudo-label them with an IDM fitted on real labelled pairs, train a BC policy; world-model error and IDM error are swept separately with matched trajectory counts and shared evaluation starts.
`latent_predict_toy.py`：离散潜变量 × 动作字典滚动 H 步（标准库，固定种子）。
`neural_traj_idm_toy.py`：在合成二维帧上走 DreamGen 四阶段——在真实轨迹上拟合世界模型步映射、生成帧、用在真实带标签帧对上拟合的 IDM 打伪标签、训练行为克隆策略；世界模型误差与 IDM 误差分开扫，轨迹数匹配、评估起点共享。

```bash
python3 latent_predict_toy.py
python3 neural_traj_idm_toy.py
```

Both outputs are checked by `examples/month-9/check.sh`. Video world models, GPUs and real robots are not run here (本页未运行); DreamGen results are per the paper.
两份输出都由 `examples/month-9/check.sh` 核对。视频世界模型、GPU 与真机本页未运行；DreamGen 结果以论文为准。
