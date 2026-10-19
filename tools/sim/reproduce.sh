#!/usr/bin/env bash
# Reproduce every simulated output quoted in the lessons and diff it against expected/.
# Usage (from the repository root or anywhere):  tools/sim/reproduce.sh [--compile-only-too]
#   --compile-only-too  also compile the sketches that are never run (ESP32, line follower)
# Prerequisites: see tools/sim/README.md (gcc, libsimavr-dev, libelf-dev, arduino-cli with
# the arduino:avr core, python3, a C compiler).
set -euo pipefail
SIM="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SIM/../.." && pwd)"
EX="$ROOT/examples/month-2"
BUILD="$SIM/build"
OUT="$SIM/out"
mkdir -p "$BUILD" "$OUT"

echo "== building the simavr harness"
gcc -O2 -o "$BUILD/avrrun" "$SIM/avrrun/avrrun.c" -lsimavr -lelf -lm

compile() {   # compile <sketch dir> -> prints path of the .elf
  local dir="$1" name; name="$(basename "$dir")"
  arduino-cli compile -b arduino:avr:uno "$dir" --output-dir "$BUILD/$name" >/dev/null
  echo "$BUILD/$name/$name.ino.elf"
}
avr() { "$BUILD/avrrun" "$@" 2>/dev/null | grep -v '^Loaded' | tr -d '\r'; }   # Serial.println ends lines with CR LF

press() {     # a button press at time $1 ms on D2, with contact bounce on press and release
  python3 -c "t=$1; print(f'{t}:D2=0 {round(t+1.2,1)}:D2=1 {round(t+2.5,1)}:D2=0 {round(t+150,1)}:D2=1 {round(t+151.5,1)}:D2=0 {round(t+153,1)}:D2=1')"
}

echo "== compiling and running"
# Month 2 / Lesson 1: pot_pwm with 0, 1.0, 2.5, 4.0, 5.0 V on A0 (repeated identical lines removed)
ELF=$(compile "$EX/arduino-io/pot_pwm")
avr "$ELF" 2500 0:A0=0 500:A0=1000 1000:A0=2500 1500:A0=4000 2000:A0=5000 | uniq > "$OUT/m2-pot_pwm.txt"

# Lesson 2: two_blinks for 1.25 s
ELF=$(compile "$EX/timing-interrupts/two_blinks")
avr "$ELF" 1250 > "$OUT/m2-two_blinks.txt"

# Lesson 2: overflow.c is ordinary C, run on your computer (not simulated)
cc -o "$BUILD/overflow" "$EX/timing-interrupts/overflow.c" && "$BUILD/overflow" > "$OUT/m2-overflow.txt"

# Lesson 2: debounce toy model
python3 "$SIM/models/debounce_sim.py" > "$OUT/m2-debounce_sim.txt"

# Lesson 2: reaction timer: one early press (foul), then reactions 243, 198 and 310.5 ms after the LED
ELF=$(compile "$EX/timing-interrupts/reaction_timer")
avr "$ELF" 17000 $(press 1000) $(press 5364.1) $(press 9931.2) $(press 14693.7) > "$OUT/m2-reaction_timer.txt"

# Lesson 4: one-revolution toy model
python3 "$SIM/models/one_rev_sim.py" > "$OUT/m2-one_rev_sim.txt"

# Lesson 4: one_rev firmware with the simulated TB6612 + gearmotor + encoder (MOTOR=<battery volts>)
ELF=$(compile "$EX/motors-drivers/one_rev")
for v in 8.4 7.4 6.6; do echo "battery $v V: $(MOTOR=$v avr "$ELF" 6000)"; done > "$OUT/m2-one_rev_brake.txt"
# ...and the coast variant: stop with drive(0) instead of brake() at the target
mkdir -p "$BUILD/src/one_rev_coast"
sed 's/^      brake();$/      drive(0);/' "$EX/motors-drivers/one_rev/one_rev.ino" > "$BUILD/src/one_rev_coast/one_rev_coast.ino"
ELF=$(compile "$BUILD/src/one_rev_coast")
for v in 8.4 7.4 6.6; do echo "battery $v V: $(MOTOR=$v avr "$ELF" 6000)"; done > "$OUT/m2-one_rev_coast.txt"

# Lesson 5: I2C scanner with and without the simulated MPU-6050 (MPU=1)
ELF=$(compile "$EX/sensors-fusion/i2c_scanner")
MPU=1 avr "$ELF" 1000 > "$OUT/m2-i2c_scanner_mpu.txt"
avr "$ELF" 1000 > "$OUT/m2-i2c_scanner_empty.txt"

# Lesson 5: filter toy model, then imu_pitch with the simulated MPU-6050 (scripted tilt, +1.5 deg/s bias)
python3 "$SIM/models/filter_sim.py" > "$OUT/m2-filter_sim.txt"
ELF=$(compile "$EX/sensors-fusion/imu_pitch")
MPU=1 avr "$ELF" 12500 > "$OUT/m2-imu_pitch.txt"

# Lesson 6: line follower and balancer toy models, balancer firmware with the simulated MPU-6050
python3 "$SIM/models/line_sim.py" > "$OUT/m2-line_sim.txt"
python3 "$SIM/models/balance_sim.py" > "$OUT/m2-balance_sim.txt"
ELF=$(compile "$EX/first-robots/balancer")
MPU=1 avr "$ELF" 10000 > "$OUT/m2-balancer.txt"

if [[ "${1:-}" == "--compile-only-too" ]]; then
  echo "== compile-only sketches"
  for d in "$EX/arduino-io/blink_custom" "$EX/arduino-io/button_pullup" "$EX/first-robots/line_follower"; do
    compile "$d" >/dev/null && echo "ok  $(basename "$d") (Uno)"
  done
  for d in "$EX/esp32/chip_info" "$EX/esp32/web_servo"; do
    arduino-cli compile -b esp32:esp32:esp32s3 "$d" --output-dir "$BUILD/$(basename "$d")" >/dev/null && echo "ok  $(basename "$d") (ESP32-S3)"
  done
fi

echo "== comparing with expected/"
fail=0
for f in "$SIM"/expected/*.txt; do
  n="$(basename "$f")"
  if diff -u "$f" "$OUT/$n" > "$OUT/$n.diff"; then echo "same  $n"; rm "$OUT/$n.diff"; else echo "DIFF  $n (see $OUT/$n.diff)"; fail=1; fi
done
exit $fail
