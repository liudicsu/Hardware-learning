# Batch-17 PR2 sources / 来源记录

Base `d6e1f35a5e5f347e2e186bf17d0bdf55df68ef39` (`d6e1f35`, main after #169; site **33930**). This PR: M5 moveit-pick-place 300→480 (+180), M5 control-modelling 600→780 (+180); site **33930→34290**; M5 2850→3210; still 71 lessons.

## Opened sources

Both were fetched with curl on 2026-11-10 (Asia/Shanghai), returned HTTP **200**, and were read as text.

| Resource id | URL | Version | What is used |
|---|---|---|---|
| `wiki-jerk` (new) | https://en.wikipedia.org/wiki/Jerk_(physics) | rev 1383557716 (oldid in the fetched HTML) | Section "In motion control" is quoted: the design goal is to minimise the transition time without exceeding speed, acceleration or jerk limits. It describes the seven segments, which arrive at zero speed and zero acceleration. For short moves it shortens segments 2 and 6 first, then 1, 3, 5 and 7. Elsewhere the page says physical systems "experience oscillations and deformations as a result of jerk", and that jerk can be limited by making acceleration continuous. |
| `wiki-invdyn` (new) | https://en.wikipedia.org/wiki/Inverse_dynamics | rev 1381498680 (oldid in the fetched HTML) | The page defines inverse rigid-body dynamics as computing forces and torques from the motion and the inertial properties (quoted). In robotics, it gives the torques the motors must deliver for the prescribed end-point motion (quoted), and forward dynamics is the opposite problem. External forces are hard to infer from the motion. The page gives **no** control law or arm model. |
| existing prose | `src/content/m5/moveit-pick-place` (scaling factors 0.5 / 0.2), `src/content/m5/control-modelling` (gravity feedforward 0.4 N·m × cos q) | in-repo | Both are contrasted in place: scaling factors do not limit jerk, and gravity feedforward is the `ĝ` term kept as arm A. |

Statements are marked 以原文为准 on the site. The S-curve time formulas (T_acc = v/a + a/j, cruise) follow from the segment description. The plant (a spring-damper), the 2R point-mass model and the computed-torque law are labelled textbook-style stand-ins, not taken from either page. No real arm, drive or identification lab was used (本页未运行).

## Toy design

- `examples/month-5/moveit-pick-place/scurve_jerk_limit_toy.py`
  - Shared limits are VMAX 0.5 m/s and AMAX 2 m/s².
  - Arms: A trapezoid; B seven-segment S-curve with JMAX 8 m/s³; C the same S-curve with JMAX_C 2 m/s³.
  - For short moves the peak speed is found by bisection.
  - Plant: y'' = −2ζω(y' − r') − ω²(y − r), with ζ 0.05 and f drawn per seed (Common random numbers, seeds 0–4).
  - Integration is semi-implicit Euler with DT 0.5 ms. The stable-step criterion is DT < H_STAR = 2(√(1+ζ²) − ζ)/ω, which is 6.0558 ms at 50 Hz.
  - Stable-step checks: spectral radius and free run at 0.98× (0.901973, decays) and 1.02× (1.372628, grows). A full rerun at DT/2 changes residual by at most 0.0347 (relative) and cycle time by at most 1.00 ms.
  - Bounds |v|, |a| and |j|, end at goal with v = 0, and acceleration returning to 0 continuously are printed for every profile.
- `examples/month-5/control-modelling/computed_torque_inverse_dynamics_toy.py`
  - Plant: planar 2R arm in a vertical plane with point masses (1.5 kg at the elbow; 1.0 kg plus payload at the tip) and links 0.30 / 0.25 m.
  - Friction FC tanh(q'/0.02), FC 0.3 N m, is in the plant only. Noise is 0.2 mrad / 0.01 rad/s, drawn per 1 ms and held.
  - Gains: KP 400, KD 40.
  - Arms: A PD + gravity with D0 = diag M(start pose); B computed torque with the matched model; C computed torque with the payload left out.
  - Integration is semi-implicit Euler with DT 1 ms. For the matched error dynamics H_STAR = 2(√(1+Z²) − Z)/W = 41.4214 ms.
  - Stable-step checks: at 0.98× the error after 300 steps is 4.0202e-10 rad (decays); at 1.02× it is 2.4418e+05 rad (grows). A full rerun at DT/2 changes rms error by at most 0.0143 (relative).
  - Common random numbers: trajectory scale, phases and noise are drawn once per seed and shared by all arms; seeds 0–4.
- Labels as in batch-15/16/17 PR1: tie → numerically zero below 1e-9 → near-tie |m| ≤ sd → consistent. A consistent gap is "small" under 20 % of the smaller arm mean and "clear" otherwise, always with a sign count.

## Results (k/N = seeds with the reported sign)

S-curve (paired):
- flexible:
  - B−A residual −1.5305±0.1620 mm, clear 5/5.
  - B−A cycle −1.3455±0.2599 s, clear 5/5.
  - B−A profile +0.2500 s, clear 5/5 (B pays time).
  - C misses the 1.5 s window (1.6869 s). C−B cycle +0.5631±0.4518 s, clear 5/5. C−B residual is a near-tie (−0.0361±0.1469, 3 of 5 seeds with the opposite sign).
- rigid_short (declared lose):
  - **B−A profile +0.2309 s and cycle +0.2310 s, clear 5/5 (B loses).** A's residual (about 0.025 mm) is already inside the 0.1 mm tolerance.
  - C misses the 0.5 s window (0.6840 s).

Computed torque (paired):
- fast_coupled:
  - B−A rms −100.9081±33.6992 mrad, clear 5/5.
  - B−A fb −13.9555±3.3677 N m, clear 5/5.
  - C−B rms +60.7909±32.6981, clear 5/5.
  - C−A rms −40.1172±17.0697, clear 5/5 (the wrong-payload model still beats PD + gravity).
- slow_quasi_static (declared near-tie):
  - **B−A rms +16.7587±13.6344, clear 5/5 (B loses; declared near-tie did not hold).**
  - B−A fb is a near-tie (0.0054±0.0094).
  - C−B rms +17.6557±15.2735, clear, 1 of 5 seeds with the opposite sign.
- payload_mismatch (declared lose):
  - **C−A rms +133.6632±28.8934, clear 5/5 (computed torque with the wrong payload loses).**
  - C−B rms +116.0034±33.1360, clear 5/5.
  - B−A rms +17.6598±4.9639, clear 5/5 (B also loses to A here; not declared).

## Post-hoc choices

- S-curve: no profile, plant, limit or regime was changed. After the first run, the bound table's end-state check was split in two, because it had flagged the trapezoid's final acceleration step (one of its four corners) as an end-state failure. Position and speed are now checked together, and acceleration returning to 0 is its own column. All residual and time numbers are byte-identical before and after. Alternatives printed on the page: raise JMAX for the short move, or drop rigid_short.
- Computed torque: no parameter changed and no regime dropped. After the first run, the friction / coupling explanation of the slow-regime loss was worked out by hand (centre pose: (M⁻¹)22 27.15 vs 1/M22 10.67, giving stiffness 14.7 vs 37.5 N m/rad). One side run was made with FC = 0; it is not printed by the toy, and its numbers are quoted on the page: B−A −0.1168±0.0515 mrad (slow) and −5.1016±1.3586 (payload_mismatch), both clear 5/5. Alternatives printed and not taken: raise KP for B to match A's joint stiffness, add friction to the model, or drop slow_quasi_static.
- Independent tests: one hand value in the first draft of the test was wrong. The B cruise time is 0.1 s, not 0.35 s. The test was fixed; the toy was not changed.

## Mismatch with §9

- §9 names the base as `25fb8f23` / 33600. The actual PR2 base is `d6e1f35` / 33930. The totals match §9: 34290, M5 3210, catalogue 71.
- H3 "rigid short → near-tie on time": not met. With a shared jerk limit B's extra time is deterministic, so it is a **clear** loss (+0.2309 s, 5/5). This is stated on the page.
- H3 flexible "consistent S-curve vibration win" and "C consistent lose (late)": met.
- H4 "fast coupled → consistent ID win" and "mismatch → consistent lose (keep)": met. The mismatch regime is kept. C loses to B in every regime and to A in payload_mismatch.
- H4 "slow → near-tie": not met. B clearly loses because of unmodelled friction and the lower joint stiffness of M̂·KP in a coupled direction. This is printed as is.
- The moveit-pick-place host has no `<Summary>` block (the same as ros2-control and policy-evaluation). The new section goes before "## Common mistakes", as in policy-evaluation, and the one summary sentence goes into the "Month 5 wrap-up" paragraph. control-modelling uses its `<Summary>`.

## Lock changes

- New `b17p2` block in `tools/check_diagrams.mjs`. It locks:
  - exact source and stdout in the sections, label rules, regime lines, markers, en/zh symmetry and Summary / wrap-up sentences;
  - resources, the plan header, the sources note and README;
  - that the declared lose / near-tie regimes are kept with their original expectations;
  - the stable-step criterion with the 0.98× / 1.02× and half-step lines, and the S-curve bound checks.
- Tips moved:
  - site total 33930→34290 (two places);
  - month table M5 2850→3210;
  - README `33 930`→`34 290` (en + zh);
  - host tips control-modelling 600→780 (obs3 check and the b14p2 Smith case).
- The b16p2 month-5 plan check no longer requires its old "Current" line; that line moved to Batch-17 PR2 and is locked in the new block. The check still requires its own section.
- No lock relaxed; `.github/workflows` untouched.

## Models / reproducibility

- opencode free models were tried first, with one prompt asking for both toys (150 s timeout each). deepseek-v4.1-flash-free, glm-5.3-flash-free, mimo-v2.6-flash-free and longcat-2.5-free all timed out (exit 124, no files). minimax-m2.5-free exited 1 with no files. The toys were written locally.
- Reproduce:
  - `python3 examples/month-5/moveit-pick-place/scurve_jerk_limit_toy.py`
  - `python3 examples/month-5/control-modelling/computed_torque_inverse_dynamics_toy.py`
  - `python3 tools/test_b17p2_scurve_ct_toys.py`
  - `bash examples/month-5/check.sh`

## Local validation

See the PR description: check_diagrams, check_widgets, check_wokwi, check_quotes, month check.sh, unit tests, lint, typegen, tsc, build + postbuild, and the CI=1 build.
