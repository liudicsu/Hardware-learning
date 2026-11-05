# Month 11 plan: Actuator hardware, tactile contact & cross-embodiment collection

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Lessons open with "This lesson is a site supplement — Months 7–11 are not part of the original six-month course." / 「本课是本站补充内容——第 7–11 个月不属于原六个月课程。」

**PR1–PR3:** full MDX + examples for **11.1–11.7** (PR1 #99: 11.1–11.3, PR2 #100: 11.4–11.5, PR3: 11.6–11.7 + this plan). Month 11 deliberately adds hardware back (power / EMC, FOC, touch) next to the newest collection, data and control directions. It does not replace the 8.7 capstone and does not open a new track; 11.7's "contact-modality experiment" is an optional advanced portfolio section.

Constraints: no required purchases — not DIGIT / GelSight Mini, a BLDC kit, a GoPro or a humanoid robot. Runnable toys are stdlib CPU with fixed seeds (11.5 is deterministic and has no seed), outputs pinned in `examples/month-11/expected/` and checked by `examples/month-11/check.sh` (7 of 7, also run by `tools/sim/reproduce.sh`). FOC flashing, battery / scope probing, tactile capture, GoPro / SLAM, OXE download, Isaac / MuJoCo training and humanoid sim2real are marked「本页未运行」. Paper numbers come only from abstracts / bodies opened at writing time and carry「以论文为准」; real OXE counts never enter CI.

| # | slug | minutes | runnable | verified against |
|---|------|---------|----------|------------------|
| 1 | `power-battery-emc` | 330 | `power_budget_toy.py`, `power_roundtrip_loss_toy.py` | Novanta EMC wiring KB; Roboteq EMI blog; ARK power & grounding |
| 2 | `foc-actuator-lab` | 480 | `clarke_park_toy.py`, `foc_current_loop_toy.py` | SimpleFOC home + `foc_theory` / `foc_implementation` / alignment / voltage_torque docs |
| 3 | `tactile-sensing` | 240 | `tactile_marker_toy.py` | AnySkin arXiv 2409.08276; DIGIT design / interface repos; GelSight (Yuan 2017); 3D Cal arXiv 2511.03078 (abstract) |
| 4 | `umi-style-collection` | 240 | `relative_traj_toy.py` | UMI arXiv 2402.10329 v3 + project page / Hardware Guide; LeRobot action representations |
| 5 | `cross-embodiment-datasets` | 180 | `oxe_imbalance_toy.py` | OXE project page + GitHub; OXE-AugE arXiv 2512.13100 (abstract) + project page |
| 6 | `humanoid-wbc-overview` | 240 | `lipm_track_toy.py` | ASAP arXiv 2502.01143 (abs + HTML, Table V) + code; HugWBC / Holosoma / TWIST / WBC-AGILE repos (README level) |
| 7 | `contact-rich-policies` | 180 | `tactile_gate_toy.py` | AnySkin Table III; BAKU arXiv 2406.07539; ViTaMIn 2504.06156 / exUMI 2509.14688 (abstract level, no numbers) |

Total 1 890 minutes after deepen-PR1 (power +150, FOC +240); site total 71 lessons / 15 180 minutes (from `src/lib/curriculum.ts`). Further deepen PRs (tactile/OXE, contact Jacobian/impedance/sync) raise M11 toward 2 460 and site toward 16 050 (in-place deepen batch; no Month 12).

Pointers: M2 motors-drivers → 11.2; M3 gripper-fingers → 11.3; 8.1 dataset-engineering → 11.5; 10.1 flow-matching → 11.4; M7 / M8 / M10 legged / Isaac electives → 11.6; M8 / M9 / M10 topics FOC → 11.2, tactile → 11.3 / 11.7; 8.7 capstone and 6.5 portfolio → Month 11 (optional, not a replacement). Banners and message ranges say Months 7–11.

Deepen PR1 (`feat/deepen-power-foc`): 11.1 round-trip IR + I²R + fuse data gates (`insufficient_data` / `reject_known_constraint` only, never `ok_slow_blow`); 11.2 electrical angle + dq PI on an R–L circuit with plant θ_e★ never fed to the controller; wrong offset / wrong p compared under identical noise.

Audit fix (#102): 11.4 toy uses fixed-anchor T0⁻¹ Tk vs step-wise delta (delta_accum 0.008287 vs relative_err 0.001875; not zero); bias demo abs 0.033248 / rel 0.000829 / bias-only 0; 11.1 EMC objectives match four-grounds / HF both-end termination (no blanket single-end rule); 11.5 drops leftover「下一批 PR」; LIPM docstring = capture-point fall.

Still electives / not run here: LeKiwi build, external F/T, Isaac Lab-scale training, on-robot DIGIT / GelSight Mini / BLDC / GoPro / humanoid runs; ViTaMIn / exUMI / MiTaS full-table numbers stay unverified.

Widgets deferred. No prices anywhere.

Verification: `examples/month-11/check.sh` (7/7 same), check_diagrams, check_quotes, lint, tsc, CI build.
