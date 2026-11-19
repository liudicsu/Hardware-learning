# Batch-24 PR3 sources

Bodies actually read, version ids, authorship notes, first-run proof, regime results, lock tips. Internal note; process labels are allowed here and must not leak into lesson prose or toys/expected/.

## Papers read

### NaVILA — arXiv 2412.04453 v2

- Abs: https://arxiv.org/abs/2412.04453 (v2 selected). HTML: https://arxiv.org/html/2412.04453v2. PDF: https://arxiv.org/pdf/2412.04453v2. Local copies under `/workspace/b24p3-opencode/papers/navila-abs.html`, `navila.html`, `navila.pdf`, plus `navila-pdf.txt` extracted from the PDF, and the arXiv API XML.
- Version: v2 updated 2025-02-17 18:27:27 UTC = 2025-02-18 02:27 Asia/Shanghai. v1 was submitted 5 December 2024 (API / abs). Cite v2, not v1.
- The v2 abs, HTML and PDF bodies read here **do not state a conference venue**. Lesson prose therefore cites arXiv v2 only and does not add a venue from an unread secondary page.
- Authorship follows the abs, 10 names in this order: An-Chieh Cheng, Yandong Ji, Zhaojing Yang, Zaitian Gongye, Xueyan Zou, Jan Kautz, Erdem Bıyık, Hongxu Yin, Sifei Liu, Xiaolong Wang.
- PDF/HTML marks not in the abs author line: Cheng, Ji and Yang are * equal contribution, ordered alphabetically; Yin, Liu and Wang are †. Affiliations on the PDF: UC San Diego, USC, NVIDIA.
- Spell Erdem Bıyık and Hongxu Yin exactly; do not expand a nickname from a secondary page. Disclose the * / † marks.
- Claims taken 以论文为准 and not used as toy outputs: mid-level language actions with spatial information plus a visual locomotion RL policy; decoupling / transfer by swapping the low-level policy; a higher-rate locomotion loop for obstacle avoidance; “over 17 %” VLN success-rate improvement; 88 % of 25 real-world instructions on Unitree Go2 / H1 / Booster T1.

### FD-VLA — arXiv 2602.02142 v2

- Abs: https://arxiv.org/abs/2602.02142. HTML: https://arxiv.org/html/2602.02142v2. PDF: https://arxiv.org/pdf/2602.02142v2. Local copies under `/workspace/b24p3-opencode/papers/fdvla-abs.html`, `fdvla.html`, `fdvla.pdf`, plus `fdvla-pdf.txt` and the arXiv API XML.
- Version: v2 dated 2026-03-20 09:53:38 UTC = 2026-03-20 17:53 Asia/Shanghai. v1 was 2026-02-02. Cite v2.
- Authorship follows the abs, 7 names in this order: Ruiteng Zhao, Wenshuo Wang, Yicheng Ma, Xiaocong Li, Francis E. H. Tay, Marcelo H. Ang Jr., Haiyue Zhu.
- PDF/HTML: same order; Haiyue Zhu is † corresponding.
- Typography: abs uses “Francis E. H. Tay” (spaces in initials); PDF title page prints “Francis E.H. Tay”. Disclose that difference; follow the abs spelling in the author list. “Marcelo H. Ang Jr.” is the same person as abs “Ang Jr., Marcelo H.” Do not copy the PDF-metadata typo `au2` (confirmed in pdfinfo Author field).
- Claims taken 以论文为准 and not used as toy outputs or retuning targets: Force Distillation Module (learnable query conditioned on vision and state predicts a force token aligned at training with latent real-force representations; no physical force sensor at inference); contrast with late-fusion / MoE force injection; the claim that the distilled token can outperform direct sensor force in their physical experiments.

## First official run (proof of no post-first-run toy edits)

Toys were written and frozen before the official first run. Official stdout was saved under `/workspace/b24p3-opencode/mine/*.txt` **before** copying into `examples/month-11/expected/`. A second rerun was byte-identical to the first-run stdout and to expected/. Toy sources were not edited after that official run. Lesson prose therefore says **Choices made after seeing results. None** / **看过结果后做的选择**。 没有。

| file | sha256 | official first-run / freeze time (Asia/Shanghai) |
| --- | --- | --- |
| mine/navila_midlevel_locomotion_toy.py | ee28330bcef18bc5a2a1a715cf003a78989ff3ebcb91c1154a86ea6b795961ac | 2026-11-19 16:58:38 +0800 (source frozen) |
| mine/navila_midlevel_locomotion_toy.txt | 0cb5273f4b7900f17c2fabbd4041882c917eefd68272a3213aa81c47a2712db6 | 2026-11-19 16:58:51 +0800 |
| mine/fdvla_force_distill_toy.py | 1876393c9978ce3936000de3cf94cd448943c9d7d218680466d17afa020ab510 | 2026-11-19 16:56:11 +0800 (source frozen before the official run) |
| mine/fdvla_force_distill_toy.txt | 45a21fff998295c43dd1349f5c76111ab07f38cabefbe2134f341622a2507d39 | 2026-11-19 16:58:51 +0800 |

Worktree copies of the toys and expected/ files are byte-identical to these mine/ files (same sha256).

**Lock changes.** Live site total tipped 41940→42300; README 41 940→42 300; live M11 3990→4350, including the Current-header includes-locks and the month-11 lesson-sum locks. New host-minute checks 480→660 and 390→570. Historical arithmetic kept, including 41220→41580, 41580=41220+180+180, 41580→41940, 41940=41580+180+180, motors-drivers 720→900, dataset-engineering 330→510, and historical [11,3990] mentions that are plan-text rather than live sums. **No lock relaxed.** FOC `grabMin("foc-actuator-lab") === 480` was left alone. `.github/workflows` untouched. No package.json / lockfile edits. Catalogue stays 71.

**Post-hoc choices.** After the official first run, the only page typography change was wrapping each new SimOutput in a text fence (layout only). No constant, arm, metric or regime was changed. **Mismatch with §9.** The FD-VLA easy_observed pre-declared near-tie did not hold (paired B−A success 0.0021±0.0017, small but consistent, 1 of 5 seeds has the opposite sign) and was kept, not retuned. NaVILA pre-declarations all held. **Code changes after the first run.** None for toy sources or expected stdout (byte-identical to the official first-run files). **declared toy parameter** values stay at their pre-declared numbers.

## Official regime results (not retuned)

NaVILA, five seeds 0 through 4, n_scenes = 25.0000:

- open_corridor: A and B success 1.0000±0.0000, collisions 0.0000±0.0000, exact tie on both. C success 0.0000±0.0000, collisions 1.0000±0.0000. Paired C−B success −1.0000±0.0000 clear 5/5; C−B collisions 1.0000±0.0000 clear 5/5. Pre-declared A/B near-tie held (exact tie). C loses, held.
- clutter_transparent: A success 0.0000±0.0000, collisions 2.0000±0.0000; B success 1.0000±0.0000, collisions 0.0000±0.0000; C success 0.0000±0.0000, collisions 1.9840±0.0219. Paired B−A success 1.0000±0.0000 clear 5/5; B−A collisions −2.0000±0.0000 clear 5/5; C−B success −1.0000±0.0000 clear 5/5; C−B collisions 1.9840±0.0219 clear 5/5. Pre-declared B-better and C-loses held.
- Alternatives (not adopted): SIDE=0.3000, C_YAW_BIAS=0.1000.
- hand_calc tokens include wall_clear 1.0500, hit_clear 0.4000, tan 0.2027, y at LEN 1.6217, wall x 5.1798, small_frac 0.2000, mid-level vocab 0.7500 / 0.5000 / 30.0000 (toy command sizes, not paper results).

FD-VLA, five seeds 0 through 4, n_scenes = 25.0000:

- easy_observed: A 0.9841±0.0015, B 0.9863±0.0024, C 0.5048±0.0073; paired B−A 0.0021±0.0017 small but consistent, 1 of 5 opposite (failed near-tie, kept); C−B −0.4815±0.0067 clear 5/5 (C loses held).
- occluded_subtle: A 0.8293±0.0119, B 0.9363±0.0035, C 0.4986±0.0155; B−A 0.1070±0.0087 small but consistent 5/5 (B above A held); C−B −0.4377±0.0175 clear 5/5.
- oracle_force 1.0000±0.0000 both regimes; B does not beat oracle (easy B−oracle −0.0137±0.0024 small 5/5; occluded −0.0637±0.0035 small 5/5) — printed, not retuned.
- Alternatives (not adopted): OCC_V_SIG=0.2000, W_V/W_S=0.5000/0.5000.

Common random numbers were used on both toys.

## Arithmetic

Verified on origin/main `f49c721f42f2f9d6a7fc93cb21fb3ecf512aecca` before writing: catalogue 71, site 41940, M11 3990 (not 4170), humanoid-wbc-overview 480, contact-rich-policies 390, M2 4110, M8 4170. After this PR: humanoid 660, contact-rich 570, M11 4350, site 42300 (42300=41940+180+180). Other months unchanged: M1 2910, M2 4110, M3 3690, M4 3570, M5 3750, M6 4020, M7 3690, M8 4170, M9 4290, M10 3750.

Work plan on each host: 30+25+50+40+35=180.

IsaacLab / real Unitree or Booster / GPU / F/T hardware: 本页未运行.
