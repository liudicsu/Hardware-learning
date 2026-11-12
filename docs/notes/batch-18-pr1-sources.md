# Batch-18 PR1 sources / 来源记录

Base `846242497217aa53313dfa1a006246386344bec6` (`8462424`, main after #172; site **34710**). This PR: M1 ohms-law 240→390 (+150), M3 gripper-fingers 390→570 (+180); site **34710→35040**; M1 2100→2250, M3 2820→3000; still 71 lessons.

## Opened sources

All fetched with curl on 2026-11-12 (Asia/Shanghai), HTTP **200**, then read as text (Wikipedia HTML; arXiv abs HTML and PDF via `pdftotext`).

| Resource id | URL | Version | What is used |
|---|---|---|---|
| `wiki-superposition` (new) | https://en.wikipedia.org/wiki/Superposition_theorem | redirects to Superposition principle, revision **1383626364**, last edited 3 November 2026 19:52 UTC (4 November 2026 03:52 Asia/Shanghai) | electrical-engineering paragraph: in a linear circuit an input (applied time-varying voltage signal) is related to the output (a current or voltage anywhere in the circuit) by a linear transformation, so a superposition (sum) of input signals will yield the superposition of the responses |
| `grasp-primer-carpin` (new) | https://arxiv.org/abs/1607.06620 and https://arxiv.org/pdf/1607.06620v1.pdf | v1, 22 July 2016; title **Multi-Fingered Robotic Grasping: A Primer**; authors **Stefano Carpin, Shuo Liu, Joe Falco, Karl Van Wyk** (4) | §2.5 Form and force closure: every form closure grasp is also force closure but not vice versa; gap function `ψ_i` and Eq. (2) `ψ(u+du, q) ≥ 0 ⇒ du = 0`; definition does not rely on friction (frictionless grasps); Somov: at least seven contact points are necessary for form closure of a 6-DoF object in 3-D, necessary not sufficient |
| `grasp-survey-zhang` (new) | https://arxiv.org/abs/2202.03631 and https://arxiv.org/pdf/2202.03631v1.pdf | v1, 8 February 2022; title **Robotic Grasping from Classical to Modern: A Survey**; authors **Hanbo Zhang, Jian Tang, Shiguang Sun, Xuguang Lan** (4) | Definition 1 (Grasp-closure): form-closure for frictionless contacts, force-closure for frictional contacts; “for a 2-D polygon, at least 4 frictionless wrenches are required for form-closure grasping”; “at least 7 contact points are needed for 3-D polygons” |

Statements from these sources are marked 以原文为准 / 以论文为准 on the site. The 4- and 7-point counts are paper figures, not measured by the planar toy. No breadboard, DMM or real gripper run (本页未运行).

## Toy design

- `examples/month-1/ohms-law/superposition_linear_circuit_toy.py`: shared two-source linear net `Vs1=5 V`, `R1=1000 Ω`, `Vs2=3 V`, `R2=2000 Ω`, `R3=4000 Ω` to ground. Arms A_joint (one nodal KCL solve) / B_super (sum of single-source responses, the other voltage source shorted) / residual on the same topology with a series ideal diode `Vf=0.7 V` plus `Rf=2000 Ω`. Common random numbers; seeds 0–4; 32 boards in the meter-noise regime (A uses `z0`, B uses `z1` then `z2`). No integration step (DC closed form on the linear net, bisection on the one-node nonlinear residual; tested). Hand values `26/7 V`, `20/7 V`, `6/7 V` are labelled as such and also printed by the toy.
- `examples/month-3/gripper-fingers/form_closure_frictionless_toy.py`: shared 2-D square of half-width 1, first-order gap / wrench test. Arms A_three / B_four (cyclically offset contacts `s = 0.75, 0.75, 0.75, 0.25`) / C_two_finger (mid-edge left and right) / aligned-normal fail cell (four contacts on two opposite sides). Common random numbers; seeds 0–4; `mu0_form` and `large_mu_force` share the same contacts and only change `μ`. No integration step (algebraic escape-twist test; tested). Not the Ferrari–Canny ε toy on perception-to-grasp.
- Labels as in batch-15/16/17 (tie → numerically zero below 1e-9 → near-tie `|m| ≤ sd` → consistent, small under 20 % of the smaller arm mean else clear, with sign count).

## Results (k/N = seeds with the reported sign)

Superposition (printed):
- linear_noiseless: A and B `3.7143±0.0000 V`; paired A−B nodeV and residual B−A vs 0 are both **tie** (`0.0000±0.0000: identical on every seed`). Joint residual `0.000e+00 V`. This is a tie, not a “clear” gap, and not a numerically-zero floating-point residue on the node voltage (the KCL current check leaves `-1.084e-19 A`).
- linear_meter (`σ = 0.001 V`): A `3.7143±0.0002 V`, B `3.7144±0.0003 V`; paired A−B `-0.0001±0.0003 V`, **near-tie** (1 of 5 seeds has the opposite sign).
- nonlinear_diode: joint `3.4250000000 V`, superposition sum `3.6000000000 V`, residual `0.1750000000 V`; residual vs 0 is `0.1750±0.0000`, **clear**, same sign on all 5 seeds. Raw node-voltage A−B is `-0.1750±0.0000`, **small but consistent** (same sign on all 5 seeds), because `|m|` is under 20 % of the node voltage; the residual-versus-0 label is the one that scores the theorem.

Form-closure (printed):
- mu0_form: B form `1.0000±0.0000`, A and C `0.0000±0.0000`; paired B−A and B−C form **clear** `1.0000±0.0000`, same sign on all 5 seeds.
- large_mu_force (same contacts, `μ = 1`): form-closure unchanged (B still leads A and C clearly); C−A and C−B on force-closure **tie** (`0.0000±0.0000: identical on every seed`). C still fails form-closure. Cell kept.
- aligned_normals: B_aligned form `0.0000±0.0000`; paired B_four−B_aligned form **clear** `1.0000±0.0000`, same sign on all 5 seeds.

## Post-hoc choices

- Superposition meter-noise sigma `0.001 V` was kept. Alternative `σ = 0.01 V` on the same seeds is still a **near-tie** (`-0.0010±0.0026 V`, 1 of 5 opposite sign). Alternative `Rf = 1000 Ω` prints residual `0.2800000000 V` (`V_joint = 2.8800000000 V`); superposition still fails.
- Form-closure: a four mid-edge layout was tried first. At the mid-points the first-order moments vanish and a pure rotation is an escape (`nominal form_mu0=0`, escape `(+0.0000, +0.0000, +1.0000)`). That is why the kept B layout is cyclically offset, **written before the first accepted run**. The jittered mid-edge alternative (disclosed, dedicated stream) has form `0.8000±0.4472`; paired against offset B the gap is `0.2000±0.4472`, a **near-tie** (no seed has the opposite sign, 4 of 5 equal). The offset was kept because of the nominal degeneracy, not because the jittered mid-edge score was shopped.
- Alternative jitter `0.05` on `mu0_form` leaves B−A form **clear** `1.0000±0.0000`, 5/5. Alternative `μ = 0.2` on the same large-`μ` contacts: C stays force-closure `1.0000` and still **ties** B, but A drops to `0.0000`, so C−A force becomes **clear** `1.0000±0.0000`, 5/5. Form-closure is unchanged. Printed and kept.

## Mismatch with §9

- §9 / H1 asked for a linear **tie / zero** between the full solve and the sum of single-source responses. The noiseless node-voltage residual is an exact **tie** (`0.000e+00 V`), not a numerically-zero floating-point residue. The KCL current check does leave a `-1.084e-19 A` residue, which is reported as such and is not used as a regime label. The nonlinear lose is **clear** on residual-versus-0 (`0.1750±0.0000`, 5/5), as required.
- §9 / H2 asked for a μ=0 **consistent** form-closure win, a large-μ force-closure cell that may **tie**, and a necessary-not-sufficient fail cell, all kept. All three printed as declared. Paper counts 4 and 7 are printed and marked 以论文为准. The mid-edge first-order degeneracy was not named in §9; it is disclosed as a post-hoc layout choice (see above).
- No other mismatch: CRN, ≥5 seeds, no integration step stated and tested, no unprinted side-run numbers, en/zh synced, locks only tip totals / Current headers / host minutes (ohms-law 240→390, gripper-fingers 390→570, site 34710→35040).

## opencode

Tried free models in order DeepSeek (`opencode/deepseek-v4.1-flash-free`), GLM (`opencode/glm-5.3-flash-free`), MiMo (`opencode/mimo-v2.6-flash-free`), LongCat (`opencode/longcat-2.5-free`), MiniMax (`opencode/minimax-m3.1-flash-free`, the free MiniMax id available in this environment). None produced toy files (permission auto-reject on `/workspace/proposals`, timeout, or empty). Implementation is local.

## Lock changes

Tipped site-total and host-minute locks only; no lock relaxed.

- README `/34 710/` and `约 34 710 分钟` → `/35 040/` and `约 35 040 分钟` (including earlier “unchanged” tips).
- Curriculum sum checks `34710` → `35040`.
- `b12p1` ohms-law host minutes in the Thévenin cases array `240` → `390`.
- `rtos1` gripper-fingers minutes `390` → `570`.
- month-1 plan Current header lock (was Batch-16, **M1 2100**) → Batch-18, **M1 2250**; historical `## Batch-16 PR1` markers kept.
- month-3 plan Current header lock (was Batch-17 PR1, **M3 2820**) → Batch-18, **M3 3000**; historical `## Batch-17 PR1` markers kept.

- `current curriculum` month totals: M1 2100→2250, M3 2820→3000 (other months unchanged).
- `tools/test_m3_optional_cad.py` FULL list extended with `form_closure_frictionless_toy.txt`.

No lock relaxed.
