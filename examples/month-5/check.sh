#!/usr/bin/env bash
# Run the Month 5 enrichment toys and compare with expected/.
# Legacy joint_freq / lqr_sim / etc. stay under tools/sim/reproduce.sh.
# Usage: examples/month-5/check.sh        UPDATE=1 examples/month-5/check.sh
set -uo pipefail
M5="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PYTHONDONTWRITEBYTECODE=1
PY="${M5_PYTHON:-python3}"
fail=0
check() {
  local name="$1"; shift
  (cd "$TMP" && "$@") > "$TMP/$name" 2>&1
  local ec=$?
  if [[ $ec -ne 0 ]]; then echo "FAIL  $name (exit $ec)"; cat "$TMP/$name"; fail=1; return; fi
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/$name" "$M5/expected/$name"; echo "wrote $name"; return; fi
  if diff -u "$M5/expected/$name" "$TMP/$name" > "$TMP/$name.diff"; then echo "same  $name"
  else echo "DIFF  $name"; cat "$TMP/$name.diff"; fail=1; fi
}

check sysid_pe_compare_toy.txt "$PY" "$M5/control-modelling/sysid_pe_compare_toy.py"
check lqr_model_error_toy.txt "$PY" "$M5/state-space-lqr/lqr_model_error_toy.py"

check stereo_depth_sigma_toy.txt "$PY" "$M5/camera-calibration/stereo_depth_sigma_toy.py"

check quat_vs_euler_gimbal_toy.txt "$PY" "$M5/kinematics-ik/quat_vs_euler_gimbal_toy.py"

exit $fail
