# rl-foundations

`ppo_reach.py` is a 1-D reach MDP with a clipped-surrogate (PPO-style) update, three fixed seeds,
stdlib only. On your machine you can swap in Gymnasium + Stable-Baselines3 PPO (CPU); that path
is marked "not run on this page" in the lesson.

`td3_clipped_double_q_toy.py` compares a DDPG-style single critic, TD3 (clipped double Q, target policy smoothing, delayed actor) and clipped double Q without the delay, with linear critics on a 1-D plant, shared replay noise and five seeds (common random numbers), stdlib only. Expected output in `../expected/td3_clipped_double_q_toy.txt`, checked by `check.sh`. MuJoCo / Gym / GPU training is not run on this page.
`td3_clipped_double_q_toy.py` 在一维对象上用线性 critic 比较 DDPG 式单 critic、TD3（裁剪双 Q、目标策略平滑、延迟 actor）和不延迟的裁剪双 Q，共用回放噪声，5 个种子（共用随机数），只用标准库。期望输出在 `../expected/td3_clipped_double_q_toy.txt`，由 `check.sh` 核对。本页未运行 MuJoCo / Gym / GPU 训练。

```bash
python3 td3_clipped_double_q_toy.py
```
