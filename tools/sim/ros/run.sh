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
TMP="$(mktemp -d)"
trap 'kill $(jobs -p) 2>/dev/null; pkill -f "gz sim.*$TMP" 2>/dev/null; ros2 daemon stop >/dev/null 2>&1; rm -rf "$TMP"' EXIT
export ROS_DOMAIN_ID=$(( 140 + RANDOM % 90 )) ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_IP=127.0.0.1          # keep Gazebo's own transport on this machine
export GZ_PARTITION="m4sim_$$"  # ... and apart from any other Gazebo running on it
export RCUTILS_COLORIZED_OUTPUT=0 PYTHONUNBUFFERED=1
ros2 daemon start > /dev/null 2>&1
fail=0
check() {     # check <name> [--tol T] [--mask REGEX]... [--drop REGEX]... [--sort 1] <command...>
  local name="$1"; shift; local tol=()
  while [[ "${1:-}" == --tol || "${1:-}" == --mask || "${1:-}" == --drop || "${1:-}" == --sort ]]; do tol+=("$1" "$2"); shift 2; done
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
cp -r "$M4/urdf-tf/m4_description" "$M4/gazebo-sim/m4_gazebo" "$M4/ros2-control/m4_control" \
      "$M4/ros2-control/m4_drive_interfaces" "$WS/src/"
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
  echo '$ ros2 topic echo --once --no-lost-messages /odom --field pose.pose.position'
  ros2 topic echo --once --no-lost-messages /odom --field pose.pose.position
  echo '$ ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}"   # then wait 4 s'
  ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}" > /dev/null; sleep 4
  echo '$ ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}"'
  ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}" > /dev/null; sleep 1
  echo '$ ros2 topic echo --once --no-lost-messages /odom --field pose.pose.position'
  ros2 topic echo --once --no-lost-messages /odom --field pose.pose.position
  echo '$ python3 scan_probe.py | grep ahead'
  python3 "$M4/gazebo-sim/scan_probe.py" | grep ahead
}
# How far the robot rolls depends on how fast the second `ros2 topic pub` starts, so the two
# travel numbers are masked and checked for consistency instead: odometry + lidar must still
# add up to the 1.67 m measured at the start, and the robot must have gone at least 0.8 m.
check m4-ros-gz_drive.txt --tol 0.25 --mask '(?m)^x: [01]\.\d+$' --mask 'ahead \(0\.0 deg\): [0-9.]+' drive
python3 - "$OUT/m4-ros-gz_drive.txt" <<'PY' || fail=1
import re, sys
t = open(sys.argv[1]).read()
x = float(re.findall(r'^x: (\S+)$', t, re.M)[1]); d = float(re.search(r'ahead \(0\.0 deg\): ([0-9.]+)', t).group(1))
ok = x >= 0.8 and abs(x + d - 1.67) <= 0.05
print(f"{'same ' if ok else 'DIFF '} m4-ros-gz_drive.txt odometry + lidar: {x:.2f} + {d:.2f} = {x + d:.2f} m (expect 1.67 m, travel >= 0.80 m)")
sys.exit(0 if ok else 1)
PY
check m4-ros-gz_frame_warning.txt bash -c "grep -o 'XML Element\[gz_frame_id\].*' '$TMP/sim' | head -1"
pkill -INT -f 'ros2 launch m4_gazebo'; wait

# ---- Lesson 5: the same robot through ros2_control (Gazebo, then mock hardware) -----------
ctl_ready() { for _ in $(seq 120); do ros2 control list_controllers 2>/dev/null | grep -q 'head_controller.*active' && return 0; sleep 0.5; done; return 1; }
timeout -s INT 150 ros2 launch m4_control control.launch.py headless:=true > "$TMP/ctl" 2>&1 &
ctl_ready || { tail -30 "$TMP/ctl"; exit 1; }
wait_for "$TMP/ctl" 'accepting goals' || { tail -30 "$TMP/ctl"; exit 1; }
check m4-ros-ctl_controllers.txt --sort 1 --drop 'waiting for service' bash -c "echo '\$ ros2 control list_controllers'; ros2 control list_controllers"
check m4-ros-ctl_interfaces.txt bash -c "echo '\$ ros2 control list_hardware_interfaces'; ros2 control list_hardware_interfaces 2>/dev/null"
timeout_demo() {
  echo '$ ros2 topic pub --once /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.2}}}"'
  ros2 topic pub --once /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.2}}}" > /dev/null
  sleep 3
  echo '$ ros2 topic echo --once --no-lost-messages /diff_drive_controller/odom --field pose.pose.position'
  ros2 topic echo --once --no-lost-messages /diff_drive_controller/odom --field pose.pose.position
}
check m4-ros-ctl_timeout.txt --tol 0.25 timeout_demo
check m4-ros-ctl_timeout_log.txt bash -c "grep -o '\[diff_drive_controller\]: Velocity command timed out.*' '$TMP/ctl' | tail -1"
drive_demo() {   # drive_demo <distance> <speed> [cancel after s]
  echo "\$ python3 drive_client.py $*"
  python3 "$M4/ros2-control/drive_client.py" "$@"
  sleep 1
  echo '$ ros2 topic echo --once --no-lost-messages /diff_drive_controller/odom --field pose.pose.position'
  ros2 topic echo --once --no-lost-messages /diff_drive_controller/odom --field pose.pose.position
}
check m4-ros-ctl_drive.txt --tol 0.25 --drop '^feedback:' drive_demo 1.0 0.2
check m4-ros-ctl_cancel.txt --tol 0.25 --drop '^feedback:' drive_demo -1.0 0.2 2.0
pkill -INT -f 'ros2 launch m4_control'; wait

timeout -s INT 60 ros2 launch m4_control control.launch.py hardware:=mock headless:=true > "$TMP/mock" 2>&1 &
ctl_ready || { tail -30 "$TMP/mock"; exit 1; }
mock_demo() {
  echo '$ ros2 control list_hardware_components'
  ros2 control list_hardware_components 2>/dev/null | head -5
  echo '$ ros2 topic pub -r 20 -t 40 /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.2}}}"'
  ros2 topic pub -r 20 -t 40 /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.2}}}" > /dev/null
  sleep 1
  echo '$ ros2 topic echo --once --no-lost-messages /diff_drive_controller/odom --field pose.pose.position'
  ros2 topic echo --once --no-lost-messages /diff_drive_controller/odom --field pose.pose.position
}
check m4-ros-ctl_mock.txt --tol 0.1 mock_demo
pkill -INT -f 'ros2 launch m4_control'; wait

exit $fail
