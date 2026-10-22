"""line_sim.py: a line follower that starts 20 mm off the line, tuned with P and then PD.

Toy model: 8 reflectance sensors 9.5 mm apart (like a QTR-8RC), a 100 Hz control loop,
and wheels that need about 80 ms to reach a new turning speed.
"""
import math

SPEED = 0.30           # forward speed, m/s
DT = 0.01              # control loop period, s (100 Hz)
MOTOR_TAU = 0.08       # how fast the turn rate follows the command, s
SPACING = 0.0095       # sensor spacing, m
LINE_HALF_WIDTH = 0.009


def read_position(offset_m):
    """Weighted average of 8 sensor readings: 0..7000, 3500 = line under the centre."""
    total = weighted = 0.0
    for i in range(8):
        x = (i - 3.5) * SPACING + offset_m           # sensor position relative to the line
        r = 1000 * math.exp(-(x / LINE_HALF_WIDTH) ** 2)  # 0 = white, 1000 = black
        total += r
        weighted += r * i * 1000
    if total < 50:                                    # line lost: report the nearest edge
        return 0 if offset_m > 0 else 7000
    return weighted / total


def run(kp, kd, seconds=3.0):
    y, heading, turn_rate = 0.020, 0.0, 0.0          # start 20 mm to one side
    last_error = None
    log = []
    for step in range(int(seconds / DT)):
        error = 3500 - read_position(y)               # setpoint − measurement
        d_error = 0.0 if last_error is None else (error - last_error) / DT
        last_error = error
        command = kp * error + kd * d_error            # rad/s of turning, positive turns towards -y
        command = max(-6.0, min(6.0, command))
        for _ in range(10):                            # robot physics at 1 ms
            turn_rate += (command - turn_rate) * 0.001 / MOTOR_TAU
            heading -= turn_rate * 0.001
            y += SPEED * math.sin(heading) * 0.001
        log.append(((step + 1) * DT, y))
    return log


def describe(log):
    ys = [y for _, y in log]
    overshoot = max(0.0, -min(ys)) * 1000              # mm past the line on the other side
    crossings = sum(1 for a, b in zip(ys, ys[1:]) if a * b < 0)
    settled = next((t for t, _ in log if all(abs(y) < 0.002 for tt, y in log if tt >= t)), None)
    return overshoot, crossings, settled


if __name__ == "__main__":
    cases = (("P only", 0.0003, 0.0), ("P + small D", 0.0003, 0.0001), ("P + D", 0.0003, 0.0002))
    logs = {name: run(kp, kd, seconds=4.0) for name, kp, kd in cases}
    print("offset from the line (mm), every 0.5 s")
    print("  t_s  " + "  ".join(f"{name:>11}" for name, _, _ in cases))
    for k in range(0, 9):
        t = k * 0.5
        row = []
        for name, _, _ in cases:
            y = 20.0 if k == 0 else logs[name][int(round(t / DT)) - 1][1] * 1000
            row.append(f"{y:11.1f}")
        print(f"  {t:3.1f}  " + "  ".join(row))
    print()
    for name, kp, kd in cases:
        overshoot, crossings, settled = describe(logs[name])
        settled_txt = f"{settled:.2f} s" if settled is not None else "never"
        print(f"{name:11} kp={kp} kd={kd}: overshoot {overshoot:4.1f} mm, "
              f"{crossings} line crossings, within 2 mm from {settled_txt}")
