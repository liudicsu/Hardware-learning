# Month 9 plan: Long-horizon tasks, contact control & mobile manipulation

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–9 are written here; they are not part of that original course). Proposal: `/workspace/proposals/m9-proposal.md`.

**Batch 1 (this PR):** scaffold all seven lessons + resources/glossary/messages/git-github/capstone pointer; full MDX + examples for **9.1, 9.3, 9.5**; outline shells for **9.2, 9.4, 9.6, 9.7**.

**Batch 2:** full MDX + examples for **9.2 moveit-servo**, **9.4 llm-skill-planning** (CI/expected = fake LLM only; optional student API marked 本页未运行).

**Batch 3:** full MDX + examples for **9.6 nav-arm-compose**, **9.7 multi-skill-demo** (thin advanced demo — does **not** replace 8.7 capstone).

**Electives** (month-page further-reading only, not formal lessons, not in the 1500 min): `lekiwi-build`, `micro-ros-foc`, `ft-sensor-admittance`, `world-models-overview`. LeKiwi real build stays elective / out of scope for 9.6 required work. Admittance lesson names no F/T brand or price.

Constraints: private env; runnable toys prefer stdlib CPU with fixed seeds. ROS 2 / MoveIt demos / real SO-101 Present Load logging / paid LLM APIs marked「本页未运行」. Hard facts from primary sources (2026-11-04 UTC+8): MoveIt MTC & Servo tutorials; control.ros.org Jazzy admittance_controller; Feetech STS3215 Present Load addr 60 / Current addr 69; SayCan arXiv 2204.01691; Inner Monologue arXiv 2207.05608; BehaviorTree.CPP; LeRobot LeKiwi docs.

| # | slug | minutes | this batch | runnable | verified against |
|---|------|---------|------------|----------|------------------|
| 1 | `mtc-long-horizon` | 240 | **full** | `stage_graph_toy.py` (stdlib) | MoveIt Task Constructor pick-and-place tutorial (generator/propagator/connector; serial/parallel/wrapper) |
| 2 | `moveit-servo` | 180 | outline | (later) | MoveIt realtime_servo_tutorial |
| 3 | `effort-admittance` | 240 | **full** | `load_contact_sim.py`, `admittance_1d.py` (stdlib) | Feetech STS3215 register ref + product page; ros2_controllers admittance userdoc `F = M a + D v + S (x−x_d)`; ζ = D/(2√(MS)); no F/T brand/price |
| 4 | `llm-skill-planning` | 240 | outline | (later; fake LLM only in CI) | SayCan arXiv 2204.01691; say-can.github.io |
| 5 | `failure-recovery` | 180 | **full** | `recovery_bt_toy.py` + `failure_table.md` (stdlib) | Inner Monologue arXiv 2207.05608; BehaviorTree.CPP; contrast M4 Nav2 + M8 watchdog |
| 6 | `nav-arm-compose` | 240 | outline | (later) | LeRobot LeKiwi docs (elective hardware); Nav2 compose contract |
| 7 | `multi-skill-demo` | 180 | outline | (later) | Thin demo gate; does not replace 8.7 |

Widgets (`StageGraphWidget` / `Admittance1DWidget` / `SayCanScoreWidget`) deferred — lessons use `SimOutput` from scripts. No prices anywhere.

Verification: `examples/month-9/check.sh` (hooked into `tools/sim/reproduce.sh`), check_quotes, check_diagrams (no new diagram widgets this batch), check_widgets, lint, check_wokwi, tsc, CI build.
