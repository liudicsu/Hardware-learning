#!/usr/bin/env bash
# Run the Month 1 Python examples exactly as the lesson does and compare with the quoted output.
# These are ordinary programs on your computer, not simulations. Needs python3 (3.9+), no packages.
# Usage: examples/month-1/check.sh
set -euo pipefail
SRC="$(cd "$(dirname "$0")/python-terminal" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cp "$SRC"/*.py "$TMP"/ && cd "$TMP"
fail=0
check() {   # check <label> <expected> <command...>
  local label="$1" want="$2"; shift 2
  local got; got="$("$@" 2>&1 || true)"
  if [[ "$got" == "$want" ]]; then echo "same  $label"; else echo "DIFF  $label"; echo "  expected: $want"; echo "  got:      $got"; fail=1; fi
}
check "ohm.py current"  "22.7 mA"  python3 ohm.py current --volts 5 --ohms 220
check "ohm.py divider"  "1.599 V"  python3 ohm.py divider --vin 5 --r1 10000 --r2 4700
check "ohm.py bad input" "error: ohms must be positive"  python3 ohm.py current --volts 5 --ohms 0
check "resistors.py" "Resistor(ohms=2200, tolerance=0.05)
range: 2090–2310 Ω
parallel: 5000 Ω
series: 5700 Ω"  python3 resistors.py
check "log.py, first run" "Logged 1 measurement.
0 of 1 measurements out of 5 % tolerance"  python3 log.py
sed -i.bak 's/record("R1", 4700, 4688)/record("R1", 4700, 4400)/' log.py   # the lesson's second run
check "log.py, second run" "Logged 1 measurement.
R1: expected 4700 Ω, measured 4400 Ω → off by 6.4 %
1 of 2 measurements out of 5 % tolerance"  python3 log.py
exit $fail
