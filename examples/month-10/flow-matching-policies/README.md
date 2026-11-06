# 10.1 flow-matching-policies

`flow_match_toy.py` — 1-D flow matching with a closed-form marginal velocity (no network). Euler-integrates noise to a bimodal target with 1/2/3/5/10/50 steps.

```bash
python3 flow_match_toy.py   # compare with ../expected/flow_match_toy.txt
```

Optional, not run here / 本页未运行: read `num_steps` in the LeRobot SmolVLA / π0 policy configs (follow the LeRobot v0.6.x docs; options may change between versions).

## Batch-6 PR3: `policy_distill_onestep_toy.py`

Stdlib CPU literacy surrogate; run `python3 examples/month-10/flow-matching-policies/policy_distill_onestep_toy.py` from repo root, then `bash examples/month-10/check.sh`. Full bilingual model, code and five-seed output are in lesson 10.1. GPU / original policy / robot 本页未运行; paper 以论文为准.
