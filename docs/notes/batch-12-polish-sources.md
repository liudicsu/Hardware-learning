# Batch-12 polish: labels, maximum power transfer and lint audit

Base: `b6175dc` (batch-12 PR1–PR3 merged: #149, #150, #151; site **29160**, 71 lessons). Polish after the batch-12 查漏补缺 pass. Minutes unchanged: **71 / 29160** (M1 1500, M4 2310, M5 2310, M7 2250, M9 3900, M11 3630). No new sections, no new slugs, no workflow edits.

## One labelling rule

All four touched toys now use the rule already used by #151: **tie** = identical on every seed; **near-tie / within seed noise** = `|paired mean| ≤ paired sd`; **consistent** = only `|paired mean| > paired sd`. In the #150 toys the 20 % rule (`|mean|` < 20 % of the smaller arm mean) only chooses "small" vs "clear"; it never decides consistency. Consistent / clear lines carry a sign count (seeds whose paired difference has the opposite sign to the mean), like #151's `sign_note`.

## Relabels found by re-checking every gazebo-sim / ohms-law label against `|m| > sd`

- **gazebo-sim gentle_rest (requested):** was "near-tie / small gap". Paired A−B `1.446±0.261 µm`, A−C `1.534±0.276 µm`, B−C `0.088±0.077 µm`: all `|m| > sd`, same sign on 5/5 seeds. Now: all small relative to the ~39 µm (39.24 µm) static sag, but the gaps are consistent (相对约 39 µm 的静沉都很小，但差距是稳定的). Bounce counts stay a tie (identical, 0).
- **gazebo-sim impact_drop COR, B vs C (found):** was "near-tie / small gap". Paired B−C `0.0018±0.0017` (`|m|` just above sd), same sign on 5/5 seeds → small but consistent gap.
- **gazebo-sim impact_drop "coarse loses" (found, nuanced):** A−C `618.19±549.08 µm` and B−C `153.83±40.77 µm` are consistent (5/5 same sign), but A−B `464.36±572.63 µm` is within seed noise (`|m| ≤ sd`; 1 of 5 seeds has the opposite sign). COR error A−B `0.2623±0.3771` is also within seed noise although A is worse on all 5 seeds (one seed dominates). Bounces A−B `0.20±2.17` (3 of 5 opposite, 1 equal). Prose now says coarse loses to fine on every seed, while A vs B is erratic rather than a consistent gap.
- **ohms-law:** no mislabels. Light-load C−B `0.0004±0.0015 mV` stays near-tie (`|m| ≤ sd`, 2 of 5 seeds opposite); A−B `0.1153±0.0588 mV` stays small but consistent (5/5 same sign); heavy-load A−B `784.7439±1.5259 mV` and C−B `10.2726±0.3258 mV` 5/5 same sign. Sign counts added to the prints and prose.

## #150 lessons

- **kinematics-ik far_from_singularity:** C−A final error printed `-0.0000+-0.0003`; now `-0.000043+-0.000253` ("indistinguishable from 0 within +-0.0003 mm"); `fmt_pair` prints six decimals only when four would show a signed zero. Near-tie lines also print "indistinguishable from 0 within ±sd".
- **kinematics-ik / depth-pointcloud:** en/zh "Read the regimes" now define consistent = `|paired mean| > sd` and say the 20 % rule only decides "small". Sign counts appended: **no sign flips** — every consistent / clear paired line (6 in kinematics-ik, 12 in depth-pointcloud) has the same sign on all 5 seeds.

## Opened source (curl -L + body read, 2026-11-09, Asia/Shanghai UTC+8)

- `wiki-max-power-transfer` / Wikipedia — Maximum power transfer theorem: https://en.wikipedia.org/wiki/Maximum_power_transfer_theorem, HTTP 200, HTML body verified (`mw-parser-output`). Load power is maximum when load resistance equals source resistance; efficiency `η = RL / (RL + RS)`; "Efficiency is only 50% if the load resistance equals the source resistance, which is the condition of maximum power transfer"; to achieve maximum efficiency the source resistance (battery or dynamo) should be as close to zero as possible (Edison / Upton, about 90 %). 以原文为准. Cached under `/workspace/b12pol-sources/` on the worktree host (not committed).
- ohms-law sentence: `RL = Rth` maximises load power (`Vth² / (4·Rth) ≈ 0.20 mW` for the lesson divider), but efficiency is only 50 %, so power supplies and battery-powered systems do not aim for impedance matching.

## Tooling

- `tools/check_diagrams.mjs`: removed the eight unused `added` destructuring bindings (array elision / dropped trailing binding); lint warnings from them are gone. No lock relaxed: the b12p1 / b12p2 strings were updated to the new outputs, and a batch-12 polish block adds stricter locks (paired lines, sign counts, no signed zero, definition sentences, max-power sentence and source).
- Tests: `tools/test_b12_thevenin_gazebo_toys.py` (gentle-rest paired rule recomputed independently; impact A−B within noise; sign_note), `tools/test_b12_manip_normals_toys.py` (sign counts, `fmt_pair`, no signed zero, all paired lines 5/5).

## Models / reproducibility

opencode `deepseek-v4.1-flash-free` was tried first on the lint item (180 s cap) and produced no file change; everything was implemented locally in `/workspace/hl-b12pol` (node_modules via `cp -al` from hl-b12p3).
