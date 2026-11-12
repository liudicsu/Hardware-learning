# Batch-18 polish sources / 来源记录

Base `b40f95f80583b290ad4952385f4e4f32562bc2c9` (main after #175; site **35820**, M4 **3030**, M7 **2970**, M10 **3750**). Minutes unchanged (**35820**); no lesson added or removed. Host minutes stay slam-nav 810, mujoco-so101 420, flow-matching-policies 870, edge-deploy-checklist 540, gripper-fingers 570.

## 1. Explicit Euler, backward Euler, and D=0 (7.x mujoco-so101)

MuJoCo Computation, Integrators, https://mujoco.readthedocs.io/en/stable/computation/index.html, body already read for #174 (cached HTML/text under `/workspace/b18p2-sources/`). 以原文为准.

- Explicit Euler is described but not implemented (eq. 2). Semi-implicit Euler (eq. 3) updates position with the new velocity. Fully implicit Euler (eq. 4) takes both velocity and acceleration at t+h. `implicit` / `implicitfast` use the implicit-in-velocity update (6), `M̂ = M + h D`, and are implicit only in velocity-dependent forces. With no joint damping, `Euler` uses (3) rather than (6).
- On the undamped linear oscillator, explicit Euler has amplification eigenvalues |λ| = √(1+(h ω0)²) > 1 for every h > 0, so it is unconditionally unstable (hand calculation / analytic; no new printed number). Only fully implicit backward Euler is unconditionally stable, and it adds numerical damping (hand calculation / analytic). That is not the MuJoCo `implicit` / `implicitfast` scheme.
- When D = 0, M̂ = M and implicit-in-velocity equals semi-implicit. The existing alternative `C_damp=0.0` block already prints B−C as `0.0000±0.0000: tie: identical on every seed`; the prose now points at that printed tie and at the Computation wording.

## 2. Damped semi-implicit Jury criterion (same toy)

The toy's B_semimpl update evaluates linear damping at the *old* velocity (`a = pend_acc(th, w, damp)`, then `w_n = w + h a`, `th_n = th + h w_n`). For the linear oscillator x'' + 2 ζ ω0 x' + ω0² x = 0 this is

v(t+h) = (1 − h c) v(t) − h ω0² x(t),  x(t+h) = x(t) + h v(t+h),  c = 2 ζ ω0.

The amplification matrix has trace α = 2 − h² ω0² − h c and determinant β = 1 − h c. The Jury conditions for both eigenvalues inside the unit disk are |β| < 1, p(1) > 0 and p(−1) > 0. p(1) = h² ω0² is positive for h, ω0 > 0. p(−1) > 0 is (ω0 h)² + 4 ζ ω0 h < 4 (strict). |β| < 1 is h < 1/(ζ ω0) when ζ > 0, which is always weaker than the p(−1) bound, because h*_damped = 2 / (ω0 (ζ + √(ζ²+1))) is strictly smaller than 1/(ζ ω0). The derived criterion therefore matches the form suggested in the audit, and is used as written. At equality, λ = −1 is a *simple* eigenvalue when ζ > 0 (a period-2 mode neither grows nor decays); the Jordan block and linear growth appear only at ζ = 0 (hand / analytic).

The toy now prints, after the original table (kept ahead of the new block):

- ζ = 0.0079818857, c = 0.0500000000, h*_damped = 0.6334743577 s (`h_star_damped=0.6334743577`), default h/h*_damped = 0.2368, `assert_below_hstar_damped=1`
- 0.98× spectral_radius=0.984358, jury_lhs=3.842842, rho_lt_one=1
- 1.00× spectral_radius=1.000000, jury_lhs=4.000000, rho_lt_one=0
- 1.02× spectral_radius=1.469468, jury_lhs=4.160308, rho_lt_one=0
- default_h spectral_radius=0.996243
- a (ζ, h) table at 0.98× / 1.02× of each of ζ ∈ {0, 0.05, 0.20, 1.00}, which confirms ρ < 1 below the bound and ρ > 1 above it (at ζ = 0 the 0.98× radius stays 1.000000 on the unit circle, as in the existing undamped test)

`expected/` was regenerated; a second run is byte-identical. The undamped 0.50× / 0.98× / 1.02× tests and all regime tables are unchanged.

## 3. Knowledge Insulation official title (10.x flow-matching-policies)

The official title *Knowledge Insulating Vision-Language-Action Models: Train Fast, Run Fast, Generalize Better* was already recorded in `docs/notes/batch-18-pr3-sources.md` from the arXiv abs/PDF (HTTP **200**, body read for #175). It is now also written in the en/zh lesson prose next to the existing arXiv **2505.23705** citation. No new source was opened.

## 4. VLA-Adapter post-hoc count (10.x edge-deploy-checklist)

The toy docstring, the en/zh fair-setup paragraph, the embedded listings, and exercise 3 said “three” post-hoc changes. STEPS/LR (250 / 0.05 → 300 / 0.10) was already disclosed in a comment, in the printed header, and in `batch-18-pr3-sources.md`, and is a fourth change. All four places now say four changes and list STEPS/LR. `expected/` is unchanged (the docstring is not printed); a rerun is byte-identical to the committed file.

## 5. Stale tip-lock comments

Four live-total tip comments in `tools/check_diagrams.mjs` still named 34710 / 34 710 / 35040 as if they were the current site total, while the assertion already checked **35820**:

- `b17p3 curriculum: 34710 minutes (tip after batch-17 PR3) (tip after batch-18 PR3: 35820)`
- `b17p3 README: 34 710 minutes (tip after batch-17 PR3)`
- `b17p3 curriculum: 34710 minutes (tip after batch-17 PR3)` (the later sum check)
- `b18p1 curriculum: 35040 minutes (tip after batch-18 PR2: 35400)`

They now read 35820 minutes (tip after batch-18 PR3). Historical sources-note locks that correctly require old totals (34710, 35040, 35400, …) in past notes were left alone. No assertion value was relaxed.

## 6. Form-closure n&s sentence, and TSDF sign / wide truncation

**Form-closure (gripper-fingers).** No new primary source was opened. The added sentence cites only the two papers already body-read for #173:

- Carpin, Liu, Falco, Van Wyk, arXiv 1607.06620, §2.5 (cached `/workspace/b18p1-sources/1607.06620v1.txt`): Somov’s seven-point count is necessary not sufficient; “seven contacts points are necessary and sufficient for the special case of a three dimensional polyhedron [47]”, where [47] is Markenscoff, Ni and Papadimitriou, *The Geometry of Grasping*, IJRR 9(1):61–74, 1990.
- Zhang, Tang, Sun, Lan, arXiv 2202.03631, after Definition 1 (cached `/workspace/b18p1-sources/2202.03631v1.txt`): traces the planar “at least 4 frictionless wrenches” count to Reuleaux [202] (*The Kinematics of Machinery*, 1876; the survey’s bibliography spells the name “F Reuleax”); [156] Markenscoff et al. “proved their conjectures”, including that seven fingers suffice in most cases without rotational symmetry.

The Reuleaux book and the Markenscoff et al. PDF were not opened this round and are **not** used as primary sources. Sage’s IJRR page (DOI 10.1177/027836499000900102) was reachable but paywalled; only the abstract was visible, so it is not cited from.

**TSDF (slam-nav).** The toy’s convention is sdf = r − t_c (range minus distance to the voxel centre along the ray) and occupied when D ≤ 0, which is **negative inside / behind the surface, positive outside / in front**; `box_sdf` / `sdf_true` use the same sign. A truncation band that is too wide averages in far-away samples, including noise that is no longer a local surface measurement — already visible in the printed first-run alternative `sdf_trunc = 0.50` m, paired C−raw `0.0131±0.0034` against TSDF. The sign convention and that averaging remark are now stated in the fair-setup paragraph, the post-hoc alternatives paragraph, and exercise 3, en/zh. Curless & Levoy and the Open3D RGBD page were already body-read for #174; this polish does not add a new quotation from them about the sign.

## opencode

Free models were tried in order DeepSeek, GLM, MiMo, LongCat, MiniMax (`opencode/*-flash-free` / `longcat-2.5-free`, 40 s each) via `/workspace/b18pol-opencode/run.sh`. DeepSeek exit 0 with 0 Python files; the others exit 124 (timeout) with 0 Python files. The toys, pages and locks were implemented locally.

## Lock changes

New `b18pol` block only tightens / adds checks: printed damped-criterion numbers in the toy, `expected/` and en/zh; explicit-Euler / backward-Euler / D=0 wording; official Knowledge Insulation title; four VLA post-hoc changes; form-closure n&s sentence via already-read Carpin/Zhang; TSDF sign and wide-truncation sentences; this note; minutes unchanged at 35820. Tip-lock comments listed in §5 now name 35820. **No lock relaxed.** `.github/workflows` untouched.

## Local validation

See the PR description (check_diagrams, check_widgets, check_wokwi, check_quotes, tools/test_*.py, month check.sh, lint, typegen, tsc, build + postbuild, CI).
