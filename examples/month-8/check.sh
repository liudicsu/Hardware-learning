#!/usr/bin/env bash
# Run the Month 8 examples and compare with expected/.
# Batch 1: 8.1 / 8.3 / 8.5 / 8.6 toys are stdlib.
# Usage: examples/month-8/check.sh        UPDATE=1 examples/month-8/check.sh
set -uo pipefail
M8="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PYTHONDONTWRITEBYTECODE=1
PY="${M8_PYTHON:-python3}"
fail=0
check() {
  local name="$1"; shift
  (cd "$TMP" && "$@") > "$TMP/$name" 2>&1
  local ec=$?
  if [[ $ec -ne 0 ]]; then echo "FAIL  $name (exit $ec)"; cat "$TMP/$name"; fail=1; return; fi
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/$name" "$M8/expected/$name"; echo "wrote $name"; return; fi
  if diff -u "$M8/expected/$name" "$TMP/$name" > "$TMP/$name.diff"; then echo "same  $name"
  else echo "DIFF  $name"; cat "$TMP/$name.diff"; fail=1; fi
}

check dataset_audit.txt "$PY" "$M8/dataset-engineering/dataset_audit.py"
check chunk_latency_sim.txt "$PY" "$M8/async-deployment/chunk_latency_sim.py"
check watchdog_sim.txt "$PY" "$M8/safety-reliability/watchdog_sim.py"
check bag_stats.txt "$PY" "$M8/robot-devops/bag_stats.py"

exit $fail
