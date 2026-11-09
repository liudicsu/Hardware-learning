#!/usr/bin/env bash
# Run the Month 7 examples and compare with expected/.
# 7.1 needs mujoco (set M7_PYTHON). 7.2/7.3/7.4 toys are stdlib.
# 7.6 handeye_toy needs NumPy; grasp_from_mask is stdlib.
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
  if [[ -n "${M7_REQUIRE_MUJOCO:-}" ]]; then fail=1; fi
fi

# ---- 7.2 RL foundations (stdlib) ----------------------------------------------------------
check ppo_reach.txt "$PY" "$M7/rl-foundations/ppo_reach.py"

# ---- 7.3 reward shaping (stdlib) ----------------------------------------------------------
check reward_shaping.txt "$PY" "$M7/rl-manipulation-sim/reward_shaping.py"
check her_sparse_grasp_toy.txt "$PY" "$M7/rl-manipulation-sim/her_sparse_grasp_toy.py"

# ---- 7.4 sim-to-real (stdlib) -------------------------------------------------------------
check sysid_fit.txt "$PY" "$M7/sim-to-real/sysid_fit.py"
check randomize_eval.txt "$PY" "$M7/sim-to-real/randomize_eval.py"
check contact_dr_toy.txt "$PY" "$M7/sim-to-real/contact_dr_toy.py"

# ---- 7.5 depth / point cloud (stdlib) -----------------------------------------------------
check cloud_pipeline.txt "$PY" "$M7/depth-pointcloud/cloud_pipeline.py"

# ---- 7.6 perception-to-grasp --------------------------------------------------------------
if "$PY" -c 'import numpy' 2>/dev/null; then
  check handeye_toy.txt "$PY" "$M7/perception-to-grasp/handeye_toy.py"
else
  echo "SKIP  handeye_toy.txt (numpy not importable under M7_PYTHON=$PY)"
  if [[ -n "${M7_REQUIRE_NUMPY:-}" ]]; then fail=1; fi
fi
check grasp_from_mask.txt "$PY" "$M7/perception-to-grasp/grasp_from_mask.py"
check antipodal_force_closure_toy.txt "$PY" "$M7/perception-to-grasp/antipodal_force_closure_toy.py"

check gsplat_collision_toy.txt "$PY" "$M7/depth-pointcloud/gsplat_collision_toy.py"
check pointcloud_pca_normals_toy.txt "$PY" "$M7/depth-pointcloud/pointcloud_pca_normals_toy.py"

check residual_action_mismatch_toy.txt "$PY" "$M7/rl-foundations/residual_action_mismatch_toy.py"

exit $fail
