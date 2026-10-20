#!/usr/bin/env bash
# Run the Month 3 examples exactly as the lessons do and compare with the outputs they quote
# (stored in expected/). These are ordinary programs on your computer, not simulations.
# Needs: python3 (3.9+), OpenSCAD (tested with 2021.01), and the pinned packages in
# requirements.txt (feetech-servo-sdk==1.0.0) for the SDK comparison:
#   python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
# Without them arm-compare_sdk is skipped (and reported as such).
# The simulated outputs (backlash, PID, cascade) are checked by tools/sim/reproduce.sh.
# Usage: examples/month-3/check.sh
set -euo pipefail
M3="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fail=0
# OpenSCAD versions differ in how many triangles they write, so that one number is ignored.
norm() { sed -E 's/triangles: [0-9]+/triangles: N/; s/[[:space:]]+$//'; }
check() {     # check <expected file> <command...>
  local name="$1"; shift
  if diff -u <(norm < "$M3/expected/$name") <("$@" 2>&1 | norm) > "$TMP/diff"; then
    echo "same  $name"
  else
    echo "DIFF  $name"; cat "$TMP/diff"; fail=1
  fi
}
scad() {      # scad <file.scad> [-D ...]: render to STL, print the ECHO lines, then stl_info
  local f="$1"; shift
  openscad "$@" -o "$TMP/part.stl" "$f" 2>&1 | grep -E '^(ECHO|ERROR|WARNING)' || true
  python3 "$M3/cad-parametric/stl_info.py" "$TMP/part.stl" "${DENSITY:-1.24}"
}
clash() {     # the closed-lid interference check: what the lid and the base share [-D ...]
  rm -f "$TMP/clash.stl"
  openscad -D 'part="clash"' "$@" -o "$TMP/clash.stl" "$M3/fdm-printing/esp32_case.scad" 2>&1 | grep -E 'empty|ERROR' || true
  if [[ -s "$TMP/clash.stl" ]]; then python3 "$M3/cad-parametric/stl_info.py" "$TMP/clash.stl"; fi
}

# Lesson 1
check cad-bracket.txt         scad "$M3/cad-parametric/servo_bracket.scad"
check cad-bracket-tight.txt   bash -c "openscad -D clearance=0.15 -o '$TMP/t.stl' '$M3/cad-parametric/servo_bracket.scad' 2>&1 | grep '^ECHO: \"cut-out'"
check cad-bracket-assert.txt  bash -c "openscad -D hole_pitch=24 -o '$TMP/a.stl' '$M3/cad-parametric/servo_bracket.scad' 2>&1 | grep -E '^ERROR' || true"
# Lesson 2
check fdm-snap_fit.txt        python3 "$M3/fdm-printing/snap_fit.py"
check fdm-case.txt            scad "$M3/fdm-printing/esp32_case.scad"
check fdm-case-clash.txt      clash
check fdm-case-clash-tight.txt clash -D fit=-0.1
# Lesson 3
check tr-gear_calc.txt        python3 "$M3/transmissions/gear_calc.py"
# Lesson 5
check arm-sts_packet.txt      python3 "$M3/so101-arm/sts_packet.py"
if python3 -c "import scservo_sdk" 2>/dev/null; then
  check arm-compare_sdk.txt   bash -c "cd '$M3/so101-arm' && python3 compare_sdk.py"
else
  echo "skip  arm-compare_sdk.txt (pip install -r examples/month-3/requirements.txt to run it)"
fi
# Lesson 6
DENSITY=1.21 check grip-finger.txt scad "$M3/gripper-fingers/finray_finger.scad"
check grip-force.txt          python3 "$M3/gripper-fingers/grip_force.py"
exit $fail
