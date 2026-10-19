"""balance_sim.py: why a self-balancer needs both a good angle estimate and a fast, steady loop.

Toy inverted pendulum: the robot's centre of mass sits 0.10 m above the axle and the
controller sets the wheels' acceleration. The angle comes from a complementary filter
(gyro bias already calibrated out, noisy gyro and accelerometer) whose time constant
is 0.5 s at every loop rate.
Real robots also need an outer speed loop from the wheel encoders; this model leaves it out.
"""
import math
import random

G, L = 9.81, 0.10            # gravity, height of the centre of mass (m)
MAX_ACCEL = 6.0              # m/s^2 the motors can deliver
MOTOR_TAU = 0.02             # wheels reach a new acceleration in ~20 ms


def run(loop_hz, kp, kd, use_filter=True, seconds=5.0, seed=3):
    """Start tipped 3 degrees; at t = 2.5 s someone gives the robot a push."""
    rng = random.Random(seed)
    dt_ctrl = 1.0 / loop_hz
    theta, omega, accel = math.radians(3.0), 0.0, 0.0    # starts tipped 3 degrees
    est, next_ctrl, command, t = 0.0, 0.0, 0.0, 0.0
    worst, sq, n, pushed = 0.0, 0.0, 0, False
    while t < seconds:
        if t >= next_ctrl:                               # --- controller runs here ---
            next_ctrl = t + dt_ctrl
            gyro = math.degrees(omega) + rng.gauss(0, 0.3)
            acc = math.degrees(theta) + rng.gauss(0, 2.5)     # accelerometer tilt, shaken by the motors
            if use_filter:
                a = 0.5 / (0.5 + dt_ctrl)                  # same 0.5 s time constant at any rate
                est = a * (est + gyro * dt_ctrl) + (1 - a) * acc
            else:
                est = acc                                # raw accelerometer angle only
            command = kp * est + kd * gyro               # PD on angle (deg) and rate (deg/s)
            command = max(-MAX_ACCEL, min(MAX_ACCEL, command))
        # --- physics at 1 ms ---
        accel += (command - accel) * 0.001 / MOTOR_TAU
        alpha = (G * math.sin(theta) - accel * math.cos(theta)) / L
        omega += alpha * 0.001
        theta += omega * 0.001
        if not pushed and t >= 2.5:
            omega += math.radians(40)                      # a push: +40 deg/s
            pushed = True
        if 1.0 < t < 2.5:
            sq += math.degrees(theta) ** 2
            n += 1
        t += 0.001
        worst = max(worst, abs(math.degrees(theta)))
        if worst > 45:
            return f"fell over after {t:.2f} s"
    return f"upright, wobble {math.sqrt(sq / n):.2f} deg rms, worst tilt {worst:.1f} deg"


if __name__ == "__main__":
    print("200 Hz, PD, filtered angle:  ", run(200, kp=0.8, kd=0.04))
    print("200 Hz, PD, raw accel angle: ", run(200, kp=0.8, kd=0.04, use_filter=False))
    print("200 Hz, P only:              ", run(200, kp=0.8, kd=0.0))
    print(" 50 Hz, PD, filtered angle:  ", run(50, kp=0.8, kd=0.04))
    print(" 10 Hz, PD, filtered angle:  ", run(10, kp=0.8, kd=0.04))
