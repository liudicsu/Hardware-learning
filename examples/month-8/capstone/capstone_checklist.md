# Capstone delivery checklist (Month 8)

Pick **one track**. Every track shares the same hard gates.

## Track choice (pick one)

- [ ] **A — Learning:** dataset (8.1) → fine-tune (8.2) → async deploy (8.3)
- [ ] **B — Perception grasp:** depth/point cloud (7.5) + open-vocab grasp (7.6) + MoveIt + hardware component (8.4)
- [ ] **C — Sim-to-real RL:** MuJoCo SO-101 (7.1) → sim-to-real (7.4), verify on the arm

## Shared gates (all tracks)

- [ ] **Safety (8.5):** filled `bench_safety_checklist.md` (e-stop location, pinch points, power order, no unsupervised runs)
- [ ] **DevOps (8.6):** Dev Container and `action-ros-ci` (or equivalent) green on **your** package repo — not this website's CI
- [ ] **Eval (M6):** 20 starts written before trials; **5** held out from training; Wilson 95 % intervals; failure table
- [ ] **Portfolio (M6):** `portfolio_check.py` reports **8/8** on the project README

## Optional

- [ ] LIBERO suite scores via `lerobot-eval --env.type=libero` (Linux; `MUJOCO_GL=egl` on headless) — **本页未运行**
- [ ] Note SimplerEnv (arXiv 2405.05941) if you discuss sim–real correlation of scores

## Commands (on your machine)

```bash
# From the Hardware-learning clone:
python3 ~/Hardware-learning/examples/month-6/specialisation-portfolio/portfolio_check.py /path/to/your/project
python3 ~/Hardware-learning/examples/month-8/capstone/capstone_gate.py /path/to/your/project
```
