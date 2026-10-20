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
stop() {      # stop <pattern>: SIGINT the launch, then SIGKILL it if it has not exited after 20 s
  pkill -INT -f "$1"                # (ros2 launch can hang on exit after all its nodes are gone)
  for _ in $(seq 40); do pgrep -f "$1" > /dev/null || break; sleep 0.5; done
  pkill -KILL -f "$1" 2>/dev/null; wait
}
wait_for() {  # wait_for <file> <regex> [tries]: poll a log until a line appears
  for _ in $(seq "${3:-100}"); do grep -q -E "$2" "$1" && return 0; sleep 0.3; done; return 1
}

WS="$TMP/ws"; mkdir -p "$WS/src"
cp -r "$M4/urdf-tf/m4_description" "$M4/gazebo-sim/m4_gazebo" "$M4/ros2-control/m4_control" \
      "$M4/ros2-control/m4_drive_interfaces" "$M4/slam-nav/m4_nav" "$WS/src/"
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
stop 'ros2 launch m4_gazebo'

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
stop 'ros2 launch m4_control'

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
stop 'ros2 launch m4_control'

# ---- Lesson 6: odometry check, mapping with SLAM Toolbox, navigation with Nav2 -------------
NAV="$M4/slam-nav"; MAPS="$TMP/maps"; mkdir -p "$MAPS"
# the scans are compared to 0.1 deg and Gazebo's contact physics is not bit-exact
timeout -s INT 90 ros2 launch m4_control control.launch.py headless:=true > "$TMP/ctl6" 2>&1 &
ctl_ready || { tail -30 "$TMP/ctl6"; exit 1; }
check m4-ros-nav_spin_raw.txt --tol 0.03 bash -c "echo '\$ python3 spin_check.py'; python3 '$NAV/spin_check.py'"
stop 'ros2 launch m4_control'

timeout -s INT 400 ros2 launch m4_nav slam.launch.py headless:=true > "$TMP/slam" 2>&1 &
ctl_ready || { tail -30 "$TMP/slam"; exit 1; }
wait_for "$TMP/slam" 'Registering sensor' 200 || { tail -30 "$TMP/slam"; exit 1; }
check m4-ros-nav_spin_cal.txt --tol 0.03 bash -c "echo '\$ python3 spin_check.py'; python3 '$NAV/spin_check.py'"
check m4-ros-nav_tour.txt --tol 0.06 --mask 'yaw -?[0-9]+ deg' bash -c "echo '\$ python3 tour.py'; python3 '$NAV/tour.py'"
save_map() {
  echo "\$ ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph \"{filename: '/home/you/maps/room'}\""
  ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '$MAPS/room'}" | sed "s|$MAPS|/home/you/maps|"
  echo '$ ros2 run nav2_map_server map_saver_cli -f ~/maps/room --ros-args -p use_sim_time:=true'
  # map_saver gives up if /map has not arrived within 2 s ("Failed to spin map subscription"),
  # which happens now and then on a loaded machine: try up to 3 times, show the last attempt
  for _ in 1 2 3; do
    ros2 run nav2_map_server map_saver_cli -f "$MAPS/room" --ros-args -p use_sim_time:=true > "$TMP/saver" 2>&1 && break
    sleep 2
  done
  sed "s|$MAPS|/home/you/maps|" "$TMP/saver"
  echo '$ ls ~/maps'; ls "$MAPS"
  echo '$ cat ~/maps/room.yaml'; cat "$MAPS/room.yaml"; echo   # map_saver ends the file without a newline
}
# the map's origin is where SLAM Toolbox's first scan put the walls: a few mm either way
check m4-ros-nav_save.txt --tol 0.01 save_map
# what must hold: the map is the room's size and every object is found; how many cells a wall
# gets depends on the scans and the loop closure (it can halve between runs), so counts are masked
# here and map_check.py itself enforces the minimums (MIN_CELLS, MIN_OCCUPIED, MIN_FREE): a map
# below them prints FAIL lines, which are not masked
check m4-ros-nav_map_check.txt --tol 0.2 --mask '\(\d+ occupied cells\)' --mask '(?m)^occupied .*$' --mask '\d+ x \d+ cells' bash -c "echo '\$ python3 map_check.py ~/maps/room.yaml'; python3 '$NAV/map_check.py' '$MAPS/room.yaml'"
# keep the saved map (tools/sim/out/maps/) and check that map_check rejects a blank map and a
# map with one object erased (examples/month-4/slam-nav/map_check_test.py)
mkdir -p "$OUT/maps"; cp "$MAPS/room.yaml" "$MAPS/room.pgm" "$OUT/maps/"
if python3 "$NAV/map_check_test.py" "$MAPS/room.yaml" > "$OUT/m4-ros-nav_map_check_negative.log" 2>&1; then
  echo "same  map_check negative tests (blank map and erased object rejected)"
else
  echo "DIFF  map_check negative tests (see $OUT/m4-ros-nav_map_check_negative.log)"; fail=1
fi
stop 'ros2 launch m4_nav'

timeout -s INT 300 ros2 launch m4_nav nav.launch.py map:="$MAPS/room" headless:=true > "$TMP/nav" 2>&1 &
wait_for "$TMP/nav" 'Managed nodes are active' 300 || { tail -30 "$TMP/nav"; exit 1; }
sleep 3
where() {     # the robot's pose in the map, as the TF tree says
  echo '$ ros2 run tf2_ros tf2_echo map base_footprint --ros-args -p use_sim_time:=true'
  timeout -s INT 8 ros2 run tf2_ros tf2_echo map base_footprint --ros-args -p use_sim_time:=true 2>/dev/null \
    | grep -m1 -A4 '^At time' | grep -E 'Translation|degree'
}
goal() {      # goal <x> <y>: one NavigateToPose goal from the command line, then where the robot is
  local g="{pose: {header: {frame_id: map}, pose: {position: {x: $1, y: $2}, orientation: {w: 1.0}}}}"
  echo "\$ ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \"$g\""
  ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "$g"
  where
}
# Nav2 stops anywhere within its goal tolerance (0.10 m, 0.15 rad in nav2.yaml): heading masked
check m4-ros-nav_goal.txt --tol 0.1 --mask 'ID: [0-9a-f]+' --mask 'degree\) \[.*\]' goal 2.0 -2.0
cp "$TMP/nav" "$OUT/m4-ros-nav_log.txt"
stop 'ros2 launch m4_nav'

exit $fail
