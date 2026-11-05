#!/usr/bin/env bash
# Run the Month 11 examples and compare with expected/.
# All 7 of 7 lessons (11.1–11.7).
# Usage: examples/month-11/check.sh        UPDATE=1 examples/month-11/check.sh
set -uo pipefail
M11="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PYTHONDONTWRITEBYTECODE=1
PY="${M11_PYTHON:-python3}"
fail=0
check() {
  local name="$1"; shift
  (cd "$TMP" && "$@") > "$TMP/$name" 2>&1
  local ec=$?
  if [[ $ec -ne 0 ]]; then echo "FAIL  $name (exit $ec)"; cat "$TMP/$name"; fail=1; return; fi
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/$name" "$M11/expected/$name"; echo "wrote $name"; return; fi
  if diff -u "$M11/expected/$name" "$TMP/$name" > "$TMP/$name.diff"; then echo "same  $name"
  else echo "DIFF  $name"; cat "$TMP/$name.diff"; fail=1; fi
}

check power_budget_toy.txt "$PY" "$M11/power-battery-emc/power_budget_toy.py"
check clarke_park_toy.txt "$PY" "$M11/foc-actuator-lab/clarke_park_toy.py"
check tactile_marker_toy.txt "$PY" "$M11/tactile-sensing/tactile_marker_toy.py"
check relative_traj_toy.txt "$PY" "$M11/umi-style-collection/relative_traj_toy.py"
check oxe_imbalance_toy.txt "$PY" "$M11/cross-embodiment-datasets/oxe_imbalance_toy.py"
check lipm_track_toy.txt "$PY" "$M11/humanoid-wbc-overview/lipm_track_toy.py"
check tactile_gate_toy.txt "$PY" "$M11/contact-rich-policies/tactile_gate_toy.py"

exit $fail
