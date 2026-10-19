#!/usr/bin/env bash
# Month 4: real ROS 2 software driving a simulated robot (Gazebo Harmonic, and ros2_control's
# mock hardware). Every output the lessons quote with the "ROS 2 + simulated robot" label is
# produced here and compared with tools/sim/expected/m4-ros-*.txt.
# Needs ROS 2 Jazzy with ros_gz, ros2_control, slam_toolbox and nav2 (examples/month-4/pixi.toml
# installs all of it: cd examples/month-4 && pixi run sim). Gazebo runs headless; no GPU needed.
# The physics and the sensor noise make every run a little different, so numbers are compared
# with a tolerance (examples/month-4/compare.py --tol).
# Usage: tools/sim/ros/run.sh        UPDATE=1 (or UPDATE=<glob>) tools/sim/ros/run.sh rewrites expected/
set -uo pipefail
SIM="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$SIM/../.." && pwd)"
M4="$ROOT/examples/month-4"
OUT="$SIM/out"; mkdir -p "$OUT"
if [[ "${ROS_DISTRO:-}" != "jazzy" ]] || ! command -v gz >/dev/null; then
  echo "skip  m4-ros-* (ROS 2 Jazzy with Gazebo is not sourced; see examples/month-4/README.md)"; exit 0
fi
TMP="$(mktemp -d)"; trap 'kill $(jobs -p) 2>/dev/null; ros2 daemon stop >/dev/null 2>&1; rm -rf "$TMP"' EXIT
export ROS_DOMAIN_ID=$(( 140 + RANDOM % 90 )) ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_IP=127.0.0.1          # keep Gazebo's own transport on this machine
export RCUTILS_COLORIZED_OUTPUT=0 PYTHONUNBUFFERED=1
ros2 daemon start > /dev/null 2>&1
fail=0
check() {     # check <name> [--tol T] [--mask REGEX]... [--sort 1] <command...>
  local name="$1"; shift; local tol=()
  while [[ "${1:-}" == --tol || "${1:-}" == --mask || "${1:-}" == --sort ]]; do tol+=("$1" "$2"); shift 2; done
  "$@" > "$OUT/$name" 2>&1
  if [[ -n "${UPDATE:-}" ]] && { [[ "$UPDATE" == 1 ]] || [[ "$name" == $UPDATE ]]; }; then
    cp "$OUT/$name" "$SIM/expected/$name"; echo "wrote $name"; return
  fi
  if python3 "$M4/compare.py" "$SIM/expected/$name" "$OUT/$name" "${tol[@]}" > "$OUT/$name.diff"; then
    echo "same  $name"; rm -f "$OUT/$name.diff"
  else
    echo "DIFF  $name (see $OUT/$name.diff)"; fail=1
  fi
}
wait_for() {  # wait_for <file> <regex> [tries]: poll a log until a line appears
  for _ in $(seq "${3:-100}"); do grep -q -E "$2" "$1" && return 0; sleep 0.3; done; return 1
}

WS="$TMP/ws"; mkdir -p "$WS/src"
cp -r "$M4/urdf-tf/m4_description" "$M4/gazebo-sim/m4_gazebo" "$WS/src/"
(cd "$WS" && colcon build > "$TMP/build" 2>&1) || { cat "$TMP/build"; exit 1; }
set +u; source "$WS/install/setup.bash"; set -u

# ---- Lesson 4: m4bot in the obstacles world, with a lidar and a camera --------------------
timeout -s INT 120 ros2 launch m4_gazebo sim.launch.py headless:=true > "$TMP/sim" 2>&1 &
wait_for "$TMP/sim" 'Creating GZ->ROS Bridge: \[/?camera/camera_info' || { tail -30 "$TMP/sim"; exit 1; }
for _ in $(seq 40); do timeout 3 ros2 topic echo --once /scan --field header.frame_id > /dev/null 2>&1 && break; sleep 0.5; done
check m4-ros-gz_spawn.txt bash -c "grep -E 'Entity creation successful|Requested creation of entity' '$TMP/sim' | sed -E 's/^\[create-[0-9]+\] //' | head -2"
check m4-ros-gz_topics.txt bash -c "echo '\$ ros2 topic list'; ros2 topic list"
check m4-ros-scan_probe.txt --tol 0.05 python3 "$M4/gazebo-sim/scan_probe.py"
check m4-ros-camera_snap.txt bash -c "cd '$TMP' && python3 '$M4/gazebo-sim/snap_camera.py' camera.png"
drive() {
  echo '$ ros2 topic echo --once /odom --field pose.pose.position'
  ros2 topic echo --once /odom --field pose.pose.position
  echo '$ ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}"   # then wait 4 s'
  ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}" > /dev/null; sleep 4
  echo '$ ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"'
  ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}" > /dev/null; sleep 1
  echo '$ ros2 topic echo --once /odom --field pose.pose.position'
  ros2 topic echo --once /odom --field pose.pose.position
  echo '$ python3 scan_probe.py | grep ahead'
  python3 "$M4/gazebo-sim/scan_probe.py" | grep ahead
}
check m4-ros-gz_drive.txt --tol 0.25 drive
check m4-ros-gz_frame_warning.txt bash -c "grep -o 'XML Element\[gz_frame_id\].*' '$TMP/sim' | head -1"
pkill -INT -f 'ros2 launch m4_gazebo'; wait

exit $fail
