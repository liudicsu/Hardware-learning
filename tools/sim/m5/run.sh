#!/usr/bin/env bash
# Month 5 runs that need more than the Python standard library: OpenCV + NumPy (Lesson 4,
# camera calibration on synthetic photos) and MoveIt 2 (Lesson 5). Compared with
# tools/sim/expected/m5-*.txt. Install everything with examples/month-5/pixi.toml:
#   cd examples/month-5 && pixi install && pixi run sim
# Usage: tools/sim/m5/run.sh        UPDATE=1 tools/sim/m5/run.sh rewrites expected/
set -uo pipefail
SIM="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$SIM/../.." && pwd)"
M5="$ROOT/examples/month-5"
OUT="$SIM/out"; mkdir -p "$OUT"
if ! python3 -c "import cv2, numpy" 2>/dev/null; then
  echo "skip  m5-cam_* and m5-moveit_* (OpenCV and NumPy not installed; see examples/month-5/README.md)"; exit 0
fi
TMP="$(mktemp -d)"
trap 'kill $(jobs -p) 2>/dev/null; rm -rf "$TMP"' EXIT
fail=0
check() {     # check <name> [--mask REGEX]... <command...>: run in $TMP, compare with expected/<name>
  local name="$1"; shift; local opts=()
  while [[ "${1:-}" == --mask ]]; do opts+=("$1" "$2"); shift 2; done
  (cd "$TMP" && "$@") > "$OUT/$name" 2>&1
  if [[ -n "${UPDATE:-}" ]]; then cp "$OUT/$name" "$SIM/expected/$name"; echo "wrote $name"; return; fi
  if python3 "$ROOT/examples/month-4/compare.py" "$SIM/expected/$name" "$OUT/$name" "${opts[@]}" > "$OUT/$name.diff"; then
    echo "same  $name"; rm -f "$OUT/$name.diff"
  else echo "DIFF  $name (see $OUT/$name.diff)"; fail=1; fi
}

# ---- Lesson 4: camera calibration on synthetic checkerboard photos --------------------------
CAM="$M5/camera-calibration"
check m5-cam_views.txt python3 "$CAM/make_views.py" views
check m5-cam_calibrate.txt python3 "$CAM/calibrate.py" views
check m5-cam_pixel.txt python3 "$CAM/pixel_to_table.py" views

# ---- Lesson 5: pick and place with MoveIt 2 on the Panda's ros2_control mock hardware ---------
if [[ "${ROS_DISTRO:-}" != "jazzy" ]] || ! python3 -c "import moveit.planning" 2>/dev/null; then
  echo "skip  m5-moveit_* (ROS 2 Jazzy with MoveIt 2 is not sourced; see examples/month-5/README.md)"; exit $fail
fi
export ROS_DOMAIN_ID=$(( 140 + RANDOM % 90 )) ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST RCUTILS_COLORIZED_OUTPUT=0 PYTHONUNBUFFERED=1
PP="$M5/moveit-pick-place"
timeout -s INT 200 ros2 launch "$PP/bringup.launch.py" > "$TMP/bringup" 2>&1 &
for _ in $(seq 120); do [[ $(grep -c 'Configured and activated' "$TMP/bringup") -ge 3 ]] && break; sleep 0.5; done
# OMPL is a random planner: its waypoint counts and its route over the wall change from run to run
check m5-moveit_pick_place.txt --mask '(?<=ompl_rrtc)\s+\d+(?= waypoints)' --mask '(?m)^     route: .*$' --mask 'all \d+ waypoints' \
  bash -c "python3 '$PP/pick_place.py' 2> '$TMP/pp.err'"
check m5-moveit_goal_invalid.txt bash -c "grep -o 'Unable to sample any valid states for goal tree\|Planner .OMPL. failed with error code [A-Z_]*' '$TMP/pp.err' | sort -u"
exit $fail
