#!/usr/bin/env bash
# Render the preview pictures used in the Month 3 lessons from the .scad files (OpenSCAD 2021.01).
# Usage: examples/month-3/render_previews.sh   -> writes public/m3/*.png
set -euo pipefail
M3="$(cd "$(dirname "$0")" && pwd)"
OUT="$M3/../../public/m3"
mkdir -p "$OUT"
shot() { openscad -o "$OUT/$1" --imgsize=900,600 --autocenter --viewall --colorscheme=Tomorrow --camera="$3" "$2" >/dev/null 2>&1 && echo "wrote public/m3/$1"; }
shot servo_bracket.png "$M3/cad-parametric/servo_bracket.scad" 0,0,0,60,0,145,0
shot esp32_case.png    "$M3/fdm-printing/esp32_case.scad"      0,0,0,55,0,25,0
shot finray_finger.png "$M3/gripper-fingers/finray_finger.scad" 0,0,0,0,0,0,0
