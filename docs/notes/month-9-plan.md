# Month 9 plan: Long-horizon tasks, contact control & mobile manipulation

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Proposal archive: `/workspace/proposals/m9-proposal.md`. Track B electives: `/workspace/proposals/promote-electives-proposal.md`.

**Batches 1–3 (merged):** full MDX + examples for **9.1–9.7**. **Track B:** append **9.8 `visual-servoing`** then **9.9 `world-models-overview`** (end of array only).

**Electives** (month-page further-reading only, not formal lessons): `lekiwi-build`, `micro-ros-foc`, `ft-sensor-admittance`. (`world-models-overview` promoted to 9.9; `multi-view-extrinsics`, `intervention-logging` and `edge-deploy-checklist` are now Month 10 lessons 10.3–10.5 — see `docs/notes/month-10-plan.md`.)

Constraints: private env; runnable toys prefer stdlib CPU with fixed seeds. ROS 2 / MoveIt demos / real SO-101 Present Load logging / paid LLM APIs / real LeKiwi / OpenCV webcam / world-model training marked「本页未运行」.

| # | slug | minutes | status | runnable | verified against |
|---|------|---------|--------|----------|------------------|
| 1 | `mtc-long-horizon` | 240 | full | `stage_graph_toy.py` | MoveIt Task Constructor |
| 2 | `moveit-servo` | 180 | full | `servo_loop_sim.py` | MoveIt realtime_servo_tutorial |
| 3 | `effort-admittance` | 240 | full | `load_contact_sim.py`, `admittance_1d.py` | Feetech STS3215 + ros2 admittance |
| 4 | `llm-skill-planning` | 240 | full | `saycan_score_toy.py` (fake LLM) | SayCan arXiv 2204.01691 |
| 5 | `failure-recovery` | 180 | full | `recovery_bt_toy.py` | Inner Monologue + BT.CPP |
| 6 | `nav-arm-compose` | 240 | full | `nav_pick_bt.py` | LeKiwi docs (elective hardware) |
| 7 | `multi-skill-demo` | 180 | full | `demo_gate.py --all` | Thin demo; does not replace 8.7 |
| **8** | **`visual-servoing`** | **240** | **Track B** | **`tag_error_jog.py`** | OpenCV ArUco/PnP docs; Servo command side |
| **9** | **`world-models-overview`** | **180** | **Track B** | **`latent_predict_toy.py`** | DreamerV3 / DayDreamer / UniSim (+ optional IRIS) reading |

Widgets deferred. No prices anywhere.

Verification: `examples/month-9/check.sh`, check_quotes, check_diagrams, check_widgets, lint, check_wokwi, tsc, CI build.
