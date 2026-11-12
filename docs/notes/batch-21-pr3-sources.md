# Batch-21 PR3 sources — FLARE future-latent alignment, OpenVLA-OFT parallel L1

Base: `122d224c91dfa02e5e7c867354dc246b02d7737e` (batch-21 PR2 #186 merged; site **38700**, M6 **3660**, M8 **3810**).
This PR: site **38700→39060** (39060=38700+180+180), M6 **3660→3840**, M8 **3810→3990**, catalogue still **71**. Hosts: `act-diffusion` 870→1050, `vla-finetune` 840→1020. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources opened and read (bodies)

All fetched this run (2026-11-13 UTC+8), HTTP 200; PDFs read with pdftotext.

| id | URL | version | What was used |
|---|---|---|---|
| flare-paper | https://arxiv.org/abs/2505.15659 (also https://arxiv.org/html/2505.15659 and https://arxiv.org/pdf/2505.15659) | v1 | Title *FLARE: Robot Learning with Implicit World Modeling*. Authors (abs `citation_author`, 21, arXiv order): **Ruijie Zheng, Jing Wang, Scott Reed, Johan Bjorck, Yu Fang, Fengyuan Hu, Joel Jang, Kaushil Kundalia, Zongyu Lin, Loic Magne, Avnish Narayan, You Liang Tan, Guanzhi Wang, Qi Wang, Jiannan Xiang, Yinzhen Xu, Seonghyeon Ye, Jan Kautz, Furong Huang, Yuke Zhu, Linxi Fan**. Read: abstract ("up to 26%"), 3.1 (M learnable future tokens, layer-L slice, MLP, eq 2 cosine alignment, eq 3 L = L_fm + λ L_align, λ = 0.2), 4.3 (human egocentric videos without action labels use the alignment loss alone), 4.4 (Table 2: 43.9 / 49.6 / 50.9 / 55.0 %; layer 6 of 8; layer 4 "notable drop"), 6 (limitations). 以论文为准. |
| openvla-oft-pdf | https://arxiv.org/pdf/2502.19645 (also https://arxiv.org/abs/2502.19645 and https://arxiv.org/html/2502.19645) | v2 | Title *Fine-Tuning Vision-Language-Action Models: Optimizing Speed and Success*. Authors (abs `citation_author`, 3, arXiv order): **Moo Jin Kim, Chelsea Finn, Percy Liang**. Read: abstract (76.5 % → 97.1 %, 26×), introduction (L1 "comparable" to diffusion; OFT+ 43× with 25-step chunks), III (K·D sequential passes for chunked autoregression), IV-A/B (parallel decoding with empty action embeddings and bidirectional attention, "may theoretically be less expressive", no degradation in their experiments; 256-bin discretisation; L1 vs diffusion), IV-C (FiLM for language grounding), VI (ALOHA language following; without FiLM success drops to chance). 以论文为准. The existing `openvla-oft-paper` card (abs link, M10) is unchanged. |
| ROS wiki URDF `<link>` (archived) | https://web.archive.org/web/20241225111435/http://wiki.ros.org/urdf/XML/link (Wayback copy, HTTP 200; the live page is the bot wall noted in the PR2 note; this URL is kept out of the lesson, resources and curriculum so that the PR2 lock "the ROS wiki bot wall is not cited" stays as strict as it was) | snapshot 2024-12-25 | Read for the one-sentence sign note on `urdf-tf`: "URDF assumes a negative product of inertia convention", i.e. `ixy` = −∫ x y dm, the inertia-tensor off-diagonal entry. This is the same sign as the toy's J_xy = −m R_x R_y (the tensor form's off-diagonal element), so the page says `ixy` is J_xy directly. |

Not cited:
- No GR00T N1, SigLIP2, RoboCasa or GR-1 material and no OpenVLA checkpoint, LIBERO or ALOHA code were opened; every toy dimension, noise level, tolerance and demonstration count is a **declared toy parameter**, printed.

## Toys

- `examples/month-6/act-diffusion/flare_future_latent_alignment_toy.py` → `examples/month-6/expected/flare_future_latent_alignment_toy.txt`
- `examples/month-8/vla-finetune/openvla_oft_parallel_l1_toy.py` → `examples/month-8/expected/openvla_oft_parallel_l1_toy.txt`

Common random numbers, five seeds `(0, 1, 2, 3, 4)`, stdlib CPU only, half-up rounding on the shortest decimal repr, byte-identical output on rerun. Neither toy steps time: FLARE is full-batch gradient descent on a linear model (gradient checked independently by finite differences in `tools/test_b21p3_flare_openvla_oft_toys.py`); OFT is closed-form lookups. Every m±sd in the new lesson prose, the new Summary sentences, the curriculum objectives, the month-6 / month-8 plans and this note is printed into `expected/`; hand calculations are labelled (printed, or marked 手算: the 1/3 variance of U[−1, 1] on the FLARE page); paper figures carry 以论文为准.

## Regime results

### H5 FLARE (`flare_future_latent_alignment_toy.txt`)

- Declared toy parameters: D 8, K 2, λ 0.2 (the paper's), λ_big 2.0, step 0.05, 400 passes, success tolerance 0.25, 200 test samples; delayed 6 labelled + 60 action-free samples, reactive 60 labelled.
- Hand calc (printed): −λ = -0.2000 at cos = 1 (−2.0000 at λ_big); goal/distractor ratio 0.1732 now, 0.5774 in the future.
- delayed: declared B win did **not** hold — B−A action_mse -0.1002±0.1756, **near-tie** (2 of 5 opposite); B−A success 0.0020±0.0179 near-tie. Declared C loss did **not** hold here — C−B action_mse 0.1016±0.2475, near-tie. A's action MSE 1.4271±0.9760 is worse than always answering 0 (1/3, 手算).
- reactive: B−A action_mse 1.343e-4±2.827e-4, **near-tie** (held); B−A success tie; C−B action_mse 0.0166±0.0154, **clear**, 5/5 (declared large-λ loss held, kept).
- Alternatives (same seeds, written before the first run, not adopted): delayed λ = 0.05 (B−A -0.1001±0.1581), λ = 1.0 (-0.3742±0.6972), 12 labelled (-0.0172±0.0202), all near-ties; reactive λ = 1.0 (0.0042±0.0046, near-tie).

### H6 OpenVLA-OFT (`openvla_oft_parallel_l1_toy.txt`)

- Declared toy parameters: 8 cells, K 8, D 2, 10 demonstrations per cell, noise 0.002, success tolerance 0.003, mode tolerance 0.1, 10 diffusion steps, 256 bins.
- Hand calc (printed): bin width 0.0078, worst-case rounding 0.0039; 16 vs 1 passes; P(5–5 split) 0.2461; empty mismatched pair 0.3487.
- unimodal: B−A abs_err -0.0015±1.281e-4, **clear**, 5/5; B−A success 1.0000±0.0000; B−A passes -15.0000±0.0000 (held). C−B success **tie** (declared "may near-tie"); C−B passes 9.0000±0.0000 (held); C−B abs_err -8.507e-5±2.293e-5, small, 5/5 (not pre-declared; C slightly better).
- bimodal: declared "B can average the modes and lose to C (and A)" did **not** hold as a consistent gap — C−B success 0.2000±0.2592, **near-tie** (no seed opposite, 2 of 5 equal); B−A success 0.5000±0.3062, **clear in B's favour** (A takes each token's mode separately and mixes left and right inside a chunk; a real autoregressive decoder conditions on earlier tokens). Kept.
- language: D−B follow_err -0.4000±0.0713, **clear**, 5/5 (held, kept); B−A and C−B follow_err tie.
- k1: B−A passes -1.0000±0.0000 (A needs D = 2; held); B−A abs_err -0.0016±2.270e-4, clear, 5/5.
- Alternatives (same seeds, written before the first run, not adopted): tolerance 0.002 (B−A success 0.9000±0.1046, clear), tolerance 0.005 (0.1500±0.2054, near-tie), noise 0.01 (B−A abs_err -0.0022±4.498e-4, clear), bimodal 11 demonstrations (C−B success tie).

## Post-hoc choices

None for parameters or regimes in either toy: dimensions, λ values, step size, passes, tolerances, noise levels, demonstration counts, the diffusion schedule and every printed alternative were written before the first run.

## Code changes after the first run

- FLARE: **none**. The first-run output is byte-identical to the committed `expected/` file.
- OpenVLA-OFT: **one formatting edit**, before the output was committed. Integer counts in five printed lines (hand-calc pass counts, the 5–5 split, the 90 % agreement, the per-seed even-split and empty-pair counts) printed as `16.0000`, `5.0000`, `90.0000` etc. in the first run and as plain integers now. No parameter, regime, arm or computed value changed; every m±sd and label is identical to the first run. Stated on both language pages.

## Mismatch with §9

- H5: §9 expects a long-horizon **consistent** alignment win and a **consistent** early-layer / large-λ action-error rise. In this linear stand-in the delayed-regime win did not hold (near-tie) and the large-λ rise held only in `reactive`. The toy has no layers, so the paper's early-layer conflict is represented only by λ = 2.0. Reported plainly on both pages; not retuned. The toy's printed closing line states the hypothesis; the pages say this run shows only its second half.
- H6: §9's unimodal L1 precision / pass-count win, "L1 vs diffusion may near-tie on success" (a tie here) and the language-follow loss match. The bimodal "L1 averages and loses" is a near-tie against C and the reverse against A; kept and explained.

No other mismatch: CRN, ≥5 seeds, no integration step, no unprinted side-run numbers, en/zh synced, difference directions in prose / Summary / curriculum / plans / this note match the printed `paired` lines (locked). FLARE ≠ CogACT / HybridVLA / InternVLA-A1 / MemoryVLA / DreamGen; OpenVLA-OFT ≠ ChatVLA / SimpleVLA-RL / VLA-Adapter / NORA.

GR00T N1 / RoboCasa / GR-1 / GPU and the 7B OpenVLA / LoRA / LIBERO / ALOHA: 本页未运行.

## Other changes in this PR

- `docs/notes/batch-21-pr2-sources.md`: the tools/process paragraph (former lines 64–66) removed at the owner's request; the rest of that note is unchanged.
- `src/content/m4/urdf-tf/{en,zh}.mdx`: one sentence that URDF's `ixy` is the tensor entry J_xy, sign included (source row above).

## Lock changes

New batch-21 PR3 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, difference directions, sources, plans, README, declared regimes that did not hold stated on both pages, post-first-run code change stated) plus `tools/test_b21p3_flare_openvla_oft_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (38700→39060, M6 3660→3840, M8 3810→3990, act-diffusion 870→1050, vla-finetune 840→1020). In the b21p2 sources-note lock, the presence token for the removed paragraph's heading is replaced by an absence check for that paragraph (owner request). The b17p3 ChatVLA lock checked every number in the vla-finetune Summary against the ChatVLA toy's expected/; the one new Summary bullet that names `openvla_oft_parallel_l1_toy.py` is now checked against that toy's expected/ instead (exactly one such bullet allowed), and every other Summary line is still checked against ChatVLA's. No lock relaxed.
