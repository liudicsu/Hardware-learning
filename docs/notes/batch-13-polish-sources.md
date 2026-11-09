# Batch-13 polish: Ferrari–Canny, Diffusion Forcing C ρ(G), MAP-VLA authors, J-STD-020

Base: `00cc3e1` (batch-13 PR1–PR3 merged: #153, #154, #155; site **30270**, 71 lessons). Polish after the batch-13 查漏补缺 pass. Minutes unchanged: **71 / 30270** (M1 1650, M5 2490, M7 2430, M10 2910). No new sections that add minutes, no new slugs, no workflow edits, no lock relaxed.

## 1. perception-to-grasp — Ferrari–Canny (1992) at ε

- Named **Ferrari–Canny (1992)** where ε is defined in en/zh: ε = radius of the largest origin-centred ball inside the GWS (= distance to the nearest facet).
- **Source actually opened (body read):** `ferrari-canny-pdf` / Carlo Ferrari & John Canny, "Planning optimal grasps," ICRA 1992 PDF: https://users.cs.duke.edu/~tomasi/public/ReadingGroup/Ferrari%20and%20Canny%20ICRA%201992.pdf, HTTP 200, body read via pdftotext. Force closure is binary; quality Q is the radius of the largest origin-centred sphere in the convex hull of the primitive contact wrenches; L∞ (per-finger) and L1 (total-force) variants; the lesson's ε follows the L1 form. 以原文为准.
- Already-read Minimal Work (arXiv 1909.11226) cites Ferrari and Canny (1992) in its references; Dex-Net 2.0 uses "epsilon quality" without naming Ferrari–Canny in the body passages we rely on.
- Wired as `ferrari-canny-pdf` in `resources.ts` and the perception-to-grasp curriculum resource list; `<Resource id="ferrari-canny-pdf" />` in the section. Also noted in `docs/notes/batch-13-pr2-sources.md`.

## 2. flow-matching-policies — arm C shared noise / re-noise

- en/zh now state that arm C **shares a single noise level** (`k_prev = k_cur`) and **re-noises the context** to that level every step.
- Printed one-token gains for C: `0.6755 0.6842 0.6824 0.6889 0.6890` → **0.6755–0.6890** (≈ 0.68).
- Explicitly: C does **not** reproduce the diverging causal full-sequence baseline in Diffusion Forcing §4.1 (arXiv 2407.01392). Also noted in `docs/notes/batch-13-pr3-sources.md`.

## 3. intervention-logging — MAP-VLA authors

- en/zh now say **MAP-VLA (Runhao Li et al., arXiv 2511.09516, …)**.
- First author verified against https://arxiv.org/abs/2511.09516 (Runhao Li); matches `resources.ts` author field. No discrepancy.

## 4. Optional J-STD-020 for the M1 reflow curve — **not cited**

Tried (2026-11-10, Asia/Shanghai UTC+8):
- `https://www.jedec.org/standards-documents/docs/j-std-020e` → HTTP 200 landing page only; free download requires registration/login.
- `https://www.jedec.org/sites/default/files/docs/jstd020d-01.pdf` → HTTP **403**.
- `https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/14/J_2D00_STD_2D00_020E.pdf` → HTTP **500**.

No body text was opened, so the soldering reflow section keeps Wikipedia / SparkFun only; cold-joint / pad-lift thresholds stay labelled toy stand-ins, not IPC/JEDEC criteria. (Matches the earlier batch-13 PR1 note that no IPC standard text was opened.)

## Lock changes

- **No lock relaxed.** Added a batch-13 polish block in `tools/check_diagrams.mjs` that requires the Ferrari–Canny name at ε, the C shared-noise / §4.1 non-reproduction sentences, the Runhao Li et al. author line, the new `ferrari-canny-pdf` resource, and this sources note. Existing PR2/PR3 locks and totals (30270) stay as they are.

## Models / reproducibility

Implemented locally in `/workspace/hl-b13pol` (node_modules via `cp -al` from hl-b13p3). Ferrari–Canny PDF/txt cached under `/workspace/b13pol-sources/` (not committed).

## Local validation

`check_diagrams`, `check_widgets`, `check_wokwi`, `check_quotes`, eslint 0 warnings, typegen, `tsc --noEmit`, full `npm run build` including postbuild. No workflow edits. Minutes **71 / 30270**.
