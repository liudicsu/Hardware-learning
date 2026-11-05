# Month 11 plan: Actuator hardware, tactile contact & cross-embodiment collection

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Lessons open with "This lesson is a site supplement — Months 7–11 are not part of the original six-month course." / 「本课是本站补充内容——第 7–11 个月不属于原六个月课程。」

**PR1–PR3:** full MDX + examples for **11.1–11.7** (PR1 #99: 11.1–11.3, PR2 #100: 11.4–11.5, PR3: 11.6–11.7 + this plan). Month 11 deliberately adds hardware back (power / EMC, FOC, touch) next to the newest collection, data and control directions. It does not replace the 8.7 capstone and does not open a new track; 11.7's "contact-modality experiment" is an optional advanced portfolio section.

Constraints: no required purchases — not DIGIT / GelSight Mini, a BLDC kit, a GoPro or a humanoid robot. Runnable toys are stdlib CPU with fixed seeds (11.5 is deterministic and has no seed), outputs pinned in `examples/month-11/expected/` and checked by `examples/month-11/check.sh` (7 of 7, also run by `tools/sim/reproduce.sh`). FOC flashing, battery / scope probing, tactile capture, GoPro / SLAM, OXE download, Isaac / MuJoCo training and humanoid sim2real are marked「本页未运行」. Paper numbers come only from abstracts / bodies opened at writing time and carry「以论文为准」; real OXE counts never enter CI.

| # | slug | minutes | runnable | verified against |
|---|------|---------|----------|------------------|
| 1 | `power-battery-emc` | 180 | `power_budget_toy.py` | Novanta EMC wiring KB; Roboteq EMI blog; ARK power & grounding |
| 2 | `foc-actuator-lab` | 240 | `clarke_park_toy.py` | SimpleFOC home + `foc_theory` docs |
| 3 | `tactile-sensing` | 240 | `tactile_marker_toy.py` | AnySkin arXiv 2409.08276; DIGIT design / interface repos; GelSight (Yuan 2017); 3D Cal arXiv 2511.03078 (abstract) |
| 4 | `umi-style-collection` | 240 | `relative_traj_toy.py` | UMI arXiv 2402.10329 v3 + project page / Hardware Guide; LeRobot action representations |
| 5 | `cross-embodiment-datasets` | 180 | `oxe_imbalance_toy.py` | OXE project page + GitHub; OXE-AugE arXiv 2512.13100 (abstract) + project page |
| 6 | `humanoid-wbc-overview` | 240 | `lipm_track_toy.py` | ASAP arXiv 2502.01143 (abs + HTML, Table V) + code; HugWBC / Holosoma / TWIST / WBC-AGILE repos (README level) |
| 7 | `contact-rich-policies` | 180 | `tactile_gate_toy.py` | AnySkin Table III; BAKU arXiv 2406.07539; ViTaMIn 2504.06156 / exUMI 2509.14688 (abstract level, no numbers) |

Total 1 500 minutes; site total 71 lessons / 14 790 minutes (from `src/lib/curriculum.ts`).

Pointers: M2 motors-drivers → 11.2; M3 gripper-fingers → 11.3; 8.1 dataset-engineering → 11.5; 10.1 flow-matching → 11.4; M7 / M8 / M10 legged / Isaac electives → 11.6; M8 / M9 / M10 topics FOC → 11.2, tactile → 11.3 / 11.7; 8.7 capstone and 6.5 portfolio → Month 11 (optional, not a replacement). Banners and message ranges say Months 7–11.

PR3 polish: 11.4 toy adds a world-frame bias on the measured EE so the relative-action result is not zero by construction (absolute 0.032893 m vs relative 0.000225 m; bias-only 0); 11.5 drops its unused seed; 11.5 scope link fixed to 8.8 sim-benchmarks.

Still electives / not run here: LeKiwi build, external F/T, Isaac Lab-scale training, on-robot DIGIT / GelSight Mini / BLDC / GoPro / humanoid runs; ViTaMIn / exUMI / MiTaS full-table numbers stay unverified.

Widgets deferred. No prices anywhere.

Verification: `examples/month-11/check.sh` (7/7 same), check_diagrams, check_quotes, lint, tsc, CI build.
