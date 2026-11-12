# Batch-20 polish sources — lead vs pitch, collar friction, rolling-shutter skew sign, GraspVLA Table 1 range, InternVLA-A1 λ

Base: `f3fc6e6b926089573712c386239aff369f036e6b` (batch-20 PR3 #183 merged; site **37980**, catalogue **71**).
This PR: site stays **37980**, catalogue stays **71**; **no minute count changed** (curriculum, month plans and README untouched for minutes). **No toy number and no `expected/` file changed.**
Head of this branch is recorded at open time in the PR; locks check this note, not a later SHA.

## Sources opened and read (bodies)

All fetched on 2026-11-12 (UTC+8); PDFs read with `pdftotext -layout`.

| id | URL | rev / version | HTTP | What was used |
|---|---|---|---|---|
| wiki-leadscrew (re-read) | https://en.wikipedia.org/wiki/Leadscrew | 1372857424 (still current) | 200 | Mechanics: the unwrapped triangle's height is the **lead** l. Collar paragraph: if the load rides on a collar, the interface friction must be added, T_c = F·μ_c·d_c / 2 (μ_c collar friction coefficient, d_c mean collar diameter); with thrust bearings the loss is negligible. The article does **not** discuss pitch or starts and does **not** say that collar friction can hold a high-lead screw. 以原文为准. |
| wiki-screw-thread | https://en.wikipedia.org/wiki/Screw_thread | 1378437137 | 200 | Section "Lead, pitch, and starts": lead = axial distance per complete rotation (360°); pitch = distance from one crest to the next; most threads are single-start so lead = pitch; "In general, lead is equal to pitch times the number of starts." 以原文为准. |
| graspvla-pdf (re-read) | https://arxiv.org/pdf/2505.03233v3 | v3 (same SHA-256 as the PR3 copy, `3fb7cb24…`) | 200 | Table 1 (p. 6), row "Ours", success %: synthetic categories basic 93.3, light 96.6, b.g. 93.3, dis. 93.3, height 90.0 (SPL 87.2); web categories basic 93.3, light 90.0, b.g. 93.3, dis. 86.6, height 86.6 (SPL 84.7). §5.1: each test set 15 objects × 2 trials. Range used on the page: **86.6 % to 96.6 %** over the ten sets; synthetic **90.0–96.6 %**, web **86.6–93.3 %**. 以论文为准. |
| internvla-a1-pdf (re-read) | https://arxiv.org/pdf/2601.02456.pdf | v2 (PR3 copy) | 200 (PR3) | §3.3 "Loss Function": Eq. (4) L_total = λ·L_gen + L_act, λ a hyperparameter balancing the two objectives. §3.4 "Training Protocol and Hyperparameters": "In addition, the hyperparameter λ, which balances the two loss components, is" [page 8 ends, Table 2 on page 9] "set to 0.01." **λ = 0.01 confirmed** in the body; it is not Table 2's weight decay (also 0.01). The PR3 note attributed λ to §3.3; it now says Eq. (4) in §3.3 and the value in §3.4. |

No leadscrew vendor catalogue, no collar-friction measurement and no camera datasheet was opened: no collar coefficient, starts count of a real product or sensor readout time is quoted. Real screws, cameras and GraspVLA weights: 本页未运行.

## Item by item

1. **Lead vs pitch** (m3/transmissions en/zh, after the worked example): l in λ = atan(l / (π·d_m)) is the lead; single-start lead = pitch, multi-start lead = starts × pitch (Screw thread article, 以原文为准); a larger lead means a larger λ, so multi-start screws often no longer self-lock; do not plug a package's "pitch" straight in. Hand calculation (手算): 5 × 2.0 = 10.0 mm, the A_steep lead, for which the toy already prints λ = 17.6568° > φ = 8.5308°; the 2.0 mm pitch would give B_fine's λ = 3.6426°. New `wiki-screw-thread` resource card.
2. **Collar / thrust-face friction** (m3/transmissions en/zh, Fair setup): the toy assumes a thrust bearing (no collar friction). The article gives T_c = F·μ_c·d_c / 2 and says it is negligible with a thrust bearing; that collar friction can sometimes hold a high-lead screw is stated qualitatively as **our reading of the formula, not an article sentence**; no number. `wiki-leadscrew` summary (en/zh) now mentions the collar term.
3. **Rolling-shutter skew sign** (m5/camera-calibration en/zh, after the worked example). Verified against the toy code: `row_time` gives row 0 at t0 and later times for larger r; the column is `x0 + v * row_time(arm, r, dt_row) + noise[r]`; `fit_line` returns slope b ≈ v·Δt_row (columns per row). So with row 0 at the top (rows read top to bottom) and columns growing to the right (v > 0 rightward), the **signed skew b·(H − 1) has the same sign as v**. The toy prints only `abs(b) * (H - 1)` and every printed speed is positive, so `expected/` has no sign to compare; `tools/test_b20pol_shutter_skew_sign.py` checks the sign for v = ±300.0 and ±1500.0 px/s on B_rolling and C_slow, five seeds, and that the toy output is still byte-identical to `expected/`.
4. **GraspVLA "around 90 %"** (m7/perception-to-grasp en/zh): replaced by the Table 1 range above, 以论文为准. **λ = 0.01** in `batch-20-pr3-sources.md`: confirmed (§3.4), attribution corrected.

## Toys

No new toy, no toy edit, no regime or parameter change; every `expected/` file is unchanged (`examples/month-3`, `month-5`, `month-7` `check.sh` all "same"). The only new numbers on the pages are document values (以原文为准 / 以论文为准), the labelled hand calculation 5 × 2.0 = 10.0 mm, and values already printed by the toys. No difference direction changed.

## opencode

Tried free models in order with a 90 s timeout on a narrow sub-task (a stdlib unittest for the skew sign): DeepSeek (`opencode/deepseek-v4.1-flash-free`) exit 0, no file; GLM (`opencode/glm-5.3-flash-free`) exit 0, wrote a file that patched a non-existent `REGIMES["B_rolling"]` key and read the intercept as the slope — **not used**; MiMo (`opencode/mimo-v2.6-flash-free`) exit 0, file read auto-rejected; LongCat (`opencode/longcat-2.5-free`) exit 0, no file; MiniMax (`opencode/minimax-m3.1-flash-free`) exit 0, file read auto-rejected. The test, prose, resources and locks were written locally.

## Lock changes

New batch-20 polish block `b20pol` only (tightening): lead/pitch and collar paragraphs (en/zh) with their sources, skew sign convention on the page plus the sign test, Table 1 range on the page and "around 90 %" / "90 % 左右" gone from that section, λ attribution in the PR3 note, `wiki-screw-thread` resource, this note, totals 71 / 37980 unchanged. No lock relaxed; no existing lock edited.
