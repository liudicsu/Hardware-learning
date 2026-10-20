# SO-101 cube pick and place with ACT

A 6-DoF SO-101 arm picks a 3 cm cube from anywhere in a 20 x 15 cm area and drops it in a bin, with an ACT
policy trained on my own demonstrations. (Sample project for the course's portfolio lesson: the numbers below are
an example of the format, not a real result.)

Video of all 20 evaluation trials, uncut: https://www.youtube.com/watch?v=EXAMPLE

## Results

Evaluated on 20 trials at 20 fixed start positions written down before the session (5 of them outside the
training area), same order for both policies.

| policy | success | 95 % interval | mean time |
|---|---|---|---|
| ACT, 50 demos | 14/20 | 48 .. 85 % | 9.1 s |
| ACT, 50 demos + 15 recovery demos | 18/20 | 70 .. 97 % | 8.7 s |

## Failure analysis

| failure | count (first policy) | what it looks like | fix tried |
|---|---|---|---|
| closes too early, misses the cube | 3 | gripper shuts 1 to 2 cm above it | 15 demos that re-open and retry |
| drops the cube on the way | 2 | cube slips when the wrist turns | lowered wrist speed in the demos |
| cube outside the training area | 1 | arm reaches to the nearest trained spot | not fixed; see limitations |

## Hardware

SO-101 leader and follower arms (Feetech STS3215 servos), one USB webcam at 640 x 480, 30 fps, fixed on a clamp;
training on one rented GPU for about 3 hours.

## How to reproduce

```bash
lerobot-record --robot.type=so101_follower ...   # full command in record.sh
lerobot-train --policy.type=act --dataset.repo_id=me/so101_cube --output_dir=outputs/act_cube
python3 eval.py --positions positions.csv --policy outputs/act_cube
```

## My part and credits

Built on LeRobot (Apache-2.0) and the SO-101 design by TheRobotStudio. My own work: the camera mount, the
recording and evaluation scripts, the 65 demonstrations, the recovery-demo idea and the failure analysis.

## Limitations and next steps

Fails outside the trained area; next, record 10 demos at the 5 outside positions and re-run the same 20 trials.
