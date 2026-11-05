# Month 11 plan: Actuator hardware, tactile contact & cross-embodiment collection

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Lessons open with "This lesson is a site supplement — Months 7–11 are not part of the original six-month course." / 「本课是本站补充内容——第 7–11 个月不属于原六个月课程。」

**PR1–PR3:** full MDX + examples for **11.1–11.7** (PR1 #99: 11.1–11.3, PR2 #100: 11.4–11.5, PR3: 11.6–11.7 + this plan). Month 11 deliberately adds hardware back (power / EMC, FOC, touch) next to the newest collection, data and control directions. It does not replace the 8.7 capstone and does not open a new track; 11.7's "contact-modality experiment" is an optional advanced portfolio section.

Constraints: no required purchases — not DIGIT / GelSight Mini, a BLDC kit, a GoPro or a humanoid robot. Runnable toys are stdlib CPU with fixed seeds (the 11.5 imbalance toy is deterministic; the score toy uses seed 29), outputs pinned in `examples/month-11/expected/` and checked by `examples/month-11/check.sh` (7 of 7, also run by `tools/sim/reproduce.sh`). FOC flashing, battery / scope probing, tactile capture, GoPro / SLAM, OXE download, Isaac / MuJoCo training and humanoid sim2real are marked「本页未运行」. Paper numbers come only from abstracts / bodies opened at writing time and carry「以论文为准」; real OXE counts never enter CI.

| # | slug | minutes | runnable | verified against |
|---|------|---------|----------|------------------|
| 1 | `power-battery-emc` | 330 | `power_budget_toy.py`, `power_roundtrip_loss_toy.py` | Novanta EMC wiring KB; Roboteq EMI blog; ARK power & grounding |
| 2 | `foc-actuator-lab` | 480 | `clarke_park_toy.py`, `foc_current_loop_toy.py` | SimpleFOC home + `foc_theory` / `foc_implementation` / alignment / voltage_torque docs |
| 3 | `tactile-sensing` | 420 | `tactile_marker_toy.py`, `tactile_debias_recal_toy.py` | AnySkin arXiv 2409.08276; DIGIT design / interface repos; GelSight (Yuan 2017); 3D Cal arXiv 2511.03078 (abstract) |
| 4 | `umi-style-collection` | 240 | `relative_traj_toy.py` | UMI arXiv 2402.10329 v3 + project page / Hardware Guide; LeRobot action representations |
| 5 | `cross-embodiment-datasets` | 330 | `oxe_imbalance_toy.py`, `oxe_auge_score_toy.py` | OXE project page + GitHub; OXE-AugE arXiv 2512.13100v1 HTML §4.2 + A.5 + project page |
| 6 | `humanoid-wbc-overview` | 480 | `lipm_track_toy.py`, `floating_base_contact_toy.py` | ALIP arXiv 2408.05308 §II-A (3) / §III (20); ASAP arXiv 2502.01143 (abs + HTML, Table V) + code; HugWBC / Holosoma / TWIST / WBC-AGILE repos (README level) |
| 7 | `contact-rich-policies` | 180 | `tactile_gate_toy.py` | AnySkin Table III; BAKU arXiv 2406.07539; ViTaMIn 2504.06156 / exUMI 2509.14688 (abstract level, no numbers) |

Total **2 460 minutes** after all three deepen PRs (power +150, FOC +240, tactile +180, OXE +150, contact Jacobian +240); site total **71 lessons / 16 410 minutes** (from `src/lib/curriculum.ts`, after follow-up PR1). M8 is 2 160 and M9 is 2 100 minutes. This completes the in-place deepen batch; no new month or slug.

Pointers: M2 motors-drivers → 11.2; M3 gripper-fingers → 11.3; 8.1 dataset-engineering → 11.5; 10.1 flow-matching → 11.4; M7 / M8 / M10 legged / Isaac electives → 11.6; M8 / M9 / M10 topics FOC → 11.2, tactile → 11.3 / 11.7; 8.7 capstone and 6.5 portfolio → Month 11 (optional, not a replacement). Banners and message ranges say Months 7–11.

Deepen PR1 (`feat/deepen-power-foc`): 11.1 round-trip IR + I²R + fuse data gates (`insufficient_data` / `reject_known_constraint` only, never `ok_slow_blow`); 11.2 electrical angle + dq PI on an R–L circuit with plant θ_e★ never fed to the controller; wrong offset / wrong p compared under identical noise.

Audit fix (#102): 11.4 toy uses fixed-anchor T0⁻¹ Tk vs step-wise delta (delta_accum 0.008287 vs relative_err 0.001875; not zero); bias demo abs 0.033248 / rel 0.000829 / bias-only 0; 11.1 EMC objectives match four-grounds / HF both-end termination (no blanket single-end rule); 11.5 drops leftover「下一批 PR」; LIPM docstring = capture-point fall.

Still electives / not run here: LeKiwi build, external F/T, Isaac Lab-scale training, on-robot DIGIT / GelSight Mini / BLDC / GoPro / humanoid runs; ViTaMIn / exUMI / MiTaS full-table numbers stay unverified.

Widgets deferred. No prices anywhere.

Verification: `examples/month-11/check.sh` (7 lessons / 12 output checks same), check_diagrams, check_quotes, lint, tsc, CI build.

Deepen PR2: synthetic tactile axes/signs, rest debias, independent skin-swap gain recalibration, shared evaluation noise, first-contact data gate (dimensionless, not measured Newtons; policy integration stays 11.7). OXE-AugE stages mask fusion → inpaint → base-position tune → replay/composite are documentation, not a CPU augmentation implementation. A.5 milestone scores 0.3/0.5/0.8/1.0, 10×4 trials, score mean±SE ≠ binary success; 24–45 % lift denominator uncertain (absolute vs relative). Toy outcomes are synthetic; no real OXE cardinality enters CI.

Deepen PR3: six-DOF sagittal base+leg, no arm; two-row point-position Jacobian and velocity no-slip residual Jc qdot=0. Full Jc stays rank2 even for a straight leg; joint-only rank1 is a separate warning. Nullspace pitch regulation checks JcN≈0. Force-only point screen omits moments; finite sole adds CoP bounds on shared synthetic demand, neither screen certifies full dynamics. 11.4 links causal stream alignment in 8.3; 9.3 explains effort-out impedance vs motion-out admittance. All three affected month checks, diagrams, quotes, lint, tsc and CI build are required. Whole deepen batch goes to audit only after reviewer merges this final PR.
