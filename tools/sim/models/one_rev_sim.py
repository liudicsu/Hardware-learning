"""one_rev_sim.py: turn a wheel exactly one revolution, open loop vs encoder feedback.

Toy model of a small 120:1 gearmotor with a 12 CPR encoder (1440 counts per wheel turn).
"""
COUNTS_PER_REV = 12 * 120          # encoder counts per motor turn x gear ratio
DT = 0.001                         # 1 ms simulation step
K_SPEED = 260.0                    # counts/s per volt at the motor, once moving
TAU = 0.05                         # motor + wheel time constant, s
DEADBAND_V = 0.8                   # below this the motor does not overcome friction


def step(speed, volts_at_motor):
    """Advance the motor speed (counts/s) by one time step."""
    drive = 0.0 if abs(volts_at_motor) < DEADBAND_V else volts_at_motor
    target = K_SPEED * drive
    return speed + (target - speed) * DT / TAU


def open_loop(battery_v, run_time_s, duty=0.6):
    """Run at a fixed duty for a fixed time, then cut power and let it coast."""
    speed, pos, t = 0.0, 0.0, 0.0
    while t < run_time_s + 0.5:
        v = battery_v * duty if t < run_time_s else 0.0
        speed = step(speed, v)
        pos += speed * DT
        t += DT
    return round(pos)


def closed_loop(battery_v, kp=0.004, max_duty=0.6, min_duty=0.0, tolerance=2):
    """P control on encoder counts: duty proportional to the remaining distance.

    min_duty, if set, is the smallest duty used while the error is outside the tolerance,
    so the motor never stalls just short of the target.
    """
    speed, pos, t = 0.0, 0.0, 0.0
    while t < 3.0:
        error = COUNTS_PER_REV - pos
        duty = max(-max_duty, min(max_duty, kp * error))
        if abs(error) <= tolerance:
            duty = 0.0
        elif abs(duty) < min_duty:
            duty = min_duty if error > 0 else -min_duty
        speed = step(speed, battery_v * duty)
        pos += speed * DT
        t += DT
    return round(pos)


if __name__ == "__main__":
    # Calibrate the open-loop run time on a full 8.4 V battery (2S LiPo, fully charged)
    run_time = COUNTS_PER_REV / (K_SPEED * 8.4 * 0.6)
    print(f"counts per wheel revolution: {COUNTS_PER_REV}")
    print(f"open-loop run time (tuned at 8.4 V): {run_time:.3f} s")
    for battery in (8.4, 7.4, 6.6, 5.0):
        print(f"battery {battery:.1f} V | open loop: {open_loop(battery, run_time):5d}"
              f" | P only: {closed_loop(battery):5d}"
              f" | min 0.15: {closed_loop(battery, min_duty=0.15):5d}"
              f" | min 0.20: {closed_loop(battery, min_duty=0.20):5d}")
