#!/usr/bin/env bash
# Run the Month 7 examples and compare with expected/.
# 7.1 needs mujoco (set M7_PYTHON to a venv that has it). 7.2 and 7.5 are stdlib only.
# Usage: examples/month-7/check.sh        UPDATE=1 examples/month-7/check.sh
set -uo pipefail
M7="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PYTHONDONTWRITEBYTECODE=1
PY="${M7_PYTHON:-python3}"
fail=0
check() {
  local name="$1"; shift
  (cd "$TMP" && "$@") > "$TMP/$name" 2>&1
  local ec=$?
  if [[ $ec -ne 0 ]]; then echo "FAIL  $name (exit $ec)"; cat "$TMP/$name"; fail=1; return; fi
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/$name" "$M7/expected/$name"; echo "wrote $name"; return; fi
  if diff -u "$M7/expected/$name" "$TMP/$name" > "$TMP/$name.diff"; then echo "same  $name"
  else echo "DIFF  $name"; cat "$TMP/$name.diff"; fail=1; fi
}

# ---- 7.1 MuJoCo grip sweep (needs mujoco) -------------------------------------------------
if "$PY" -c 'import mujoco' 2>/dev/null; then
  check grip_sweep.txt "$PY" "$M7/mujoco-so101/grip_sweep.py"
else
  echo "SKIP  grip_sweep.txt (mujoco not importable under M7_PYTHON=$PY)"
  # Still fail the overall check when UPDATE is unset, so CI/reproduce notices the gap only
  # if someone opts in; for local without mujoco we skip without failing.
  if [[ -n "${M7_REQUIRE_MUJOCO:-}" ]]; then fail=1; fi
fi

# ---- 7.2 RL foundations (stdlib) ----------------------------------------------------------
check ppo_reach.txt "$PY" "$M7/rl-foundations/ppo_reach.py"

# ---- 7.5 depth / point cloud (stdlib) -----------------------------------------------------
check cloud_pipeline.txt "$PY" "$M7/depth-pointcloud/cloud_pipeline.py"

exit $fail
