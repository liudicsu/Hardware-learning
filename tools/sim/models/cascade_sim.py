"""cascade_sim.py: finish the Month 2 balancer with an outer speed loop (a cascade).

Same toy inverted pendulum as balance_sim.py (centre of mass 0.10 m above the axle, the
controller sets wheel acceleration, complementary filter with a 0.5 s time constant),
plus the things that make a real balancer roll away:
  * the IMU is mounted 1 degree off, so "pitch = 0" is not quite the balance point
  * the wheels have a top speed, and a coarse encoder (90 counts per turn of a 65 mm wheel)
Inner loop: PD on pitch at 200 Hz. Outer loop: PI on wheel speed at 25 Hz, which moves
the inner loop's SETPOINT. 60 s run; at t = 30 s someone pushes the robot.
"""
import math
import random

G, L = 9.81, 0.10            # gravity, height of the centre of mass (m)
MAX_ACCEL = 6.0              # m/s^2 the motors can deliver
MOTOR_TAU = 0.02             # wheels reach a new acceleration in ~20 ms
MAX_SPEED = 1.0              # m/s, wheel top speed
MOUNT_ERROR = 1.0            # deg, IMU reads this much more than the true tilt
WHEEL_TURN = math.pi * 0.065 # m per wheel turn (65 mm wheel)
COUNTS_PER_TURN = 90         # encoder counts per wheel turn (A edges only, as in the sketch)
KP, KD = 0.8, 0.04           # inner PD, same gains as balance_sim.py


def run(outer=None, kp_s=0.0, ki_s=0.0, push=40.0, go=None, seconds=60.0, seed=3, trace=None):
    """outer=None: inner loop only; outer="P" or "PI" adds the speed loop.
    kp_s is in deg of setpoint per m/s of speed error, ki_s in deg per metre.
    go=(t, speed): from time t on, ask for this wheel speed instead of 0."""
    rng = random.Random(seed)
    dt = 0.005
    theta, omega, accel = math.radians(3.0), 0.0, 0.0
    x, v = 0.0, 0.0
    est, setpoint, integral = 0.0, 0.0, 0.0
    last_counts, tick, t, next_ctrl = 0, 0, 0.0, 0.0
    far, pushed, sq, n = 0.0, False, 0.0, 0
    x_before, push_far, settled = 0.0, 0.0, None
    log = []
    while t < seconds:
        if t >= next_ctrl:                                   # --- 200 Hz controller tick ---
            next_ctrl += dt
            gyro = math.degrees(omega) + rng.gauss(0, 0.3)
            acc = math.degrees(theta) + MOUNT_ERROR + rng.gauss(0, 2.5)
            a = 0.5 / (0.5 + dt)
            est = a * (est + gyro * dt) + (1 - a) * acc
            if outer and tick % 8 == 0:                      # --- 25 Hz outer loop ---
                counts = math.floor(x / WHEEL_TURN * COUNTS_PER_TURN)
                speed = (counts - last_counts) / COUNTS_PER_TURN * WHEEL_TURN / (8 * dt)
                last_counts = counts
                target = go[1] if go and t >= go[0] else 0.0
                error = target - speed
                if outer == "PI":
                    integral += error * 8 * dt
                    limit = 3.0 / ki_s                       # anti-windup: the integral alone
                    integral = max(-limit, min(limit, integral))  # may ask for at most 3 deg
                setpoint = max(-3.0, min(3.0, kp_s * error + ki_s * integral))
            tick += 1
            command = KP * (est - setpoint) + KD * gyro
            command = max(-MAX_ACCEL, min(MAX_ACCEL, command))
            if trace and trace[0] <= t < trace[1] and tick % 8 == 1:
                log.append(f"t={t:5.2f} s  setpoint {setpoint:+5.2f} deg  tilt {math.degrees(theta):+5.2f} deg  "
                           f"wheels {v:+.2f} m/s")
        # --- physics at 1 ms ---
        accel += (command - accel) * 0.001 / MOTOR_TAU
        a_real = accel
        if (v >= MAX_SPEED and a_real > 0) or (v <= -MAX_SPEED and a_real < 0):
            a_real = 0.0                                     # motors are flat out
        alpha = (G * math.sin(theta) - a_real * math.cos(theta)) / L
        omega += alpha * 0.001
        theta += omega * 0.001
        v += a_real * 0.001
        x += v * 0.001
        if not pushed and t >= 30.0:
            omega += math.radians(push)
            pushed, x_before = True, x
        if pushed:
            push_far = max(push_far, abs(x - x_before))
            if settled is None and t >= 35.0:
                settled = abs(x - x_before)                  # 5 s after the push
        if 40.0 < t < 60.0:
            sq += math.degrees(theta) ** 2
            n += 1
        t += 0.001
        if not go:
            far = max(far, abs(x))
        if abs(math.degrees(theta)) > 40:
            return f"fell over after {t:.1f} s, {x:+.2f} m from the start", log
    return (f"upright, farthest {far / WHEEL_TURN:.2f} wheel turns from the start; push moved it "
            f"{push_far / WHEEL_TURN:.2f} turns, {settled / WHEEL_TURN:.2f} turns off 5 s later; "
            f"wobble {math.sqrt(sq / n):.1f} deg rms"), log


if __name__ == "__main__":
    print("inner loop only:         ", run()[0])
    print("outer P   (12):          ", run("P", kp_s=12)[0])
    print("outer PI  (12, 12):      ", run("PI", kp_s=12, ki_s=12)[0])
    print("outer PI  (60, 60):      ", run("PI", kp_s=60, ki_s=60)[0])
    print("outer PI (12, 12), asked to drive at +0.2 m/s from t = 40 s:")
    print("\n".join(run("PI", kp_s=12, ki_s=12, go=(40.0, 0.2), seconds=41.0, trace=(39.96, 40.6))[1]))
