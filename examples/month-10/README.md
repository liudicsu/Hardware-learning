# Month 10 examples

CPU-reproducible scripts for Month 10 (site supplement). Run `./check.sh` from this folder.

| lesson | script | needs |
|--------|--------|-------|
| flow-matching-policies | `flow-matching-policies/flow_match_toy.py` | stdlib |
| real-time-chunking | `real-time-chunking/rtc_blend_toy.py`, `forge_tree_mctd_toy.py` | stdlib |
| edge-deploy-checklist | `edge-deploy-checklist/int8_quant_toy.py`, `edge-deploy-checklist/latency_budget.py`, `edge-deploy-checklist/vla_edge_budget_toy.py` | stdlib |
| multi-view-extrinsics | `multi-view-extrinsics/extrinsics_chain_toy.py` | stdlib |
| intervention-logging | `intervention-logging/intervention_log_toy.py` | stdlib |
| real-world-rl | `real-world-rl/rlpd_chain_toy.py`, `thinkact_visual_latent_toy.py` | stdlib |
| vla-rl-finetune | `vla-rl-finetune/advantage_filter_toy.py` | stdlib |

7 of 7 lessons / 7 课全部写完（10.1–10.7）.
No GPU, no Jetson, no robot, no second camera, no weight downloads, no Isaac, no F/T sensor. Steps that need them are marked 本页未运行 / not run on this page in the lessons.

## Batch-5 PR3

`cal_conrft_offline_toy.py`: shared offline BC/CQL/Cal-QL batches/updates, MC-masked conservative gradient, restricted and `--tabular` representation controls; five-seed scale/success tables. No online phase or consistency head. / 同数据等更新、MC 屏蔽与表示能力对照；五种子；无在线阶段或一致性头。
