# Batch-11 PR3 sources — CogACT DiT action + continual ER

Base: `777543d` (batch-11 PR2 #146 merged; site **27630**). Proposal §9 PR3 locks: H5 6.2 act-diffusion CogACT +210, H6 8.2 vla-finetune continual ER +210. No arithmetic mismatch: after this PR M6 **2400**, M8 **3390**, site **28050**; 71 lessons. All prior expected files remain byte-identical except the two added here.

## Sources opened this PR (abs + HTML body + PDF via pdftotext)

| id | URL | What was verified |
|----|-----|-------------------|
| cogact-abs | https://arxiv.org/abs/2411.19650 | Title *CogACT: A Foundational Vision-Language-Action Model for Synergizing Cognition and Action in Robotic Manipulation*; authors **Qixiu Li**, Yaobo Liang, Zeyu Wang, et al. curl 200. |
| cogact-html | https://arxiv.org/html/2411.19650 | Body: componentized VLM → specialized action module; MLP depths vs DiT-style diffusion action heads (§3). PDF also fetched; `pdftotext` cross-check. Paper SIMPLER/real % **以论文为准**. |
| cl-abs | https://arxiv.org/abs/2603.03818 | Title *Pretrained Vision-Language-Action Models are Surprisingly Resistant to Forgetting in Continual Learning*; authors **Huihan Liu**, Changyeon Kim, Bo Liu, Minghuan Liu, Yuke Zhu. curl 200. |
| cl-html | https://arxiv.org/html/2603.03818 | Body: pretrained VLAs resist forgetting; simple Experience Replay often cuts forgetting sharply (§3.2); LIBERO / NBT / buffer-size notes. PDF + `pdftotext`. Paper NBT/LIBERO % **以论文为准**. |

Local mirrors used during authorship: `/workspace/b11p3-sources/` (`cogact-*.html/txt/pdf/pdftxt`, `cl-*.html/txt/pdf/pdftxt`).

## Toys

- `examples/month-6/act-diffusion/cogact_dit_action_toy.py` — A ridge-linear, B pairwise-expand+iterative DiT-style **expressivity stand-in** (not a real transformer), C quantized tokens; CRN demos/noise; unimodal_short exact tie; multimodal_long DiT-style edge.
- `examples/month-8/vla-finetune/vla_continual_er_toy.py` — A sequential cap=0, B ER cap=8 replay=2, C ER cap=48 replay=4 with protected prior-task prefix; compute = samples touched; no_shift near-tie / small gap; task_shift ER reduces NBT forget.

## Checks run

`tools/test_b11_cogact_continual_toys.py`, month-6 / month-8 `check.sh`, `check_quotes`, `check_diagrams`, `check_widgets`, `check_wokwi`, lint, next typegen, `tsc --noEmit`, production build. No workflow edits. Minutes **71 / 28050**.
