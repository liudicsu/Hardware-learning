# Month 9 plan: Long-horizon tasks, contact control & mobile manipulation

Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Proposal archive: `/workspace/proposals/m9-proposal.md`. Track B electives: `/workspace/proposals/promote-electives-proposal.md`.

**Batches 1–3 (merged):** full MDX + examples for **9.1–9.7**. **Track B:** append **9.8 `visual-servoing`** then **9.9 `world-models-overview`** (end of array only).

**Electives** (month-page further-reading only, not formal lessons): `lekiwi-build`, `micro-ros-foc`, `ft-sensor-admittance`. (`world-models-overview` promoted to 9.9; `multi-view-extrinsics`, `intervention-logging` and `edge-deploy-checklist` are now Month 10 lessons 10.3–10.5 — see `docs/notes/month-10-plan.md`.)

Constraints: private env; runnable toys prefer stdlib CPU with fixed seeds. ROS 2 / MoveIt demos / real SO-101 Present Load logging / paid LLM APIs / real LeKiwi / OpenCV webcam / world-model training marked「本页未运行」.

| # | slug | minutes | status | runnable | verified against |
|---|------|---------|--------|----------|------------------|
| 1 | `mtc-long-horizon` | 420 | full + H7 | `stage_graph_toy.py`, `mtc_stage_memory_toy.py` | MoveIt Task Constructor |
| 2 | `moveit-servo` | 180 | full | `servo_loop_sim.py` | MoveIt realtime_servo_tutorial |
| 3 | `effort-admittance` | 630 | full | `load_contact_sim.py`, `admittance_1d.py`, `impedance_vs_admittance_toy.py`, `ft_bias_gravity_toy.py` | Feetech STS3215 + ros2 admittance |
| 4 | `llm-skill-planning` | 240 | full | `saycan_score_toy.py` (fake LLM) | SayCan arXiv 2204.01691 |
| 5 | `failure-recovery` | 330 | full + batch-8 H4 | `recovery_bt_toy.py`, `recovery_escalate_budget_toy.py` | Inner Monologue + BT.CPP Fallback / RetryUntilSuccessful |
| 6 | `nav-arm-compose` | 450 | full + H2 | `nav_pick_bt.py`, `multi_robot_corridor_toy.py` | LeKiwi elective; ORCA primary / MRS curriculum IL reading |
| 7 | `multi-skill-demo` | 180 | full | `demo_gate.py --all` | Thin demo; does not replace 8.7 |
| **8** | **`visual-servoing`** | **420** | **Track B + batch-8 H3** | **`tag_error_jog.py`**, **`ibvs_interaction_matrix_toy.py`** | OpenCV ArUco/PnP docs; Servo command side; ViSP IBVS tutorial + Wikipedia (secondary) |
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

## Batch-6 PR2 / 本月 H5 (+210)

9.3 effort-admittance **420→630**, M9 **2730→2940**, nine lessons. Sensor-frame synthetic static wrench, declared payload-on-sensor sign; six orientations ×16=96 free-space rows identify mass, COM and six offsets by LS. Twelve held-out poses, five seeds, shared contact/noise; raw / one-pose tare (first 16 rows only, disclosed) / estimated bias-only / estimated gravity compensation. No oracle parameters, force/torque RMSE, F1 and free-space false triggers with mean/std/min/max. Single-pose zero fails when orientation changes; rank-deficient calibration rejected. / 明确轴向与原点，不把 Load 当牛顿，不替换旧路径；真实 F/T 本页未运行，无需购买。

Allocation 45+45+45+45+30=210 min. Sources: opened/curl200 ft_tools_ros2 calibration README and official Jazzy admittance frames/CoG docs; sign convention difference stated. / 已打开并核对来源，不冒称运行软件包。

M8 separately +180: **21570+180+210=21960**, **M8=2850**, **M9=2940**, **71 lessons**. M1/M2 remain 1020/1980; no PR3 minutes. All additions before sole final Summary, en/zh code/stdout identical, old expected outputs unchanged. / 正确月标题，仅计本 PR。

## Batch-8 PR2 — IBVS and escalation budget (Month 9 hosts only)

Base166392f, after #133. H3 9.8 visual-servoing 240→420 (+180), H4 9.5 failure-recovery 180→330 (+150).
M9 **2940→3270**, nine lessons; site **23910→24240** (+330), still 71 lessons. No arithmetic mismatch with proposal §9 or curriculum.ts on 166392f. Earlier table rows above now show current per-lesson minutes; historical batch paragraphs keep their own totals.

- H3: 40 min PBVS/IBVS error spaces and 2×6 point interaction matrix +40 min shared-estimate setup (same noisy points, model scale, λ, cap, FOV; no true-depth oracle) +50 min wrong-Z / near-edge / large-roll / rank-deficient readings over five seeds +50 min exercises =180. Formula from the opened ViSP IBVS tutorial; camera retreat/singularity literacy from Wikipedia (secondary). LAAS course notes returned an Anubis bot-check page to curl, so they are not cited. Not 9.2 Servo κ-scale, not 10.4 extrinsics. Webcam/OpenCV/robot 本页未运行.
- H4: 35 min ladder and rung costs +35 min shared failure stream / common random numbers / equal detect signal +40 min three arms and operator-budget sweep over five seeds +40 min handoff schema and exercises =150. Autonomous Retry+Fallback carries most recoveries; human handoff is never the only success path. Not 8.5 watchdog, not Nav2 recoveries, not MTC stale prefix; 10.5 intervention merge only cross-linked. Real robot / operator console 本页未运行.
- New sections, code, stdout and exercises sit before each sole final Summary; each Summary gained one sentence in en and zh. No winner declared in either toy. Excludes VQ-BeT and dual-system (PR3).
