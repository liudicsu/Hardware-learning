# Batch-18 PR3 sources — Knowledge Insulation and VLA-Adapter

Base `e055b90690d7655f9810d49fff920c193f1e7338` (batch-18 PR2 merged as #174; site **35400**, M10 **3330**). This PR: **M10 3330→3750 (+420)**, site **35400→35820**, still 71 lessons. Branch `feat/ki-vla-adapter`. Hosts: `flow-matching-policies` 660→870, `edge-deploy-checklist` 330→540.

## Papers, opened and body-read on 2026-11-12 (Asia/Shanghai)

- Knowledge Insulation, arXiv **2505.23705**. Title: *Knowledge Insulating Vision-Language-Action Models: Train Fast, Run Fast, Generalize Better*. **11 authors** verified on the abs page and PDF: Danny Driess, Jost Tobias Springenberg, Brian Ichter, Lili Yu, Adrian Li-Bell, Karl Pertsch, Allen Z. Ren, Homer Walke, Quan Vuong, Lucy Xiaoyang Shi, Sergey Levine. `https://arxiv.org/abs/2505.23705`, `https://arxiv.org/html/2505.23705`, `https://arxiv.org/pdf/2505.23705.pdf` — all HTTP **200**. HTML body and pdftotext of the PDF read (introduction / Figure 1, §5.2 eqs. 5–6, §6–7). Cited as `knowledge-insulation-html` and `knowledge-insulation-pdf`.
- VLA-Adapter, arXiv **2509.09372**. Title: *VLA-Adapter: An Effective Paradigm for Tiny-Scale Vision-Language-Action Model*. **16 authors** verified: Yihao Wang, Pengxiang Ding, Lingxiao Li, Can Cui, Zirui Ge, Xinyang Tong, Wenxuan Song, Han Zhao, Wei Zhao, Pengxu Hou, Siteng Huang, Yifan Tang, Wenhui Wang, Ru Zhang, Jianyi Liu, Donglin Wang. `https://arxiv.org/abs/2509.09372`, `https://arxiv.org/html/2509.09372`, `https://arxiv.org/pdf/2509.09372.pdf` — all HTTP **200**. HTML body and pdftotext of the PDF read (§3.2 findings, §3.3 Bridge Attention eqs. 1–2, training). Cited as `vla-adapter-html` and `vla-adapter-pdf`.

Paper percentages, 0.5B / 8-hour / LIBERO / DROID / 7.5× training-step claims stay **以论文为准**. GPU / π0 / 0.5B / LIBERO: **本页未运行**. Every m±sd figure below was **printed by the toys** into `expected/`.

## Fairness

Common random numbers; five seeds `(0, 1, 2, 3, 4)`; stdlib CPU only. Tie / lose regimes were written in the toy docstrings and lesson prose **before any first run**. Post-hoc architecture choices are named in the pages together with the first-run alternative, rerun on the same seeds.

## Results (printed by the toys)

Knowledge Insulation, `knowledge_insulation_flow_toy.py` (no plant integration step):

- conflict, slot head (main): frozen baseline probe 97.8000±0.7583 %; B-A probe 33.9000±6.9991 clear, same sign on all 5 seeds; C-B probe 0.0000+-0.0000 tie: identical on every seed; B-A control 0.8500±4.2815 near-tie (3 of 5 opposite); C-B control -10.1500±6.3161 clear, 5/5; B-A fit_mid 2.1921±0.6843 clear, 5/5 (A faster).
- coarse_bins: B-A probe 41.4000±2.5100 clear, 5/5; B-A control near-tie; B-A mse_4step 0.0904±0.0818 clear, 5/5 (B loses on the 4-step residual; kept).
- aligned: C near-ties on control; B-A probe 1.2000±0.8909 small but consistent, 5/5.
- First-run alternative, discrete head on the full h, same seeds, conflict: B-A probe -12.7500±12.1861 clear, 1 of 5 opposite (B worse); control still a near-tie.

VLA-Adapter, `vla_adapter_bridge_attention_toy.py` (no plant integration step):

- short_id: B-A success 5.6000±7.9009 near-tie; B-A params -2393.0000±0.0000 clear, 5/5; B-A flops -2036.0000±0.0000 clear, 5/5. Param counts A/B at d_raw=6: 2882/489.
- need_vl: C-B success -41.9000±12.6461 clear, 5/5 (shuffled lose). B-A success is a near-tie.
- precise: B-A success -20.2000±14.4075 clear, 1 of 5 opposite (tiny+bridge loses to the large head; kept); B-A params -2673.0000±0.0000 and flops -2316.0000±0.0000, both clear, 5/5.
- First-run alternative on short_id (`_vla_adapter_firstrun.py`, same seeds): A params 266, B 381; B success 11.3000±9.9411 against A's 98.7000±2.0797 (B-A -87.4000±9.6138 clear, 5/5).

Not ChatVLA, not OneDP, not SmolVLA, not the weights-only budget table, not OpenVLA-OFT.

## Post-hoc choices

- Knowledge Insulation: after the first run, the discrete head was restricted to action-slot hidden units `h[SEM:]`. The first-run full-h head is still trained on the same seeds and printed. That choice was not fixed before the first run.
- VLA-Adapter: after the first run, ActionQuery became a trained MLP, a proprio / ActionQuery residual was added to the readout (bridge-output block starting at 0), the large arm gained a 48-wide two-layer backbone stand-in, and STEPS/LR moved from 250 / 0.05 to 300 / 0.10, so the tiny arm wins the size and FLOP proxy and can actually fit short_id. The first-run short_id table is still produced by `_vla_adapter_firstrun.py` on the same seeds and printed.

## Mismatch with §9

- H5 said arm A would show a consistent semantic drop and/or a slower residual drop. The semantic drop holds on conflict with the slot head (B-A probe 33.9000±6.9991, clear, 5/5). The slower residual drop did **not** hold: A is faster at `fit_mid` (B-A 2.1921±0.6843, clear, 5/5). Printed as it is. The first-run full-h head had the probe comparison the other way around (B-A -12.7500±12.1861); that alternative is kept.
- H6 holds: size / latency consistent tiny win; shuffled conditions consistent lose; a success loss versus the large head on precise is kept; short_id A/B near-tie on success. Paper 0.5B / 8 h are not printed as toy results.

## opencode

Free models were tried in order DeepSeek, GLM, MiMo, LongCat, MiniMax (`opencode/*-flash-free` / `longcat-2.5-free`, 40 s each) via `/workspace/b18p3-opencode/run.sh`. DeepSeek exit 124 (timeout); the others exit 0 with 0 Python files. The toys, pages and locks were implemented locally.

## Lock changes

Curriculum totals 35400→35820; README 35 400→35 820; M10 3330→3750; host minutes 660→870 and 330→540 (including older locks that read the live host minutes). New block for this PR only tightens / adds checks. **No lock relaxed.**
