# Month 7 plan: Simulation, reinforcement learning & 3D perception

Current / 当前：**M7 3510 min**, Batch-22 PR3. Earlier entries below retain their historical totals.

## Batch-20 PR3 / 本月 H6 (+210)

Base `38f5083ba5eaf0de84cc822c6eb698b277596d73` (batch-20 PR2 #182 merged; site **37560**). PR3 on M7 host: **M7 3120→3330 (+210)**; M9 moves in the same PR on its own plan. Site **37560→37980** (37980=37560+210+210), still 71 lessons.

- **H6 / 7.6 perception-to-grasp: 480→690 (+210).** GraspVLA (`graspvla_syngrasp_pretrain_toy.py`; common random numbers, 5 seeds). arXiv 2505.03233 abs page checked (title *GraspVLA: a Grasping Foundation Model Pre-trained on Billion-scale Synthetic Action Data*; **13 authors**: Shengliang Deng, Mi Yan, Songlin Wei, Haixin Ma, Yuxin Yang, Jiayi Chen, Zhiqi Zhang, Taoyu Yang, Xuheng Zhang, Wenhao Zhang, Heming Cui, Zhizheng Zhang, He Wang) and PDF body (v3) read: SynGrasp-1B with domain randomisation; Progressive Action Generation box → grasp pose → flow-matching action; Internet grounding supervises only the box step; paper success rates 以论文为准, not reproduced. Declared toy parameters: 8-D appearance, 6 synthetic + 4 web categories, 30 samples per category, 3 objects, 60 scenes, DR gain 0.4–1.6 / offset −0.5–0.5, real gain 0.60 / offset 0.35, ORI_SIGMA=5.0 deg, ORI_TOL=10.0 deg. Hand calcs (printed): chance pick 0.3333 (0.2000 with 5 objects); grasp ceiling 0.9545. in_family: paired B−A success `0.5400±0.1217`, **clear**, 5/5 — pre-declared win held; shuffled labels paired D−B success `-0.6467±0.1114`, **clear**, 5/5, **kept**; **no-DR did not lose**: paired C−B success `0.0233±0.0630`, near-tie — the expected DR benefit did not appear, printed as it came out. web_category: paired B−A success `0.5667±0.1074`, **clear**, 5/5; C ties B on every seed (pre-declared possible). single_object: every arm identical on every seed (pre-declared near-tie or tie). Alternatives on the same seeds, written before the first run: narrow DR (paired Bwide−Bnarrow success `-0.0367±0.0492`, near-tie), N_OBJ=5 (paired B−A success@alt `0.6333±0.1054`). One code change after the first run, to the closing printed sentence only (it claimed DR was needed); disclosed on the lesson pages. ≠ force-closure ε; ≠ Dex-Net; ≠ Tobin detector DR. GPU / SynGrasp-1B / LIBERO / real grasp cell 本页未运行. / GraspVLA：先定位在杂乱和网络类别上胜，标签错乱输，不做 DR 没有输。

**Allocation / 安排:** 30+20+50+50+60=210 minutes.

## Batch-20 PR2 / 本月 H4 (+150)

Base `bf2716c4ad5d843f4e1c5a8cf4e62b0bd357d81c` (batch-20 PR1 #181 merged; site **37230**). PR2 on M7 host: **M7 2970→3120 (+150)**; M5 moves in the same PR on its own plan. Site **37230→37560** (37560=37230+180+150), still 71 lessons.

- **H4 / 7.4 sim-to-real: 390→540 (+150).** Tobin-style visual domain randomisation (`tobin_visual_domain_randomization_toy.py`; common random numbers, 5 seeds). arXiv 1703.06907 abs page checked (title *Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World*; 6 authors: Josh Tobin, Rachel Fong, Alex Ray, Jonas Schneider, Wojciech Zaremba, Pieter Abbeel) and PDF body read; paper numbers (1.5 cm, 38/40, fewer than 1,000 textures) 以论文为准, not reproduced. Declared toy parameters: 24-px row, 4.0 px object, 600 training rows, 3-NN, PALETTE=200, U=30.0 px/s, TAU_REAL=0.10 s, TAU_SIM=0.05 s, TOL=1.0 px. Hand calc (printed): wrong-τ aim error 1.5000 px. heldout: paired B−A loc_err `-3.4207±0.8743`, **clear**, 5/5 — pre-declared DR win held. canonical: paired B−A loc_err `0.1828±0.0448`, **clear**, 5/5 — B loses (pre-declared possible), **kept**. moving: paired C−B success `-0.3300±0.1110`, **clear**, 5/5 — wrong τ loses even with visual DR, **kept**. Alternatives on the same seeds, written before the first run: PALETTE=10 beats PALETTE=200 (paired B200−B10 loc_err `0.7390±0.3862`) — the **opposite** direction from the paper's ablation, printed as it came out; TOL=2.0 px hides the τ error (paired C−B success@alt `-0.0450±0.0818`, near-tie). ≠ contact-DR; ≠ lag sysid; ≠ Peng dynamics DR. GPU training / real camera / robot 本页未运行. / Tobin 式视觉域随机化：留出外观上胜，固定纹理上稍输，错误 τ 修不好。

**Allocation / 安排:** 25+25+40+35+25=150 minutes.

## Batch-18 PR2 / 本月 H4 (+180)

Base `26d4664edc52abc3a0c35b8c960ddc29d35b5057` (batch-18 PR1 merged as #173; site **35040**). PR2 on M7 host: **M7 2790→2970 (+180)**; M4 moves in the same PR on its own plan. Site **35040→35400**, still 71 lessons.

- **H4 / 7.1 mujoco-so101: 240→420 (+180).** Semi-implicit / implicit-in-velocity vs explicit Euler energy drift. Toy `mujoco_integrator_energy_toy.py`: stdlib stand-in of the MuJoCo Computation updates (not `mujoco.step`, not a redo of `grip_sweep`); shared lightly damped pendulum and a tumbling asymmetric spinner; arms A explicit / B semi-implicit / C implicit-in-velocity / C_bad flipped D. Common random numbers, 5 seeds. Stable-step: strict `h < h*=2/ω0=0.6385508568 s` (at h=h* a repeated eigenvalue −1 is a Jordan block, linear growth: hand/analytic, not printed); default `h=0.1500 s` is below it; 0.98× `h*` energy-bounded=1, 1.02× grows (spectral radius 1.490835), half step bounded. moderate_h: A−B |dE| 62.9097±3.0587 **clear** 5/5 (A blows 2/5). tiny_h: declared near-tie on |dE| **did not hold** — A |dE| 0.0346±0.0091 looks smaller because energy gain cancels damping, but |E−Eref| 0.4553±0.0855 vs B 0.0019±0.0005 is **clear** (kept). large_h_spin: pendulum A blows 5/5, |dE| 92.5926±16.7441; spinner A and B **tie** (identical velocity update) at 52.8938±16.4901, C 13.3682±0.2701, A−C **clear** 39.5256±16.3407 5/5. inconsistent_D: C_bad blows 5/5, C_bad−C 12514.0224±6611.4795 **clear** (kept). Alternative `C_damp=0`: B and C **tie**, A still loses. Real MuJoCo / Menagerie 本页未运行.

**Allocation / 安排:** 30+30+40+50+30=180 minutes.

**Site accounting / 全站核算:** **35400=35040+360** with M4 +180 on month-4-plan.md; **M7=2970**, **71 lessons**.

## Batch-16 PR2 — TD3 on rl-foundations (+180)

Base `208706f` (batch-16 PR1 merged as #165; site **32820**). PR2 on M7 host: **M7 2610→2790 (+180)**; M5 moves in the same PR on its own plan. Site **32820→33180**, still 71 lessons.

**H / 7.x rl-foundations:** `rl-foundations` 450→**630**. Toy `td3_clipped_double_q_toy.py`: 1-D continuing plant, critics linear in (1, s, a, s², a², s·a), actor a = clip(k·s + b); arms A DDPG-style single critic / B TD3 (two critics, minimum, target smoothing N(0, 0.2) clipped ±0.5, actor and targets every d = 2) / C TD3 without the delay; shared start states, exploration, reward noise, minibatches, smoothing noise and initial weights (common random numbers, 5 seeds). No integration step; critic SGD stability LR·max|φ|² = 0.2700 < 2 asserted (limit LR 0.0741; tests at 0.98× / 1.02×). noisy_reward: B−A bias −0.3451±0.0468 clear 5/5, return near-tie; easy: B−A bias −0.3765±0.0563 and absbias −0.2847±0.1360 clear 5/5, return near-tie; bandit_no_bootstrap (γ = 0): TD3 loses return −0.2140±0.0683 clear 5/5, C−A tie on every seed. C−A line added after the first run (disclosed). Paper numbers 以论文为准; MuJoCo / GPU 本页未运行.

**Allocation / 安排:** 30+30+40+50+30=180 minutes.

**Site accounting / 全站核算:** **33180=32820+360** with M5 +180 on month-5-plan.md; **M7=2790**, **71 lessons**.

## Batch-15 PR2 / 本月 H4 (+180)

Base `d0da082` (batch-15 PR1 merged as #161; site **31710**). PR2 on M7 host: **M7 2430→2610 (+180)**; M4 moves in the same PR on its own plan. Site **31710→32070**, still 71 lessons.

- **H4 / 7.3 rl-manipulation-sim: 240→420 (+180).** Hindsight Experience Replay on sparse grasp goals. Toy `her_sparse_grasp_toy.py`: `reward_shaping.py`'s grid made goal-conditioned, tabular Q indexed by the goal-relative offset (chosen after the first run; the (goal, cell, grip) table printed), replay-only learning with 64 updates per episode (no integration step, discrete grid); arms A sparse / B sparse + HER future k = 4 / C dense; shared episode starts, goals and exploration draws (common random numbers, 5 seeds). near_goal: final **tie**, auc **near-tie**; fixed_goal: B−A 1.0000±0.0000 clear 5/5, B−C **tie**; far_goals: B−A auc 0.5846±0.4715 clear 5/5, B−C **near-tie**; big_grid (added after the first run, 8×8 printed): A = B **tie** at 0, B−C −0.4321±0.2232 clear 5/5 (HER loses). SB3 HER / ManiSkill3 本页未运行.

**Allocation / 安排:** 30+30+40+50+30=180 minutes.

**Site accounting / 全站核算:** **32070=31710+360** with M4 +180 on month-4-plan.md; **M7=2610**, **71 lessons**.

## Batch-13 PR2 / 本月 H4 (+180)

Base `a95f352` (batch-13 PR1 merged; site **29490**). PR2 on M7 host: **M7 2250→2430 (+180)**; M5 moves in the same PR on its own plan. Site **29490→29850**, still 71 lessons.

- **H4 / perception-to-grasp: 300→480 (+180).** Planar two point contacts with Coulomb friction (cone edges `n ± μ t`), wrenches `(fx, fy, τ/L)`, L1 grasp wrench space = hull of four primitive wrenches; force closure = origin strictly inside; ε = distance to the nearest facet (stand-in, labelled); lift stand-in = resist one shared disturbance with total normal force ≤ 1 (exact check over wrench triples). Toy `antipodal_force_closure_toy.py`: shared true / perceived poses, 8 jaw candidates and disturbances (common random numbers, 5 seeds × 40 trials); arms random first candidate / largest-ε antipodal on the perceived object / B's grasp with μ = 0. disc_noisy_centre: B−A fc 0.3500±0.0685 clear 5/5, lift clear with 1 of 5 opposite; box_near_perfect: B−A fc **tie: identical on every seed**, eps and lift small but consistent; box_pose_error: fc clear 5/5 but lift near-tie (0.0600±0.0877), 100 of 200 picks force closure only on the perceived box; frictionless C never force closure. ≠ Dex-Net GQ-CNN; ≠ MoveIt collision-only; ≠ hand-eye. Real gripper / GPU 本页未运行.

**Allocation / 安排:** 30+40+40+40+30=180 minutes.

**Site accounting / 全站核算:** **29850=29490+360** with M5 +180 on month-5-plan.md; **M7=2430**, **71 lessons**.

## Batch-12 PR2 / 本月 H4 (+180)

Base `ad9407a` (batch-12 PR1 merged; site **28380**). PR2 on M7 host: **M7 2070→2250 (+180)**; M5 moves in the same PR on its own plan. Site **28380→28740**, still 71 lessons.

- **H4 / depth-pointcloud: 450→630 (+180).** Local PCA normals: k-NN covariance, eigenvector of the smallest eigenvalue (stdlib cyclic Jacobi), flipped toward the viewpoint; neighbourhood size vs noise / curvature; orientation ambiguity. Toy `pointcloud_pca_normals_toy.py`: shared height-field cloud, depth-noise draws and queries (common random numbers, 5 seeds); arms global plane (no per-point normals) / PCA k = 20 / PCA k = 4. flat_low_noise: k = 20 loses to the global plane on angle (paired B−A 0.7449±0.0397°), residual a small but consistent gap in B's favour (metric rewards fitting noise); ripple_noisy: k = 20 wins; fine_ripple_low_noise: k = 4 beats k = 20 on angle (paired B−C 5.2476±0.4954°). ≠ voxel/RANSAC-only; ≠ ICP. Open3D / PCL on a real sensor 本页未运行.

**Allocation / 安排:** 30+30+40+50+30=180 minutes.

**Site accounting / 全站核算:** **28740=28380+360** with M5 +180 on month-5-plan.md; **M7=2250**, **71 lessons**.

Site supplement beyond @DeRonin_'s 6-month roadmap. Proposal: `/workspace/proposals/m7-m8-proposal.md` §2 / §5 / §6.
Batch 1 (merged #83): scaffold all six lessons; full MDX + examples for **7.1, 7.2, 7.5**.
Batch 2 (this PR): full MDX + examples for **7.3, 7.4, 7.6**; curriculum promoted; portfolio / grip mass nits.
Electives E7-a/b/c stay on the month page topics only (not formal lessons, not in minutes).

Constraints: no shared month-4 pixi; private venv for MuJoCo (`M7_PYTHON`). Runnable toys prefer stdlib / NumPy CPU with fixed seeds. GPU / GUI / true SB3 / ManiSkill / Open3D / SAM2 / Menagerie meshes marked「本页未运行」or「本页未强制」/「需硬件」. Hard facts re-fetched from primary sources (2026-11-04 UTC+8), not copied from the proposal.

| # | slug | minutes | this batch | runnable | verified against |
|---|------|---------|------------|----------|------------------|
| 1 | `mujoco-so101` | 240 | batch 1 | `grip_sweep.py` + `grip_scene.xml` (needs mujoco) | Menagerie robotstudio_so101; MuJoCo modeling/XMLreference; SO-ARM100 Simulation/SO101 |
| 2 | `rl-foundations` | 450 | batch 1 | `ppo_reach.py` (stdlib) | SB3 PPO docs; Gymnasium; Spinning Up; arXiv 1707.06347 |
| 3 | `rl-manipulation-sim` | 240 | **full** | `reward_shaping.py` (stdlib) | ManiSkill install + PickCubeSO100-v1; SB3 SAC; arXiv 1801.01290 / 2410.00425 |
| 4 | `sim-to-real` | 390 | **full** | `sysid_fit.py` + `randomize_eval.py` + `contact_dr_toy.py` (stdlib) | Tobin arXiv 1703.06907; Peng arXiv 1710.06537; Isaac Lab README (Sim 6.2); ISO 10218-1 403 → soft safety wording |
| 5 | `depth-pointcloud` | 450 | batch 1 | `cloud_pipeline.py` (stdlib) | Open3D APIs; Depth Anything V2 licences |
| 6 | `perception-to-grasp` | 300 | **full** | `handeye_toy.py` (NumPy) + `grasp_from_mask.py` (stdlib) | OpenCV `calib3d.hpp` calibrateHandEye (TSAI/Park; ≥3 poses; eye-in-hand vs eye-to-hand); SAM2 LICENSE Apache-2.0 |

Rechecks from proposal §6 (batch 2):
- OpenCV `calibrateHandEye` via raw `calib3d.hpp` (HTML previously 403) — signature + ≥3 poses + eye-in-hand/eye-to-hand notes confirmed.
- ISO 10218-1 still Cloudflare/403 — not cited as hard clause numbers; general e-stop / torque / speed language only.
- Isaac Lab README: GPU-accelerated; Isaac Sim workflows target Isaac Sim 6.2 — elective only, no invented install steps (install HTML scrape empty / path 404).
- micro.ros.org hardware page still not used (M8).

Widgets: RewardCurveWidget / PointCloudWidget deferred (must be measurable via check_widgets; not in this batch).

Verification: `examples/month-7/check.sh` (hooked into `tools/sim/reproduce.sh`), check_diagrams bindings + mutations, check_quotes, lint, tsc, CI build, check_text_size.

Batch-after-obs PR3 (G5, +150): 7.4 `sim-to-real` 240→390 — `contact_dr_toy.py`: contact-parameter DR (friction µ, mass) vs latency-only randomisation tuning one push speed on the same budget (41 candidates × 200 episodes) and seed stream; nominal and shifted µ / mass reported (DR ties nominal success but pays cycle time 0.72 → 1.08 s; fails outside its range at µ = 0.15). No τ refit, no PE narrative; toy friction ≠ MuJoCo. Month 7 **6 lessons / 1 650 min**; site **71 lessons / 18 570 min**.

## Batch-4 PR2 (locked H1/H6)

H1 7.5 240→450 (+210): thresholded Gaussians are not hard surfaces; shared scene/query sphere collision, independent distance truth vs conservative AABB and finite-s K(s) witness test. Month 7 **1 860 min** (1 650 + 210); **2 070 is the future PR3 total after H2 +210**, not this PR. No occupancy A* redo; GPU 本页未运行.

Site: **71 lessons / 19 440 min** (19 050 + 390). See `batch-4-pr2-sources.md` for source checks and the M7 arithmetic correction.

## Batch-4 PR3 (last planned PR)

H2 7.2 240→450 (+210): Plant-A pretrained tracker → shared160 Plant-B transitions per arm → SysID-retune/DR-widen/residual-action simulation fine-tuning → policy-only B deployment. Five seeds with spread; no universal winner; not PPO/contact-DR/PE redo. M7 **2070 min** (1860+210).

Site **71 lessons /19830 min** (19440+390); M7=2070,M11=3000. New material precedes final bilingual Summary. Source/limit audit: `batch-4-pr3-sources.md`.
