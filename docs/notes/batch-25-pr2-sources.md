# Batch-25 PR2 sources

Base `55c7e5033b8600d33584e2ccece0fff29c8e3aab` (batch-25 PR1 #201 merged; 71 lessons, site **42660**). This PR: **M7 3690→3870**, **M8 4170→4350**, site **42660→43020** (43020=42660+180+180), still 71 lessons. Hosts: `mujoco-so101` 420→**600**, `sim-benchmarks` 330→**510**.

## Opened sources

- MuJoCo Computation, tag 4.0.1, Friction cones, https://mujoco.readthedocs.io/en/4.0.1/computation/index.html#friction-cones, HTTP 200 on 2026-11-19. Body read (saved under `/workspace/b25p2-sources/mujoco-4.0.1-computation.html`, sha256 `a806069860e7ce784eb266b47c8598f012a8714eddcd2967e07dea0bb2b97b83`). The contact friction cone can be elliptic or pyramidal; this is a global setting determined by the constraint solver. `condim` table: `condim=1` is 1 for elliptic and 1 for pyramidal (frictionless, the non-negative ray); regular frictional contact is `condim=3` → 3 for elliptic, 4 for pyramidal; `condim=4` → 4 / 6; `condim=6` → 6 / 10. Formal sets (n>1): elliptic `K = { f in R^n : f1 >= 0, f1^2 >= sum_{i=2}^n f_i^2 / mu_{i-1}^2 }`; pyramidal `K = { f in R^{2(n-1)} : f >= 0 }` element-wise. For n=1 both cones are the non-negative ray. Pyramid edges combine a normal component and one frictional component, scaled so the edges (and any convex combination) lie in the elliptic cone. Pyramidal approximation has `2(n-1)` edges. Inequalities 以文档为准.
- GitHub `google-deepmind/mujoco` tag 4.0.1, `doc/computation/index.rst`, blob SHA `6445e6637b52cf57fb14a0853c08251e49634152` (confirmed with `git hash-object` on the 4.0.1 raw file; the GitHub git-blob API returned the same body). Saved under `/workspace/b25p2-sources/mujoco-4.0.1-computation.rst` and `mujoco-computation-blob.rst`, sha256 `aaf49ad783def859a0007d41a40b3fe0e534096fe75714e83ad05cb56015ca46`. Same formal elliptic / pyramidal `K` and `condim` table as the versioned readthedocs page. 以文档为准.
- LIBERO-X abs, https://arxiv.org/abs/2602.06556, HTTP 200 on 2026-11-19. Title: “LIBERO-X: Robustness Litmus for Vision-Language-Action Models.” Seven authors in abs / citation order: Guodong Wang, Chenkai Zhang, Qingjie Liu, Jinjin Zhang, Jiancheng Cai, Junjie Liu, Xinmin Liu. v1 only; dateline “[Submitted on 6 Feb 2026]”; submission history `[v1] Fri, 6 Feb 2026 09:59:12 UTC`. Comments: “19 pages, 14 figures and 8 tables”; no venue. Saved under `/workspace/b25p2-sources/arxiv-2602.06556-abs.html`, sha256 `49e02d8a383bc28f445b3b3d12b41decf9bcb4b693fc8a0ae021c9cfc3b2c3da`.
- LIBERO-X HTML, https://arxiv.org/html/2602.06556, HTTP 200 on 2026-11-19. v1 body read (levels, dataset sizes). HTML author marks are garbled (footnote blocks dumped onto several names; affiliations mixed). Marks were **not** transcribed from the HTML. Saved under `/workspace/b25p2-sources/arxiv-2602.06556.html`, sha256 `fb2f1cc1834b7546b4a06616a30a4f5220fc01e75cadd9cb1bf570a33d451096`.
- LIBERO-X PDF, https://arxiv.org/pdf/2602.06556, HTTP 200 on 2026-11-19, 19 pages, arXiv:2602.06556v1 [cs.CV] 6 Feb 2026. PDF opened with pdftotext. Title page: “Guodong Wang∗1, Chenkai Zhang∗2, Qingjie Liu2, Jinjin Zhang2, Jiancheng Cai1, Junjie Liu†1, Xinmin Liu‡1”; “1 Meituan, 2 Beihang University”; “∗Equal Contribution †Corresponding author ‡Project Leader”; project page https://zackhxn.github.io/LIBERO-X/. Evaluation Framework levels: L1 Local Spatial Perturbation, L2 Extended Spatial Perturbation, L3 Scene Topology Reconstruction, L4 Visual Attribute Variation (unseen / confounding objects), L5 Semantic-Equivalent Reformulation. Training set: 2,520 demonstration trajectories, 600 tasks, 100 scenes. Finding 1 / Figure 5: “the transition to Level 2 … triggers a notable 9.8% drop in average success rate (Figure 5).” Caption: “Fig. 5: Success Rate Decline across Multi-level Evaluation.” The 9.8 % figure is a drop, not a suite mean, and not the L1-to-L5 decline. Saved under `/workspace/b25p2-sources/arxiv-2602.06556.pdf`, sha256 `7f91b21af1bfb13b9f3b1bc17a3048141b6f35310b77715ccdbd27082aca957e`. 以论文为准.

Resource cards: `mujoco-computation-401`, `libero-x-paper`. Real MuJoCo / `mujoco.step` / second grip scene / GPU `lerobot-eval` / real LIBERO-X: 本页未运行. MuJoCo figures 以文档为准; paper figures 以论文为准.

## Declared headers and first-run results

Official first run: 2026-11-19 22:49:29 Asia/Shanghai. Official expected sha256:

- `examples/month-7/expected/friction_cone_elliptic_pyramid_toy.txt` `98eecf26978c2907605d2bf1db67f293b23090385d360a42b99a80c7b43f1e93`
- `examples/month-8/expected/libero_x_robustness_ladder_toy.txt` `5d22ca3589545cc2b91bcd3661fad06cca9cc0becd6562ad7a819b03333d76c7`

Both files were rerun twice and `cmp` was byte-identical.

Common random numbers: the cone toy shares the force and slip-velocity samples across arms at each regime and seed (five seeds). The ladder toy shares scenes, slots, instructions, competence draws and Bernoulli uniforms across arms at each regime and seed (five seeds).

Friction-cone declared stand-in: `MU_Y=MU_Z=0.5000`, `N_SAMPLE=40`, `FN_SCALE=1.0000`, `SMALL_FRAC=0.2000`, seeds 0–4; official frictional `condim=3` (elliptic_dims=3, pyramidal_dims=4); frictionless `condim=1` (both 1). Hand calc (printed): pyramid edges `4.0000`; mid-diagonal `fn=1.0000 mu=0.5000 r=0.8500 fy=0.3005 fz=0.3005 elliptic_sum_sq=0.7225 pyramid_l1=1.2021 ell_in=1 pyr_in=0`. frictionless: B−A admit_rate `0.0000+-0.0000`, tie: identical on every seed — held (declared may tie or near-tie, held as an exact tie, kept). mid_tangential: `ell_in_pyr_out 8.0000+-0.0000`, `pyr_in_ell_out 0.0000+-0.0000`, example `fn=0.9009 fy=-0.2859 fz=0.2859`; B−A admit_rate `-0.2000+-0.0000`, clear, 5/5 — discrepancy printed and kept; the documented sets did not produce the vice-versa cell (pyramid stayed inside the elliptic cone); not retuned to force a slogan. high_tangential: C illegal_admit_rate `0.8250+-0.0000`, clear, 5/5 — held, kept. A and B admit `0.1750+-0.0000` and tie on admit_rate.

LIBERO-X declared stand-in: `P_BASE=0.8000`, `N_EP=40`, `N_SCENES=8`, `N_SLOTS=4`, penalties `0.0200, 0.1200, 0.1800, 0.1600, 0.1400`, `SMALL_FRAC=0.2000`, seeds 0–4. Hand calc (printed): cumulative penalties `0.0200, 0.1400, 0.3200, 0.4800, 0.6200`. Paper figures (printed as `paper_figure`, 以论文为准, not toy outputs): 2,520 demonstrations, 600 tasks, 100 scenes, and the 9.8 % L1-to-L2 drop in Figure 5 (a drop, not a suite mean, not L1-to-L5). l1_jitter: B−A L1 success `-0.0150+-0.0224`, near-tie — held, kept. cumulative_shift: B−A L3 `-0.3900+-0.1009`, L4 `-0.5000+-0.0530`, L5 `-0.6250+-0.0250`, clear, 5/5 — held, kept. leak_misreport: C−B leaked_L5_minus_true_L5 `0.6300+-0.0671`, clear, 5/5 — held, kept.

## Declared expectations that did not hold

None. Every pre-declared official regime held (frictionless A/B exact tie; mid-tangential discrepancy printed and kept, with no vice-versa cell from the documented sets; high-tangential C lose; L1 near-tie; cumulative L3–L5 consistent drop; C leak mis-report).

## Post-hoc choices

None of the official parameters were changed after the first official run. The lesson pages were written from the frozen official output. Named alternatives on the same seeds, not adopted:

- Cone: `MU_Y=MU_Z=1.0000` keeps the official labels (frictionless exact tie at admit `0.8750+-0.0000`; mid-tangential `ell_in_pyr_out 8.0000+-0.0000`, B−A admit_rate `-0.2000+-0.0000` clear, 5/5; high-tangential C illegal_admit_rate `0.8250+-0.0000` clear, 5/5).
- Ladder: unstructured harsh `HARSH_PENALTY=0.7000` on the cumulative_shift bank yields success `0.0750+-0.0177` (hand_calc floor `0.1000` if competence is zero), below even B’s L5 `0.1850+-0.0576` — too harsh; the official lose arm stays the L1-as-L5 leak.

`grip_sweep.py`, the existing `solref` / integrator sections, batch-20–24 hosts, #201 wording, `package.json`, and `.github/workflows` were not edited.

## Lock changes

No lock relaxed. Live site-total locks were tipped 42660 → 43020 and live README `/42 660/` → `/43 020/`. Live M7 / M8 curriculum sums were tipped 3690 → 3870 and 4170 → 4350. Live host-minute locks for `mujoco-so101` (420→600) and `sim-benchmarks` (330→510) were tipped. Historical strings inside already-written plan and sources files (including previous Current lines and the batch-25 PR1 sources note) were left unchanged. New PR2 locks were added for the two toys, expected output, CRN, label order, pinned 4.0.1 inequalities, LIBERO-X authorship / PDF marks / no venue, mid-regime disclosures, live totals 43020, and host / month minutes. The zh typography walk skips fenced toy source and expected output so a Python `**` exponent is not treated as MDX bold. After the official freeze, H4 lesson/curriculum/resource prose was adjusted so the paper figure is written `9.8 %` (house style: a space before the percent sign); official expected output was not retuned, and that typography change is disclosed on the page. Independent tests: `tools/test_b25p2_cone_libero_toys.py`.

## Mismatch with §9

None.

