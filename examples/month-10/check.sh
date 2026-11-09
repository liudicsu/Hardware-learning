#!/usr/bin/env bash
# Run the Month 10 examples and compare with expected/.
# 7 of 7 lessons / 7 课全部写完（10.1–10.7，PR1–PR3）.
# Usage: examples/month-10/check.sh        UPDATE=1 examples/month-10/check.sh
set -uo pipefail
M10="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PYTHONDONTWRITEBYTECODE=1
PY="${M10_PYTHON:-python3}"
fail=0
check() {
  local name="$1"; shift
  (cd "$TMP" && "$@") > "$TMP/$name" 2>&1
  local ec=$?
  if [[ $ec -ne 0 ]]; then echo "FAIL  $name (exit $ec)"; cat "$TMP/$name"; fail=1; return; fi
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/$name" "$M10/expected/$name"; echo "wrote $name"; return; fi
  if diff -u "$M10/expected/$name" "$TMP/$name" > "$TMP/$name.diff"; then echo "same  $name"
  else echo "DIFF  $name"; cat "$TMP/$name.diff"; fail=1; fi
}

check flow_match_toy.txt "$PY" "$M10/flow-matching-policies/flow_match_toy.py"
check rtc_blend_toy.txt "$PY" "$M10/real-time-chunking/rtc_blend_toy.py"
check int8_quant_toy.txt "$PY" "$M10/edge-deploy-checklist/int8_quant_toy.py"
check latency_budget.txt "$PY" "$M10/edge-deploy-checklist/latency_budget.py"
check vla_edge_budget_toy.txt "$PY" "$M10/edge-deploy-checklist/vla_edge_budget_toy.py"
check extrinsics_chain_toy.txt "$PY" "$M10/multi-view-extrinsics/extrinsics_chain_toy.py"
check spatialvla_ego3d_grid_toy.txt "$PY" "$M10/multi-view-extrinsics/spatialvla_ego3d_grid_toy.py"
check intervention_log_toy.txt "$PY" "$M10/intervention-logging/intervention_log_toy.py"
check rlpd_chain_toy.txt "$PY" "$M10/real-world-rl/rlpd_chain_toy.py"
check advantage_filter_toy.txt "$PY" "$M10/vla-rl-finetune/advantage_filter_toy.py"

check cal_conrft_offline_toy.txt "$PY" "$M10/vla-rl-finetune/cal_conrft_offline_toy.py"
check cal_conrft_offline_tabular.txt "$PY" "$M10/vla-rl-finetune/cal_conrft_offline_toy.py" --tabular

check policy_distill_onestep_toy.txt "$PY" "$M10/flow-matching-policies/policy_distill_onestep_toy.py"

check preference_dpo_lite_toy.txt "$PY" "$M10/real-world-rl/preference_dpo_lite_toy.py"

exit $fail
