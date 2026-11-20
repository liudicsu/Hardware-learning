# rl-manipulation-sim

`reward_shaping.py` — tabular Q-learning on a discrete reach–grasp grid comparing
**sparse** vs **dense** rewards (stdlib, seed 7). ManiSkill3 / SB3 SAC are described
in the lesson MDX and marked「本页未强制」/ "not required on this page".

`her_sparse_grasp_toy.py` — Hindsight Experience Replay on the same grid made goal-conditioned
(stdlib, five seeds, common random numbers): sparse vs sparse + HER (future, k = 4) vs dense, four
regimes; expected output in `../expected/her_sparse_grasp_toy.txt`, compared by `../check.sh`.
SB3 HER / ManiSkill3 本页未运行.

`potential_based_shaping_toy.py` — potential-based reward shaping on a shared
tabular MDP with a distractor cycle (stdlib, five seeds, common random numbers):
unshaped sparse R vs F = γΦ(s')-Φ(s) vs a non-potential bonus; expected output
in `../expected/potential_based_shaping_toy.txt`, compared by `../check.sh`.
ManiSkill / SB3 / a real arm 本页未运行.
