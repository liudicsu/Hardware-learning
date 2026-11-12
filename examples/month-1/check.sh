#!/usr/bin/env bash
# Run the Month 1 Python examples exactly as the lesson does and compare with the quoted output.
# Legacy scripts are ordinary program runs; DMM enrichment is a synthetic Monte Carlo model.
# Needs python3 (3.9+), no packages.
# Usage: examples/month-1/check.sh
set -euo pipefail
M1="$(cd "$(dirname "$0")" && pwd)"
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
series: 5700 Ω, range 5415–5985 Ω"  python3 resistors.py
check "log.py, first run" "Logged 1 measurement.
0 of 1 measurements out of 5 % tolerance"  python3 log.py
sed -i.bak 's/record("R1", 4700, 4688)/record("R1", 4700, 4400)/' log.py   # the lesson's second run
check "log.py, second run" "Logged 1 measurement.
R1: expected 4700 Ω, measured 4400 Ω → off by 6.4 %
1 of 2 measurements out of 5 % tolerance"  python3 log.py
if python3 "$M1/bench-multimeter/dmm_uncertainty_toy.py" > "$TMP/dmm_uncertainty_toy.txt" && diff -u "$M1/expected/dmm_uncertainty_toy.txt" "$TMP/dmm_uncertainty_toy.txt"; then
  echo "same  dmm_uncertainty_toy.txt"
else
  echo "DIFF  dmm_uncertainty_toy.txt"; fail=1
fi
if python3 "$M1/components/supply_dip_decoupling_toy.py" > "$TMP/supply_dip_decoupling_toy.txt" && diff -u "$M1/expected/supply_dip_decoupling_toy.txt" "$TMP/supply_dip_decoupling_toy.txt"; then
  echo "same  supply_dip_decoupling_toy.txt"
else
  echo "DIFF  supply_dip_decoupling_toy.txt"; fail=1
fi
if python3 "$M1/components/esd_tvs_clamp_toy.py" > "$TMP/esd_tvs_clamp_toy.txt" && diff -u "$M1/expected/esd_tvs_clamp_toy.txt" "$TMP/esd_tvs_clamp_toy.txt"; then
  echo "same  esd_tvs_clamp_toy.txt"
else
  echo "DIFF  esd_tvs_clamp_toy.txt"; fail=1
fi
if python3 "$M1/components/wheatstone_bridge_sense_toy.py" > "$TMP/wheatstone_bridge_sense_toy.txt" && diff -u "$M1/expected/wheatstone_bridge_sense_toy.txt" "$TMP/wheatstone_bridge_sense_toy.txt"; then
  echo "same  wheatstone_bridge_sense_toy.txt"
else
  echo "DIFF  wheatstone_bridge_sense_toy.txt"; fail=1
fi
if python3 "$M1/components/bridge_rectifier_ripple_toy.py" > "$TMP/bridge_rectifier_ripple_toy.txt" && diff -u "$M1/expected/bridge_rectifier_ripple_toy.txt" "$TMP/bridge_rectifier_ripple_toy.txt"; then
  echo "same  bridge_rectifier_ripple_toy.txt"
else
  echo "DIFF  bridge_rectifier_ripple_toy.txt"; fail=1
fi
if python3 "$M1/ohms-law/thevenin_loaded_divider_toy.py" > "$TMP/thevenin_loaded_divider_toy.txt" && diff -u "$M1/expected/thevenin_loaded_divider_toy.txt" "$TMP/thevenin_loaded_divider_toy.txt"; then
  echo "same  thevenin_loaded_divider_toy.txt"
else
  echo "DIFF  thevenin_loaded_divider_toy.txt"; fail=1
fi
if python3 "$M1/soldering/soldering_thermal_window_toy.py" > "$TMP/soldering_thermal_window_toy.txt" && diff -u "$M1/expected/soldering_thermal_window_toy.txt" "$TMP/soldering_thermal_window_toy.txt"; then
  echo "same  soldering_thermal_window_toy.txt"
else
  echo "DIFF  soldering_thermal_window_toy.txt"; fail=1
fi
if python3 "$M1/bench-multimeter/kelvin_four_wire_sense_toy.py" > "$TMP/kelvin_four_wire_sense_toy.txt" && diff -u "$M1/expected/kelvin_four_wire_sense_toy.txt" "$TMP/kelvin_four_wire_sense_toy.txt"; then
  echo "same  kelvin_four_wire_sense_toy.txt"
else
  echo "DIFF  kelvin_four_wire_sense_toy.txt"; fail=1
fi
if python3 "$M1/python-terminal/nyquist_aliasing_toy.py" > "$TMP/nyquist_aliasing_toy.txt" && diff -u "$M1/expected/nyquist_aliasing_toy.txt" "$TMP/nyquist_aliasing_toy.txt"; then
  echo "same  nyquist_aliasing_toy.txt"
else
  echo "DIFF  nyquist_aliasing_toy.txt"; fail=1
fi

if python3 "$M1/bench-multimeter/true_rms_vs_average_responding_toy.py" > "$TMP/true_rms_vs_average_responding_toy.txt" && diff -u "$M1/expected/true_rms_vs_average_responding_toy.txt" "$TMP/true_rms_vs_average_responding_toy.txt"; then
  echo "same  true_rms_vs_average_responding_toy.txt"
else
  echo "DIFF  true_rms_vs_average_responding_toy.txt"; fail=1
fi
if python3 "$M1/components/zener_shunt_ldo_headroom_toy.py" > "$TMP/zener_shunt_ldo_headroom_toy.txt" && diff -u "$M1/expected/zener_shunt_ldo_headroom_toy.txt" "$TMP/zener_shunt_ldo_headroom_toy.txt"; then
  echo "same  zener_shunt_ldo_headroom_toy.txt"
else
  echo "DIFF  zener_shunt_ldo_headroom_toy.txt"; fail=1
fi

if python3 "$M1/ohms-law/superposition_linear_circuit_toy.py" > "$TMP/superposition_linear_circuit_toy.txt" && diff -u "$M1/expected/superposition_linear_circuit_toy.txt" "$TMP/superposition_linear_circuit_toy.txt"; then
  echo "same  superposition_linear_circuit_toy.txt"
else
  echo "DIFF  superposition_linear_circuit_toy.txt"; fail=1
fi
if python3 "$M1/components/peukert_rate_capacity_toy.py" > "$TMP/peukert_rate_capacity_toy.txt" && diff -u "$M1/expected/peukert_rate_capacity_toy.txt" "$TMP/peukert_rate_capacity_toy.txt"; then
  echo "same  peukert_rate_capacity_toy.txt"
else
  echo "DIFF  peukert_rate_capacity_toy.txt"; fail=1
fi
if python3 "$M1/soldering/crimp_vs_solder_strain_relief_toy.py" > "$TMP/crimp_vs_solder_strain_relief_toy.txt" && diff -u "$M1/expected/crimp_vs_solder_strain_relief_toy.txt" "$TMP/crimp_vs_solder_strain_relief_toy.txt"; then
  echo "same  crimp_vs_solder_strain_relief_toy.txt"
else
  echo "DIFF  crimp_vs_solder_strain_relief_toy.txt"; fail=1
fi
exit $fail
