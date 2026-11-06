# Month 9 plan: Long-horizon tasks, contact control & mobile manipulation

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Proposal archive: `/workspace/proposals/m9-proposal.md`. Track B electives: `/workspace/proposals/promote-electives-proposal.md`.

**Batches 1–3 (merged):** full MDX + examples for **9.1–9.7**. **Track B:** append **9.8 `visual-servoing`** then **9.9 `world-models-overview`** (end of array only).

**Electives** (month-page further-reading only, not formal lessons): `lekiwi-build`, `micro-ros-foc`, `ft-sensor-admittance`. (`world-models-overview` promoted to 9.9; `multi-view-extrinsics`, `intervention-logging` and `edge-deploy-checklist` are now Month 10 lessons 10.3–10.5 — see `docs/notes/month-10-plan.md`.)

Constraints: private env; runnable toys prefer stdlib CPU with fixed seeds. ROS 2 / MoveIt demos / real SO-101 Present Load logging / paid LLM APIs / real LeKiwi / OpenCV webcam / world-model training marked「本页未运行」.

| # | slug | minutes | status | runnable | verified against |
|---|------|---------|--------|----------|------------------|
| 1 | `mtc-long-horizon` | 420 | full + H7 | `stage_graph_toy.py`, `mtc_stage_memory_toy.py` | MoveIt Task Constructor |
| 2 | `moveit-servo` | 180 | full | `servo_loop_sim.py` | MoveIt realtime_servo_tutorial |
| 3 | `effort-admittance` | 420 | full | `load_contact_sim.py`, `admittance_1d.py`, `impedance_vs_admittance_toy.py` | Feetech STS3215 + ros2 admittance |
| 4 | `llm-skill-planning` | 240 | full | `saycan_score_toy.py` (fake LLM) | SayCan arXiv 2204.01691 |
| 5 | `failure-recovery` | 180 | full | `recovery_bt_toy.py` | Inner Monologue + BT.CPP |
| 6 | `nav-arm-compose` | 450 | full + H2 | `nav_pick_bt.py`, `multi_robot_corridor_toy.py` | LeKiwi elective; ORCA primary / MRS curriculum IL reading |
| 7 | `multi-skill-demo` | 180 | full | `demo_gate.py --all` | Thin demo; does not replace 8.7 |
| **8** | **`visual-servoing`** | **240** | **Track B** | **`tag_error_jog.py`** | OpenCV ArUco/PnP docs; Servo command side |
| **9** | **`world-models-overview`** | **420** | **Track B + G3** | **`latent_predict_toy.py`**, **`neural_traj_idm_toy.py`** | DreamerV3 / DayDreamer / UniSim / DreamGen reading |

Widgets deferred. No prices anywhere.

Verification: `examples/month-9/check.sh`, check_quotes, check_diagrams, check_widgets, lint, check_wokwi, tsc, CI build.

Deepen PR3 (+180): 9 lessons / **2 100 min** then. Impedance commands effort; admittance commands motion through an explicit inner servo on the same mass/damper/spring/wall, disturbances and noise. Peak force, penetration and post-release settling compare chosen gains/interfaces, not universal safety. SO-101 stays Load proxy + admittance; external F/T elective. Site was 71 lessons / 16 050 min before follow-up observability batch.

## Batch-after-obs PR2 (G3, +240 here)

G3 `world-models-overview` 180→420 — `neural_traj_idm_toy.py`: DreamGen four-stage read (finetune video WM → generate video → IDM / latent-action pseudo-labels → train policy); synthetic low-dim frames; IDM fitted on real labelled pairs then applied to WM frames; WM rollout error and IDM error swept independently on shared eval ICs; DreamGen Bench correlation per the paper; original dict toy kept. Month 9 **9 lessons / 2 340 min**. With G4: site then **71 lessons / 18 120 min**; after G5–G7: site **71 lessons / 18 570 min** (from `src/lib/curriculum.ts`).

## Batch-5 PR2 (+210 here)

9.6 `nav-arm-compose`:240→450. M9 **2340→2550 min**,9 lessons;this PR site **20310→20700** with5.4+180,M5=1800. Shared corridor/start-goal/noise,5 seeds,equal speed/acceleration;mutex communication is extra information;holonomic reciprocal-stop is an ORCA-inspired sketch,not the full LP. Collision episodes,actual/capped arrival times,deadline misses,finite deadlock/starvation proxies and min separation all retained. No winner presumed. Curriculum IL paper reading only,以论文为准;real fleet本页未运行. / 相同输入与运动约束，披露预约额外信息和简化边界，保留所有失败，不复现论文。

## Batch-5 PR3 (+180 here)

9.1:240→420; M9 **2550→2730**,9 lessons. Site **20700→21090** with M10+210 (1860). Same planning stream, genuine stale-prefix rejection, charged revalidation/root fallback, bounded expansions; node counts only, no wall-clock claim. Cache is our sketch, not an MTC API promise; Panda/SO-101本页未运行. Batch-5 final totals applied now, not in earlier PRs.
