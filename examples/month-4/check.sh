#!/usr/bin/env bash
# Run the Month 4 ROS 2 examples the way the lessons do and compare with the outputs they quote
# (stored in expected/). These are real ROS 2 programs on your computer; nothing here uses a
# simulator (the Gazebo and mock-hardware runs are in tools/sim/reproduce.sh).
# Needs: ROS 2 Jazzy sourced (ros2, colcon) - see README.md. Output that changes from run to run
# (timestamps, timings, process numbers) is masked by compare.py.
# Usage: examples/month-4/check.sh        UPDATE=1 examples/month-4/check.sh rewrites expected/
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
check() {     # check <expected file> [--tol T] [--mask REGEX]... <command...>
  local name="$1"; shift; local tol=()
  while [[ "${1:-}" == --tol || "${1:-}" == --mask ]]; do tol+=("$1" "$2"); shift 2; done
  "$@" > "$TMP/out" 2>&1
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/out" "$M4/expected/$name"; echo "wrote $name"; return; fi
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

exit $fail
