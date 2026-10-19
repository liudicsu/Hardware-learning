#!/usr/bin/env bash
# Re-render the Month 4 figures in public/m4/ (needs ROS 2 Jazzy, graphviz, xvfb and Pillow).
#   tf_tree.png     the m4bot TF tree from tf2_tools view_frames, drawn with graphviz
#   m4bot_rviz.png  m4bot in RViz with the camera head panned 30 degrees
set -eo pipefail
M4="$(cd "$(dirname "$0")" && pwd)"; OUT="$M4/../../public/m4"; mkdir -p "$OUT"
[ "${ROS_DISTRO:-}" = jazzy ] || { echo "source ROS 2 Jazzy first"; exit 1; }
export ROS_DOMAIN_ID=$((RANDOM % 100 + 100)) ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
# background jobs ignore SIGINT in a script, so every node runs under timeout -s INT instead
mkdir -p "$TMP/ws/src"; cp -r "$M4/urdf-tf/m4_description" "$TMP/ws/src/"
(cd "$TMP/ws" && colcon build > /dev/null 2>&1)
source "$TMP/ws/install/setup.bash"

# 1. TF tree: robot_state_publisher + a 30 degree pan, then view_frames writes a .gv file
timeout -s INT 12 ros2 launch m4_description display.launch.py joints:=none rviz:=false > /dev/null 2>&1 &
sleep 3
timeout -s INT 9 python3 "$M4/urdf-tf/pose_head.py" 30 0 > /dev/null 2>&1 &
sleep 2
(cd "$TMP" && ros2 run tf2_tools view_frames > /dev/null 2>&1)
dot -Tpng -Gdpi=110 "$(ls "$TMP"/frames_*.gv | head -1)" -o "$OUT/tf_tree.png"
wait

# 2. RViz on a virtual screen, screenshot cropped to the 3D view
xvfb-run -a -s "-screen 0 1200x800x24" bash -c "
  timeout -s INT 22 ros2 launch m4_description display.launch.py joints:=none > /dev/null 2>&1 &
  sleep 4; timeout -s INT 16 python3 '$M4/urdf-tf/pose_head.py' 30 0 > /dev/null 2>&1 &
  sleep 12
  python3 -c \"from PIL import ImageGrab; ImageGrab.grab().crop(tuple(int(v) for v in '${CROP:-366,66,1182,766}'.split(','))).save('$OUT/m4bot_rviz.png')\"
  wait"
echo "wrote $OUT/tf_tree.png $OUT/m4bot_rviz.png"
