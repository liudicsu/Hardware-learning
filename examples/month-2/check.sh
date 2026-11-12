#!/usr/bin/env bash
# Run the Month 2 enrichment toys and compare with expected/.
# Legacy Arduino sketches stay under tools/sim/reproduce.sh / Wokwi.
# Usage: examples/month-2/check.sh        UPDATE=1 examples/month-2/check.sh
set -uo pipefail
M2="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PYTHONDONTWRITEBYTECODE=1
PY="${M2_PYTHON:-python3}"
fail=0
check() {
  local name="$1"; shift
  (cd "$TMP" && "$@") > "$TMP/$name" 2>&1
  local ec=$?
  if [[ $ec -ne 0 ]]; then echo "FAIL  $name (exit $ec)"; cat "$TMP/$name"; fail=1; return; fi
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/$name" "$M2/expected/$name"; echo "wrote $name"; return; fi
  if diff -u "$M2/expected/$name" "$TMP/$name" > "$TMP/$name.diff"; then echo "same  $name"
  else echo "DIFF  $name"; cat "$TMP/$name.diff"; fail=1; fi
}

check freertos_priority_toy.txt "$PY" "$M2/esp32/freertos_priority_toy.py"
check encoder_index_cal_toy.txt "$PY" "$M2/motors-drivers/encoder_index_cal_toy.py"

check imu_kf_vs_complementary_toy.txt "$PY" "$M2/sensors-fusion/imu_kf_vs_complementary_toy.py"

check winding_thermal_rc_toy.txt "$PY" "$M2/motors-drivers/winding_thermal_rc_toy.py"
check i2c_risetime_toy.txt "$PY" "$M2/arduino-io/i2c_risetime_toy.py"

check spi_mode_mismatch_toy.txt "$PY" "$M2/sensors-fusion/spi_mode_mismatch_toy.py"

check hw_wdt_kick_toy.txt "$PY" "$M2/timing-interrupts/hw_wdt_kick_toy.py"

check pwm_deadtime_distortion_toy.txt "$PY" "$M2/motors-drivers/pwm_deadtime_distortion_toy.py"
check rs485_termination_toy.txt "$PY" "$M2/arduino-io/rs485_termination_toy.py"

check adc_enob_noise_toy.txt "$PY" "$M2/arduino-io/adc_enob_noise_toy.py"
check mag_hard_soft_iron_toy.txt "$PY" "$M2/sensors-fusion/mag_hard_soft_iron_toy.py"

check esp32_light_deep_sleep_toy.txt "$PY" "$M2/esp32/esp32_light_deep_sleep_toy.py"
check i2c_clock_stretch_toy.txt "$PY" "$M2/sensors-fusion/i2c_clock_stretch_toy.py"

check madgwick_vs_complementary_balancer_toy.txt "$PY" "$M2/first-robots/madgwick_vs_complementary_balancer_toy.py"

exit $fail
