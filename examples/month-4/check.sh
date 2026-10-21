#!/usr/bin/env bash
# Run the Month 4 ROS 2 examples the way the lessons do and compare with the outputs they quote
# (stored in expected/). These are real ROS 2 programs on your computer; nothing here uses a
# simulator (the Gazebo and mock-hardware runs are in tools/sim/reproduce.sh).
# Needs: ROS 2 Jazzy sourced (ros2, colcon) - see README.md. Output that changes from run to run
# (timestamps, timings, process numbers) is masked by compare.py.
# Usage: examples/month-4/check.sh        UPDATE=1 (or UPDATE=<glob>) examples/month-4/check.sh rewrites expected/
set -uo pipefail
M4="$(cd "$(dirname "$0")" && pwd)"
if [[ "${ROS_DISTRO:-}" != "jazzy" ]] || ! command -v colcon >/dev/null; then
  echo "ROS 2 Jazzy is not sourced (ROS_DISTRO=${ROS_DISTRO:-unset}); see examples/month-4/README.md"; exit 2
fi
TMP="$(mktemp -d)"; trap 'kill $(jobs -p) 2>/dev/null; ros2 daemon stop >/dev/null 2>&1; rm -rf "$TMP"' EXIT
export ROS_DOMAIN_ID=$(( 40 + RANDOM % 50 )) ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export RCUTILS_COLORIZED_OUTPUT=0 PYTHONUNBUFFERED=1
ros2 daemon start > /dev/null 2>&1   # the CLI's discovery cache for this domain; warm it up early
fail=0
check() {     # check <expected file> [--tol T] [--mask REGEX]... [--sort 1] <command...>
  local name="$1"; shift; local tol=()
  while [[ "${1:-}" == --tol || "${1:-}" == --mask || "${1:-}" == --sort ]]; do tol+=("$1" "$2"); shift 2; done
  "$@" > "$TMP/out" 2>&1
  # UPDATE=1 rewrites every expected file; UPDATE=<glob> only the matching ones (e.g. UPDATE='ros-bag*')
  if [[ -n "${UPDATE:-}" ]] && { [[ "$UPDATE" == 1 ]] || [[ "$name" == $UPDATE ]]; }; then
    cp "$TMP/out" "$M4/expected/$name"; echo "wrote $name"; return
  fi
  if python3 "$M4/compare.py" "$M4/expected/$name" "$TMP/out" "${tol[@]}" > "$TMP/diff"; then
    echo "same  $name"
  else
    echo "DIFF  $name"; cat "$TMP/diff"; fail=1
  fi
}

# ---- Lesson 1: the installation check, then a workspace with one package --------------------
talker_listener() {
  timeout -s INT 15 ros2 run demo_nodes_cpp talker > "$TMP/talker" 2>&1 &
  timeout -s INT 3.6 ros2 run demo_nodes_py listener 2>&1 | head -3
  pkill -INT -f 'demo_nodes_cpp/talker'; wait
  head -3 "$TMP/talker"
}
check ros-talker_listener.txt --mask 'World: [0-9]+' talker_listener
WS="$TMP/ros2_ws"; mkdir -p "$WS/src"
# (the temporary path is printed as /home/you/ros2_ws, the lesson's example home folder)
check ros-pkg_create.txt bash -c "cd '$WS/src' && ros2 pkg create m4_hello \
  --build-type ament_python --dependencies rclpy std_msgs --node-name hello_node \
  --description 'Month 4 lesson 1: a first ROS 2 node' --maintainer-name 'Your Name' --maintainer-email you@example.com \
  2>&1 | sed 's|$WS|/home/you/ros2_ws|'"
rm -rf "$WS/src/m4_hello"; cp -r "$M4/ros2-setup/m4_hello" "$WS/src/"   # the edited package from the lesson
check ros-colcon_build.txt bash -c "cd '$WS' && colcon build"
check ros-not_sourced.txt  ros2 run m4_hello hello_node
set +u; source "$WS/install/setup.bash"; set -u
check ros-hello_run.txt    bash -c "timeout -s INT 6 ros2 run m4_hello hello_node 2>&1 | head -4"
hello_graph() {
  timeout -s INT 15 ros2 run m4_hello hello_node > /dev/null 2>&1 &
  sleep 3
  echo '$ ros2 node list'; ros2 node list
  echo '$ ros2 topic list'; ros2 topic list
  echo '$ ros2 topic echo /hello --once'; ros2 topic echo /hello --once
  echo '$ ros2 topic hz /hello'; timeout -s INT 3.5 ros2 topic hz /hello 2>&1 | head -1
  pkill -INT -f 'lib/m4_hello/hello_node'; wait
}
check ros-hello_graph.txt --tol 0.05 --mask 'hello #[0-9]+' hello_graph

# ---- Lesson 2: a graph with custom interfaces, a C++ node, a launch file and a bag ----------
WS2="$TMP/graph_ws"; mkdir -p "$WS2/src"; cp -r "$M4/ros2-graph/"m4_* "$WS2/src/"
check ros-graph_build.txt  bash -c "cd '$WS2' && colcon build"
set +u; source "$WS2/install/setup.bash"; set -u
check ros-interface_show.txt bash -c "for i in msg/Reading srv/SetAlpha action/Collect; do echo \"\$ ros2 interface show m4_interfaces/\$i\"; ros2 interface show m4_interfaces/\$i; done"
check ros-launch_args.txt  ros2 launch m4_graph graph.launch.py --show-args
start_graph() {   # start_graph [launch args...]: the Lesson 2 graph in the background, log in $TMP/launch
  timeout -s INT 60 ros2 launch m4_graph graph.launch.py "$@" > "$TMP/launch" 2>&1 &
  for _ in $(seq 50); do grep -q 'listening on' "$TMP/launch" && grep -q 'set_alpha ready' "$TMP/launch" && break; sleep 0.2; done
  for _ in $(seq 20); do [[ $(ros2 node list | wc -l) -ge 4 ]] && break; sleep 0.5; done   # CLI cache
  sleep 1
}
stop_graph() { pkill -INT -f 'ros2 launch m4_graph' ; wait; }
start_graph
check ros-graph_launch.txt --sort 1 bash -c "grep -v -E 'Traceback|^\[[a-z_]+-[0-9]\]  ' '$TMP/launch' | head -10"
graph_inspect() {
  echo '$ ros2 node list'; ros2 node list
  echo '$ ros2 topic list -t'; ros2 topic list -t
  echo '$ ros2 node info /aggregator_node'; ros2 node info /aggregator_node
}
check ros-graph_inspect.txt graph_inspect
check ros-summary_echo.txt --tol 1 ros2 topic echo /summary --once
set_alpha() {
  echo '$ ros2 service call /set_alpha m4_interfaces/srv/SetAlpha "{alpha: 0.5}"'
  ros2 service call /set_alpha m4_interfaces/srv/SetAlpha "{alpha: 0.5}"
  echo '$ ros2 service call /set_alpha m4_interfaces/srv/SetAlpha "{alpha: 1.5}"'
  ros2 service call /set_alpha m4_interfaces/srv/SetAlpha "{alpha: 1.5}"
  echo '$ ros2 param get /filter_node alpha'; ros2 param get /filter_node alpha
  echo '$ ros2 param set /filter_node alpha 2.0'; ros2 param set /filter_node alpha 2.0
}
check ros-set_alpha.txt set_alpha
check ros-collect.txt --tol 1 ros2 run m4_graph collect_client 5
check ros-collect_cancel.txt --tol 1 ros2 run m4_graph collect_client 20 --cancel-after 3
# ros2 bag: record 4 s of /raw and /filtered, look inside, replay /raw into a lone filter node
bag() {
  cd "$TMP" && rm -rf sensor_run
  echo '$ ros2 bag record -o sensor_run /raw /filtered'
  timeout -s INT 4 ros2 bag record -o sensor_run /raw /filtered 2>&1 | grep -E 'Subscribed|Recording stopped'
  echo '$ ros2 bag info sensor_run'; ros2 bag info sensor_run
}
check ros-bag_record.txt --tol 0.35 --sort 1 --mask '(Bag size|Duration|Start|End): .*' bag
stop_graph
bag_play() {
  cd "$TMP"
  timeout -s INT 20 ros2 run m4_graph_cpp filter_node > /dev/null 2>&1 &
  sleep 1
  timeout -s INT 6 ros2 topic echo /filtered --field value > "$TMP/replayed" 2>&1 &
  sleep 1
  ros2 bag play sensor_run --topics /raw > /dev/null 2>&1
  wait %2 2>/dev/null
  grep -v -- '---' "$TMP/replayed" | head -3
  pkill -INT -f 'm4_graph_cpp/filter_node'; wait
}
check ros-bag_play.txt --tol 1 bag_play
start_graph rate:=10.0 summary_topic:=stats
remapped() {
  echo '$ ros2 topic list'; ros2 topic list
  echo '$ ros2 topic hz /raw'; timeout -s INT 3.5 ros2 topic hz /raw 2>&1 | head -1
}
check ros-launch_remap.txt --tol 0.05 remapped
stop_graph
qos() {
  timeout -s INT 8 ros2 topic pub -r 2 --qos-reliability best_effort /qos_demo std_msgs/msg/String "{data: hi}" > /dev/null 2>&1 &
  sleep 1.5
  echo '$ ros2 topic echo --qos-reliability reliable /qos_demo std_msgs/msg/String'
  timeout -s INT 3 ros2 topic echo --qos-reliability reliable /qos_demo std_msgs/msg/String 2>&1 | head -3
  echo '$ ros2 topic echo --qos-reliability best_effort /qos_demo std_msgs/msg/String'
  timeout -s INT 2.5 ros2 topic echo --qos-reliability best_effort /qos_demo std_msgs/msg/String 2>&1 | head -2
  wait
}
check ros-qos_mismatch.txt qos

# ---- Lesson 3: the m4bot description, its inertias and its TF tree --------------------------
WS3="$TMP/desc_ws"; mkdir -p "$WS3/src"; cp -r "$M4/urdf-tf/m4_description" "$WS3/src/"
(cd "$WS3" && colcon build > /dev/null 2>&1)
set +u; source "$WS3/install/setup.bash"; set -u
URDF_X="$M4/urdf-tf/m4_description/urdf/robot.urdf.xacro"
check ros-xacro_check.txt bash -c "cd '$TMP' && xacro '$URDF_X' > robot.urdf && check_urdf robot.urdf"
check ros-inertia_check.txt python3 "$M4/urdf-tf/inertia_check.py" "$TMP/robot.urdf"
start_display() {   # start_display <joints>: robot_state_publisher (+ joint source), no RViz
  timeout -s INT 60 ros2 launch m4_description display.launch.py joints:="$1" rviz:=false > "$TMP/display" 2>&1 &
  for _ in $(seq 50); do grep -q 'Robot initialized' "$TMP/display" && break; sleep 0.2; done
  sleep 2
}
stop_display() { pkill -INT -f 'pose_head.py|static_transform_publisher' ; pkill -INT -f 'ros2 launch m4_description'; wait; }
echo_tf() {   # echo_tf <from> <to> <lines>: the first transform tf2_echo prints (or what it waits for)
  timeout -s INT 4 ros2 run tf2_ros tf2_echo "$1" "$2" 2>&1 | grep -v -E 'signal_handler|^\[INFO\].*target_frame - frame does not exist' | head -"$3"
}
export -f echo_tf
start_display none
broken() {
  echo '$ ros2 run tf2_ros tf2_echo base_link camera_link'; echo_tf base_link camera_link 1
  echo '$ ros2 run tf2_ros tf2_echo base_link laser'; echo_tf base_link laser 1
  echo '$ ros2 run tf2_ros tf2_echo base_link lidar_link'; echo_tf base_link lidar_link 5
}
check ros-tf_broken.txt broken
timeout -s INT 30 python3 "$M4/urdf-tf/pose_head.py" 30 0 > /dev/null 2>&1 &
sleep 2
check ros-tf_pan30.txt --mask 'At time [0-9.]+' bash -c "echo_tf base_link camera_link 10"
timeout -s INT 30 ros2 run tf2_ros static_transform_publisher --frame-id lidar_link --child-frame-id laser > /dev/null 2>&1 &
sleep 2
check ros-tf_laser_alias.txt bash -c "echo_tf base_link laser 3"
stop_display

# ---- Lesson 5: diff_drive.py, the wheel-speed arithmetic of diff_drive_controller ----------
# (plain Python, no ROS needed; tools/sim/reproduce.sh runs it too, without ROS)
check ctl-diff_drive.txt python3 "$M4/ros2-control/diff_drive.py"

# ---- Lesson 6: map_check.py must reject a blank map and a map with one object erased ---------
# (plain Python on a map saved by a real run, slam-nav/test/room.*; tools/sim/ros/run.sh repeats
# it on every freshly saved map)
check slam-map_check_negative.txt python3 "$M4/slam-nav/map_check_test.py"

exit $fail
