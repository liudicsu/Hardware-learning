# Batch-12 PR1 source, scope and validation audit

Base: `a4b3b93` (batch-11 closed incl. polish #148; site **28050**). Proposal `batch-12-proposal.md` §9 PR1 locks: H1 1.1 ohms-law Thévenin +150, H2 4.4 gazebo-sim Δt / contact stability +180. No arithmetic mismatch: curriculum.ts on base gives M1 1350 / M4 2130 / site 28050; after this PR M1 **1500**, M4 **2310**, site **28380**; 71 lessons. No new slugs, no Month 12, no polish-tree edits. All prior expected files remain byte-identical; two expected files are added.

## Opened sources (curl -L + body read, 2026-11-09, Asia/Shanghai UTC+8)

- `wiki-thevenin` / Wikipedia — Thévenin's theorem: https://en.wikipedia.org/wiki/Th%C3%A9venin%27s_theorem, HTTP 200, HTML body verified (mw-parser-output). Linear network → `Vth` in series with `Rth` at two terminals; `Vth` = open-circuit voltage; `Rth` = resistance with ideal voltage sources shorted and current sources opened, or `Vth / Isc`. Numbers 以原文为准.
- `wiki-norton` / Wikipedia — Norton's theorem: https://en.wikipedia.org/wiki/Norton%27s_theorem, HTTP 200, HTML body verified. Short-circuit current `In` in parallel with `Rn`; `Rn = Rth`, `Vth = In × Rn`; worked example 3.75 mA ∥ 2 kΩ. Numbers 以原文为准.
- `sdf-physics-spec` / SDFormat 1.11 `physics.sdf` spec source: https://raw.githubusercontent.com/gazebosim/sdformat/sdf14/sdf/1.11/physics.sdf, HTTP 200, file body read. `max_step_size` default 0.001 ("Maximum time step size at which every system in simulation can interact with the states of the world"); `real_time_factor` default 1.0. **Not cited:** `https://sdformat.org/spec?ver=1.11&elem=physics` and `...elem=collision` (named in the proposal) return HTTP 200 but only a JavaScript shell without the element text, so they are not used as sources.
- `gz-physics-engines` / Gazebo Sim 8 API — Physics engines: https://gazebosim.org/api/sim/8/physics.html, HTTP 200, HTML body verified. DART default (`gz-physics-dartsim-plugin`); Bullet / Bullet Featherstone preliminary; select via Physics plugin `<engine><filename>` or `gz sim --physics-engine`. Numbers 以原文为准.
- `wiki-euler-method` / Wikipedia — Euler method: https://en.wikipedia.org/wiki/Euler_method, HTTP 200, HTML body verified ("Numerical stability" section: region `|z + 1| ≤ 1` for `y′ = ky`, `z = hk`; unstable on stiff equations with large steps).
- `wiki-semi-implicit-euler` / Wikipedia — Semi-implicit Euler method: https://en.wikipedia.org/wiki/Semi-implicit_Euler_method, HTTP 200, HTML body verified (update `v` then `x` with `v[n+1]`; first order; symplectic; nearly conserves energy).

The semi-implicit Euler limit `(ωΔt)² + 4ζ(ωΔt) < 4` on `m·x″ + c·x′ + k·x = 0` is derived in the lesson (trace/determinant of the 2×2 step matrix, Jury conditions) and verified numerically in the toy (spectral radius) and in `tools/test_b12_thevenin_gazebo_toys.py` (free oscillation decays at 0.98× and blows up at 1.02× the limit; explicit Euler at 1 ms blows up). It is not quoted from a source.

Cached under `/workspace/b12p1-sources/` on the worktree host (not committed).

## Toy design

- `thevenin_loaded_divider_toy.py` (1.1): ideal 5 V source, nominal 10 kΩ / 4.7 kΩ (the lesson divider: `Vth = 1.5986 V`, `Rth = 3197.3 Ω`, `V_L(10 kΩ) = 1.2113 V`). Truth = independent KCL at the output node with actual 1 % parts. **Common random numbers** per (seed, board): R1, R2, RL, Rtest and meter noise z1/z2 shared by all arms (same `Voc` reading). Arms A Voc-only / B Thévenin two-reading (`Rth = Rtest_nom·(Voc/Vtest − 1)`) / C Norton short-circuit through a synthetic 100 Ω ammeter burden. Regimes heavy (3.3 kΩ), lesson (10 kΩ), light (10 MΩ: B vs C **near-tie / small gap**, paired C−B 0.0004±0.0015 mV within seed noise; A−B **small but consistent gap, not a tie**, paired 0.1153±0.0588 mV, A's ≈ 0.51 mV bias diluted by 1 mV meter noise). 5 seeds × 32 boards. Metric blind to short-circuit risk, time and test-resistor power.
- `gazebo_step_contact_stability_toy.py` (4.4): 1 kg box, linear Kelvin–Voigt contact `k = 2.5e5 N/m`, `ζ = 0.2` (`ω = 500 rad/s`), unilateral, no force clamp, no friction, no event location; semi-implicit Euler at 3 ms / 1 ms / 0.1 ms vs a 10 µs reference. **Common random numbers**: per seed one drop height and one disturbance `f(t)` (ZOH 0.1 ms grid), applied as a step average so every arm receives the same impulse per whole step. Criterion table (spectral radius) for semi-implicit and explicit Euler. Regimes impact_drop (coarse loses; B vs C COR is a near-tie / small gap) and gentle_rest (**near-tie / small gap**, 0 bounces for every arm). Not DART; `k`/`c` are not Gazebo knobs (DART ignores `<contact><ode><kp>/<kd>`). Steps per simulated second is a compute proxy blind to solver iterations and rendering.

Independent tests: `tools/test_b12_thevenin_gazebo_toys.py` (also executed by the batch-12 PR1 block in `tools/check_diagrams.mjs`).

## Models / reproducibility

opencode free models were tried first with the toy brief (`/workspace/b12p1-opencode/`): `deepseek-v4.1-flash-free` (120 s), `glm-5.3-flash-free`, `mimo-v2.6-flash-free`, `longcat-2.5-free` (90 s each) all timed out with no file output; no MiniMax free model is listed by `opencode models`. Toys, tests and lesson text implemented locally in `/workspace/hl-b12p1` (`cp -al` node_modules from hl-b11pol).

## Local validation

`tools/test_b12_thevenin_gazebo_toys.py`, month-1 / month-4 `check.sh` (Python-only toys), `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build. No workflow edits. Minutes **71 / 28380**.

## NEEDS_FIX follow-up (same PR)

- Light-load wording split: B vs C = near-tie / small gap (0.0004 mV, paired C−B 0.0004±0.0015 mV, within seed noise; burden / Rth error barely matters at RL ≫ Rth); A vs B = small but consistent gap, not a tie (paired 0.1153±0.0588 mV; A's ~0.51 mV bias diluted by 1 mV meter noise). Toy prints, expected, en/zh prose, Summary, curriculum objective, plan note, tests and locks updated. Minutes unchanged (28380 / M1 1500 / M4 2310).
