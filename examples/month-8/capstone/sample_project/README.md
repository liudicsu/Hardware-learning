# Sample capstone — Track A (learning)

Demo project for `capstone_gate.py`. Not a real robot result.

## Video

Watch the run: https://youtu.be/dQw4w9WgXcQ

## Results

| policy | success |
|--------|---------|
| ACT baseline | 14/20 |
| SmolVLA FT | 16/20 |

Wilson 95 % intervals computed with Month 6 `eval_report` helpers (14/20 → about 48–85 %).

## Trials

We fixed **20 trials** (20 starts) before the first session; **5** were held-out (未见) poses never used in teleop. Same list for every policy.

## Failures

| start | mode |
|-------|------|
| 3 | gripper slip |
| 11 | timeout |

## Reproduce

```bash
cd ~/my-capstone
python3 train.py --seed 0
```

## Hardware

SO-101 follower, USB camera, laptop. Bill of materials in `bom.md`.

## My part / Credits

I recorded the dataset, fine-tuned SmolVLA, and wrote the async client. ACT baseline reused from Month 6 examples; LeRobot for training.

## Limitations / next steps

Only one lighting condition. Next: add domain randomization from Month 7 and re-run the 20 starts.
