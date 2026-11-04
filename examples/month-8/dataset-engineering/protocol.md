# Recording protocol template (SO-101 / LeRobot)

Fill this before the first teleop session. Keep it next to the dataset README.

## Task
- Task name:
- Language instruction (must match what the VLA sees at train and at rollout):
- Success criterion (one sentence):

## Variation × repetition
List the factors you will vary, and how many episodes per cell. SmolVLA docs suggest starting around **~50 episodes** for a single task; their pick-and-place example used **5 cube positions × 10 episodes**. Under 25 episodes was not enough in that setup.

| variation factor | levels | episodes per level |
|------------------|--------|--------------------|
| object pose      |        |                    |
| lighting         |        |                    |
| distractors      |        |                    |

## Cameras and ports
- Wrist cam device / topic:
- Scene cam device / topic:
- Control rate (Hz):

## Evaluation starts (link to Month 6)
Reserve **20 evaluation start poses**; **5 must not appear in the training set**. Record their joint indices or end-effector poses here:

1.
…

## Exclusion rules
Drop an episode if: lost tracking / e-stop / collision / teleop freeze > 1 s / wrong instruction spoken.

## Operator notes
