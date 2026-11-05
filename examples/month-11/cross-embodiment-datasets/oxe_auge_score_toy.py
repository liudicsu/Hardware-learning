#!/usr/bin/env python3
"""A.5-style partial scores vs binary completion on SYNTHETIC equal trials.

Documentation constants describe AugE-Toolkit stages, not a CPU implementation
of segmentation/inpainting/IK/rendering. No real OXE counts or paper outcomes.
A.5: .3 attempt, .5 grasp, .8 carry towards target, 1.0 correct placement.
Zero below is OUR convention for no milestone (A.5 does not specify it).
Sample SE assumes independent trials; it is not the paper's error bar.
"""
import math
import random
import statistics

SEED = 29
STAGES = ("mask_fusion", "inpaint", "base_position_tune", "replay_composite")
# Four tasks, ten trials each; deterministic synthetic outcome distribution.
TASK_SCORES = [
    [0, .3, .3, .5, .5, .8, .8, 1, 1, 1],
    [0, 0, .3, .3, .5, .5, .8, .8, 1, 1],
    [0, .3, .3, .3, .5, .5, .5, .8, 1, 1],
    [0, 0, .3, .5, .5, .8, .8, .8, 1, 1],
]
rng = random.Random(SEED)
for scores in TASK_SCORES:
    rng.shuffle(scores)
flat = [score for scores in TASK_SCORES for score in scores]
binary = [float(score == 1) for score in flat]


def mean_se(values):
    return statistics.mean(values), statistics.stdev(values) / math.sqrt(len(values))


mean, se = mean_se(flat)
full, full_se = mean_se(binary)
assert len(flat) == 40 and all(len(task) == 10 for task in TASK_SCORES)
assert mean > full  # partial progress is not binary placement
print(f"seed={SEED}")
print("data=synthetic_not_paper_results")
print("stages=" + "->".join(STAGES))
print("rubric=0.3_attempt,0.5_grasp,0.8_carry,1.0_place")
print("zero=no_milestone_toy_convention")
print(f"tasks={len(TASK_SCORES)} trials_per_task=10 trials={len(flat)}")
print(f"partial_score_mean={mean:.4f}")
print(f"partial_score_se={se:.4f}")
print(f"binary_completion_mean={full:.4f}")
print(f"binary_completion_se={full_se:.4f}")
print(f"full_placements={int(sum(binary))}/40")
print("paper_24_45_percent_denominator=uncertain_absolute_vs_relative")
