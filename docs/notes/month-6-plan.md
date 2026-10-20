# Month 6 plan: Robot learning, specialisation & getting hired

Course source: @DeRonin_'s 6-month roadmap (`COURSE_SOURCE` in src/lib/curriculum.ts). Month 6 topics there:
imitation learning (behaviour cloning, ACT, diffusion policy), VLA models and which have open weights,
choosing a specialisation, portfolio and job applications. Milestones are already in curriculum.ts.

Constraints that shape the design: no GPU and no PyTorch on the build box, and every quoted output must be
reproducible from a clean checkout. So each lesson's runnable example is a **standard-library Python toy model**
(fixed seeds, `random.Random`) that shows the real algorithmic effect, quoted as `<SimOutput source="model">`.
The real-hardware path (LeRobot on an SO-101, `lerobot-record` / `lerobot-train`) is given as commands to run on
the learner's own machine, clearly marked as not run here. All code lives in `examples/month-6/<slug>/`, outputs in
`examples/month-6/expected/`, and `examples/month-6/check.sh` re-runs everything and diffs (also hooked into
`tools/sim/reproduce.sh`). `tools/check_quotes.py` checks CodeSource and SimOutput blocks.

| # | slug | lesson | runnable example | how it is verified |
|---|------|--------|------------------|--------------------|
| 1 | `behaviour-cloning` | Imitation learning I: demonstrations, behaviour cloning, covariate shift, DAgger | `bc_reach.py`: a point gripper in a narrow corridor; a scripted expert records episodes in a LeRobot-style table (episode_index, frame_index, observation.state, action); a nearest-neighbour BC policy is trained on 5 / 20 / 80 demos and evaluated over 100 seeded rollouts with actuator noise; then 3 DAgger rounds | success rate, mean off-path distance and failure count per policy compared with `expected/bc_reach.txt` |
| 2 | `act-diffusion` | Imitation learning II: multimodal demos, action chunking (ACT) and diffusion policy | `multimodal.py`: an obstacle the expert passes on the left or the right (50/50). Compares an MSE-style averaging policy (drives into the obstacle), single-step sampling (mode switching, dithering), action chunks with temporal ensembling (ACT idea), and DDPM sampling with the exact denoiser of the demo set (what a diffusion policy's network learns to approximate) | success / collision / timeout counts over seeded rollouts, `expected/multimodal.txt` |
| 3 | `vla-models` | VLA models: what they are, how actions become tokens, which have open weights | `action_tokens.py`: RT-2/OpenVLA-style 256-bin per-dimension tokenisation (1st–99th percentile range) vs. a DCT-based chunk compression in the spirit of FAST; token counts and reconstruction error on a recorded trajectory | `expected/action_tokens.txt`; open-weight facts (OpenVLA, Octo, π0/π0.5 via openpi, SmolVLA, GR00T N1.x, RDT) checked against each official page with "check the official page" note |
| 4 | `policy-evaluation` | Evaluating a policy: success rate, confidence intervals, failure analysis | `eval_report.py`: reads the episode logs written by lessons 1–2, prints success with Wilson 95 % intervals, how many trials are needed to tell two policies apart, and a failure taxonomy table | `expected/eval_report.txt` |
| 5 | `specialisation-portfolio` | Choosing a specialisation, the portfolio and getting hired | `portfolio_check.py`: checks a project folder's README for the parts a reviewer looks for (demo video link, metrics table, failure analysis, reproduce commands, hardware list) and prints what is missing; run on a good and a bad sample project in the repo | `expected/portfolio_check.txt` (pass + fail case) |

Per lesson: zh.mdx + en.mdx in `src/content/m6/<slug>/` (same structure, quiz ids, numbers), README.md in the
example folder, lesson entry with tasks in `month6Lessons` in curriculum.ts, resources in resources.ts
(official pages only, external links). Month 6 `status` stays `"outline"` until all five lessons exist, then `"ready"`.
Verification per lesson: `npx tsc --noEmit`, `npx eslint .`, `npm run build`, `examples/month-6/check.sh`,
`python3 tools/check_quotes.py`; commit and push after each lesson.
