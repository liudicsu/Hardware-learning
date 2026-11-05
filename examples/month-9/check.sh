#!/usr/bin/env bash
# Run the Month 9 examples and compare with expected/.
# 9 lessons complete / 9 课已齐 (9.1–9.9 Track B).
# Usage: examples/month-9/check.sh        UPDATE=1 examples/month-9/check.sh
set -uo pipefail
M9="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PYTHONDONTWRITEBYTECODE=1
PY="${M9_PYTHON:-python3}"
fail=0
check() {
  local name="$1"; shift
  (cd "$TMP" && "$@") > "$TMP/$name" 2>&1
  local ec=$?
  if [[ $ec -ne 0 ]]; then echo "FAIL  $name (exit $ec)"; cat "$TMP/$name"; fail=1; return; fi
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/$name" "$M9/expected/$name"; echo "wrote $name"; return; fi
  if diff -u "$M9/expected/$name" "$TMP/$name" > "$TMP/$name.diff"; then echo "same  $name"
  else echo "DIFF  $name"; cat "$TMP/$name.diff"; fail=1; fi
}

check stage_graph_toy.txt "$PY" "$M9/mtc-long-horizon/stage_graph_toy.py"
check servo_loop_sim.txt "$PY" "$M9/moveit-servo/servo_loop_sim.py"
check load_contact_sim.txt "$PY" "$M9/effort-admittance/load_contact_sim.py"
check admittance_1d.txt "$PY" "$M9/effort-admittance/admittance_1d.py"
check saycan_score_toy.txt "$PY" "$M9/llm-skill-planning/saycan_score_toy.py"
check recovery_bt_toy.txt "$PY" "$M9/failure-recovery/recovery_bt_toy.py"
check nav_pick_bt.txt "$PY" "$M9/nav-arm-compose/nav_pick_bt.py"
check demo_gate.txt "$PY" "$M9/multi-skill-demo/demo_gate.py" --all
check tag_error_jog.txt "$PY" "$M9/visual-servoing/tag_error_jog.py"
check latent_predict_toy.txt "$PY" "$M9/world-models-overview/latent_predict_toy.py"

exit $fail
