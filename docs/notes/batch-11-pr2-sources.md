# Batch-11 PR2 source, scope and validation audit

Base: `014a8ba` (batch-11 PR1 merged; site **27270**). Proposal §9 PR2 locks: H3 3.x transmissions gear η(load) +180, H4 5.2 state-space-lqr discrete LQR +180. No arithmetic mismatch: after this PR M3 **1950**, M5 **2130**, site **27630**; 71 lessons. All prior expected files remain byte-identical except the two added here.

## Opened sources (curl -L + body read, 2026-11-09, Asia/Shanghai UTC+8)

- `wiki-gear-train` / Wikipedia — Gear train: https://en.wikipedia.org/wiki/Gear_train, HTTP 200, HTML body verified. Gear / speed ratio; torque ratio via virtual work under the assumption that gears are **rigid** and there are **no losses** in tooth engagement — contrasted with the toy’s load-dependent Coulomb+viscous loss. Numbers 以原文为准.
- `ua-lqr` / Underactuated Robotics — Linear Quadratic Regulators: https://underactuated.mit.edu/lqr.html, HTTP 200, HTML body verified. Discrete-time Riccati difference equation; infinite-horizon **DARE** fixed point; discrete vs continuous LQR. Numbers 以原文为准.
- `scipy-dare` / SciPy `scipy.linalg.solve_discrete_are`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_discrete_are.html, HTTP 200, HTML body verified. DARE `A^H X A - X - (A^H X B)(R+B^H X B)^{-1}(B^H X A) + Q = 0`; controllability / unit-circle limitations. Numbers 以原文为准.

Cached under `/workspace/b11p2-sources/` on the worktree host (not committed).

## Toy design

- `gear_efficiency_load_toy.py` (3.x transmissions): shared `n` / τ–ω schedule; **common random numbers** for `(τ_c, b_v)` across A/B/C; arms constant η₀=0.9 / Coulomb+viscous / heavy-load-fit η; heavy_load **near-tie / small gap** on η (not a true zero gap); light_load constant-η power-error gap; backdrive threshold separate from forward η; heat-proxy metric blindness noted; five seeds; ≠ backlash-in-loop.
- `discrete_lqr_zoh_toy.py` (5.2): shared continuous plant + Q/R; **ZOH via matrix exponential** (augmented expm); DARE iteration to `‖ΔP‖_F < 1e-12`; stability `|λ(A_d−B_d K)| < 1`; shared process-noise series by absolute substep; arms cont+ZOH / discrete-at-Ts / discrete-fine; coarse_Ts discrete win; fine_Ts **near-tie / small gap**; cost/settling blind to CPU budget; five seeds; ≠ Bode redo.

Independent tests: `tools/test_b11_gear_dlqr_toys.py` (identical friction/noise per seed; stability; ZOH≠Euler; step-size).

## Models / reproducibility

opencode free model attempted first; server error / empty. Toys implemented locally in `/workspace/hl-b11p2` (`cp -al` node_modules from hl-b11p1).

## Local validation

`tools/test_b11_gear_dlqr_toys.py`, month-3 / month-5 `check.sh`, `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build. No workflow edits. Minutes **71 / 27630**.
