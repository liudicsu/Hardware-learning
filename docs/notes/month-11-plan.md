# Month 11 plan: Actuator hardware, tactile contact & cross-embodiment collection

Current / 当前：**M11 3990 min**, Batch-22 PR3. Earlier entries below retain their historical totals.

## Batch-22 PR3 / 本月 H6 (+180)

Base `0193f7837fcf135a369a678d1abac948651bda88` (batch-22 PR2 #190 merged; site **39780**). PR3 on M11 host: **M11 3810→3990 (+180)**; M7 moves in the same PR on its own plan. Site **39780→40140** (40140=39780+180+180), still 71 lessons.

- **H6 / 11.4 umi-style-collection: 420→600 (+180).** EgoVLA (`egovla_human_pretrain_retarget_toy.py`; common random numbers, 5 seeds, 4 tasks per seed). arXiv 2507.12440 abs page checked (title *EgoVLA: Learning Vision-Language-Action Models from Egocentric Human Videos*; 15 authors in arXiv order: Ruihan Yang, Qinxi Yu, Yecheng Wu, Rui Yan, Borui Li, An-Chieh Cheng, Xueyan Zou, Yunhao Fang, Xuxin Cheng, Ri-Zhao Qiu, Hongxu Yin, Sifei Liu, Song Han, Yao Lu, Xiaolong Wang) and HTML/PDF body (v3) read: wrist pose plus MANO hand parameters, IK and MLP retargeting, robot post-training required (zero-shot 0 % on all tasks); ablation numbers 以论文为准, not reproduced. Declared toy parameters: D=16, P=17, B_ROBOT=1.0, OFFSET_MISMATCH=1.5, SIG_DEMO=0.5, 32 / 16 demos, TOL=0.5, LAM 0.25 (A) / 25 (B). Hand calcs (printed): 0.5510, 0.4000, 0.6358 / 0.1635, 0.7887 / 0.3869, offset 3.0000× tolerance. in_domain_full: C−A short_sr `-0.6320±0.0746`, **clear**, 5/5; B−A long_sr `0.4300±0.1430`, **clear**, 5/5; B−A short_sr `0.2220±0.0968`, clear. half_data: B−A long_sr `0.4900±0.0775`, clear; half-data B minus full-data B long_sr `-0.1620±0.0841`, **clear**, 5/5. large_mismatch: B−A long_sr `-0.2180±0.0955`, **clear**, 5/5 — over-trusted wrong prior loses (declared possible), **kept**. All declared regimes held in the kept output. Alternatives on the same seeds, written before the first run: LAM_B=5 (B−A long_sr `-0.1180±0.1085`); TOL=0.7 (B−A long_sr `0.4140±0.1724`); OFFSET_MISMATCH=0.5 (C−A long_sr `-0.1860±0.0713`); none adopted. Code changes after the first run: a syntax-error fix before any output; then, after a full run had printed, a ridge-solver bug fix (missing symmetric intercept row of the normal equations) that changed results — in the buggy run the half-data drop on long_sr was a near-tie; no parameter changed; disclosed on the lesson pages. ≠ UMI relative / absolute / delta; ≠ FLARE; ≠ GraspVLA. EgoVLA model / MANO / Isaac Lab / humanoid 本页未运行. / EgoVLA：接近的人类先验加后训练胜过只用机器人数据，零样本因偏置失败，过度信任的错误先验落败。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

## Batch-22 PR2 / 本月 H4 (+180)

Base `833aac3e5ab0a197f7f1dcb155ad3c4f7c956b15` (batch-22 PR1 #189 merged; site **39420**). PR2 on M11 host: **M11 3630→3810 (+180)**; M5 moves in the same PR on its own plan. Site **39420→39780** (39780=39420+180+180), still 71 lessons.

- **H4 / 11.1 power-battery-emc: 690→870 (+180).** NTC inrush limiter (`ntc_inrush_limiter_toy.py`; common random numbers, 5 seeds; one capacitor, source-resistance, tolerance and ambient draw per regime and seed, shared by all four arms). Wikipedia Inrush current body read (rev 1326751079; 以原文为准): a discharged capacitor looks like a short, limited only by source resistance and ESR; NTC self-heats; just after switch-off a hot NTC cannot limit inrush unless it cools for more than 1 minute. Wikipedia Inrush current limiter body read (rev 1312732367; 以原文为准): high cold resistance, self-heating, 100 % of supply voltage cannot reach the load, fixed resistor never falls, relay / MOSFET bypass. Declared toy parameters: 24 V source, R_SRC 0.05 ohm, 2200 µF, 12 ohm load (6 ohm heavy), R25 5 ohm, BETA 3500 K, R_TH 60 K/W, C_TH 0.5 J/K, 0.05 s window, I²t budget 1.0 A²s. Hand calc (printed): 480.0000 A, 4.7525 A, 12.6720 A²s, 0.1255 A²s, 0.6336 J, 1.9917 A. cold_start: A−B peak_a `483.8672±62.9814`, **clear**, 5/5; B peak `4.2502±0.2690` A; A fails the budget; C−B peak_a `0.3278±0.0755`, **small** (declared "may near-tie" did **not** hold as a near-tie); B−D v_drop_ss `0.7479±0.0153`, clear; C−B p_ss `8.6198±0.2385`, clear, **kept**. hot_restart (declared model assumption, no cooling time): B peak `56.1052±0.8280` A, B i2t `1.7419±0.1192` A²s fails the budget on every seed; A−B fuse_ok **tie** (both fail). heavy_load: C−B p_ss `21.3877±0.1482`, clear; C−B peak_a `-0.1153±0.3361` near-tie. Alternatives (declared, same seeds): R25=10 → C−B p_ss `10.0913±0.0408`; R_TH=30 → A−B peak_a `510.6694±38.8185`; budget 0.25 → A still fails; none adopted. No code change after the first run. ≠ fuse certification; ≠ coulomb SoC + derate; ≠ Peukert. Real PSU / NTC / fuse 本页未运行. / NTC 浪涌限流，不宣布实测。

**Allocation / 安排:** 30+25+50+40+35=180 minutes.

## Batch-12 PR3 / 本月 H6 (+210)

Base `4982bb2` (batch-12 PR2 merged; site **28740**). PR3 on M11 host: **M11 3420→3630 (+210)**; M9 moves in the same PR on its own plan. Site **28740→29160**, still 71 lessons.

- **H6 / cross-embodiment-datasets: 540→750 (+210).** X-VLA (arXiv 2510.10274): per-source learnable soft prompts, soft-prompted Transformer encoders, Phase I pretraining and Phase II prompt warm-up with a frozen backbone. Toy `xvla_soft_prompt_toy.py`: bilinear stand-in `a = (Σ h_e[j] T_j) x`; arms pooled map / one-hot ID as fixed prompt (= separate heads) / K = 2 learned prompts with a shared backbone (ALS); adaptation to a held-out embodiment with 4 demos; common random numbers, 5 seeds. single_embodiment: A = B identical on every seed, C near-tie on seen data, C loses on the new embodiment; shared_low_rank: C wins both metrics; unrelated_full_rank: C loses on seen data (paired C−B 0.5499±0.0422). ≠ OXE-AugE; ≠ UniVLA latent actions. Benchmarks 以论文为准; GPU 本页未运行.

**Allocation / 安排:** 40+40+50+50+30=210 minutes.

**Site accounting / 全站核算:** **29160=28740+420** with M9 +210 on month-9-plan.md; **M11=3630**, **71 lessons**.

## Batch-10 PR2 / 本月 H6 (+210)

Base `59aa6df`. PR2 only on M11 host: **M11 3210→3420 (+210)**; M1 +150 on month-1-plan.md. Site **26160→26520**, still 71 lessons.

- **H6 / 11.1 power-battery-emc: 480→690 (+210).** Shared-return ground-loop IR vs star vs kelvin; V=I·R literacy; physical I_bias·R_sense; R_MOTOR_FEED reported off sense; L·di/dt not modelled; ≥5 seeds; ≠ SoC shunt-bias; ≠ shield prose-only. Chassis 本页未运行. / 共享回流跳动，不宣布暗室结果。

**Allocation / 安排:** 45+45+45+45+30=210 minutes.

**Site accounting / 全站核算:** **26520=26160+360**, **M11=3420**, **71 lessons**.


Site supplement beyond @DeRonin_'s 6-month roadmap (Months 7–11). Lessons open with "This lesson is a site supplement — Months 7–11 are not part of the original six-month course." / 「本课是本站补充内容——第 7–11 个月不属于原六个月课程。」

**PR1–PR3:** full MDX + examples for **11.1–11.7** (PR1 #99: 11.1–11.3, PR2 #100: 11.4–11.5, PR3: 11.6–11.7 + this plan). Month 11 deliberately adds hardware back (power / EMC, FOC, touch) next to the newest collection, data and control directions. It does not replace the 8.7 capstone and does not open a new track; 11.7's "contact-modality experiment" is an optional advanced portfolio section.

Constraints: no required purchases — not DIGIT / GelSight Mini, a BLDC kit, a GoPro or a humanoid robot. Runnable toys are stdlib CPU with fixed seeds (the 11.5 imbalance toy is deterministic; the score toy uses seed 29), outputs pinned in `examples/month-11/expected/` and checked by `examples/month-11/check.sh` (7 of 7, also run by `tools/sim/reproduce.sh`). FOC flashing, battery / scope probing, tactile capture, GoPro / SLAM, OXE download, Isaac / MuJoCo training and humanoid sim2real are marked「本页未运行」. Paper numbers come only from abstracts / bodies opened at writing time and carry「以论文为准」; real OXE counts never enter CI.

| # | slug | minutes | runnable | verified against |
|---|------|---------|----------|------------------|
| 1 | `power-battery-emc` | 690 | `power_budget_toy.py`, `power_roundtrip_loss_toy.py`, `soc_coulomb_thermal_toy.py` | Novanta EMC wiring KB; Roboteq EMI blog; ARK power & grounding |
| 2 | `foc-actuator-lab` | 480 | `clarke_park_toy.py`, `foc_current_loop_toy.py` | SimpleFOC home + `foc_theory` / `foc_implementation` / alignment / voltage_torque docs |
| 3 | `tactile-sensing` | 420 | `tactile_marker_toy.py`, `tactile_debias_recal_toy.py` | AnySkin arXiv 2409.08276; DIGIT design / interface repos; GelSight (Yuan 2017); 3D Cal arXiv 2511.03078 (abstract) |
| 4 | `umi-style-collection` | 420 | `relative_traj_toy.py` | UMI arXiv 2402.10329 v3 + project page / Hardware Guide; LeRobot action representations |
| 5 | `cross-embodiment-datasets` | 540 | `oxe_imbalance_toy.py`, `oxe_auge_score_toy.py`, `univla_latent_action_toy.py` | OXE project page + GitHub; OXE-AugE arXiv 2512.13100v1 HTML §4.2 + A.5 + project page; UniVLA arXiv 2505.06111 |
| 6 | `humanoid-wbc-overview` | 480 | `lipm_track_toy.py`, `floating_base_contact_toy.py` | ALIP arXiv 2408.05308 §II-A (3) / §III (20); ASAP arXiv 2502.01143 (abs + HTML, Table V) + code; HugWBC / Holosoma / TWIST / WBC-AGILE repos (README level) |
| 7 | `contact-rich-policies` | 390 | `tactile_gate_toy.py`, `contact_slip_residual_toy.py` | AnySkin Table III; BAKU arXiv 2406.07539; ViTaMIn 2504.06156 / exUMI 2509.14688 (abstract level, no numbers) |

Total **2 460 minutes** after all three deepen PRs (power +150, FOC +240, tactile +180, OXE +150, contact Jacobian +240); site total was then 71 lessons / 16 410 minutes (after follow-up PR1). M9 was 2 100 minutes then (now 2 340 after G3; site 18 570). This completes the in-place deepen batch; no new month or slug.

Pointers: M2 motors-drivers → 11.2; M3 gripper-fingers → 11.3; 8.1 dataset-engineering → 11.5; 10.1 flow-matching → 11.4; M7 / M8 / M10 legged / Isaac electives → 11.6; M8 / M9 / M10 topics FOC → 11.2, tactile → 11.3 / 11.7; 8.7 capstone and 6.5 portfolio → Month 11 (optional, not a replacement). Banners and message ranges say Months 7–11.

Deepen PR1 (`feat/deepen-power-foc`): 11.1 round-trip IR + I²R + fuse data gates (`insufficient_data` / `reject_known_constraint` only, never `ok_slow_blow`); 11.2 electrical angle + dq PI on an R–L circuit with plant θ_e★ never fed to the controller; wrong offset / wrong p compared under identical noise.

Audit fix (#102): 11.4 toy uses fixed-anchor T0⁻¹ Tk vs step-wise delta (delta_accum 0.008287 vs relative_err 0.001875; not zero); bias demo abs 0.033248 / rel 0.000829 / bias-only 0; 11.1 EMC objectives match four-grounds / HF both-end termination (no blanket single-end rule); 11.5 drops leftover「下一批 PR」; LIPM docstring = capture-point fall.

Still electives / not run here: LeKiwi build, external F/T, Isaac Lab-scale training, on-robot DIGIT / GelSight Mini / BLDC / GoPro / humanoid runs; ViTaMIn / exUMI / MiTaS full-table numbers stay unverified.

Widgets deferred. No prices anywhere.

Verification: `examples/month-11/check.sh` (7 lessons / 12 output checks same), check_diagrams, check_quotes, lint, tsc, CI build.

Deepen PR2: synthetic tactile axes/signs, rest debias, independent skin-swap gain recalibration, shared evaluation noise, first-contact data gate (dimensionless, not measured Newtons; policy integration stays 11.7). OXE-AugE stages mask fusion → inpaint → base-position tune → replay/composite are documentation, not a CPU augmentation implementation. A.5 milestone scores 0.3/0.5/0.8/1.0, 10×4 trials, score mean±SE ≠ binary success; 24–45 % lift denominator uncertain (absolute vs relative). Toy outcomes are synthetic; no real OXE cardinality enters CI.

Deepen PR3: six-DOF sagittal base+leg, no arm; two-row point-position Jacobian and velocity no-slip residual Jc qdot=0. Full Jc stays rank2 even for a straight leg; joint-only rank1 is a separate warning. Nullspace pitch regulation checks JcN≈0. Force-only point screen omits moments; finite sole adds CoP bounds on shared synthetic demand, neither screen certifies full dynamics. 11.4 links causal stream alignment in 8.3; 9.3 explains effort-out impedance vs motion-out admittance. All three affected month checks, diagrams, quotes, lint, tsc and CI build are required. Whole deepen batch goes to audit only after reviewer merges this final PR.

Follow-up PR2 (+210): 11.7 `contact-rich-policies` 180→390 — same-frame velocity residual `v_meas − J(q)·qdot` (m/s, never N − m/s), contact break only from an assumed force-threshold flag, slip as a toy proxy (not a GelSight/AnySkin classifier), shared noise across stick/slip/break; points to 11.6 `J_c qdot`. Month 11 **2 670 min**; M8 **2 340**; site **71 lessons / 16 800 min** (from `src/lib/curriculum.ts`).

Follow-up PR3 (F5–F7 on M5/M6, +510): Month 11 stays **2 670 min**. Site **71 lessons / 17 310 min**.

Batch-4 PR1 (+150 on 11.1 only in this PR): `power-battery-emc` 330→480 — coulomb-counting SoC with discharge-positive sign, η on charge only, shared current profile across shunt-bias / Q-error / SoC0-error arms, lesson-defined thermal derate, OCV rest re-anchor as concept only; no charging procedure. Month 11 **2 820 min**; site **71 lessons / 19 050 min** (M2 1500 / M4 1620 after the sibling encoder + EtherCAT deepenings in the same PR).

## Batch-4 PR3 (last planned PR)

H7 11.4 240→420 (+180): unilateral position teleop; distinct one-way/control/video RTT; explicit display-age plus operator reaction; stop-advance/miss metrics; passivity/wave-variable survey reading, not bilateral proof. M11 **3000 min** (2820+180).

Site **71 lessons /19830 min** (19440+390); M7=2070,M11=3000. New material precedes final bilingual Summary. Source/limit audit: `batch-4-pr3-sources.md`.

## Batch-9 PR3 / 本月 H6 (+210)

Base `64579b5`. PR3 only: **M11 3000→3210 (+210)** and M6 **1980→2190 (+210**, own host in month-6-plan.md); site **25380→25800**, still 71 lessons; no arithmetic mismatch with proposal §9 or curriculum.ts.

- **H6 / 11.5 cross-embodiment-datasets: 330→540 (+210).** UniVLA task-centric latent actions (arXiv 2505.06111, opened; numbers 以论文为准). Toy: two embodiments with different motor maps, shared video / wanderer / evaluation starts; A raw BC from A only, B latent with the actor split + per-embodiment linear decoder, C latent over the whole frame change (no language split), D raw BC on the decoder's 20 labels only; equal codebook, Lloyd iterations, grid and decoder labels (decoder input 2 vs 4 numbers, labelled); wanderer vs still scene; five seeds; no winner. ≠ OXE-AugE count / score toys on this lesson; ≠ 9.9 LAPA / IDM curve. VLM / GPU / robots 本页未运行. / 潜动作跨本体，不宣布赢家。

**Allocation / 安排:** 40+30+50+60+30=210 minutes. Sources: batch-9-pr3-sources.md.
