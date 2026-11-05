#!/usr/bin/env bash
# Run the Month 10 examples and compare with expected/.
# 3 of 7 lessons so far / 已写 3 课（共 7 课；10.1–10.3，PR1）.
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

exit $fail
